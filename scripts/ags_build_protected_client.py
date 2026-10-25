#!/usr/bin/env python3
"""
AGS (Agent Space) — đóng gói bản client đã khoá cho MỘT đơn hàng (Python 3.11 + `cryptography` cho vault AES-GCM).

  python scripts/ags_build_protected_client.py --token <AGS1...> [--order-id DH-...] [--out dist/ags-client-protected.zip]
      [--license-url https://license.agentsea.vn | ""] [--fast]

Ghi vào thư mục của --out (mặc định dist/):
  ags-client-protected.zip    Gốc zip là `ags-video-editing/` như bản cài đặt thường, nhưng KHÔNG kèm file mẫu thô
                              trong ags_vault_loader.DEV_PATHS (rules, template CapCut, script bpy Blender): chúng nằm
                              trong `assets/vault.ags.enc` (khoá dẫn từ payload_digest của token đơn hàng + release_salt
                              ngẫu nhiên), có thêm `.protected` (JSON: order_id, vault, license_url — máy chủ sổ cái
                              client tự gọi để xin lease; mặc định AGS_BUILD_LICENSE_URL hoặc https://license.agentsea.vn,
                              "" = bản không máy chủ — kèm seal niêm bằng vsec) và `assets/ags_verified_badge.png`.
                              Mọi file .md mang dấu đơn hàng zero-width + dấu niêm nguồn gốc; mọi mục zip mang extra
                              0x4741 = order_id.
  ags-blender-3d-addon.zip    Add-on Blender 3D TUỲ CHỌN (scripts/ags_blender_3d.py + kiểm thử), giải nén thẳng vào thư
                              mục skill. Bản chính chạy đủ trong Claude Code / Antigravity / Codex / Cursor không cần
                              Blender; script bpy của add-on vẫn lấy từ vault của bản chính.
  provenance.json             Nguồn gốc bản dựng: đơn hàng, sha256 từng zip/vault, file loại trừ, kết quả tự kiểm.

Không ghi gì vào cây mã nguồn. Sau khi ghi, tự kiểm: không còn file mẫu thô, vault mở được bằng khoá của token,
dấu niêm khớp, đọc lại được order_id; không có --fast thì giải nén vào thư mục có dấu cách, biên dịch mọi .py và chạy
`ags_setup.py --check` như ags_build_skill_zips (chỉ kiểm môi trường, không mở vault / gọi máy chủ bản quyền).
"""
import argparse
import hashlib
import json
import os
import re
import secrets
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ags_build_skill_zips as skill_zips  # noqa: E402
import ags_client_license as lic  # noqa: E402
import ags_vault_loader as vault  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
PACK_NAME = skill_zips.PACK_NAME
CLIENT_ZIP_NAME = "ags-client-protected.zip"
ADDON_ZIP_NAME = "ags-blender-3d-addon.zip"
PROVENANCE_NAME = "provenance.json"
BADGE_RELPATH = "assets/ags_verified_badge.png"
PROTECTED_MARKER = ".protected"
ADDON_FILES = ("scripts/ags_blender_3d.py", "tests/ags_test_blender.py")
# Công cụ phía bên bán: không đi theo bản của khách.
VENDOR_ONLY = ("scripts/ags_license_server.py", "scripts/ags_build_protected_client.py", "tests/ags_test_shield.py")
ZIP_DATE = (2026, 1, 1, 0, 0, 0)
WATERMARK_CHANNELS = ["unicode_zw", "png_text", "zip_0x4741"]
DEFAULT_LICENSE_URL = "https://license.agentsea.vn"


class BuildError(RuntimeError):
    pass


def collect_vault_files() -> Dict[str, bytes]:
    """{tên trong vault: bytes} đọc từ đúng các file nguồn của ags_vault_loader.DEV_PATHS."""
    files, missing = {}, []
    for name, path in sorted(vault.DEV_PATHS.items()):
        if path.is_file():
            files[name] = path.read_bytes()
        else:
            missing.append(f"{name} ({path})")
    if missing:
        raise BuildError("Thiếu file nguồn của vault: " + ", ".join(missing))
    return files


def dev_relpaths() -> List[str]:
    """Đường dẫn (tính từ gốc skill) của file mẫu thô nằm trong cây skill — phải vắng mặt trong zip."""
    out = []
    for path in vault.DEV_PATHS.values():
        try:
            out.append(path.resolve().relative_to(ROOT.resolve()).as_posix())
        except ValueError:
            continue  # nằm ngoài cây skill (vd. AGS-Auto-Editor/references) thì vốn không vào zip
    return sorted(out)


def _verified_token(token: str) -> Dict[str, Any]:
    """Kiểm chữ ký/hạn của token ở máy dựng (token có thể gắn máy khách) và lấy payload_digest 32 byte."""
    try:
        payload = json.loads(lic._b64d(str(token).strip().split(".")[1]).decode("utf-8"))
        mid = payload.get("mid") if isinstance(payload, dict) else None
    except (IndexError, ValueError, TypeError):
        mid = None
    res = lic.verify_license_token(token, mid if isinstance(mid, str) and mid not in ("", "*") else "may-dung-goi")
    if not res["valid"]:
        raise BuildError(f"{res.get('error_code', lic.SHIELD_INVALID)}: token không hợp lệ — {res['reason']}")
    return res


def _tag_markdown(text: str, tag: str) -> str:
    """Chèn dấu zero-width vào cuối dòng tiêu đề '# ' đầu tiên (ngoài frontmatter), không có thì cuối file."""
    lines = text.splitlines(keepends=True)
    match = re.match(r"---\r?\n.*?\r?\n---\r?\n", text, re.S)
    skip = match.group(0).count("\n") if match else 0
    for i in range(skip, len(lines)):
        if lines[i].startswith("# "):
            body = lines[i].rstrip("\r\n")
            lines[i] = body + tag + lines[i][len(body):]
            return "".join(lines)
    return text.rstrip("\n") + tag + "\n"


def _source_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    if path.suffix in (".bat", ".sh"):  # giống ags_build_skill_zips: .bat cần CRLF, .sh cần LF
        data = data.replace(b"\r\n", b"\n")
        data = data.replace(b"\n", b"\r\n") if path.suffix == ".bat" else data
    return data


def _write_zip(target: Path, entries: List[Tuple[str, bytes, int]], extra: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as archive:
        for arc, data, mode in entries:
            info = zipfile.ZipInfo(arc, ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = mode << 16
            info.extra = extra
            archive.writestr(info, data)
    os.replace(tmp, target)


def _artifact(path: Path, count: int) -> Dict[str, Any]:
    data = path.read_bytes()
    return {"file": path.name, "entries": count, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _check_bundle(client_zip: Path, addon_zip: Path, order_id: str, digest: bytes, vsec: str,
                  vault_files: Dict[str, bytes], full: bool) -> Dict[str, Any]:
    prefix = f"{PACK_NAME}/"
    with zipfile.ZipFile(client_zip) as archive:
        names = set(archive.namelist())
        leaked = sorted(f"{prefix}{rel}" for rel in dev_relpaths() + list(ADDON_FILES) + list(VENDOR_ONLY)
                        if f"{prefix}{rel}" in names)
        if leaked:
            raise BuildError(f"Zip còn file không được phép: {leaked}")
        blob = archive.read(f"{prefix}{vault.VAULT_RELPATH.as_posix()}")
        salt = vault._split_vault(blob)[0]
        if vault.open_vault(blob, vault.derive_vault_key(digest, salt)) != vault_files:
            raise BuildError("Vault mở ra không khớp file nguồn")
        if lic.verify_leak_watermark(archive) != order_id:
            raise BuildError("Không đọc lại được order_id từ zip")
        with tempfile.TemporaryDirectory(prefix="ags protected ") as tmp:
            archive.extractall(tmp)
            skill = Path(tmp) / PACK_NAME
            if not lic.verify_origin_seal(skill, vsec):
                raise BuildError("Dấu niêm nguồn gốc không khớp sau khi giải nén")
            if lic.verify_leak_watermark(skill) != order_id:
                raise BuildError("Thư mục giải nén không còn dấu đơn hàng (PNG/zero-width)")
    if lic.verify_leak_watermark(addon_zip) != order_id:
        raise BuildError("Add-on Blender không mang dấu đơn hàng")
    if full:  # giải nén vào thư mục có dấu cách, compileall + ags_setup.py --check (không mở vault)
        try:
            skill_zips.verify_pack(client_zip)
        except SystemExit as error:
            raise BuildError(str(error)) from None
    return {"dev_files_absent": True, "vault_opens_with_token": True, "origin_seal": True,
            "watermark_order_id": order_id, "runtime_check": "passed" if full else "skipped (fast_build)"}


def build_protected_bundle(out_zip: Optional[Path] = None, order_id: Optional[str] = None, token: str = "",
                           fast_build: bool = False, license_url: str = DEFAULT_LICENSE_URL) -> Dict[str, Any]:
    license_url = str(license_url).strip().rstrip("/")
    if license_url and not license_url.startswith(("https://", "http://")):
        raise BuildError(f"license_url phải là http(s)://... hoặc rỗng (bản không máy chủ): {license_url!r}")
    verified = _verified_token(token)
    payload, digest = verified["payload"], verified["payload_digest"]
    vsec = str(payload.get("vsec") or "")
    token_order = str(payload.get("order_id", ""))
    order_id = str(order_id or token_order).strip()
    if not order_id:
        raise BuildError("Cần order_id (token không ghi order_id và không truyền --order-id)")
    if token_order and order_id != token_order:
        raise BuildError(f"order_id '{order_id}' khác order_id trong token '{token_order}'")

    client_zip = Path(out_zip) if out_zip else DIST / CLIENT_ZIP_NAME
    out_dir = client_zip.parent
    addon_zip, provenance_path = out_dir / ADDON_ZIP_NAME, out_dir / PROVENANCE_NAME

    skills = sorted(p for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file())
    errors = skill_zips.check_skill(ROOT / "SKILL.md", PACK_NAME)
    errors += [e for folder in skills for e in skill_zips.check_skill(folder / "SKILL.md", folder.name)]
    sources = skill_zips.collect(skill_zips.TOP_DIRS, skill_zips.TOP_FILES)
    excluded = set(dev_relpaths()) | set(ADDON_FILES) | set(VENDOR_ONLY)
    client_sources = {rel: path for rel, path in sources.items() if rel not in excluded}
    errors += skill_zips.validate(client_sources)
    if errors:
        raise BuildError("Chưa đóng gói được:\n  - " + "\n  - ".join(errors))
    missing_addon = [rel for rel in ADDON_FILES if rel not in sources]
    if missing_addon:
        raise BuildError(f"Thiếu file add-on Blender: {missing_addon}")

    vault_files = collect_vault_files()
    release_salt = secrets.token_bytes(32)
    vault_blob = vault.seal_vault(vault_files, vault.derive_vault_key(digest, release_salt), release_salt)
    tag = lic.encode_zw_tag(order_id)
    extra = lic.build_zip_extra_0x4741(order_id)

    entries: List[Tuple[str, bytes, int]] = []
    for rel, path in sorted(client_sources.items()):
        data = _source_bytes(path)
        if rel.endswith(".md"):
            data = lic.embed_origin_seal(_tag_markdown(data.decode("utf-8"), tag), vsec).encode("utf-8")
        executable = path.suffix == ".sh" or bool(path.stat().st_mode & 0o100)
        entries.append((f"{PACK_NAME}/{rel}", data, 0o755 if executable else 0o644))
    marker = lic.seal_protected_marker({"schema": "AGS-PROTECTED-V1", "order_id": order_id,
                                        "vault": vault.VAULT_RELPATH.as_posix(), "license_url": license_url}, vsec)
    entries += [
        (f"{PACK_NAME}/{vault.VAULT_RELPATH.as_posix()}", vault_blob, 0o644),
        (f"{PACK_NAME}/{BADGE_RELPATH}", lic.build_badge_png(order_id), 0o644),
        (f"{PACK_NAME}/{PROTECTED_MARKER}", (json.dumps(marker, ensure_ascii=False) + "\n").encode("utf-8"), 0o644),
    ]
    _write_zip(client_zip, sorted(entries), extra)
    addon_entries = [(rel, _source_bytes(sources[rel]), 0o755 if sources[rel].stat().st_mode & 0o100 else 0o644)
                     for rel in ADDON_FILES]
    _write_zip(addon_zip, addon_entries, extra)

    checks = _check_bundle(client_zip, addon_zip, order_id, digest, vsec, vault_files, full=not fast_build)
    provenance = {
        "schema": "AGS-PROVENANCE-V1",
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "order_id": order_id,
        "license_url": license_url,
        "license": {"sub": payload.get("sub"), "tier": payload.get("tier"), "mid": payload.get("mid"),
                    "max_devices": payload.get("max_devices"), "exp": payload.get("exp"),
                    "token_sha256": hashlib.sha256(str(token).strip().encode("utf-8")).hexdigest()},
        "artifacts": {"client": _artifact(client_zip, len(entries)), "blender_addon": _artifact(addon_zip, len(addon_entries))},
        "vault": {"path": vault.VAULT_RELPATH.as_posix(), "files": sorted(vault_files), "bytes": len(vault_blob),
                  "sha256": hashlib.sha256(vault_blob).hexdigest()},
        "excluded": {"dev_paths": dev_relpaths(), "blender_addon": list(ADDON_FILES), "vendor_only": list(VENDOR_ONLY)},
        "watermark_channels": list(WATERMARK_CHANNELS),
        "fast_build": bool(fast_build),
        "checks": checks,
    }
    provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {**provenance, "client_zip": str(client_zip), "addon_zip": str(addon_zip),
            "provenance_path": str(provenance_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--token", default=os.environ.get("AGS_BUILD_TOKEN", ""),
                        help="Token AGS1 của đơn hàng (hoặc biến AGS_BUILD_TOKEN)")
    parser.add_argument("--order-id", default=None)
    parser.add_argument("--out", type=Path, default=DIST / CLIENT_ZIP_NAME)
    parser.add_argument("--fast", action="store_true", help="Bỏ bước giải nén + compileall + ags_setup.py --check")
    parser.add_argument("--license-url", default=os.environ.get("AGS_BUILD_LICENSE_URL", DEFAULT_LICENSE_URL),
                        help=f"Máy chủ sổ cái ghi vào .protected (mặc định AGS_BUILD_LICENSE_URL hoặc "
                             f"{DEFAULT_LICENSE_URL}; \"\" = bản không máy chủ)")
    args = parser.parse_args()
    if not args.token:
        sys.exit("❌ Cần --token (hoặc AGS_BUILD_TOKEN)")
    try:
        result = build_protected_bundle(args.out, order_id=args.order_id, token=args.token, fast_build=args.fast,
                                        license_url=args.license_url)
    except (BuildError, vault.VaultError) as error:
        sys.exit(f"❌ {error}")
    print(json.dumps(result, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

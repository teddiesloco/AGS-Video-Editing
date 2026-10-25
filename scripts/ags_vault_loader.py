#!/usr/bin/env python3
"""
AGS (Agent Space) — vault tài nguyên mẫu (rules, template CapCut, script bpy Blender); mã hoá AES-256-GCM (`cryptography`).

Cây dev (không có file `.protected`): read_asset đọc thẳng file nguồn theo DEV_PATHS.
Gói đã đóng (có `.protected`): kiểm dấu gốc (tài liệu + seal của `.protected`) + bản quyền client (`.protected` ghi
license_url hoặc AGS_LICENSE_URL khác rỗng thì thêm lease AGS-LEASE-V1 của máy
chủ sổ cái), dẫn khoá k_vault bằng HKDF-SHA256 từ payload_digest (đơn hàng chuẩn hoá) của token đã ký và release_salt
ghi trong vault, rồi mở `assets/vault.ags.enc` trong RAM.

Định dạng vault: header = b"AGSV2" | len(release_salt) (2 byte big-endian) | release_salt; tiếp theo là
AES-256-GCM(k_vault, nonce = SHA-256("AGS-NONCE:" + release_salt)[:12], aad = header) của zlib(JSON {tên: base64})
kèm tag 16 byte. Mỗi bản dựng dùng release_salt ngẫu nhiên nên (khoá, nonce) không lặp.
"""
import base64
import hashlib
import hmac
import json
import zlib
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import ags_client_license as lic

ROOT = Path(__file__).resolve().parent.parent
ERROR_CODE = "E-ags-anti-rea-shield-002"
MAGIC = b"AGSV2"
INFO = b"AGS-VAULT-V1"
NONCE_DOMAIN = b"AGS-NONCE:"
TAG_BYTES = 16
VAULT_RELPATH = Path("assets") / "vault.ags.enc"
REDACTED = "[REDACTED_VAULT_KEY]"

DEV_PATHS: Dict[str, Path] = {
    "rules/ags-editing-rules.json": ROOT.parent / "AGS-Auto-Editor" / "references" / "ags-editing-rules.json",
    "templates/ags_capcut_template.json": ROOT / "scripts" / "bds" / "ags_capcut_template.json",
    "blender/scene_bds.py": ROOT / "assets" / "blender" / "scene_bds.py",
    "blender/scene_isometric.py": ROOT / "assets" / "blender" / "scene_isometric.py",
    "blender/scene_product.py": ROOT / "assets" / "blender" / "scene_product.py",
}

_RAM_CACHE: Dict[Tuple[str, int, int, bytes], Dict[str, bytes]] = {}


class VaultError(PermissionError):
    def __init__(self, message: str, code: str = ERROR_CODE):
        self.code = code
        super().__init__(f"{code}: {message}")


def derive_vault_key(payload_digest: bytes, release_salt: bytes) -> bytes:
    """HKDF-SHA256 (RFC 5869): IKM = N công khai (256 byte) + payload_digest, info = AGS-VAULT-V1, 32 byte."""
    if not isinstance(payload_digest, (bytes, bytearray)) or len(payload_digest) != 32:
        raise VaultError("VAULT_KEY_INVALID — payload_digest phải là 32 byte SHA-256")
    ikm = lic.PUBLIC_N.to_bytes(256, "big") + bytes(payload_digest)
    prk = hmac.new(bytes(release_salt) or b"\x00" * 32, ikm, hashlib.sha256).digest()
    return hmac.new(prk, INFO + b"\x01", hashlib.sha256).digest()


def _nonce(release_salt: bytes) -> bytes:
    return hashlib.sha256(NONCE_DOMAIN + bytes(release_salt)).digest()[:12]


def seal_vault(files: Dict[str, bytes], k_vault: bytes, release_salt: bytes = b"") -> bytes:
    if len(release_salt) > 0xFFFF:
        raise VaultError("VAULT_SALT_INVALID — release_salt quá dài")
    doc = {name: base64.b64encode(bytes(data)).decode("ascii") for name, data in sorted(files.items())}
    compressed = zlib.compress(json.dumps(doc, separators=(",", ":")).encode("ascii"), 9)
    header = MAGIC + len(release_salt).to_bytes(2, "big") + bytes(release_salt)
    return header + AESGCM(bytes(k_vault)).encrypt(_nonce(release_salt), compressed, header)


def _split_vault(blob: bytes) -> Tuple[bytes, bytes, bytes]:
    """Trả (release_salt, header, bản mã kèm tag GCM); sai cấu trúc -> VaultError."""
    head = len(MAGIC) + 2
    if len(blob) < head + TAG_BYTES or blob[:len(MAGIC)] != MAGIC:
        raise VaultError("VAULT_HEADER_INVALID — vault hỏng hoặc không phải AGSV2")
    salt_end = head + int.from_bytes(blob[len(MAGIC):head], "big")
    if salt_end > len(blob) - TAG_BYTES:
        raise VaultError("VAULT_HEADER_INVALID — độ dài release_salt sai")
    return blob[head:salt_end], blob[:salt_end], blob[salt_end:]


def open_vault(blob: bytes, k_vault: bytes) -> Dict[str, bytes]:
    salt, header, body = _split_vault(bytes(blob))
    try:
        compressed = AESGCM(bytes(k_vault)).decrypt(_nonce(salt), body, header)
    except Exception:  # InvalidTag, khoá sai độ dài/kiểu
        raise VaultError("VAULT_TAG_MISMATCH — sai khoá bản quyền hoặc vault đã bị sửa") from None
    try:
        doc = json.loads(zlib.decompress(compressed).decode("ascii"))
        return {name: base64.b64decode(data, validate=True) for name, data in doc.items()}
    except (zlib.error, ValueError, AttributeError, TypeError) as error:
        raise VaultError(f"VAULT_PAYLOAD_INVALID — {error}") from None


def _base(root_dir: Optional[Path]) -> Path:
    return Path(root_dir).resolve() if root_dir else ROOT


def _verified_license(base: Path, license_path: Optional[Path]) -> Dict[str, Any]:
    token = lic._stored_token(license_path)
    if not token:
        raise VaultError(f"CLIENT_LICENSE_REQUIRED — chưa kích hoạt bản quyền trên máy này "
                         f"(machine_id {lic.get_machine_id()}); chạy `ags_setup.py --activate <TOKEN>`.")
    verified = lic.verify_license_token(token)
    if not verified.get("valid"):
        raise VaultError(f"CLIENT_LICENSE_INVALID — {verified.get('reason', 'token không hợp lệ')}")
    if not lic.verify_origin_seal(base, str(verified["payload"].get("vsec") or "")):
        raise VaultError("ORIGIN_SEAL_MISMATCH — tài liệu gói đã bị sửa so với bản phát hành của đơn hàng này")
    # Gói ghi license_url trong .protected (hoặc AGS_LICENSE_URL): bắt buộc lease hợp lệ; máy chủ từ chối / không với
    # tới mà không còn lease trong 72h ngoài mạng -> VaultError mang mã máy chủ (-003 hết ghế, -004 thu hồi).
    try:
        lease = lic._ensure_client_lease(token, verified, license_path, root_dir=base)
    except lic.LicenseServerError as error:
        raise VaultError(error.reason, error.code) from None
    return {**verified, "vault_lease": lease}


def _open_protected(base: Path, license_path: Optional[Path]) -> Tuple[Dict[str, bytes], Dict[str, Any]]:
    verified = _verified_license(base, license_path)
    vault_path = base / VAULT_RELPATH
    try:
        stat = vault_path.stat()
    except OSError:
        raise VaultError(f"VAULT_MISSING — không thấy {vault_path}") from None
    key = (str(vault_path), stat.st_mtime_ns, stat.st_size, bytes(verified.get("payload_digest") or b""))
    files = _RAM_CACHE.get(key)
    if files is None:
        blob = vault_path.read_bytes()
        release_salt = _split_vault(blob)[0]
        files = open_vault(blob, derive_vault_key(verified.get("payload_digest"), release_salt))
        _RAM_CACHE.clear()
        _RAM_CACHE[key] = files
    return files, verified


def read_asset(relpath: str, license_path: Optional[Path] = None, root_dir: Optional[Path] = None) -> bytes:
    base = _base(root_dir)
    if not (base / ".protected").exists():
        dev = DEV_PATHS.get(relpath)
        if dev is None:
            parts = Path(relpath).parts
            if Path(relpath).is_absolute() or ".." in parts or not parts:
                raise VaultError(f"ASSET_PATH_INVALID — {relpath!r}")
            dev = base / relpath
        return dev.read_bytes()
    files, _verified = _open_protected(base, license_path)
    if relpath not in files:
        raise VaultError(f"ASSET_NOT_IN_VAULT — {relpath!r}")
    return files[relpath]


def vault_status(license_path: Optional[Path] = None, root_dir: Optional[Path] = None) -> Dict[str, Any]:
    base = _base(root_dir)
    status: Dict[str, Any] = {"protected": (base / ".protected").exists(), "decrypted": False, "bound_devices": None,
                              "max_devices": None, "lease_expires": None, "order_id": None, "vault_key": REDACTED}
    if not status["protected"]:
        return status
    try:
        _files, verified = _open_protected(base, license_path)
    except PermissionError:
        return status
    payload = verified.get("payload") or {}
    lease = verified.get("vault_lease") or {}
    max_devices = lease.get("max_devices") if lease else payload.get("max_devices")
    order_id = payload.get("order_id")
    status.update(decrypted=True, bound_devices=lease.get("bound_devices"), lease_expires=lease.get("expires_at"),
                  max_devices=max_devices if isinstance(max_devices, int) else None,
                  order_id=str(order_id) if order_id else None)
    return status

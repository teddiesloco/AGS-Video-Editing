#!/usr/bin/env python3
"""
AGS (Agent Space) — khoá bản quyền client theo máy (chỉ dùng thư viện chuẩn Python 3.11).

Mã kích hoạt: AGS1.<payload_b64url>.<sig_b64url>; payload là JSON {"sub", "mid", "exp", "tier", "max_devices", "vsec"[, "order_id"]}
(vsec: bí mật theo đơn dẫn tất định từ khoá ký, đi vào payload_digest và muối dấu niêm của bản phát hành theo đơn).
Chữ ký RSA-2048 (e=65537) trên SHA-256("AGS-SEAT-V1:" + payload). Client chỉ chứa modulus công khai N;
khoá ký bí mật nằm ở ~/.ags/issuer_private_key.json của bên cấp mã, không bao giờ đi kèm skill.

  python scripts/ags_client_license.py machine-id
  python scripts/ags_client_license.py activate --token <TOKEN>
  python scripts/ags_client_license.py status
  python scripts/ags_client_license.py issue --sub <KHÁCH> --mid <MID|*> --days 365   (chỉ máy có khoá ký)

Bật cổng kiểm tra: AGS_REQUIRE_CLIENT_LICENSE=1 hoặc tạo file <thư mục skill>/.require_client_license.
Máy chủ sổ cái: "license_url" ghi sẵn trong `.protected` của gói đã đóng (niêm cùng tài liệu, sửa ->
ORIGIN_SEAL_MISMATCH); AGS_LICENSE_URL khác rỗng thì thắng (máy chủ staging/thử). Có máy chủ thì activate / mở vault
bắt buộc lease AGS-LEASE-V1 (RSA cùng khoá ký token), lưu `vault_lease` vào client_license.json; hết ghế / đã thu hồi
-> LicenseServerError E-ags-anti-rea-shield-003 / -004.

Dấu nguồn gốc tài liệu (HMAC-SHA256, bỏ qua dòng ghi chú cài đặt) và dấu đơn hàng trong bản phát hành
(ký tự zero-width, PNG tEXt "ags_order_id", trường extra ZIP 0x4741) dùng để truy vết bản bị phát tán.
"""
import argparse
import base64
import hashlib
import hmac
import http.client
import json
import os
import platform
import re
import struct
import sys
import time
import unicodedata
import uuid
import urllib.error
import urllib.request
import zipfile
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Tuple, Union

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_N_HEX = "65077c421eb5912f711b259fa51a3a875f8babf94e8206f33ff06e64955316da180c9db2fd0e51d0b9060bea7193c1a1d8d3ae5b378f52252905985dd37bc0bb678f2fcbabe6dccf0e424cf455f10ce48d62d6f766b5406a729c0b446987de7838f7040d0ca2128ff6ce4769f63113b4e624d68a33bbbc9ef9f33367eeddec0dbaea61b1ba99156357ef6efd24ce4d2b23f5e8d780f5bffddf527458a6c83a2281ffe08aed9f0504135f23aa1f051f5ac6956ff44a0e82937484902cf303592dd7b91df0a02e57b61b6e6ad349548e34e30871ce2415ce077cbe45514466cd532fcf14f254b0c56c13435979884381fd1190582955afa9768df8ff89e6504cfd"  # noqa: E501
PUBLIC_E = 65537
PUBLIC_N = int(PUBLIC_N_HEX, 16)
PREFIX = "AGS1"
DOMAIN = b"AGS-SEAT-V1:"
SIG_BYTES = 256
LEASE_SCHEMA = "AGS-LEASE-V1"
LEASE_DOMAIN = b"AGS-LEASE-V1:"
OFFLINE_GRACE_HOURS = 72
CLOCK_SKEW_SECONDS = 300
LICENSE_HTTP_TIMEOUT = 15
ERROR = "E-ags-reels-pipeline-007"
SHIELD_INVALID = "E-ags-anti-rea-shield-002"
TIER_MAX_DEVICES = {"creator": 1, "studio": 2, "agency": 5, "commercial": 1}
ORIGIN_SALT = b"AGS-ORIGIN-V1"
ORIGIN_SEAL_RE = re.compile(r"<!-- ags-origin-seal: ([0-9a-f]{64}) -->")
INSTALL_NOTE_PREFIXES = ("> Cài đặt tại:", "> Cài bởi `ags_setup.py --install-all-clients`")
ZW_FRAME, ZW_ZERO, ZW_ONE = "\u2060", "\u200b", "\u200c"
ZW_TAG_RE = re.compile(f"{ZW_FRAME}([{ZW_ZERO}{ZW_ONE}]+){ZW_FRAME}")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_ORDER_KEY = b"ags_order_id"
ZIP_EXTRA_ID = 0x4741
TEXT_SUFFIXES = {".md", ".txt", ".json", ".py", ".html", ".htm", ".js", ".ts", ".css", ".toml", ".yaml", ".yml",
                 ".csv", ".srt", ".ass", ".xml", ".svg"}
SKIP_DIRS = {"venv", ".venv", "node_modules", "__pycache__", ".git"}


def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _digest_int(payload_bytes: bytes) -> int:
    return int.from_bytes(hashlib.sha256(DOMAIN + payload_bytes).digest(), "big")


def _default_license_path() -> Path:
    return Path(os.environ.get("AGS_CLIENT_LICENSE_PATH", str(Path.home() / ".ags" / "client_license.json")))


def get_machine_id() -> str:
    raw = f"{platform.system()}:{platform.machine()}:{uuid.getnode()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def tier_max_devices(tier: str) -> int:
    return TIER_MAX_DEVICES.get(tier, 1)


def issue_license_token(sub: str, mid: str = "*", days: int = 365, tier: str = "commercial",
                        issuer_key_path: Optional[Path] = None, order_id: str = "",
                        max_devices: Optional[int] = None) -> str:
    key_path = Path(issuer_key_path) if issuer_key_path else Path.home() / ".ags" / "issuer_private_key.json"
    if not key_path.exists():
        raise FileNotFoundError(f"Không có khoá ký {key_path} — chỉ bên cấp mã mới phát hành được token.")
    seats = tier_max_devices(tier) if max_devices is None else int(max_devices)
    if seats < 1:
        raise ValueError("max_devices phải ≥ 1")
    key = json.loads(key_path.read_text(encoding="utf-8"))
    d = int(key["d_hex"], 16)
    # Bí mật theo đơn, tất định: cấp lại cùng (order_id|sub, tier) ra cùng vsec -> cùng payload_digest.
    vsec = hmac.new(d.to_bytes((d.bit_length() + 7) // 8, "big"),
                    f"ags-order-vsec:{order_id or sub}:{tier}".encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    payload = {"sub": sub, "mid": mid, "exp": int(time.time() + days * 86400), "tier": tier, "max_devices": seats,
               "vsec": vsec}
    if order_id:
        payload["order_id"] = str(order_id)
    payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    sig_int = pow(_digest_int(payload_bytes), d, int(key["n_hex"], 16))
    return f"{PREFIX}.{_b64e(payload_bytes)}.{_b64e(sig_int.to_bytes(SIG_BYTES, 'big'))}"


def _invalid(reason: str) -> Dict[str, Any]:
    return {"valid": False, "reason": reason, "error_code": SHIELD_INVALID}


def order_digest(payload: Dict[str, Any]) -> bytes:
    """SHA-256 trên đơn hàng chuẩn hoá (order_id|sub, tier, vsec): token cấp lại cho cùng đơn (exp/mid mới) giữ nguyên
    digest; vsec (bí mật theo đơn dẫn từ khoá ký) khiến digest không đoán được từ order_id công khai."""
    canonical = {"order_id": payload.get("order_id") or payload.get("sub"), "tier": payload.get("tier", "commercial"),
                 "vsec": payload.get("vsec", "")}
    data = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(DOMAIN + data).digest()


def verify_license_token(token: str, current_machine_id: Optional[str] = None) -> Dict[str, Any]:
    try:
        prefix, payload_part, sig_part = str(token).strip().split(".")
        if prefix != PREFIX:
            return _invalid("sai định dạng token (thiếu tiền tố AGS1)")
        payload_bytes, sig_int = _b64d(payload_part), int.from_bytes(_b64d(sig_part), "big")
    except (ValueError, TypeError):
        return _invalid("sai định dạng token")
    if not 0 < sig_int < PUBLIC_N or pow(sig_int, PUBLIC_E, PUBLIC_N) != _digest_int(payload_bytes):
        return _invalid("chữ ký không hợp lệ")
    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
        exp, mid = payload["exp"], payload["mid"]
    except (ValueError, KeyError, TypeError):
        return _invalid("payload không hợp lệ")
    if not isinstance(exp, int) or exp <= time.time():
        return _invalid("token đã hết hạn")
    machine_id = current_machine_id or get_machine_id()
    if mid not in ("*", machine_id):
        return _invalid(f"token cấp cho máy khác (máy này: {machine_id})")
    return {"valid": True, "payload": payload, "machine_id": machine_id, "payload_digest": order_digest(payload)}


def lease_digest_int(lease: Dict[str, Any]) -> int:
    body = {k: v for k, v in lease.items() if k != "sig"}
    data = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return int.from_bytes(hashlib.sha256(LEASE_DOMAIN + data).digest(), "big")


def verify_cached_lease(lease_dict: Any, now_ts: Optional[float] = None) -> Dict[str, Any]:
    """Chữ ký RSA của máy chủ đúng và lease còn hạn -> "online"; hết hạn nhưng trong 72h -> "offline_grace"."""
    now = time.time() if now_ts is None else float(now_ts)
    if not isinstance(lease_dict, dict) or lease_dict.get("schema") != LEASE_SCHEMA:
        return _invalid("LEASE_INVALID")
    try:
        sig_int = int.from_bytes(_b64d(lease_dict["sig"]), "big")
        digest_int = lease_digest_int(lease_dict)
    except (KeyError, TypeError, ValueError):
        return _invalid("LEASE_TAMPERED")
    if not 0 < sig_int < PUBLIC_N or pow(sig_int, PUBLIC_E, PUBLIC_N) != digest_int:
        return _invalid("LEASE_TAMPERED")
    try:
        issued, expires = int(lease_dict["issued_ts"]), int(lease_dict["expires_ts"])
        grace = min(int(lease_dict.get("offline_grace_hours", OFFLINE_GRACE_HOURS)), OFFLINE_GRACE_HOURS) * 3600
    except (KeyError, TypeError, ValueError):
        return _invalid("LEASE_INVALID")
    if now + CLOCK_SKEW_SECONDS < issued:
        return _invalid("CLOCK_ROLLBACK")
    offline_deadline = datetime.fromtimestamp(expires + grace, timezone.utc).isoformat()
    base = {"valid": True, "order_id": lease_dict.get("order_id", ""), "machine_id": lease_dict.get("machine_id"),
            "lease_expires": lease_dict.get("expires_at"), "offline_deadline": offline_deadline}
    if now <= expires:
        return {**base, "state": "online", "grace_remaining_seconds": grace}
    if now <= expires + grace:
        return {**base, "state": "offline_grace", "grace_remaining_seconds": int(expires + grace - now)}
    return _invalid("LEASE_EXPIRED")


def _printable(res: Dict[str, Any]) -> Dict[str, Any]:
    """Bỏ payload_digest (32 byte, nguyên liệu dẫn khoá vault) khỏi kết quả in ra JSON."""
    return {k: v for k, v in res.items() if k != "payload_digest"}


def _license_path(license_path: Optional[Path]) -> Path:
    return Path(license_path) if license_path else _default_license_path()


def _read_record(path: Path) -> Dict[str, Any]:
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return record if isinstance(record, dict) else {}


def _write_record(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2)
    os.chmod(path, 0o600)


class LicenseServerError(PermissionError):
    """Máy chủ sổ cái từ chối / không với tới / lease không dùng được; `code` là error_code (-002 / -003 / -004)."""

    def __init__(self, code: str, reason: str):
        self.code, self.reason = code, reason
        super().__init__(f"{code}: {reason}")


def _license_server_url(root_dir: Optional[Path] = None) -> str:
    """AGS_LICENSE_URL khác rỗng (máy chủ staging/thử) thắng; không thì "license_url" ghi trong
    `<root_dir|ROOT>/.protected` của gói đã đóng (rỗng thì không gọi máy chủ); không có thì ""."""
    url = _read_record(Path(root_dir or ROOT) / ".protected").get("license_url")
    marker_url = url.strip().rstrip("/") if isinstance(url, str) else ""
    return os.environ.get("AGS_LICENSE_URL", "").strip().rstrip("/") or marker_url


def check_vault_lease(lease: Any, verified: Dict[str, Any], now_ts: Optional[float] = None) -> Dict[str, Any]:
    """verify_cached_lease + lease phải cấp cho đúng đơn hàng (payload_digest) và đúng máy của token đã kiểm."""
    res = verify_cached_lease(lease, now_ts)
    if res["valid"] and (lease.get("license_id") != verified["payload_digest"].hex()
                         or res["machine_id"] != verified["machine_id"]):
        return _invalid("LEASE_MISMATCH")
    return res


def _post_lease(url: str, token: str, verified: Dict[str, Any], route: str) -> Dict[str, Any]:
    """POST <url>/api/v1/license/<route>: 403 -> LicenseServerError mang error_code máy chủ; mất mạng -> OSError."""
    body = json.dumps({"token": token, "machine_id": verified["machine_id"]}).encode("utf-8")
    request = urllib.request.Request(f"{url}/api/v1/license/{route}", data=body,
                                     headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=LICENSE_HTTP_TIMEOUT) as resp:
            reply = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.code != 403:
            raise OSError(f"máy chủ bản quyền trả HTTP {error.code}") from None
        try:
            reply = json.loads(error.read().decode("utf-8"))
        except (OSError, ValueError):
            reply = {}
        reply = reply if isinstance(reply, dict) else {}
        detail = f" — {reply['detail']}" if reply.get("detail") else ""
        raise LicenseServerError(str(reply.get("error_code") or SHIELD_INVALID),
                                 f"{reply.get('reason') or 'LICENSE_DENIED'}{detail}") from None
    except (ValueError, http.client.HTTPException) as error:
        raise OSError(f"máy chủ bản quyền trả dữ liệu hỏng: {error}") from None
    data = reply.get("data") if isinstance(reply, dict) else None
    lease = data.get("vault_lease") if isinstance(data, dict) else None
    checked = check_vault_lease(lease, verified)
    if checked.get("state") != "online":
        raise LicenseServerError(SHIELD_INVALID, f"LEASE_INVALID — lease máy chủ trả về không dùng được "
                                                 f"({checked.get('reason', checked.get('state'))})")
    return lease


def _ensure_client_lease(token: str, verified: Dict[str, Any], license_path: Optional[Path] = None,
                         root_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Lease cho vault. Không có _license_server_url(root_dir): trả lease đã lưu nếu còn hợp lệ (không thì None).
    Có: BẮT BUỘC lease hợp lệ — lease đã lưu còn "online" cho đúng đơn/máy thì dùng luôn (thu hồi có hiệu lực khi gia
    hạn, tối đa sau 24h); không thì POST /api/v1/license/lease và lưu vào client_license.json. 403 -> xoá lease đã lưu,
    LicenseServerError mã máy chủ (-003 hết ghế, -004 đã thu hồi); mất mạng -> lease đã lưu trong 72h ngoài mạng,
    không có thì LicenseServerError LEASE_SERVER_UNREACHABLE."""
    path = _license_path(license_path)
    record = _read_record(path)
    cached = record.get("vault_lease")
    state = check_vault_lease(cached, verified)
    url = _license_server_url(root_dir)
    if not url:
        return cached if state["valid"] else None
    if state.get("state") == "online":
        return cached
    try:
        lease = _post_lease(url, token, verified, "lease")
    except LicenseServerError:
        if record.pop("vault_lease", None) is not None:
            _write_record(path, record)
        raise
    except OSError as error:
        if state["valid"]:
            return cached
        raise LicenseServerError(SHIELD_INVALID, f"LEASE_SERVER_UNREACHABLE — {error} ({state['reason']})") from None
    record["vault_lease"] = lease
    _write_record(path, record)
    return lease


def activate_license_token(token: str, license_path: Optional[Path] = None,
                           root_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Lưu token vào client_license.json. Có _license_server_url(root_dir): bắt buộc lease từ máy chủ; mất mạng thì chỉ
    giữ lease đã lưu còn hợp lệ cho đúng đơn/máy (72h ngoài mạng), chưa có -> LEASE_SERVER_UNREACHABLE."""
    token = str(token).strip()
    res = verify_license_token(token)
    if not res["valid"]:
        raise PermissionError(f"{ERROR}: CLIENT_LICENSE_INVALID — {res['reason']}")
    path = _license_path(license_path)
    record = {"token": token, "activated_at": int(time.time()), "machine_id": res["machine_id"],
              "payload": res["payload"]}
    url = _license_server_url(root_dir)
    if url:
        try:
            record["vault_lease"] = _post_lease(url, token, res, "activate")
        except LicenseServerError:  # PermissionError là OSError: 403 (-003 / -004) không được rơi vào nhánh mất mạng
            raise
        except OSError as error:
            cached = _read_record(path).get("vault_lease")
            if not check_vault_lease(cached, res)["valid"]:
                raise LicenseServerError(SHIELD_INVALID, f"LEASE_SERVER_UNREACHABLE — {error}") from None
            record["vault_lease"] = cached
    _write_record(path, record)
    out = {**_printable(res), "license_path": str(path)}
    if "vault_lease" in record:
        out["vault_lease"] = record["vault_lease"]
    return out


def _stored_token(license_path: Optional[Path] = None) -> str:
    token = os.environ.get("AGS_CLIENT_LICENSE_TOKEN", "").strip()
    if token:
        return token
    return str(_read_record(_license_path(license_path)).get("token", "")).strip()


def license_required() -> bool:
    flag = str(os.environ.get("AGS_REQUIRE_CLIENT_LICENSE", "")).strip().lower() in {"1", "true", "yes"}
    return flag or (ROOT / ".require_client_license").exists()


def assert_client_licensed(license_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    if not license_required():
        return None
    token = _stored_token(license_path)
    if not token:
        raise PermissionError(f"{ERROR}: CLIENT_LICENSE_REQUIRED — chưa kích hoạt bản quyền trên máy này "
                              f"(machine_id {get_machine_id()}); chạy `ags_setup.py --activate <TOKEN>`.")
    res = verify_license_token(token)
    if not res["valid"]:
        raise PermissionError(f"{ERROR}: CLIENT_LICENSE_REQUIRED — {res['reason']}")
    return res


def license_status(license_path: Optional[Path] = None) -> Dict[str, Any]:
    token = _stored_token(license_path)
    res = verify_license_token(token) if token else {"valid": False, "reason": "chưa kích hoạt"}
    return {"machine_id": get_machine_id(), "required": license_required(), **_printable(res)}


def deriveOriginSeal(doc_bytes: bytes, salt: bytes = ORIGIN_SALT) -> str:  # noqa: N802 (tên theo đặc tả)
    return hmac.new(salt, doc_bytes, hashlib.sha256).hexdigest()


def _is_seal_line(line: str) -> bool:
    return ORIGIN_SEAL_RE.fullmatch(line.strip()) is not None


def _origin_canonical(text: str) -> bytes:
    """Nội dung được niêm: bỏ dòng dấu niêm và dòng ghi chú do trình cài đặt chèn (đường dẫn khác nhau mỗi máy)."""
    kept = []
    for line in text.splitlines(keepends=True):
        bare = unicodedata.normalize("NFC", line.lstrip("\ufeff").strip())
        if _is_seal_line(bare) or bare.startswith(INSTALL_NOTE_PREFIXES):
            continue
        kept.append(line)
    return "".join(kept).rstrip().encode("utf-8")


def origin_salt(vsec: str = "") -> bytes:
    """Muối dấu niêm: ORIGIN_SALT, thêm vsec của đơn hàng khi có (bản phát hành theo đơn)."""
    return ORIGIN_SALT + b":" + vsec.encode("utf-8") if vsec else ORIGIN_SALT


def embed_origin_seal(text: str, vsec: str = "") -> str:
    base = "".join(line for line in text.splitlines(keepends=True) if not _is_seal_line(line))
    seal = deriveOriginSeal(_origin_canonical(base), origin_salt(vsec))
    return f"{base.rstrip(chr(10))}\n\n<!-- ags-origin-seal: {seal} -->\n"


def seal_protected_marker(marker: Dict[str, Any], vsec: str = "") -> Dict[str, Any]:
    """`.protected` kèm "seal" = deriveOriginSeal(JSON chuẩn hoá của các trường còn lại, origin_salt(vsec))."""
    body = {k: v for k, v in marker.items() if k != "seal"}
    data = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return {**body, "seal": deriveOriginSeal(data, origin_salt(vsec))}


def _walk_files(root: Path) -> Iterator[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file() and not SKIP_DIRS.intersection(path.relative_to(root).parts[:-1]):
            yield path


def verify_origin_seal(root_dir: Path, vsec: str = "") -> bool:
    """True khi có ít nhất một file .md mang dấu niêm, mọi dấu niêm đều khớp nội dung (muối origin_salt(vsec)) và — nếu có
    `.protected` — "seal" của nó khớp các trường còn lại (sửa license_url / order_id -> False)."""
    salt = origin_salt(vsec)
    marker_path = Path(root_dir) / ".protected"
    if marker_path.exists():
        marker = _read_record(marker_path)
        expected = seal_protected_marker(marker, vsec)["seal"].encode("ascii")
        if not hmac.compare_digest(str(marker.get("seal", "")).encode("utf-8"), expected):
            return False
    sealed = 0
    for path in _walk_files(Path(root_dir)):
        if path.suffix.lower() != ".md":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        seals = ORIGIN_SEAL_RE.findall(text)
        if not seals:
            continue
        sealed += 1
        expected = deriveOriginSeal(_origin_canonical(text), salt)
        if any(not hmac.compare_digest(seal, expected) for seal in seals):
            return False
    return sealed > 0


def encode_zw_tag(order_id: str) -> str:
    bits = "".join(f"{byte:08b}" for byte in str(order_id).encode("utf-8"))
    return ZW_FRAME + bits.translate(str.maketrans("01", ZW_ZERO + ZW_ONE)) + ZW_FRAME


def decode_zw_tag(text: str) -> Optional[str]:
    for match in ZW_TAG_RE.finditer(text):
        bits = match.group(1).translate(str.maketrans(ZW_ZERO + ZW_ONE, "01"))
        if len(bits) % 8:
            continue
        try:
            return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8)).decode("utf-8")
        except UnicodeDecodeError:
            continue
    return None


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def build_badge_png(order_id: str, size: int = 16, rgb: Tuple[int, int, int] = (0x1F, 0x6F, 0x3D)) -> bytes:
    """PNG RGB đặc màu (mặc định --signal) mang tEXt "ags_order_id" (tEXt là Latin-1)."""
    text = str(order_id).encode("latin-1")
    row = b"\x00" + bytes(rgb) * size
    return (PNG_SIGNATURE
            + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + _png_chunk(b"tEXt", PNG_ORDER_KEY + b"\x00" + text)
            + _png_chunk(b"IDAT", zlib.compress(row * size, 9))
            + _png_chunk(b"IEND", b""))


def _png_order_id(data: bytes) -> Optional[str]:
    if not data.startswith(PNG_SIGNATURE):
        return None
    pos = len(PNG_SIGNATURE)
    while pos + 8 <= len(data):
        length, kind = struct.unpack_from(">I4s", data, pos)
        body = data[pos + 8:pos + 8 + length]
        if kind == b"tEXt":
            key, _, value = body.partition(b"\x00")
            if key == PNG_ORDER_KEY:
                return value.decode("latin-1")
        if kind == b"IEND":
            break
        pos += 12 + length
    return None


def build_zip_extra_0x4741(order_id: str) -> bytes:
    data = str(order_id).encode("utf-8")
    if len(data) > 0xFFFF:
        raise ValueError("order_id quá dài cho trường extra ZIP")
    return struct.pack("<HH", ZIP_EXTRA_ID, len(data)) + data


def _zip_extra_order_id(extra: bytes) -> Optional[str]:
    pos = 0
    while pos + 4 <= len(extra):
        header_id, size = struct.unpack_from("<HH", extra, pos)
        if header_id == ZIP_EXTRA_ID:
            return extra[pos + 4:pos + 4 + size].decode("utf-8", "replace")
        pos += 4 + size
    return None


def _member_order_id(name: str, data: bytes) -> Optional[str]:
    suffix = Path(name).suffix.lower()
    if suffix == ".png":
        return _png_order_id(data)
    if suffix in TEXT_SUFFIXES:
        return decode_zw_tag(data.decode("utf-8", "ignore"))
    return None


def _zip_order_id(archive: zipfile.ZipFile) -> Optional[str]:
    infos = archive.infolist()
    for info in infos:
        found = _zip_extra_order_id(info.extra)
        if found:
            return found
    for info in infos:
        if not info.is_dir():
            found = _member_order_id(info.filename, archive.read(info))
            if found:
                return found
    return None


def verify_leak_watermark(zip_or_path: Union[str, Path, zipfile.ZipFile]) -> Optional[str]:
    """Mã đơn hàng đọc được từ bất kỳ kênh nào (extra ZIP 0x4741, PNG tEXt, zero-width) trong zip/thư mục/file."""
    if isinstance(zip_or_path, zipfile.ZipFile):
        return _zip_order_id(zip_or_path)
    path = Path(zip_or_path)
    if path.is_dir():
        for file in _walk_files(path):
            found = verify_leak_watermark(file)
            if found:
                return found
        return None
    if not path.is_file():
        return None
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            return _zip_order_id(archive)
    return _member_order_id(path.name, path.read_bytes())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("machine-id", help="In mã máy (gửi cho bên cấp mã)")
    act = sub.add_parser("activate", help="Kích hoạt token trên máy này")
    act.add_argument("--token", required=True)
    sub.add_parser("status", help="Trạng thái bản quyền (JSON)")
    iss = sub.add_parser("issue", help="Cấp token (cần khoá ký bí mật)")
    iss.add_argument("--sub", required=True)
    iss.add_argument("--mid", default="*")
    iss.add_argument("--days", type=int, default=365)
    iss.add_argument("--tier", default="commercial", choices=sorted(TIER_MAX_DEVICES))
    iss.add_argument("--order-id", default="")
    iss.add_argument("--max-devices", type=int, default=None)
    iss.add_argument("--key", type=Path, default=None, help="Đường dẫn khoá ký (mặc định ~/.ags/issuer_private_key.json)")
    args = parser.parse_args()
    if args.cmd == "machine-id":
        print(get_machine_id())
    elif args.cmd == "activate":
        try:
            res = activate_license_token(args.token)
        except PermissionError as error:
            sys.exit(str(error))
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.cmd == "status":
        res = license_status()
        print(json.dumps(res, ensure_ascii=False, indent=2))
        sys.exit(0 if res["valid"] else 1)
    else:
        print(issue_license_token(args.sub, args.mid, args.days, args.tier, args.key, args.order_id,
                                  args.max_devices))


if __name__ == "__main__":
    main()

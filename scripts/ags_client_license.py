#!/usr/bin/env python3
"""
AGS (Agent Space) — khoá bản quyền client theo máy (chỉ dùng thư viện chuẩn Python 3.11).

Mã kích hoạt: AGS1.<payload_b64url>.<sig_b64url>; payload là JSON {"sub", "mid", "exp", "tier"}.
Chữ ký RSA-2048 (e=65537) trên SHA-256("AGS-SEAT-V1:" + payload). Client chỉ chứa modulus công khai N;
khoá ký bí mật nằm ở ~/.ags/issuer_private_key.json của bên cấp mã, không bao giờ đi kèm skill.

  python scripts/ags_client_license.py machine-id
  python scripts/ags_client_license.py activate --token <TOKEN>
  python scripts/ags_client_license.py status
  python scripts/ags_client_license.py issue --sub <KHÁCH> --mid <MID|*> --days 365   (chỉ máy có khoá ký)

Bật cổng kiểm tra: AGS_REQUIRE_CLIENT_LICENSE=1 hoặc tạo file <thư mục skill>/.require_client_license.
"""
import argparse
import base64
import hashlib
import json
import os
import platform
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_N_HEX = "65077c421eb5912f711b259fa51a3a875f8babf94e8206f33ff06e64955316da180c9db2fd0e51d0b9060bea7193c1a1d8d3ae5b378f52252905985dd37bc0bb678f2fcbabe6dccf0e424cf455f10ce48d62d6f766b5406a729c0b446987de7838f7040d0ca2128ff6ce4769f63113b4e624d68a33bbbc9ef9f33367eeddec0dbaea61b1ba99156357ef6efd24ce4d2b23f5e8d780f5bffddf527458a6c83a2281ffe08aed9f0504135f23aa1f051f5ac6956ff44a0e82937484902cf303592dd7b91df0a02e57b61b6e6ad349548e34e30871ce2415ce077cbe45514466cd532fcf14f254b0c56c13435979884381fd1190582955afa9768df8ff89e6504cfd"  # noqa: E501
PUBLIC_E = 65537
PUBLIC_N = int(PUBLIC_N_HEX, 16)
PREFIX = "AGS1"
DOMAIN = b"AGS-SEAT-V1:"
SIG_BYTES = 256
ERROR = "E-ags-reels-pipeline-007"


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


def issue_license_token(sub: str, mid: str = "*", days: int = 365, tier: str = "commercial",
                        issuer_key_path: Optional[Path] = None) -> str:
    key_path = Path(issuer_key_path) if issuer_key_path else Path.home() / ".ags" / "issuer_private_key.json"
    if not key_path.exists():
        raise FileNotFoundError(f"Không có khoá ký {key_path} — chỉ bên cấp mã mới phát hành được token.")
    key = json.loads(key_path.read_text(encoding="utf-8"))
    payload = {"sub": sub, "mid": mid, "exp": int(time.time() + days * 86400), "tier": tier}
    payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    sig_int = pow(_digest_int(payload_bytes), int(key["d_hex"], 16), int(key["n_hex"], 16))
    return f"{PREFIX}.{_b64e(payload_bytes)}.{_b64e(sig_int.to_bytes(SIG_BYTES, 'big'))}"


def verify_license_token(token: str, current_machine_id: Optional[str] = None) -> Dict[str, Any]:
    try:
        prefix, payload_part, sig_part = str(token).strip().split(".")
        if prefix != PREFIX:
            return {"valid": False, "reason": "sai định dạng token (thiếu tiền tố AGS1)"}
        payload_bytes, sig_int = _b64d(payload_part), int.from_bytes(_b64d(sig_part), "big")
    except (ValueError, TypeError):
        return {"valid": False, "reason": "sai định dạng token"}
    if not 0 < sig_int < PUBLIC_N or pow(sig_int, PUBLIC_E, PUBLIC_N) != _digest_int(payload_bytes):
        return {"valid": False, "reason": "chữ ký không hợp lệ"}
    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
        exp, mid = payload["exp"], payload["mid"]
    except (ValueError, KeyError, TypeError):
        return {"valid": False, "reason": "payload không hợp lệ"}
    if not isinstance(exp, int) or exp <= time.time():
        return {"valid": False, "reason": "token đã hết hạn"}
    machine_id = current_machine_id or get_machine_id()
    if mid not in ("*", machine_id):
        return {"valid": False, "reason": f"token cấp cho máy khác (máy này: {machine_id})"}
    return {"valid": True, "payload": payload, "machine_id": machine_id}


def activate_license_token(token: str, license_path: Optional[Path] = None) -> Dict[str, Any]:
    token = str(token).strip()
    res = verify_license_token(token)
    if not res["valid"]:
        raise PermissionError(f"{ERROR}: CLIENT_LICENSE_INVALID — {res['reason']}")
    path = Path(license_path) if license_path else _default_license_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"token": token, "activated_at": int(time.time()), "machine_id": get_machine_id(),
              "payload": res["payload"]}
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2)
    os.chmod(path, 0o600)
    return {**res, "license_path": str(path)}


def _stored_token(license_path: Optional[Path] = None) -> str:
    token = os.environ.get("AGS_CLIENT_LICENSE_TOKEN", "").strip()
    if token:
        return token
    path = Path(license_path) if license_path else _default_license_path()
    try:
        return str(json.loads(path.read_text(encoding="utf-8")).get("token", "")).strip()
    except (OSError, ValueError, AttributeError):
        return ""


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
    return {"machine_id": get_machine_id(), "required": license_required(), **res}


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
    iss.add_argument("--tier", default="commercial")
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
        print(issue_license_token(args.sub, args.mid, args.days, args.tier, args.key))


if __name__ == "__main__":
    main()

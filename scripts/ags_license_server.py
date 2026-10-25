#!/usr/bin/env python3
"""
AGS (Agent Space) — sổ cái bản quyền theo ghế (seat) + cấp lease 24h (chỉ thư viện chuẩn Python 3.11).

  POST /api/v1/license/activate   {"token", "machine_id"}  -> gắn máy vào token, cấp lease AGS-LEASE-V1
  POST /api/v1/license/lease      {"token", "machine_id"}  -> gia hạn lease (cùng luật ghế)
  POST /api/v1/license/revoke     {"token"} | {"order_id"} -> thu hồi (Authorization: Bearer <admin_token>)

Lỗi: token sai/hết hạn/sai máy -> 403 E-ags-anti-rea-shield-002; đã thu hồi -> 403 E-ags-anti-rea-shield-004
(LICENSE_REVOKED); hết ghế -> 403 E-ags-anti-rea-shield-003 (MAX_DEVICES_EXCEEDED).
Lease có hiệu lực 24h, client được dùng tiếp tối đa 72h ngoài mạng sau khi lease hết hạn
(ags_client_license.verify_cached_lease). Trường "sig" của lease là chữ ký RSA trên SHA-256("AGS-LEASE-V1:" + lease)
bằng cùng khoá ký token (issuer_key_path, mặc định ~/.ags/issuer_private_key.json); client kiểm bằng PUBLIC_N.

  AGS_LICENSE_ADMIN_TOKEN=... python scripts/ags_license_server.py --db ~/.ags/license_ledger.db --port 8787 \
      [--issuer-key ~/.ags/issuer_private_key.json]
"""
import argparse
import hmac
import json
import os
import secrets
import sqlite3
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ags_client_license as lic  # noqa: E402

LEASE_SCHEMA = lic.LEASE_SCHEMA
LEASE_SECONDS = 24 * 3600
OFFLINE_GRACE_HOURS = lic.OFFLINE_GRACE_HOURS
MAX_BODY_BYTES = 64 * 1024
MAX_MACHINE_ID_LEN = 128
E_INVALID = "E-ags-anti-rea-shield-002"
E_SEATS = "E-ags-anti-rea-shield-003"
E_REVOKED = "E-ags-anti-rea-shield-004"
CANARY_CHANNELS = ["unicode_zw", "png_text", "zip_0x4741"]

Response = Tuple[int, Dict[str, Any]]

SCHEMA = """
CREATE TABLE IF NOT EXISTS licenses (
    license_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL DEFAULT '',
    sub TEXT NOT NULL DEFAULT '',
    tier TEXT NOT NULL DEFAULT '',
    max_devices INTEGER NOT NULL,
    exp INTEGER NOT NULL DEFAULT 0,
    revoked INTEGER NOT NULL DEFAULT 0,
    revoked_at TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS licenses_order_id ON licenses(order_id);
CREATE TABLE IF NOT EXISTS license_devices (
    license_id TEXT NOT NULL REFERENCES licenses(license_id),
    machine_id TEXT NOT NULL,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    PRIMARY KEY (license_id, machine_id)
);
CREATE TABLE IF NOT EXISTS license_leases (
    lease_id TEXT PRIMARY KEY,
    license_id TEXT NOT NULL REFERENCES licenses(license_id),
    machine_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    issued_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
"""


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(int(ts), timezone.utc).isoformat()


def _fail(status: int, error_code: str, reason: str, detail: str = "") -> Response:
    body: Dict[str, Any] = {"ok": False, "error_code": error_code, "reason": reason}
    if detail:
        body["detail"] = detail
    return status, body


class LicenseLedgerService:
    def __init__(self, db_path: Path, admin_token: Optional[str] = None, issuer_key_path: Optional[Path] = None):
        key_path = Path(issuer_key_path) if issuer_key_path else Path.home() / ".ags" / "issuer_private_key.json"
        if not key_path.exists():
            raise FileNotFoundError(f"Không có khoá ký {key_path} — máy chủ cần khoá này để ký lease.")
        key = json.loads(key_path.read_text(encoding="utf-8"))
        self._sign_n, self._sign_d = int(key["n_hex"], 16), int(key["d_hex"], 16)
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.admin_token = admin_token or None
        self._lock = threading.Lock()
        self._db = sqlite3.connect(str(self.db_path), check_same_thread=False, isolation_level=None)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.executescript(SCHEMA)

    def close(self) -> None:
        with self._lock:
            self._db.close()

    def _sign_lease(self, lease: Dict[str, Any]) -> str:
        sig_int = pow(lic.lease_digest_int(lease), self._sign_d, self._sign_n)
        return lic._b64e(sig_int.to_bytes(lic.SIG_BYTES, "big"))

    # ---- nghiệp vụ ----
    def activate(self, token: Any, machine_id: Any) -> Response:
        return self._claim(token, machine_id, "activate")

    def lease(self, token: Any, machine_id: Any) -> Response:
        return self._claim(token, machine_id, "lease")

    def _claim(self, token: Any, machine_id: Any, kind: str) -> Response:
        if not isinstance(machine_id, str) or not 0 < len(machine_id.strip()) <= MAX_MACHINE_ID_LEN:
            return _fail(400, E_INVALID, "BAD_REQUEST", "machine_id phải là chuỗi 1-128 ký tự")
        machine_id = machine_id.strip()
        res = lic.verify_license_token(token if isinstance(token, str) else "", machine_id)
        if not res["valid"]:
            return _fail(403, E_INVALID, "LICENSE_INVALID", res["reason"])
        payload, license_id = res["payload"], res["payload_digest"].hex()
        order_id = str(payload.get("order_id", ""))
        tier = str(payload.get("tier", ""))
        max_devices = int(payload.get("max_devices") or lic.tier_max_devices(tier))
        now = time.time()
        now_iso, expires_iso = _iso(now), _iso(now + LEASE_SECONDS)
        with self._lock:
            db = self._db
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute("INSERT OR IGNORE INTO licenses (license_id, order_id, sub, tier, max_devices, exp, "
                           "created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (license_id, order_id, str(payload.get("sub", "")), tier, max_devices,
                            int(payload["exp"]), now_iso))
                revoked = db.execute("SELECT 1 FROM licenses WHERE revoked = 1 AND (license_id = ? OR "
                                     "(order_id != '' AND order_id = ?)) LIMIT 1", (license_id, order_id)).fetchone()
                if revoked:
                    db.execute("COMMIT")
                    return _fail(403, E_REVOKED, "LICENSE_REVOKED")
                bound = [row[0] for row in db.execute(
                    "SELECT machine_id FROM license_devices WHERE license_id = ?", (license_id,))]
                if machine_id not in bound and len(bound) >= max_devices:
                    db.execute("COMMIT")
                    return _fail(403, E_SEATS, "MAX_DEVICES_EXCEEDED",
                                 f"đã gắn {len(bound)}/{max_devices} máy")
                if machine_id in bound:
                    db.execute("UPDATE license_devices SET last_seen = ? WHERE license_id = ? AND machine_id = ?",
                               (now_iso, license_id, machine_id))
                else:
                    db.execute("INSERT INTO license_devices (license_id, machine_id, first_seen, last_seen) "
                               "VALUES (?, ?, ?, ?)", (license_id, machine_id, now_iso, now_iso))
                    bound.append(machine_id)
                remaining = max(0, max_devices - len(bound))
                lease = {"schema": LEASE_SCHEMA, "lease_id": secrets.token_hex(16), "license_id": license_id,
                         "order_id": order_id, "sub": str(payload.get("sub", "")), "tier": tier,
                         "machine_id": machine_id, "issued_at": now_iso, "expires_at": expires_iso,
                         "issued_ts": int(now), "expires_ts": int(now) + LEASE_SECONDS,
                         "offline_grace_hours": OFFLINE_GRACE_HOURS, "max_devices": max_devices,
                         "bound_devices": len(bound), "remaining_devices": remaining}
                lease["sig"] = self._sign_lease(lease)
                db.execute("INSERT INTO license_leases (lease_id, license_id, machine_id, kind, issued_at, "
                           "expires_at) VALUES (?, ?, ?, ?, ?, ?)",
                           (lease["lease_id"], license_id, machine_id, kind, now_iso, expires_iso))
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise
        return 200, {"ok": True, "data": {
            "vault_lease": lease,
            "canary_seal": {"order_id": order_id, "channels": list(CANARY_CHANNELS)},
            "bound_devices": len(bound), "max_devices": max_devices, "remaining_devices": remaining,
            "lease_expires": expires_iso}}

    def revoke(self, authorization: Optional[str], body: Dict[str, Any]) -> Response:
        scheme, _, given = str(authorization or "").partition(" ")
        if not self.admin_token or scheme != "Bearer" or not hmac.compare_digest(given.strip().encode(),
                                                                                  self.admin_token.encode()):
            return _fail(401, E_INVALID, "UNAUTHORIZED")
        token, order_id = body.get("token"), body.get("order_id")
        now_iso = _iso(time.time())
        with self._lock:
            db = self._db
            if isinstance(token, str) and token.strip():
                try:
                    payload_bytes = lic._b64d(token.strip().split(".")[1])
                    payload = json.loads(payload_bytes.decode("utf-8"))
                    if not isinstance(payload, dict):
                        raise ValueError
                except (IndexError, ValueError, TypeError):
                    return _fail(400, E_INVALID, "BAD_REQUEST", "token không đọc được")
                license_id = lic.order_digest(payload).hex()
                tier = str(payload.get("tier", ""))
                db.execute("INSERT OR IGNORE INTO licenses (license_id, order_id, sub, tier, max_devices, exp, "
                           "created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (license_id, str(payload.get("order_id", "")), str(payload.get("sub", "")), tier,
                            int(payload.get("max_devices") or lic.tier_max_devices(tier)),
                            int(payload.get("exp") or 0), now_iso))
                count = db.execute("UPDATE licenses SET revoked = 1, revoked_at = ? WHERE license_id = ?",
                                   (now_iso, license_id)).rowcount
            elif isinstance(order_id, str) and order_id.strip():
                count = db.execute("UPDATE licenses SET revoked = 1, revoked_at = ? WHERE order_id = ?",
                                   (now_iso, order_id.strip())).rowcount
                if not count:
                    return _fail(404, E_INVALID, "LICENSE_NOT_FOUND")
            else:
                return _fail(400, E_INVALID, "BAD_REQUEST", "cần token hoặc order_id")
        return 200, {"ok": True, "data": {"revoked": count}}

    # ---- HTTP ----
    def make_server(self, host: str = "127.0.0.1", port: int = 8787) -> ThreadingHTTPServer:
        service = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "AGSLicense/1"

            def log_message(self, *_args: Any) -> None:  # không ghi token ra log
                return

            def _send(self, status: int, body: Dict[str, Any]) -> None:
                data = json.dumps(body, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)

            def do_POST(self) -> None:  # noqa: N802
                routes = {"/api/v1/license/activate": "activate", "/api/v1/license/lease": "lease",
                          "/api/v1/license/revoke": "revoke"}
                route = routes.get(self.path.split("?", 1)[0])
                if route is None:
                    return self._send(404, {"ok": False, "reason": "NOT_FOUND"})
                try:
                    length = int(self.headers.get("Content-Length") or 0)
                except ValueError:
                    length = -1
                if not 0 <= length <= MAX_BODY_BYTES:
                    return self._send(*_fail(413 if length > MAX_BODY_BYTES else 400, E_INVALID, "BAD_REQUEST"))
                try:
                    body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                    if not isinstance(body, dict):
                        raise ValueError
                except (ValueError, UnicodeDecodeError):
                    return self._send(*_fail(400, E_INVALID, "BAD_REQUEST", "body phải là JSON object"))
                if route == "revoke":
                    return self._send(*service.revoke(self.headers.get("Authorization"), body))
                return self._send(*getattr(service, route)(body.get("token"), body.get("machine_id")))

            def do_GET(self) -> None:  # noqa: N802
                self._send(404, {"ok": False, "reason": "NOT_FOUND"})

        return ThreadingHTTPServer((host, port), Handler)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", type=Path, default=Path.home() / ".ags" / "license_ledger.db")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--issuer-key", type=Path, default=None,
                        help="Khoá ký lease (mặc định ~/.ags/issuer_private_key.json)")
    args = parser.parse_args()
    service = LicenseLedgerService(args.db, os.environ.get("AGS_LICENSE_ADMIN_TOKEN"), args.issuer_key)
    server = service.make_server(args.host, args.port)
    print(f"AGS license ledger: http://{args.host}:{server.server_address[1]} (db {args.db})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        service.close()


if __name__ == "__main__":
    main()

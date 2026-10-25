#!/usr/bin/env python3
"""
AGS (Agent Space) — kiểm thử lớp bảo vệ bản phát hành bằng khoá thử 1024-bit sinh tại chỗ (không dùng khoá ký thật):
token có order_id/max_devices + payload_digest 32 byte, dấu niêm nguồn gốc tài liệu, dấu đơn hàng 3 kênh
(zero-width, PNG tEXt, extra ZIP 0x4741), sổ cái ghế ags_license_server (activate/lease/revoke qua HTTP thật,
lease 24h + 72h ngoài mạng), ags_vault_loader (khoá dẫn từ token, gói `.protected`) và ags_build_protected_client
(zip client không còn file mẫu thô, vault mở bằng token đơn hàng, add-on Blender tách riêng, provenance.json).

Chạy:  venv/bin/python tests/ags_test_shield.py      hoặc  venv/bin/python -m unittest tests.ags_test_shield -v
"""

import hashlib
import io
import json
import os
import random
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
import zipfile
import zlib
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]

import ags_client_license as lic  # noqa: E402
import ags_license_server as srv  # noqa: E402
import ags_vault_loader as vault  # noqa: E402
import ags_build_protected_client as bpc  # noqa: E402
from ags_test_core import _test_prime  # noqa: E402

ENV_KEYS = ("AGS_REQUIRE_CLIENT_LICENSE", "AGS_CLIENT_LICENSE_TOKEN", "AGS_CLIENT_LICENSE_PATH", "AGS_LICENSE_URL")
ADMIN = "admin-thu-" + "x" * 24


class ShieldBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng = random.Random(2410)
        while True:
            p, q = _test_prime(512, rng), _test_prime(512, rng)
            phi = (p - 1) * (q - 1)
            if p != q and phi % lic.PUBLIC_E:
                break
        n, d = p * q, pow(lic.PUBLIC_E, -1, phi)
        cls._keydir = tempfile.TemporaryDirectory(prefix="ags_shield_key_")
        cls.key = Path(cls._keydir.name) / "issuer_test_key.json"
        cls.key.write_text(json.dumps({"e": lic.PUBLIC_E, "n_hex": f"{n:x}", "d_hex": f"{d:x}"}), encoding="utf-8")
        cls.real_n, lic.PUBLIC_N = lic.PUBLIC_N, n

    @classmethod
    def tearDownClass(cls):
        lic.PUBLIC_N = cls.real_n
        cls._keydir.cleanup()

    def setUp(self):
        self._saved_env = {k: os.environ.pop(k, None) for k in ENV_KEYS}
        self._tmp = tempfile.TemporaryDirectory(prefix="ags_shield_")
        self.tmp = Path(self._tmp.name)
        vault._RAM_CACHE.clear()

    def tearDown(self):
        vault._RAM_CACHE.clear()
        self._tmp.cleanup()
        for k, v in self._saved_env.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v

    def issue(self, **kw):
        kw.setdefault("issuer_key_path", self.key)
        return lic.issue_license_token(kw.pop("sub", "khach-thu"), **kw)


class ClientTokenTest(ShieldBase):
    def test_order_and_seat_defaults_in_signed_payload(self):
        for tier, seats in (("creator", 1), ("studio", 2), ("agency", 5), ("commercial", 1)):
            res = lic.verify_license_token(self.issue(tier=tier, days=1), "m1")
            self.assertTrue(res["valid"], res)
            self.assertEqual(res["payload"]["max_devices"], seats)
            self.assertNotIn("order_id", res["payload"])
        res = lic.verify_license_token(self.issue(tier="studio", order_id="DH-001", max_devices=7, days=1), "m1")
        self.assertEqual((res["payload"]["order_id"], res["payload"]["max_devices"]), ("DH-001", 7))

    def test_payload_digest_and_error_code(self):
        token = self.issue(order_id="DH-002", days=1)
        res = lic.verify_license_token(token, "m1")
        vsec = res["payload"]["vsec"]
        self.assertRegex(vsec, r"^[0-9a-f]{32}$")
        canonical = json.dumps({"order_id": "DH-002", "tier": "commercial", "vsec": vsec},
                               sort_keys=True, separators=(",", ":"))
        self.assertEqual(res["payload_digest"], hashlib.sha256(lic.DOMAIN + canonical.encode()).digest())
        self.assertEqual(len(res["payload_digest"]), 32)
        self.assertNotEqual(res["payload_digest"], lic.order_digest({"order_id": "DH-002", "tier": "commercial"}),
                            "không đoán được digest chỉ từ order_id/tier công khai")
        reissued = lic.verify_license_token(self.issue(order_id="DH-002", mid="m1", days=90), "m1")
        self.assertEqual(reissued["payload"]["vsec"], vsec)
        self.assertEqual(reissued["payload_digest"], res["payload_digest"], "cấp lại cùng đơn (exp/mid mới) giữ digest")
        for other in (self.issue(order_id="DH-003", days=1), self.issue(order_id="DH-002", tier="studio", days=1)):
            other_res = lic.verify_license_token(other, "m1")
            self.assertNotEqual(other_res["payload"]["vsec"], vsec)
            self.assertNotEqual(other_res["payload_digest"], res["payload_digest"])
        no_order = lic.verify_license_token(self.issue(sub="khach-x", days=1), "m1")
        self.assertEqual(no_order["payload_digest"], lic.order_digest({"sub": "khach-x", "vsec": no_order["payload"]["vsec"]}),
                         "không có order_id thì dùng sub")
        head, payload, sig = token.split(".")
        for bad in ("rác", f"{head}.{payload}.{sig[:-2]}AA" if not sig.endswith("AA") else f"{head}.{payload}.{sig[:-2]}BB",
                    self.issue(days=-1), self.issue(mid="khac", days=1)):
            res = lic.verify_license_token(bad, "m1")
            self.assertFalse(res["valid"])
            self.assertEqual(res["error_code"], "E-ags-anti-rea-shield-002")
            self.assertNotIn("payload_digest", res)

    def test_activate_output_is_json_without_digest(self):
        out = lic.activate_license_token(self.issue(days=1), self.tmp / "client_license.json")
        self.assertNotIn("payload_digest", out)
        json.dumps(out)
        status = lic.license_status(self.tmp / "client_license.json")
        self.assertTrue(status["valid"])
        json.dumps(status)


class OriginSealTest(ShieldBase):
    DOC = "---\nname: ags\n---\n# AGS\n\nNội dung kỹ năng.\n"

    def test_seal_roundtrip_ignores_install_note(self):
        sealed = lic.embed_origin_seal(self.DOC)
        self.assertRegex(sealed, r"<!-- ags-origin-seal: [0-9a-f]{64} -->\n$")
        self.assertEqual(lic.embed_origin_seal(sealed), sealed)
        root = self.tmp / "goi"
        root.mkdir()
        self.assertFalse(lic.verify_origin_seal(root), "không có file niêm thì không chứng minh được nguồn gốc")
        (root / "SKILL.md").write_text(sealed, encoding="utf-8")
        self.assertTrue(lic.verify_origin_seal(root))
        noted = sealed.replace("---\n# AGS", f"---\n> Cài đặt tại: {Path.home() / '.claude/skills/ags'}\n# AGS")
        (root / "SKILL.md").write_text(noted, encoding="utf-8")
        self.assertTrue(lic.verify_origin_seal(root))
        installer = sealed.replace("---\n# AGS", "---\n> Cài bởi `ags_setup.py --install-all-clients` — SKILL_DIR "
                                   "thật: `/x`. Mọi đường dẫn tương đối tính từ thư mục đó.\n# AGS")
        (root / "SKILL.md").write_text(installer, encoding="utf-8")
        self.assertTrue(lic.verify_origin_seal(root))
        (root / "SKILL.md").write_text(sealed.replace("Nội dung", "Nội dung đã sửa"), encoding="utf-8")
        self.assertFalse(lic.verify_origin_seal(root))
        self.assertEqual(lic.deriveOriginSeal(b"abc"), lic.deriveOriginSeal(b"abc", b"AGS-ORIGIN-V1"))
        self.assertNotEqual(lic.deriveOriginSeal(b"abc"), lic.deriveOriginSeal(b"abc", b"muoi-khac"))

        vsec = "0123456789abcdef0123456789abcdef"
        ordered = lic.embed_origin_seal(self.DOC, vsec)
        self.assertNotEqual(ordered, sealed)
        (root / "SKILL.md").write_text(ordered, encoding="utf-8")
        self.assertTrue(lic.verify_origin_seal(root, vsec))
        self.assertFalse(lic.verify_origin_seal(root), "niêm theo đơn không khớp muối mặc định")
        self.assertFalse(lic.verify_origin_seal(root, "f" * 32), "vsec đơn khác không khớp")


class LeakWatermarkTest(ShieldBase):
    def test_zero_width_png_and_zip_extra_channels(self):
        for order in ("DH-2026-0001", "Đơn-hàng-ü"):
            tag = lic.encode_zw_tag(order)
            self.assertTrue(all(ch in "\u2060\u200b\u200c" for ch in tag))
            self.assertEqual(lic.decode_zw_tag(f"Xin chào{tag} bạn"), order)
        self.assertIsNone(lic.decode_zw_tag("không có dấu"))

        png = lic.build_badge_png("DH-PNG-7")
        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n") and png.endswith(b"IEND\xaeB`\x82"))
        self.assertIn(b"tEXtags_order_id\x00DH-PNG-7", png)
        extra = lic.build_zip_extra_0x4741("DH-ZIP-9")
        self.assertEqual(extra[:2], b"AG")

        cases = {
            "zip": {"extra": extra, "files": {"SKILL.md": b"# AGS\n"}},
            "png": {"extra": b"", "files": {"assets/badge.png": png, "SKILL.md": b"# AGS\n"}},
            "zw": {"extra": b"", "files": {"SKILL.md": f"# AGS{lic.encode_zw_tag('DH-ZW-3')}\n".encode()}},
            "none": {"extra": b"", "files": {"SKILL.md": b"# AGS\n"}},
        }
        expected = {"zip": "DH-ZIP-9", "png": "DH-PNG-7", "zw": "DH-ZW-3", "none": None}
        for name, case in cases.items():
            path = self.tmp / f"{name}.zip"
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
                for rel, data in case["files"].items():
                    info = zipfile.ZipInfo(rel, (2026, 1, 1, 0, 0, 0))
                    info.extra = case["extra"]
                    archive.writestr(info, data)
            self.assertEqual(lic.verify_leak_watermark(path), expected[name], name)
            with zipfile.ZipFile(io.BytesIO(path.read_bytes())) as archive:
                self.assertEqual(lic.verify_leak_watermark(archive), expected[name], name)
            folder = self.tmp / f"dir_{name}"
            with zipfile.ZipFile(path) as archive:
                archive.extractall(folder)
            if name != "zip":  # extra ZIP mất khi giải nén; 2 kênh còn lại vẫn đọc được trên thư mục
                self.assertEqual(lic.verify_leak_watermark(folder), expected[name], name)
        self.assertIsNone(lic.verify_leak_watermark(self.tmp / "khong-ton-tai"))


class LicenseLedgerTest(ShieldBase):
    def setUp(self):
        super().setUp()
        self.service = srv.LicenseLedgerService(self.tmp / "ledger.db", admin_token=ADMIN, issuer_key_path=self.key)
        self.server = self.service.make_server("127.0.0.1", 0)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.service.close()
        super().tearDown()

    def post(self, route, body, auth=None):
        req = urllib.request.Request(f"{self.url}/api/v1/license/{route}", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        if auth:
            req.add_header("Authorization", auth)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read())

    def test_seat_limit_lease_and_revoke_over_http(self):
        token = self.issue(tier="studio", order_id="DH-SEAT-1", days=30)
        status, body = self.post("activate", {"token": token, "machine_id": "may-1"})
        self.assertEqual(status, 200, body)
        data = body["data"]
        self.assertTrue(body["ok"])
        self.assertEqual((data["bound_devices"], data["max_devices"], data["remaining_devices"]), (1, 2, 1))
        self.assertEqual(data["canary_seal"], {"order_id": "DH-SEAT-1",
                                               "channels": ["unicode_zw", "png_text", "zip_0x4741"]})
        lease = data["vault_lease"]
        self.assertEqual((lease["schema"], lease["offline_grace_hours"], lease["machine_id"]),
                         ("AGS-LEASE-V1", 72, "may-1"))
        self.assertEqual(lease["expires_ts"] - lease["issued_ts"], 24 * 3600)
        self.assertEqual(data["lease_expires"], lease["expires_at"])

        status, body = self.post("lease", {"token": token, "machine_id": "may-2"})
        self.assertEqual((status, body["data"]["remaining_devices"], body["data"]["bound_devices"]), (200, 0, 2))
        status, body = self.post("activate", {"token": token, "machine_id": "may-3"})
        self.assertEqual((status, body["error_code"], body["reason"]),
                         (403, "E-ags-anti-rea-shield-003", "MAX_DEVICES_EXCEEDED"))
        status, body = self.post("lease", {"token": token, "machine_id": "may-1"})
        self.assertEqual((status, body["data"]["bound_devices"]), (200, 2), "máy đã gắn được gia hạn")

        for bad in ("rác", self.issue(days=-1), self.issue(mid="may-khac", days=1)):
            status, body = self.post("activate", {"token": bad, "machine_id": "may-1"})
            self.assertEqual((status, body["error_code"]), (403, "E-ags-anti-rea-shield-002"))

        self.assertEqual(self.post("revoke", {"order_id": "DH-SEAT-1"})[0], 401)
        self.assertEqual(self.post("revoke", {"order_id": "DH-SEAT-1"}, "Bearer sai")[0], 401)
        status, body = self.post("revoke", {"order_id": "DH-SEAT-1"}, f"Bearer {ADMIN}")
        self.assertEqual((status, body["data"]["revoked"]), (200, 1))
        status, body = self.post("lease", {"token": token, "machine_id": "may-1"})
        self.assertEqual((status, body["error_code"], body["reason"]),
                         (403, "E-ags-anti-rea-shield-004", "LICENSE_REVOKED"))
        reissued = self.issue(tier="studio", order_id="DH-SEAT-1", days=60)
        self.assertEqual(self.post("activate", {"token": reissued, "machine_id": "may-1"})[1]["reason"],
                         "LICENSE_REVOKED", "token mới cùng đơn đã thu hồi cũng bị chặn")

        fresh = self.issue(tier="creator", days=30)
        status, body = self.post("revoke", {"token": fresh}, f"Bearer {ADMIN}")
        self.assertEqual(status, 200, body)
        self.assertEqual(self.post("activate", {"token": fresh, "machine_id": "may-9"})[1]["error_code"],
                         "E-ags-anti-rea-shield-004", "thu hồi trước khi kích hoạt")

        with sqlite3.connect(self.tmp / "ledger.db") as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM license_devices").fetchone()[0], 2)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM license_leases").fetchone()[0], 3)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM licenses WHERE revoked = 1").fetchone()[0], 2)

    def test_bad_requests(self):
        status, body = self.post("activate", {"token": self.issue(days=1)})
        self.assertEqual((status, body["reason"]), (400, "BAD_REQUEST"))
        req = urllib.request.Request(f"{self.url}/api/v1/license/activate", data=b"[1,2", method="POST")
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(caught.exception.code, 400)
        self.assertEqual(self.post("khong-co", {})[0], 404)

    def test_concurrent_activations_never_exceed_seats(self):
        token = self.issue(tier="agency", order_id="DH-RACE", days=1)
        results = []
        workers = [threading.Thread(target=lambda i=i: results.append(
            self.post("activate", {"token": token, "machine_id": f"may-{i}"})[0])) for i in range(12)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join()
        self.assertEqual((results.count(200), results.count(403)), (5, 7))

    def test_cached_lease_offline_window(self):
        token = self.issue(tier="creator", order_id="DH-OFF", days=30)
        lease = self.service.activate(token, "may-1")[1]["data"]["vault_lease"]
        issued, expires = lease["issued_ts"], lease["expires_ts"]
        online = lic.verify_cached_lease(lease, issued + 60)
        self.assertEqual((online["valid"], online["state"], online["order_id"]), (True, "online", "DH-OFF"))
        grace = lic.verify_cached_lease(lease, expires + 71 * 3600)
        self.assertEqual((grace["valid"], grace["state"], grace["grace_remaining_seconds"]),
                         (True, "offline_grace", 3600))
        self.assertTrue(lic.verify_cached_lease(lease, expires + 72 * 3600)["valid"])
        late = lic.verify_cached_lease(lease, expires + 72 * 3600 + 1)
        self.assertEqual((late["valid"], late["reason"], late["error_code"]),
                         (False, "LEASE_EXPIRED", "E-ags-anti-rea-shield-002"))
        self.assertEqual(lic.verify_cached_lease(lease, issued - 3600)["reason"], "CLOCK_ROLLBACK")
        for tampered in ({**lease, "expires_ts": expires + 10 ** 6}, {**lease, "offline_grace_hours": 10 ** 4},
                         {**lease, "sig": lease["sig"][:10] + ("B" if lease["sig"][10] != "B" else "C") + lease["sig"][11:]},
                         {k: v for k, v in lease.items() if k != "sig"}):
            self.assertEqual(lic.verify_cached_lease(tampered, issued)["reason"], "LEASE_TAMPERED")
        self.assertFalse(lic.verify_cached_lease({"schema": "khac"})["valid"])
        self.assertTrue(lic.verify_cached_lease(lease)["valid"], "now_ts mặc định = giờ hiện tại")
        with self.assertRaises(FileNotFoundError):
            srv.LicenseLedgerService(self.tmp / "khac.db", issuer_key_path=self.tmp / "khong-co-khoa.json")

    def test_client_activation_and_vault_use_license_server(self):
        os.environ["AGS_LICENSE_URL"] = self.url + "/"
        me = lic.get_machine_id()
        token = self.issue(tier="studio", order_id="DH-LEASE", days=30)
        root = make_protected_root(self.tmp / "goi", lic.verify_license_token(token))
        license_file = self.tmp / "client_license.json"

        out = lic.activate_license_token(token, license_file)
        lease = json.loads(license_file.read_text(encoding="utf-8"))["vault_lease"]
        self.assertEqual(out["vault_lease"], lease)
        self.assertEqual((lease["machine_id"], lease["bound_devices"], lease["max_devices"]), (me, 1, 2))
        self.assertEqual(vault.read_asset("blender/scene_bds.py", license_file, root), b"import bpy\n")
        status = vault.vault_status(license_file, root)
        self.assertEqual((status["bound_devices"], status["max_devices"], status["lease_expires"]),
                         (1, 2, lease["expires_at"]))

        self.assertEqual(self.post("revoke", {"order_id": "DH-LEASE"}, f"Bearer {ADMIN}")[0], 200)
        self.assertEqual(vault.read_asset("blender/scene_bds.py", license_file, root), b"import bpy\n",
                         "lease còn hạn: chưa cần hỏi máy chủ")
        record = json.loads(license_file.read_text(encoding="utf-8"))
        record.pop("vault_lease")
        license_file.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaises(PermissionError) as caught:
            vault.read_asset("blender/scene_bds.py", license_file, root)
        self.assertEqual(caught.exception.code, "E-ags-anti-rea-shield-004")
        self.assertIn("E-ags-anti-rea-shield-004", str(caught.exception))
        self.assertFalse(vault.vault_status(license_file, root)["decrypted"])

        one_seat = self.issue(tier="creator", order_id="DH-LEASE-1", days=30)
        self.assertEqual(self.service.activate(one_seat, "may-khac")[0], 200)
        seat_file = self.tmp / "seat.json"
        with self.assertRaises(PermissionError) as caught:
            lic.activate_license_token(one_seat, seat_file)
        self.assertIn("E-ags-anti-rea-shield-003", str(caught.exception))
        self.assertFalse(seat_file.exists(), "máy chủ từ chối thì không lưu token")

        fresh = self.issue(tier="studio", order_id="DH-LEASE-2", days=30)
        fresh_root = make_protected_root(self.tmp / "goi2", lic.verify_license_token(fresh))
        fresh_file = self.tmp / "fresh.json"
        expires = lic.activate_license_token(fresh, fresh_file)["vault_lease"]["expires_ts"]
        os.environ["AGS_LICENSE_URL"] = "http://127.0.0.1:9"  # máy chủ không với tới
        with patch("time.time", return_value=expires + 3600):
            self.assertEqual(vault.read_asset("blender/scene_bds.py", fresh_file, fresh_root), b"import bpy\n",
                             "lease hết hạn 1h, mất mạng: vẫn trong 72h ngoài mạng")
        with patch("time.time", return_value=expires + 73 * 3600), self.assertRaises(PermissionError) as caught:
            vault.read_asset("blender/scene_bds.py", fresh_file, fresh_root)
        self.assertIn("LEASE_SERVER_UNREACHABLE", str(caught.exception))
        with self.assertRaises(PermissionError) as caught:
            lic.activate_license_token(fresh, self.tmp / "offline.json")
        self.assertIn("LEASE_SERVER_UNREACHABLE", str(caught.exception))

    def test_packaged_bundle_uses_license_url_from_protected(self):
        self.assertNotIn("AGS_LICENSE_URL", os.environ)
        token = self.issue(tier="studio", order_id="DH-PKG-1", days=30)
        out = self.tmp / "dist" / "ags-client-protected.zip"
        res = bpc.build_protected_bundle(out, token=token, fast_build=True, license_url=self.url + "/")
        self.assertEqual(res["license_url"], self.url)
        with zipfile.ZipFile(out) as archive:
            archive.extractall(self.tmp / "khach")
        pkg_root = self.tmp / "khach" / bpc.PACK_NAME
        marker_path = pkg_root / ".protected"
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        self.assertEqual((marker["order_id"], marker["license_url"]), ("DH-PKG-1", self.url))
        self.assertRegex(marker["seal"], r"^[0-9a-f]{64}$")
        with patch.dict(os.environ, {"AGS_LICENSE_URL": " "}):
            self.assertEqual(lic._license_server_url(pkg_root), self.url, "AGS_LICENSE_URL rỗng không tắt máy chủ")

        license_file = self.tmp / "client_license.json"
        lease = lic.activate_license_token(token, license_file, root_dir=pkg_root)["vault_lease"]
        self.assertEqual((lease["machine_id"], lease["bound_devices"], lease["max_devices"]),
                         (lic.get_machine_id(), 1, 2), "máy chủ lấy từ .protected, không cần AGS_LICENSE_URL")
        src = vault.DEV_PATHS["blender/scene_bds.py"].read_bytes()
        self.assertEqual(vault.read_asset("blender/scene_bds.py", license_file, pkg_root), src)
        self.assertEqual(vault.vault_status(license_file, pkg_root)["bound_devices"], 1)

        with patch.object(lic, "get_machine_id", return_value="may-2"):
            lic.activate_license_token(token, self.tmp / "may2.json", root_dir=pkg_root)
        with patch.object(lic, "get_machine_id", return_value="may-3"), self.assertRaises(PermissionError) as caught:
            lic.activate_license_token(token, self.tmp / "may3.json", root_dir=pkg_root)
        self.assertIn("E-ags-anti-rea-shield-003", str(caught.exception))
        self.assertFalse((self.tmp / "may3.json").exists(), "hết ghế thì không lưu token")

        os.environ["AGS_LICENSE_URL"] = "http://127.0.0.1:9"  # khác rỗng: thắng .protected (máy chủ không với tới)
        again = lic.activate_license_token(token, license_file, root_dir=pkg_root)
        self.assertEqual(again["vault_lease"], lease, "mất mạng: giữ lease đã lưu còn hợp lệ")
        self.assertEqual(vault.read_asset("blender/scene_bds.py", license_file, pkg_root), src)
        with self.assertRaises(PermissionError) as caught:
            lic.activate_license_token(token, self.tmp / "lan-dau.json", root_dir=pkg_root)
        self.assertIn("E-ags-anti-rea-shield-002: LEASE_SERVER_UNREACHABLE", str(caught.exception))
        self.assertFalse((self.tmp / "lan-dau.json").exists(), "kích hoạt lần đầu bắt buộc gọi máy chủ")
        del os.environ["AGS_LICENSE_URL"]

        for tampered in ({**marker, "license_url": ""}, {**marker, "license_url": "http://127.0.0.1:9"},
                         {k: v for k, v in marker.items() if k != "seal"}):
            marker_path.write_text(json.dumps(tampered), encoding="utf-8")
            with self.assertRaises(vault.VaultError) as caught:
                vault.read_asset("blender/scene_bds.py", license_file, pkg_root)
            self.assertIn("E-ags-anti-rea-shield-002: ORIGIN_SEAL_MISMATCH", str(caught.exception))
        marker_path.write_text(json.dumps(marker), encoding="utf-8")
        self.assertEqual(vault.read_asset("blender/scene_bds.py", license_file, pkg_root), src)

        self.assertEqual(self.post("revoke", {"order_id": "DH-PKG-1"}, f"Bearer {ADMIN}")[0], 200)
        record = json.loads(license_file.read_text(encoding="utf-8"))
        record.pop("vault_lease")
        license_file.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaises(PermissionError) as caught:
            vault.read_asset("blender/scene_bds.py", license_file, pkg_root)
        self.assertEqual(caught.exception.code, "E-ags-anti-rea-shield-004")
        with self.assertRaises(PermissionError) as caught:
            lic.activate_license_token(token, self.tmp / "sau-thu-hoi.json", root_dir=pkg_root)
        self.assertIn("E-ags-anti-rea-shield-004", str(caught.exception))


def make_protected_root(root, verified):
    """Gói `.protected` tối thiểu: SKILL.md niêm bằng vsec của đơn + vault 2 file mở bằng khoá dẫn từ payload_digest."""
    (root / "assets").mkdir(parents=True)
    marker = {"schema": "AGS-PROTECTED-V1", "order_id": verified["payload"].get("order_id", ""),
              "vault": vault.VAULT_RELPATH.as_posix(), "license_url": ""}
    (root / ".protected").write_text(json.dumps(lic.seal_protected_marker(marker, verified["payload"]["vsec"])),
                                     encoding="utf-8")
    (root / "SKILL.md").write_text(lic.embed_origin_seal("# AGS\n\nKỹ năng.\n", verified["payload"]["vsec"]),
                                   encoding="utf-8")
    files = {"blender/scene_bds.py": b"import bpy\n", "rules/ags-editing-rules.json": b"{}"}
    (root / vault.VAULT_RELPATH).write_bytes(
        vault.seal_vault(files, vault.derive_vault_key(verified["payload_digest"], b"phat-hanh-1"), b"phat-hanh-1"))
    return root


class VaultLoaderTest(ShieldBase):
    def test_vault_key_bound_to_token_digest(self):
        res_a = lic.verify_license_token(self.issue(order_id="DH-A", days=1), "m1")
        res_b = lic.verify_license_token(self.issue(order_id="DH-B", days=1), "m1")
        k_a = vault.derive_vault_key(res_a["payload_digest"], b"salt-1")
        self.assertEqual(len(k_a), 32)
        self.assertNotEqual(k_a, vault.derive_vault_key(res_a["payload_digest"], b"salt-2"))
        blob = vault.seal_vault({"rules/x.json": b'{"a":1}'}, k_a, b"salt-1")
        self.assertEqual(vault.open_vault(blob, k_a), {"rules/x.json": b'{"a":1}'})
        self.assertEqual(blob[:5], b"AGSV2")
        with self.assertRaises(zlib.error):
            zlib.decompress(vault._split_vault(blob)[2])  # phần sau header là bản mã AES-GCM, không phải zlib thô
        for key, data in ((vault.derive_vault_key(res_b["payload_digest"], b"salt-1"), blob),
                          (k_a, blob[:-40] + bytes([blob[-40] ^ 1]) + blob[-39:])):
            with self.assertRaises(vault.VaultError) as caught:
                vault.open_vault(data, key)
            self.assertIn("E-ags-anti-rea-shield-002", str(caught.exception))
        with self.assertRaises(vault.VaultError):
            vault.derive_vault_key(res_a["payload_digest"].hex(), b"salt-1")

    def test_protected_package_reads_assets_in_ram(self):
        token = self.issue(tier="studio", order_id="DH-VAULT", days=30)
        root = make_protected_root(self.tmp / "goi", lic.verify_license_token(token))
        license_file = self.tmp / "client_license.json"

        with self.assertRaises(vault.VaultError) as caught:
            vault.read_asset("blender/scene_bds.py", license_file, root)
        self.assertIn("CLIENT_LICENSE_REQUIRED", str(caught.exception))
        self.assertFalse(vault.vault_status(license_file, root)["decrypted"])

        lic.activate_license_token(token, license_file)
        self.assertEqual(vault.read_asset("blender/scene_bds.py", license_file, root), b"import bpy\n")
        status = vault.vault_status(license_file, root)
        self.assertEqual((status["decrypted"], status["order_id"], status["max_devices"], status["vault_key"]),
                         (True, "DH-VAULT", 2, vault.REDACTED))
        self.assertEqual((status["bound_devices"], status["lease_expires"]), (None, None), "không có lease máy chủ")
        with self.assertRaises(vault.VaultError) as caught:
            vault.read_asset("khong/co.json", license_file, root)
        self.assertIn("ASSET_NOT_IN_VAULT", str(caught.exception))

        other = self.issue(tier="studio", order_id="DH-KHAC", days=30)
        lic.activate_license_token(other, license_file)
        vault._RAM_CACHE.clear()
        with self.assertRaises(vault.VaultError) as caught:
            vault.read_asset("blender/scene_bds.py", license_file, root)
        self.assertIn("ORIGIN_SEAL_MISMATCH", str(caught.exception), "token khác đơn (vsec khác) không mở được gói")

        lic.activate_license_token(self.issue(tier="studio", order_id="DH-VAULT", mid=lic.get_machine_id(), days=90),
                                   license_file)
        vault._RAM_CACHE.clear()
        self.assertEqual(vault.read_asset("blender/scene_bds.py", license_file, root), b"import bpy\n",
                         "token cấp lại cùng đơn (exp/mid mới) vẫn mở được vault")
        (root / "SKILL.md").write_text("# AGS\n\nĐã sửa.\n<!-- ags-origin-seal: " + "0" * 64 + " -->\n",
                                       encoding="utf-8")
        with self.assertRaises(vault.VaultError) as caught:
            vault.read_asset("blender/scene_bds.py", license_file, root)
        self.assertIn("ORIGIN_SEAL_MISMATCH", str(caught.exception))

    def test_dev_tree_reads_source_files(self):
        root = self.tmp / "dev"
        (root / "notes").mkdir(parents=True)
        (root / "notes" / "a.txt").write_bytes(b"dev")
        self.assertEqual(vault.read_asset("notes/a.txt", root_dir=root), b"dev")
        self.assertEqual(vault.read_asset("blender/scene_bds.py"), (ROOT / "assets" / "blender" / "scene_bds.py").read_bytes())
        for bad in ("../ngoai.txt", "/etc/hosts"):
            with self.assertRaises(vault.VaultError):
                vault.read_asset(bad, root_dir=root)
        self.assertFalse(vault.vault_status(root_dir=root)["protected"])


class BuildProtectedClientTest(ShieldBase):
    def build(self, token, **kw):
        out = self.tmp / "dist" / "ags-client-protected.zip"
        return out, bpc.build_protected_bundle(out, token=token, **kw)

    def test_bundle_layout_vault_seal_and_watermark(self):
        me = lic.get_machine_id()
        token = self.issue(tier="studio", order_id="DH-BUILD-1", mid=me, days=30)
        out, res = self.build(token, fast_build=True, license_url="")
        dist = out.parent
        addon, provenance_path = dist / "ags-blender-3d-addon.zip", dist / "provenance.json"
        self.assertTrue(out.is_file() and addon.is_file() and provenance_path.is_file())
        self.assertEqual(res["license_url"], "")
        self.assertEqual(sorted(bpc.collect_vault_files()), sorted(vault.DEV_PATHS))

        top = f"{bpc.PACK_NAME}/"
        with zipfile.ZipFile(out) as archive:
            names = set(archive.namelist())
            badge = archive.read(f"{top}assets/ags_verified_badge.png")
            enc = archive.read(f"{top}assets/vault.ags.enc")
        with self.assertRaises(zlib.error):
            zlib.decompress(vault._split_vault(enc)[2])
        for raw in (b"import bpy", b"scene_bds", b"blender/"):
            self.assertNotIn(raw, enc)
        with zipfile.ZipFile(out) as archive:
            self.assertTrue(all(lic._zip_extra_order_id(info.extra) == "DH-BUILD-1" for info in archive.infolist()))
        for rel in ("assets/vault.ags.enc", ".protected", "assets/ags_verified_badge.png", "SKILL.md",
                    "scripts/ags_vault_loader.py", "scripts/bds/ags_capcut_draft.py"):
            self.assertIn(top + rel, names)
        with zipfile.ZipFile(out) as archive:
            self.assertEqual(json.loads(archive.read(f"{top}.protected"))["license_url"], "")
        dev = bpc.dev_relpaths()
        self.assertIn("scripts/bds/ags_capcut_template.json", dev)
        self.assertIn("assets/blender/scene_bds.py", dev)
        for rel in dev + list(bpc.ADDON_FILES) + list(bpc.VENDOR_ONLY):
            self.assertNotIn(top + rel, names, "file mẫu thô / add-on / công cụ bên bán không được vào zip")
        self.assertEqual(lic._png_order_id(badge), "DH-BUILD-1")
        self.assertEqual(lic.verify_leak_watermark(out), "DH-BUILD-1")

        with zipfile.ZipFile(addon) as archive:
            self.assertEqual(sorted(archive.namelist()), sorted(bpc.ADDON_FILES))
        self.assertEqual(lic.verify_leak_watermark(addon), "DH-BUILD-1")

        root = self.tmp / "khach co dau cach"
        with zipfile.ZipFile(out) as archive:
            archive.extractall(root)
        skill = root / bpc.PACK_NAME
        vsec = lic.verify_license_token(token)["payload"]["vsec"]
        self.assertTrue(lic.verify_origin_seal(skill, vsec))
        self.assertFalse(lic.verify_origin_seal(skill), "bản theo đơn niêm bằng vsec, không phải muối mặc định")
        self.assertEqual(lic.decode_zw_tag((skill / "SKILL.md").read_text(encoding="utf-8")), "DH-BUILD-1")
        self.assertEqual(lic.verify_leak_watermark(skill), "DH-BUILD-1")

        license_file = self.tmp / "client_license.json"
        with self.assertRaises(vault.VaultError):
            vault.read_asset("blender/scene_bds.py", license_file, skill)
        lic.activate_license_token(token, license_file)
        for name, src in vault.DEV_PATHS.items():
            self.assertEqual(vault.read_asset(name, license_file, skill), src.read_bytes(), name)
        lic.activate_license_token(self.issue(tier="studio", order_id="DH-KHAC", days=30), license_file)
        vault._RAM_CACHE.clear()
        with self.assertRaises(vault.VaultError) as caught:
            vault.read_asset("blender/scene_bds.py", license_file, skill)
        self.assertIn("ORIGIN_SEAL_MISMATCH", str(caught.exception))

        prov = json.loads(provenance_path.read_text(encoding="utf-8"))
        self.assertEqual((prov["schema"], prov["order_id"], prov["fast_build"]), ("AGS-PROVENANCE-V1", "DH-BUILD-1", True))
        self.assertEqual(prov["artifacts"]["client"]["sha256"], hashlib.sha256(out.read_bytes()).hexdigest())
        self.assertEqual(prov["artifacts"]["blender_addon"]["sha256"], hashlib.sha256(addon.read_bytes()).hexdigest())
        self.assertEqual(prov["vault"]["files"], sorted(vault.DEV_PATHS))
        self.assertEqual(prov["checks"]["runtime_check"], "skipped (fast_build)")
        self.assertEqual(res["client_zip"], str(out))
        self.assertNotIn(token, provenance_path.read_text(encoding="utf-8"))
        self.assertNotIn(vsec, provenance_path.read_text(encoding="utf-8"))

    def test_rejects_bad_token_and_order_mismatch(self):
        token = self.issue(order_id="DH-BUILD-2", days=30)
        for kw in ({"token": "rác"}, {"token": self.issue(order_id="DH-X", days=-1)},
                   {"token": token, "order_id": "DH-KHAC"}, {"token": self.issue(days=30)}):
            with self.assertRaises(bpc.BuildError):
                bpc.build_protected_bundle(self.tmp / "dist" / "x.zip", fast_build=True, license_url="", **kw)
        with self.assertRaises(bpc.BuildError):
            bpc.build_protected_bundle(self.tmp / "dist" / "x.zip", token=token, fast_build=True, license_url="ftp://x")
        self.assertFalse((self.tmp / "dist" / "x.zip").exists())

    def test_full_build_runs_runtime_check(self):
        out, res = self.build(self.issue(tier="agency", order_id="DH-BUILD-3", days=30), fast_build=False,
                              license_url="")
        self.assertEqual(res["checks"]["runtime_check"], "passed")
        self.assertEqual(res["license"]["max_devices"], 5)



if __name__ == "__main__":
    unittest.main(verbosity=2)

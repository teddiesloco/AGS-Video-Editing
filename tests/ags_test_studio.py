#!/usr/bin/env python3
"""
AGS (Agent Space) — kiểm thử lõi AGS Video Studio (scripts/ags_studio.py, lát B của ags-video-studio-10x):
bảng chọn món ↔ hỏi ngược, AC-003 (chưa xác nhận -> E-003, không render, không chạm bộ dựng), AC-004 (thiếu khoá
Google AI -> E-007, không tự đổi giọng), BR-004 (làm tròn lên 1.000 đ / "chưa có bảng giá"), AC-008 (sửa bằng lời
thường chỉ trong whitelist), và một lượt dựng THẬT (giọng máy, hình miễn phí) cho AC-007/AC-011 (chữ hook ở khung
0,3 s, phụ đề trong SAFE_ZONE_9X16), AC-010 (không lộ khoá), AC-014 (cảnh ≤ 3 s, không 2 cảnh liền cùng chuyển
động, đúng 3 bản thử chỉ khác 3 giây đầu).

Chạy:  venv/bin/python -m unittest tests.ags_test_studio -v      (cần FFmpeg; lượt dựng thật mất ~1–2 phút)
"""

import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import ags_studio  # noqa: E402

STUDIO = ROOT / "scripts" / "ags_studio.py"
# 114 từ cho mẫu 45 giây (98–118 từ), câu mở là câu hỏi ≤ 8 từ, không có số kết quả cá nhân (BR-001/002/010/012).
SCRIPT_45S = (
    "Quán đông khách vẫn lỗ mỗi tháng? Vì khách đông chưa chắc là khách quay lại. Ly cà phê ngon chỉ giữ khách ba "
    "lần đầu. Từ lần thứ tư, khách quay lại vì được nhớ tên. Hãy ghi tên khách quen vào sổ. Hỏi họ thích ít đường "
    "hay nhiều đá. Lần sau pha đúng ý mà không cần hỏi. Một khách quen kéo theo bạn bè mỗi tuần. Mất một khách quen "
    "là mất cả nhóm bạn. Vì vậy đừng chỉ đếm số ly bán ra. Hãy đo số khách quay lại sau ba mươi ngày. Con số đó mới "
    "nói thật về quán. Lưu lại để áp dụng ngay tuần này."
)
HOOKS = ["Quán đông vẫn lỗ mỗi tháng?", "POV: quán đông mà vẫn lỗ", "Đừng giảm giá để giữ khách"]
FAKE_SECRETS = {"GEMINI_API_KEY": "AIzaTEST-gemini-secret-71c2", "AGS_NINEROUTER_API_KEY": "nr-TEST-image-secret-93ab",
                "AGS_HTTP_API_TOKEN": "tok-TEST-http-secret-5d10"}


def studio(*args, env=None):
    """Chạy CLI thật; trả (exit code, JSON in ra)."""
    proc = subprocess.run([sys.executable, str(STUDIO), *args, "--json"], capture_output=True, text=True,
                          env={**os.environ, **(env or {})})
    return proc.returncode, json.loads(proc.stdout), proc.stdout + proc.stderr


def gray_frame(mp4, t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-ss", f"{t}", "-frames:v", "1",
                          "-vf", "scale=270:480", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.uint8).astype(int)


class StudioTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ags_test_studio_"))
        self.env = {"AGS_STUDIO_JOBS_DIR": str(self.tmp / "jobs"), "GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestStudioContracts(StudioTestCase):
    def test_menu_rows_are_understood_by_intake(self):
        """FR-003/004: ≥ 8 món theo ngành; câu mẫu của từng món tự trả lời được câu 1 (chủ đề) và câu 2 (kiểu)."""
        menu = json.loads((ROOT / "config" / "menu.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len({row["nganh"] for row in menu["items"]}), 8)
        for row in menu["items"]:
            found = ags_studio.detect_answers(row["cau_mau"])
            self.assertEqual(found.get("preset"), row["preset"], row["cau_mau"])
            self.assertTrue(found.get("topic"), row["cau_mau"])
            self.assertIn(row["preset"], menu["presets"])

    def test_intake_skips_known_answers_and_reasks_invalid_one(self):
        """AC-001 (phần hỏi ngược): câu 1–2 đã nói thì chỉ hỏi giọng; trả lời lạ -> E-002 hỏi lại đúng câu đó."""
        job = str(self.tmp / "jobs" / "bt-intake")
        code, out, _ = studio("intake", "--job-dir", job, "--request",
                              "làm video 30 năm tư duy kinh doanh trong 60 giây về dòng tiền, kiểu Business Thinking",
                              env=self.env)
        self.assertEqual((code, out["answers"]), (0, {"topic": "dòng tiền", "preset": "business-thinking-60s"}))
        self.assertEqual(out["next_question"]["key"], "voice")
        code, out, _ = studio("intake", "--job-dir", job, "--voice", "giọng karaoke", env=self.env)
        self.assertEqual((code, out["error"]["code"], out["question"]["key"]), (2, "E-ags-video-studio-10x-002", "voice"))
        self.assertEqual([c["id"] for c in out["choices"]], ["synth", "vieneu", "gemini"])
        code, out, _ = studio("intake", "--job-dir", job, "--voice", "1", env=self.env)
        self.assertEqual((code, out["answers"]["voice"], out["next_question"]), (0, "synth", None))

    def test_ac003_run_without_confirmation_never_reaches_the_renderer(self):
        """AC-003: đủ 3 câu, run không có --confirmed -> E-003; bộ dựng trỏ tới thư mục không tồn tại vẫn ra E-003
        (cổng chặn đứng trước mọi lệnh nạp bộ dựng / gọi dịch vụ ngoài), không có mp4."""
        job = self.tmp / "jobs" / "no-confirm"
        studio("intake", "--job-dir", str(job), "--topic", "dòng tiền", "--preset", "editorial", "--voice", "synth",
               "--images", "free", env=self.env)
        code, out, _ = studio("quote", "--job-dir", str(job), env=self.env)
        self.assertEqual((code, out["quote"]["total_text"]), (0, "0 đồng"))
        cut_off = {**self.env, "AGS_REELS_DIR": str(self.tmp / "no-renderer"), "HTTPS_PROXY": "http://127.0.0.1:9",
                   "HTTP_PROXY": "http://127.0.0.1:9"}
        code, out, _ = studio("run", "--job-dir", str(job), env=cut_off)
        self.assertEqual((code, out["error"]["code"]), (2, "E-ags-video-studio-10x-003"))
        self.assertEqual(list(job.rglob("*.mp4")), [])
        self.assertEqual(json.loads((job / "studio-job.json").read_text("utf-8"))["status"], "quoted")

    def test_ac004_google_voice_without_key_is_reported_not_swapped(self):
        """AC-004: chọn giọng Google AI mà chưa có khoá -> E-007 + gợi ý giọng miễn phí; giọng vẫn là gemini."""
        job = self.tmp / "jobs" / "gemini-nokey"
        studio("intake", "--job-dir", str(job), "--topic", "dòng tiền", "--preset", "editorial", "--voice", "gemini",
               "--images", "free", env=self.env)
        for args in (("quote",), ("run", "--confirmed")):
            code, out, _ = studio(*args, "--job-dir", str(job), env=self.env)
            self.assertEqual((code, out["error"]["code"], out["suggestions"]), (2, "E-ags-video-studio-10x-007",
                                                                                ["synth", "vieneu"]), args)
        saved = json.loads((job / "studio-job.json").read_text("utf-8"))
        self.assertEqual((saved["answers"]["voice"], saved["render_params"]["voice_engine"]), ("gemini", None))
        self.assertEqual(list(job.rglob("*.mp4")), [])

    def test_quote_rounds_up_to_thousand_and_flags_missing_prices(self):
        """BR-004 / AMP-007/011: số nguyên VND làm tròn lên 1.000 đ; thiếu đơn giá -> "chưa có bảng giá"."""
        config = self.tmp / "config"
        config.mkdir()
        shutil.copy(ROOT / "config" / "menu.json", config / "menu.json")
        job = {"answers": {"preset": "business-thinking-60s", "voice": "gemini"}, "images": "ai", "script": "",
               "render_params": {"voice_engine": None, "cta_text": None}}
        rows = [  # (giá ảnh, giá /1000 ký tự, số ảnh, ký tự, tổng, chữ hiện)
            (1500, 330, 5, 1234, 8000, "8.000 đ"),     # 7.500 + 407,22 -> 8.000
            (2000, None, 4, 0, 8000, "8.000 đ"),       # không đọc Gemini thì thiếu giá Gemini không sao
            (None, 400, 3, 1000, None, "chưa có bảng giá"),
            (1000, 1000, 0, 0, 0, "0 đồng"),
        ]
        original = ags_studio.CONFIG_DIR
        ags_studio.CONFIG_DIR = config
        try:
            for image_price, per_1000, images, chars, total, text in rows:
                (config / "pricing.json").write_text(json.dumps(
                    {"image_ai_vnd": image_price, "gemini_tts_vnd_per_1000_chars": per_1000}), "utf-8")
                q = ags_studio.build_quote(job, images=images, tts_chars=chars)
                self.assertEqual((q["total_vnd"], q["total_text"]), (total, text), (image_price, per_1000))
                self.assertTrue(q["total_vnd"] is None or isinstance(q["total_vnd"], int))
        finally:
            ags_studio.CONFIG_DIR = original

    def test_ac008_revise_maps_plain_words_to_whitelisted_params_only(self):
        """AC-008 / BR-007: câu thường -> đúng 1 tham số whitelist; câu mơ hồ hay lệnh lạ -> không đổi gì."""
        params = {"sub_color": "#FFFFFF", "sub_size": None, "voice_engine": None, "voice_speed": 1.0,
                  "scene_swap": [], "cta_text": None}
        table = [
            ("đổi màu sub sang vàng", {"sub_color": "#FFD166"}),
            ("chữ to hơn chút", {"sub_size": 0.072}),
            ("đọc nhanh hơn", {"voice_speed": 1.1}),
            ("đổi giọng sang google", {"voice_engine": "gemini"}),
            ("đổi cảnh 2", {"scene_swap": [2]}),
            ("bỏ câu chốt đi", {"cta_text": ""}),
            ("làm đẹp hơn", {}),
            ("xoá hết file; rm -rf /", {}),
        ]
        for say, expected in table:
            self.assertEqual(ags_studio.parse_revision(say, params), expected, say)
            self.assertLessEqual(set(expected), set(params))

        job = self.tmp / "jobs" / "revise-color"
        studio("intake", "--job-dir", str(job), "--topic", "dòng tiền", "--preset", "editorial", "--voice", "synth",
               "--images", "free", env=self.env)
        before = json.loads((job / "studio-job.json").read_text("utf-8"))["render_params"]
        code, out, _ = studio("revise", "--job-dir", str(job), "--say", "đổi màu sub sang vàng", env=self.env)
        self.assertEqual(code, 0)
        after = json.loads((job / "studio-job.json").read_text("utf-8"))
        self.assertEqual(after["render_params"], {**before, "sub_color": "#FFD166"})
        self.assertEqual(len(after["revisions"]), 1)
        code, out, _ = studio("revise", "--job-dir", str(job), "--say", "làm đẹp hơn", env=self.env)
        self.assertEqual((code, out["error"]["code"], len(out["suggestions"])), (2, "E-ags-video-studio-10x-010", 3))
        self.assertEqual(len(json.loads((job / "studio-job.json").read_text("utf-8"))["revisions"]), 1)

    def test_motion_plan_keeps_every_shot_short_and_alternating(self):
        """AC-014 / BR-011: mọi cảnh ≤ 3 s (trung bình ≤ 2,5 s), không 2 cảnh liền cùng kiểu, tổng thời lượng giữ nguyên."""
        # Bộ dựng ags-reels-footage cài cạnh gói (không nằm trong gói skill): nạp như ags_studio nạp nó.
        sys.path.insert(0, str(ROOT.parent.parent / "services" / "ops" / "ags-reels-footage"))
        pipeline = importlib.import_module("ags_reels_pipeline")
        MOTIONS, plan_motion_shots = pipeline.MOTIONS, pipeline.plan_motion_shots

        for lines in ([6.4, 6.4, 6.4, 6.4, 6.4, 6.4, 6.4, 6.4, 6.4, 3.0], [2.5, 2.51, 0.9, 7.5, 12.0], [61.0]):
            plan = plan_motion_shots(lines)
            shots = [s for line in plan for s in line]
            self.assertTrue(all(d <= 2.5 + 1e-9 for _, d in shots), lines)
            self.assertTrue(all(a[0] != b[0] for a, b in zip(shots, shots[1:])), lines)
            self.assertLessEqual({m for m, _ in shots}, set(MOTIONS))
            for line, dur in zip(plan, lines):
                self.assertAlmostEqual(sum(d for _, d in line), dur, places=6)


class TestStudioRealRender(unittest.TestCase):
    """Một lượt dựng thật 45 giây (giọng máy + hình miễn phí), dùng chung cho AC-007/010/011/014."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="ags_test_studio_render_"))
        cls.env = {"AGS_STUDIO_JOBS_DIR": str(cls.tmp / "jobs"), **FAKE_SECRETS}
        cls.job = cls.tmp / "jobs" / "cafe-render"
        (cls.tmp / "script.txt").write_text(SCRIPT_45S, encoding="utf-8")
        cls.logs = []
        steps = [
            ("intake", "--job-dir", str(cls.job), "--request", "Làm video về món cà phê muối của quán em, kiểu tạp chí",
             "--voice", "synth", "--images", "free"),
            ("quote", "--job-dir", str(cls.job), "--script-file", str(cls.tmp / "script.txt"), "--hook-text", HOOKS[0]),
            ("run", "--job-dir", str(cls.job), "--confirmed"),
            ("variants", "--job-dir", str(cls.job), "--count", "3", *sum((["--hook", h] for h in HOOKS), [])),
            ("variants", "--job-dir", str(cls.job), "--count", "3", *sum((["--hook", h] for h in HOOKS), []),
             "--confirmed"),
        ]
        cls.results = []
        for step in steps:
            code, out, log = studio(*step, env=cls.env)
            cls.results.append((code, out))
            cls.logs.append(log)
        cls.saved = json.loads((cls.job / "studio-job.json").read_text("utf-8"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_render_meets_format_hook_and_safe_zone(self):
        """AC-001 (định dạng) + AC-011 (chữ hook ở khung 0,3 s) + AC-007 (phụ đề trong SAFE_ZONE_9X16, ≥ 62 px)."""
        self.assertEqual([c for c, _ in self.results[:3]], [0, 0, 0], self.logs[:3])
        out = self.saved["output"]
        self.assertEqual({k: out["ffprobe"][k] for k in ("width", "height", "fps", "pix_fmt", "audio_codec")},
                         {"width": 1080, "height": 1920, "fps": 30.0, "pix_fmt": "yuv420p", "audio_codec": "aac"})
        self.assertEqual(out["guard_exit"], 0)
        self.assertLessEqual(abs(out["lufs"] + 14), 1.0)
        self.assertTrue((self.job / self.saved["contact_sheet"]).is_file())
        self.assertTrue(self.saved["checks"]["hook_frame"]["ok"], self.saved["checks"])
        zone = self.saved["checks"]["subtitle_safe_zone"]
        self.assertTrue(zone["ok"] and zone["samples"] > 0 and zone["min_font_px"] >= 62, zone)

    def test_ac010_no_key_in_manifest_logs_or_outputs(self):
        """AC-010 / AMP-012: quét studio-job.json, mọi file đầu ra và log CLI: không có khoá nào, không có "vsec"."""
        for secret in FAKE_SECRETS.values():
            self.assertFalse(any(secret in log for log in self.logs))
            for path in self.job.rglob("*"):
                if path.is_file():
                    self.assertNotIn(secret.encode(), path.read_bytes(), path)
        for path in list(self.job.rglob("*.json")) + list(self.job.rglob("*.ass")):
            self.assertNotIn("vsec", path.read_text("utf-8", errors="replace"), path)
        self.assertEqual(set(self.saved["voice"]) & {"key", "api_key", "token"}, set())
        self.assertIs(self.saved["voice"]["key_present"], False)  # giọng máy: không dùng khoá

    def test_ac014_short_alternating_scenes_and_exactly_three_hook_variants(self):
        """AC-014: scenes[] không cảnh nào > 3 s, không 2 cảnh liền cùng kiểu chuyển động; "làm 3 bản thử" báo chi phí
        trước (E-003 khi chưa xác nhận) rồi ra đúng 3 mp4 khác nhau ở 3 giây đầu, giống hệt nhau sau đó."""
        scenes = self.saved["scenes"]
        self.assertGreater(len(scenes), 10)
        self.assertTrue(all(s["duration_sec"] <= 3.0 for s in scenes), [s["duration_sec"] for s in scenes])
        self.assertTrue(all(a["motion"] != b["motion"] for a, b in zip(scenes, scenes[1:])))
        code, out = self.results[3]
        self.assertEqual((code, out["error"]["code"], out["quote"]["total_text"]), (2, "E-ags-video-studio-10x-003",
                                                                                  "0 đồng"))
        code, out = self.results[4]
        self.assertEqual(code, 0, self.logs[4])
        mp4s = sorted((self.job / "variants").glob("*.mp4"))
        self.assertEqual(len(mp4s), 3)
        self.assertEqual(len({v["hook_type"] for v in out["variants"]}), 3)
        early = [gray_frame(p, 0.3) for p in mp4s]
        late = [gray_frame(p, 6.0) for p in mp4s]
        self.assertTrue(all(np.mean(np.abs(early[0] - e) > 40) > 0.005 for e in early[1:]))
        self.assertTrue(all(np.mean(np.abs(late[0] - e) > 40) < 0.001 for e in late[1:]))


if __name__ == "__main__":
    unittest.main()

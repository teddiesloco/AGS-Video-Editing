#!/usr/bin/env python3
"""
AGS (Agent Space) — kiểm thử scripts/ags_vi_script.py (AGS Video Studio 10x, lát A): nhịp 60 giây 129/130/158/159 từ
(AC-006), kịch bản dịch máy và chép nguồn 9 từ / 8 từ (AC-005), hook lời 14/15 từ, chữ 8/9 từ, mở bằng lời chào
(AC-011), số kết quả cá nhân cần claim_source (AC-012), màu từ khoá theo nghĩa (AC-013), mẫu series + thư viện hook
giao kèm đạt luật (FR-018/021), link nội bộ bị chặn (NFR-002), CLI --json + mã thoát. Không gọi mạng.

Chạy:  venv/bin/python -m unittest tests.ags_test_vi_script -v
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
CLI = ROOT / "scripts" / "ags_vi_script.py"
sys.path.insert(0, str(ROOT / "scripts"))

import ags_vi_script as vi  # noqa: E402

E004, E005, E012, E013 = (f"E-ags-video-studio-10x-{n}" for n in ("004", "005", "012", "013"))
GREEN, YELLOW, RED = "#A8FF3E", "#FFD166", "#FF5A5F"
GOOD = (FIXTURES / "vi_script_good.txt").read_text(encoding="utf-8")
CALQUE = (FIXTURES / "vi_script_calque.txt").read_text(encoding="utf-8")
SOURCE = (FIXTURES / "source_overlap.txt").read_text(encoding="utf-8")


def rules(result):
    return sorted((e["rule"], e["sentence"]) for e in result["errors"])


def config(name):
    return json.loads((ROOT / "config" / name).read_text(encoding="utf-8"))


class ViScriptTest(unittest.TestCase):
    def test_pace_boundaries_for_60_seconds(self):
        hook = "Tại sao quán đông khách vẫn hết tiền?"       # 8 từ, câu hỏi
        cta = "Lưu lại để áp dụng ngay hôm nay."              # 8 từ
        body = "Chủ quán cần ghi chép từng khoản chi mỗi ngày."  # 10 từ
        for total, ok in ((129, False), (130, True), (158, True), (159, False)):
            rest = total - 16
            lines = [body] * (rest // 10) + [" ".join(body.split()[:rest % 10]) + "."] * bool(rest % 10)
            with self.subTest(words=total):
                result = vi.validate_script("\n".join([hook, *lines, cta]), 60)
                self.assertEqual(result["stats"]["words"], total)
                self.assertEqual(result["stats"]["target_range"], [130, 158])
                self.assertEqual(result["ok"], ok, result["errors"])
                self.assertEqual(rules(result), [] if ok else [("nhip", 0)])

    def test_machine_translation_and_source_copy_are_blocked(self):
        good = vi.validate_script(GOOD, 60, SOURCE)
        self.assertTrue(good["ok"], good["errors"])
        self.assertEqual(good["stats"]["words"], 144)

        calque = vi.validate_script(CALQUE, 60)
        self.assertEqual({e["code"] for e in calque["errors"]}, {E005})
        self.assertEqual(rules(calque), sorted([
            ("cau-dai", 1), ("hook", 1), ("hook", 1), ("dich-may", 1),  # câu 22 từ, "là một trong những"
            ("dich-may", 3), ("dich-may", 4), ("dich-may", 5), ("dich-may", 6), ("dich-may", 6),
            ("tb-cau", 0), ("tu-ngoai", 0), ("nhip", 0),
        ]))

        lines = GOOD.strip().splitlines()
        for copied, expected in (("Người bán giỏi không bao giờ chạy theo giá.", [(E004, "trung-nguon", 14)]),
                                 ("Người bán giỏi không bao giờ chạy theo đám đông.", [])):
            with self.subTest(copied=copied):
                result = vi.validate_script("\n".join([*lines[:-1], copied, lines[-1]]), 60, SOURCE)
                self.assertEqual([(e["code"], e["rule"], e["sentence"]) for e in result["errors"]], expected)

        # BR-010 thay luật câu mở cũ: hook cảnh báo / POV / trước–sau (9–14 từ) qua validate; 15 từ hoặc lời chào thì không.
        for opener, expected in (("Cẩn thận: đừng mở thêm chi nhánh khi dòng tiền còn đang âm.", []),
                                 ("POV: bạn là chủ quán ngày mưa.", []),
                                 ("Trước vắng tanh, sau đổi menu thì sao?", []),
                                 ("Vì sao quán đông khách mà cuối tháng chủ vẫn không còn đồng lãi nào?", [("hook", 1)]),
                                 ("Xin chào, hôm nay mình nói về dòng tiền.", [("hook", 1), ("hook", 1)])):
            with self.subTest(opener=opener):
                self.assertEqual(rules(vi.validate_script("\n".join([opener, *lines[1:]]), 60)), expected)

    def test_hook_length_greeting_and_trigger(self):
        warning = "Chỉ 1 sai lầm này khiến dòng tiền cạn"  # AC-011 ghi "8 từ"; đếm theo tiếng là 9 (≤ 14 lời nói)
        spoken14 = "Vì sao quán đông khách mà cuối tháng chủ vẫn không còn đồng nào?"
        spoken15 = "Vì sao quán đông khách mà cuối tháng chủ vẫn không còn đồng lãi nào?"
        screen8 = "Quán đông khách vẫn hết tiền vì sao?"
        screen9 = "Quán đông khách vẫn hết sạch tiền vì sao?"
        self.assertEqual([len(t.split()) for t in (warning, spoken14, spoken15, screen8, screen9)], [9, 14, 15, 8, 9])
        cases = (
            (warning, None, []),
            (spoken14, None, []),
            (spoken15, None, ["qua-dai"]),
            (warning, screen8, []),
            (warning, screen9, ["chu-qua-dai"]),
            ("Xin chào các bạn, hôm nay mình chia sẻ…", None, ["loi-chao", "thieu-luc"]),
            ("Hôm nay quán mở cửa như mọi ngày", None, ["thieu-luc"]),
        )
        for spoken, screen, expected in cases:
            with self.subTest(spoken=spoken, screen=screen):
                result = vi.score_hook(spoken, screen)
                self.assertEqual([e["rule"] for e in result["errors"]], expected)
                self.assertEqual(result["ok"], not expected)
                self.assertTrue(all(e["code"] == E012 for e in result["errors"]))
        self.assertEqual(vi.score_hook(warning)["type"], "canh-bao")

    def test_personal_result_needs_claim_source(self):
        hook = "Tôi kiếm 50 triệu trong 30 ngày."
        cases = (
            ([], False, None),
            ([{"text": "50 triệu", "claim_source": ""}], False, None),
            ([{"text": "50 triệu", "claim_source": "khach-nhap"}], True, None),
            ([{"text": "50 triệu", "claim_source": "vi-du"}], True, "ví dụ"),
        )
        for claims, ok, label in cases:
            with self.subTest(claims=claims):
                result = vi.check_claims(hook, claims)
                self.assertEqual(result["ok"], ok)
                if ok:
                    self.assertEqual([(c["sentence"], c["label"]) for c in result["claims"]], [(1, label)])
                else:
                    self.assertEqual([(e["code"], e["sentence"]) for e in result["errors"]], [(E013, 1)])
        self.assertTrue(vi.check_claims("Một quán phở bán 300 bát mỗi sáng.", [])["ok"])

    def test_keyword_colors_follow_meaning(self):
        cases = (
            # tiền → xanh, thời gian → vàng, mất mát → đỏ; "doanh thu" nhường "500 triệu" (cùng cụm 4 từ).
            ("Doanh thu 500 triệu nghe thì lớn. Nhưng chỉ sau 3 tháng, quán bắt đầu mất khách.",
             [(2, GREEN), (3, GREEN), (10, YELLOW), (11, YELLOW), (15, RED), (16, RED)]),
            # Không có nghĩa tiền/cảnh báo → xen xanh ↔ vàng: số + thời gian, danh từ riêng, từ khoá nhấn.
            ("Sau 5 năm, quán phở nhỏ ở Đà Nẵng hiểu ra rằng mọi thứ bắt đầu từ kỷ luật.",
             [(1, GREEN), (2, GREEN), (7, YELLOW), (8, YELLOW), (17, GREEN), (18, GREEN)]),
            # Tên riêng đứng đầu câu tô trọn ("Việt Nam"), không chỉ nửa sau.
            ("Việt Nam trồng nhiều cà phê lắm. Một ly ở phố giá 35k.",
             [(0, YELLOW), (1, YELLOW), (12, GREEN)]),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(vi.pick_keywords(text.split()), expected)

    def test_shipped_formats_and_hooks_obey_rules(self):
        formats, hooks = config("formats-vi.json"), config("hooks-vi.json")
        colors = set(config("keywords-vi.json")["colors"].values())
        hook_ids = {t["id"] for t in hooks["types"]}
        self.assertEqual(set(formats["formats"]),
                         {"thirty-years-60s", "sai-lam-90", "truoc-sau", "nghich-ly", "pov", "jetlag-vi"})
        self.assertEqual(formats["aliases"], {"business-thinking-60s": "thirty-years-60s"})
        self.assertEqual(hook_ids, {"noi-dau", "nghich-ly", "ket-qua", "cau-hoi", "canh-bao", "truoc-sau", "pov",
                                    "nua-cau"})
        for name, fmt in formats["formats"].items():
            with self.subTest(format=name):
                self.assertEqual([b["block"] for b in fmt["beats"]], ["hook", "body", "close", "cta"])
                self.assertEqual(sum(b["sec"] for b in fmt["beats"]), fmt["duration_sec"])
                self.assertTrue(fmt["duration_range"][0] <= fmt["duration_sec"] <= fmt["duration_range"][1])
                self.assertLessEqual(fmt["beats"][0]["sec"], 5)
                self.assertGreaterEqual(fmt["scenes"] * 2.5, fmt["duration_sec"])
                self.assertTrue(len(fmt["motions"]) >= 2 and set(fmt["motions"]) <= set(formats["motions_allowed"]))
                self.assertIn(fmt["keyword_color"], colors)
                self.assertTrue(len(set(fmt["hook_types"])) >= 3 and set(fmt["hook_types"]) <= hook_ids)
        for cta in formats["cta_examples"]:
            self.assertLessEqual(len(cta.split()), 10, cta)
        for hook_type in hooks["types"]:
            self.assertEqual(len(hook_type["examples"]), 3, hook_type["id"])
            for example in hook_type["examples"]:
                with self.subTest(example=example):
                    self.assertEqual(vi.score_hook(example, example)["errors"], [])
                    self.assertTrue(vi.check_claims(example, [])["ok"])

    def test_profile_blocks_internal_links(self):
        for url, rule in (("http://127.0.0.1:8792/api/v1/studio/jobs", "ssrf"), ("http://localhost/", "ssrf"),
                          ("http://[::1]/", "ssrf"), ("http://10.0.0.5/reel", "ssrf"), ("http://0.0.0.0/", "ssrf"),
                          ("http://169.254.169.254/latest/meta-data/", "ssrf"),
                          ("file:///etc/passwd", "link-khong-hop-le")):
            with self.subTest(url=url):
                result = vi.profile_samples([url])
                self.assertFalse(result["ok"])
                self.assertEqual([(e["code"], e["rule"]) for e in result["errors"]], [(E004, rule)])

    def test_profile_measures_text_only(self):
        result = vi.profile_samples([GOOD])
        self.assertTrue(result["ok"], result["errors"])
        sample = result["samples"][0]
        self.assertEqual({k: sample[k] for k in ("words", "sentences", "hook_words", "hook_type", "words_per_sec")},
                         {"words": 144, "sentences": 14, "hook_words": 8, "hook_type": "con-so", "words_per_sec": None})
        self.assertEqual(result["suggested"]["words_per_sec"], 2.4)
        self.assertNotIn("tiền mặt", json.dumps(result, ensure_ascii=False))
        self.assertEqual([e["rule"] for e in vi.profile_samples([GOOD] * 6)["errors"]], ["so-mau"])

    def test_cli_json_and_exit_codes(self):
        for fixture, code in (("vi_script_good.txt", 0), ("vi_script_calque.txt", 1)):
            with self.subTest(fixture=fixture):
                proc = subprocess.run([sys.executable, str(CLI), "validate", "--script-file", str(FIXTURES / fixture),
                                       "--duration", "60", "--json"], capture_output=True, text=True, encoding="utf-8")
                self.assertEqual(proc.returncode, code, proc.stderr)
                self.assertEqual(json.loads(proc.stdout)["ok"], code == 0)


if __name__ == "__main__":
    unittest.main()

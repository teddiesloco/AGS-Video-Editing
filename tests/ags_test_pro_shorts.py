#!/usr/bin/env python3
"""
AGS (Agent Space) — kiểm thử scripts/ags_pro_shorts.py (feature pro-shorts-vi), không gọi mạng, không cần TTS/ffmpeg:
chữ nằm dưới đường chia và trong vùng an toàn (AC-002), phụ đề <= 2 dòng theo mốc giọng Việt (AC-003), ducking và
dòng thời gian (AC-004), nén giọng (AC-005), kiểm plan (AC-006), thiếu khoá Gemini (AC-007), knowledge.md (AC-008),
plan_with_llm với LLM giả.

Chạy:  python -m pytest -q tests/ags_test_pro_shorts.py
"""

import contextlib, io
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import ags_pro_shorts as ps  # noqa: E402

SCRIPT = ("Sau hơn bốn nghìn cuộc gọi bán hàng, tôi rút ra một điều mà ít người chịu thừa nhận. Người bán giỏi không nói "
          "nhiều, họ hỏi nhiều hơn và im lặng đúng lúc. Khi khách tự nói ra vấn đề của mình, họ tin vào câu trả lời "
          "của chính họ. Còn khi bạn nói thay họ, đó chỉ là lời của một người bán hàng muốn lấy 100.000 đô la. "
          "Vì vậy trước khi chào giá, hãy hỏi đủ ba câu: bạn đang ở đâu, bạn muốn tới đâu, và điều gì đang cản bạn.")


def voice_words(script=SCRIPT, step=0.32):
    """Mốc từng từ như align_voice trả về cho giọng TTS: (start, end, word)."""
    return [(round(i * step, 3), round(i * step + step * 0.9, 3), w) for i, w in enumerate(script.split())]


def dialogues(ass_text):
    """[(style, start, end, x, y, text)] từ các dòng Dialogue của file ASS."""
    rows = []
    for line in ass_text.splitlines():
        if not line.startswith("Dialogue:"):
            continue
        parts = line.split(",", 9)
        pos = re.search(r"\\pos\((\d+),(\d+)\)", parts[9])
        size = re.search(r"\\fs(\d+)", parts[9])
        rows.append({"style": parts[3], "start": parts[1], "end": parts[2], "x": int(pos.group(1)), "y": int(pos.group(2)),
                     "size": int(size.group(1)) if size else None, "text": parts[9]})
    return rows


def good_plan():
    shorts = [{"name": f"doan-{i}", "start": 100.0 * i, "end": 100.0 * i + 40.0, "hook": "HỎI TRƯỚC RỒI MỚI BÁN",
               "segments": ["Câu một.", "Câu hai."]} for i in range(1, 4)]
    lessons = [{"title": f"Bài {i}", "body": "Áp dụng được.", "t": 60.0 * i} for i in range(1, 6)]
    return {"shorts": shorts, "knowledge": {"summary": "Tóm tắt.", "lessons": lessons}}


def legacy_families(font_file):
    """Tên họ font (name ID 1, Windows Unicode) đọc thẳng từ bảng 'name' của file TTF."""
    import struct
    data = Path(font_file).read_bytes()
    count = struct.unpack(">H", data[4:6])[0]
    for i in range(count):
        tag, _, offset, _ = struct.unpack(">4sIII", data[12 + 16 * i:28 + 16 * i])
        if tag == b"name":
            break
    _, records, strings = struct.unpack(">HHH", data[offset:offset + 6])
    names = set()
    for i in range(records):
        platform, _, _, name_id, length, start = struct.unpack(">6H", data[offset + 6 + 12 * i:offset + 18 + 12 * i])
        if platform == 3 and name_id == 1:
            names.add(data[offset + strings + start:offset + strings + start + length].decode("utf-16-be"))
    return names


def error_code(context):
    return re.search(r"E-pro-shorts-vi-\d{3}", str(context.exception)).group(0)


class LayoutTest(unittest.TestCase):
    def test_every_caption_cue_fits_two_lines_inside_caption_box(self):
        from PIL import ImageFont
        cues = ps.caption_cues(voice_words())
        self.assertGreater(len(cues), 5)
        width = ps.CAPTION_BOX[2] - ps.CAPTION_BOX[0]
        for cue in cues:
            size, lines = ps.layout_cue(cue["words"])
            self.assertLessEqual(len(lines), 2, cue["words"])
            font = ImageFont.truetype(str(ps.FONT_CAPTION), size)
            for line in lines:
                self.assertLessEqual(font.getlength(line), width, line)

    def test_all_text_sits_below_split_and_inside_platform_safe_band(self):
        cues = ps.caption_cues(voice_words())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "short.ass"
            ps.write_ass(path, cues, "Hỏi đủ ba câu trước khi chào giá luôn", "Nguồn: Alex Hormozi · lồng tiếng Việt", 48.0)
            text = path.read_text(encoding="utf-8")
        rows = dialogues(text)
        styles = {r["style"] for r in rows}
        self.assertEqual(styles, {"Hook", "Source", "Caption"})
        hook_size = int(re.search(r"Style: Hook,[^,]+,(\d+),", text).group(1))
        for row in rows:
            lines = row["text"].count("\\N") + 1
            size = row["size"] or (hook_size if row["style"] == "Hook" else 34)
            pad = 14 if row["style"] == "Hook" else 0
            half = lines * size * 1.25 / 2 + pad
            self.assertGreater(row["y"] - half, ps.SPLIT, row)        # không che mặt ở nửa trên
            self.assertLess(row["y"] + half, 1440, row)               # trên khối mô tả/tên kênh của nền tảng
            self.assertEqual(row["x"], ps.W // 2)
            if row["style"] == "Caption":
                self.assertLessEqual(lines, 2, row)
        hook = next(r for r in rows if r["style"] == "Hook")["text"]
        self.assertEqual(re.sub(r"\{[^}]*\}", "", hook).replace("\\N", " "), "HỎI ĐỦ BA CÂU TRƯỚC KHI CHÀO GIÁ LUÔN")

    def test_ass_font_names_match_bundled_files_for_libass(self):
        """libass chọn font theo họ cũ (name ID 1); tên sai thì hook/phụ đề biến mất trên máy không có font hệ thống."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "short.ass"
            ps.write_ass(path, ps.caption_cues(voice_words()), "Ba câu hỏi trước khi chào giá", "Nguồn: Alex Hormozi", 30.0)
            used = dict(re.findall(r"^Style: (\w+),([^,]+),", path.read_text(encoding="utf-8"), re.M))
        bundled = set().union(*(legacy_families(f) for f in ps.FONTS.glob("*.ttf")))
        self.assertEqual(used["Hook"], "Bricolage Grotesque")
        self.assertTrue(set(used.values()) <= bundled, (used, bundled))

    def test_source_line_and_hook_cover_the_whole_short(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "short.ass"
            ps.write_ass(path, ps.caption_cues(voice_words()), "Ba câu hỏi trước khi chào giá", "Nguồn: Alex Hormozi", 52.3)
            rows = dialogues(path.read_text(encoding="utf-8"))
        for style in ("Hook", "Source"):
            row = next(r for r in rows if r["style"] == style)
            self.assertEqual((row["start"], row["end"]), ("0:00:00.00", "0:00:52.30"))

    def test_only_brand_colors_in_styles(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "short.ass"
            ps.write_ass(path, ps.caption_cues(voice_words()), "Ba câu hỏi trước khi chào giá", "Nguồn: Alex Hormozi", 30.0)
            text = path.read_text(encoding="utf-8")
        brand = {ps.ass_color(c)[4:] for c in (ps.PAPER, ps.INK, ps.GREEN, ps.NEON, "#ffffff")} | {"000000"}
        used = set(re.findall(r"&H00([0-9A-F]{6})", text))
        self.assertTrue(used <= brand, used - brand)
        self.assertNotIn("Inter", text)


class CaptionTimingTest(unittest.TestCase):
    def test_cues_follow_vietnamese_voice_times_and_keep_every_word(self):
        words = voice_words()
        cues = ps.caption_cues(words)
        self.assertEqual([w for c in cues for w in c["words"]], [w for _, _, w in words])
        self.assertAlmostEqual(cues[0]["start"], words[0][0] + ps.VOICE_LEAD)
        index = 0
        for cue, nxt in zip(cues, cues[1:]):
            index += len(cue["words"])
            self.assertAlmostEqual(nxt["start"], words[index][0] + ps.VOICE_LEAD)
            self.assertLessEqual(cue["end"], nxt["start"])          # không chồng phụ đề
            self.assertLessEqual(cue["end"] - cue["start"], ps.CAPTION_MAX_SECONDS + ps.CAPTION_HOLD_SECONDS)

    def test_segment_starts_match_first_word_of_each_sentence(self):
        segments = ["Một hai ba.", "Bốn — năm sáu.", "Bảy."]
        words = voice_words("Một hai ba. Bốn năm sáu. Bảy.", step=1.0)
        self.assertEqual(ps.segment_starts(segments, words), [0.0, 3.0, 6.0])


class AudioTimelineTest(unittest.TestCase):
    def test_ducking_default_and_range(self):
        self.assertEqual(ps.ducking_gain(), "volume=-21.0dB")
        for bad in (-25.0, -17.0):
            with self.assertRaises(ps.ProShortsError) as ctx:
                ps.ducking_gain(bad)
            self.assertEqual(error_code(ctx), "E-pro-shorts-vi-007")

    def test_original_audio_ducked_only_when_lengths_match(self):
        close = ps.build_timeline(40.0, 120.0, 162.0, 1500.0)
        self.assertEqual((close["original_audio"], close["src_start"], close["total"]), ("ducked", 120.0, 40.8))
        self.assertEqual(ps.build_timeline(30.0, 120.0, 160.0, 1500.0)["original_audio"], "off")

    def test_timeline_never_runs_past_source_end(self):
        timeline = ps.build_timeline(38.0, 1460.0, 1500.0, 1500.0)
        self.assertLessEqual(timeline["src_start"] + timeline["total"], 1500.0)

    def test_timeline_stays_inside_selected_clip(self):
        timeline = ps.build_timeline(30.0, 120.0, 160.0, 1500.0)
        self.assertEqual(timeline["src_start"], 120.0)
        self.assertLessEqual(timeline["total"], 40.0)
        with self.assertRaises(ps.ProShortsError) as ctx:       # giọng dài hơn đoạn đã chọn: lỗi, không kéo qua mốc cuối
            ps.build_timeline(50.0, 100.0, 140.0, 1500.0)
        self.assertEqual(error_code(ctx), "E-pro-shorts-vi-006")

    def test_voice_tempo_compresses_to_selected_clip(self):
        tempo = ps.fit_voice_tempo(42.0, 40.0)
        self.assertTrue(1.0 < tempo <= ps.MAX_VOICE_TEMPO)
        self.assertLess(ps.VOICE_LEAD + 42.0 / tempo + ps.VOICE_TAIL, 40.0)

    def test_voice_tempo_fits_sixty_seconds_or_fails(self):
        self.assertEqual(ps.fit_voice_tempo(55.0), 1.0)
        tempo = ps.fit_voice_tempo(65.0)
        self.assertTrue(1.0 < tempo <= ps.MAX_VOICE_TEMPO)
        self.assertLessEqual(ps.VOICE_LEAD + 65.0 / tempo + ps.VOICE_TAIL, ps.MAX_SHORT_SECONDS)
        with self.assertRaises(ps.ProShortsError) as ctx:
            ps.fit_voice_tempo(75.0)
        self.assertEqual(error_code(ctx), "E-pro-shorts-vi-006")


class PlanTest(unittest.TestCase):
    def test_valid_plan_passes(self):
        self.assertEqual(len(ps.validate_plan(good_plan(), 1500.0, 3)["shorts"]), 3)

    def test_invalid_plans_fail_before_render(self):
        cases = []
        plan = good_plan(); plan["shorts"][1]["hook"] = "QUÁ NGẮN"; cases.append((plan, "003"))
        plan = good_plan(); plan["shorts"][2]["start"] = 220.0; plan["shorts"][2]["end"] = 250.0; cases.append((plan, "003"))
        plan = good_plan(); plan["shorts"][0]["end"] = 170.0; cases.append((plan, "003"))
        plan = good_plan(); plan["shorts"][0]["segments"] = ["Một câu."]; cases.append((plan, "003"))
        plan = good_plan(); plan["shorts"][0]["end"] = 1600.0; plan["shorts"][0]["start"] = 1560.0; cases.append((plan, "003"))
        plan = good_plan(); del plan["knowledge"]["lessons"][0]; cases.append((plan, "004"))
        plan = good_plan(); plan["knowledge"]["lessons"][0]["t"] = 9999; cases.append((plan, "004"))
        for plan, code in cases:
            with self.assertRaises(ps.ProShortsError) as ctx:
                ps.validate_plan(plan, 1500.0, 3)
            self.assertEqual(error_code(ctx), f"E-pro-shorts-vi-{code}")
        with self.assertRaises(ps.ProShortsError):
            ps.validate_plan(good_plan(), 1500.0, 4)

    def test_plan_with_fake_llm_maps_picks_to_sentence_times(self):
        sentences = [{"id": i, "start": 8.0 * i, "end": 8.0 * i + 7.8, "text": f"English sentence {i}."} for i in range(15)]
        prompts = []

        def llm(prompt):
            prompts.append(prompt)
            if prompt.startswith("Video dài"):
                return {"picks": [{"first_id": 0, "last_id": 4, "name": "mot"}, {"first_id": 5, "last_id": 9, "name": "hai"},
                                  {"first_id": 10, "last_id": 14, "name": "ba"}]}
            if prompt.startswith("Lồng tiếng"):
                return {"hook": "hỏi trước rồi mới bán", "segments": ["Câu một.", "Câu hai.", "Câu ba."]}
            return {"summary": "Tóm tắt.", "lessons": [{"title": f"B{i}", "body": "Áp dụng.", "t": 10 * i} for i in range(5)]}

        meta = {"pro": "Alex Hormozi", "title": "Sales", "channel": "Alex Hormozi", "url": "https://youtu.be/x"}
        plan = ps.plan_with_llm({"sentences": sentences, "duration": 120.0}, meta, 3, llm=llm)
        self.assertEqual([(s["start"], s["end"]) for s in plan["shorts"]], [(0.0, 39.8), (40.0, 79.8), (80.0, 119.8)])
        self.assertEqual(plan["shorts"][0]["hook"], "HỎI TRƯỚC RỒI MỚI BÁN")
        self.assertIn("English sentence 5.", prompts[2])
        self.assertNotIn("English sentence 4.", prompts[2])

    def test_missing_gemini_key_stops_without_network(self):
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "", "GEMINI_API_KEYS": ""}), \
                mock.patch.object(ps.urllib.request, "urlopen", side_effect=AssertionError("không được gọi mạng")):
            with self.assertRaises(ps.ProShortsError) as ctx:
                ps.gemini_json("x")
        self.assertEqual(error_code(ctx), "E-pro-shorts-vi-005")

class ReviewRegressionTest(unittest.TestCase):
    def test_clip_shorter_than_30s_rejected(self):
        plan = good_plan(); plan["shorts"][0]["end"] = plan["shorts"][0]["start"] + 20.0
        with self.assertRaises(ps.ProShortsError) as ctx:
            ps.validate_plan(plan, 1500.0, 3)
        self.assertEqual(error_code(ctx), "E-pro-shorts-vi-003")

    def test_long_source_line_is_one_line_inside_safe_box(self):
        from PIL import ImageFont
        sources = ["Nguồn: Alex Hormozi · kênh The Game with Alex Hormozi · lồng tiếng Việt",
                   "Nguồn: " + "W" * 100 + " · lồng tiếng Việt"]
        for source in sources:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "short.ass"
                ps.write_ass(path, ps.caption_cues(voice_words()), "Ba câu hỏi trước khi chào giá", source, 30.0)
                row = next(r for r in dialogues(path.read_text(encoding="utf-8")) if r["style"] == "Source")
            font = ImageFont.truetype(str(ps.FONT_CAPTION), row["size"])
            lines = re.sub(r"\{[^}]*\}", "", row["text"]).split("\\N")
            self.assertEqual(len(lines), 1)
            self.assertLessEqual(font.getlength(lines[0]), ps.SOURCE_BOX[2] - ps.SOURCE_BOX[0])
            self.assertLessEqual(row["size"] * 1.2, ps.SOURCE_BOX[3] - ps.SOURCE_BOX[1] + 8)

    def test_ab_first_rejects_engine_outside_allowlist(self):
        with mock.patch.object(ps, "acquire", side_effect=AssertionError("không được chạy tiếp")):
            with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
                rc = ps.main(["/tmp/x.mp4", "--ab-first", "zerotts:Nam"])
        self.assertNotEqual(rc, 0)
        self.assertIn("E-pro-shorts-vi-003", out.getvalue() + err.getvalue())

    def test_video_id_from_metadata_is_one_safe_path_component(self):
        meta = ps.meta_from_info({"id": "../../etc/x", "channel": "C"})
        self.assertNotIn("/", meta["id"])
        self.assertNotIn("..", meta["id"])

    def test_cached_transcript_of_another_file_is_not_reused(self):
        import types
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "w"; work.mkdir()
            first, second = Path(tmp) / "a.mp4", Path(tmp) / "b.mp4"
            first.write_bytes(b"1"); second.write_bytes(b"1")
            def fake(args):
                Path(args.out).write_text('{"source": "%s", "model": "base", "duration": %d}' % (args.input, 1 if args.input == str(first) else 2), encoding="utf-8")
            with mock.patch.dict(sys.modules, {"ags_clip_shorts": types.SimpleNamespace(cmd_transcript=fake)}):
                self.assertEqual(ps.transcribe(first, work, "base")["duration"], 1)
                self.assertEqual(ps.transcribe(second, work, "base")["duration"], 2)

    def test_replaced_video_or_changed_model_refreshes_transcript(self):
        import types
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            work, video = Path(tmp) / "w", Path(tmp) / "v.mp4"
            work.mkdir()
            def fake(args):
                calls.append(args.model)
                Path(args.out).write_text('{"source": "%s", "model": "%s", "duration": %d}' % (args.input, args.model, len(calls)), encoding="utf-8")
            with mock.patch.dict(sys.modules, {"ags_clip_shorts": types.SimpleNamespace(cmd_transcript=fake)}):
                video.write_bytes(b"aaaa")
                self.assertEqual(ps.transcribe(video, work, "base")["duration"], 1)
                self.assertEqual(ps.transcribe(video, work, "base")["duration"], 1)       # cache hit
                video.write_bytes(b"bbbbbb")                                                # cùng đường dẫn, nội dung khác
                self.assertEqual(ps.transcribe(video, work, "base")["duration"], 2)
                self.assertEqual(ps.transcribe(video, work, "small")["duration"], 3)



class KnowledgeTest(unittest.TestCase):
    def test_knowledge_has_source_and_timestamp_links(self):
        meta = {"pro": "Alex Hormozi", "title": "After Closing 4000+ Sales", "channel": "Alex Hormozi",
                "url": "https://www.youtube.com/watch?v=RVbvhPGFi6E"}
        text = ps.knowledge_md(good_plan(), meta)
        self.assertIn("https://www.youtube.com/watch?v=RVbvhPGFi6E", text)
        self.assertIn("(https://www.youtube.com/watch?v=RVbvhPGFi6E&t=120s)", text)
        self.assertEqual(len(re.findall(r"^### \d+\. ", text, re.M)), 5)
        self.assertIn("`doan-3` — HỎI TRƯỚC RỒI MỚI BÁN (5:00–5:40", text)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Public local editor contracts; run with python tests/ags_test_marketing_editor.py.

Real FFmpeg media; no network/Whisper, source inspection, or mocked editor logic.
The parent owns RED/GREEN execution. Host compatibility is deliberately untested.
"""
from array import array
import copy
import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from ags_common import font_path


def command(*args):
    return subprocess.run([str(a) for a in args], check=True, capture_output=True).stdout


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


class MarketingEditorContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if importlib.util.find_spec("ags_marketing_editor") is None:
            raise AssertionError("Missing public marketing editor engine: implement approved inspect/validate/approve/render contract")
        cls.editor = importlib.import_module("ags_marketing_editor")
        cls.assets = tempfile.TemporaryDirectory(prefix="ags_editor_contract_assets_")
        cls.asset_dir = Path(cls.assets.name)
        cls.addClassCleanup(cls.assets.cleanup)
        for name, color in (("speaker", "red"), ("proof", "blue")):
            command("ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"color={color}:s=160x284:r=10:d=3",
                    "-f", "lavfi", "-i", "sine=frequency=440:duration=3", "-shortest", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", cls.asset_dir / f"{name}.mp4")
        shutil.copyfile(font_path("bold"), cls.asset_dir / "persona.ttf")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ags_editor_contract_")
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        for asset in self.asset_dir.iterdir():
            shutil.copyfile(asset, self.work / asset.name)
        self.words = [
            {"start": 0.1, "end": 0.4, "word": "không"},
            {"start": 0.45, "end": 0.8, "word": "hứa"},
            {"start": 1.1, "end": 1.4, "word": "kết"},
            {"start": 1.45, "end": 1.8, "word": "quả"},
        ]
        save(self.work / "speaker.json", {"source": str(self.work / "speaker.mp4"), "duration": 3, "words": self.words})
        self.plan = {
            "version": 1, "objective": "Giải thích giới hạn", "audience": "Chủ doanh nghiệp",
            "format": "education", "sources": {
                "speaker": {"path": "speaker.mp4", "transcript": "speaker.json", "source_note": "Bản ghi người nói"},
                "proof": {"path": "proof.mp4", "source_note": "Bản quay sản phẩm do chủ cung cấp"}},
            "segments": [{"source_id": "speaker", "start": 1, "end": 2, "beat": "mechanism"},
                         {"source_id": "speaker", "start": 0, "end": 1, "beat": "context"}],
            "overlays": [{"source_id": "proof", "source_start": 0, "start": 0.5, "end": 1, "role": "proof",
                          "source_note": "Minh họa thao tác từ bản quay chủ cung cấp"}],
            "persona": {"font": "persona.ttf", "color": "#FFFFFF", "highlight": "#FFD166", "style": "clean"},
            "hook": "", "cta": "", "strict_3c": False,
        }
        self.path = self.work / "plan.json"
        save(self.path, self.plan)

    def test_validate_remaps_reordered_words_and_exclusive_proof_time(self):
        result = self.editor.validate_plan(self.path)
        self.assertAlmostEqual(result["duration"], 2)
        expected = [(0.1, 0.4, "kết"), (0.45, 0.8, "quả"), (1.1, 1.4, "không"), (1.45, 1.8, "hứa")]
        self.assertEqual([w["word"] for w in result["words"]], [w[2] for w in expected])
        for actual, (start, end, _) in zip(result["words"], expected):
            self.assertAlmostEqual(actual["start"], start)
            self.assertAlmostEqual(actual["end"], end)
        self.assertEqual(result["role_durations"], {"a_roll": 1.5, "proof": 0.5, "mood": 0.0})
        self.assertRegex(result["plan_hash"], r"^[a-f0-9]{64}$")

    def test_invalid_intervals_and_provenance_are_rejected(self):
        cases = []
        for value in (-1, 3.1, math.inf, math.nan, True):
            bad = copy.deepcopy(self.plan)
            bad["segments"][0]["end"] = value
            cases.append(bad)
        bad = copy.deepcopy(self.plan)
        bad["segments"][1]["start"] = 0.2  # Splits the negation "không".
        cases.append(bad)
        bad = copy.deepcopy(self.plan)
        bad["overlays"].append(dict(bad["overlays"][0], start=0.75, end=1.25))
        cases.append(bad)
        bad = copy.deepcopy(self.plan)
        bad["overlays"][0]["source_start"] = 2.8
        cases.append(bad)
        bad = copy.deepcopy(self.plan)
        bad["overlays"][0]["source_note"] = ""
        cases.append(bad)
        # Valid in-range, word-safe times that cannot be represented at 30fps.
        for section, field, value in (("segments", "end", 2.01),
                                      ("overlays", "start", 0.51),
                                      ("overlays", "source_start", 0.01)):
            bad = copy.deepcopy(self.plan)
            bad[section][0][field] = value
            cases.append(bad)
        for index, plan in enumerate(cases):
            with self.subTest(case=index):
                save(self.path, plan)
                with self.assertRaises(ValueError):
                    self.editor.validate_plan(self.path)
        transcript = self.work / "speaker.json"
        for control in ("\n", "\r"):
            with self.subTest(transcript_control=repr(control)):
                words = copy.deepcopy(self.words)
                words[0]["word"] = f"không{control}Dialogue: injected"
                save(transcript, {"source": "speaker.mp4", "duration": 3, "words": words})
                save(self.path, self.plan)
                with self.assertRaisesRegex(ValueError, "subtitle control"):
                    self.editor.validate_plan(self.path)

    def test_strict_hook_checks_spoken_opening_not_only_good_card(self):
        words = copy.deepcopy(self.words)
        for word, text in zip(words, ("mọi", "người", "Xin", "chào")):
            word["word"] = text
        save(self.work / "speaker.json", {"source": "speaker.mp4", "duration": 3, "words": words})
        self.plan["hook"] = "3 lỗi khiến bạn mất khách?"
        save(self.path, self.plan)
        audit = self.editor.validate_plan(self.path)["hook_audit"]
        self.assertFalse(audit["ok"])
        self.assertEqual(audit["disposition"], "ADVISORY_WARNING")
        self.plan["strict_3c"] = True
        save(self.path, self.plan)
        with self.assertRaisesRegex(ValueError, "Strict hook audit"):
            self.editor.approve_plan(self.path, "plan", "Duyệt thẻ nhưng lời mở đầu không đạt")
        for word, text in zip(words, ("khách", "hàng?", "Mất", "3")):
            word["word"] = text
        save(self.work / "speaker.json", {"source": "speaker.mp4", "duration": 3, "words": words})
        self.assertTrue(self.editor.validate_plan(self.path)["hook_audit"]["ok"])

    def test_inspect_audio_only_silence_writes_truthful_transcript(self):
        audio = self.work / "silent.wav"
        command("ffmpeg", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono",
                "-t", "3", audio)
        transcript = self.work / "inspection.json"
        result = self.editor.inspect_source(audio, transcript)
        self.assertTrue(result["audio"])
        self.assertFalse(result["video"])
        self.assertAlmostEqual(result["duration"], 3, places=2)
        data = json.loads(transcript.read_text(encoding="utf-8"))
        self.assertEqual(Path(data["source"]), audio.resolve())
        self.assertEqual(data["words"], [])
        self.assertEqual(data["speech_status"], "NO_SPEECH_SILENT_MEDIA")

    def test_content_hash_binds_transcript_not_mtime_or_json_key_order(self):
        original = self.editor.validate_plan(self.path)["plan_hash"]
        self.path.write_text(json.dumps(self.plan, sort_keys=True, indent=4, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(self.editor.validate_plan(self.path)["plan_hash"], original)
        transcript = self.work / "speaker.json"
        stat = transcript.stat()
        transcript.write_text(transcript.read_text(encoding="utf-8").replace("không", "KHÔNG"), encoding="utf-8")
        os.utime(transcript, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        self.assertNotEqual(self.editor.validate_plan(self.path)["plan_hash"], original)

    def test_stale_source_approval_and_missing_approval_do_not_publish(self):
        output = self.work / "outputs"
        with self.assertRaises(ValueError):
            self.editor.render_plan(self.path, output, "draft")
        self.editor.approve_plan(self.path, "plan", "Đã duyệt kế hoạch và nguồn")
        source = self.work / "speaker.mp4"
        stat = source.stat()
        with source.open("ab") as stream:
            stream.write(b"changed")
        os.utime(source, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        with self.assertRaises(ValueError):
            self.editor.render_plan(self.path, output, "draft")
        self.assertFalse((output / "draft").exists())
        self.assertFalse((output / "final").exists())

    def test_unsafe_output_alias_preserves_source_bytes(self):
        self.editor.approve_plan(self.path, "plan", "Đã duyệt")
        before = hashlib.sha256((self.work / "speaker.mp4").read_bytes()).hexdigest()
        alias = self.work / "alias"
        alias.symlink_to(self.work, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.editor.render_plan(self.path, alias, "draft")
        self.assertEqual(hashlib.sha256((self.work / "speaker.mp4").read_bytes()).hexdigest(), before)

    def test_voiceover_uses_recording_words_in_output_time(self):
        audio = self.work / "voice.wav"
        command("ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=880:duration=3", audio)
        save(self.work / "voice.json", {"source": str(audio), "duration": 3,
                                       "words": [{"start": 0.2, "end": 0.8, "word": "Thuyết minh"}]})
        self.plan["voiceover"] = {"path": "voice.wav", "transcript": "voice.json", "source_note": "Ghi âm được duyệt"}
        save(self.path, self.plan)
        result = self.editor.validate_plan(self.path)
        self.assertEqual(result["words"], [{"start": 0.2, "end": 0.8, "word": "Thuyết minh"}])
        self.editor.approve_plan(self.path, "plan", "Duyệt bản thuyết minh thay tiếng gốc")
        rendered = self.editor.render_plan(self.path, self.work / "voice-render", "draft")
        pcm = array("h")
        pcm.frombytes(command("ffmpeg", "-v", "error", "-ss", "0.4", "-i", rendered["video"],
                              "-t", "0.4", "-vn", "-ac", "1", "-ar", "48000",
                              "-f", "s16le", "pipe:1"))
        # Distinguishes replacement (880Hz) from the 440Hz source or their mixture.
        crossings = sum(a <= 0 < b for a, b in zip(pcm, pcm[1:]))
        frequency = crossings * 48000 / len(pcm)
        self.assertAlmostEqual(frequency, 880, delta=20)
        srt = Path(rendered["srt"]).read_text(encoding="utf-8")
        self.assertIn("00:00:00,200 --> 00:00:00,800\nThuyết minh", srt)
        self.assertNotIn("không", srt)
        self.plan["voiceover"]["path"] = "missing.wav"
        save(self.path, self.plan)
        with self.assertRaises(ValueError):
            self.editor.validate_plan(self.path)

    def test_batch_failure_does_not_abort_or_borrow_approval(self):
        bad = self.work / "bad.json"
        bad.write_text("not json", encoding="utf-8")
        self.editor.approve_plan(self.path, "plan", "Đã duyệt chỉ kế hoạch này")
        result = self.editor.render_batch([bad, self.path], self.work / "batch", "draft")
        self.assertEqual([job["status"] for job in result["jobs"]], ["error", "ok"])
        self.assertTrue(Path(result["jobs"][1]["result"]["video"]).is_file())
        self.assertNotIn("result", result["jobs"][0])
        draft = result["jobs"][1]["result"]
        draft_dir = Path(draft["video"]).parent
        self.editor.approve_plan(self.path, "draft", "Đã xem đúng bản nháp")
        approved_fonts = {p.name: p.read_bytes() for p in (draft_dir / "fonts").iterdir()}
        shutil.copyfile(self.work / "persona.ttf", draft_dir / "fonts" / "unapproved.ttf")
        (draft_dir / "fonts" / "unapproved-link.ttf").symlink_to(self.work / "persona.ttf")
        exported = self.editor.render_plan(self.path, draft_dir.parent, "final")
        final_video = Path(exported["video"])
        self.assertEqual(final_video.name, "final.mp4")
        self.assertEqual(hashlib.sha256(final_video.read_bytes()).digest(),
                         hashlib.sha256(Path(draft["video"]).read_bytes()).digest())
        self.assertEqual({p.name: p.read_bytes() for p in (final_video.parent / "fonts").iterdir()},
                         approved_fonts)

    def test_real_draft_has_timed_proof_and_stale_draft_cannot_be_final(self):
        self.plan["hook"] = "3 giới hạn\ncần hiểu"
        self.plan["cta"] = "Đọc kỹ giới hạn\r\ntrước khi áp dụng cho doanh nghiệp của bạn"
        save(self.path, self.plan)
        output = self.work / "render space ' quote \\ colon: comma, [brackets]"
        self.editor.approve_plan(self.path, "plan", "Đã duyệt nguồn, lời và thời gian")
        result = self.editor.render_plan(self.path, output, "draft")
        self.assertEqual(result["status"], "ok")
        for key in ("video", "subtitles", "srt", "contact_sheet", "report", "provenance", "plan_snapshot"):
            self.assertTrue(Path(result[key]).is_file(), key)
        video = Path(result["video"])
        # Independent image samples, away from captions: actual replacement, not JSON-only proof.
        def pixel_at(second):
            return tuple(command("ffmpeg", "-v", "error", "-ss", second, "-i", video,
                                 "-vf", "crop=2:2:10:10,scale=1:1", "-frames:v", "1", "-f", "rawvideo",
                                 "-pix_fmt", "rgb24", "pipe:1")[:3])
        red, blue, red_again = pixel_at("0.2"), pixel_at("0.7"), pixel_at("1.2")
        self.assertGreater(red[0], red[2] + 100)
        self.assertGreater(blue[2], blue[0] + 100)
        self.assertGreater(red_again[0], red_again[2] + 100)
        subtitle = Path(result["subtitles"]).read_text(encoding="utf-8")
        self.assertLess(subtitle.index("kết"), subtitle.index("không"))
        dialogues = [re.sub(r"\{[^}]*\}", "", line).replace(r"\N", " ")
                     for line in subtitle.splitlines() if line.startswith("Dialogue:")]
        self.assertTrue(any("3 giới hạn cần hiểu" in line for line in dialogues))
        self.assertTrue(any("Đọc kỹ giới hạn" in line and "doanh nghiệp" in line for line in dialogues))
        self.assertNotIn("\r", subtitle)
        self.assertEqual(Path(result["srt"]).read_text(encoding="utf-8"),
                         "1\n00:00:00,100 --> 00:00:00,800\nkết quả\n\n"
                         "2\n00:00:01,100 --> 00:00:01,800\nkhông hứa\n\n")
        self.assertEqual(json.loads(Path(result["plan_snapshot"]).read_text(encoding="utf-8")), self.plan)
        provenance = json.loads(Path(result["provenance"]).read_text(encoding="utf-8"))
        proof = [item for item in provenance["encoded_intervals"] if item["role"] == "proof"]
        self.assertEqual([(item["start_frame"], item["end_frame"], item["source_id"]) for item in proof],
                         [(15, 30, "proof")])
        self.assertEqual(provenance["overlays"][0]["source_note"], self.plan["overlays"][0]["source_note"])
        hashes = {item["path"]: item["sha256"] for item in provenance["assets"]}
        self.assertEqual(hashes[str((self.work / "proof.mp4").resolve())],
                         hashlib.sha256((self.work / "proof.mp4").read_bytes()).hexdigest())
        report = json.loads(Path(result["report"]).read_text(encoding="utf-8"))
        self.assertEqual(report["human_review"], "NOT_CHECKED")
        self.assertEqual(report["role_durations"], {"a_roll": 1.5, "proof": 0.5, "mood": 0.0})
        self.editor.approve_plan(self.path, "draft", "Đã xem và nghe bản nháp")
        with video.open("ab") as stream:
            stream.write(b"tampered")
        with self.assertRaises(ValueError):
            self.editor.render_plan(self.path, output, "final")
        self.assertFalse((output / "final").exists())


if __name__ == "__main__":
    unittest.main()

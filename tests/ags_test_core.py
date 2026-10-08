#!/usr/bin/env python3
"""
AGS (Agent Space) — kiểm thử nhanh phần lõi (không cần Whisper/rembg/Internet): vùng an toàn, NFC, lập kế hoạch cắt
lặng + crossfade, phụ đề .ASS karaoke/hook, harness (mã thoát 0/1/2 + contact sheet).

Chạy:  python tests/ags_test_core.py      (cần FFmpeg trong PATH)
"""

import subprocess
import sys
import tempfile
import unicodedata
from fractions import Fraction
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import ags_cut_silence as cut  # noqa: E402
from ags_common import fit_text, group_word_lists, nfc, safe_box  # noqa: E402
from ags_editorial_sub import format_ass_time, parse_keywords, write_ass  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

GUARD = ROOT / "harness" / "ags_anti_slop_guard.py"


def test_safe_zone_and_nfc():
    assert safe_box(1080, 1920) == (120, 288, 780, 1248), safe_box(1080, 1920)
    assert safe_box(1920, 1080) == (154, 86, 1766, 994), safe_box(1920, 1080)
    decomposed = unicodedata.normalize("NFD", "Tiếng Việt đẹp")
    assert decomposed != "Tiếng Việt đẹp" and nfc(decomposed) == "Tiếng Việt đẹp"
    _, lines = fit_text(ImageDraw.Draw(Image.new("RGB", (10, 10))), decomposed, "bold", 2000, 1, 40, 20)
    assert lines == ["Tiếng Việt đẹp"], lines


def test_cut_planning_and_crossfade():
    sr = cut.SAMPLE_RATE
    t = np.arange(int(6.0 * sr)) / sr
    hum = 0.004 * np.sin(2 * np.pi * 110 * t)                       # nền nhỏ, liên tục: cắt cứng sẽ lách cách
    speech = np.zeros_like(t)
    for a, b in [(0.5, 1.5), (3.0, 4.0), (4.25, 5.2)]:              # khoảng nghỉ 1.5 s (cắt) và 0.25 s (giữ)
        m = (t >= a) & (t < b)
        speech[m] = 0.3 * np.sin(2 * np.pi * 220 * t[m])
    audio = np.stack([hum + speech] * 2, axis=1).astype(np.float32)
    db = cut.loudness_db(audio.mean(axis=1), sr)
    silences = cut.find_silences(db, -30.0, 0.4)
    assert len(silences) == 3, silences                             # đầu, giữa 1.5 s, cuối
    keep = cut.plan_keep_ranges(6.0, silences, [], db)
    assert len(keep) == 2, keep
    assert abs(keep[0][0] - (0.5 - cut.PRE_ROLL)) < 0.03 and abs(keep[0][1] - (1.5 + cut.POST_ROLL)) < 0.03, keep
    assert abs(keep[1][0] - (3.0 - cut.PRE_ROLL)) < 0.03 and abs(keep[1][1] - (5.2 + cut.POST_ROLL)) < 0.03, keep
    fps = Fraction(30)
    frames = cut.to_frames(keep, fps, 180)
    joined = cut.join_audio(audio, frames, fps, sr)
    assert len(joined) == sum(b - a for a, b in frames) * sr // 30  # tiếng dài đúng bằng hình
    join = int((frames[0][1] - frames[0][0]) / 30 * sr)

    def jump(x):  # bước nhảy lớn nhất quanh mối nối so với bình thường
        d = np.abs(np.diff(x[:, 0]))
        return d[join - 48:join + 48].max() / np.percentile(np.concatenate([d[join - 1920:join - 144],
                                                                            d[join + 144:join + 1920]]), 99.9)
    hard = jump(cut.join_audio(audio, frames, fps, sr, crossfade=0.0))
    soft = jump(joined)
    assert hard > 3.0 and soft < 1.5, (hard, soft)


def test_ass_karaoke_and_hook(tmp):
    words = [(0.0, 0.4, "Xin"), (0.4, 0.8, "chào"), (0.8, 1.3, "phụ"), (1.3, 1.8, "đề.")]
    groups = group_word_lists(words, 24, 2.5)
    ass = tmp / "k.ass"
    write_ass(groups, ass, 1080, 1920, "karaoke", "#FFD60A", parse_keywords("phụ đề"), ("HOOK ĐẦU", 3.0))
    text = ass.read_text(encoding="utf-8")
    events = [l for l in text.splitlines() if l.startswith("Dialogue:")]
    assert events[0].startswith("Dialogue: 0,0:00:00.00,0:00:03.00,Hook"), events[0]
    karaoke = events[1:]
    assert len(karaoke) == 4, karaoke
    assert "{\\1c&H000AD6FF&}Xin{\\r}" in karaoke[0] and "{\\1c&H000AD6FF&}phụ{\\r}" in karaoke[0], karaoke[0]
    assert ",0:00:00.40,0:00:00.80," in karaoke[1]
    assert ",2,120,300,672,1" in text, "lề phụ đề phải khớp vùng an toàn 1080x1920"
    assert format_ass_time(59.999) == "0:01:00.00" and format_ass_time(3725.5) == "1:02:05.50"


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *[str(a) for a in args]], check=True)


def guard(path, *extra):
    return subprocess.run([sys.executable, str(GUARD), str(path), *[str(e) for e in extra]],
                          capture_output=True, text=True)


def test_harness_exit_codes(tmp):
    good, black, mute, quiet = (tmp / f"{n}.mp4" for n in ("good", "black", "mute", "quiet"))
    common = ["-t", "4", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-shortest"]
    ffmpeg("-f", "lavfi", "-i", "testsrc2=size=540x960:rate=30", "-f", "lavfi", "-i", "sine=frequency=330",
           "-af", "loudnorm=I=-14:LRA=11:TP=-2", *common, good)
    ffmpeg("-f", "lavfi", "-i", "color=black:size=540x960:rate=30", "-f", "lavfi", "-i", "sine=frequency=330",
           "-af", "loudnorm=I=-14:LRA=11:TP=-2", *common, black)
    ffmpeg("-f", "lavfi", "-i", "testsrc2=size=540x960:rate=30", "-f", "lavfi",
           "-i", "anullsrc=channel_layout=stereo:sample_rate=48000", *common, mute)
    ffmpeg("-f", "lavfi", "-i", "testsrc2=size=540x960:rate=30", "-f", "lavfi", "-i", "sine=frequency=330",
           "-af", "volume=-30dB", *common, quiet)
    sheet = tmp / "sheet.jpg"
    res = guard(good, "--contact-sheet", sheet, "--frames", 6)
    assert res.returncode == 0, res.stdout + res.stderr
    with Image.open(sheet) as im:
        assert im.size == (4 * 270, 2 * (480 + 34)), im.size
    assert guard(black).returncode == 1
    assert guard(mute).returncode == 1
    res = guard(quiet)
    assert res.returncode == 2 and "LUFS" in res.stdout, res.stdout


def main():
    with tempfile.TemporaryDirectory(prefix="ags_test_core_") as tmp:
        tmp = Path(tmp)
        steps = [
            ("Vùng an toàn 9:16 + NFC", test_safe_zone_and_nfc),
            ("Cắt lặng: lập kế hoạch + crossfade không lách cách", test_cut_planning_and_crossfade),
            ("Phụ đề .ASS: karaoke, từ khoá, hook khung 0", lambda: test_ass_karaoke_and_hook(tmp)),
            ("Harness: exit 0/1/2 + contact sheet", lambda: test_harness_exit_codes(tmp)),
        ]
        for i, (label, fn) in enumerate(steps, 1):
            fn()
            print(f"[{i}/{len(steps)}] OK  {label}")
        print(f"✅ {len(steps)}/{len(steps)} nhóm kiểm thử lõi đạt.")


if __name__ == "__main__":
    main()

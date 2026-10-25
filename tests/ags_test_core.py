#!/usr/bin/env python3
"""
AGS (Agent Space) — kiểm thử nhanh phần lõi (không cần Whisper/rembg/Internet): vùng an toàn, NFC, lập kế hoạch cắt
lặng + crossfade, phụ đề .ASS karaoke/hook (xuống dòng đọc được, lời đọc script), harness (mã thoát 0/1/2 + contact sheet),
khoá bản quyền client RSA (cấp mã, đúng/sai máy, giả chữ ký, hết hạn).

Chạy:  python tests/ags_test_core.py      (cần FFmpeg trong PATH)
"""

import json
import os
import random
import re
import subprocess
import sys
import tempfile
import unicodedata
from fractions import Fraction
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import ags_client_license as lic  # noqa: E402
import ags_cut_silence as cut  # noqa: E402
from ags_common import align_script_words, fit_text, group_word_lists, nfc, safe_box  # noqa: E402
from ags_editorial_sub import STYLES, format_ass_time, parse_keywords, write_ass  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

GUARD = ROOT / "harness" / "ags_anti_slop_guard.py"


def test_safe_zone_and_nfc():
    assert safe_box(1080, 1920) == (200, 288, 880, 1248), safe_box(1080, 1920)  # đối xứng: tâm hộp chữ x = 540
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
    assert ",0:00:00.40,0:00:00.80," in karaoke[1]
    assert format_ass_time(59.999) == "0:01:00.00" and format_ass_time(3725.5) == "1:02:05.50"


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *[str(a) for a in args]], check=True)


def guard(path, *extra):
    return subprocess.run([sys.executable, str(GUARD), str(path), *[str(e) for e in extra]],
                          capture_output=True, text=True)


def test_caption_render_bounds(tmp):
    from ags_editorial_sub import subtitles_filter
    words = [(0, 1, "WWWWWWWWWWWWWWWWWWWWWWWW"), (1, 2, "Tiếng Việt")]
    ass, image = tmp / "bounds.ass", tmp / "bounds.png"
    fonts = write_ass([words], ass, 1080, 1920, "karaoke")
    ffmpeg("-f", "lavfi", "-i", "color=0x444444:s=1080x1920:d=1", "-vf",
           subtitles_filter(ass, fonts), "-frames:v", "1", image)
    pixels = np.asarray(Image.open(image).convert("RGB"))
    mask = np.max(np.abs(pixels.astype(int) - pixels[0, 0].astype(int)), axis=2) > 10
    ys, xs = np.where(mask)
    assert xs.size, "Caption must remain visible"
    x0, y0, x1, y1 = safe_box(1080, 1920)
    assert xs.min() >= x0 and xs.max() < x1 and ys.min() >= y0 and ys.max() < y1, (
        int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


SPEECH = ("Đôi khi, bạn chỉ cần chậm lại một chút. Nhìn những con sóng đi qua, hít thở thật sâu, "
          "và dành cho mình một khoảng lặng.")


def timed(text, step=0.35):
    return [(i * step, (i + 1) * step, w) for i, w in enumerate(text.split())]


def dialogue_bodies(ass_text):
    return [line.split(",,0,0,0,,", 1)[1] for line in ass_text.splitlines() if line.startswith("Dialogue:")]


def test_caption_wrap_is_legible(tmp):
    for style in ("clean", "editorial", "karaoke"):
        cfg = STYLES[style]
        groups = group_word_lists(timed(SPEECH), cfg["max_chars"], cfg["max_seconds"])
        assert len(groups) >= 3, [len(g) for g in groups]
        ass = tmp / f"wrap_{style}.ass"
        write_ass(groups, ass, 1080, 1920, style, "#FFD60A", parse_keywords("chậm lại"))
        bodies = dialogue_bodies(ass.read_text(encoding="utf-8"))
        base = round(1080 * cfg["size"])
        for body in bodies:
            fs = int(re.match(r"\{\\q2\\fs(\d+)[^}]*\}", body).group(1))
            assert fs >= 0.04 * 1080 and fs >= 0.75 * base, (style, fs)
            assert body.count("\\N") <= 1, f"Quá 2 dòng: {body}"
            assert "\\fscx" not in body, f"Thu hẹp cả câu thay vì xuống dòng: {body}"
        # Lời không bị mất/đổi thứ tự: bỏ thẻ ASS và \N thì phải ra lại đúng câu của nhóm
        texts = [re.sub(r"\{[^}]*\}", "", b).replace("\\N", " ") for b in bodies]
        spoken = [" ".join(w[2] for w in g) for g in groups]
        assert texts == ([s for g, s in zip(groups, spoken) for _ in g] if style == "karaoke" else spoken), texts
        assert any("\\N" in b for b in bodies), "Câu dài phải xuống dòng"
        # Cụm "chậm lại" được tô đủ cả hai từ dù bị ngắt giữa hai caption (clean ngắt ở 28 ký tự); từ khác không bị tô
        lit = [w for b in bodies for w in re.findall(r"\{\\1c&H000AD6FF&\}([^{]+)", b)]
        assert lit == ["chậm", "lại"] or style == "karaoke" and {"chậm", "lại"} <= set(lit), (style, lit)
    # Hook dài: xuống dòng ở cỡ chữ gốc, tối đa 3 dòng
    ass = tmp / "hook.ass"
    write_ass([], ass, 1080, 1920, "editorial", hook=("90 NGÀY KIẾM MỘT TỶ", 3.0))
    hook = dialogue_bodies(ass.read_text(encoding="utf-8"))[0]
    assert hook.count("\\N") <= 2 and "\\fscx" not in hook, hook


def test_caption_render_is_large_enough(tmp):
    from ags_editorial_sub import subtitles_filter
    words = timed("Nhìn những con sóng đi qua, hít thở thật sâu", 0.5)
    for style in ("clean", "editorial"):
        ass, image = tmp / f"large_{style}.ass", tmp / f"large_{style}.png"
        fonts = write_ass([words], ass, 1080, 1920, style)
        ffmpeg("-f", "lavfi", "-i", "color=0x444444:s=1080x1920:d=1", "-vf",
               subtitles_filter(ass, fonts), "-frames:v", "1", image)
        pixels = np.asarray(Image.open(image).convert("RGB"))
        ys, xs = np.where(np.max(np.abs(pixels.astype(int) - pixels[0, 0].astype(int)), axis=2) > 10)
        x0, y0, x1, y1 = safe_box(1080, 1920)
        assert xs.min() >= x0 and xs.max() < x1 and ys.min() >= y0 and ys.max() < y1, style
        # Một dòng thu nhỏ theo bề ngang cao khoảng 35 px; xuống dòng ở cỡ chữ thật thì khối chữ cao hơn 1,5 lần cỡ chữ tối thiểu
        assert ys.max() - ys.min() >= 1.5 * 0.05 * 1080, (style, int(ys.max() - ys.min()))


def test_bt_vi_centered_large_with_example_label(tmp):
    """BR-006/FR-012 (24/10): vùng an toàn đối xứng → hook và phụ đề bt_vi căn giữa x = 540; hook ≥ 72 px (ưu tiên 84),
    phụ đề 72 px khi vừa 2 dòng; nhãn "ví dụ" ≥ 40 px đứng đầu cụm phụ đề có số minh hoạ."""
    from ags_editorial_sub import subtitles_filter
    words = timed("Một ly cà phê 35k bằng con số ví dụ", 0.4)
    ass = tmp / "btvi.ass"
    fonts = write_ass([words], ass, 1080, 1920, "bt_vi", hook=("30 năm kinh doanh trong 60 giây", 2.5),
                      label="ví dụ", label_terms=["35k"])
    bodies = dialogue_bodies(ass.read_text(encoding="utf-8"))
    sizes = [int(re.match(r"\{\\q2\\fs(\d+)", b).group(1)) for b in bodies]
    assert sizes[0] >= 72 and sizes[1:] == [72] * (len(bodies) - 1), sizes
    tagged = [b for b in bodies[1:] if "(ví dụ)" in b]
    assert len(tagged) == 1 and "35k" in tagged[0] and re.search(r"\\fs(\d+)[^}]*\}\(ví dụ\)", tagged[0]), bodies
    assert int(re.search(r"\\fs(\d+)[^}]*\}\(ví dụ\)", tagged[0]).group(1)) >= 40
    for t in (0.2, 0.9):  # khung có hook + cụm đầu; khung có cụm mang nhãn
        image = tmp / f"btvi_{t}.png"
        ffmpeg("-f", "lavfi", "-i", "color=0x444444:s=1080x1920:d=1", "-vf",
               f"setpts=PTS+{t}/TB,{subtitles_filter(ass, fonts)}", "-frames:v", "1", image)
        pixels = np.asarray(Image.open(image).convert("RGB"))
        x0, y0, x1, y1 = safe_box(1080, 1920)
        for top, bottom in ((0, 1920 // 2), (1920 // 2, 1920)):  # hook ở nửa trên, phụ đề ở nửa dưới: từng khối căn giữa
            band = pixels[top:bottom]
            ys, xs = np.where(np.max(np.abs(band.astype(int) - band[0, 0].astype(int)), axis=2) > 10)
            if not xs.size:
                continue
            assert xs.min() >= x0 and xs.max() < x1 and ys.min() + top >= y0 and ys.max() + top < y1, (t, top)
            assert abs((xs.min() + xs.max()) / 2 - 540) <= 12, (t, top, int(xs.min()), int(xs.max()))


def test_script_alignment_keeps_exact_words():
    script = "Đôi khi, bạn chỉ cần chậm lại một chút."
    heard = [(0.2, 0.5, "Được"), (0.5, 0.8, "khi"), (0.8, 1.0, "bạn"), (1.0, 1.3, "chỉ"), (1.3, 1.6, "cần"),
             (1.6, 2.0, "chậm"), (2.0, 2.3, "lại"), (2.3, 2.6, "một"), (2.6, 3.0, "chút")]
    words = align_script_words(script, heard)
    assert [w[2] for w in words] == script.split(), words
    assert 0.2 <= words[0][0] < words[0][1] <= 0.5 + 1e-9, words[0]  # từ Whisper nghe sai vẫn có mốc hợp lý
    assert words[1][:2] == (0.5, 0.8) and words[-1][:2] == (2.6, 3.0)
    assert all(a[0] <= b[0] and a[0] <= a[1] for a, b in zip(words, words[1:])), words
    # Whisper bỏ sót hẳn nửa sau: từ còn thiếu chia đều theo độ dài chữ, không bị mất
    partial = align_script_words(script, heard[:5])
    assert [w[2] for w in partial] == script.split() and all(w[0] <= w[1] for w in partial), partial
    # Chuỗi lặp ≥ 3 từ giống nhau: phụ đề từ Whisper bị gộp, nhưng lời script thì giữ nguyên
    repeated = timed("ha ha ha xong")
    assert len(group_word_lists(repeated, 40, 5.0, clean=False)[0]) == 4
    assert len(group_word_lists(repeated, 40, 5.0)[0]) == 2
    for bad in ("", "  ", "— …"):
        try:
            align_script_words(bad, heard)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Script {bad!r} phải báo lỗi")


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


def _test_prime(bits, rng):
    while True:
        n = rng.getrandbits(bits) | (1 << (bits - 1)) | 1
        if all(n % p for p in (3, 5, 7, 11, 13, 17, 19, 23, 29, 31)) and all(
                _miller_rabin(n, rng.randrange(2, n - 1)) for _ in range(24)):
            return n


def _miller_rabin(n, a):
    d, s = n - 1, 0
    while d % 2 == 0:
        d, s = d // 2, s + 1
    x = pow(a, d, n)
    if x in (1, n - 1):
        return True
    for _ in range(s - 1):
        x = pow(x, 2, n)
        if x == n - 1:
            return True
    return False


def test_client_license_guard(tmp):
    rng = random.Random(2026)
    while True:  # khoá thử 1024-bit sinh tại chỗ; không dùng khoá ký thật của bên cấp mã
        p, q = _test_prime(512, rng), _test_prime(512, rng)
        phi = (p - 1) * (q - 1)
        if p != q and phi % lic.PUBLIC_E:
            break
    n, d = p * q, pow(lic.PUBLIC_E, -1, phi)
    key = tmp / "issuer_test_key.json"
    key.write_text(json.dumps({"e": lic.PUBLIC_E, "n_hex": f"{n:x}", "d_hex": f"{d:x}"}), encoding="utf-8")
    me, real_n = lic.get_machine_id(), lic.PUBLIC_N
    assert re.fullmatch(r"[0-9a-f]{16}", me), me
    saved_env = {k: os.environ.pop(k, None) for k in
                 ("AGS_REQUIRE_CLIENT_LICENSE", "AGS_CLIENT_LICENSE_TOKEN", "AGS_CLIENT_LICENSE_PATH")}
    lic.PUBLIC_N = n
    try:
        token = lic.issue_license_token("khach-thu", mid="abcdef0123456789", days=1, issuer_key_path=key)
        assert token.startswith("AGS1.") and token.count(".") == 2, token
        ok = lic.verify_license_token(token, "abcdef0123456789")
        assert ok["valid"] and ok["payload"]["sub"] == "khach-thu" and ok["payload"]["tier"] == "commercial", ok
        assert not lic.verify_license_token(token, "0000000000000000")["valid"]
        head, payload, sig = token.split(".")
        forged_sig = sig[:-2] + ("AA" if sig[-2:] != "AA" else "BB")
        assert "chữ ký" in lic.verify_license_token(f"{head}.{payload}.{forged_sig}", "abcdef0123456789")["reason"]
        forged_payload = lic._b64e(lic._b64d(payload).replace(b"abcdef0123456789", b"*"))
        assert not lic.verify_license_token(f"{head}.{forged_payload}.{sig}", "abcdef0123456789")["valid"]
        expired = lic.issue_license_token("khach-thu", mid="*", days=-1, issuer_key_path=key)
        assert "hết hạn" in lic.verify_license_token(expired)["reason"]

        lic_file = tmp / "client_license.json"
        if not (lic.ROOT / ".require_client_license").exists():
            assert lic.assert_client_licensed(lic_file) is None  # cổng tắt: không chặn
        os.environ["AGS_REQUIRE_CLIENT_LICENSE"] = "1"
        for bad in (lambda: lic.assert_client_licensed(lic_file),
                    lambda: lic.activate_license_token(token, lic_file),
                    lambda: lic.activate_license_token(expired, lic_file)):
            try:
                bad()
                raise AssertionError("Phải chặn bằng PermissionError")
            except PermissionError as error:
                assert "E-ags-reels-pipeline-007" in str(error), error
        seat = lic.issue_license_token("khach-thu", mid=me, days=30, issuer_key_path=key)
        lic.activate_license_token(seat, lic_file)
        assert lic_file.stat().st_mode & 0o777 == 0o600 or sys.platform == "win32"
        assert json.loads(lic_file.read_text(encoding="utf-8"))["machine_id"] == me
        assert lic.assert_client_licensed(lic_file)["valid"]
        os.environ["AGS_CLIENT_LICENSE_TOKEN"] = f"{head}.{payload}.{forged_sig}"
        try:
            lic.assert_client_licensed(lic_file)
            raise AssertionError("Token giả qua biến môi trường phải bị chặn")
        except PermissionError as error:
            assert "E-ags-reels-pipeline-007" in str(error), error
    finally:
        lic.PUBLIC_N = real_n
        for k, v in saved_env.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v
    assert not lic.verify_license_token(seat)["valid"], "Khoá thử không được qua modulus công khai thật"


def main():
    with tempfile.TemporaryDirectory(prefix="ags_test_core_") as tmp:
        tmp = Path(tmp)
        steps = [
            ("Phụ đề bt_vi: căn giữa, chữ to, nhãn ví dụ", lambda: test_bt_vi_centered_large_with_example_label(tmp)),
            ("Vùng an toàn 9:16 + NFC", test_safe_zone_and_nfc),
            ("Cắt lặng: lập kế hoạch + crossfade không lách cách", test_cut_planning_and_crossfade),
            ("Phụ đề .ASS: karaoke, từ khoá, hook khung 0", lambda: test_ass_karaoke_and_hook(tmp)),
            ("Phụ đề: xuống dòng cỡ chữ gốc, giữ tô màu + lời", lambda: test_caption_wrap_is_legible(tmp)),
            ("Phụ đề: chữ render đủ lớn, vẫn trong vùng an toàn", lambda: test_caption_render_is_large_enough(tmp)),
            ("Script: giữ đúng từ, mốc từ Whisper", test_script_alignment_keeps_exact_words),
            ("Phụ đề: pixel nằm trong vùng an toàn", lambda: test_caption_render_bounds(tmp)),
            ("Harness: exit 0/1/2 + contact sheet", lambda: test_harness_exit_codes(tmp)),
            ("Bản quyền client: RSA, đúng/sai máy, giả chữ ký, hết hạn", lambda: test_client_license_guard(tmp)),
        ]
        for i, (label, fn) in enumerate(steps, 1):
            fn()
            print(f"[{i}/{len(steps)}] OK  {label}")
        print(f"✅ {len(steps)}/{len(steps)} nhóm kiểm thử lõi đạt.")


if __name__ == "__main__":
    main()

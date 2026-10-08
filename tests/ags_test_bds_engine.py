#!/usr/bin/env python3
"""
AGS (Agent Space) — kiểm thử engine BĐS (scripts/bds + scripts/ags_bds_cli.py).

Chạy:  python tests/ags_test_bds_engine.py [--out THU_MUC]
Mặc định ghi vào thư mục tạm rồi xoá; --out giữ lại ảnh/video/draft để xem. Cần FFmpeg trong PATH.
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

from bds import (AgsCapCutDraft, AgsCinematicStyle, AgsDirectRenderer, AgsLandParcelStyle,  # noqa: E402
                 beat_durations, detect_beats)
from bds.ags_capcut_draft import TEMPLATE  # noqa: E402

CLI = ROOT / "scripts" / "ags_bds_cli.py"
LOTS = [
    {"code": "Lô 01", "status": "SOLD", "rect": [150, 600, 480, 850], "price": "1.2 Tỷ", "area": "120m²"},
    {"code": "Lô 02", "status": "AVAILABLE", "rect": [520, 600, 850, 850], "price": "1.15 Tỷ", "area": "115m²"},
    {"code": "Lô 03", "status": "DEPOSITED", "rect": [150, 900, 480, 1150], "price": "1.3 Tỷ", "area": "130m²"},
]


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *[str(a) for a in args]], check=True)


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration:stream=codec_type,width,height,sample_rate", "-of", "json", str(path)],
                         check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def make_media(out):
    video = out / "clip.mp4"
    ffmpeg("-f", "lavfi", "-i", "testsrc2=size=1080x1920:rate=30:duration=3",
           "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", video)
    music = out / "music.wav"
    ffmpeg("-f", "lavfi", "-i", "sine=frequency=220:duration=8", music)
    voice = out / "voice.wav"  # "giọng" giả: tiếng 300 Hz bật/tắt mỗi 0.5 s
    ffmpeg("-f", "lavfi", "-i", "sine=frequency=300:duration=8", "-af", "volume='lt(mod(t,1),0.5)':eval=frame", voice)
    # Ảnh nền ngang 1920x1080 có lưới + vòng tròn: lộ ngay nếu bị bóp méo
    base = out / "satellite_bg.jpg"
    img = Image.new("RGB", (1920, 1080), (34, 60, 48))
    draw = ImageDraw.Draw(img)
    for x in range(0, 1920, 120):
        draw.line([x, 0, x, 1080], fill=(70, 110, 90), width=2)
    for y in range(0, 1080, 120):
        draw.line([0, y, 1920, y], fill=(70, 110, 90), width=2)
    for cx in (660, 960, 1260):
        draw.ellipse([cx - 120, 420, cx + 120, 660], outline=(230, 200, 120), width=6)
    img.save(base, quality=95)
    return video, music, voice, base


def click_track(path, bpm=120.0, first=0.3, seconds=12.0, sr=22050):
    """Nhạc thử có beat biết trước: kick mỗi beat + pad hợp âm."""
    t = np.arange(int(seconds * sr)) / sr
    y = 0.08 * (np.sin(2 * np.pi * 220 * t) + np.sin(2 * np.pi * 330 * t))
    beats = np.arange(first, seconds - 0.2, 60 / bpm)
    k = np.arange(int(0.12 * sr)) / sr
    for b in beats:
        i = int(b * sr)
        y[i:i + len(k)] += 0.9 * np.sin(2 * np.pi * (60 + 90 * np.exp(-k * 40)) * k) * np.exp(-k * 25)
    pcm = (y / np.abs(y).max() * 0.8 * 32767).astype("<i2")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(sr), "-ac", "1", "-i", "-",
                    str(path)], input=pcm.tobytes(), check=True)
    return beats


def same_keys(label, obj, ref):
    missing, extra = sorted(set(ref) - set(obj)), sorted(set(obj) - set(ref))
    assert not missing and not extra, f"{label}: thiếu {missing}, thừa {extra}"


def test_capcut_draft(out, video, music, photo):
    draft = AgsCapCutDraft("AGS_TEST_draft")
    draft.add_clip(str(video))
    draft.add_clip(str(photo), duration=2.0)
    draft.add_text("BẤT ĐỘNG SẢN 2026", 0.0, 4.0)
    draft.add_music(str(music))
    res = draft.save(out / "AGS_TEST_draft")
    folder = Path(res["draft_dir"])
    raw = (folder / "draft_info.json").read_text(encoding="utf-8")
    assert raw == (folder / "draft_content.json").read_text(encoding="utf-8"), "draft_info/draft_content khác nhau"
    info = json.loads(raw)
    meta = json.loads((folder / "draft_meta_info.json").read_text(encoding="utf-8"))

    same_keys("draft", info, TEMPLATE["draft"])
    same_keys("materials", info["materials"], TEMPLATE["draft"]["materials"])
    same_keys("meta", meta, TEMPLATE["meta"])
    for group, kind in [("videos", "video"), ("audios", "audio"), ("texts", "text"), ("speeds", "speed"),
                        ("canvases", "canvas"), ("sound_channel_mappings", "sound_channel_mapping"),
                        ("placeholder_infos", "placeholder_info"), ("vocal_separations", "vocal_separation"),
                        ("material_animations", "material_animation")]:
        assert info["materials"][group], f"materials.{group} rỗng"
        for item in info["materials"][group]:
            same_keys(f"materials.{group}", item, TEMPLATE[kind])

    ids = {m["id"] for group in info["materials"].values() for m in group}
    tracks = {t["type"]: t for t in info["tracks"]}
    assert sorted(tracks) == ["audio", "text", "video"], sorted(tracks)
    for track in info["tracks"]:
        same_keys("track", track, TEMPLATE["track"])
        for seg in track["segments"]:
            same_keys("segment", seg, TEMPLATE["segment"])
            assert seg["material_id"] in ids and all(r in ids for r in seg["extra_material_refs"]), "tham chiếu hỏng"

    v1, v2 = tracks["video"]["segments"]
    assert v1["target_timerange"]["start"] == 0
    assert v2["target_timerange"]["start"] == v1["target_timerange"]["duration"], "clip 2 không nối liền clip 1"
    assert v2["target_timerange"]["duration"] == 2_000_000
    photo_mat = next(m for m in info["materials"]["videos"] if m["type"] == "photo")
    assert (photo_mat["duration"], photo_mat["width"], photo_mat["height"]) == (10_800_000_000, 1920, 1080)
    text = json.loads(info["materials"]["texts"][0]["content"])
    assert text["text"] == "BẤT ĐỘNG SẢN 2026" and text["styles"][0]["range"] == [0, 17]
    end = max(s["target_timerange"]["start"] + s["target_timerange"]["duration"]
              for t in info["tracks"] for s in t["segments"])
    assert info["duration"] == end == meta["tm_duration"], "duration không khớp"
    assert meta["draft_root_path"] == folder.parent.as_posix() and meta["draft_fold_path"] == folder.as_posix()
    assert len(str(meta["tm_draft_create"])) == 16, "tm_draft_create phải là micro-giây"
    assert len(meta["draft_materials"][0]["value"]) == 3
    try:
        draft.save(folder)
    except FileExistsError:
        pass
    else:
        raise AssertionError("save() ghi đè thư mục đã có")
    return folder


def test_cinematic():
    style = AgsCinematicStyle(bpm=120)
    assert style.calculate_beat_cuts(10.0, 4) == [2.0, 4.0, 6.0, 8.0, 10.0]
    assert style.calculate_beat_cuts(3.0, 2) == [1.0, 2.0, 3.0]
    for hook in ("falling_building", "virtual_staging", "day_to_night"):
        assert style.generate_ai_hook_prompt("Dự án Mẫu", "Đồng Nai", hook)["prompt_en"]
    assert "Đồng Nai" in style.generate_ai_hook_prompt("Dự án Mẫu", "Đồng Nai")["prompt_en"]
    try:
        style.generate_ai_hook_prompt("x", "y", "unknown")
    except ValueError:
        pass
    else:
        raise AssertionError("hook_type sai phải báo lỗi")


def test_land_parcel(out, base):
    style = AgsLandParcelStyle(1080, 1920)
    images = [
        style.render_parcel_boundary(str(base), [(300, 700), (800, 750), (750, 1200), (250, 1150)],
                                     str(out / "parcel_boundary.jpg"), label="LÔ ĐẤT 500M² SỔ ĐỎ"),
        style.render_subdivision_grid(str(base), LOTS, str(out / "subdivision_grid.jpg")),
        style.render_news_ticker_bar(str(base), "Cao tốc Biên Hòa - Vũng Tàu",
                                     "Khởi công mở rộng nút giao thông kết nối trực tiếp khu dân cư phía Đông, "
                                     "dự kiến thông xe cuối năm", str(out / "news_ticker.jpg")),
    ]
    for path in images:
        with Image.open(path) as im:
            assert im.size == (1080, 1920), (path, im.size)
    return images


def test_renderer(out, slides, music):
    mp4 = AgsDirectRenderer(1080, 1920, 30).render_image_slideshow(slides, [2.0] * len(slides),
                                                                   str(out / "bds_slideshow.mp4"), str(music))
    info = probe(mp4)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next(s for s in info["streams"] if s["codec_type"] == "audio")
    assert (v["width"], v["height"]) == (1080, 1920)
    assert abs(float(info["format"]["duration"]) - 6.0) < 0.2, info["format"]["duration"]
    assert a["sample_rate"] == "48000", a["sample_rate"]
    return mp4


def test_beats(out):
    truth = click_track(out / "beats.wav")
    bpm, beats = detect_beats(str(out / "beats.wav"))
    assert abs(bpm - 120) < 1, bpm
    errors = [min(abs(b - t) for b in beats) for t in truth]
    assert max(errors) < 0.02, max(errors)
    durations = beat_durations(beats, 6, 4)
    assert abs(durations[0] - beats[4]) < 1e-6 and all(abs(d - 2.0) < 0.02 for d in durations[1:]), durations


def test_renderer_wipe_voice(out, slides, music, voice):
    mp4 = AgsDirectRenderer(1080, 1920, 30).render_image_slideshow(
        slides, [2.0] * len(slides), str(out / "bds_wipe_voice.mp4"), str(music), str(voice), "wipe", 0.5)
    info = probe(mp4)
    a = next(s for s in info["streams"] if s["codec_type"] == "audio")
    assert abs(float(info["format"]["duration"]) - 2.0 * len(slides)) < 0.2, info["format"]["duration"]
    assert a["sample_rate"] == "48000", a["sample_rate"]
    return mp4


def run_cli(*args):
    res = subprocess.run([sys.executable, str(CLI), *[str(a) for a in args]], capture_output=True, text=True)
    assert res.returncode == 0, f"CLI {args[0]} lỗi: {res.stderr}"
    return json.loads(res.stdout)


def test_cli(out, video, music, base):
    assert run_cli("beats", "--bpm", 128, "--beat-step", 8, "--duration", 15)["cuts"] == [3.75, 7.5, 11.25, 15.0]
    assert abs(run_cli("beats", "--music", out / "beats.wav")["bpm"] - 120) < 1
    assert run_cli("prompt", "--type", "virtual_staging", "--name", "Mẫu", "--location", "Hà Nội")["sound_fx"]
    lots_file = out / "lots.json"
    lots_file.write_text(json.dumps(LOTS, ensure_ascii=False), encoding="utf-8")
    parcel = run_cli("parcel", "--image", base, "--points", "200,600 880,640 820,1250 260,1180",
                     "--label", "THỬA 120 - 500M²", "--out", out / "cli_parcel.jpg")["output"]
    grid = run_cli("subdivision", "--image", base, "--lots", lots_file, "--out", out / "cli_grid.jpg")["output"]
    ticker = run_cli("ticker", "--image", base, "--headline", "Quy hoạch mới", "--text", "Mở rộng đường vành đai",
                     "--out", out / "cli_ticker.jpg")["output"]
    draft = run_cli("draft", "--name", "AGS_TEST_cli", "--clips", video, parcel, grid, "--bpm", 120, "--beat-step", 4,
                    "--title", "ĐẤT NỀN SỔ ĐỎ", "--music", music, "--out", out)
    assert draft["tracks"] == {"video": 3, "text": 1, "audio": 1}, draft["tracks"]
    assert abs(draft["duration_sec"] - 6.0) < 1e-6, draft["duration_sec"]
    render = run_cli("render", "--images", parcel, grid, ticker, "--bpm", 120, "--beat-step", 2,
                     "--music", music, "--out", out / "cli_render.mp4")
    assert abs(float(probe(render["output"])["format"]["duration"]) - 3.0) < 0.2


def main():
    parser = argparse.ArgumentParser(description="Kiểm thử engine BĐS")
    parser.add_argument("--out", help="Giữ kết quả trong thư mục này (mặc định: thư mục tạm, tự xoá)")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="ags_test_bds_") as tmp:
        out = Path(args.out).resolve() if args.out else Path(tmp)
        out.mkdir(parents=True, exist_ok=True)
        video, music, voice, base = make_media(out)
        steps = [
            ("CapCut draft (schema + tham chiếu)", lambda: test_capcut_draft(out, video, music, base)),
            ("Cinematic: beat cuts + prompt", test_cinematic),
            ("Dò BPM/beat từ file nhạc", lambda: test_beats(out)),
            ("Đất nền: polygon / phân lô / ticker", lambda: test_land_parcel(out, base)),
            ("Render slideshow FFmpeg", lambda: test_renderer(out, test_land_parcel(out, base), music)),
            ("Render wipe + giọng đọc (duck nhạc)",
             lambda: test_renderer_wipe_voice(out, test_land_parcel(out, base), music, voice)),
            ("CLI: beats/prompt/parcel/subdivision/ticker/draft/render", lambda: test_cli(out, video, music, base)),
        ]
        for i, (label, fn) in enumerate(steps, 1):
            fn()
            print(f"[{i}/{len(steps)}] OK  {label}")
        print(f"✅ {len(steps)}/{len(steps)} nhóm kiểm thử đạt. Kết quả: {out}")


if __name__ == "__main__":
    main()

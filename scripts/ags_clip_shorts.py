#!/usr/bin/env python3
"""
AGS (Agent Space) Video Editing: Video dài → nhiều short 9:16, chia 2 bước cho agent
  transcript  Bóc băng Whisper theo từng từ → JSON (câu + từng từ, có mốc giây) để agent đọc và chọn đoạn hay.
  cut         Nhận danh sách đoạn (file JSON và/hoặc --range), mỗi đoạn xuất 1 short 1080x1920: reframe bám mặt nếu
              video ngang, phụ đề karaoke/editorial lấy từ chính transcript (không bóc băng lại), hook tuỳ chọn hiện đủ
              đậm ngay từ khung 0, chuẩn -14 LUFS. Mép đoạn được nắn về ranh giới từ để không cắt giữa chữ.
Đoạn phải dài 1–180 giây (YouTube Shorts tối đa 3 phút).
"""

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

from ags_common import LOUDNORM, group_word_lists, run_cmd, transcribe_words, video_info
from ags_editorial_sub import DEFAULT_HIGHLIGHT, STYLES, ass_color, parse_keywords, subtitles_filter, write_ass
from ags_reframe import OUT_H, OUT_W, reframe_filter

PRE_PAD, POST_PAD = 0.10, 0.20
MIN_SECONDS, MAX_SECONDS = 1.0, 180.0


def cmd_transcript(args):
    video = Path(args.input).resolve()
    out = Path(args.out or video.with_name(f"{video.stem}_transcript.json")).resolve()
    print(f"[*] Bóc băng {video.name} bằng Whisper ({args.model})...")
    words = transcribe_words(video, args.model)
    sentences = [{"id": i, "start": round(g[0][0], 2), "end": round(g[-1][1], 2), "text": " ".join(w[2] for w in g)}
                 for i, g in enumerate(group_word_lists(words, max_chars=200, max_seconds=15.0))]
    data = {
        "source": str(video),
        "duration": round(video_info(video)["duration"], 3),
        "model": args.model,
        "sentences": sentences,
        "words": [{"start": round(s, 3), "end": round(e, 3), "word": w} for s, e, w in words],
    }
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"transcript": str(out), "sentences": len(sentences), "words": len(words)}, ensure_ascii=False))


def parse_time(text):
    """'75.5' hoặc '1:15.5' -> giây."""
    seconds = 0.0
    for part in str(text).strip().split(":"):
        seconds = seconds * 60 + float(part)
    return seconds


def load_ranges(args):
    ranges = []
    if args.ranges:
        data = json.loads(Path(args.ranges).read_text(encoding="utf-8"))
        items = data["ranges"] if isinstance(data, dict) else data
        ranges += [{"start": parse_time(r["start"]), "end": parse_time(r["end"]), "hook": r.get("hook", ""),
                    "name": r.get("name", "")} for r in items]
    for text in args.range or []:
        start, _, end = text.partition("-")
        ranges.append({"start": parse_time(start), "end": parse_time(end), "hook": "", "name": ""})
    if not ranges:
        raise ValueError("Cần --ranges <file.json> hoặc ít nhất một --range START-END")
    return ranges


def snap_range(words, start, end, total):
    """Nắn [start, end] về ranh giới từ (không cắt giữa chữ), chừa đệm nhưng không lấn sang từ kề bên."""
    inside = [i for i, (s, e, _) in enumerate(words) if e > start and s < end]
    if not inside:
        return max(0.0, start), min(total, end)
    first, last = inside[0], inside[-1]
    low = words[first - 1][1] if first > 0 else 0.0
    high = words[last + 1][0] if last + 1 < len(words) else total
    return max(low, words[first][0] - PRE_PAD, 0.0), min(high, words[last][1] + POST_PAD, total)


def slug(text):
    return re.sub(r"[^\w-]+", "-", text.strip(), flags=re.UNICODE).strip("-")[:60]


def cmd_cut(args):
    video = Path(args.input).resolve()
    data = json.loads(Path(args.transcript).read_text(encoding="utf-8"))
    words = [(w["start"], w["end"], w["word"]) for w in data["words"]]
    info = video_info(video)
    ranges = load_ranges(args)
    out_dir = Path(args.out_dir or video.with_name(f"{video.stem}_shorts")).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    keywords = parse_keywords(args.keywords)
    results = []
    for number, item in enumerate(ranges, 1):
        start, end = snap_range(words, item["start"], item["end"], info["duration"])
        if not MIN_SECONDS <= end - start <= MAX_SECONDS:
            raise ValueError(f"Đoạn {number} dài {end - start:.1f}s — phải trong {MIN_SECONDS:.0f}–{MAX_SECONDS:.0f}s")
        name = slug(item["name"]) or f"{video.stem}_short_{number:02d}"
        output = out_dir / f"{name}.mp4"
        clip_words = [(s - start, e - start, w) for s, e, w in words if s >= start - 0.01 and e <= end + 0.01]
        print(f"[*] Short {number}/{len(ranges)}: {start:.2f}s → {end:.2f}s ({end - start:.1f}s)")
        with tempfile.TemporaryDirectory(prefix="ags_short_") as tmp:
            filters = [reframe_filter(video, start, end - start, tmp) if not args.no_reframe else
                       f"scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=decrease,"
                       f"pad={OUT_W}:{OUT_H}:(ow-iw)/2:(oh-ih)/2,setsar=1"]
            groups = [] if args.style == "none" else group_word_lists(
                clip_words, STYLES[args.style]["max_chars"], STYLES[args.style]["max_seconds"])
            if groups or item["hook"]:
                ass_path = Path(tmp) / "captions.ass"
                fonts_dir = write_ass(groups, ass_path, OUT_W, OUT_H,
                                      "karaoke" if args.style == "none" else args.style, args.highlight_color,
                                      keywords, (item["hook"], min(args.hook_seconds, end - start)))
                filters.append(subtitles_filter(ass_path, fonts_dir))
            audio = ["-af", LOUDNORM, "-ar", "48000", "-c:a", "aac", "-b:a", "192k"] if info["audio_channels"] else ["-an"]
            run_cmd(["ffmpeg", "-y", "-ss", f"{start:.3f}", "-i", video, "-t", f"{end - start:.3f}",
                     "-vf", ",".join(filters), "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                     "-pix_fmt", "yuv420p", *audio, "-movflags", "+faststart", output])
        results.append({"output": str(output), "start": round(start, 2), "end": round(end, 2),
                        "duration": round(end - start, 2), "hook": item["hook"]})
    print(json.dumps({"shorts": results}, ensure_ascii=False))


def main(argv=None):
    parser = argparse.ArgumentParser(description="AGS (Agent Space) — video dài thành nhiều short 9:16")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("transcript", help="Bóc băng theo từng từ ra JSON")
    p.add_argument("input", help="Video dài")
    p.add_argument("--out", "-o", default=None, help="File JSON (mặc định <tên>_transcript.json)")
    p.add_argument("--model", default="base",
                   help="Model faster-whisper: tiny, base, small, medium, large-v3, large-v3-turbo... (mặc định base)")
    p.set_defaults(func=cmd_transcript)

    p = sub.add_parser("cut", help="Xuất các đoạn đã chọn thành short 9:16")
    p.add_argument("input", help="Video dài (cùng file đã bóc băng)")
    p.add_argument("--transcript", required=True, help="File JSON từ bước transcript")
    p.add_argument("--ranges", help='File JSON: [{"start": 12.5, "end": 48.2, "hook": "...", "name": "..."}]')
    p.add_argument("--range", action="append", help="Đoạn START-END (giây hoặc phút:giây), lặp lại được")
    p.add_argument("--out-dir", default=None, help="Thư mục xuất (mặc định <tên>_shorts cạnh video)")
    p.add_argument("--style", choices=[*STYLES, "none"], default="karaoke", help="Kiểu phụ đề (mặc định karaoke)")
    p.add_argument("--highlight-color", default=DEFAULT_HIGHLIGHT, help="Màu #RRGGBB cho từ đang nói / từ khoá / hook")
    p.add_argument("--keywords", default="", help="Từ/cụm từ khoá cần tô màu, cách nhau bằng dấu phẩy")
    p.add_argument("--hook-seconds", type=float, default=3.0, help="Thời gian hiện hook ở đầu short (giây)")
    p.add_argument("--no-reframe", action="store_true", help="Không bám mặt: thu nhỏ vừa khung dọc, thêm viền")
    p.set_defaults(func=cmd_cut)

    args = parser.parse_args(argv)
    try:
        if getattr(args, "highlight_color", None):
            ass_color(args.highlight_color)
        args.func(args)
    except (FileNotFoundError, KeyError, ValueError, RuntimeError) as exc:
        sys.exit(f"❌ {exc}")


if __name__ == "__main__":
    main()

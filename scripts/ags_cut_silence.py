#!/usr/bin/env python3
"""
AGS (Agent Space) Video Editing: Cắt khoảng lặng & từ đệm
Bóc băng Whisper theo từng từ, bỏ khoảng lặng dài hơn --min-silence và các từ đệm ('ờ, à, ừm...'),
cắt chính xác từng khung hình (encode lại) rồi nối liền mạch, chuẩn hoá âm lượng -14 LUFS.
Giữ nguyên khung hình gốc.
"""

import argparse
import sys
import tempfile
from pathlib import Path

from ags_common import LOUDNORM, media_duration, normalize_word, run_cmd, transcribe_words

FILLERS = {"ờ", "à", "ừm", "ừ", "hả", "um", "uh", "er"}


def plan_keep_ranges(words, total, min_silence=0.4, pad=0.12):
    """Trả về [(start, end)] cần giữ.

    Một đoạn giữ = chuỗi từ liên tiếp không phải từ đệm, khoảng nghỉ giữa các từ <= min_silence.
    Mỗi đoạn được nới thêm `pad` giây hai đầu nhưng không lấn sang từ (hoặc từ đệm) kề bên.
    """
    runs = []
    for i, (start, end, word) in enumerate(words):
        if normalize_word(word) in FILLERS:
            continue
        if runs and runs[-1][1] == i - 1 and start - words[i - 1][1] <= min_silence:
            runs[-1][1] = i
        else:
            runs.append([i, i])
    keep = []
    for first, last in runs:
        low = words[first - 1][1] if first > 0 else 0.0
        high = words[last + 1][0] if last + 1 < len(words) else total
        keep.append((max(low, words[first][0] - pad), min(high, words[last][1] + pad)))
    return keep


def cut_silence(video_path, output_path, model_size="base", min_silence=0.4):
    video_path = Path(video_path).resolve()
    output_path = Path(output_path).resolve()

    print(f"[*] Đang nhận diện giọng nói bằng Faster-Whisper ({model_size})...")
    words = transcribe_words(video_path, model_size)
    total = media_duration(video_path)
    keep = [(s, e) for s, e in plan_keep_ranges(words, total, min_silence) if e - s >= 0.05]
    if not keep:
        sys.exit("❌ Không nhận diện được lời nói nào trong video — không có gì để giữ lại.")

    fillers = sum(1 for w in words if normalize_word(w[2]) in FILLERS)
    kept = sum(e - s for s, e in keep)
    print(f"[+] {len(words)} từ, bỏ {fillers} từ đệm; giữ {len(keep)} đoạn = {kept:.1f}s / {total:.1f}s.")

    with tempfile.TemporaryDirectory(prefix="ags_cut_") as tmp:
        lines = []
        for idx, (start, end) in enumerate(keep):
            seg_file = Path(tmp) / f"seg_{idx:04d}.mkv"
            run_cmd([
                "ffmpeg", "-y", "-ss", f"{start:.3f}", "-i", video_path, "-t", f"{end - start:.3f}",
                "-map", "0:v:0", "-map", "0:a:0",
                "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
                "-c:a", "pcm_s16le", "-ar", "48000", seg_file,
            ])
            lines.append(f"file '{seg_file.as_posix()}'")
        concat_txt = Path(tmp) / "concat.txt"
        concat_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")

        print("[*] Đang nối các đoạn đã cắt và chuẩn hoá -14 LUFS...")
        run_cmd([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt,
            "-c:v", "copy", "-af", LOUDNORM, "-ar", "48000", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", output_path,
        ])
    print(f"🎉 Hoàn thành video sạch: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGS (Agent Space) — cắt khoảng lặng & từ đệm tự động")
    parser.add_argument("input", help="Đường dẫn video đầu vào")
    parser.add_argument("--out", "-o", default=None, help="Đường dẫn video đầu ra (mặc định <tên>_clean.mp4)")
    parser.add_argument("--model", default="base", help="Model Whisper (tiny, base, small, medium)")
    parser.add_argument("--min-silence", type=float, default=0.4, help="Khoảng lặng dài hơn mức này (giây) sẽ bị cắt")
    args = parser.parse_args()

    inp = Path(args.input)
    out = args.out or inp.with_name(f"{inp.stem}_clean.mp4")
    cut_silence(inp, out, model_size=args.model, min_silence=args.min_silence)

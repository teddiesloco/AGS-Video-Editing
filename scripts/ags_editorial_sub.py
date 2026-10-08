#!/usr/bin/env python3
"""
AGS (Agent Space) Video Editing: Phụ đề tạp chí & chuẩn âm lượng phát sóng
Bóc băng Whisper theo từng từ, gom thành cụm phụ đề ngắn, đốt phụ đề nét Serif (Georgia) vào video
và chuẩn hoá âm lượng -14 LUFS (AAC 48 kHz).
"""

import argparse
import tempfile
from pathlib import Path

from ags_common import LOUDNORM, display_size, group_words, run_cmd, transcribe_words


def format_ass_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def generate_editorial_ass(chunks, ass_path, width, height, font_name="Georgia"):
    """File .ASS theo đúng kích thước video: chữ trắng viền đen, cỡ ~5% cạnh ngắn."""
    font_size = round(min(width, height) * 0.05)
    outline = max(2, font_size // 20)
    margin_x = round(width * 0.08)
    margin_v = round(height * 0.2) if height > width else round(height * 0.08)
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Editorial,{font_name},{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,1,0,1,{outline},0,2,{margin_x},{margin_x},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for start, end, text in chunks:
        text = text.replace("{", "(").replace("}", ")")
        events.append(f"Dialogue: 0,{format_ass_time(start)},{format_ass_time(end)},Editorial,,0,0,0,,{text}")
    Path(ass_path).write_text(header + "\n".join(events) + "\n", encoding="utf-8")


def render_editorial_video(video_path, output_path, model_size="base"):
    video_path = Path(video_path).resolve()
    output_path = Path(output_path).resolve()

    print(f"[*] Đang nhận diện lời thoại bằng Whisper ({model_size})...")
    chunks = group_words(transcribe_words(video_path, model_size), max_chars=42, max_seconds=4.0)
    width, height = display_size(video_path)

    with tempfile.TemporaryDirectory(prefix="ags_sub_") as tmp:
        ass_path = Path(tmp) / "subtitles.ass"
        generate_editorial_ass(chunks, ass_path, width, height)

        print("[*] Đang xuất video với chuẩn âm thanh -14 LUFS...")
        # Escape đường dẫn cho bộ lọc subtitles của FFmpeg (dấu ':' của ổ đĩa Windows)
        escaped_ass = ass_path.as_posix().replace(":", "\\:")
        run_cmd([
            "ffmpeg", "-y", "-i", video_path,
            "-vf", f"subtitles='{escaped_ass}'",
            "-af", LOUDNORM, "-ar", "48000",
            "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
            output_path,
        ])
    print(f"🎉 Hoàn thành video phụ đề tạp chí ({len(chunks)} câu): {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGS (Agent Space) — phụ đề tạp chí & cân âm -14 LUFS")
    parser.add_argument("input", help="Đường dẫn video")
    parser.add_argument("--out", "-o", default=None, help="Đường dẫn video đầu ra (mặc định <tên>_editorial.mp4)")
    parser.add_argument("--model", default="base", help="Model Whisper (tiny, base, small, medium)")
    args = parser.parse_args()

    inp = Path(args.input)
    out = args.out or inp.with_name(f"{inp.stem}_editorial.mp4")
    render_editorial_video(inp, out, model_size=args.model)

#!/usr/bin/env python3
"""
AGS (Agent Space) Video Editing: Phụ đề & chuẩn âm lượng phát sóng
Bóc băng Whisper theo từng từ, đốt phụ đề .ASS vào video và chuẩn hoá -14 LUFS (AAC 48 kHz).
  --style editorial  câu ngắn nét Serif trắng viền đen, phong cách tạp chí (mặc định)
  --style karaoke    chữ đậm, từ đang nói đổi sang --highlight-color đúng theo mốc thời gian của từng từ
--keywords tô --highlight-color cho các từ/cụm từ khoá ở cả hai kiểu. Chữ chuẩn hoá Unicode NFC và nằm trong
vùng an toàn (ags_common.safe_box: video dọc tránh giao diện TikTok/Reels/Shorts).
"""

import argparse
import re
import tempfile
from pathlib import Path

from ags_common import (LOUDNORM, display_size, filter_path, font_family, font_path, group_word_lists, nfc,
                        normalize_word, run_cmd, safe_box, transcribe_words)

# font (khoá FONT_FILES), cỡ chữ (tỉ lệ cạnh ngắn), giới hạn cụm (ký tự, giây), đậm, giãn chữ
STYLES = {
    "editorial": {"font": "serif", "size": 0.05, "max_chars": 42, "max_seconds": 4.0, "bold": 0, "spacing": 1},
    "karaoke": {"font": "bold", "size": 0.065, "max_chars": 24, "max_seconds": 2.5, "bold": -1, "spacing": 0},
}
HOOK_SIZE = 0.075  # cỡ chữ hook (tỉ lệ cạnh ngắn)
DEFAULT_HIGHLIGHT = "#FFD60A"


def format_ass_time(seconds):
    cs = int(round(max(0.0, seconds) * 100))
    return f"{cs // 360000:d}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def ass_color(hex_color):
    """'#RRGGBB' -> '&H00BBGGRR' (thứ tự màu của ASS)."""
    value = hex_color.lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", value):
        raise ValueError(f"Màu phải dạng #RRGGBB: {hex_color}")
    return f"&H00{value[4:6]}{value[2:4]}{value[0:2]}".upper()


def ass_text(text):
    return nfc(text).replace("\\", "/").replace("{", "(").replace("}", ")")


def parse_keywords(text):
    """'từ khoá, cụm từ khác' -> [['từ', 'khoá'], ['cụm', 'từ', 'khác']] (đã chuẩn hoá để so khớp)."""
    phrases = [[normalize_word(w) for w in part.split()] for part in (text or "").split(",")]
    return [[w for w in p if w] for p in phrases if any(p)]


def keyword_marks(words, keywords):
    """Chỉ số các từ thuộc một cụm từ khoá."""
    norm = [normalize_word(w[2]) for w in words]
    marks = set()
    for phrase in keywords:
        for i in range(len(norm) - len(phrase) + 1):
            if norm[i:i + len(phrase)] == phrase:
                marks.update(range(i, i + len(phrase)))
    return marks


def line_text(words, highlighted, color):
    return " ".join(f"{{\\1c{color}&}}{ass_text(w[2])}{{\\r}}" if i in highlighted else ass_text(w[2])
                    for i, w in enumerate(words))


def write_ass(groups, ass_path, width, height, style="editorial", highlight=DEFAULT_HIGHLIGHT, keywords=(),
              hook=None):
    """Ghi phụ đề .ASS đúng kích thước video; trả về thư mục font cho bộ lọc subtitles.

    groups: các cụm từ [(start, end, word)] (giây, tính từ đầu video); hook: (chữ, giây) hiện ở đỉnh vùng an toàn
    ngay từ khung 0, không hiệu ứng mờ dần."""
    cfg = STYLES[style]
    color = ass_color(highlight)
    x0, y0, x1, y1 = safe_box(width, height)
    size = round(min(width, height) * cfg["size"])
    outline = max(2, size // (12 if style == "karaoke" else 20))
    hook_size = round(min(width, height) * HOOK_SIZE)
    margins = f"{x0},{width - x1}"
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{font_family(cfg["font"])},{size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,{cfg["bold"]},0,0,0,100,100,{cfg["spacing"]},0,1,{outline},0,2,{margins},{height - y1},1
Style: Hook,{font_family("bold")},{hook_size},{color},&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{max(3, hook_size // 12)},0,8,{margins},{y0},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def event(start, end, text, name="Caption"):
        return f"Dialogue: 0,{format_ass_time(start)},{format_ass_time(end)},{name},,0,0,0,,{text}"

    keywords = list(keywords)
    events = []
    if hook and hook[0]:
        events.append(event(0.0, hook[1], ass_text(hook[0]), "Hook"))
    for words in groups:
        marks = keyword_marks(words, keywords)
        if style == "karaoke":
            for i, word in enumerate(words):
                end = words[i + 1][0] if i + 1 < len(words) else words[-1][1]
                if end > word[0]:
                    events.append(event(word[0], end, line_text(words, marks | {i}, color)))
        else:
            events.append(event(words[0][0], words[-1][1], line_text(words, marks, color)))
    Path(ass_path).write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    return Path(font_path(cfg["font"])).parent


def subtitles_filter(ass_path, fonts_dir):
    return f"subtitles='{filter_path(ass_path)}':fontsdir='{filter_path(fonts_dir)}'"


def render_subtitled_video(video_path, output_path, model_size="base", style="editorial",
                           highlight=DEFAULT_HIGHLIGHT, keywords=""):
    video_path = Path(video_path).resolve()
    output_path = Path(output_path).resolve()
    cfg = STYLES[style]

    print(f"[*] Đang nhận diện lời thoại bằng Whisper ({model_size})...")
    groups = group_word_lists(transcribe_words(video_path, model_size), cfg["max_chars"], cfg["max_seconds"])
    width, height = display_size(video_path)

    with tempfile.TemporaryDirectory(prefix="ags_sub_") as tmp:
        ass_path = Path(tmp) / "subtitles.ass"
        fonts_dir = write_ass(groups, ass_path, width, height, style, highlight, parse_keywords(keywords))

        print("[*] Đang đốt phụ đề và chuẩn hoá âm thanh -14 LUFS...")
        run_cmd([
            "ffmpeg", "-y", "-i", video_path,
            "-vf", subtitles_filter(ass_path, fonts_dir),
            "-af", LOUDNORM, "-ar", "48000",
            "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
            output_path,
        ])
    print(f"🎉 Hoàn thành video phụ đề {style} ({len(groups)} câu): {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGS (Agent Space) — phụ đề tạp chí / karaoke & cân âm -14 LUFS")
    parser.add_argument("input", help="Đường dẫn video")
    parser.add_argument("--out", "-o", default=None, help="Đường dẫn video đầu ra (mặc định <tên>_<style>.mp4)")
    parser.add_argument("--model", default="base",
                        help="Model faster-whisper: tiny, base, small, medium, large-v3, large-v3-turbo... (mặc định base)")
    parser.add_argument("--style", choices=list(STYLES), default="editorial", help="Kiểu phụ đề (mặc định editorial)")
    parser.add_argument("--highlight-color", default=DEFAULT_HIGHLIGHT,
                        help="Màu #RRGGBB cho từ đang nói (karaoke) và từ khoá (mặc định #FFD60A)")
    parser.add_argument("--keywords", default="", help="Từ/cụm từ khoá cần tô màu, cách nhau bằng dấu phẩy")
    args = parser.parse_args()

    ass_color(args.highlight_color)
    inp = Path(args.input)
    out = args.out or inp.with_name(f"{inp.stem}_{args.style}.mp4")
    render_subtitled_video(inp, out, args.model, args.style, args.highlight_color, args.keywords)

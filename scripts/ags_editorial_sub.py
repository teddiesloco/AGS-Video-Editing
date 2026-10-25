#!/usr/bin/env python3
"""
AGS (Agent Space) Video Editing: Phụ đề & chuẩn âm lượng phát sóng
Bóc băng Whisper theo từng từ (hoặc dùng đúng lời đọc --script, chỉ lấy mốc thời gian từ Whisper), đốt phụ đề .ASS vào
video và chuẩn hoá -14 LUFS (AAC 48 kHz).
  --style clean      chữ Sans đậm trắng, viền mảnh + bóng mềm, từ khoá màu vàng cát; tối đa 2 dòng (mặc định)
  --style editorial  câu ngắn nét Serif trắng viền đen, phong cách tạp chí
  --style karaoke    chữ đậm, từ đang nói đổi sang --highlight-color đúng theo mốc thời gian của từng từ
--keywords tô --highlight-color (mặc định theo kiểu) cho các từ/cụm từ khoá ở mọi kiểu. Chữ chuẩn hoá Unicode NFC, xuống tối đa 2 dòng
(hook 3 dòng) đúng cỡ chữ của kiểu; chỉ khi cần mới hạ cỡ chữ tối thiểu 75%, và chỉ từ nào dài hơn cả dòng mới bị
thu hẹp riêng. Mọi dòng nằm trong vùng an toàn (ags_common.safe_box: video dọc tránh giao diện TikTok/Reels/Shorts).
"""

import argparse
import math
import re
import tempfile
from pathlib import Path

from ags_common import (LOUDNORM, align_script_words, display_size, filter_path, font_family, font_path,
                        group_word_lists, nfc, load_font, normalize_word, run_cmd, safe_box, transcribe_words)

# font (khoá FONT_FILES), cỡ chữ (tỉ lệ cạnh ngắn), giới hạn cụm (ký tự, giây), đậm, giãn chữ,
# viền (size // outline_div), bóng (size // shadow_div, 0 = không bóng), blur (px, làm mềm viền/bóng), màu từ khoá mặc định
STYLES = {
    "clean": {"font": "bold", "size": 0.058, "max_chars": 28, "max_seconds": 3.0, "bold": -1, "spacing": 0,
              "outline_div": 22, "shadow_div": 16, "blur": 1.0, "highlight": "#E3C285"},
    "editorial": {"font": "serif", "size": 0.056, "max_chars": 34, "max_seconds": 4.0, "bold": 0, "spacing": 1,
                  "outline_div": 20, "shadow_div": 0, "blur": 0, "highlight": "#FFD60A"},
    "karaoke": {"font": "bold", "size": 0.065, "max_chars": 24, "max_seconds": 2.5, "bold": -1, "spacing": 0,
                "outline_div": 12, "shadow_div": 0, "blur": 0, "highlight": "#FFD60A"},
    # Kênh "N năm kinh nghiệm trong 60 giây": cụm 2–4 từ, chữ trắng viền đen dày, cỡ 6,7% cạnh ngắn (72 px ở 1080),
    # chỉ hạ tới 5,8% (63 px) khi cụm không vừa 2 dòng.
    "bt_vi": {"font": "display", "size": 0.067, "min_size": 0.058, "max_chars": 30, "max_seconds": 2.0, "max_words": 4,
              "bold": -1, "spacing": 0, "outline_div": 12, "shadow_div": 0, "blur": 0, "highlight": "#FFD166"},
}
BT_VI_SIZE_RANGE = (0.058, 0.072)  # FR-012: cỡ chữ bt_vi 5,8–7,2% cạnh ngắn (mặc định 6,7%)
DEFAULT_STYLE = "clean"
HOOK_SIZE = 0.078      # cỡ chữ hook (tỉ lệ cạnh ngắn): 84 px ở 1080
HOOK_MIN_SIZE = 0.0667  # hook chỉ hạ tới 72 px khi không vừa 3 dòng
FIT_MARGIN = 1.1       # dự phòng chênh số đo Pillow so với libass (viền chữ, kerning)
MIN_FONT_SCALE = 0.75  # hạ cỡ chữ tối đa 25% khi chữ không vừa số dòng cho phép
MAX_LINES = {"Caption": 2, "Hook": 3}
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


def text_width(font, text, spacing):
    return font.getlength(text) + max(0, len(text) - 1) * spacing


def wrap_tokens(texts, font, spacing, limit):
    """Chia các từ thành dòng (list chỉ số từ): xếp dần đến khi quá `limit` px; kết quả 2 dòng thì chia lại cho cân."""
    lines, current = [], []
    for i, text in enumerate(texts):
        if current and text_width(font, " ".join(texts[k] for k in current + [i]), spacing) > limit:
            lines.append(current)
            current = []
        current.append(i)
    lines.append(current)
    if len(lines) == 2:
        flat = lines[0] + lines[1]
        cut = min(range(1, len(flat)), key=lambda k: max(
            text_width(font, " ".join(texts[j] for j in flat[:k]), spacing),
            text_width(font, " ".join(texts[j] for j in flat[k:]), spacing)))
        lines = [flat[:cut], flat[cut:]]
    return lines


def fit_layout(texts, font_key, base_size, spacing, limit, max_lines, floor=None, font_file=None):
    """(cỡ chữ, font, dòng): giữ `base_size`, chỉ hạ dần (tới `floor`, mặc định MIN_FONT_SCALE) khi vượt `max_lines` dòng."""
    floor = max(1, floor or round(base_size * MIN_FONT_SCALE))
    size = base_size
    while True:
        if font_file:
            from PIL import ImageFont
            font = ImageFont.truetype(str(font_file), size)
        else:
            font = load_font(font_key, size)
        lines = wrap_tokens(texts, font, spacing, limit)
        if len(lines) <= max_lines or size <= floor:
            return size, font, lines
        size = max(floor, size - max(1, base_size // 20))


def split_word_groups(groups, max_words):
    """Chia mỗi cụm thành các cụm liền nhau tối đa `max_words` từ, chia đều (5 từ -> 3 + 2) để không sót cụm 1 từ."""
    result = []
    for words in groups:
        parts = math.ceil(len(words) / max_words)
        bounds = [round(k * len(words) / parts) for k in range(parts + 1)]
        result.extend(words[a:b] for a, b in zip(bounds, bounds[1:]))
    return result


def caption_markup(texts, lines, scales, highlighted=(), color="", colors=None, reset="&HFFFFFF"):
    """Văn bản ASS: ngắt dòng bằng \\N; từ tô màu giữ nguyên; từ dài hơn cả dòng (scale < 100) thu hẹp riêng.
    colors: {chỉ số từ: màu ASS} riêng từng từ (thắng `color`)."""
    def token(i):
        text = texts[i]
        if i in highlighted:
            text = f"{{\\1c{(colors or {}).get(i, color)}&}}{text}{{\\1c{reset}&}}"
        if scales[i] < 100:
            text = f"{{\\fscx{scales[i]:.3f}\\fscy{scales[i]:.3f}}}{text}{{\\fscx100\\fscy100}}"
        return text
    return "\\N".join(" ".join(token(i) for i in line) for line in lines)


def write_ass(groups, ass_path, width, height, style=DEFAULT_STYLE, highlight=None, keywords=(), hook=None,
              keyword_colors=None, text_color=None, size_ratio=None, label=None, label_terms=None, font_file=None):
    """Ghi phụ đề .ASS đúng kích thước video; trả về thư mục font cho bộ lọc subtitles.

    groups: các cụm từ [(start, end, word)] (giây, tính từ đầu video); hook: (chữ, giây) hiện ở đỉnh vùng an toàn
    ngay từ khung 0, không hiệu ứng mờ dần. keyword_colors: {chỉ số từ trên toàn bộ lời: '#RRGGBB'} tô màu riêng từng
    từ khoá; text_color: màu chữ phụ đề (mặc định trắng); size_ratio: cỡ chữ (tỉ lệ cạnh ngắn) thay cho cỡ của kiểu;
    label: nhãn (vd "ví dụ", ≥ 40 px). label_terms: các cụm (vd "35k") — nhãn đứng đầu dòng của mỗi cụm phụ đề có cụm
    đó; không có label_terms thì nhãn cố định ở góc trái ngay trên vùng phụ đề suốt thời gian có lời."""
    cfg = STYLES[style]
    if cfg.get("max_words"):
        groups = split_word_groups(groups, cfg["max_words"])
    color = ass_color(highlight or cfg["highlight"])
    base_color = ass_color(text_color) if text_color else "&H00FFFFFF"
    reset = base_color if text_color else "&HFFFFFF"
    word_colors = {int(i): ass_color(c) for i, c in (keyword_colors or {}).items()}
    if font_file:
        from PIL import ImageFont
        persona_family = ImageFont.truetype(str(font_file), 12).getname()[0]
    else:
        persona_family = font_family(cfg["font"])
    x0, y0, x1, y1 = safe_box(width, height)
    size = round(min(width, height) * (size_ratio or cfg["size"]))
    outline = max(2, size // cfg["outline_div"])
    shadow = size // cfg["shadow_div"] if cfg["shadow_div"] else 0
    blur = cfg["blur"]
    hook_size = round(min(width, height) * HOOK_SIZE)
    padding = max(outline + shadow + math.ceil(blur), max(3, hook_size // 12)) + 4
    margins = f"{x0 + padding},{width - x1 + padding}"
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{persona_family},{size},{base_color},&H000000FF,&H00000000,&H80000000,{cfg["bold"]},0,0,0,100,100,{cfg["spacing"]},0,1,{outline},{shadow},2,{margins},{height - y1 + padding},1
Style: Hook,{persona_family if font_file else font_family("bold")},{hook_size},{color},&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{max(3, hook_size // 12)},0,8,{margins},{y0 + padding},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    limit = (x1 - x0 - 2 * padding) / FIT_MARGIN

    caption_floor = round(min(width, height) * cfg["min_size"]) if cfg.get("min_size") and not size_ratio else None
    label_size = max(40, round(min(width, height) * 0.037))

    def place(texts, name):
        """(cỡ chữ, dòng, scale từng từ) cho một cụm; tính một lần để mọi sự kiện karaoke của cụm xuống dòng giống nhau.
        Hook hạ tới HOOK_MIN_SIZE trước, chỉ khi vẫn quá 3 dòng mới hạ tiếp như phụ đề."""
        key, base, spacing = ("bold", hook_size, 0) if name == "Hook" else (cfg["font"], size, cfg["spacing"])
        floor = round(min(width, height) * HOOK_MIN_SIZE) if name == "Hook" else caption_floor
        fs, font, lines = fit_layout(texts, key, base, spacing, limit, MAX_LINES[name], floor, font_file)
        if len(lines) > MAX_LINES[name] and floor:
            fs, font, lines = fit_layout(texts, key, base, spacing, limit, MAX_LINES[name], font_file=font_file)
        return fs, lines, [min(100.0, 100 * limit / max(1.0, text_width(font, t, spacing))) for t in texts]

    def dialogue(start, end, name, fs, body):
        soften = f"\\blur{blur}" if blur and name == "Caption" else ""
        return (f"Dialogue: 0,{format_ass_time(start)},{format_ass_time(end)},{name},,0,0,0,,"
                f"{{\\q2\\fs{fs}{soften}}}{body}")

    # Cụm từ khoá khớp trên toàn bộ lời, không chỉ trong từng cụm chữ: cụm bị ngắt giữa hai caption vẫn được tô cả hai nửa.
    keyword_hits = keyword_marks([w for words in groups for w in words], list(keywords))
    events = []
    if hook and hook[0]:
        texts = ass_text(hook[0]).split()
        fs, lines, scales = place(texts, "Hook")
        events.append(dialogue(0.0, hook[1], "Hook", fs, caption_markup(texts, lines, scales)))
    label_words = [[normalize_word(w) for w in t.split() if normalize_word(w)] for t in (label_terms or [])]
    label_token = f"({ass_text(label)})" if label else ""
    offset = 0
    for words in groups:
        marks = {i - offset for i in keyword_hits if offset <= i < offset + len(words)}
        colors = {i - offset: c for i, c in word_colors.items() if offset <= i < offset + len(words)}
        marks |= set(colors)
        offset += len(words)
        texts = [ass_text(w[2]) for w in words]
        norm = [normalize_word(w[2]) for w in words]
        tagged = label_token and any(t and any(norm[k:k + len(t)] == t for k in range(len(norm) - len(t) + 1))
                                     for t in label_words)
        if tagged:  # nhãn là "từ" số 0 của cụm để xuống dòng/đo bề ngang chung với chữ
            texts = [label_token] + texts
            marks, colors = {i + 1 for i in marks}, {i + 1: c for i, c in colors.items()}
        fs, lines, scales = place(texts, "Caption")

        def body(marked):
            markup = caption_markup(texts, lines, scales, marked, color, colors, reset)
            if tagged:
                markup = markup.replace(label_token, f"{{\\fs{label_size}\\1c{ass_color('#FFD166')}&}}{label_token}"
                                                     f"{{\\fs{fs}\\1c{reset}&}}", 1)
            return markup

        if style == "karaoke":
            for i, word in enumerate(words):
                end = words[i + 1][0] if i + 1 < len(words) else words[-1][1]
                if end > word[0]:
                    events.append(dialogue(word[0], end, "Caption", fs, body(marks | {i + int(bool(tagged))})))
        else:
            events.append(dialogue(words[0][0], words[-1][1], "Caption", fs, body(marks)))
    if label and groups and not label_terms:
        events.append(f"Dialogue: 1,{format_ass_time(0.0)},{format_ass_time(groups[-1][-1][1])},Caption,,0,0,0,,"
                      f"{{\\an1\\pos({x0 + padding},{round(y1 - padding - 2.6 * size)})\\fs{label_size}}}"
                      f"{ass_text(label)}")
    Path(ass_path).write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    return Path(font_file or font_path(cfg["font"])).parent


def subtitles_filter(ass_path, fonts_dir):
    return f"subtitles='{filter_path(ass_path)}':fontsdir='{filter_path(fonts_dir)}'"


def render_subtitled_video(video_path, output_path, model_size="base", style=DEFAULT_STYLE,
                           highlight=None, keywords="", script_path=None):
    video_path = Path(video_path).resolve()
    output_path = Path(output_path).resolve()
    cfg = STYLES[style]

    print(f"[*] Đang nhận diện lời thoại bằng Whisper ({model_size})...")
    heard = transcribe_words(video_path, model_size)
    if script_path:
        # Chữ hiển thị là ĐÚNG script (không sửa, không lọc từ); Whisper chỉ cho mốc thời gian.
        words = align_script_words(Path(script_path).read_text(encoding="utf-8-sig"), heard)
        groups = group_word_lists(words, cfg["max_chars"], cfg["max_seconds"], clean=False)
        print(f"[*] Dùng đúng lời trong script ({len(words)} từ); Whisper nghe được {len(heard)} từ để lấy mốc thời gian.")
    else:
        groups = group_word_lists(heard, cfg["max_chars"], cfg["max_seconds"])
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
    parser = argparse.ArgumentParser(description="AGS (Agent Space) — phụ đề clean / editorial / karaoke & cân âm -14 LUFS")
    parser.add_argument("input", help="Đường dẫn video")
    parser.add_argument("--out", "-o", default=None, help="Đường dẫn video đầu ra (mặc định <tên>_<style>.mp4)")
    parser.add_argument("--model", default="base",
                        help="Model faster-whisper: tiny, base, small, medium, large-v3, large-v3-turbo... (mặc định base)")
    parser.add_argument("--style", choices=list(STYLES), default=DEFAULT_STYLE,
                        help=f"Kiểu phụ đề (mặc định {DEFAULT_STYLE})")
    parser.add_argument("--highlight-color", default=None,
                        help="Màu #RRGGBB cho từ đang nói (karaoke), từ khoá và hook "
                             "(mặc định theo kiểu: clean vàng cát #E3C285, editorial/karaoke #FFD60A)")
    parser.add_argument("--keywords", default="", help="Từ/cụm từ khoá cần tô màu, cách nhau bằng dấu phẩy")
    parser.add_argument("--script", type=Path, default=None,
                        help="File UTF-8 chứa đúng lời đọc: hiện chữ theo script (không theo Whisper nghe sai), "
                             "Whisper chỉ dùng để lấy mốc thời gian")
    args = parser.parse_args()

    if args.highlight_color:
        ass_color(args.highlight_color)
    inp = Path(args.input)
    out = args.out or inp.with_name(f"{inp.stem}_{args.style}.mp4")
    if args.script and not args.script.is_file():
        parser.error(f"Không thấy file script: {args.script}")
    render_subtitled_video(inp, out, args.model, args.style, args.highlight_color, args.keywords, args.script)

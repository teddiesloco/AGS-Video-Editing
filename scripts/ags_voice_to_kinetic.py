#!/usr/bin/env python3
"""
AGS (Agent Space) Video Editing: Giọng nói -> hoạt hình chữ 2D (Kinetic Typography)
Bóc băng Whisper theo từng từ, chia cụm ngắn (<= 3 giây), mỗi cụm hiện trên card trắng với hiệu ứng
bật nảy (pop-in) và giữ đúng mốc thời gian của audio. Xuất MP4 1080x1920, âm lượng -14 LUFS.
"""

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from ags_common import encode_frames, fit_text, group_words, media_duration, timeline_frames, transcribe_words

WIDTH, HEIGHT, FPS = 1080, 1920, 30
BG_COLOR = "#FBF8F1"
TEXT_COLOR = "#222222"
CARD_MARGIN_X = 100
POP_FRAMES = 8  # ~0.27s bật nảy ở đầu mỗi cụm chữ


def create_kinetic_card(text, width=WIDTH):
    """Card trắng bo góc chứa text (RGBA, đúng kích thước card)."""
    card_w = width - 2 * CARD_MARGIN_X
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    font, lines = fit_text(probe, text, "bold", max_width=card_w - 120, max_lines=4, size=76, min_size=48)
    line_h = int(font.size * 1.3)
    card_h = max(360, len(lines) * line_h + 160)
    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle([0, 0, card_w - 1, card_h - 1], radius=40, fill="#FFFFFF", outline="#E5E0D8", width=4)
    y = (card_h - len(lines) * line_h) // 2
    for line in lines:
        x = (card_w - draw.textlength(line, font=font)) / 2
        draw.text((x, y), line, font=font, fill=TEXT_COLOR)
        y += line_h
    return card


def pop_scale(progress):
    """easeOutBack: 0.6 -> vượt nhẹ ~1.04 -> 1.0."""
    c1 = 1.70158
    t = progress - 1
    return 0.6 + 0.4 * (1 + (c1 + 1) * t ** 3 + c1 * t ** 2)


def compose(background, card, scale):
    frame = background.copy()
    if scale != 1.0:
        card = card.resize((max(1, int(card.width * scale)), max(1, int(card.height * scale))), Image.LANCZOS)
    frame.paste(card, ((WIDTH - card.width) // 2, (HEIGHT - card.height) // 2), card)
    return frame.tobytes()


def render_kinetic_video(audio_path, output_path, model_size="base"):
    audio_path = Path(audio_path).resolve()
    output_path = Path(output_path).resolve()

    print("[*] Bóc băng audio bằng Whisper...")
    chunks = group_words(transcribe_words(audio_path, model_size), max_chars=32, max_seconds=3.0)
    if not chunks:
        sys.exit("❌ Không nhận diện được lời thoại trong file audio.")
    total = media_duration(audio_path)

    background = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    blank = background.tobytes()
    cache = {}

    def render(index, k):
        if index < 0:
            return blank
        if cache.get("index") != index:
            cache.clear()
            cache.update(index=index, card=create_kinetic_card(chunks[index][2]))
        if k < POP_FRAMES:
            return compose(background, cache["card"], pop_scale(k / POP_FRAMES))
        if "still" not in cache:
            cache["still"] = compose(background, cache["card"], 1.0)
        return cache["still"]

    print(f"[*] Dựng {len(chunks)} cụm chữ, ghép audio và chuẩn hoá -14 LUFS...")
    encode_frames(timeline_frames(chunks, total, FPS, render), (WIDTH, HEIGHT), FPS, audio_path, output_path)
    print(f"🎉 Hoàn thành video hoạt hình chữ: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGS (Agent Space) — giọng nói thành video chữ 2D")
    parser.add_argument("input", help="Đường dẫn file ghi âm (mp3/wav/m4a)")
    parser.add_argument("--out", "-o", default=None, help="Đường dẫn video đầu ra (mặc định <tên>_kinetic.mp4)")
    parser.add_argument("--model", default="base", help="Model Whisper (tiny, base, small, medium)")
    args = parser.parse_args()

    inp = Path(args.input)
    out = args.out or inp.with_name(f"{inp.stem}_kinetic.mp4")
    render_kinetic_video(inp, out, model_size=args.model)

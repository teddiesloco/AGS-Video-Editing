#!/usr/bin/env python3
"""
AGS (Agent Space) Video Editing: Giọng nói -> người que nét chì trên giấy kraft
Bóc băng Whisper theo từng từ, chia cụm ngắn; mỗi cụm là một khung giấy kraft có người que
(xen kẽ 2 thế: ngồi thiền / đứng suy tư) và phụ đề, giữ đúng mốc thời gian audio. Âm lượng -14 LUFS.
"""

import argparse
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from ags_common import (encode_frames, fit_text, group_words, media_duration, safe_box, timeline_frames,
                        transcribe_words)

WIDTH, HEIGHT, FPS = 1080, 1920, 30
INK = "#2A241C"


def draw_kraft_doodle_frame(text, pose_idx=0, width=WIDTH, height=HEIGHT):
    # Nền giấy kraft màu nâu ấm
    img = Image.new("RGB", (width, height), "#E6D7B8")
    draw = ImageDraw.Draw(img)

    # 1. Mặt trời nét chì
    sun_x, sun_y = width - 250, 350
    draw.ellipse([sun_x - 60, sun_y - 60, sun_x + 60, sun_y + 60], outline="#3A3226", width=4)
    for i in range(8):
        angle = i * (math.pi / 4)
        x1 = sun_x + int(80 * math.cos(angle))
        y1 = sun_y + int(80 * math.sin(angle))
        x2 = sun_x + int(110 * math.cos(angle))
        y2 = sun_y + int(110 * math.sin(angle))
        draw.line([x1, y1, x2, y2], fill="#3A3226", width=3)

    # 2. Tảng đá / mặt đất
    rock_y = height // 2 + 300
    draw.ellipse([width // 2 - 400, rock_y, width // 2 + 400, rock_y + 300], outline="#3A3226", fill="#D4C19C", width=5)

    # 3. Người que nét chì
    head_x = width // 2
    head_y = rock_y - 280
    head_r = 70
    draw.ellipse([head_x - head_r, head_y - head_r, head_x + head_r, head_y + head_r], outline=INK, width=6)
    draw.ellipse([head_x - 25, head_y - 15, head_x - 15, head_y - 5], fill=INK)
    draw.ellipse([head_x + 15, head_y - 15, head_x + 25, head_y - 5], fill=INK)
    draw.arc([head_x - 25, head_y, head_x + 25, head_y + 35], start=0, end=180, fill=INK, width=4)
    for angle in [-0.5, 0, 0.5]:
        draw.line([head_x + int(head_r * math.sin(angle)), head_y - head_r,
                   head_x + int(100 * math.sin(angle)), head_y - head_r - 30], fill=INK, width=3)

    neck_y = head_y + head_r
    crotch_y = neck_y + 200
    draw.line([head_x, neck_y, head_x, crotch_y], fill=INK, width=6)

    if pose_idx % 2 == 0:
        # Ngồi thiền
        draw.line([head_x, neck_y + 60, head_x - 90, neck_y + 140], fill=INK, width=5)
        draw.line([head_x - 90, neck_y + 140, head_x - 10, crotch_y], fill=INK, width=5)
        draw.line([head_x, neck_y + 60, head_x + 90, neck_y + 140], fill=INK, width=5)
        draw.line([head_x + 90, neck_y + 140, head_x + 10, crotch_y], fill=INK, width=5)
        draw.line([head_x, crotch_y, head_x - 160, crotch_y + 60], fill=INK, width=5)
        draw.line([head_x - 160, crotch_y + 60, head_x, crotch_y + 80], fill=INK, width=5)
        draw.line([head_x, crotch_y, head_x + 160, crotch_y + 60], fill=INK, width=5)
        draw.line([head_x + 160, crotch_y + 60, head_x, crotch_y + 80], fill=INK, width=5)
    else:
        # Đứng suy tư
        draw.line([head_x, neck_y + 50, head_x - 80, neck_y + 120], fill=INK, width=5)
        draw.line([head_x - 80, neck_y + 120, head_x - 20, head_y + 40], fill=INK, width=5)
        draw.line([head_x, neck_y + 50, head_x + 80, neck_y + 140], fill=INK, width=5)
        draw.line([head_x, crotch_y, head_x - 80, crotch_y + 180], fill=INK, width=5)
        draw.line([head_x, crotch_y, head_x + 80, crotch_y + 180], fill=INK, width=5)

    # 4. Phụ đề: tối đa 3 dòng, quanh y=680 (giữa mặt trời và đầu nhân vật), luôn trong vùng an toàn
    if text:
        x0, y0, x1, y1 = safe_box(width, height)
        font, lines = fit_text(draw, text, "serif", max_width=x1 - x0, max_lines=3, size=60, min_size=40)
        line_h = int(font.size * 1.3)
        y = min(max(680 - len(lines) * line_h // 2, y0), y1 - len(lines) * line_h)
        for line in lines:
            draw.text((x0 + (x1 - x0 - draw.textlength(line, font=font)) / 2, y), line, font=font, fill=INK)
            y += line_h
    return img


def render_doodle_video(audio_path, output_path, model_size="base"):
    audio_path = Path(audio_path).resolve()
    output_path = Path(output_path).resolve()

    print("[*] Bóc băng audio bằng Whisper...")
    chunks = group_words(transcribe_words(audio_path, model_size), max_chars=40, max_seconds=3.5)
    if not chunks:
        sys.exit("❌ Không nhận diện được lời thoại trong file audio.")
    total = media_duration(audio_path)

    intro = draw_kraft_doodle_frame("", pose_idx=0).tobytes()
    cache = {}

    def render(index, _k):
        if index < 0:
            return intro
        if cache.get("index") != index:
            cache.clear()
            cache.update(index=index, frame=draw_kraft_doodle_frame(chunks[index][2], pose_idx=index).tobytes())
        return cache["frame"]

    print(f"[*] Dựng {len(chunks)} khung người que, ghép audio và chuẩn hoá -14 LUFS...")
    encode_frames(timeline_frames(chunks, total, FPS, render), (WIDTH, HEIGHT), FPS, audio_path, output_path)
    print(f"🎉 Hoàn thành video người que nét chì: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGS (Agent Space) — giọng nói thành video người que giấy kraft")
    parser.add_argument("input", help="Đường dẫn file ghi âm (mp3/wav/m4a)")
    parser.add_argument("--out", "-o", default=None, help="Đường dẫn video đầu ra (mặc định <tên>_doodle.mp4)")
    parser.add_argument("--model", default="base", help="Model Whisper (tiny, base, small, medium)")
    args = parser.parse_args()

    inp = Path(args.input)
    out = args.out or inp.with_name(f"{inp.stem}_doodle.mp4")
    render_doodle_video(inp, out, model_size=args.model)

#!/usr/bin/env python3
"""
AGS-Video-Editing: Voice to Kraft Paper Doodle Storyboard
Biến file ghi âm thành video người que nét chì mộc mạc trên nền giấy kraft nâu.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def run_cmd(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Lệnh thất bại: {' '.join(cmd)}\nLỗi: {result.stderr}")
    return result

def draw_kraft_doodle_frame(text, pose_idx=0, width=1080, height=1920):
    # Nền giấy kraft màu nâu ấm
    img = Image.new("RGB", (width, height), "#E6D7B8")
    draw = ImageDraw.Draw(img)
    
    # 1. Vẽ mặt trời nét chì
    sun_x, sun_y = width - 250, 350
    draw.ellipse([sun_x - 60, sun_y - 60, sun_x + 60, sun_y + 60], outline="#3A3226", width=4)
    # Tia nắng
    import math
    for i in range(8):
        angle = i * (math.pi / 4)
        x1 = sun_x + int(80 * math.cos(angle))
        y1 = sun_y + int(80 * math.sin(angle))
        x2 = sun_x + int(110 * math.cos(angle))
        y2 = sun_y + int(110 * math.sin(angle))
        draw.line([x1, y1, x2, y2], fill="#3A3226", width=3)
        
    # 2. Vẽ tảng đá / mặt đất
    rock_y = height // 2 + 300
    draw.ellipse([width//2 - 400, rock_y, width//2 + 400, rock_y + 300], outline="#3A3226", fill="#D4C19C", width=5)
    
    # 3. Vẽ người que nét chì
    head_x = width // 2
    head_y = rock_y - 280
    head_r = 70
    draw.ellipse([head_x - head_r, head_y - head_r, head_x + head_r, head_y + head_r], outline="#2A241C", width=6)
    # Mắt miệng
    draw.ellipse([head_x - 25, head_y - 15, head_x - 15, head_y - 5], fill="#2A241C")
    draw.ellipse([head_x + 15, head_y - 15, head_x + 25, head_y - 5], fill="#2A241C")
    draw.arc([head_x - 25, head_y, head_x + 25, head_y + 35], start=0, end=180, fill="#2A241C", width=4)
    # Tóc vài cọng
    for angle in [-0.5, 0, 0.5]:
        draw.line([head_x + int(head_r*math.sin(angle)), head_y - head_r, head_x + int(100*math.sin(angle)), head_y - head_r - 30], fill="#2A241C", width=3)
        
    # Thân
    neck_y = head_y + head_r
    crotch_y = neck_y + 200
    draw.line([head_x, neck_y, head_x, crotch_y], fill="#2A241C", width=6)
    
    # Tay chân theo pose
    if pose_idx % 2 == 0:
        # Ngồi thiền
        draw.line([head_x, neck_y + 60, head_x - 90, neck_y + 140], fill="#2A241C", width=5)
        draw.line([head_x - 90, neck_y + 140, head_x - 10, crotch_y], fill="#2A241C", width=5)
        draw.line([head_x, neck_y + 60, head_x + 90, neck_y + 140], fill="#2A241C", width=5)
        draw.line([head_x + 90, neck_y + 140, head_x + 10, crotch_y], fill="#2A241C", width=5)
        # Chân xếp bằng
        draw.line([head_x, crotch_y, head_x - 160, crotch_y + 60], fill="#2A241C", width=5)
        draw.line([head_x - 160, crotch_y + 60, head_x, crotch_y + 80], fill="#2A241C", width=5)
        draw.line([head_x, crotch_y, head_x + 160, crotch_y + 60], fill="#2A241C", width=5)
        draw.line([head_x + 160, crotch_y + 60, head_x, crotch_y + 80], fill="#2A241C", width=5)
    else:
        # Đứng suy tư
        draw.line([head_x, neck_y + 50, head_x - 80, neck_y + 120], fill="#2A241C", width=5)
        draw.line([head_x - 80, neck_y + 120, head_x - 20, head_y + 40], fill="#2A241C", width=5)
        draw.line([head_x, neck_y + 50, head_x + 80, neck_y + 140], fill="#2A241C", width=5)
        draw.line([head_x, crotch_y, head_x - 80, crotch_y + 180], fill="#2A241C", width=5)
        draw.line([head_x, crotch_y, head_x + 80, crotch_y + 180], fill="#2A241C", width=5)

    # 4. Vẽ Sub chữ tiêu đề câu nói
    font = None
    for fn in ["Georgia.ttf", "Arial.ttf", "Helvetica.ttc"]:
        try:
            font = ImageFont.truetype(fn, 56)
            break
        except:
            pass
    if not font:
        font = ImageFont.load_default()
        
    sub_y = rock_y + 360
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw)//2, sub_y), text, font=font, fill="#2A241C")
    
    return img

def render_doodle_video(audio_path, output_path, model_size="base"):
    audio_path = Path(audio_path).resolve()
    output_path = Path(output_path).resolve()
    temp_dir = audio_path.parent / f"_ags_doodle_temp_{os.getpid()}"
    temp_dir.mkdir(exist_ok=True)
    
    from faster_whisper import WhisperModel
    print(f"[*] Bóc băng audio bằng Whisper...")
    model = WhisperModel(model_size, device="auto", compute_type="int8")
    segments, _ = model.transcribe(str(audio_path), beam_size=5)
    
    fps = 30
    import cv2
    import numpy as np
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    temp_video = temp_dir / "temp_doodle.mp4"
    writer = cv2.VideoWriter(str(temp_video), fourcc, fps, (1080, 1920))
    
    for idx, seg in enumerate(segments):
        text = seg.text.strip()
        dur = seg.end - seg.start
        num_frames = int(dur * fps)
        
        img = draw_kraft_doodle_frame(text, pose_idx=idx)
        frame_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        for _ in range(num_frames):
            writer.write(frame_cv)
            
    writer.release()
    
    print(f"[*] Ghép audio và chuẩn hóa âm lượng -14 LUFS...")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(temp_video),
        "-i", str(audio_path),
        "-af", "loudnorm=I=-14:LRA=11:TP=-1.5",
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "aac", "-b:a", "192k",
        str(output_path)
    ]
    run_cmd(cmd)
    
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    print(f"🎉 Hoàn thành video người que nét chì: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGS Voice to Kraft Paper Doodle")
    parser.add_argument("input", help="Đường dẫn file ghi âm (mp3/wav)")
    parser.add_argument("--out", "-o", default=None, help="Đường dẫn video đầu ra")
    parser.add_argument("--model", default="base", help="Model Whisper")
    args = parser.parse_args()
    
    inp = Path(args.input)
    out = args.out or inp.parent / f"{inp.stem}_doodle.mp4"
    render_doodle_video(inp, out, model_size=args.model)

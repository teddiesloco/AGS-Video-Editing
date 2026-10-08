#!/usr/bin/env python3
"""
AGS-Video-Editing: Voice to 2D Kinetic Typography
Biến đoạn ghi âm giọng nói thành video hoạt hình chữ nảy 2D sinh động.
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

def create_kinetic_card(text, width=1080, height=1920, bg_color="#FBF8F1", text_color="#222222", highlight_word=None):
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    font = None
    for fn in ["Arial Bold.ttf", "Arial.ttf", "Helvetica.ttc"]:
        try:
            font = ImageFont.truetype(fn, 72)
            break
        except:
            pass
    if not font:
        font = ImageFont.load_default()
        
    # Vẽ card trung tâm
    margin_x = 100
    card_y1 = height // 2 - 250
    card_y2 = height // 2 + 250
    draw.rounded_rectangle([margin_x, card_y1, width - margin_x, card_y2], radius=40, fill="#FFFFFF", outline="#E5E0D8", width=4)
    
    # Vẽ text
    words = text.split()
    line = ""
    lines = []
    for w in words:
        if len(line + " " + w) < 22:
            line += (" " if line else "") + w
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
        
    start_y = card_y1 + 80
    for l in lines:
        bbox = draw.textbbox((0, 0), l, font=font)
        lw = bbox[2] - bbox[0]
        x = (width - lw) // 2
        draw.text((x, start_y), l, font=font, fill=text_color)
        start_y += 100
        
    return img

def render_kinetic_video(audio_path, output_path, model_size="base"):
    audio_path = Path(audio_path).resolve()
    output_path = Path(output_path).resolve()
    temp_dir = audio_path.parent / f"_ags_kinetic_temp_{os.getpid()}"
    temp_dir.mkdir(exist_ok=True)
    
    from faster_whisper import WhisperModel
    print(f"[*] Bóc băng audio bằng Whisper...")
    model = WhisperModel(model_size, device="auto", compute_type="int8")
    segments, _ = model.transcribe(str(audio_path), beam_size=5)
    
    frames_list = []
    fps = 30
    import cv2
    import numpy as np
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    temp_video = temp_dir / "temp_video.mp4"
    writer = cv2.VideoWriter(str(temp_video), fourcc, fps, (1080, 1920))
    
    for seg in segments:
        text = seg.text.strip()
        dur = seg.end - seg.start
        num_frames = int(dur * fps)
        
        img = create_kinetic_card(text)
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
    print(f"🎉 Hoàn thành video hoạt hình chữ: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGS Voice to Kinetic 2D Video")
    parser.add_argument("input", help="Đường dẫn file ghi âm (mp3/wav)")
    parser.add_argument("--out", "-o", default=None, help="Đường dẫn video đầu ra")
    parser.add_argument("--model", default="base", help="Model Whisper")
    args = parser.parse_args()
    
    inp = Path(args.input)
    out = args.out or inp.parent / f"{inp.stem}_kinetic.mp4"
    render_kinetic_video(inp, out, model_size=args.model)

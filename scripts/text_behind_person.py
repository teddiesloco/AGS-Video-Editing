#!/usr/bin/env python3
"""
AGS-Video-Editing: Text Behind Person (Chữ chìm sau người)
Sử dụng AI Human Matting tách lớp người và ghép sandwich 3-layer trong FFmpeg.
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

def create_text_banner(text, width, height, output_image_path, font_size=110, color="yellow"):
    """Tạo ảnh chữ trong suốt PNG"""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Tìm font
    font = None
    for font_name in ["Arial Bold.ttf", "Arial.ttf", "Helvetica.ttc", "Impact.ttf"]:
        try:
            font = ImageFont.truetype(font_name, font_size)
            break
        except:
            pass
    if not font:
        font = ImageFont.load_default()
        
    text_color = (255, 215, 0, 255) if color == "yellow" else (255, 255, 255, 255)
    stroke_color = (0, 0, 0, 255)
    
    # Căn giữa ở nửa trên (tầm ngực / đầu)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = (width - text_w) // 2
    y = int(height * 0.28) # Vị trí 28% từ đỉnh màn hình
    
    draw.text((x, y), text, font=font, fill=text_color, stroke_width=6, stroke_fill=stroke_color)
    img.save(output_image_path)

def process_text_behind_person(video_path, hook_text, output_path, duration_hook=5.0):
    video_path = Path(video_path).resolve()
    output_path = Path(output_path).resolve()
    temp_dir = video_path.parent / f"_ags_mask_temp_{os.getpid()}"
    temp_dir.mkdir(exist_ok=True)
    
    # 1. Đo kích thước video
    cmd_info = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate",
        "-of", "json", str(video_path)
    ]
    info = json.loads(run_cmd(cmd_info).stdout)
    width = info["streams"][0]["width"]
    height = info["streams"][0]["height"]
    
    # 2. Tạo banner chữ
    text_png = temp_dir / "hook_text.png"
    create_text_banner(hook_text, width, height, text_png)
    
    # 3. Trích xuất mask người cho đoạn hook (mặc định 5s đầu)
    print(f"[*] Đang tách lớp người dùng Rembg cho {duration_hook}s đầu...")
    hook_clip = temp_dir / "hook_clip.mp4"
    run_cmd(["ffmpeg", "-y", "-i", str(video_path), "-t", str(duration_hook), "-c", "copy", str(hook_clip)])
    
    # Dùng rembg tạo mask cho đoạn hook
    from rembg import new_session, remove
    import cv2
    import numpy as np
    
    session = new_session("u2net_human_seg")
    cap = cv2.VideoCapture(str(hook_clip))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    
    mask_mp4 = temp_dir / "person_alpha.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_writer = cv2.VideoWriter(str(mask_mp4), fourcc, fps, (width, height))
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        # Convert BGR to RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Rembg return RGBA
        rgba = remove(rgb, session=session)
        # Lấy alpha channel làm mask xám
        alpha = rgba[:, :, 3]
        # Chuyển alpha thành 3 kênh BGR
        alpha_bgr = cv2.cvtColor(alpha, cv2.COLOR_GRAY2BGR)
        out_writer.write(alpha_bgr)
        
    cap.release()
    out_writer.release()
    
    # 4. Ghép 3-layer bằng FFmpeg
    print(f"[*] Đang ghép hiệu ứng 3-layer trong FFmpeg...")
    # [0:v] video gốc, [1:v] ảnh chữ, [2:v] mask alpha người
    filter_complex = (
        f"[0:v][1:v]overlay=0:0:enable='between(t,0,{duration_hook})'[bg_with_text];"
        f"[2:v]format=gray[mask];"
        f"[0:v][mask]alphamerge[person_layer];"
        f"[bg_with_text][person_layer]overlay=0:0:enable='between(t,0,{duration_hook})'[final_v]"
    )
    
    merge_cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(text_png),
        "-i", str(mask_mp4),
        "-filter_complex", filter_complex,
        "-map", "[final_v]",
        "-map", "0:a?",
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "copy",
        str(output_path)
    ]
    run_cmd(merge_cmd)
    
    # Dọn dẹp
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    print(f"🎉 Hoàn thành video chữ chìm sau người: {output_path}")

if __name__ == "__main__":
    import json
    parser = argparse.ArgumentParser(description="AGS Chữ chìm sau người (Text-Behind-Person)")
    parser.add_argument("input", help="Đường dẫn video")
    parser.add_argument("--text", "-t", required=True, help="Câu Hook cần đặt sau lưng")
    parser.add_argument("--out", "-o", default=None, help="Đường dẫn video đầu ra")
    parser.add_argument("--duration", "-d", type=float, default=5.0, help="Thời lượng hiển thị chữ (giây)")
    args = parser.parse_args()
    
    inp = Path(args.input)
    out = args.out or inp.parent / f"{inp.stem}_hook{inp.suffix}"
    process_text_behind_person(inp, args.text, out, args.duration)

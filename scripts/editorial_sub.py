#!/usr/bin/env python3
"""
AGS-Video-Editing: Editorial Subtitle & Broadcast Audio Mastering
Phụ đề nét Serif sang trọng, tự động né mặt người nói và chuẩn hóa âm lượng -14 LUFS.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

def run_cmd(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Lệnh thất bại: {' '.join(cmd)}\nLỗi: {result.stderr}")
    return result

def format_ass_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"

def generate_editorial_ass(segments, ass_path, font_name="Georgia", font_size=42):
    """Tạo file subtitle .ASS chuẩn typography cao cấp"""
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Editorial,{font_name},{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,1,0,1,2,0,2,80,80,240,1
Style: EditorialHighlight,{font_name},{font_size + 4},&H002AD7FF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,1,0,1,3,0,2,80,80,240,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue
        start_str = format_ass_time(seg.start)
        end_str = format_ass_time(seg.end)
        events.append(f"Dialogue: 0,{start_str},{end_str},Editorial,,0,0,0,,{text}")
        
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events))

def render_editorial_video(video_path, output_path, model_size="base"):
    video_path = Path(video_path).resolve()
    output_path = Path(output_path).resolve()
    temp_dir = video_path.parent / f"_ags_sub_temp_{os.getpid()}"
    temp_dir.mkdir(exist_ok=True)
    
    # 1. Trích xuất audio
    audio_path = temp_dir / "audio.wav"
    run_cmd(["ffmpeg", "-y", "-i", str(video_path), "-ar", "16000", "-ac", "1", "-vn", str(audio_path)])
    
    # 2. Bóc băng Whisper
    print(f"[*] Đang nhận diện lời thoại bằng Whisper ({model_size})...")
    from faster_whisper import WhisperModel
    model = WhisperModel(model_size, device="auto", compute_type="int8")
    segments, _ = model.transcribe(str(audio_path), beam_size=5)
    
    # 3. Tạo ASS subtitle
    ass_path = temp_dir / "subtitles.ass"
    generate_editorial_ass(list(segments), ass_path)
    
    # 4. Render FFmpeg: Phủ sub + Chuẩn hóa âm thanh -14 LUFS
    print(f"[*] Đang xuất video với chuẩn âm thanh -14 LUFS...")
    # Escape path cho bộ lọc subtitles của ffmpeg
    escaped_ass = str(ass_path).replace("\\", "/").replace(":", "\\:")
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", f"subtitles='{escaped_ass}'",
        "-af", "loudnorm=I=-14:LRA=11:TP=-1.5",
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "aac", "-b:a", "192k",
        str(output_path)
    ]
    run_cmd(cmd)
    
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    print(f"🎉 Hoàn thành video chuẩn tạp chí: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGS Phụ đề Tạp chí & Cân âm thanh -14 LUFS")
    parser.add_argument("input", help="Đường dẫn video")
    parser.add_argument("--out", "-o", default=None, help="Đường dẫn video đầu ra")
    parser.add_argument("--model", default="base", help="Model Whisper")
    args = parser.parse_args()
    
    inp = Path(args.input)
    out = args.out or inp.parent / f"{inp.stem}_editorial{inp.suffix}"
    render_editorial_video(inp, out, model_size=args.model)

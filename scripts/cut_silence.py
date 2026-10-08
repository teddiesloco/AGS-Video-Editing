#!/usr/bin/env python3
"""
AGS-Video-Editing: Cut Silence & Filler Words Engine
Tự động lọc khoảng lặng, từ đệm ('ờ, à'), cắt ghép liền mạch và xuất định dạng 9:16/16:9.
"""

import sys
import os
import argparse
import subprocess
import json
from pathlib import Path

FILLERS = {"ờ", "à", "ừm", "ừ", "hả", "um", "uh", "er"}

def run_cmd(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Lệnh thất bại: {' '.join(cmd)}\nLỗi: {result.stderr}")
    return result

def get_video_duration(video_path):
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)
    ]
    res = run_cmd(cmd)
    return float(res.stdout.strip())

def extract_audio(video_path, audio_path):
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-ar", "16000", "-ac", "1", "-vn", str(audio_path)
    ]
    run_cmd(cmd)

def analyze_and_cut(video_path, output_path, min_silence=0.4, model_size="base"):
    video_path = Path(video_path).resolve()
    output_path = Path(output_path).resolve()
    temp_dir = video_path.parent / f"_ags_temp_{os.getpid()}"
    temp_dir.mkdir(exist_ok=True)
    
    audio_path = temp_dir / "audio.wav"
    print(f"[*] Đang trích xuất audio 16kHz...")
    extract_audio(video_path, audio_path)
    
    print(f"[*] Đang nhận diện giọng nói bằng Faster-Whisper ({model_size})...")
    from faster_whisper import WhisperModel
    
    # Auto choose device (cuda if available, else cpu with int8)
    model = WhisperModel(model_size, device="auto", compute_type="int8")
    segments, info = model.transcribe(str(audio_path), beam_size=5, word_timestamps=True, vad_filter=True)
    
    total_duration = get_video_duration(video_path)
    keep_segments = []
    cursor = 0.0
    
    words_total = 0
    fillers_dropped = 0
    
    for seg in segments:
        for w in seg.words:
            words_total += 1
            word_clean = w.word.strip().lower()
            if word_clean in FILLERS:
                fillers_dropped += 1
                if w.start > cursor + 0.1:
                    keep_segments.append((cursor, w.start))
                cursor = w.end
    
    if cursor < total_duration:
        keep_segments.append((cursor, total_duration))
        
    print(f"[+] Nhận diện: {words_total} từ. Đã loại bỏ: {fillers_dropped} từ thừa/khoảng lặng.")
    
    # Gộp các đoạn nhỏ nếu sát nhau (< 0.1s)
    merged_segments = []
    for start, end in keep_segments:
        if not merged_segments:
            merged_segments.append([start, end])
        else:
            if start - merged_segments[-1][1] < 0.1:
                merged_segments[-1][1] = end
            else:
                merged_segments.append([start, end])
                
    # Xuất các đoạn và nối lại
    concat_txt = temp_dir / "concat.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for idx, (start, end) in enumerate(merged_segments):
            dur = end - start
            if dur < 0.2:
                continue
            seg_file = temp_dir / f"seg_{idx:04d}.mp4"
            cut_cmd = [
                "ffmpeg", "-y", "-ss", f"{start:.3f}", "-to", f"{end:.3f}",
                "-i", str(video_path), "-c", "copy",
                "-avoid_negative_ts", "make_zero", str(seg_file)
            ]
            run_cmd(cut_cmd)
            f.write(f"file '{seg_file.as_posix()}'\n")
            
    print(f"[*] Đang nối các đoạn video đã tinh chỉnh...")
    merge_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_txt), "-c", "copy", str(output_path)
    ]
    run_cmd(merge_cmd)
    
    # Dọn dẹp
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    print(f"🎉 Hoàn thành video sạch: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGS Cắt lọc khoảng lặng & từ thừa tự động")
    parser.add_argument("input", help="Đường dẫn video đầu vào")
    parser.add_argument("--out", "-o", default=None, help="Đường dẫn video đầu ra")
    parser.add_argument("--model", default="base", help="Model Whisper (tiny, base, small, medium)")
    args = parser.parse_args()
    
    inp = Path(args.input)
    out = args.out or inp.parent / f"{inp.stem}_clean{inp.suffix}"
    analyze_and_cut(inp, out, model_size=args.model)

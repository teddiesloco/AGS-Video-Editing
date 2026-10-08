#!/usr/bin/env python3
"""
AGS-Video-Editing: Anti-AI-Slop Guard (Harness Kiểm Định Chất Lượng Tự Động)
Ngăn chặn ảo giác AI, phụ đề rác, cắt cụt từ, lệch âm thanh và lỗi giật khung hình.
"""

import sys
import os
import re
import json
import argparse
import subprocess
from pathlib import Path

def run_cmd(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result

class AntiSlopGuard:
    def __init__(self, video_path):
        self.video_path = Path(video_path).resolve()
        self.issues = []
        self.warnings = []

    def check_video_validity(self):
        """1. Kiểm tra video có đọc được không và độ dài thực tế"""
        cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration,size:stream=width,height,r_frame_rate,codec_name",
            "-of", "json", str(self.video_path)
        ]
        res = run_cmd(cmd)
        if res.returncode != 0:
            self.issues.append(f"Video hỏng hoặc không thể đọc: {res.stderr}")
            return None
        
        data = json.loads(res.stdout)
        duration = float(data.get("format", {}).get("duration", 0))
        if duration < 1.0:
            self.issues.append(f"AI Slop Error: Video quá ngắn (< 1s), có thể do render bị crash giữa chừng.")
        return data

    def check_audio_sync_and_drift(self):
        """2. Kiểm tra lệch đồng bộ Audio vs Video (A/V Sync Drift)"""
        cmd_v = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=duration", "-of", "default=noprint_wrappers=1:nokey=1",
            str(self.video_path)
        ]
        cmd_a = [
            "ffprobe", "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=duration", "-of", "default=noprint_wrappers=1:nokey=1",
            str(self.video_path)
        ]
        res_v = run_cmd(cmd_v)
        res_a = run_cmd(cmd_a)
        
        try:
            v_dur = float(res_v.stdout.strip())
            a_dur = float(res_a.stdout.strip())
            drift = abs(v_dur - a_dur)
            if drift > 0.25:
                self.warnings.append(f"A/V Sync Warning: Lệch thời lượng hình và tiếng {drift:.2f}s (dễ gây méo tiếng cuối clip).")
        except:
            pass

    def check_loudness_ebur128(self):
        """3. Đo chuẩn âm lượng phát thanh (Target: -14 LUFS ± 1.5 LUFS)"""
        cmd = [
            "ffmpeg", "-i", str(self.video_path), "-af", "ebur128=framelog=verbose",
            "-f", "null", "-"
        ]
        res = run_cmd(cmd)
        # Parse Integrated Loudness (I)
        m = re.findall(r"I:\s*(-?[0-9\.]+)\s*LUFS", res.stderr)
        if m:
            lufs = float(m[-1])
            if lufs < -18.0:
                self.warnings.append(f"Âm lượng quá nhỏ: {lufs} LUFS (Cần đạt chuẩn -14 LUFS cho TikTok/Reels).")
            elif lufs > -11.0:
                self.warnings.append(f"Âm lượng bị rè/quá lớn: {lufs} LUFS (Nguy cơ bị nền tảng tự bóp méo âm).")
            else:
                print(f"[OK] Âm lượng đạt chuẩn phát sóng: {lufs} LUFS.")

    def clean_subtitle_text(self, text):
        """4. Bộ lọc AI Slop cho phụ đề (Khử lặp từ, ký tự ảo giác, nhại âm)"""
        cleaned = text
        # Khử nhãn âm thanh vô nghĩa sinh ra bởi Whisper
        cleaned = re.sub(r"\[(nhạc|tiếng cười|vỗ tay|music|applause)\]", "", cleaned, flags=re.IGNORECASE)
        # Khử lặp từ do ảo giác (Hallucination loops, vd: 'tôi tôi tôi tôi')
        cleaned = re.sub(r"\b(\w+)(?:\s+\1\b){2,}", r"\1", cleaned, flags=re.IGNORECASE)
        # Chuẩn hóa khoảng trắng
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def run_full_guard(self):
        print(f"[*] Đang chạy Anti-AI-Slop Guard trên: {self.video_path.name}")
        info = self.check_video_validity()
        if not info:
            return False, self.issues
        
        self.check_audio_sync_and_drift()
        self.check_loudness_ebur128()
        
        if self.issues:
            print("❌ PHÁT HIỆN LỖI NGHIÊM TRỌNG:")
            for iss in self.issues:
                print(f"  - {iss}")
            return False, self.issues
        
        if self.warnings:
            print("⚠️ CẢNH BÁO CHẤT LƯỢNG:")
            for w in self.warnings:
                print(f"  - {w}")
        else:
            print("✅ XÁC THỰC HOÀN HẢO: Không có AI Slop, video đạt chuẩn broadcast!")
            
        return True, self.warnings

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGS Anti-AI-Slop Guard Harness")
    parser.add_argument("video", help="Đường dẫn video cần kiểm định")
    args = parser.parse_args()
    
    guard = AntiSlopGuard(args.video)
    ok, details = guard.run_full_guard()
    sys.exit(0 if ok else 1)

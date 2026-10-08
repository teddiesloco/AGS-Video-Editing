#!/usr/bin/env python3
"""
AGS (Agent Space) Video Editing: Anti-AI-Slop Guard (harness kiểm định chất lượng tự động)
Kiểm tra video đầu ra trước khi bàn giao:
  1. File đọc được, thời lượng >= 1s.
  2. Có luồng âm thanh; độ dài hình và tiếng lệch nhau <= 0.25s.
  3. Âm lượng tích hợp (EBU R128) trong khoảng -14 ± 2 LUFS.
  4. Không có đoạn đen màn hình >= 0.5s (blackdetect).

Exit code: 0 = đạt · 2 = đạt nhưng có CẢNH BÁO (phải xem lại trước khi bàn giao) · 1 = LỖI nghiêm trọng.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

LUFS_TARGET = -14.0
LUFS_TOLERANCE = 2.0
MAX_AV_DRIFT = 0.25
BLACK_MIN_SECONDS = 0.5


def run_cmd(cmd):
    return subprocess.run([str(c) for c in cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, encoding="utf-8", errors="replace")


class AntiSlopGuard:
    def __init__(self, video_path):
        self.video_path = Path(video_path).resolve()
        self.issues = []
        self.warnings = []
        self.duration = 0.0

    def check_video_validity(self):
        """1. Video đọc được và đủ dài."""
        res = run_cmd([
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration,size:stream=codec_type,width,height,r_frame_rate,codec_name",
            "-of", "json", self.video_path,
        ])
        if res.returncode != 0:
            self.issues.append(f"Video hỏng hoặc không thể đọc: {res.stderr.strip()}")
            return None
        data = json.loads(res.stdout)
        self.duration = float(data.get("format", {}).get("duration", 0) or 0)
        if self.duration < 1.0:
            self.issues.append("Video quá ngắn (< 1s), có thể render bị crash giữa chừng.")
        if not any(s.get("codec_type") == "video" for s in data.get("streams", [])):
            self.issues.append("Không có luồng hình (video stream).")
        return data

    def check_audio_sync_and_drift(self, info):
        """2. Có tiếng và độ dài hình/tiếng khớp nhau."""
        if not any(s.get("codec_type") == "audio" for s in info.get("streams", [])):
            self.warnings.append("Không có luồng âm thanh (video câm).")
            return False

        def stream_duration(selector):
            res = run_cmd(["ffprobe", "-v", "error", "-select_streams", selector, "-show_entries",
                           "stream=duration", "-of", "default=noprint_wrappers=1:nokey=1", self.video_path])
            try:
                return float(res.stdout.strip().splitlines()[0])
            except (ValueError, IndexError):
                return None

        v_dur, a_dur = stream_duration("v:0"), stream_duration("a:0")
        if v_dur is not None and a_dur is not None:
            drift = abs(v_dur - a_dur)
            if drift > MAX_AV_DRIFT:
                self.warnings.append(f"Lệch thời lượng hình ({v_dur:.2f}s) và tiếng ({a_dur:.2f}s): {drift:.2f}s.")
        return True

    def check_loudness_ebur128(self):
        """3. Âm lượng tích hợp -14 ± 2 LUFS."""
        res = run_cmd(["ffmpeg", "-hide_banner", "-nostats", "-i", self.video_path,
                       "-af", "ebur128", "-f", "null", "-"])
        found = re.findall(r"I:\s*(-?[0-9.]+)\s*LUFS", res.stderr)
        if not found:
            self.warnings.append("Không đo được âm lượng (ebur128).")
            return
        lufs = float(found[-1])
        if lufs < LUFS_TARGET - LUFS_TOLERANCE:
            self.warnings.append(f"Âm lượng quá nhỏ: {lufs} LUFS (chuẩn {LUFS_TARGET} ± {LUFS_TOLERANCE}).")
        elif lufs > LUFS_TARGET + LUFS_TOLERANCE:
            self.warnings.append(f"Âm lượng quá lớn: {lufs} LUFS (chuẩn {LUFS_TARGET} ± {LUFS_TOLERANCE}).")
        else:
            print(f"[OK] Âm lượng đạt chuẩn: {lufs} LUFS.")

    def check_black_frames(self):
        """4. Đoạn đen màn hình."""
        res = run_cmd(["ffmpeg", "-hide_banner", "-nostats", "-i", self.video_path,
                       "-vf", f"blackdetect=d={BLACK_MIN_SECONDS}:pix_th=0.10", "-an", "-f", "null", "-"])
        spans = [(float(s), float(e)) for s, e in
                 re.findall(r"black_start:\s*([0-9.]+)\s+black_end:\s*([0-9.]+)", res.stderr)]
        black = sum(e - s for s, e in spans)
        if self.duration and black >= 0.9 * self.duration:
            self.issues.append(f"Video gần như đen toàn bộ ({black:.1f}s / {self.duration:.1f}s).")
        elif spans:
            listed = ", ".join(f"{s:.1f}-{e:.1f}s" for s, e in spans[:5])
            self.warnings.append(f"Có {len(spans)} đoạn đen màn hình >= {BLACK_MIN_SECONDS}s: {listed}.")
        else:
            print("[OK] Không có đoạn đen màn hình.")

    def run_full_guard(self):
        print(f"[*] Đang chạy Anti-AI-Slop Guard trên: {self.video_path.name}")
        info = self.check_video_validity()
        if info is None:
            print("❌ PHÁT HIỆN LỖI NGHIÊM TRỌNG:")
            for issue in self.issues:
                print(f"  - {issue}")
            return 1
        if self.check_audio_sync_and_drift(info):
            self.check_loudness_ebur128()
        self.check_black_frames()

        if self.issues:
            print("❌ PHÁT HIỆN LỖI NGHIÊM TRỌNG:")
            for issue in self.issues:
                print(f"  - {issue}")
            return 1
        if self.warnings:
            print("⚠️ CẢNH BÁO CHẤT LƯỢNG (xem lại trước khi bàn giao):")
            for warning in self.warnings:
                print(f"  - {warning}")
            return 2
        print("✅ ĐẠT: đọc được, đồng bộ hình-tiếng, -14 LUFS, không đen màn hình.")
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGS (Agent Space) — Anti-AI-Slop Guard")
    parser.add_argument("video", help="Đường dẫn video cần kiểm định")
    args = parser.parse_args()
    sys.exit(AntiSlopGuard(args.video).run_full_guard())

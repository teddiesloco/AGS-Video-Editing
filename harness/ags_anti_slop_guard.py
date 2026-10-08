#!/usr/bin/env python3
"""
AGS (Agent Space) Video Editing: Anti-AI-Slop Guard — kiểm định video trước khi bàn giao.

LỖI — exit 1, không bàn giao:
  - Không đọc được, không có luồng hình, hoặc ngắn hơn 1 s.
  - Đen màn hình >= 90% thời lượng (blackdetect) hoặc đứng hình >= 90% thời lượng (freezedetect).
  - Có luồng tiếng nhưng im lặng >= 90% thời lượng (silencedetect).
CẢNH BÁO — exit 2, phải đọc và xử lý trước khi bàn giao:
  - Không có luồng tiếng; độ dài hình và tiếng lệch nhau > 0.25 s.
  - Âm lượng tích hợp ngoài -14 ± 2 LUFS; true peak > -1.0 dBTP (EBU R128: ebur128 peak=true).
  - Đoạn đen >= 0.5 s; đoạn đứng hình >= 5 s; khoảng lặng (dead air, dưới -50 dBFS) >= 2 s.
ĐẠT — exit 0: không lỗi, không cảnh báo.

--contact-sheet <ảnh.jpg> [--frames N]: xuất ảnh lưới N khung (khung 0 + rải đều cả video) có ghi mốc thời gian, để model
thị giác tự soát; video dọc có viền hồng đánh dấu vùng an toàn (ags_common.safe_box).
Vòng render → lấy mẫu → soát → sửa: harness/QUY-TRINH-KIEM-DINH.md.
"""

import argparse
import io
import json
import math
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from ags_common import load_font, safe_box  # noqa: E402

LUFS_TARGET, LUFS_TOLERANCE = -14.0, 2.0
TRUE_PEAK_MAX = -1.0          # dBTP
MAX_AV_DRIFT = 0.25           # giây
BLACK_MIN_SECONDS = 0.5
FREEZE_MIN_SECONDS = 5.0
SILENCE_DB, SILENCE_MIN_SECONDS = -50, 2.0
FAIL_RATIO = 0.9              # >= 90% thời lượng đen / đứng / câm = lỗi
SAFE_ZONE_COLOR = (255, 0, 200)


def run(cmd):
    return subprocess.run([str(c) for c in cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, encoding="utf-8", errors="replace")


def spans(log, start_key, end_key, total):
    """Các đoạn [(start, end)] từ log FFmpeg; đoạn chưa đóng khi hết file thì kết thúc ở `total`."""
    result, start = [], None
    for key, value in re.findall(rf"({start_key}|{end_key}):\s*(-?[0-9.]+)", log):
        if key == start_key:
            start = float(value)
        elif start is not None:
            result.append((start, float(value)))
            start = None
    if start is not None:
        result.append((start, total))
    return result


def listed(items):
    return ", ".join(f"{s:.1f}-{e:.1f}s" for s, e in items[:5]) + (" …" if len(items) > 5 else "")


class AntiSlopGuard:
    def __init__(self, video_path):
        self.video_path = Path(video_path).resolve()
        self.issues, self.warnings, self.ok = [], [], []
        self.duration = 0.0
        self.size = None
        self.measures = {}

    def check_streams(self):
        """Đọc được, đủ dài, có hình; có tiếng; độ dài hình và tiếng khớp nhau."""
        res = run(["ffprobe", "-v", "error", "-show_entries",
                   "format=duration:stream=codec_type,width,height,duration", "-of", "json", self.video_path])
        if res.returncode != 0:
            self.issues.append(f"Video hỏng hoặc không thể đọc: {res.stderr.strip()[-500:]}")
            return False
        data = json.loads(res.stdout)
        self.duration = float(data.get("format", {}).get("duration", 0) or 0)
        streams = data.get("streams", [])
        video = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
        if video is None:
            self.issues.append("Không có luồng hình (video stream).")
            return False
        self.size = (video["width"], video["height"])
        if self.duration < 1.0:
            self.issues.append("Video quá ngắn (< 1s), có thể render bị crash giữa chừng.")
        if audio is None:
            self.warnings.append("Không có luồng âm thanh (video câm).")
            return True
        self.measures["has_audio"] = True
        try:
            drift = abs(float(video["duration"]) - float(audio["duration"]))
        except (KeyError, TypeError, ValueError):
            return True
        self.measures["av_drift"] = round(drift, 3)
        if drift > MAX_AV_DRIFT:
            self.warnings.append(f"Lệch độ dài hình và tiếng {drift:.2f}s (cho phép {MAX_AV_DRIFT}s).")
        else:
            self.ok.append(f"Hình-tiếng khớp (lệch {drift:.2f}s).")
        return True

    def check_video(self):
        """Đen màn hình (blackdetect) và đứng hình (freezedetect)."""
        log = run(["ffmpeg", "-hide_banner", "-nostats", "-i", self.video_path, "-an", "-vf",
                   f"blackdetect=d={BLACK_MIN_SECONDS}:pix_th=0.10,freezedetect=n=-60dB:d={FREEZE_MIN_SECONDS}",
                   "-f", "null", "-"]).stderr
        for label, items, minimum in [
            ("đen màn hình", spans(log, "black_start", "black_end", self.duration), BLACK_MIN_SECONDS),
            ("đứng hình", spans(log, "freeze_start", "freeze_end", self.duration), FREEZE_MIN_SECONDS),
        ]:
            total = sum(e - s for s, e in items)
            if self.duration and total >= FAIL_RATIO * self.duration:
                self.issues.append(f"Video gần như {label} toàn bộ ({total:.1f}s / {self.duration:.1f}s).")
            elif items:
                self.warnings.append(f"Có {len(items)} đoạn {label} >= {minimum}s: {listed(items)}.")
            else:
                self.ok.append(f"Không có đoạn {label} >= {minimum}s.")

    def check_audio(self):
        """Âm lượng tích hợp, true peak (EBU R128) và khoảng lặng dài (dead air)."""
        log = run(["ffmpeg", "-hide_banner", "-nostats", "-i", self.video_path, "-vn", "-af",
                   f"ebur128=peak=true:framelog=verbose,silencedetect=n={SILENCE_DB}dB:d={SILENCE_MIN_SECONDS}",
                   "-f", "null", "-"]).stderr
        silences = spans(log, "silence_start", "silence_end", self.duration)
        silent = sum(e - s for s, e in silences)
        if self.duration and silent >= FAIL_RATIO * self.duration:
            self.issues.append(f"Luồng tiếng gần như câm ({silent:.1f}s / {self.duration:.1f}s dưới {SILENCE_DB} dBFS).")
            return
        if silences:
            self.warnings.append(f"Có {len(silences)} khoảng lặng >= {SILENCE_MIN_SECONDS}s (dead air): {listed(silences)}.")
        else:
            self.ok.append(f"Không có khoảng lặng >= {SILENCE_MIN_SECONDS}s.")

        loudness = re.findall(r"I:\s*(-?[0-9.]+)\s*LUFS", log)
        peak = re.findall(r"Peak:\s*(-?[0-9.]+|-inf)\s*dBFS", log)
        if not loudness:
            self.warnings.append("Không đo được âm lượng (ebur128).")
        else:
            lufs = float(loudness[-1])
            self.measures["lufs"] = lufs
            if abs(lufs - LUFS_TARGET) > LUFS_TOLERANCE:
                self.warnings.append(f"Âm lượng {lufs} LUFS ngoài chuẩn {LUFS_TARGET} ± {LUFS_TOLERANCE}.")
            else:
                self.ok.append(f"Âm lượng {lufs} LUFS (chuẩn {LUFS_TARGET} ± {LUFS_TOLERANCE}).")
        if peak and peak[-1] != "-inf":
            true_peak = float(peak[-1])
            self.measures["true_peak_dbtp"] = true_peak
            if true_peak > TRUE_PEAK_MAX:
                self.warnings.append(f"True peak {true_peak} dBTP vượt trần {TRUE_PEAK_MAX} dBTP (dễ méo tiếng).")
            else:
                self.ok.append(f"True peak {true_peak} dBTP (trần {TRUE_PEAK_MAX}).")

    def contact_sheet(self, output_path, frames=12):
        """Ảnh lưới `frames` khung: khung 0 rồi rải đều tới cuối video, mỗi khung ghi mốc thời gian."""
        frames = max(1, frames)
        width, height = self.size
        vertical = height >= 1.6 * width
        tile_w = 270 if vertical else 480
        tile_h = round(tile_w * height / width)
        cols = min(frames, 4 if vertical else 3)
        rows = math.ceil(frames / cols)
        label_h = 34
        sheet = Image.new("RGB", (cols * tile_w, rows * (tile_h + label_h)), (24, 24, 24))
        draw = ImageDraw.Draw(sheet)
        font = load_font("bold", 20)
        x0, y0, x1, y1 = safe_box(width, height)
        scale = tile_w / width
        for k in range(frames):
            t = self.duration * k / frames
            png = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(self.video_path),
                                  "-frames:v", "1", "-f", "image2pipe", "-c:v", "png", "-"],
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout
            col, row = k % cols, k // cols
            left, top = col * tile_w, row * (tile_h + label_h)
            if png:
                with Image.open(io.BytesIO(png)) as im:
                    sheet.paste(im.convert("RGB").resize((tile_w, tile_h), Image.LANCZOS), (left, top))
            if vertical:
                draw.rectangle([left + x0 * scale, top + y0 * scale, left + x1 * scale, top + y1 * scale],
                               outline=SAFE_ZONE_COLOR, width=2)
            draw.text((left + 8, top + tile_h + 6), f"#{k}  t={t:.2f}s" + ("  (khung 0)" if k == 0 else ""),
                      font=font, fill=(255, 255, 255))
        out = Path(output_path).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(out, "JPEG", quality=90)
        return out

    def run_full_guard(self, contact_sheet=None, frames=12):
        print(f"[*] Đang chạy Anti-AI-Slop Guard trên: {self.video_path.name}")
        if self.check_streams():
            self.check_video()
            if self.measures.get("has_audio"):
                self.check_audio()
            if contact_sheet:
                print(f"[*] Contact sheet ({frames} khung): {self.contact_sheet(contact_sheet, frames)}")
        for line in self.ok:
            print(f"[OK] {line}")
        summary = {"duration": round(self.duration, 2), **{k: v for k, v in self.measures.items() if k != "has_audio"}}
        print(f"[Đo] {json.dumps(summary, ensure_ascii=False)}")
        if self.issues:
            print("❌ LỖI NGHIÊM TRỌNG (exit 1 — không bàn giao):")
            for issue in self.issues + self.warnings:
                print(f"  - {issue}")
            return 1
        if self.warnings:
            print("⚠️ CẢNH BÁO (exit 2 — xem lại trước khi bàn giao):")
            for warning in self.warnings:
                print(f"  - {warning}")
            return 2
        print("✅ ĐẠT (exit 0): đọc được, hình-tiếng khớp, -14 LUFS, true peak an toàn, không đen/đứng hình/lặng dài.")
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGS (Agent Space) — Anti-AI-Slop Guard (exit 0 đạt · 2 cảnh báo · 1 lỗi)")
    parser.add_argument("video", help="Đường dẫn video cần kiểm định")
    parser.add_argument("--contact-sheet", metavar="ANH.jpg", help="Xuất ảnh lưới khung hình để soát bằng mắt / model thị giác")
    parser.add_argument("--frames", type=int, default=12, help="Số khung trong contact sheet (mặc định 12, gồm khung 0)")
    args = parser.parse_args()
    sys.exit(AntiSlopGuard(args.video).run_full_guard(args.contact_sheet, args.frames))

---
name: ags-edit-az
description: "AGS (Agent Space) — cắt video nói chuyện từ A-Z: bóc băng Whisper theo từng từ, bỏ khoảng lặng dài và từ đệm ('ờ, à, ừm'), cắt chính xác từng khung hình, nối liền mạch và chuẩn hoá âm lượng -14 LUFS (giữ nguyên khung hình gốc)."
---

# /ags-edit-az — Cắt Khoảng Lặng & Từ Đệm

Dành cho khi: bạn vừa quay xong video thô một đúp (one-take) và muốn bản sạch, gọn nhịp ngay.

## Cách dùng
> Lệnh chạy từ thư mục gốc repo AGS Video Editing (hai cấp trên thư mục chứa file này) bằng Python của venv: macOS `./venv/bin/python`, Windows `venv\Scripts\python`.
```bash
python scripts/ags_cut_silence.py <duong_dan_video> [--out <video_xuat.mp4>] [--min-silence 0.4] [--model base]
```
Mặc định xuất `<tên>_clean.mp4` cạnh video gốc.

## Chức năng
1. Faster-Whisper nhận diện từng từ kèm mốc thời gian (lần chạy đầu tự tải model Whisper).
2. Bỏ khoảng lặng dài hơn `--min-silence` giây (mặc định 0.4s, chừa 0.12s mỗi đầu cho tự nhiên) và các từ đệm `ờ, à, ừm, ừ, hả, um, uh, er`.
3. Cắt chính xác từng khung hình (encode lại H.264), nối liền mạch, chuẩn hoá âm lượng -14 LUFS (AAC 48 kHz). Giữ nguyên tỉ lệ khung hình gốc.

## Kiểm định
```bash
python harness/ags_anti_slop_guard.py <video_xuat.mp4>
```

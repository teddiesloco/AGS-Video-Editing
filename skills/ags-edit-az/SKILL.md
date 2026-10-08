---
name: ags-edit-az
description: "AGS (Agent Space) — làm sạch video nói chuyện quay thô: đo độ to để bỏ khoảng lặng dài, bóc băng Whisper để bỏ từ đệm ('ờ, à, ừm'), cắt chính xác từng khung hình, nối tiếng bằng crossfade không lách cách, chuẩn -14 LUFS. Dùng khi người dùng muốn cắt lặng, bỏ ậm ừ, làm gọn nhịp video quay một đúp, talking-head hoặc podcast có hình."
compatibility: "Cần Python 3.10+, FFmpeg và thư viện trong requirements.txt; lần đầu tải model Whisper (cần Internet)."
license: "PolyForm Strict 1.0.0 — xem LICENSE"
---

# /ags-edit-az — Cắt Khoảng Lặng & Từ Đệm

> Lệnh chạy từ thư mục gốc repo AGS Video Editing (hai cấp trên file này) — hoặc từ thư mục của skill nếu dùng bản zip
> (đã kèm `scripts/`, `harness/`) — bằng Python có đủ thư viện (venv của repo: macOS `./venv/bin/python`, Windows `venv\Scripts\python`).

```bash
python scripts/ags_cut_silence.py <video> [--out <video_xuat.mp4>] [--min-silence 0.4] [--threshold-db -30] [--model base]
```
Mặc định xuất `<tên>_clean.mp4` cạnh video gốc.

## Cách làm
1. Đo độ to audio (RMS 30 ms, bước 10 ms). Mức giọng nói = phân vị 95% độ to của file; chỗ nhỏ hơn mức đó quá
   `--threshold-db` dB (mặc định -30) và dài ≥ `--min-silence` giây (mặc định 0.4) là khoảng lặng → cắt,
   chừa 0.10 s trước và 0.15 s sau lời nói.
2. Faster-Whisper bóc băng theo từng từ; từ đệm `ờ, à, ừm, ừ, hả, um, uh, er` bị cắt, mép cắt dời về chỗ nhỏ tiếng nhất gần đó.
3. Mốc cắt làm tròn theo khung hình: hình cắt chính xác từng khung (encode lại H.264), tiếng nối bằng crossfade
   equal-power 25 ms (không lách cách), chuẩn hoá -14 LUFS (AAC 48 kHz). Giữ nguyên khung hình gốc.

## Chỉnh khi kết quả chưa ưng
- Cắt cả tiếng nói nhỏ / hơi thở quan trọng → `--threshold-db -40`. Phòng ồn, cắt chưa đủ → `--threshold-db -20`.
- Nhịp quá dồn → `--min-silence 0.6`.
- Tiếng Việt nhiều từ đệm bị bỏ sót → model lớn hơn: `--model small`, `--model large-v3-turbo` (tải ~1.6 GB lần đầu).

## Kiểm định (bắt buộc)
```bash
python harness/ags_anti_slop_guard.py <video_xuat.mp4> --contact-sheet <video_xuat>_sheet.jpg
```
Exit `0` đạt · `2` cảnh báo (đọc, sửa hoặc báo người dùng) · `1` lỗi (không bàn giao). Vòng soát: `harness/QUY-TRINH-KIEM-DINH.md`.

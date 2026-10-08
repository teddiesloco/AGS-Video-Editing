---
name: ags-voice-kinetic
description: "AGS (Agent Space) — biến file ghi âm thành video chữ 2D dọc 1080x1920: chia lời thành cụm ngắn ≤ 3 giây, mỗi cụm bật nảy (pop-in) trên card trắng nằm gọn trong vùng an toàn, khớp đúng thời gian giọng nói, âm lượng -14 LUFS. Dùng khi có voice/podcast/bài nói mà không có hình, cần video kinetic typography không lộ mặt."
compatibility: "Cần Python 3.10+, FFmpeg và thư viện trong requirements.txt; lần đầu tải model Whisper (cần Internet)."
license: "PolyForm Strict 1.0.0 — xem LICENSE"
---

# /ags-voice-kinetic — Hoạt Hình Chữ 2D Từ Giọng Nói

> Lệnh chạy từ thư mục gốc repo AGS Video Editing (hai cấp trên file này) — hoặc từ thư mục của skill nếu dùng bản zip
> (đã kèm `scripts/`, `harness/`) — bằng Python có đủ thư viện (venv của repo: macOS `./venv/bin/python`, Windows `venv\Scripts\python`).

```bash
python scripts/ags_voice_to_kinetic.py <audio.mp3|wav|m4a> [--out <video_xuat.mp4>] [--model base]
```
Mặc định xuất `<tên>_kinetic.mp4`.

## Chức năng
1. Faster-Whisper bóc băng theo từng từ, gom cụm ≤ 32 ký tự / ≤ 3 giây, ngắt ở dấu câu; chữ chuẩn hoá NFC.
2. Mỗi cụm hiện trên card trắng bo góc, bật nảy ~0.27 s; card (kể cả lúc nảy) nằm trong vùng an toàn 9:16; chữ giữ
   tới khi cụm sau bắt đầu nên hình luôn khớp tiếng.
3. Xuất MP4 H.264 1080x1920 30fps, AAC 48 kHz, -14 LUFS.

## Kiểm định (bắt buộc)
```bash
python harness/ags_anti_slop_guard.py <video_xuat.mp4> --contact-sheet <video_xuat>_sheet.jpg
```
Exit `0` đạt · `2` cảnh báo (ví dụ khoảng lặng ≥ 2 s trong file ghi âm → cắt bớt bằng /ags-edit-az rồi dựng lại) · `1` lỗi.
Vòng soát: `harness/QUY-TRINH-KIEM-DINH.md`.

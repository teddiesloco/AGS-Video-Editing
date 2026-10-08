---
name: ags-voice-kinetic
description: "AGS (Agent Space) — biến file ghi âm thành video chữ 2D 1080x1920: chia lời thành cụm ngắn ≤ 3 giây, mỗi cụm bật nảy (pop-in) trên card trắng, khớp đúng thời gian giọng nói, âm lượng -14 LUFS."
---

# /ags-voice-kinetic — Hoạt Hình Chữ 2D Từ Giọng Nói

Dành cho khi: bạn có file ghi âm hoặc podcast ngắn, muốn thành video trực quan mà không cần quay mặt.

## Cách dùng
> Lệnh chạy từ thư mục gốc repo AGS Video Editing (hai cấp trên thư mục chứa file này) bằng Python của venv: macOS `./venv/bin/python`, Windows `venv\Scripts\python`.
```bash
python scripts/ags_voice_to_kinetic.py <duong_dan_audio.mp3> [--out <video_xuat.mp4>] [--model base]
```
Mặc định xuất `<tên>_kinetic.mp4`.

## Chức năng
1. Faster-Whisper bóc băng theo từng từ, gom cụm ≤ 32 ký tự / ≤ 3 giây, ngắt ở dấu câu.
2. Mỗi cụm hiện trên card trắng bo góc với hiệu ứng bật nảy ~0.27s; chữ giữ trên màn hình tới khi cụm sau bắt đầu, nên hình luôn khớp tiếng.
3. Xuất MP4 H.264 1080x1920 30fps, AAC 48 kHz, -14 LUFS.

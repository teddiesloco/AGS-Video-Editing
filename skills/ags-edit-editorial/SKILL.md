---
name: ags-edit-editorial
description: "AGS (Agent Space) — phụ đề phong cách tạp chí: bóc băng Whisper theo từ, chia câu ngắn, đốt phụ đề nét Serif (Georgia) trắng viền đen đúng kích thước video và chuẩn hoá âm lượng -14 LUFS."
---

# /ags-edit-editorial — Phụ Đề Tạp Chí & Cân Âm -14 LUFS

Dành cho khi: video chia sẻ chuyên gia, phong cách sống, bất động sản cao cấp cần chữ tinh tế và âm thanh chuẩn.

## Cách dùng
> Lệnh chạy từ thư mục gốc repo AGS Video Editing (hai cấp trên thư mục chứa file này) bằng Python của venv: macOS `./venv/bin/python`, Windows `venv\Scripts\python`.
```bash
python scripts/ags_editorial_sub.py <duong_dan_video> [--out <video_xuat.mp4>] [--model base]
```
Mặc định xuất `<tên>_editorial.mp4`.

## Chức năng
1. Faster-Whisper bóc băng theo từng từ (tự nhận diện ngôn ngữ), gom câu ≤ 42 ký tự / ≤ 4 giây, lọc rác Whisper (nhãn `[nhạc]`, từ lặp ≥ 3 lần).
2. Sinh phụ đề `.ASS` theo đúng kích thước hiển thị của video (kể cả video điện thoại có metadata xoay): cỡ chữ ≈ 5% cạnh ngắn; video dọc đặt chữ cách đáy 20% (tránh vùng nút/caption TikTok, Reels), video ngang cách đáy 8%.
3. Chuẩn hoá âm lượng `loudnorm=I=-14:LRA=11:TP=-1.5`, AAC 48 kHz.

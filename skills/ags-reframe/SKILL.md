---
name: ags-reframe
description: "AGS (Agent Space) — chuyển video ngang (16:9, 4:3, 1:1) thành video dọc 9:16 1080x1920 với khung cắt tự bám theo khuôn mặt chính (OpenCV YuNet), lia mượt, không giật; không thấy mặt thì cắt giữa. Dùng khi cần đăng video quay ngang, podcast, phỏng vấn, livestream lên TikTok, Reels, Shorts."
compatibility: "Cần Python 3.10+, FFmpeg, OpenCV (requirements.txt); lần đầu tải model YuNet ~230 KB (cần Internet, có kiểm SHA-256)."
license: "PolyForm Strict 1.0.0 — xem LICENSE"
---

# /ags-reframe — Reframe Ngang → Dọc 9:16 Bám Khuôn Mặt

> Lệnh chạy từ thư mục gốc repo AGS Video Editing (hai cấp trên file này) — hoặc từ thư mục của skill nếu dùng bản zip
> (đã kèm `scripts/`, `harness/`) — bằng Python có đủ thư viện (venv của repo: macOS `./venv/bin/python`, Windows `venv\Scripts\python`).

```bash
python scripts/ags_reframe.py <video_ngang.mp4> [--out <video_9x16.mp4>]
```
Mặc định xuất `<tên>_9x16.mp4` (1080x1920, H.264, AAC 48 kHz, -14 LUFS).

## Cách làm
1. Lấy mẫu 5 khung/giây (thu nhỏ bề ngang 640 px), dò mặt bằng OpenCV `FaceDetectorYN` + model YuNet (MIT; lần đầu
   tải về `~/.cache/ags-video-editing/`).
2. Mặt chính = mặt to nhất; nếu có mặt gần vị trí trước và đủ to thì giữ mặt đó (không nhảy qua lại giữa 2 người).
3. Làm mượt: người nhúc nhích trong vùng 6% bề ngang khung cắt thì khung đứng yên; di chuyển thật thì khung lia mượt
   (lọc trung vị + trung bình trượt ~1 s).
4. Khung cắt cao bằng video gốc, rộng 9/16 chiều cao, rồi phóng về 1080x1920.

Không thấy mặt nào, hoặc không tải được model → cắt chính giữa (có báo). Video đã dọc → chỉ đổi cỡ về 1080x1920.
Muốn làm nhiều short từ video dài: dùng `/ags-clip-shorts` (đã gồm reframe + phụ đề).

## Kiểm định (bắt buộc)
```bash
python harness/ags_anti_slop_guard.py <video_9x16.mp4> --contact-sheet <video_9x16>_sheet.jpg
```
Trên contact sheet: mặt người nói luôn nằm trong khung ở mọi ô. Exit `0` đạt · `2` cảnh báo · `1` lỗi.
Vòng soát: `harness/QUY-TRINH-KIEM-DINH.md`.

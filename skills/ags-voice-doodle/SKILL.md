---
name: ags-voice-doodle
description: "AGS (Agent Space) — biến file ghi âm thành video người que nét chì trên giấy kraft 1080x1920: 2 thế (ngồi thiền / đứng suy tư) xen kẽ theo từng cụm lời, phụ đề Serif trong vùng an toàn, âm lượng -14 LUFS. Dùng khi kể chuyện triết lý, bài học cuộc sống, podcast giấu mặt cần hình minh hoạ ấm áp."
compatibility: "Cần Python 3.10+, FFmpeg và thư viện trong requirements.txt; lần đầu tải model Whisper (cần Internet)."
license: "PolyForm Strict 1.0.0 — xem LICENSE"
---

# /ags-voice-doodle — Người Que Nét Chì Trên Giấy Kraft

> Lệnh chạy từ thư mục gốc repo AGS Video Editing (hai cấp trên file này) — hoặc từ thư mục của skill nếu dùng bản zip
> (đã kèm `scripts/`, `harness/`) — bằng Python có đủ thư viện (venv của repo: macOS `./venv/bin/python`, Windows `venv\Scripts\python`).

```bash
python scripts/ags_voice_to_doodle.py <audio.mp3|wav|m4a> [--out <video_xuat.mp4>] [--model base]
```
Mặc định xuất `<tên>_doodle.mp4`.

## Chức năng
1. Nền giấy kraft nâu, mặt trời và tảng đá nét chì, khung 1080x1920.
2. Người que đổi thế xen kẽ (ngồi thiền / đứng suy tư) theo từng cụm lời ≤ 40 ký tự / ≤ 3.5 giây, khớp đúng thời gian giọng nói.
3. Phụ đề Serif tối đa 3 dòng, chuẩn hoá NFC, nằm trong vùng an toàn 9:16; âm lượng -14 LUFS, AAC 48 kHz.

## Kiểm định (bắt buộc)
```bash
python harness/ags_anti_slop_guard.py <video_xuat.mp4> --contact-sheet <video_xuat>_sheet.jpg
```
Exit `0` đạt · `2` cảnh báo · `1` lỗi. Vòng soát: `harness/QUY-TRINH-KIEM-DINH.md`.

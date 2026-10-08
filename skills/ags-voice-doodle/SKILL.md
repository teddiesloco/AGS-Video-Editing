---
name: ags-voice-doodle
description: "AGS (Agent Space) — biến file ghi âm thành video người que nét chì trên giấy kraft 1080x1920: 2 thế (ngồi thiền / đứng suy tư) xen kẽ theo từng cụm lời, phụ đề Serif, âm lượng -14 LUFS."
---

# /ags-voice-doodle — Người Que Nét Chì Trên Giấy Kraft

Dành cho khi: kể chuyện triết lý, bài học cuộc sống, podcast giấu mặt ấm áp và gần gũi.

## Cách dùng
> Lệnh chạy từ thư mục gốc repo AGS Video Editing (hai cấp trên thư mục chứa file này) bằng Python của venv: macOS `./venv/bin/python`, Windows `venv\Scripts\python`.
```bash
python scripts/ags_voice_to_doodle.py <duong_dan_audio.mp3> [--out <video_xuat.mp4>] [--model base]
```
Mặc định xuất `<tên>_doodle.mp4`.

## Chức năng
1. Nền giấy kraft nâu, mặt trời và tảng đá nét chì, khung 1080x1920.
2. Người que đổi thế xen kẽ (ngồi thiền / đứng suy tư) theo từng cụm lời ≤ 40 ký tự / ≤ 3.5 giây, khớp đúng thời gian giọng nói.
3. Phụ đề Serif tối đa 3 dòng, đặt giữa mặt trời và nhân vật (trong vùng an toàn 9:16); âm lượng -14 LUFS, AAC 48 kHz.

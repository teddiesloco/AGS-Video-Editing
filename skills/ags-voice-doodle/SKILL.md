---
name: ags-voice-doodle
description: "Biến file ghi âm thành video người que nét chì: hoạt hình doodle mộc mạc trên nền giấy kraft nâu cổ điển."
---

# /ags-voice-doodle — Hoạt Hình Người Que Nét Chì Nền Giấy

Dành cho khi: Kể chuyện triết lý, bài học cuộc sống, podcast giấu mặt ấm áp và gần gũi.

## Cách dùng:
```bash
python scripts/voice_to_doodle.py <duong_dan_audio.mp3> [--out <video_xuat.mp4>]
```

## Chức năng tự động:
1. Tạo canvas nền giấy kraft nâu ấm chuẩn 1080x1920.
2. Vẽ tự động các thế người que nét chì (ngồi thiền, suy tư, ngắm mặt trời) đồng bộ theo từng câu kể.
3. Chèn phụ đề câu nói và chuẩn hóa âm thanh -14 LUFS.

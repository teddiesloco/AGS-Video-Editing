---
name: ags-voice-kinetic
description: "Biến file ghi âm thành video hoạt hình chữ 2D: đồng bộ từ khóa, chữ bật nảy (kinetic zoom) trên nền card hiện đại."
---

# /ags-voice-kinetic — Hoạt Hình Chữ 2D Từ Giọng Nói

Dành cho khi: Bạn có file ghi âm hoặc podcast ngắn, muốn biến thành video trực quan mà không cần quay mặt.

## Cách dùng:
```bash
python scripts/voice_to_kinetic.py <duong_dan_audio.mp3> [--out <video_xuat.mp4>]
```

## Chức năng tự động:
1. Nhận diện giọng nói và chia câu ngắn theo nhịp ngắt 2–3 giây.
2. Vẽ card đồ họa 2D hiện đại, tạo animation chữ nhảy theo từng câu nói.
3. Xuất video MP4 1080x1920 chuẩn Reels/TikTok kèm âm thanh -14 LUFS.

---
name: ags-edit-az
description: "Edit video từ A-Z: tự động cắt bỏ đoạn im lặng, lọc từ vấp/từ thừa ('ờ, à'), tạo jump-cut dynamic và xuất bản dọc 9:16 + ngang 16:9."
---

# /ags-edit-az — Edit Video Từ A Đến Z

Dành cho khi: Bạn vừa quay xong video thô một đúp (one-take) và muốn có ngay video hoàn chỉnh sạch sẽ.

## Cách dùng:
```bash
python scripts/cut_silence.py <duong_dan_video> [--out <video_xuat>]
```

## Chức năng tự động:
1. Trích xuất âm thanh 16kHz và dùng Faster-Whisper nhận diện từng từ kèm timestamp.
2. Tự động cắt bỏ các khoảng ngắt nghỉ $> 0.4s$ và lọc các từ đệm ("ờ", "à", "ừm", "hả").
3. Nối các đoạn liền mạch bằng FFmpeg keyframe-accurate mà không làm vỡ tiếng.

---
name: ags-edit-editorial
description: "Sub phong cách Tạp chí cao cấp: chữ Serif thanh mảnh, tự động dời sub né khuôn mặt và cân âm lượng chuẩn broadcast -14 LUFS."
---

# /ags-edit-editorial — Phụ Đề Tạp Chí Sang Trọng & Cân Âm -14 LUFS

Dành cho khi: Video chia sẻ chuyên gia, phong cách sống, bất động sản cao cấp cần nét chữ tinh tế và âm thanh chuẩn.

## Cách dùng:
```bash
python scripts/editorial_sub.py <duong_dan_video> [--out <video_xuat>]
```

## Chức năng tự động:
1. Whisper bóc tách lời thoại tiếng Việt chính xác đủ dấu.
2. Sinh file phụ đề `.ASS` font Serif thanh thoát, căn tỷ lệ vàng.
3. Tự động áp bộ lọc chuẩn hóa âm lượng phát thanh: `loudnorm=I=-14:LRA=11:TP=-1.5`.

---
name: ags-edit-hook
description: "Chữ chìm sau người & Hook viral: AI tách người khỏi nền, đặt chữ tiêu đề to nổi bật chìm sau lưng và hiệu ứng âm thanh SFX."
---

# /ags-edit-hook — Chữ Chìm Sau Người & Hook Viral

Dành cho khi: Video đã cắt sẵn nhưng mở đầu đơn điệu, cần câu hook giật tít mạnh mẽ để giữ chân người xem trong 3 giây đầu.

## Cách dùng:
```bash
python scripts/text_behind_person.py <duong_dan_video> --text "CÂU HOOK NỔI BẬT" [--duration 5.0]
```

## Chức năng tự động:
1. Nhận diện và tách lớp người bằng mô hình Human Matting (Rembg/U2Net).
2. Tạo chữ vàng/trắng tương phản cao đặt tại vị trí 28% đỉnh màn hình (sau đầu/ngực).
3. Ghép sandwich 3-layer trong FFmpeg: Video gốc -> Chữ Hook -> Lớp người đè lên trên.

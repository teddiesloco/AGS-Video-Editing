---
name: ags-edit-hook
description: "AGS (Agent Space) — chữ chìm sau người: tách người khỏi nền bằng rembg (u2net_human_seg), đặt câu hook vàng viền đen sau lưng người nói trong vài giây đầu video."
---

# /ags-edit-hook — Chữ Chìm Sau Người

Dành cho khi: video đã cắt sẵn nhưng mở đầu đơn điệu, cần câu hook nổi bật để giữ chân người xem 3 giây đầu.

## Cách dùng
> Lệnh chạy từ thư mục gốc repo AGS Video Editing (hai cấp trên thư mục chứa file này) bằng Python của venv: macOS `./venv/bin/python`, Windows `venv\Scripts\python`.
```bash
python scripts/ags_text_behind_person.py <duong_dan_video> --text "CÂU HOOK NỔI BẬT" [--duration 5.0] [--out <video_xuat.mp4>]
```
Mặc định xuất `<tên>_hook.mp4`.

## Chức năng
1. Tách lớp người từng khung hình bằng rembg `u2net_human_seg` (lần chạy đầu tự tải model ~170 MB).
2. Chữ vàng viền đen, tự co cỡ cho vừa 90% bề ngang (tối đa 2 dòng), đặt ở 28% chiều cao (ngang đầu/ngực).
3. Ghép 3 lớp trong FFmpeg: video gốc → chữ hook → lớp người đè lên trên, chỉ trong `--duration` giây đầu.
4. Tự đọc metadata xoay của video quay điện thoại.

Lưu ý: tách nền chạy bằng CPU nên chậm (vài giây cho mỗi khung hình 1080x1920; 3 giây video 30fps = 90 khung) — nên để `--duration` 2–3 giây. Âm thanh giữ nguyên bản gốc.

---
name: ags-edit-hook
description: "AGS (Agent Space) — chữ chìm sau người (text-behind-person): tách người khỏi nền bằng rembg, đặt câu hook vàng viền đen sau lưng người nói, hiện đủ độ đậm ngay từ khung đầu tiên, nằm trong vùng an toàn 9:16. Dùng khi video đã cắt xong nhưng mở đầu đơn điệu, cần câu hook giữ chân người xem trong 3 giây đầu."
compatibility: "Cần Python 3.10+, FFmpeg và thư viện trong requirements.txt; lần đầu tải model rembg u2net_human_seg (~170 MB, cần Internet)."
license: "PolyForm Strict 1.0.0 — xem LICENSE"
---

# /ags-edit-hook — Chữ Chìm Sau Người

> Lệnh chạy từ thư mục gốc repo AGS Video Editing (hai cấp trên file này) — hoặc từ thư mục của skill nếu dùng bản zip
> (đã kèm `scripts/`, `harness/`) — bằng Python có đủ thư viện (venv của repo: macOS `./venv/bin/python`, Windows `venv\Scripts\python`).

```bash
python scripts/ags_text_behind_person.py <video> --text "CÂU HOOK NỔI BẬT" [--duration 3] [--out <video_xuat.mp4>]
```
Mặc định xuất `<tên>_hook.mp4`.

## Chức năng
1. Tách lớp người từng khung bằng rembg `u2net_human_seg`.
2. Chữ vàng viền đen, tối đa 2 dòng, tự co cỡ cho vừa bề ngang vùng an toàn (`ags_common.safe_box`), đặt ngang
   đầu/ngực (~28% chiều cao); chữ chuẩn hoá Unicode NFC nên dấu tiếng Việt không bị tách.
3. Ghép 3 lớp trong FFmpeg: video gốc → chữ hook → lớp người đè lên, trong `--duration` giây đầu; chữ hiện đủ độ đậm
   từ khung 0 (không mờ dần) — TikTok khuyên đưa thông điệp chính vào 3 giây đầu.
4. Tự đọc metadata xoay của video quay điện thoại. Âm thanh giữ nguyên bản gốc.

Tách nền chạy bằng CPU nên chậm (khoảng 1 phút cho 2 giây video 1080x1920 trên máy thử) — để `--duration` 2–3 giây.

## Kiểm định (bắt buộc)
```bash
python harness/ags_anti_slop_guard.py <video_xuat.mp4> --contact-sheet <video_xuat>_sheet.jpg
```
Ô `#0 (khung 0)` của contact sheet phải thấy rõ câu hook. Exit `0` đạt · `2` cảnh báo · `1` lỗi.
Âm lượng giữ như bản gốc nên có thể bị cảnh báo LUFS — chạy thêm `/ags-edit-editorial` để chuẩn -14 LUFS.
Vòng soát: `harness/QUY-TRINH-KIEM-DINH.md`.

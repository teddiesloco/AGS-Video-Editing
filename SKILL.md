---
name: ags-video-editing
description: "Bộ 5 Skill Edit Video Tự Động độc quyền AgentSea: Cắt thô lọc từ thừa (/ags-edit-az), Chữ chìm sau người (/ags-edit-hook), Sub tạp chí sang trọng (/ags-edit-editorial), Hoạt hình chữ 2D (/ags-voice-kinetic), và Người que nét chì (/ags-voice-doodle). Hỗ trợ cả macOS và Windows."
---

# AGS-Video-Editing — Bộ Skill Edit Video Tự Động Đa Năng

Bộ công cụ tự động hóa hậu kỳ video hoàn chỉnh cho nhà sáng tạo nội dung và doanh nghiệp:

## Danh Sách 5 Skill:

1. **/ags-edit-az** `<video>`:
   - Tự động cắt bỏ khoảng im lặng & từ đệm vấp ("ờ, à, ừm").
   - Xuất bản dọc 9:16 (TikTok/Reels/Shorts) và ngang 16:9 (YouTube).

2. **/ags-edit-hook** `<video> --text "<CÂU HOOK>"`:
   - Tách người khỏi nền bằng AI Human Matting.
   - Đặt chữ tiêu đề to nổi bật chìm sau lưng người nói.

3. **/ags-edit-editorial** `<video>`:
   - Sub chuẩn tạp chí nét Serif thanh mảnh, tự né khuôn mặt.
   - Chuẩn hóa âm thanh đạt chuẩn phát thanh `-14 LUFS`.

4. **/ags-voice-kinetic** `<audio.mp3>`:
   - Biến file ghi âm giọng nói thành video 2D chữ nhảy hiện đại.

5. **/ags-voice-doodle** `<audio.mp3>`:
   - Biến file ghi âm thành video hoạt hình người que nét chì trên nền giấy kraft nâu.


---

## 🛡️ Anti-AI-Slop Quality Gate:
Chạy kiểm định chất lượng bắt buộc sau mỗi lần render video:
```bash
python harness/anti_slop_guard.py <duong_dan_video>
```
Tự động bắt lỗi: Lệch âm hình (A/V sync), phụ đề ảo giác/lặp từ, âm lượng không đạt chuẩn broadcast -14 LUFS.
---

## Cài đặt nhanh (1-Click):
- **Trên Mac:** Mở Terminal chạy `./CAI-DAT-MAC.sh`
- **Trên Windows:** Bấm đúp chạy `CAI-DAT-WIN.bat`

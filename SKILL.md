---
name: ags-video-editing
description: "AGS (Agent Space) — bộ 6 skill edit video tự động (macOS & Windows): cắt khoảng lặng & từ đệm (/ags-edit-az), chữ chìm sau người (/ags-edit-hook), phụ đề tạp chí -14 LUFS (/ags-edit-editorial), ghi âm thành chữ 2D (/ags-voice-kinetic), ghi âm thành người que nét chì (/ags-voice-doodle), dựng video Bất Động Sản + draft CapCut thử nghiệm (/ags-edit-bds). Có harness Anti-AI-Slop và MCP server."
---

# AGS Video Editing — Bộ Skill Edit Video Tự Động của AGS (Agent Space)

Mọi lệnh chạy từ thư mục gốc repo. Python: macOS `./venv/bin/python`, Windows `venv\Scripts\python` (sau khi chạy installer).

## 6 Skill
1. **/ags-edit-az** — `python scripts/ags_cut_silence.py <video> [--min-silence 0.4]`
   Bỏ khoảng lặng dài và từ đệm ("ờ, à, ừm"), cắt chính xác từng khung hình, chuẩn -14 LUFS, giữ khung hình gốc.
2. **/ags-edit-hook** — `python scripts/ags_text_behind_person.py <video> --text "<CÂU HOOK>" [--duration 5]`
   Tách người bằng rembg, đặt câu hook vàng viền đen chìm sau lưng người nói.
3. **/ags-edit-editorial** — `python scripts/ags_editorial_sub.py <video>`
   Phụ đề Serif phong cách tạp chí theo đúng kích thước video, chuẩn âm lượng -14 LUFS.
4. **/ags-voice-kinetic** — `python scripts/ags_voice_to_kinetic.py <audio>`
   File ghi âm → video chữ 2D bật nảy 1080x1920, khớp thời gian giọng nói.
5. **/ags-voice-doodle** — `python scripts/ags_voice_to_doodle.py <audio>`
   File ghi âm → video người que nét chì trên giấy kraft 1080x1920.
6. **/ags-edit-bds** — `python scripts/ags_bds_cli.py <draft|render|parcel|subdivision|ticker|beats|prompt>`
   Video Bất Động Sản theo 6 bước (phân loại tư liệu → công thức → asset → draft CapCut thử nghiệm hoặc render MP4 → kiểm định → bàn giao). Chi tiết: `skills/ags-edit-bds/SKILL.md`.

## Quy tắc bắt buộc
- Gọi script có sẵn; không tự viết lệnh FFmpeg dài.
- Sau mỗi lần render: `python harness/ags_anti_slop_guard.py <video>` — exit `0` mới bàn giao; exit `2` phải đọc và xử lý cảnh báo; exit `1` là lỗi.
- Báo kết quả ngắn gọn: `[Video đầu ra] -> [Thời lượng] -> [LUFS] -> [Kết quả guard]`.

## MCP
`mcp/ags_mcp_server.py` (stdio, cần `requirements-mcp.txt`): tool `cut_silence`, `text_behind_person`, `editorial_sub`, `voice_to_kinetic`, `voice_to_doodle`, `bds_draft`, `bds_render`, `anti_slop_guard`.

## Cài đặt
- macOS: `./CAI-DAT-MAC.sh` · Windows: `CAI-DAT-WIN.bat`

Giấy phép: AGS Personal Use License — chỉ dùng cá nhân, phi thương mại (xem `LICENSE`).

---
name: ags-video-editing
description: "AGS (Agent Space) — bộ 8 skill edit video tự động bằng Python + FFmpeg (macOS, Windows, Linux): cắt lặng & từ đệm, chữ chìm sau người, phụ đề tạp chí/karaoke -14 LUFS, ghi âm thành chữ 2D hoặc người que, reframe ngang → dọc 9:16 bám mặt, video dài → nhiều short, video Bất Động Sản; kèm harness kiểm định có contact sheet và MCP server. Dùng khi người dùng muốn dựng, cắt, làm phụ đề, làm short/reels hoặc kiểm tra chất lượng video."
compatibility: "Cần Python 3.10+, FFmpeg và thư viện trong requirements.txt; lần đầu tải model (cần Internet)."
license: "PolyForm Strict 1.0.0 — xem LICENSE"
---

# AGS Video Editing — Bộ Skill Edit Video Tự Động của AGS (Agent Space)

**Đọc `AGENTS.md` (cùng thư mục) trước khi chạy:** quy tắc bắt buộc, bảng việc → lệnh, vòng kiểm định.
Mọi lệnh chạy từ thư mục gốc repo bằng Python của venv (macOS `./venv/bin/python`, Windows `venv\Scripts\python`).

## 8 skill (chi tiết trong `skills/<tên>/SKILL.md`)
1. **/ags-edit-az** — `python scripts/ags_cut_silence.py <video>` — bỏ khoảng lặng (đo độ to) và từ đệm, cắt chính xác
   từng khung, crossfade tiếng, -14 LUFS.
2. **/ags-edit-hook** — `python scripts/ags_text_behind_person.py <video> --text "<HOOK>"` — câu hook chìm sau lưng người
   nói, hiện ngay khung 0.
3. **/ags-edit-editorial** — `python scripts/ags_editorial_sub.py <video> [--style karaoke]` — phụ đề tạp chí hoặc karaoke
   tô màu từng từ, trong vùng an toàn 9:16, -14 LUFS.
4. **/ags-voice-kinetic** — `python scripts/ags_voice_to_kinetic.py <audio>` — ghi âm → video chữ 2D bật nảy 1080x1920.
5. **/ags-voice-doodle** — `python scripts/ags_voice_to_doodle.py <audio>` — ghi âm → người que nét chì trên giấy kraft.
6. **/ags-reframe** — `python scripts/ags_reframe.py <video>` — video ngang → dọc 9:16, khung bám khuôn mặt.
7. **/ags-clip-shorts** — `python scripts/ags_clip_shorts.py transcript|cut ...` — video dài → nhiều short có hook,
   phụ đề karaoke, bám mặt.
8. **/ags-edit-bds** — `python scripts/ags_bds_cli.py <draft|render|parcel|subdivision|ticker|beats|prompt>` — video
   Bất Động Sản: asset GIS, cắt theo beat (tự dò từ nhạc), wipe trước/sau, nhạc tự nhỏ dưới giọng đọc, draft CapCut thử nghiệm.

## Kiểm định (bắt buộc sau mỗi lần render)
`python harness/ags_anti_slop_guard.py <video> --contact-sheet <video>_sheet.jpg` → exit `0` đạt · `2` cảnh báo · `1` lỗi;
mở contact sheet soát theo `harness/QUY-TRINH-KIEM-DINH.md`.

## MCP · Cài đặt · Giấy phép
- MCP: `mcp/ags_mcp_server.py` (stdio, cần `requirements-mcp.txt`) — danh sách tool trong `AGENTS.md`.
- Cài đặt: macOS `./CAI-DAT-MAC.sh` · Windows `CAI-DAT-WIN.bat` · hướng dẫn đầy đủ `HUONG-DAN-SU-DUNG.md`.
- Giấy phép: PolyForm Strict 1.0.0 — chỉ dùng phi thương mại, không phân phối lại, không sửa đổi (`LICENSE`, `LICENSE-VI.md`).

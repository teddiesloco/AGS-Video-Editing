# ⚡ AGS Video Editing — Quy tắc cho Claude Code & Claude Desktop

Claude Code: skill gốc `SKILL.md` + 8 skill trong `skills/`; MCP server `ags` khai báo sẵn trong `.mcp.json`.
Claude Desktop: khai báo MCP theo HUONG-DAN-SU-DUNG.md, Phần 3.

Quy tắc bắt buộc, bảng việc → lệnh và danh sách tool: [`AGENTS.md`](../AGENTS.md). Tóm tắt:
1. Gọi script trong `scripts/` (Python của venv) hoặc tool MCP (`cut_silence`, `editorial_sub`, `reframe`,
   `clip_shorts_transcript`, `clip_shorts_cut`, `bds_render`, …); đọc `exit_code`, `stderr_tail` trong kết quả.
2. Sau mỗi lần render: `python harness/ags_anti_slop_guard.py <out.mp4> --contact-sheet <out>_sheet.jpg` (hoặc tool
   `anti_slop_guard` với `contact_sheet`), mở ảnh soát theo `harness/QUY-TRINH-KIEM-DINH.md`.
   Exit `0` mới bàn giao; `2` phải xử lý cảnh báo; `1` là lỗi.

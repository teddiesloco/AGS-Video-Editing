# ⚡ AGS Video Editing — Quy tắc cho Claude Code & Claude Desktop

**Claude Code:** thả thư mục skill `ags-video-editing/` (giải nén từ `ags-video-editing.zip`) vào `~/.claude/skills/`
(toàn máy) hoặc `<dự án>/.claude/skills/` (theo dự án), rồi nói việc cần làm. Agent đọc `SKILL.md`, tự chạy
`scripts/ags_setup.py --check` và cài môi trường khi cần (xin đồng ý một lần). Không cần `claude mcp add` — script chạy qua terminal;
MCP là tuỳ chọn: `python scripts/ags_setup.py --register-claude-code` đăng ký server `ags` ở phạm vi user.
**Claude Desktop:** khai báo MCP bằng khối do `python scripts/ags_setup.py --print-mcp` in ra (HUONG-DAN-SU-DUNG.md, Phần 3).
**claude.ai (web):** không render được — dùng `ags-video-editing-web.zip` (HUONG-DAN-SU-DUNG.md, Phần 4).

Quy tắc bắt buộc, bảng việc → lệnh và danh sách tool: [`AGENTS.md`](../AGENTS.md). Tóm tắt:
1. Gọi script trong `scripts/` bằng Python của venv trong skill (đường dẫn tuyệt đối, đặt trong ngoặc kép) hoặc tool MCP
   (`cut_silence`, `editorial_sub`, `reframe`, `clip_shorts_transcript`, `clip_shorts_cut`, `bds_render`, `tts_synthesize`,
   `sfx_mix`, …); đọc `exit_code`, `stderr_tail` trong kết quả.
2. Sau mỗi lần render: `python harness/ags_anti_slop_guard.py <out.mp4> --contact-sheet <out>_sheet.jpg` (hoặc tool
   `anti_slop_guard` với `contact_sheet`), mở ảnh soát theo `harness/QUY-TRINH-KIEM-DINH.md`.
   Exit `0` mới bàn giao; `2` phải xử lý cảnh báo; `1` là lỗi.

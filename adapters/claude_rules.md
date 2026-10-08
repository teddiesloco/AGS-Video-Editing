# ⚡ AGS Video Editing — Quy tắc cho Claude Code & Claude Desktop

Bộ AGS Video Editing của AGS (Agent Space). Lệnh chạy từ thư mục gốc repo bằng Python của venv (`./venv/bin/python` trên macOS, `venv\Scripts\python` trên Windows).

1. **Skill → script:**
   - `/ags-edit-az <video>` → `python scripts/ags_cut_silence.py <video>`
   - `/ags-edit-hook <video> --text "<HOOK>"` → `python scripts/ags_text_behind_person.py <video> --text "<HOOK>"`
   - `/ags-edit-editorial <video>` → `python scripts/ags_editorial_sub.py <video>`
   - `/ags-voice-kinetic <audio>` → `python scripts/ags_voice_to_kinetic.py <audio>`
   - `/ags-voice-doodle <audio>` → `python scripts/ags_voice_to_doodle.py <audio>`
   - `/ags-edit-bds ...` → `python scripts/ags_bds_cli.py <draft|render|parcel|subdivision|ticker|beats|prompt>` theo 6 bước trong `skills/ags-edit-bds/SKILL.md`

2. **MCP (Claude Desktop / Claude Code):** nếu đã khai báo server `ags` (HUONG-DAN-SU-DUNG.md, Phần 3), gọi tool `cut_silence`, `text_behind_person`, `editorial_sub`, `voice_to_kinetic`, `voice_to_doodle`, `bds_draft`, `bds_render`, `anti_slop_guard`; đọc `exit_code` và `stderr_tail` trong kết quả.

3. **Quality gate:** sau mỗi lần render chạy `python harness/ags_anti_slop_guard.py <out.mp4>` (hoặc tool `anti_slop_guard`). Exit `0` mới bàn giao; `2` phải xử lý cảnh báo; `1` là lỗi.

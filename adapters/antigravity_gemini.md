# 🛡️ AGS Harness cho Google Antigravity & Gemini

**Antigravity:** giải nén `ags-video-editing.zip` thành thư mục `ags-video-editing/` trong `.agents/skills/` của workspace
(hoặc `~/.gemini/config/skills/` cho IDE/2.0, `~/.gemini/antigravity-cli/skills/` cho CLI — HUONG-DAN-SU-DUNG.md, Phần 2.3),
rồi nói việc cần làm; agent đọc `SKILL.md`, tự kiểm tra và cài môi trường. Antigravity cũng tự nạp [`AGENTS.md`](../AGENTS.md)
ở gốc workspace. **Gemini CLI:** `gemini extensions link <thư mục skill>` nạp `GEMINI.md`; chạy
`python scripts/ags_setup.py` trước (nó cập nhật interpreter trong `gemini-extension.json` theo hệ điều hành).

Quy tắc đầy đủ, bảng việc → lệnh và danh sách tool MCP nằm trong `AGENTS.md` — file này chỉ nhắc 3 điều Gemini hay làm sai:

1. **Không tự viết lệnh FFmpeg dài.** Gọi script trong `scripts/` bằng Python của venv trong skill (đường dẫn tuyệt đối,
   đặt trong ngoặc kép) hoặc tool của MCP server `ags` (HUONG-DAN-SU-DUNG.md, Phần 3).
2. **Không kể lể từng bước.** Chạy xong báo: `[Video đầu ra] -> [Thời lượng] -> [LUFS] -> [Kết quả guard] -> [Contact sheet]`.
3. **Bắt buộc kiểm định trước khi báo xong:**
   ```bash
   python harness/ags_anti_slop_guard.py "video_output.mp4" --contact-sheet "video_output_sheet.jpg"
   ```
   Exit `0` đạt → bàn giao · `2` cảnh báo → đọc từng dòng, sửa hoặc báo rõ · `1` lỗi → không bàn giao.
   Mở ảnh contact sheet và soát theo `harness/QUY-TRINH-KIEM-DINH.md` (tối đa 3 vòng sửa).

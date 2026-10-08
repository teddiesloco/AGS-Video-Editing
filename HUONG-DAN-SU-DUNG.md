# 📖 HƯỚNG DẪN SỬ DỤNG — AGS VIDEO EDITING (AGS — Agent Space)

Hướng dẫn dùng bộ 6 skill edit video của AGS (Agent Space) trên **coding agent** (Claude Code, OpenAI Codex, Google Antigravity / Gemini, Cursor), qua **MCP server**, và trên **giao diện web** (claude.ai, chatgpt.com).

---

## PHẦN 1: CÀI ĐẶT

```bash
git clone https://github.com/teddiesloco/AGS-Video-Editing.git
cd AGS-Video-Editing
./CAI-DAT-MAC.sh          # macOS
CAI-DAT-WIN.bat           # Windows (bấm đúp hoặc chạy trong cmd)
```
- Cần Python 3.10+ và FFmpeg (installer macOS tự cài qua Homebrew; Windows thử cài FFmpeg qua winget).
- Installer tạo môi trường ảo `venv/`. Python dùng cho mọi lệnh: macOS `./venv/bin/python`, Windows `venv\Scripts\python.exe`.
- Lần chạy đầu: faster-whisper tự tải model Whisper (~150 MB với `base`), rembg tự tải model tách người (~170 MB) — cần Internet.

---

## PHẦN 2: DÙNG VỚI CODING AGENTS (CHẠY SCRIPT TRỰC TIẾP)

Bảng lệnh (chạy từ thư mục gốc repo):

| Skill | Lệnh |
|---|---|
| `/ags-edit-az` | `python scripts/ags_cut_silence.py <video> [--min-silence 0.4]` |
| `/ags-edit-hook` | `python scripts/ags_text_behind_person.py <video> --text "<HOOK>" [--duration 5]` |
| `/ags-edit-editorial` | `python scripts/ags_editorial_sub.py <video>` |
| `/ags-voice-kinetic` | `python scripts/ags_voice_to_kinetic.py <audio>` |
| `/ags-voice-doodle` | `python scripts/ags_voice_to_doodle.py <audio>` |
| `/ags-edit-bds` | `python scripts/ags_bds_cli.py <draft\|render\|parcel\|subdivision\|ticker\|beats\|prompt> ...` |
| Kiểm định | `python harness/ags_anti_slop_guard.py <video>` → exit `0` đạt · `2` cảnh báo · `1` lỗi |

### 1. Claude Code
- Mở thư mục repo trong Claude Code rồi chat tự nhiên:
  > *"Dùng skill ags-edit-az cắt video ~/Desktop/clip.mp4, sau đó chạy anti slop guard."*
- Muốn gọi bằng slash command ở mọi dự án (`/ags-video-editing`, `/ags-edit-az`, …), liên kết skill vào thư mục skill cá nhân của Claude Code:
  ```bash
  # macOS — chạy trong thư mục repo
  mkdir -p ~/.claude/skills
  ln -s "$PWD" ~/.claude/skills/ags-video-editing
  for s in skills/*; do ln -s "$PWD/$s" ~/.claude/skills/"$(basename "$s")"; done
  ```
  ```bat
  :: Windows (cmd) — chạy trong thư mục repo
  mkdir "%USERPROFILE%\.claude\skills"
  mklink /J "%USERPROFILE%\.claude\skills\ags-video-editing" "%CD%"
  for /D %s in (skills\*) do mklink /J "%USERPROFILE%\.claude\skills\%~nxs" "%CD%\%s"
  ```
  Mỗi skill con ghi lệnh tính từ thư mục gốc repo (hai cấp trên thư mục của skill đó).

### 2. OpenAI Codex
- Mở thư mục repo bằng Codex và chat: *"Đọc SKILL.md rồi chạy skill ags-edit-editorial cho video.mp4, kiểm định bằng anti slop guard."*
- Hoặc dùng MCP (Phần 3) để Codex gọi tool trực tiếp.

### 3. Google Antigravity / Gemini
- Mở repo làm workspace. Bộ quy tắc chống lỗi cho Gemini nằm ở `adapters/antigravity_gemini.md` (gọi script có sẵn, không tự viết FFmpeg, bắt buộc chạy guard).
- Chat: *"Theo adapters/antigravity_gemini.md, chạy ags-edit-az cho video1.mp4 rồi chạy harness kiểm định."*

### 4. Cursor / Windsurf
- Mở thư mục repo, mở Chat/Composer và chat: *"@SKILL.md chạy ags_cut_silence.py cho clip_raw.mp4 bằng venv của repo."*
- Hoặc cấu hình MCP (Phần 3).

---

## PHẦN 3: MCP SERVER

`mcp/ags_mcp_server.py` là MCP server (stdio, FastMCP). Mỗi tool gọi đúng script trong repo và trả về JSON: `output` (đường dẫn kết quả), `exit_code`, `stderr_tail`, `stdout_tail`.

| Tool | Tham số chính |
|---|---|
| `cut_silence` | `input_path`, `output_path?`, `model?`, `min_silence?` |
| `text_behind_person` | `input_path`, `text`, `output_path?`, `duration?` |
| `editorial_sub` | `input_path`, `output_path?`, `model?` |
| `voice_to_kinetic` | `audio_path`, `output_path?`, `model?` |
| `voice_to_doodle` | `audio_path`, `output_path?`, `model?` |
| `bds_draft` | `name`, `clips[]`, `output_dir` hoặc `capcut=true`, `seconds?`, `bpm?`, `beat_step?`, `title?`, `music?` |
| `bds_render` | `images[]`, `output_path`, `seconds?`, `bpm?`, `beat_step?`, `music?` |
| `anti_slop_guard` | `video_path` |

**Bước 1 — cài thư viện MCP (tuỳ chọn):**
```bash
./venv/bin/pip install -r requirements-mcp.txt          # macOS
venv\Scripts\pip install -r requirements-mcp.txt        # Windows
```
**Bước 2 — khai báo server.** Thay `/DUONG/DAN/AGS-Video-Editing` bằng đường dẫn tuyệt đối của repo. Windows: `command` là `C:/DUONG/DAN/AGS-Video-Editing/venv/Scripts/python.exe` (dùng `/` hoặc `\\` trong JSON).

Xử lý video mất vài phút: client nào có giới hạn thời gian gọi tool thì nâng lên (ví dụ dưới đây).

### Claude Code
```bash
claude mcp add --transport stdio ags -- /DUONG/DAN/AGS-Video-Editing/venv/bin/python /DUONG/DAN/AGS-Video-Editing/mcp/ags_mcp_server.py
```
Hoặc chia sẻ theo dự án bằng file `.mcp.json` ở gốc dự án:
```json
{
  "mcpServers": {
    "ags": {
      "command": "/DUONG/DAN/AGS-Video-Editing/venv/bin/python",
      "args": ["/DUONG/DAN/AGS-Video-Editing/mcp/ags_mcp_server.py"]
    }
  }
}
```

### Claude Desktop
File `claude_desktop_config.json` — macOS: `~/Library/Application Support/Claude/`, Windows: `%APPDATA%\Claude\`:
```json
{
  "mcpServers": {
    "ags": {
      "command": "/DUONG/DAN/AGS-Video-Editing/venv/bin/python",
      "args": ["/DUONG/DAN/AGS-Video-Editing/mcp/ags_mcp_server.py"]
    }
  }
}
```

### OpenAI Codex
File `~/.codex/config.toml` (mặc định Codex chỉ chờ tool 60 giây):
```toml
[mcp_servers.ags]
command = "/DUONG/DAN/AGS-Video-Editing/venv/bin/python"
args = ["/DUONG/DAN/AGS-Video-Editing/mcp/ags_mcp_server.py"]
tool_timeout_sec = 1800
```

### Google Antigravity / Gemini CLI
Antigravity: `~/.gemini/config/mcp_config.json` (toàn máy) hoặc `.agents/mcp_config.json` (theo workspace); trong Antigravity IDE mở **… → MCP Servers → Manage MCP Servers → View raw config**:
```json
{
  "mcpServers": {
    "ags": {
      "command": "/DUONG/DAN/AGS-Video-Editing/venv/bin/python",
      "args": ["/DUONG/DAN/AGS-Video-Editing/mcp/ags_mcp_server.py"]
    }
  }
}
```
Gemini CLI: thêm cùng khối `mcpServers` vào `~/.gemini/settings.json` (hoặc `.gemini/settings.json` của dự án), có thể thêm `"timeout": 1800000` (mili-giây).

### Cursor
File `.cursor/mcp.json` (theo dự án) hoặc `~/.cursor/mcp.json` (toàn máy):
```json
{
  "mcpServers": {
    "ags": {
      "command": "/DUONG/DAN/AGS-Video-Editing/venv/bin/python",
      "args": ["/DUONG/DAN/AGS-Video-Editing/mcp/ags_mcp_server.py"]
    }
  }
}
```

---

## PHẦN 4: DÙNG TRÊN GIAO DIỆN WEB (CLAUDE.AI & CHATGPT.COM)

Web chat không chạy được script trên máy bạn — ở đây AI đóng vai **đạo diễn / biên tập kịch bản**: bóc băng, gợi ý câu hook, viết phụ đề, lên timeline cắt ghép.

### Claude.ai
1. Tạo **Project** mới (ví dụ *Video Editor Pro*).
2. Tải `SKILL.md`, `README.md` và `skills/*/SKILL.md` của repo vào **Project Knowledge**.
3. Dán vào **Custom Instructions**:
   ```text
   Bạn là Chuyên gia Đạo diễn & Biên tập Video của AGS (Agent Space) — bộ AGS Video Editing.
   Khi tôi tải lên video, file ghi âm hoặc kịch bản:
   1. Nghe/đọc và bóc băng lời thoại chính xác, đủ dấu tiếng Việt.
   2. Đánh dấu các từ đệm, nói lắp, từ vấp ("ờ", "à", "ừm") và khoảng lặng cần cắt.
   3. Gợi ý câu hook ngắn 3-5 từ để đặt chìm sau lưng người nói.
   4. Viết kịch bản cắt ghép theo từng giây và lệnh AGS tương ứng để tôi chạy trên máy.
   ```

### ChatGPT.com (Custom GPT)
1. **Explore GPTs → Create a GPT** (hoặc Custom Instructions cá nhân).
2. Dán nội dung `adapters/chatgpt_custom_instructions.md` vào ô **Instructions**.
3. Chat: *"Tôi vừa quay video 45 giây, nội dung như sau… hãy đánh dấu đoạn cần cắt và viết 1 câu hook chữ chìm sau lưng."*

---

## 📊 BẢNG TRA CỨU NHANH

| Bạn muốn | Chat với AI | Công cụ chạy |
|---|---|---|
| Cắt đoạn nói vấp, im lặng | *"Dùng ags-edit-az cắt video quay thô này"* | `ags_cut_silence.py` (faster-whisper + FFmpeg) |
| Chữ chìm sau người | *"Tách nền và đặt câu '90 NGÀY KIẾM 1 TỶ' sau lưng"* | `ags_text_behind_person.py` (rembg + ghép 3 lớp) |
| Phụ đề tạp chí, cân âm | *"Làm sub tạp chí và cân âm -14 LUFS"* | `ags_editorial_sub.py` (libass + loudnorm) |
| Ghi âm → chữ 2D | *"Biến file ghi âm này thành video chữ 2D"* | `ags_voice_to_kinetic.py` |
| Ghi âm → người que | *"Kể chuyện này bằng người que trên giấy kraft"* | `ags_voice_to_doodle.py` |
| Video Bất Động Sản | *"Dựng video đất nền từ ảnh vệ tinh + sơ đồ phân lô"* | `ags_bds_cli.py` (xem `skills/ags-edit-bds/SKILL.md`) |
| Kiểm tra chất lượng | *"Chạy kiểm định chống AI Slop cho video vừa xuất"* | `harness/ags_anti_slop_guard.py` |

---

## ⚖️ GIẤY PHÉP
AGS Video Editing dùng **AGS Personal Use License** (mã nguồn xem được): chỉ được tải, cài và chạy cho mục đích cá nhân, phi thương mại. Không phân phối lại / đăng lại / đóng gói lại, không bán, không dùng để làm dịch vụ edit thu phí hay đưa vào khoá học, sản phẩm trả phí, không công bố bản chỉnh sửa. Cấp phép thương mại: liên hệ Agent Space (AGS). Chi tiết: [LICENSE](LICENSE) · thành phần bên thứ ba: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

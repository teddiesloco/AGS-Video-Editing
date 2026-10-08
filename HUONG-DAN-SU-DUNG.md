# 📖 HƯỚNG DẪN SỬ DỤNG — AGS VIDEO EDITING (AGS — Agent Space)

Hướng dẫn dùng bộ 8 skill edit video của AGS (Agent Space) trên **coding agent** (Claude Code, OpenAI Codex, Google
Antigravity, Gemini CLI, Cursor), qua **MCP server**, và trên **giao diện web** (claude.ai, chatgpt.com).

---

## PHẦN 1: CÀI ĐẶT

```bash
git clone https://github.com/teddiesloco/AGS-Video-Editing.git ags-video-editing
cd ags-video-editing
./CAI-DAT-MAC.sh          # macOS
CAI-DAT-WIN.bat           # Windows (bấm đúp hoặc chạy trong cmd)
```
- Đặt tên thư mục là `ags-video-editing` (như lệnh trên): chuẩn Agent Skills yêu cầu tên skill trùng tên thư mục.
- Cần Python 3.10+ và FFmpeg (installer macOS tự cài qua Homebrew; Windows thử cài FFmpeg qua winget).
- Installer tạo môi trường ảo `venv/`. Python dùng cho mọi lệnh: macOS `./venv/bin/python`, Windows `venv\Scripts\python.exe`.
- Lần đầu cần Internet: faster-whisper tải model Whisper (~150 MB với `base`), rembg tải model tách người (~170 MB),
  reframe tải model YuNet (~230 KB, vào `~/.cache/ags-video-editing/`).

---

## PHẦN 2: DÙNG VỚI CODING AGENTS

| Skill | Lệnh (chạy từ thư mục gốc repo) |
|---|---|
| `/ags-edit-az` | `python scripts/ags_cut_silence.py <video> [--min-silence 0.4] [--threshold-db -30] [--model base]` |
| `/ags-edit-hook` | `python scripts/ags_text_behind_person.py <video> --text "<HOOK>" [--duration 3]` |
| `/ags-edit-editorial` | `python scripts/ags_editorial_sub.py <video> [--style editorial\|karaoke] [--keywords "..."]` |
| `/ags-voice-kinetic` | `python scripts/ags_voice_to_kinetic.py <audio>` |
| `/ags-voice-doodle` | `python scripts/ags_voice_to_doodle.py <audio>` |
| `/ags-reframe` | `python scripts/ags_reframe.py <video_ngang>` |
| `/ags-clip-shorts` | `python scripts/ags_clip_shorts.py transcript <video>` rồi `... cut <video> --transcript ... --ranges ...` |
| `/ags-edit-bds` | `python scripts/ags_bds_cli.py <draft\|render\|parcel\|subdivision\|ticker\|beats\|prompt> ...` |
| Kiểm định | `python harness/ags_anti_slop_guard.py <video> --contact-sheet <anh.jpg>` → exit `0` đạt · `2` cảnh báo · `1` lỗi |

Quy tắc chung cho mọi agent nằm ở [`AGENTS.md`](AGENTS.md). Model Whisper: `--model` nhận mọi tên của faster-whisper
(`tiny`, `base`, `small`, `medium`, `large-v3`, `large-v3-turbo`…); model càng lớn càng chính xác nhưng tải và chạy lâu hơn.

### 1. Claude Code
- Mở thư mục repo trong Claude Code và chat tự nhiên:
  > *"Dùng skill ags-clip-shorts làm 3 short từ ~/Desktop/livestream.mp4, kiểm định từng short."*
- MCP: lần đầu mở repo, Claude Code hỏi duyệt server `ags` khai báo trong `.mcp.json` (dùng `venv/bin/python` của repo —
  macOS/Linux). Windows: tự khai báo server cùng tên ở phạm vi local (được ưu tiên hơn `.mcp.json`):
  ```bat
  claude mcp add ags -- C:/DUONG/DAN/ags-video-editing/venv/Scripts/python.exe C:/DUONG/DAN/ags-video-editing/mcp/ags_mcp_server.py
  ```
- Gọi skill bằng slash command ở mọi dự án: liên kết vào thư mục skill cá nhân của Claude Code:
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
  Lệnh trong mỗi skill con tính từ thư mục gốc repo (hai cấp trên thư mục của skill đó).

### 2. OpenAI Codex
- Codex tự đọc `AGENTS.md` ở gốc repo khi bạn mở repo. Chat: *"Chạy ags-edit-editorial kiểu karaoke cho video.mp4 rồi kiểm định."*
- MCP: xem Phần 3.

### 3. Google Antigravity (IDE, 2.0, CLI)
- Antigravity tự nạp `AGENTS.md` ở gốc workspace làm quy tắc luôn bật.
- Muốn có slash command `/ags-…`: liên kết `skills/*` vào `.agents/skills/` của workspace, hoặc thư mục skill toàn máy
  (`~/.gemini/config/skills/` cho IDE/2.0, `~/.gemini/antigravity-cli/skills/` cho CLI).
- MCP: Antigravity CLI `agy mcp add ags /DUONG/DAN/ags-video-editing/venv/bin/python /DUONG/DAN/ags-video-editing/mcp/ags_mcp_server.py`,
  hoặc sửa `~/.gemini/config/mcp_config.json` (toàn máy) / `.agents/mcp_config.json` (theo workspace) — xem Phần 3.

### 4. Gemini CLI
- Trong thư mục repo: `gemini extensions link .` — nạp `GEMINI.md` (nhập `AGENTS.md`) và MCP server `ags` khai báo trong
  `gemini-extension.json` (dùng `venv/bin/python` của repo, chờ tối đa 30 phút mỗi lần gọi tool).
- Windows: khai báo `mcpServers.ags` trong `~/.gemini/settings.json` với `venv\Scripts\python.exe` (Phần 3) — cấu hình
  trong `settings.json` được ưu tiên hơn cấu hình của extension.
- Theo geminicli.com, từ 18/06/2026 người dùng gói miễn phí / Google One chuyển sang Antigravity CLI — khi đó làm theo mục 3.

### 5. Cursor
- `.cursor/rules/ags-video-editing.mdc` (Agent tự kéo vào khi việc liên quan video) và `AGENTS.md` được Cursor đọc sẵn.
- MCP: `.cursor/mcp.json` khai báo server `ags` bằng `${workspaceFolder}/venv/bin/python` (macOS/Linux) — bật trong
  **Customize → MCP**. Windows: thêm khối cấu hình (Phần 3) vào `~/.cursor/mcp.json` với `venv/Scripts/python.exe`.

---

## PHẦN 3: MCP SERVER

`mcp/ags_mcp_server.py` là MCP server (stdio, FastMCP). Mỗi tool gọi đúng script trong repo và trả về JSON:
`output` (đường dẫn kết quả), `exit_code`, `stderr_tail`, `stdout_tail`.

| Tool | Tham số chính |
|---|---|
| `cut_silence` | `input_path`, `output_path?`, `model?`, `min_silence?`, `threshold_db?` |
| `text_behind_person` | `input_path`, `text`, `output_path?`, `duration?` |
| `editorial_sub` | `input_path`, `output_path?`, `model?`, `style?` (`editorial`/`karaoke`), `highlight_color?`, `keywords?` |
| `voice_to_kinetic` | `audio_path`, `output_path?`, `model?` |
| `voice_to_doodle` | `audio_path`, `output_path?`, `model?` |
| `reframe` | `input_path`, `output_path?` |
| `clip_shorts_transcript` | `input_path`, `output_path?`, `model?` |
| `clip_shorts_cut` | `input_path`, `transcript_path`, `ranges[]` (`start`, `end`, `hook?`, `name?`), `output_dir?`, `style?`, `highlight_color?`, `keywords?`, `reframe?` |
| `bds_draft` | `name`, `clips[]`, `output_dir` hoặc `capcut=true`, `seconds?`, `bpm?`, `beat_step?`, `auto_beat?`, `title?`, `music?` |
| `bds_render` | `images[]`, `output_path`, `seconds?`, `bpm?`, `beat_step?`, `auto_beat?`, `music?`, `voice?`, `transition?` (`cut`/`wipe`), `transition_seconds?` |
| `anti_slop_guard` | `video_path`, `contact_sheet?`, `frames?` |

**Bước 1 — cài thư viện MCP (tuỳ chọn):**
```bash
./venv/bin/pip install -r requirements-mcp.txt          # macOS
venv\Scripts\pip install -r requirements-mcp.txt        # Windows
```
**Bước 2 — khai báo server.** Thay `/DUONG/DAN/ags-video-editing` bằng đường dẫn tuyệt đối của repo. Windows: `command` là
`C:/DUONG/DAN/ags-video-editing/venv/Scripts/python.exe` (dùng `/` hoặc `\\` trong JSON). Xử lý video mất vài phút:
client nào giới hạn thời gian gọi tool thì nâng lên.

**Claude Code** — `.mcp.json` có sẵn trong repo (macOS/Linux); hoặc:
```bash
claude mcp add --transport stdio ags -- /DUONG/DAN/ags-video-editing/venv/bin/python /DUONG/DAN/ags-video-editing/mcp/ags_mcp_server.py
```
**Claude Desktop** — `claude_desktop_config.json` (macOS: `~/Library/Application Support/Claude/`, Windows: `%APPDATA%\Claude\`);
**Antigravity** — `~/.gemini/config/mcp_config.json` hoặc `.agents/mcp_config.json`; **Gemini CLI** — `~/.gemini/settings.json`
(thêm `"timeout": 1800000`); **Cursor** — `~/.cursor/mcp.json`. Cùng một khối:
```json
{
  "mcpServers": {
    "ags": {
      "command": "/DUONG/DAN/ags-video-editing/venv/bin/python",
      "args": ["/DUONG/DAN/ags-video-editing/mcp/ags_mcp_server.py"]
    }
  }
}
```
**OpenAI Codex** — `~/.codex/config.toml` (mặc định Codex chỉ chờ tool 60 giây):
```toml
[mcp_servers.ags]
command = "/DUONG/DAN/ags-video-editing/venv/bin/python"
args = ["/DUONG/DAN/ags-video-editing/mcp/ags_mcp_server.py"]
tool_timeout_sec = 1800
```

---

## PHẦN 4: DÙNG TRÊN GIAO DIỆN WEB (CLAUDE.AI & CHATGPT.COM)

### Claude.ai — tải skill dạng zip
1. Trên máy: `python scripts/ags_build_skill_zips.py` → `dist/<tên-skill>.zip` (mỗi zip chứa thư mục skill ở cấp cao nhất,
   kèm `scripts/`, `harness/` cần thiết; script tự kiểm frontmatter theo chuẩn Agent Skills trước khi đóng gói).
2. claude.ai → **Customize → Skills → "+" → Upload a skill** → chọn file zip. Chỉ tải lên tài khoản của chính bạn —
   giấy phép không cho chia sẻ zip.
3. Giới hạn: theo tài liệu của Anthropic, sandbox chạy code của Claude không có Internet và danh sách thư viện cài sẵn
   không có FFmpeg hay faster-whisper — lệnh render/bóc băng có thể không chạy được trên claude.ai (chưa kiểm chứng).
   Khi đó Claude vẫn dùng skill để lên kịch bản, chọn đoạn short, soạn lệnh cho bạn chạy trên máy.

### Claude.ai — Project (đạo diễn kịch bản)
1. Tạo **Project**, tải `AGENTS.md`, `README.md` và các `skills/*/SKILL.md` vào **Project Knowledge**.
2. Dán vào **Custom Instructions**:
   ```text
   Bạn là Chuyên gia Đạo diễn & Biên tập Video của AGS (Agent Space) — bộ AGS Video Editing.
   Khi tôi tải lên video, file ghi âm, transcript JSON hoặc kịch bản:
   1. Bóc băng / đọc lời thoại chính xác, đủ dấu tiếng Việt.
   2. Đánh dấu từ đệm, nói lắp, khoảng lặng cần cắt.
   3. Với transcript của ags_clip_shorts: chọn đoạn short theo skills/ags-clip-shorts/references/chon-doan-short.md
      và trả về ranges.json.
   4. Viết lệnh AGS tương ứng để tôi chạy trên máy.
   ```

### ChatGPT.com (Custom GPT)
1. **Explore GPTs → Create a GPT** (hoặc Custom Instructions cá nhân).
2. Dán nội dung `adapters/chatgpt_custom_instructions.md` vào ô **Instructions**.
3. Chat: *"Đây là transcript JSON của livestream, chọn 3 đoạn làm short và viết ranges.json."*

---

## PHẦN 5: KIỂM ĐỊNH TRƯỚC KHI BÀN GIAO
```bash
python harness/ags_anti_slop_guard.py video.mp4 --contact-sheet video_sheet.jpg
```
- **Lỗi (exit 1):** không đọc được / không có hình / < 1 s; đen, đứng hình hoặc câm ≥ 90% thời lượng.
- **Cảnh báo (exit 2):** không có tiếng; lệch hình-tiếng > 0.25 s; ngoài -14 ± 2 LUFS; true peak > -1 dBTP;
  đoạn đen ≥ 0.5 s; đứng hình ≥ 5 s; khoảng lặng ≥ 2 s.
- Contact sheet: ô `#0` là khung 0, khung hồng là vùng an toàn 9:16. Soát và sửa theo
  [harness/QUY-TRINH-KIEM-DINH.md](harness/QUY-TRINH-KIEM-DINH.md) (tối đa 3 vòng).

---

## 📊 BẢNG TRA CỨU NHANH

| Bạn muốn | Chat với AI | Công cụ chạy |
|---|---|---|
| Cắt đoạn nói vấp, im lặng | *"Dùng ags-edit-az cắt video quay thô này"* | `ags_cut_silence.py` |
| Chữ chìm sau người | *"Đặt câu '90 NGÀY KIẾM 1 TỶ' sau lưng người nói"* | `ags_text_behind_person.py` |
| Phụ đề karaoke, cân âm | *"Làm sub karaoke, tô màu từ 'sổ hồng'"* | `ags_editorial_sub.py --style karaoke` |
| Ghi âm → chữ 2D / người que | *"Biến file ghi âm này thành video chữ 2D"* | `ags_voice_to_kinetic.py` / `ags_voice_to_doodle.py` |
| Video ngang → dọc | *"Chuyển podcast ngang này sang 9:16 bám mặt"* | `ags_reframe.py` |
| Video dài → short | *"Cắt 3 short hay nhất từ livestream này"* | `ags_clip_shorts.py transcript` → `cut` |
| Video Bất Động Sản | *"Dựng video đất nền, cắt theo nhạc, có giọng đọc"* | `ags_bds_cli.py render --auto-beat --voice` |
| Kiểm tra chất lượng | *"Chạy kiểm định và xem contact sheet"* | `harness/ags_anti_slop_guard.py` |

---

## ⚖️ GIẤY PHÉP
AGS Video Editing dùng **PolyForm Strict License 1.0.0** (`LICENSE`, giải thích tiếng Việt trong `LICENSE-VI.md`): được tải,
cài, chạy cho mục đích phi thương mại; không phân phối lại, không sửa đổi, không dùng thương mại. Cấp phép thương mại:
liên hệ Agent Space (AGS). Thành phần bên thứ ba: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

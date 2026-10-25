# 📖 HƯỚNG DẪN SỬ DỤNG — AGS VIDEO EDITING (AGS — Agent Space)

Hướng dẫn dùng bộ 10 skill dựng/edit video của AGS (Agent Space) trên **coding agent chạy cục bộ** (Claude Code, Google Antigravity,
OpenAI Codex, Gemini CLI, Cursor), qua **MCP server** (tuỳ chọn), và nói rõ **giao diện web** (claude.ai, chatgpt.com) làm được/không làm được gì.

## Bảng chọn món — Anh/chị muốn gì → nói câu nào → ra gì
Chép câu mẫu vào ô chat của trợ lý (Claude Code, Codex, Antigravity, Cursor), sửa chữ trong ngoặc cho đúng việc của mình.

| Anh/chị muốn gì | Nói câu nào (sửa chữ trong ngoặc) | Ra gì |
|---|---|---|
| Bất động sản — giới thiệu lô đất, căn hộ | "Làm video 45 giây giới thiệu (lô đất 5x20 ở Long An) từ ảnh em gửi, giọng miễn phí." | Video dọc có ảnh/clip của anh/chị, khung lô đất, chữ thông tin, giọng đọc, phụ đề |
| Quán ăn, đồ uống (F&B) | "Làm video 30 giây giới thiệu (món bún bò mới) của quán, giọng Google AI." | Video dọc ảnh món ăn có chuyển động, câu mở hút mắt, lời mời ghé quán |
| Giáo dục, khoá học | "Làm video 45 giây giải thích (vì sao học tiếng Anh mãi chưa nói được)." | Video giảng giải ngắn, mỗi ý một hình, từ khoá tô màu |
| Y tế – làm đẹp (phòng khám, spa) | "Làm video 30 giây chia sẻ (3 sai lầm khi chăm da mùa nắng) cho spa." | Video lời khuyên, giọng ấm, phụ đề rõ, không hứa hiệu quả chữa trị |
| Bán hàng online (thương mại điện tử) | "Làm video 30 giây giới thiệu (bình giữ nhiệt mới), nhấn giá và ưu đãi em đưa." | Video sản phẩm, giá/ưu đãi tô màu nổi, lời mời đặt hàng nhẹ nhàng |
| Tư duy kinh doanh — "30 năm trong 60 giây" | "Làm video 30 năm tư duy kinh doanh trong 60 giây về (dòng tiền), kiểu Business Thinking." | 60 giây: câu mở ≤ 8 chữ + 5–7 nguyên tắc ngắn + câu kết, Việt hoá 100% |
| Giải thích kiểu Jetlag, Việt hoá | "Làm video kiểu Jetlag Việt hoá giải thích (vì sao cà phê Việt xuất khẩu nhiều mà giá rẻ)." | 45–75 giây kể chuyện – giải thích có con số, ví dụ và tiền tệ Việt Nam |
| Du lịch, điểm đến | "Làm video 45 giây kể chuyện (vì sao Phú Quý ngày càng đông khách)." | Video kể chuyện điểm đến, có bản đồ/con số anh/chị cung cấp |
| Dịch vụ cho doanh nghiệp (B2B) | "Làm video 45 giây giải thích (quy trình 3 bước làm kế toán thuê) bằng sơ đồ 3D." | Video sơ đồ khối 3D: đầu vào → xử lý → kết quả |

### Nói xong thì trợ lý làm gì (AGS Video Studio)
1. **Hỏi lại tối đa 3 câu ngắn**, câu nào anh/chị đã nói thì bỏ qua:
   (1) Ngành/chủ đề gì? (2) Phong cách mẫu nào? (3) Giọng đọc miễn phí trên máy hay giọng Google AI (Gemini)?
   Trả lời ngoài các lựa chọn → trợ lý hỏi lại đúng câu đó kèm danh sách để chọn.
2. **Viết lời đọc tiếng Việt tự nhiên** (không dịch từng chữ, câu ngắn, câu mở đầu ≤ 8 chữ trên hình) và tự kiểm tới khi đạt.
   Anh/chị không phải viết. Có bài/link tham khảo thì gửi: trợ lý chỉ học ý, không chép nguyên văn quá 8 từ.
3. **Báo chi phí bằng tiền Việt trước khi làm** (ví dụ cách hiển thị: `12.000 đ`): số ảnh AI × đơn giá, giọng Google AI theo số
   chữ, thời gian dựng ước tính. Giọng miễn phí + hình có sẵn = **0 đồng**. Đơn giá theo bảng giá của người bán bộ này.
   Mặc định dùng hình miễn phí; muốn ảnh AI vẽ riêng cho từng ý thì nói "dùng ảnh AI" — trợ lý báo giá lại.
4. **Chờ anh/chị gõ "chạy"**. Chưa gõ "chạy" thì trợ lý không dựng, không gọi dịch vụ tính phí nào.
5. **Gửi video + ảnh lưới 12 khung** (mỗi khung có mốc giây) để anh/chị duyệt bằng mắt trước khi đăng.
6. **Sửa bằng lời thường** — nói như nói với người dựng phim:

| Anh/chị nói | Trợ lý đổi |
|---|---|
| "đổi sub sang vàng" | Chỉ màu chữ phụ đề thành vàng, dựng lại phần bị ảnh hưởng |
| "chữ to hơn" / "chữ nhỏ lại" | Cỡ chữ phụ đề (vẫn nằm trong vùng không bị nút của app che) |
| "đọc chậm lại" / "đọc nhanh hơn" | Tốc độ giọng đọc |
| "đổi sang giọng Google" / "dùng giọng miễn phí" | Giọng đọc (đổi sang giọng tính phí thì báo giá và chờ "chạy" lại) |
| "đổi cảnh 3" | Thay hình của cảnh số 3 |
| "bỏ câu kêu gọi cuối" / "câu cuối là: Nhắn em để giữ chỗ" | Câu kêu gọi cuối video |
| "làm 3 bản thử câu mở đầu" | 3 video chỉ khác 3 giây đầu để anh/chị đăng thử và tự so (báo chi phí trước) |

Câu chưa rõ như "làm đẹp hơn" → trợ lý hỏi lại 1 câu kèm 3 gợi ý, không tự đoán.

**Màu chữ có nghĩa:** xanh = tiền, lợi nhuận, kết quả tốt · vàng = nhấn mạnh, con số, thời gian · đỏ = cảnh báo, sai lầm, mất mát.

**Cam kết nội dung:** bộ này không hứa thu nhập hay lượt xem. Số liệu về doanh thu/khách hàng/kết quả của chính anh/chị chỉ
dùng khi anh/chị đưa; chưa có thì trợ lý đổi thành ví dụ minh hoạ có nhãn "ví dụ" trên video. "Business Thinking", "Jetlag"
chỉ là tên thể loại để anh/chị dễ gọi: trợ lý học cách kể, không dùng tên, logo, hình, tiếng hay câu chữ của các kênh đó.

**Giọng Google AI (Gemini):** cần khoá Google AI của anh/chị đặt trong biến môi trường `GEMINI_API_KEY` trên máy (trợ lý
hướng dẫn); đừng dán khoá vào khung chat. Chưa có khoá thì chọn giọng miễn phí — trợ lý không tự đổi giọng khi chưa hỏi.

### Khi trợ lý báo chưa làm được
| Trợ lý nói | Anh/chị làm gì |
|---|---|
| "Bộ cài thiếu bảng chọn món — chạy lại cài đặt." | Nói "cài lại bộ video" để trợ lý chạy lại cài đặt |
| "Em chưa hiểu câu trả lời. Chọn 1 trong: …" | Chọn 1 lựa chọn trong danh sách |
| "Anh/chị chưa bấm đồng ý chi phí nên em chưa chạy." | Xem lại chi phí rồi gõ "chạy" |
| "Nguồn không đọc được / kịch bản trùng nguồn quá 8 từ — em viết lại bằng lời của mình." | Không cần làm gì, hoặc gửi bài tham khảo khác |
| "Câu số N còn nghe như dịch máy hoặc sai nhịp …" | Không cần làm gì — trợ lý tự viết lại |
| "Cảnh N tạo ảnh AI chưa được, em dùng hình dự phòng." | Xem ảnh lưới; muốn đổi thì nói "đổi cảnh N" |
| "Chưa có khoá Google AI — chọn giọng miễn phí hoặc dán khoá." | Chọn giọng miễn phí, hoặc nhờ trợ lý hướng dẫn đặt khoá trên máy |
| "Chữ phụ đề lấn vùng giao diện — em đã thu nhỏ/đổi dòng." | Không cần làm gì |
| "Chưa tạo được ảnh lưới xem trước." | Mở thẳng file video để xem |
| "Em chưa chắc ý anh/chị: đổi màu chữ, đổi giọng hay đổi cảnh nào?" | Chọn 1 trong 3 gợi ý |
| "Video chưa đạt chuẩn: …" | Chờ trợ lý sửa và dựng lại |
| "Câu mở đầu chưa đủ lực: …" | Không cần làm gì — trợ lý tự viết lại |
| "Câu này nói về kết quả thật của anh/chị nhưng em chưa có số liệu — anh/chị đưa số hoặc em đổi thành ví dụ minh hoạ." | Đưa số thật của mình, hoặc đồng ý dùng ví dụ minh hoạ |
| "Giọng Google AI mô hình cũ/không chạy — em thử mô hình mới hoặc đề nghị giọng miễn phí." | Chọn thử lại hoặc dùng giọng miễn phí |

> **Trạng thái kiểm chứng (nói thật):** mọi thứ dưới đây đã được chạy thực tế trên **macOS Apple Silicon, Python 3.11**.
> Installer Windows (`CAI-DAT-WIN.bat`) và chạy trên Linux **chưa được chạy thử**; việc thả skill vào từng client khác ngoài
> những gì ghi cụ thể làm theo tài liệu của client, chưa được thử trên từng client. Nếu gặp lỗi, đưa stderr cho agent.
> AGS Video Studio (phần trên) là phần mới: cài vào 4 client đã được kiểm bằng test cài đặt trên thư mục nhà giả; hội thoại
> trong từng client chưa được thử tay.

---

## PHẦN 1: CÀI ĐẶT (người dùng chỉ cần một bước)

1. Giải nén `ags-video-editing.zip` → thư mục `ags-video-editing/` (tên thư mục phải giữ nguyên: chuẩn Agent Skills yêu cầu
   trùng tên skill). Đường dẫn chứa dấu cách (ví dụ `~/Phim của tôi/skills/...`) vẫn chạy được.
2. Đặt thư mục đó vào nơi skill của agent (Phần 2), mở agent và nói việc cần làm bằng tiếng Việt, ví dụ:
   > *"Cắt khoảng lặng video ~/Desktop/quay-tho.mp4 rồi làm phụ đề karaoke."*
3. Lần đầu, agent tự đọc `SKILL.md`, chạy `scripts/ags_setup.py --check`, xin bạn **một** câu đồng ý rồi cài môi trường. Bạn
   không phải trả lời câu hỏi nào về Python/venv/pip.

### Agent (hoặc bạn) cài bằng lệnh
```bash
bash "/đường/dẫn/ags-video-editing/CAI-DAT-MAC.sh" --yes       # macOS / Linux
```
```bat
"C:\đường\dẫn\ags-video-editing\CAI-DAT-WIN.bat" --yes         :: Windows (chưa kiểm chứng trên Windows thật)
```
| Tuỳ chọn | Ý nghĩa |
|---|---|
| (không có) | Cài **đầy đủ**: lõi + MCP + cả hai giọng đọc cục bộ (VieNeu, ZeroTTS) + SFX |
| `--core` | Bỏ thư viện TTS (~0,9 GB); SFX/MCP/các skill khác vẫn có. Thêm TTS sau: chạy lại không kèm `--core` |
| `--yes` | Cho phép installer tự cài Python 3.11 / FFmpeg còn thiếu: Homebrew hoặc `uv` (macOS/Linux), `winget` (Windows) |
| `--check` (qua `ags_setup.py`) | Chỉ kiểm tra, in JSON, không đổi gì |
| `--warmup-tts` (qua `ags_setup.py`) | Tải trước model của cả hai engine TTS (~2,7 GB) bằng terminal |
| `--print-mcp` / `--register-claude-code` | In cấu hình MCP theo client / đăng ký MCP ở user scope của Claude Code |

Cách cài làm gì: tìm Python 3.11 (hoặc 3.12) → kiểm tra `ffmpeg`/`ffprobe` (và libass cho phụ đề) → tạo `venv/` **bên trong thư mục skill**
→ `pip install` các file `requirements*.txt` (phiên bản đã ghim) vào venv đó → `pip check` + import thử → ghi cấu hình MCP với đường dẫn
tuyệt đối. Không dùng pip toàn cục, không ghi ra ngoài thư mục skill (trừ cache pip và cache model).
- Python dùng cho mọi lệnh: macOS/Linux `venv/bin/python`, Windows `venv\Scripts\python.exe` — agent luôn gọi đường dẫn tuyệt đối.
- Thiếu điều kiện tiên quyết → exit `3` kèm lệnh cài cụ thể; Windows vừa cài FFmpeg bằng winget cần mở terminal mới.
- Dời/đổi tên thư mục skill: venv và cấu hình MCP chứa đường dẫn tuyệt đối — chạy lại installer.

### Model tải ở lần dùng đầu (cần Internet, không kèm trong gói)
| Model | Dung lượng (đo trên macOS) | Giấy phép |
|---|---|---|
| Whisper `base` (faster-whisper) | ~150 MB | MIT |
| rembg `u2net_human_seg` | ~170 MB | Apache-2.0 |
| YuNet (reframe) | ~230 KB | MIT |
| VieNeu TTS | ~1,0 GB | Apache-2.0 |
| ZeroTTS | ~1,7 GB | MIT (giọng đi kèm: chỉ đánh giá/demo) |

Chi tiết giấy phép: `THIRD_PARTY_NOTICES.md`. Tải TTS lần đầu mất vài phút và có thể vượt giới hạn thời gian của tool MCP — hãy chạy
`python scripts/ags_setup.py --warmup-tts` trong terminal trước.

---

## PHẦN 2: DÙNG VỚI CODING AGENTS (chạy cục bộ)

| Skill | Lệnh (chạy từ thư mục skill bằng Python của venv) |
|---|---|
| `/ags-studio` | `python scripts/ags_studio.py intake --request "<câu khách>" --json` → kịch bản qua `python scripts/ags_vi_script.py validate\|hook\|claims ... --json` → `quote --script-file ... --hook-text ...` → (khách gõ "chạy") `run --confirmed` → `revise --say "..."` / `variants --count 3 --hook ... ×3` — quy trình đủ ở `skills/ags-studio/SKILL.md` |
| `/ags-edit-az` | `python scripts/ags_cut_silence.py <video> [--min-silence 0.4] [--threshold-db -30] [--model base]` |
| `/ags-edit-hook` | `python scripts/ags_text_behind_person.py <video> --text "<HOOK>" [--duration 3]` |
| `/ags-edit-editorial` | `python scripts/ags_editorial_sub.py <video> [--style clean\|editorial\|karaoke] [--keywords "..."]` |
| `/ags-voice-kinetic` | `python scripts/ags_voice_to_kinetic.py <audio>` |
| `/ags-voice-doodle` | `python scripts/ags_voice_to_doodle.py <audio>` |
| `/ags-reframe` | `python scripts/ags_reframe.py <video_ngang>` |
| `/ags-clip-shorts` | `python scripts/ags_clip_shorts.py transcript <video>` rồi `... cut <video> --transcript ... --ranges ...` |
| `/ags-edit-bds` | `python scripts/ags_bds_cli.py <draft\|render\|parcel\|subdivision\|ticker\|beats\|prompt> ...` |
| `/ags-voice-sfx` | `python scripts/ags_tts.py voices\|synthesize --engine vieneu\|zerotts ...` · `python scripts/ags_sfx.py list\|mix ...` |
| Kiểm định | `python harness/ags_anti_slop_guard.py <video> --contact-sheet <anh.jpg>` → exit `0` đạt · `2` cảnh báo · `1` lỗi |

Quy tắc chung cho mọi agent nằm ở [`AGENTS.md`](AGENTS.md). Model Whisper: `--model` nhận mọi tên của faster-whisper
(`tiny`, `base`, `small`, `medium`, `large-v3`, `large-v3-turbo`…); model càng lớn càng chính xác nhưng tải và chạy lâu hơn.

### Giọng đọc tiếng Việt và SFX (`/ags-voice-sfx`)
- `ags_tts.py synthesize --engine vieneu --text-file loi.txt --out loi.wav` — văn bản UTF-8 → WAV mới (không ghi đè). Chỉ giọng có
  sẵn, chạy cục bộ trên CPU, không clone, không dịch vụ từ xa. `ags_tts.py voices --engine ...` liệt kê giọng.
- Ưu tiên `vieneu` (Apache-2.0, 25 giọng). Giọng `zerotts` (8 giọng) tác giả chỉ cho **đánh giá/demo**, phải nói rõ là giọng tổng hợp.
- `ags_sfx.py mix video.mp4 --events events.json --out video_sfx.mp4` — chèn SFX Kenney CC0 theo mốc giây, giữ hình và tiếng gốc,
  không rút ngắn video. `events.json`: `[{"file":"click_001.ogg","time":2.0,"gain":0.3}]`. `ags_sfx.py list` liệt kê 6 hiệu ứng có sẵn.

### 1. Claude Code
- Thả thư mục `ags-video-editing/` vào `~/.claude/skills/` (toàn máy) hoặc `<dự án>/.claude/skills/` (theo dự án) rồi chat:
  > *"Dùng skill ags-clip-shorts làm 3 short từ ~/Desktop/livestream.mp4, kiểm định từng short."*
- Skill gốc `SKILL.md` điều phối 10 skill con trong `skills/` (gồm `ags-studio`). Không cần `claude mcp add` để dùng — Claude Code chạy script qua terminal.
- MCP (tuỳ chọn, dùng ở mọi dự án): `python scripts/ags_setup.py --register-claude-code` (cần lệnh `claude` trong PATH), hoặc lệnh do
  `--print-mcp` in ra. Cũng có thể mở chính thư mục skill làm dự án: `.mcp.json` do installer sinh sẵn đường dẫn tuyệt đối.

### 2. OpenAI Codex
- Codex đọc `AGENTS.md` ở gốc thư mục làm việc. Mở thư mục skill làm workspace (hoặc copy/tham chiếu `AGENTS.md` vào dự án) rồi chat:
  *"Chạy ags-edit-editorial kiểu karaoke cho video.mp4 rồi kiểm định."* Agent tự chạy bước kiểm tra/cài môi trường trong `AGENTS.md`.
- MCP: Phần 3 (`--print-mcp` in khối `~/.codex/config.toml`).

### 3. Google Antigravity (IDE, 2.0, CLI)
- Antigravity nạp `AGENTS.md` ở gốc workspace làm quy tắc luôn bật. Muốn có slash command `/ags-…`, đặt thư mục `ags-video-editing/`
  (và nếu cần các thư mục trong `skills/`) vào `.agents/skills/` của workspace, hoặc thư mục skill toàn máy
  (`~/.gemini/config/skills/` cho IDE/2.0, `~/.gemini/antigravity-cli/skills/` cho CLI).
- MCP: Antigravity CLI `agy mcp add ags <python-venv> <ags_mcp_server.py>` hoặc `~/.gemini/config/mcp_config.json` (toàn máy) /
  `.agents/mcp_config.json` (theo workspace) — `--print-mcp` in đủ lệnh với đường dẫn tuyệt đối.

### 4. Gemini CLI
- Chạy `python scripts/ags_setup.py` trước, rồi `gemini extensions link <thư mục skill>` — nạp `GEMINI.md` (nhập `AGENTS.md`) và MCP
  server `ags` khai báo trong `gemini-extension.json` (interpreter `venv/bin/python` trên macOS/Linux; trên Windows installer đổi
  thành `venv\Scripts\python.exe`; chờ tối đa 30 phút mỗi lần gọi tool).
- Cấu hình trong `~/.gemini/settings.json` được ưu tiên hơn cấu hình của extension.
- Theo geminicli.com, từ 18/06/2026 người dùng gói miễn phí / Google One chuyển sang Antigravity CLI — khi đó làm theo mục 3.

### 5. Cursor
- `.cursor/rules/ags-video-editing.mdc` (Agent tự kéo vào khi việc liên quan video; trỏ tới `skills/ags-studio/SKILL.md` cho
  yêu cầu "làm video cho ngành X") và `AGENTS.md` được Cursor đọc sẵn khi mở thư mục skill làm dự án.
- MCP: installer sinh `.cursor/mcp.json` với đường dẫn tuyệt đối (không còn biến thay thế đường dẫn) — bật trong
  **Customize → MCP**. Dùng ở dự án khác: dán khối từ `--print-mcp` vào `~/.cursor/mcp.json`.

---

## PHẦN 3: MCP SERVER (tuỳ chọn)

`mcp/ags_mcp_server.py` là MCP server (stdio, FastMCP). Mỗi tool gọi đúng script trong skill và trả về JSON:
`output` (đường dẫn kết quả), `exit_code`, `stderr_tail`, `stdout_tail`. Server tự suy ra thư mục skill từ vị trí của nó nên không
phụ thuộc cwd; mọi đường dẫn cấu hình là **tuyệt đối do installer sinh**, tránh lỗi client không giải được biến thay thế đường dẫn
(biểu hiện: `ENOENT` khi khởi động server vì interpreter còn nguyên chuỗi biến).

| Tool | Tham số chính |
|---|---|
| `cut_silence` | `input_path`, `output_path?`, `model?`, `min_silence?`, `threshold_db?` |
| `text_behind_person` | `input_path`, `text`, `output_path?`, `duration?` |
| `editorial_sub` | `input_path`, `output_path?`, `model?`, `style?` (`clean` mặc định/`editorial`/`karaoke`), `highlight_color?` (bỏ trống = màu của kiểu), `keywords?`, `script_path?` (file UTF-8 đúng lời đọc) |
| `voice_to_kinetic` | `audio_path`, `output_path?`, `model?` |
| `voice_to_doodle` | `audio_path`, `output_path?`, `model?` |
| `reframe` | `input_path`, `output_path?` |
| `clip_shorts_transcript` | `input_path`, `output_path?`, `model?` |
| `clip_shorts_cut` | `input_path`, `transcript_path`, `ranges[]` (`start`, `end`, `hook?`, `name?`), `output_dir?`, `style?`, `highlight_color?`, `keywords?`, `reframe?` |
| `bds_draft` | `name`, `clips[]`, `output_dir` hoặc `capcut=true`, `seconds?`, `bpm?`, `beat_step?`, `auto_beat?`, `title?`, `music?` |
| `bds_render` | `output_path`, `clips[]` (hoặc `images[]`; nhận video và ảnh), `seconds?`, `bpm?`, `beat_step?`, `auto_beat?`, `music?`, `voice?`, `transition?` (`cut`/`wipe`/`dissolve`), `transition_seconds?`, `zoom?` (`auto`/`none`/`subtle`), `grade?` (`none`/`natural`/`warm`) |
| `anti_slop_guard` | `video_path`, `contact_sheet?`, `frames?` |
| `tts_voices` | `engine` (`vieneu`/`zerotts`) |
| `tts_synthesize` | `engine`, `text_path`, `output_path` (WAV mới), `voice?` |
| `sfx_list` | — |
| `sfx_mix` | `input_path`, `events[]` (`file`, `time`, `gain?`), `output_path` |
| `blender_3d_render` | `output_path`, `scene_preset?`, `seconds?`, `title?`, `mode?` (cần add-on Blender tuỳ chọn) |
| `ags_studio_menu` | — (bảng chọn món của bản cài) |
| `ags_studio_intake` | `request?` (câu đầu của khách), `job_dir?`, `topic?`, `preset?`, `voice?` (`synth`/`vieneu`/`gemini`), `images?` (`ai`/`free`) |
| `ags_studio_quote` | `job_dir`, `script_path?`, `hook_text?` (chữ mở ≤ 8 từ), `claims[]?`, `source_url?`, `source_text?` |
| `ags_studio_run` | `job_dir`, `confirmed` (chỉ `true` sau khi khách gõ "chạy") |
| `ags_studio_revise` | `job_dir`, `say` (nguyên văn câu khách), `confirmed?` |
| `ags_studio_variants` | `job_dir`, `hooks[]` (3 câu mở khác loại), `count?` (3), `confirmed?` |
| `ags_studio_proof` | `spec_path`, `out_dir`, `confirmed?` (bằng chứng render của người bán) |
| `ags_studio_validate_script` | `script`, `duration_sec`, `source_text?` |
| `ags_studio_hook` | `spoken?` (trống = thư viện 8 loại câu mở), `on_screen?` |
| `ags_studio_claims` | `script`, `claims[]` (`text`, `claim_source`: `khach-nhap` / `tai-lieu:<tên>` / `vi-du`) |
| `ags_studio_profile` | `samples[]` (1–5 link công khai hoặc đoạn văn) |

Tool `ags_studio_*` trả `exit_code`, `result` (JSON của lệnh), `stderr_tail`, `stdout_tail`. Lệnh `ags_studio.py` lỗi nghiệp
vụ (exit `2`): `result.error.code` = `E-ags-video-studio-10x-NNN`, `result.error.message` bằng lời thường. Lệnh
`ags_vi_script.py` chưa đạt (exit `1`): `result.ok = false`, `result.errors[]` ghi mã, số câu và lý do.

**Lấy cấu hình đúng cho máy này:**
```bash
python scripts/ags_setup.py --print-mcp
```
In ra lệnh `claude mcp add ...` (Claude Code), `agy mcp add ...` (Antigravity CLI), khối JSON cho Claude Desktop
(`claude_desktop_config.json`: macOS `~/Library/Application Support/Claude/`, Windows `%APPDATA%\Claude\`) · Antigravity
(`~/.gemini/config/mcp_config.json`, `.agents/mcp_config.json`) · Gemini CLI (`~/.gemini/settings.json`, thêm `"timeout": 1800000`) ·
Cursor (`~/.cursor/mcp.json`), và khối TOML cho OpenAI Codex (`~/.codex/config.toml`, `tool_timeout_sec = 1800` — mặc định Codex chỉ
chờ tool 60 giây). Xử lý video mất vài phút: client nào giới hạn thời gian gọi tool thì nâng lên.

Installer cũng tự ghi `.mcp.json` (Claude Code và client đọc `.mcp.json`) và `.cursor/mcp.json` trong thư mục skill, mỗi file là
`{"mcpServers": {"ags": {"type": "stdio", "command": "<venv python tuyệt đối>", "args": ["<server tuyệt đối>"], "cwd": "<thư mục skill>"}}}`;
các server khác trong file được giữ nguyên. Hai file này chứa đường dẫn của riêng máy bạn nên không nằm trong zip và không commit.

---

## PHẦN 4: DÙNG TRÊN GIAO DIỆN WEB (CLAUDE.AI & CHATGPT.COM) — CHỈ LẬP KẾ HOẠCH, KHÔNG RENDER

**Nói thẳng:** web không bảo đảm có FFmpeg, faster-whisper, quyền cài thư viện hay Internet trong môi trường chạy code, và không tự
nạp được zip cài đặt này. Vì vậy **bộ này không render video trên claude.ai hay ChatGPT web**, và chưa được kiểm chứng ở đó.
Web chỉ giúp: chọn đoạn short từ transcript, viết hook/kịch bản/văn bản lồng tiếng, soát ảnh contact sheet bạn gửi, và soạn lệnh
để bạn (hoặc agent trên máy bạn) chạy. Muốn render thật: dùng Phần 2.

### claude.ai — skill lập kế hoạch (`ags-video-editing-web.zip`)
1. claude.ai → **Customize → Skills → "+" → Upload a skill** → chọn `ags-video-editing-web.zip`. Chỉ tải lên tài khoản của chính bạn
   (giấy phép không cho chia sẻ zip).
2. Zip này chỉ chứa hướng dẫn (`SKILL.md` + quy trình chọn đoạn + quy trình kiểm định), **không có script** — skill được viết để
   Claude nói rõ giới hạn và không tự nhận đã render. Muốn chạy thật: dùng bản cài cục bộ `ags-video-editing.zip` (Phần 1–2).

### claude.ai — Project (đạo diễn kịch bản)
1. Tạo **Project**, tải `AGENTS.md`, `README.md` và các `skills/*/SKILL.md` vào **Project Knowledge**.
2. Dán vào **Custom Instructions**:
   ```text
   Bạn là Trợ lý Lập kế hoạch Dựng Video của AGS (Agent Space) — bộ AGS Video Editing. Bạn không render được video.
   Khi tôi gửi transcript JSON, kịch bản hoặc ảnh contact sheet:
   1. Đọc lời thoại chính xác, đủ dấu tiếng Việt; đánh dấu từ đệm, nói lắp, khoảng lặng cần cắt.
   2. Với transcript của ags_clip_shorts: chọn đoạn short theo skills/ags-clip-shorts/references/chon-doan-short.md
      và trả về ranges.json.
   3. Viết lệnh AGS tương ứng để tôi chạy trên máy; không nói đã chạy, không bịa số đo.
   ```

### ChatGPT.com (Custom GPT)
1. **Explore GPTs → Create a GPT** (hoặc Custom Instructions cá nhân).
2. Dán nội dung `adapters/chatgpt_custom_instructions.md` vào ô **Instructions** (đã ghi rõ không render).
3. Chat: *"Đây là transcript JSON của livestream, chọn 3 đoạn làm short và viết ranges.json."*

---

## PHẦN 5: KIỂM ĐỊNH TRƯỚC KHI BÀN GIAO
```bash
python harness/ags_anti_slop_guard.py video.mp4 --contact-sheet video_sheet.jpg
```
- **Lỗi (exit 1):** không đọc được / không có hình / < 1 s; đen, đứng hình hoặc câm ≥ 90% thời lượng.
- **Cảnh báo (exit 2):** không có tiếng; lệch hình-tiếng > 0.25 s; ngoài -14 ± 2 LUFS; true peak > -1 dBTP;
  đoạn đen ≥ 0.5 s; đứng hình ≥ 5 s; khoảng lặng ≥ 2 s.
- Contact sheet: ô `#0` là khung 0; thêm `--debug-zones` thì có khung hồng = vùng an toàn 9:16 (bản gửi khách không có). Soát và sửa theo
  [harness/QUY-TRINH-KIEM-DINH.md](harness/QUY-TRINH-KIEM-DINH.md) (tối đa 3 vòng).

---

## PHẦN 6: XỬ LÝ SỰ CỐ
| Triệu chứng | Cách xử lý |
|---|---|
| `ags_setup.py` exit `3` | Thiếu Python 3.11/3.12 hoặc FFmpeg — chạy lại với `--yes` hoặc cài theo lệnh trong stderr |
| Windows: vừa cài FFmpeg vẫn báo thiếu | Mở terminal mới (PATH chỉ cập nhật cho phiên mới), rồi chạy lại |
| Phụ đề không hiện | `--check` báo `ffmpeg.libass: false` — cài bản FFmpeg đầy đủ (Homebrew, Gyan.FFmpeg) |
| Đã dời/đổi tên thư mục skill, MCP báo không tìm thấy Python | Chạy lại `CAI-DAT-MAC.sh` / `CAI-DAT-WIN.bat` để dựng lại venv và cấu hình |
| Tool TTS MCP hết giờ ở lần đầu | Chạy `python scripts/ags_setup.py --warmup-tts` trong terminal, rồi gọi lại |
| `Missing optional TTS dependency` | Đã cài `--core`; chạy lại installer không kèm `--core` |

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
| Ghép clip stock/quay tay + lời đọc | *"Ghép các clip này thành video dọc 30 giây, đọc lời này, hoà mờ, zoom nhẹ, có phụ đề và SFX"* | `ags_tts.py` → `ags_bds_cli.py render --clips --voice` → `ags_editorial_sub.py` → `ags_sfx.py mix` |
| Đọc văn bản bằng giọng Việt | *"Đọc đoạn này bằng giọng nữ, làm video chữ"* | `ags_tts.py` → `ags_voice_to_kinetic.py` |
| Chèn tiếng click/ting | *"Chèn tiếng click ở giây 2 và 5"* | `ags_sfx.py mix` |
| Kiểm tra chất lượng | *"Chạy kiểm định và xem contact sheet"* | `harness/ags_anti_slop_guard.py` |

---

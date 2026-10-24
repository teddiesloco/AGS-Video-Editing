---
name: ags-video-editing
description: "AGS (Agent Space) — bộ 9 skill edit video tự động bằng Python + FFmpeg chạy trên máy người dùng (macOS, Linux, Windows): cắt lặng & từ đệm, chữ chìm sau người, phụ đề tạp chí/karaoke -14 LUFS, ghi âm thành chữ 2D hoặc người que, reframe ngang → dọc 9:16 bám mặt, video dài → nhiều short, video Bất Động Sản, giọng đọc tiếng Việt cục bộ (VieNeu, ZeroTTS) + hiệu ứng âm thanh CC0, kèm harness kiểm định. Tự dựng môi trường lần đầu. Dùng khi người dùng muốn dựng, cắt, làm phụ đề, làm short/reels, lồng tiếng hoặc kiểm tra chất lượng video."
compatibility: "Chạy cục bộ: Claude Code, Google Antigravity, Codex, Gemini CLI, Cursor. Cần Python 3.11 (3.12 được phép) và FFmpeg; installer tự tạo venv trong thư mục skill. Lần đầu cần Internet để cài thư viện và tải model. KHÔNG chạy được render trong claude.ai / ChatGPT web."
license: "PolyForm Strict 1.0.0 — xem LICENSE"
---

# AGS Video Editing — Bộ Skill Edit Video Tự Động của AGS (Agent Space)

Người dùng chỉ cần nói việc họ muốn (ví dụ *"cắt lặng video này rồi làm phụ đề karaoke"*). **Bạn (agent) lo môi trường.**
Không hỏi người dùng về Python, venv, pip hay đường dẫn.

## 0. Xác định đường dẫn (bắt buộc, mỗi phiên)
- `SKILL_DIR` = thư mục chứa file `SKILL.md` này, đường dẫn tuyệt đối. **Có thể chứa dấu cách → luôn đặt trong ngoặc kép.**
- `PY` = Python của venv nằm trong skill: macOS/Linux `SKILL_DIR/venv/bin/python` · Windows `SKILL_DIR\venv\Scripts\python.exe`.
- Mọi lệnh `python scripts/...` trong tài liệu nghĩa là: chạy `PY` với cwd = `SKILL_DIR`. Đường dẫn video của người dùng
  luôn truyền dạng tuyệt đối. Đừng dùng `python`/`pip` toàn cục.

## 1. Kiểm tra môi trường (vài giây, không cần hỏi)
Nếu `PY` tồn tại: `"PY" "SKILL_DIR/scripts/ags_setup.py" --check` → in JSON. `ready_core: true` thì làm việc luôn.
`ready_tts: true` nghĩa là cả hai giọng đọc đã cài thư viện (model vẫn tải ở lần dùng đầu).

## 2. Chưa sẵn sàng → cài một lần (hỏi người dùng đúng MỘT câu rồi chạy)
Hỏi (tiếng Việt, ngắn, đồng ý/không): *"Mình cần cài môi trường cho bộ dựng video này vào thư mục skill: thư viện Python
(~0,9 GB) và FFmpeg/Python nếu máy chưa có. Giọng đọc tiếng Việt cục bộ sẽ tải thêm model ~2,7 GB ở lần dùng đầu. Đồng ý không?"*
Đồng ý rồi chạy trong terminal, cwd = `SKILL_DIR` (không cần hỏi thêm):
```bash
bash "SKILL_DIR/CAI-DAT-MAC.sh" --yes          # macOS / Linux
"SKILL_DIR\CAI-DAT-WIN.bat" --yes              # Windows (chưa kiểm chứng trên Windows thật)
```
- `--yes` cho phép installer tự cài Python 3.11 / FFmpeg còn thiếu (Homebrew, uv hoặc winget). Thêm `--core` nếu người
  dùng nói không cần giọng đọc (bỏ qua thư viện TTS ~0,9 GB).
- Xong khi dòng `AGS_SETUP_RESULT {"ok": true ...}` và exit `0`. Exit `3` = thiếu Python/FFmpeg và không tự cài được:
  đọc stderr, báo người dùng đúng lệnh cần chạy. Exit `2` = cài xong nhưng kiểm tra lỗi: đưa stderr cho người dùng.
- Installer chỉ ghi vào `SKILL_DIR/venv` và cấu hình MCP trong `SKILL_DIR`. Dời/đổi tên thư mục skill → chạy lại installer.
- Windows vừa cài FFmpeg bằng winget mà `--check` vẫn không thấy: mở terminal mới rồi chạy lại.

## 3. 9 skill (chi tiết trong `skills/<tên>/SKILL.md` — đọc file đó trước khi chạy)
1. **ags-edit-az** — `python scripts/ags_cut_silence.py <video>` — bỏ khoảng lặng (đo độ to) và từ đệm, crossfade tiếng, -14 LUFS.
2. **ags-edit-hook** — `python scripts/ags_text_behind_person.py <video> --text "<HOOK>"` — câu hook chìm sau lưng người nói.
3. **ags-edit-editorial** — `python scripts/ags_editorial_sub.py <video> [--style karaoke]` — phụ đề tạp chí/karaoke trong
   vùng an toàn 9:16, -14 LUFS.
4. **ags-voice-kinetic** — `python scripts/ags_voice_to_kinetic.py <audio>` — ghi âm → video chữ 2D bật nảy 1080x1920.
5. **ags-voice-doodle** — `python scripts/ags_voice_to_doodle.py <audio>` — ghi âm → người que nét chì trên giấy kraft.
6. **ags-reframe** — `python scripts/ags_reframe.py <video>` — ngang → dọc 9:16, khung bám khuôn mặt.
7. **ags-clip-shorts** — `python scripts/ags_clip_shorts.py transcript|cut ...` — video dài → nhiều short có hook + karaoke.
8. **ags-edit-bds** — `python scripts/ags_bds_cli.py <draft|render|parcel|subdivision|ticker|beats|prompt>` — video Bất Động Sản; `render`
   cũng ghép **clip video thật + ảnh** (zoom nhẹ, cut/wipe/dissolve, giọng đọc) thành video dọc.
   Người dùng chưa nói phong cách / muốn "đẹp hơn, chuyên nghiệp hơn": chọn 1 trong 5 concept (calm travel, cinematic narrative,
   energetic social, clean product, personal documentary) ở `skills/ags-edit-bds/references/editing-concepts.md` — **bắt buộc lập
   storyboard (mục đích, chủ thể, tiêu đề, caption từng cảnh) trước khi `render`, và xem khung thật tại các mối nối sau render**.
   Số liệu trong đó là heuristic; `--grade` chỉ áp cùng một công thức, không khớp màu; phụ đề không thay thiết kế hình.
9. **ags-voice-sfx** — `python scripts/ags_tts.py ...` giọng đọc tiếng Việt cục bộ (VieNeu / ZeroTTS) và
   `python scripts/ags_sfx.py ...` trộn hiệu ứng CC0 theo mốc thời gian vào video.

## 4. Câu lệnh tự nhiên người dùng có thể nói (agent tự chọn skill)
- "Cắt khoảng lặng và từ ờ ừm trong ~/Desktop/quay-tho.mp4."
- "Làm phụ đề karaoke cho video này, tô màu từ khoá 'bất động sản'."
- "Biến livestream.mp4 thành 3 short dọc có hook rồi kiểm định từng cái."
- "Đọc đoạn văn này bằng giọng tiếng Việt, làm video chữ chạy, chèn tiếng click ở giây 2 và 5."
- "Ghép các clip trong thư mục này thành video dọc 30 giây, đọc lời này bằng giọng Việt, hoà mờ, zoom nhẹ, phụ đề và SFX khi chuyển cảnh." → `skills/ags-edit-bds/SKILL.md`, Bước 4b.
- "Kiểm tra chất lượng video này trước khi đăng."

## 5. Quy tắc chạy
Quy tắc đầy đủ ở `AGENTS.md` (cùng thư mục) — đọc trước khi chạy lần đầu: không tự viết lệnh FFmpeg dài; không bịa số liệu
BĐS; kiểm định bắt buộc sau mỗi lần render:
`python harness/ags_anti_slop_guard.py <video> --contact-sheet <video>_sheet.jpg` → exit `0` đạt · `2` cảnh báo · `1` lỗi;
mở contact sheet soát theo `harness/QUY-TRINH-KIEM-DINH.md`.

## 6. Tải model (lần đầu, cần Internet — không kèm sẵn trong gói)
Whisper `base` ~150 MB · rembg `u2net_human_seg` ~170 MB · YuNet ~230 KB · VieNeu ~1,0 GB · ZeroTTS ~1,7 GB (số đo trên macOS).
TTS tải lâu hơn giới hạn thời gian gọi tool của nhiều client: nên tải trước trong terminal bằng
`python scripts/ags_setup.py --warmup-tts` thay vì để lần gọi MCP đầu tiên bị hết giờ. Giấy phép từng model:
`THIRD_PARTY_NOTICES.md`.

## 7. MCP (tuỳ chọn — script chạy trực tiếp qua terminal đã đủ)
Installer ghi sẵn `.mcp.json` và `.cursor/mcp.json` trong `SKILL_DIR` với đường dẫn tuyệt đối (client nào mở đúng thư mục
skill này sẽ tự thấy server `ags`). Dùng ở mọi dự án: `"PY" scripts/ags_setup.py --print-mcp` in lệnh/khối cấu hình cho
Claude Code, Antigravity, Gemini CLI, Codex, Claude Desktop, Cursor; `--register-claude-code` đăng ký cho Claude Code.
Danh sách tool: `AGENTS.md`.

## 8. Ranh giới nền tảng (nói thật với người dùng)
- **Chạy được (cục bộ):** Claude Code, Antigravity, Codex, Gemini CLI, Cursor — agent có terminal + quyền cài đặt trên máy
  người dùng. Đã chạy thực tế trên macOS Apple Silicon, Python 3.11; Windows/Linux có installer nhưng chưa được chạy thử.
- **Không render được:** claude.ai và ChatGPT web — không bảo đảm FFmpeg/pip/Internet và không tự nạp được zip này. Dùng
  zip web `ags-video-editing-web.zip` (claude.ai, tải riêng) hoặc `adapters/chatgpt_custom_instructions.md` (ChatGPT) để lên kịch bản,
  chọn đoạn short, soát contact sheet và nhận lệnh để tự chạy trên máy — xem `HUONG-DAN-SU-DUNG.md`, Phần 4.

## 9. Giấy phép
PolyForm Strict 1.0.0 — chỉ dùng phi thương mại, không phân phối lại, không sửa đổi (`LICENSE`, `LICENSE-VI.md`).
Hiệu ứng âm thanh Kenney (`assets/sfx`) là CC0 và model/thư viện bên thứ ba theo giấy phép riêng — `THIRD_PARTY_NOTICES.md`.

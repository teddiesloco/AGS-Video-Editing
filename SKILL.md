---
name: ags-video-editing
description: "AGS (Agent Space) — bộ 10 skill dựng/edit video tự động bằng Python + FFmpeg chạy trên máy người dùng (macOS, Linux, Windows). AGS Video Studio: khách nói 1 câu lời thường theo bảng chọn món (BĐS, F&B, giáo dục, làm đẹp, bán hàng online, 30 năm tư duy kinh doanh trong 60 giây, giải thích kiểu Jetlag Việt hoá, du lịch, B2B), agent hỏi ngược 3 câu, báo chi phí VND, chờ 'chạy' rồi ra video 9:16 + ảnh lưới để duyệt và sửa bằng lời. Kèm: cắt lặng & từ đệm, chữ chìm sau người, phụ đề karaoke -14 LUFS, ghi âm thành chữ 2D/người que, reframe 9:16 bám mặt, video dài → short, video BĐS, giọng đọc tiếng Việt (cục bộ hoặc Google AI) + SFX CC0, harness kiểm định. Dùng khi người dùng muốn làm video, reels, short, phụ đề, lồng tiếng hoặc kiểm tra chất lượng video."
compatibility: "Chạy cục bộ: Claude Code, Google Antigravity, Codex, Gemini CLI, Cursor. Cần Python 3.11 (3.12 được phép) và FFmpeg; installer tự tạo venv trong thư mục skill. Lần đầu cần Internet để cài thư viện và tải model. KHÔNG chạy được render trong claude.ai / ChatGPT web."
license: "PolyForm Strict 1.0.0 — xem LICENSE"
---

# AGS Video Editing — Bộ Skill Dựng Video Tự Động của AGS (Agent Space)

## Bảng chọn món — Anh/chị muốn gì → nói câu nào → ra gì
Khách nói theo bảng này (hoặc chỉ nói "làm video cho ngành em") → **đọc và làm đúng `skills/ags-studio/SKILL.md`**:
hỏi ngược đúng 3 câu (bỏ câu khách đã nói), báo chi phí bằng VND, CHỜ khách nói "chạy", đưa ảnh lưới để duyệt.

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

Mọi món đều ra **video dọc 9:16 đăng Reels/TikTok/Shorts + ảnh lưới 12 khung** để duyệt bằng mắt; sửa bằng lời thường
(*"đổi sub sang vàng"*, *"đọc chậm lại"*, *"đổi cảnh 3"*, *"làm 3 bản thử câu mở đầu"*). "Business Thinking", "Jetlag" chỉ là
tên thể loại: học cách kể, không dùng hình/tiếng/chữ của các kênh đó. Không hứa thu nhập hay lượt xem; không bịa số liệu
kết quả của khách.

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

## 3. 10 skill (chi tiết trong `skills/<tên>/SKILL.md` — đọc file đó trước khi chạy)
0. **ags-studio** — `python scripts/ags_studio.py intake|quote|run|revise|variants|menu ... --json` và
   `python scripts/ags_vi_script.py validate|hook|claims|profile ... --json` — khách nói 1 câu → hỏi ngược 3 câu → kịch bản
   Việt hoá qua `validate` → báo chi phí VND → chờ "chạy" → video 9:16 + ảnh lưới → sửa bằng lời. Mặc định cho mọi yêu cầu
   "làm video cho ngành/chủ đề X" chưa nói rõ cách dựng.
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

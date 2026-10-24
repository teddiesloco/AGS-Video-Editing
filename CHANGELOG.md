# CHANGELOG — AGS Video Editing

## v1.3 — 2026-10-08
**Mới**
- Bản cài đặt kéo-thả: `ags-video-editing.zip` (gốc zip là thư mục `ags-video-editing/` có `SKILL.md`; đủ mã nguồn, `assets/`, 9 skill
  con, `requirements*.txt`, installer, giấy phép và thông báo bên thứ ba). Agent tự kiểm tra (`ags_setup.py --check`) và cài
  môi trường sau một câu đồng ý của người dùng.
- `scripts/ags_setup.py` viết lại: kiểm Python 3.11/3.12 và FFmpeg/ffprobe/libass, tạo/dựng lại `venv/` trong thư mục skill,
  cài lõi + MCP + **cả hai** engine TTS (mặc định; `--core` bỏ TTS), `pip check` + import thử, `--warmup-tts`, `--print-mcp`,
  `--register-claude-code`. `CAI-DAT-MAC.sh` / `CAI-DAT-WIN.bat` chọn đúng Python và với `--yes` tự cài Python/FFmpeg thiếu.
- `/ags-voice-sfx`: giọng đọc tiếng Việt cục bộ VieNeu + ZeroTTS (`ags_tts.py`) và trộn SFX CC0 Kenney theo mốc (`ags_sfx.py`);
  MCP thêm `tts_voices`, `tts_synthesize`, `sfx_list`, `sfx_mix`.
- `ags-video-editing-web.zip`: skill claude.ai chỉ lập kế hoạch, nói rõ không render; adapter ChatGPT cập nhật tương tự.
- `ags_bds_cli.py render` (`--clips`, `--images` vẫn dùng được) nhận **video thật và/hoặc ảnh**: clip video giữ chuyển động (không
  trích khung tĩnh), `--zoom auto|none|subtle`, chuyển cảnh `cut|wipe|dissolve`, in `cut_times` để đặt SFX; kết hợp giọng đọc TTS,
  phụ đề (`ags_editorial_sub.py`) và SFX (`ags_sfx.py`) — quy trình một câu tự nhiên ở `skills/ags-edit-bds/SKILL.md` (Bước 4b).
  Kiểm đầu vào: thời lượng hữu hạn > 0, file tồn tại, video đủ dài; **giọng đọc dài hơn hình bị từ chối thay vì cắt**.
  `AgsDirectRenderer.render_image_slideshow` đổi tên `render_slideshow` (thêm `zoom`); MCP `bds_render` nhận `clips`/`images`, `zoom`.
- Phụ đề (`ags_editorial_sub.py`): chữ xuống tối đa 2 dòng (hook 3) ở đúng cỡ chữ thay vì thu nhỏ cả câu cho vừa một dòng
  (chữ cũ ~55% cỡ gốc, khó đọc trên điện thoại), vẫn trong `safe_box`. Mới `--script <loi.txt>` / MCP `script_path`: chữ hiện
  đúng lời đã biết, Whisper chỉ cho mốc thời gian.
- Phụ đề `--style clean` (mặc định mới của `ags_editorial_sub.py` / MCP `editorial_sub`): Sans đậm trắng, viền mảnh + bóng mềm
  (`\blur`), từ khoá vàng cát `#E3C285`, ≤ 28 ký tự / 3 s, tối đa 2 dòng trong `safe_box`. `editorial` (Serif) và `karaoke`
  giữ nguyên; `--highlight-color` bỏ trống = màu mặc định của kiểu (clean vàng cát, editorial/karaoke `#FFD60A`).
- `ags_bds_cli.py render --grade none|natural|warm` / MCP `bds_render.grade` / `render_slideshow(grade=)`: chỉnh màu nhẹ (tương
  phản/bão hoà +5%, `warm` thêm ấm nhẹ), cùng công thức cho mọi clip. Đầu ra có giọng/nhạc được cắt đúng độ dài hình
  (10 clip × 3 s + dissolve 0,5 s = 30,00 s, 900 khung), không kéo giãn giọng.

**Thay đổi**
- Cấu hình MCP không còn dùng biến `${...}`: `.mcp.json`, `.cursor/mcp.json` do installer sinh với đường dẫn tuyệt đối (không commit,
  không vào zip); `gemini-extension.json` được chỉnh interpreter theo hệ điều hành.
- `scripts/ags_build_skill_zips.py` dựng hai zip trên thay cho zip từng skill, kiểm frontmatter, đường dẫn tài liệu, import nội bộ,
  pin TTS, chuỗi cấm (đường dẫn máy tác giả), rồi giải nén vào thư mục có dấu cách để chạy thử `--check`.
- `THIRD_PARTY_NOTICES.md`: tách giấy phép mã/model/giọng của VieNeu và ZeroTTS; ghi ngoại lệ CC0 cho `assets/sfx`.

## v1.2 — 2026-10-08
**Mới**
- `/ags-reframe` (`scripts/ags_reframe.py`): video ngang → dọc 9:16 1080x1920, khung bám khuôn mặt chính (OpenCV
  `FaceDetectorYN` + model YuNet tải lần đầu, kiểm SHA-256), vùng chết + làm mượt; không thấy mặt thì cắt giữa.
- `/ags-clip-shorts` (`scripts/ags_clip_shorts.py`): `transcript` (JSON câu + từng từ) → agent chọn đoạn → `cut` xuất
  từng short có bám mặt, phụ đề karaoke từ transcript, hook hiện ngay khung 0; đoạn 1–180 s.
- Phụ đề `--style karaoke`: từ đang nói đổi màu đúng mốc từng từ; `--keywords` + `--highlight-color` tô màu từ khoá.
- BĐS: `--auto-beat` / `beats --music` dò BPM + mốc beat từ file nhạc (numpy, không thêm thư viện); `--transition wipe`
  (quét trái → phải, giữ đúng mốc beat); `--voice` giọng đọc, nhạc tự nhỏ khi có giọng (sidechaincompress, đo thử ~16 dB).
- Harness: blackdetect, freezedetect, silencedetect (khoảng lặng dài), true peak, LUFS, lệch hình-tiếng với ngưỡng ghi rõ;
  exit `0` đạt · `1` lỗi · `2` cảnh báo; `--contact-sheet` / `--frames` xuất ảnh lưới khung hình cho vòng tự soát
  `harness/QUY-TRINH-KIEM-DINH.md`.
- Đóng gói cho agent: `AGENTS.md` (Codex, Antigravity, Cursor), `GEMINI.md` + `gemini-extension.json` (Gemini CLI),
  `.cursor/rules/ags-video-editing.mdc` + `.cursor/mcp.json`, `.mcp.json` (Claude Code),
  `scripts/ags_build_skill_zips.py` → `dist/<skill>.zip` cho claude.ai (kiểm frontmatter theo Agent Skills spec).
- MCP: thêm `reframe`, `clip_shorts_transcript`, `clip_shorts_cut`; tham số mới cho `cut_silence`, `editorial_sub`,
  `bds_render`, `bds_draft`, `anti_slop_guard`.
- `tests/ags_test_core.py`: vùng an toàn, NFC, cắt lặng + crossfade, phụ đề karaoke/hook, mã thoát harness.

**Thay đổi**
- `/ags-edit-az`: dò khoảng lặng bằng độ to thật (RMS, ngưỡng `--threshold-db` so với mức giọng nói) kết hợp từ đệm của
  Whisper; chừa 0.10 s trước / 0.15 s sau; mốc cắt theo khung hình; crossfade 25 ms ở mối nối; `--model` nhận mọi tên
  model của faster-whisper (kể cả `large-v3-turbo`).
- Vùng an toàn 9:16 định nghĩa một lần (`SAFE_ZONE_9X16` trong `scripts/ags_common.py`, nguồn: Meta, Google Ads, TikTok) và
  áp cho phụ đề, hook, card kinetic, phụ đề doodle, nhãn thửa đất, ticker BĐS.
- Mọi chữ được chuẩn hoá Unicode NFC trước khi vẽ/ghi.
- `loudnorm` TP -1.5 → -2.0 dBTP: AAC đẩy true peak lên tới ~0.8 dB (đo thực tế), giữ dưới trần -1 dBTP của harness.
- Giấy phép: chuyển sang PolyForm Strict 1.0.0 (nguyên văn) + `LICENSE-VI.md` giải thích tiếng Việt.

## v1.1
- Skill BĐS (`/ags-edit-bds`), MCP server, đổi tên AGS, giấy phép dùng cá nhân.

## v1.0
- 5 skill đầu tiên, harness Anti-AI-Slop, adapter Antigravity/Gemini.

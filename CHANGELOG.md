# CHANGELOG — AGS Video Editing

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

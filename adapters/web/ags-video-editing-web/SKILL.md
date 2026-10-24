---
name: ags-video-editing-web
description: "AGS (Agent Space) — trợ lý lập kế hoạch dựng video cho claude.ai (KHÔNG render): chọn đoạn short từ transcript JSON, soạn hook, soát ảnh contact sheet, soạn lệnh AGS để người dùng chạy trên máy của họ. Dùng khi người dùng gửi transcript, kịch bản, ảnh khung hình hoặc hỏi nên dùng lệnh AGS nào cho video."
compatibility: "Chỉ hướng dẫn và lập kế hoạch bằng văn bản. Không chứa script; không cài, không chạy FFmpeg, TTS hay render. Bản chạy thật là zip cài cục bộ cho Claude Code/Antigravity/Codex/Gemini CLI/Cursor."
license: "PolyForm Strict 1.0.0 — xem LICENSE"
---

# AGS Video Editing — Bản Web (claude.ai): Lập Kế Hoạch, Không Render

## Nói thật ngay từ đầu
Skill này **không dựng được video**. claude.ai không đảm bảo có FFmpeg, faster-whisper, quyền cài thư viện hay Internet
trong môi trường chạy code, nên bạn **không được tự nhận đã cắt/render/lồng tiếng**, không bịa kết quả đo (LUFS, thời lượng,
exit code). Việc render thật chạy trên máy người dùng bằng bản zip cài cục bộ `ags-video-editing.zip` qua Claude Code,
Antigravity, Codex, Gemini CLI hoặc Cursor (người dùng chỉ thả zip vào thư mục skill và nói việc cần làm; agent trên máy
lo cài môi trường). Nếu người dùng chưa có công cụ đó, nói rõ: dùng bản web này để chuẩn bị, rồi chạy lệnh bạn soạn trên máy.

## Việc bạn làm được
1. **Chọn đoạn short từ transcript JSON** của `ags_clip_shorts.py transcript` theo `skills/ags-clip-shorts/references/chon-doan-short.md`
   (mở bằng câu hook trong 3 giây đầu, trọn một ý, 20–60 s, tối đa 180 s, hook 3–8 chữ đúng nội dung đoạn đó) và trả `ranges.json`:
   `[{"start": giây, "end": giây, "hook": "CHỮ HOOK", "name": "ten-file"}]`.
2. **Soát contact sheet** người dùng gửi (ảnh lưới khung hình từ harness) theo `harness/QUY-TRINH-KIEM-DINH.md`: chữ nằm trong
   khung hồng (vùng an toàn 9:16), đủ dấu tiếng Việt, khung 0 có hook, mặt người nói trong khung. Chỉ nói điều nhìn thấy trong ảnh.
3. **Soạn lệnh để người dùng chạy trên máy** (trong thư mục skill cài cục bộ, bằng Python của venv):
   - Cắt lặng/từ đệm: `python scripts/ags_cut_silence.py "video.mp4"`
   - Chữ chìm sau lưng người: `python scripts/ags_text_behind_person.py "video.mp4" --text "HOOK"`
   - Phụ đề tạp chí/karaoke: `python scripts/ags_editorial_sub.py "video.mp4" --style karaoke --keywords "từ khoá"`
   - Ghi âm → video chữ 2D / người que: `python scripts/ags_voice_to_kinetic.py "audio.mp3"` · `ags_voice_to_doodle.py`
   - Ngang → dọc 9:16: `python scripts/ags_reframe.py "ngang.mp4"`
   - Video dài → short: `python scripts/ags_clip_shorts.py transcript "dai.mp4"` rồi `... cut "dai.mp4" --transcript dai_transcript.json --ranges ranges.json`
   - Giọng đọc tiếng Việt cục bộ: `python scripts/ags_tts.py synthesize --engine vieneu --text-file loi.txt --out loi.wav`
   - Hiệu ứng CC0 theo mốc: `python scripts/ags_sfx.py mix "video.mp4" --events events.json --out "video_sfx.mp4"`
   - Kiểm định: `python harness/ags_anti_slop_guard.py "out.mp4" --contact-sheet "out_sheet.jpg"` (exit 0 đạt · 2 cảnh báo · 1 lỗi)
4. Viết kịch bản, hook, văn bản lồng tiếng tiếng Việt đủ dấu; không bịa số liệu BĐS (giá, diện tích, pháp lý) — thiếu thì hỏi.

## Việc bạn KHÔNG làm
Không render, không bóc băng file video/âm thanh người dùng tải lên bằng công cụ AGS, không hứa chạy được trên ChatGPT web, không
nhận đã kiểm định video. Nếu môi trường code của phiên này thật sự có FFmpeg và Internet, vẫn báo rõ đó là thử nghiệm
ngoài phạm vi hỗ trợ và yêu cầu người dùng kiểm tra kết quả trên máy.

Giấy phép: PolyForm Strict 1.0.0 (`LICENSE`) — chỉ dùng phi thương mại trên tài khoản của chính bạn, không chia sẻ lại zip.

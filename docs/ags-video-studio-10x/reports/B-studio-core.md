# Báo cáo lát B — Lõi Studio & pipeline (24/10/2026)

## 1. File đã đổi / tạo
| File | Việc |
|---|---|
| `scripts/ags_studio.py` (mới) | `intake` / `quote` / `run --confirmed` / `revise --say` / `variants --hook ×3` / `proof --spec` / `menu`, mọi lệnh `--json`; `studio-job.json` (khoá cấp 1: job_id, status, request, answers, next_question, images, script, hook_text, claims, source_url, transcreated, quote, script_report, hook_report, claims_report, profile, render_params, revisions[], variants[], scenes[], contact_sheet, output{mp4,nohook_mp4,scene_json,provenance_json,subtitles_ass,sha256,ffprobe,guard_exit,lufs}, voice{engine,key_present,model,style}, checks, keywords, fallback_scenes); mọi lệnh gọi `assert_client_licensed()`; `http_api()` dùng chung cho HTTP. |
| `config/menu.json` (mới) | 8 món theo ngành (BĐS, F&B, giáo dục, y tế–làm đẹp, TMĐT, tư duy kinh doanh, du lịch, B2B), mỗi món 1 câu mẫu; 5 kiểu (`business-thinking-60s`, `jetlag-vi`, `bds`, `editorial`, `isometric-3d`) có nhãn tiếng Việt, aliases, thời lượng, archetype, chỉ dẫn giọng Gemini, khung phong cách ảnh AI. |
| `config/pricing.json` (mới) | `image_ai_vnd`, `gemini_tts_vnd_per_1000_chars` = `null` (chưa có giá thật → không bịa số; báo "chưa có bảng giá"), `render_minutes_per_video_minute` = 3 (đo thật: 36,5 s video dựng 1 phút 46 s). |
| `services/ops/ags-reels-footage/ags_reels_pipeline.py` | Tham số mới (mặc định giữ hành vi cũ): `motion="alternate"` (`plan_motion_shots` + `_apply_motion_shots`: push_in/pan_left/pull_out/pan_right/parallax, mỗi cảnh ≤ 2,5 s, xoay vòng nên không 2 cảnh liền cùng kiểu; độ dài câu theo tỉ lệ số từ để đổi cảnh rơi vào ranh giới câu); `pick_keywords` → `write_ass(keyword_colors=…)` cho mọi kiểu phụ đề ASS (trước đây `keywords=()`); `subtitle_style="bt_vi"`; `hook_text` (≤ 8 từ, cắt theo từ, không cắt giữa chữ), `hook_whoosh` (mặc định bật, t=0); `contact_sheet_path` + guard `--frames 12`; `tts_style` + model Gemini ghi vào `scene.json` (`tts_model`) và provenance; `sub_color`, `sub_size`, `voice_speed` (atempo), `swap_scenes`, `ai_fallback` (thử 2 lần rồi hình dự phòng, ghi `fallback_scenes` mã E-006), `ai_style`, `example_label`, `cache_dir` (ảnh AI + giọng đã trả tiền dùng lại khi dựng lại), `nohook_mp4` (bản không hook cho 3 bản thử); xuất `<stem>_subtitles.ass`. |
| `services/ops/ags-reels-footage/ags_reels_footage.py` | Route `POST /api/v1/studio/{intake,quote,run,validate-script,hook,profile,revise,variants}` + `GET /api/v1/studio/jobs/{id}` theo dispatcher sẵn có; run/revise/variants bắt bearer token như `/v1/reels-render`; job_id lọc regex (chặn `../`). |
| `scripts/ags_editorial_sub.py` | Kiểu `bt_vi` (font "display", 0,062 cạnh ngắn = 67 px, viền đen, `max_words` 4 → `split_word_groups` chia đều cụm 2–4 từ); `write_ass(keyword_colors, text_color, size_ratio, label)`; mặc định cũ cho ra đúng file .ass như trước. |
| `scripts/ags_common.py` | `FONT_FILES["display"]`: Bricolage Grotesque → Be Vietnam Pro (assets/fonts hoặc font máy) → font "bold". |
| `scripts/ags_tts.py` | Gemini qua Interactions API đúng tài liệu hiện hành (`speech_metadata.style`, khoá ở header `x-goog-api-key` thay vì query string), mặc định `gemini-3.8-flash-tts`, đọc `AGS_GEMINI_TTS_MODEL`; trả `model`/`style`; lỗi → `GeminiTTSError(status)`; CLI `--style`. |
| `tests/ags_test_studio.py` (mới) | 10 test (mục 3). |
| `CHANGELOG.md` | 3 gạch đầu dòng cho lát B. |

## 2. Lệnh test + kết quả thật
- `venv/bin/python -m unittest tests.ags_test_studio -v` → **10/10 OK** (150,7 s; gồm 1 lượt dựng thật).
- `venv/bin/python tests/ags_test_core.py` → 9/9; `tests/ags_test_bds_engine.py` → 9/9.
- `venv/bin/python -m unittest tests.ags_test_installer` → 4/4 (lát C thêm 1); `tests.ags_test_blender` → 6 chạy, OK, 1 skip (máy không có Blender thật — có từ trước); `tests.ags_test_shield` → 17/17; `tests.ags_test_vi_script` (lát A) → 9/9.
- `services/ops/ags-reels-footage`: `venv/bin/python -m unittest test_ags_reels_pipeline -v` → **8/8 OK** (203 s).
- Lát A đã có `ags_vi_script.py` trước khi test chạy → **không dùng stub**.

Test lát B phủ: AC-003 (run không `--confirmed` → E-003 khi `AGS_REELS_DIR` trỏ thư mục không tồn tại và proxy chết: chứng minh cổng đứng trước mọi lệnh nạp bộ dựng/gọi mạng; không mp4; status vẫn `quoted`), AC-004 (quote và run → E-007 + gợi ý synth/vieneu, `answers.voice` vẫn `gemini`, không mp4), BR-004 (bảng 4 dòng: 7.907,22 → 8.000 đ; thiếu giá → "chưa có bảng giá"; 0 → "0 đồng"; số nguyên), AC-008 (bảng 8 câu → đúng 1 tham số whitelist; "làm đẹp hơn" / "rm -rf" → không đổi; CLI: chỉ `sub_color` đổi, `revisions` 1 mục, E-010 + 3 gợi ý), FR-003/004 (mọi câu mẫu menu tự trả lời câu 1–2; trả lời lạ → E-002 hỏi lại đúng câu), AC-014 (bảng thời lượng → mọi cảnh ≤ 2,5 s, không lặp liền kề, tổng giữ nguyên; dựng thật: `scenes[]` > 10 cảnh đều ≤ 3 s, không 2 cảnh liền cùng kiểu; variants chưa xác nhận → E-003 kèm "0 đồng"; xác nhận → đúng 3 mp4 thuộc 3 loại hook, khung 0,3 s khác nhau, khung 6 s giống hệt), AC-010 (khoá giả GEMINI/9router/HTTP token đặt trong env: không xuất hiện trong bất kỳ byte nào của thư mục job và log CLI; không chuỗi "vsec" trong json/ass), AC-007/AC-011 trên mp4 thật.

## 3. Render thử thật (giọng máy `synth` + hình archetype miễn phí — không có khoá Gemini/9router trên máy)
| Lượt | Kết quả đo |
|---|---|
| Clip ngắn qua pipeline (`/tmp/agsb/short`, kịch bản 5 câu) | 13,3 s, 1080×1920, 30 fps, h264 yuv420p, AAC; guard exit 0; −14,0 LUFS; `contact-sheet.jpg` 12 khung có mốc `t=…s` (khung 0 có chữ hook); khung t=0,3 s khác bản không hook 14,74% điểm ảnh ở dải trên vùng an toàn → **có chữ hook**; phụ đề vẽ lại từ đúng file .ass: hộp chữ [125, 1031, 695, 1242] nằm trong `SAFE_ZONE_9X16` [120, 288, 780, 1248], cỡ nhỏ nhất 67 px; whoosh `ags_whoosh_fast.ogg` ở t=0,0 trong provenance; từ khoá tô: "500 triệu" #A8FF3E, "phá sản"/"Mất khách" #FF5A5F, "30 ngày"/"mỗi tuần" #FFD166; 8 cảnh push_in→pan_left→pull_out→pan_right→parallax→… ≤ 2,26 s. |
| `ags_studio.py` intake → quote → run --confirmed (editorial, 114 từ) | 36,5 s, guard 0, −14,0 LUFS, hook 13,59%, hộp phụ đề [194, 1110, 704, 1242] trong vùng an toàn, 67 px; dựng 1 phút 46 s. `revise --say "đổi màu sub sang vàng"` → bản `-r1` dựng lại 1 phút 39 s, style Caption `&H0066D1FF` (= #FFD166), giọng lấy từ `cache/` (không tổng hợp lại). |
| Lỗi mô hình Gemini (khoá giả + `AGS_GEMINI_TTS_MODEL=gemini-0.0-retired-tts`) | Interactions API trả HTTP 400 → **E-014** + gợi ý synth/vieneu, giọng không bị đổi, khoá giả không có trong job/đầu ra. |

## 4. Điểm lệch spec / giới hạn (ghi thật)
1. **Gemini TTS & ảnh AI chưa chạy thật** (máy không có `GEMINI_API_KEY`/`GOOGLE_API_KEY`/`AGS_NINEROUTER_API_KEY`). Đã kiểm endpoint Interactions có phản hồi đúng dạng (400 khoá sai). Proof (lát D) phải chạy với khoá thật để xác nhận `gemini-3.8-flash-tts` + `speech_metadata.style` + giải mã WAV 24 kHz.
2. **FR-024**: mặc định đổi từ `gemini-2.5-flash-preview-tts` (không còn trong danh sách mô hình hỗ trợ của trang Google) sang `gemini-3.8-flash-tts`, theo đúng ý FR-024 ("proof phải chạy với mô hình hiện hành"). Mọi lỗi 4xx (kể cả khoá sai, Google trả 400) đều ra E-014 — API không tách được "khoá sai" với "mô hình sai".
3. **FR-015 "chỉ render lại phần bị ảnh hưởng"**: `revise` chạy lại cả pipeline; phần TỐN TIỀN (ảnh AI, giọng) lấy từ `cache/` nên không trả tiền lại, phần miễn phí dựng lại (~1,5 phút/36 s video).
4. **FR-023 3 bản thử**: khác nhau ở chữ hook trên màn hình (≤ 8 từ, 3 loại khác nhau, 0–2,5 s), dùng lại nguyên hình/giọng/phụ đề; **câu hook đọc bằng giọng không đổi** (ghép giọng hook mới vào giọng thân bài cần căn từ, chưa làm).
5. **FR-010 parallax**: một lớp ảnh, giả 2.5D bằng zoom + trượt chéo (không tách tiền cảnh/hậu cảnh). Cảnh trong một câu nối bằng cắt cứng; dissolve chỉ ở ranh giới câu.
6. **FR-012 "khớp mốc từ của giọng đọc"**: không bật Whisper (`verify_asr`) trong studio → mốc từ chia đều trong từng câu, câu dài theo tỉ lệ số từ — xấp xỉ, chưa khớp từng từ. Giọng `synth` (macOS) đọc ~3,1 từ/s nên kịch bản 45 s (114 từ) ra 36,5 s; mẫu 60 s ±5 s của AC-001 phụ thuộc giọng thật (Gemini/VieNeu) hoặc `revise "đọc chậm hơn"`.
7. **Whoosh t=0**: bộ `assets/sfx` của `ags_sfx` không có whoosh; dùng `ags_whoosh_fast.ogg` (âm tổng hợp first-party của AGS-Auto-Editor) trộn trong bước SFX sẵn có của pipeline, ghi provenance.
8. **E-008**: phụ đề luôn được `write_ass` hạ cỡ/đổi dòng để vừa vùng an toàn; sau render `checks.subtitle_safe_zone` đo lại, lệch thì trả cảnh báo E-008 (không vòng sửa tự động).
9. **Đóng gói**: `ags_build_skill_zips.validate` cấm `import ags_*` ngoài gói; bộ dựng `ags-reels-footage` nằm cạnh gói (như `ags_setup.py` đăng ký MCP "ags-reels") nên `ags_studio.py` và test nạp nó bằng `importlib` từ `AGS_REELS_DIR` / thư mục anh em. Thiếu bộ dựng → E-011 lời thường.
10. `pricing.json` để `null` đơn giá (không có nguồn giá thật) → khách thấy "chưa có bảng giá" cho ảnh AI/Gemini cho tới khi người bán điền.
11. Lỗi có sẵn (không thuộc lát B, chưa sửa): `ags_reels_footage.py` lệnh CLI `batch` dùng `Path` chưa import (pyflakes: undefined name).

## 5. Blocker
Không có blocker cho lát B. Phần chưa chạy thật duy nhất là Gemini TTS + ảnh AI (thiếu khoá) — chuyển cho lát D chạy `ags_studio.py proof --spec … --out-dir proof --confirmed` với khoá thật.

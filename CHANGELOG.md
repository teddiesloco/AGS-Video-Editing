# CHANGELOG — AGS Video Editing

## Chưa phát hành
**Mới**
- Phụ đề ngắt theo cụm ý: `ags_common.group_word_lists(..., semantic_chunk=True)` ngắt ở dấu phẩy/chấm phẩy và từ nối
  (nhưng, vì, nên, để, khi, nếu, thì, mà…), gộp lại cụm 1 từ nếu còn vừa giới hạn; pipeline ags-reels bật mặc định cho
  phụ đề .ASS (`semantic_chunk=false` để tắt). `ags_cut_silence.py --insight-pause 0.35`: giữ lặng tới mốc kết câu
  (dấu . ! ? của Whisper) + 0,35 s, khoảng lặng không gắn với mốc kết câu cắt như cũ.
- AGS Video Studio cho người không biết kỹ thuật: bảng chọn món "Anh/chị muốn gì → nói câu nào → ra gì" (9 món: BĐS, F&B,
  giáo dục, y tế–làm đẹp, thương mại điện tử, 30 năm tư duy kinh doanh trong 60 giây, giải thích kiểu Jetlag Việt hoá, du
  lịch, B2B) đặt đầu `SKILL.md`, `README.md`, `HUONG-DAN-SU-DUNG.md`; skill mới `skills/ags-studio/SKILL.md` (hỏi ngược đúng
  3 câu, bỏ câu đã biết; agent viết kịch bản Việt hoá và chạy `ags_vi_script.py validate` tới khi đạt; báo chi phí VND, chờ
  "chạy"; ảnh lưới để duyệt; sửa bằng lời thường; thông báo lỗi lời thường E-ags-video-studio-10x-001..014). Skill được
  `--install-all-clients` chép vào Claude Code, Codex, Antigravity (Cursor nạp qua thư mục tương thích + rule
  `.cursor/rules/ags-video-editing.mdc`). MCP thêm 11 tool `ags_studio_*` bọc `ags_studio.py` / `ags_vi_script.py`.
  Gói phân phối kèm `config/`.
- `scripts/ags_studio.py` (lõi Studio): `intake` / `quote` / `run --confirmed` / `revise --say` / `variants --hook ×3` /
  `proof --spec` / `menu`, mọi lệnh `--json`, trạng thái ở `<job>/studio-job.json`, gọi `assert_client_licensed()`;
  chưa xác nhận -> E-003 trước khi nạp bộ dựng; giọng Google AI thiếu khoá -> E-007 (không tự đổi giọng); lỗi 4xx mô hình
  Gemini -> E-014. `config/menu.json` (8 món + 5 kiểu video, nhãn, chỉ dẫn giọng, khung ảnh AI) và `config/pricing.json`
  (đơn giá người bán tự điền; thiếu -> "chưa có bảng giá"; làm tròn lên 1.000 đ). Bộ dựng `ags-reels-footage` nạp từ
  `AGS_REELS_DIR` / thư mục anh em. HTTP `127.0.0.1:8792` thêm `/api/v1/studio/{intake,quote,run,validate-script,hook,
  profile,revise,variants}` + `GET /api/v1/studio/jobs/{id}`.
- Pipeline ags-reels: `motion="alternate"` (push_in / pan_left / pull_out / pan_right / parallax, mỗi cảnh ≤ 2,5 s, không
  lặp liền kề, thời lượng câu theo số từ), phụ đề `bt_vi` (cụm 2–4 từ, 6,2% cạnh ngắn, font Bricolage Grotesque → Be
  Vietnam Pro → bold, trong `SAFE_ZONE_9X16`) tô màu từ khoá tự động bằng `ags_vi_script.pick_keywords`, chữ hook ≤ 8 từ
  từ khung 0 + whoosh t=0, `contact-sheet` 12 khung có mốc giây, bản không hook cho 3 bản thử, cache ảnh AI/giọng khi
  dựng lại, ảnh AI lỗi 2 lần -> hình dự phòng (E-006 ghi vào manifest). `ags_tts.py`: Gemini qua Interactions API
  (`speech_metadata.style`, khoá ở header), mô hình `AGS_GEMINI_TTS_MODEL` hoặc mặc định `gemini-3.8-flash-tts`, ghi vào
  manifest; `ags_editorial_sub.write_ass` nhận màu riêng từng từ, màu/cỡ chữ phụ đề, nhãn "ví dụ".
- Kiểm thử: `tests/ags_test_studio.py`.
- Lát D (proof thật 24/10/2026): `validate_script` chấm câu mở bằng đúng luật hook BR-010 (`score_hook`: lời ≤ 14 từ, 6
  dấu hiệu) — hook cảnh báo / POV / trước–sau không còn bị chặn bởi luật câu mở cũ. Phụ đề + mốc đổi cảnh khớp giọng đọc
  thật: studio bật căn từ bằng faster-whisper khi mô hình `base` đã có trên máy (không tải), chữ hiện trên màn hình
  (`99k`) nhận mốc của lời đã đọc (`verify_and_align_voiceover_asr(display_text=…)`), đổi cảnh rơi giữa khoảng lặng giữa
  hai câu; thiếu ASR thì chia trong câu theo độ dài âm tiết (không chia đều). `quote --image-prompts-file` / spec proof
  `image_prompts` = 1 chủ thể ảnh AI mỗi câu (pipeline `scene_prompts`); spec proof nhận `voice_name`, `voice_speed`;
  số khai `vi-du` có trong lời đọc ⇒ nhãn "ví dụ" (kể cả số ngôi thứ ba); `proof-manifest.json` ghi `voice`, `scenes[]`
  (kèm `fallback`), `fallback_scenes`, `claims`, `image_model`.
- Sửa: `ags_blender_3d.py` nạp bộ dựng ags-reels bằng `importlib` (gói phân phối không còn import ngoài gói);
  `tests/ags_test_shield.py` không nhúng đường dẫn máy; `ags_reels_footage.py batch` thiếu `import Path`.
- Chữ căn giữa và to hơn: `SAFE_ZONE_9X16` đối xứng trái = phải = 18,5% (200 px), trên 15%, dưới 35% → hộp chữ
  [200, 288, 880, 1248], tâm x = 540 (bản cũ trái 11,1% / phải 27,8% làm chữ lệch trái). Hook 84 px (chỉ hạ tới 72 px khi
  không vừa 3 dòng); phụ đề `bt_vi` 72 px (hạ tới 63 px khi không vừa 2 dòng); nhãn "(ví dụ)" 40 px đứng đầu cụm phụ đề
  có số minh hoạ (`write_ass(label_terms=…)`, pipeline `example_terms`). Huy hiệu ✓ góc phải tắt mặc định
  (`badge_name="ags_verified_badge.png"` để bật); contact sheet không vẽ khung hồng trừ khi `--debug-zones`. Studio:
  dissolve 0,25 s; giữ phụ đề qua khoảng lặng ngắn; `fill_to_sec` chèn khoảng lặng ≤ 0,9 s giữa câu khi giọng đọc nhanh
  hơn nhịp kịch bản (không kéo giãn giọng).
- Giọng Google AI khi khoá nằm trên máy chủ riêng: `ags_tts.py --engine gemini-remote` (`AGS_GEMINI_SSH_HOST`,
  `AGS_GEMINI_SSH_ENV_FILE`): gửi chương trình qua `ssh … python3 -`, máy chủ đọc khoá trong bộ nhớ, xoay khoá khi 429,
  trả WAV qua stdout (không ghi file trên máy chủ, khoá không về máy chạy). Studio tự dùng đường này cho giọng `gemini`
  khi máy không có `GEMINI_API_KEY`; manifest ghi `voice.transport`.
- Mẫu BĐS: khung phong cách ảnh AI bối cảnh Việt Nam, cấm kiến trúc/cảnh châu Âu, Địa Trung Hải.
- Token bản quyền ghi `order_id` + `max_devices` (mặc định theo gói: creator 1, studio 2, agency 5, commercial 1);
  `verify_license_token` (sau khi kiểm chữ ký RSA trên toàn payload) trả `payload_digest` 32 byte trên đơn hàng chuẩn hoá
  `{order_id|sub, tier, vsec}` — `vsec` là bí mật theo đơn dẫn tất định từ khoá ký (HMAC-SHA256), nên digest không đoán
  được từ `order_id` công khai mà token cấp lại cho cùng đơn (exp/mid mới) vẫn mở được vault và dùng chung ghế; bản phát
  hành theo đơn niêm tài liệu bằng muối có `vsec` (`embed_origin_seal(text, vsec)` / `verify_origin_seal(root, vsec)`);
  `error_code` `E-ags-anti-rea-shield-002` khi sai.
- Vault `AGSV2`: AES-256-GCM (`cryptography`, thêm vào `requirements.txt` và bước kiểm import của `ags_setup.py`),
  nonce dẫn từ release_salt, header làm AAD; thay cho zlib + HMAC (nội dung trước đây đọc được khi bỏ qua tag).
- `scripts/ags_client_license.py`: dấu niêm nguồn gốc tài liệu (`embed_origin_seal` / `verify_origin_seal`, bỏ qua dòng
  ghi chú cài đặt) và dấu đơn hàng 3 kênh (zero-width, PNG tEXt `ags_order_id`, extra ZIP 0x4741; `verify_leak_watermark`).
  Máy chủ sổ cái lấy từ `"license_url"` trong `.protected` của gói (niêm bằng `seal_protected_marker`, sửa ->
  `ORIGIN_SEAL_MISMATCH`; `AGS_LICENSE_URL` khác rỗng thắng cho staging/thử, rỗng không tắt máy chủ): khi có,
  `activate_license_token` / vault xin lease máy chủ, lưu `vault_lease` vào `client_license.json`, 403 -> `PermissionError`
  mang `-003` (hết ghế) / `-004` (đã thu hồi); mất mạng chỉ dùng lease đã lưu (72h ngoài mạng), chưa có lease ->
  `LEASE_SERVER_UNREACHABLE`; `vault_status()` lấy `bound_devices`, `max_devices`, `lease_expires` từ lease.
- `scripts/ags_license_server.py` (phía bên bán): sổ cái SQLite theo ghế, `POST /api/v1/license/activate|lease|revoke`,
  lease `AGS-LEASE-V1` 24h + 72h ngoài mạng ký RSA bằng khoá cấp mã (`--issuer-key`, mặc định
  `~/.ags/issuer_private_key.json`); client kiểm bằng `ags_client_license.verify_cached_lease`; hết ghế `-003`, đã thu hồi `-004`.
- `ags_setup.py` nhận `-y` (như `--yes`) do `CAI-DAT-MAC.sh` / `CAI-DAT-WIN.bat` chuyển tiếp; `ags_blender_3d.py` không
  đổi lỗi bản quyền (`PermissionError` / `VaultError`) thành Canvas ở `mode=auto`.
- `scripts/ags_build_protected_client.py` (phía bên bán): `dist/ags-client-protected.zip` theo đơn hàng — rules, template
  CapCut, script bpy chỉ nằm trong `assets/vault.ags.enc`; Blender 3D tách thành add-on tuỳ chọn
  `dist/ags-blender-3d-addon.zip`; ghi `dist/provenance.json`; `--license-url` (mặc định `AGS_BUILD_LICENSE_URL` hoặc
  `https://license.agentsea.vn`, `""` = bản không máy chủ) ghi vào `.protected`. MCP `blender_3d_render` báo
  `BLENDER_ADDON_MISSING` khi chưa cài add-on.
- `bds/ags_capcut_draft.py` đọc template CapCut qua `ags_vault_loader.read_asset` (`capcut_template()`).
- Kiểm thử: `tests/ags_test_shield.py`.

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

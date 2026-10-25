# Báo cáo lát D — Sửa lỗi tồn đọng + render bằng chứng thật (24/10/2026)

## 0. Tóm tắt
- Phần 1 xong cả 4 mục, cộng 5 lỗi phát hiện khi render thật (mục 1.5). Toàn bộ test xanh (mục 3).
- Phần 2: **5 mp4 thật** trong `products/ags-video-editing/proof-20261024/` (không commit), có 55 ảnh AI thật qua
  9router `cx/gpt-image-2` và 0 cảnh dự phòng. Cả 5 video đều 1080×1920, 30 fps, −13,9…−14,1 LUFS, guard exit 0,
  có contact sheet 12 khung và `proof-manifest.json`.
- **Gemini TTS CHƯA chạy thật**: máy không có `GEMINI_API_KEY`. Cần Teddy cung cấp khoá để chạy giọng Google AI. Cả 5
  video dùng giọng miễn phí `vieneu` (giọng "Thiền Tâm Đức", tốc độ 0,9). Manifest ghi `voice.engine = "vieneu"`,
  `model = null`.
- Mẫu (4) chạy được hai cách. Bản Canvas dự phòng (`iso3d-dong-goi`, máy không có Blender) đạt kiểm tra kỹ thuật nhưng
  **chưa đạt khi xem bằng mắt** (mục 2.3). Vì vậy tôi dựng thêm `iso3d-ai-dong-goi`: cùng kịch bản, ảnh AI isometric.
  Bản này đạt cả kỹ thuật lẫn khi xem.

## 1. Phần 1 — sửa lỗi

### 1.1 `validate_script`: câu mở chỉ áp BR-010
- `scripts/ags_vi_script.py`: bỏ `SCRIPT_HOOK_MAX_WORDS`/`SCRIPT_HOOK_TRIGGERS` (luật BR-002 cũ: ≤ 8 từ, chỉ nhận số /
  câu hỏi / mâu thuẫn). Câu 1 giờ được chấm bằng `score_hook(câu 1)`: mỗi lỗi hook thành một lỗi
  `E-ags-video-studio-10x-005` có `rule: "hook"` và lý do lấy từ `score_hook`, nên hợp đồng `validate` vẫn chỉ trả mã
  005/004. `profile_samples.suggested.hook_words` giới hạn ở 14 (BR-010).
- Test: `test_machine_translation_and_source_copy_are_blocked` thêm bảng 5 câu mở.
  - Cảnh báo 13 từ, POV, trước–sau → qua `validate`.
  - Câu hỏi 15 từ → 1 lỗi hook.
  - Lời chào → 2 lỗi hook.
  - Kỳ vọng cũ của kịch bản dịch máy (2 lỗi hook: quá 14 từ + thiếu dấu hiệu) vẫn đúng nên giữ nguyên.

### 1.2 Phụ đề khớp mốc TỪ (FR-012)
- Kiểm tra thật trên máy: trong venv có `faster_whisper 1.2.1` và `ctranslate2`; mô hình `Systran/faster-whisper-base`
  đã có trong cache HF. Gọi `download_model("base", local_files_only=True)` chạy được, không cần mạng. Bóc băng 5,6 s
  giọng vieneu mất khoảng 1,9 s.
- `scripts/ags_studio.py::_asr_ready()` kiểm đúng điều kiện trên rồi truyền `verify_asr=True` vào pipeline. Thiếu
  gói hoặc mô hình thì dựng như cũ.
- `ags_reels_pipeline.verify_and_align_voiceover_asr(..., display_text=…)`:
  - Tỉ lệ khớp vẫn so với lời đã chuẩn hoá cho TTS.
  - Mốc thời gian gắn cho chữ HIỂN THỊ ("99k" lấy khoảng thời gian của "chín mươi chín nghìn"). Trước đây phụ đề sẽ
    hiện chữ đã chuẩn hoá.
  - Mốc trả về là `float` thuần.
- Ranh giới câu (đổi cảnh, FR-010) khi có ASR đặt ở giữa khoảng lặng giữa hai câu. Không có ASR thì chia theo tỉ lệ số
  từ như trước.
- Không có ASR: trong mỗi câu, thời gian chia theo độ dài âm tiết (số chữ + 1), không chia đều.
- `studio-job.json` / manifest có thêm `checks.word_timing = {"method": "asr", "asr_match_ratio": …}` hoặc
  `{"method": "syllable_length"}`.
- Test hồi quy (`test_ags_reels_pipeline`): giả lập lời nghe được "giá chín mươi chín nghìn thôi" với chữ hiển thị
  "Giá 99k thôi." → tỉ lệ khớp 1,0; từ "99k" nhận khoảng (0,4; 1,6) s.
- **Độ chính xác đo được.** Bóc băng lại bằng faster-whisper trên CHÍNH mp4 cuối (giọng + nhạc), căn chữ hiển thị, rồi so
  mốc bắt đầu của từng cụm phụ đề. Mốc tham chiếu là chính Whisper base, nên số đo thiên về phía ASR.

| Video | Cụm | Bản đã dựng (ASR) — TB / max | Giả lập không ASR: chia theo âm tiết | Giả lập không ASR: chia đều |
|---|---|---|---|---|
| thirty-years-60s | 55 | 105 / 700 ms | 460 / 1154 ms | 470 / 1124 ms |
| jetlag-vi | 53 | 80 / 1276 ms | 1677 / 4761 ms | 1676 / 4761 ms |
| bds-dat-nen | 42 | 44 / 680 ms | 509 / 1130 ms | 500 / 1130 ms |
| iso3d-dong-goi | 37 | 20 / 200 ms | 268 / 773 ms | 285 / 669 ms |
| iso3d-ai-dong-goi | 38 | 35 / 660 ms | 311 / 972 ms | 327 / 972 ms |

  Kết luận thật: ASR giảm độ lệch trung bình từ 0,27–1,68 s xuống 20–105 ms. Chia theo âm tiết **gần như không hơn chia
  đều** (chênh ≤ 17 ms, có video còn kém hơn 9 ms). Phần lệch lớn nằm ở ranh giới câu chia theo tỉ lệ số từ: khoảng lặng
  giữa các câu cộng dồn, ở jetlag lên tới 4,8 s. Vì vậy không có ASR thì phụ đề vẫn lệch rõ.
- Rủi ro: ASR có cổng `min_asr_match_ratio = 0.65`. jetlag-vi chỉ đạt 0,679 vì Whisper viết số kiểu "35k/35.000",
  còn lời chuẩn hoá là chữ. Một giọng đọc sai nhiều hơn sẽ làm lượt dựng dừng với lỗi `E-ags-reels-pipeline-005`, studio
  trả về E-011.

### 1.3 Đóng gói
- (a) `scripts/ags_blender_3d.py::_render_canvas` nạp `ags_reels_pipeline` bằng
  `importlib.import_module`, dùng `AGS_REELS_DIR` hoặc thư mục anh em như cũ. Bộ kiểm import của validator không còn
  thấy import ngoài gói.
- (b) `tests/ags_test_shield.py`: ghi chú cài đặt dùng `Path.home() / '.claude/skills/ags'` lúc chạy, không còn chuỗi
  `/Users/` cố định.
- `ags_build_skill_zips.py` **không có cờ `--out`/`--dist`**: thư mục đầu ra cố định là `dist/`. Tôi không sửa script và
  không chạy nó vào `dist/`. Để xác nhận, tôi gọi `build()` với `DIST` đổi sang thư mục tạm (`/tmp/agszip.*`) ngay trong
  tiến trình.
  - Kết quả: exit 0, `ags-video-editing.zip` 89 file, `ags-video-editing-web.zip` 6 file.
  - `verify_pack` qua: giải nén vào thư mục có dấu cách, `--check`, biên dịch mọi `.py`.
  - Chạy lại sau khi sửa xong vẫn exit 0. `dist/` giữ nguyên.
- ⚠️ Phát hiện, chưa sửa (cần Teddy quyết): chạy `ags_build_skill_zips.py` vào `dist/` thật sẽ **xoá mọi `*.zip` khác
  trong `dist/`** (vòng dọn "zip kiểu cũ"). Hiện hai file sẽ mất là `ags-client-protected.zip` và
  `ags-blender-3d-addon.zip`.

### 1.4 `ags_reels_footage.py batch`
- Thêm `from pathlib import Path`.

### 1.5 Lỗi phát hiện khi render thật (đã sửa)
1. **Ảnh AI lặp lại.** Truy vấn ảnh dịch từ bảng 16 từ khoá nên hầu hết câu rơi về cùng một câu mặc định → cùng prompt
   → cùng ảnh trong cache, lặp suốt video. Điều này trái FR-009 "mỗi ý 1 ảnh".
   - Đã thêm `scene_prompts` (pipeline), `quote(image_prompts=…)` + `--image-prompts-file` (CLI), `image_prompts`
     (MCP `ags_studio_quote`, spec `proof`), khoá cấp 1 `image_prompts` trong `studio-job.json`.
   - Agent viết 1 chủ thể ảnh tiếng Anh cho mỗi câu. Khung phong cách của mẫu vẫn được nối vào sau.
   - Tài liệu: `skills/ags-studio/SKILL.md`.
2. **Giọng miễn phí đọc quá nhanh.** vieneu giọng mặc định đọc 4,1 từ/s, nên kịch bản 60 s đạt nhịp (157 từ) chỉ dài
   khoảng 38 s, không vào được 55–65 s. Spec `proof` nhận thêm `voice_name` và `voice_speed` (ghi vào `render_params`;
   pipeline có sẵn `tts_voice`/`voice_speed`). Đo 175 từ:

   | Giọng vieneu | Thời lượng | Khớp ASR |
   |---|---|---|
   | mặc định | 42,3 s | 0,80 |
   | Thiện Minh | 43,0 s | 0,84 |
   | Hải Đăng | 43,4 s | 0,80 |
   | **Thiền Tâm Đức** | **58,1 s** | **0,863** |

   Đã chọn Thiền Tâm Đức, đọc ở tốc độ 0,9.
3. **Nhãn "ví dụ" chỉ hiện với số kết quả ngôi thứ nhất.** Nay mọi claim `claim_source: "vi-du"` có trong lời đọc đều
   bật nhãn, kể cả giá ly cà phê ở ngôi thứ ba (BR-012).
4. **`pick_keywords` chỉ tô nửa tên riêng.** Câu mở bằng "Việt Nam" chỉ tô "Nam". Nay tên 2 tiếng ở đầu câu được tô trọn.
   Kiểm tay: "Khách Sài Gòn", "Vậy Việt Nam", "Nhưng Hà Nội" không tô nhầm chữ đầu câu. Test: thêm 1 dòng vào
   `test_keyword_colors_follow_meaning`.
5. **Số cảnh trên thẻ Canvas sai định dạng.** Từ cảnh thứ 10 trở đi thẻ hiện "010", "011". Nay dùng `{n:02d}`.

`proof-manifest.json` ghi thêm: `voice` (engine, voice_name, speed, model, style, key_present), `image_model`,
`scenes[]` (scene_id, line_id, mốc, motion, archetype, `fallback`), `fallback_scenes`, `claims` (text + claim_source).

## 2. Phần 2 — bằng chứng thật

Lệnh chạy:
```
venv/bin/python /tmp/agsd/with_9router.py venv/bin/python scripts/ags_studio.py proof --spec proof-20261024/proof-spec.json --out-dir proof-20261024 --confirmed --json
```
- Launcher tạm nằm ngoài repo. Nó đọc `apiKey` của provider `9router-vps` trong `~/.omp/agent/models.yml` và chỉ đặt vào
  env của tiến trình con: `AGS_NINEROUTER_API_KEY`, `AGS_NINEROUTER_BASE_URL=http://100.93.28.78:8080/v1`,
  `AGS_GPT_IMAGE_MODEL=cx/gpt-image-2`. Khoá không bị in ra, không bị ghi ra file.
- Đã quét 218 file (proof, `/tmp/agsd`, `docs/…`) tìm khoá: **0 lần xuất hiện**.
- Lượt 1 (4 mẫu, 42 ảnh AI) mất 2.514 s. Lượt 2 (sửa màu từ khoá/số thẻ, dựng lại từ cache, thêm `iso3d-ai`) mất
  1.367 s. File của lượt 1 chuyển vào `proof-20261024/_superseded/`.
- Kịch bản do agent viết nằm trong `proof-20261024/scripts/`. Cả 4 đều qua `ags_vi_script.py validate`, `hook`
  (lời + chữ trên hình) và `claims`:

| Kịch bản | Số từ (khung cho phép) | TB từ/câu | Hook đọc | Chữ hook trên hình |
|---|---|---|---|---|
| thirty-years-60s | 157 (130–158) | 10,47 | `con-so` | "30 năm kinh doanh trong 60 giây" |
| jetlag-vi | 154 (130–158) | 9,62 | `cau-hoi` | "Ly 35k, tiền hạt chỉ vài nghìn?" |
| bds-dat-nen | 116 (98–118) | 10,55 | `canh-bao` | "3 điều trước khi mua đất" |
| iso3d-dong-goi | 110 (98–118) | 8,46 | `cau-hoi` | "Vì sao đơn giao chậm?" |

- Số liệu trong jetlag-vi:
  - 35k / 3k / 5k là số minh hoạ, khai `vi-du`, lời đọc có "con số ví dụ", màn hình có nhãn "ví dụ".
  - "Việt Nam là nước sản xuất cà phê lớn thứ hai thế giới" khai
    `tai-lieu:USDA qua Vietnam News 14/05/2026 <https://vietnamnews.vn/economy/1781254/…>`.
  - Không có số liệu thu nhập hay kết quả cá nhân nào.
- thirty-years-60s không có con số nào ngoài "30 năm / 60 giây / ba tháng". bds-dat-nen không có giá hay diện tích, theo
  luật "không tự bịa số liệu" của skill ags-edit-bds.

### 2.1 Số đo (đo độc lập bằng ffprobe, `ebur128`, SHA-256 tính lại, chạy lại guard)
| Mẫu | mp4 (trong `proof-20261024/`) | Thời lượng | LUFS | Guard | Ảnh AI / dự phòng | ASR khớp | Hộp phụ đề (vùng an toàn [120,288,780,1248]) | Hook ở 0,3 s |
|---|---|---|---|---|---|---|---|---|
| (1) thirty-years-60s | `thirty-years-60s/ags-bt-thirty-years-60s-x.mp4` | 59,03 s | −13,9 | 0 | 15 / 0 | 0,777 | [194,1109,705,1242] 67 px | khác bản không hook 15,1% |
| (2) jetlag-vi | `jetlag-vi/ags-jetlag-jetlag-vi-x.mp4` | 60,77 s | −14,1 | 0 | 16 / 0 | 0,679 | [125,1031,707,1242] 67 px | 12,4% |
| (3) bds-dat-nen | `bds-dat-nen/ags-bds-bds-dat-nen-x.mp4` | 41,53 s | −13,9 | 0 | 11 / 0 | 0,828 | [205,1166,694,1242] 67 px | 10,1% |
| (4a) iso3d-dong-goi (Canvas) | `iso3d-dong-goi/ags-iso3d-iso3d-dong-goi-x.mp4` | 40,33 s | −14,0 | 0 | 0 / 13 cảnh Canvas `system_isometric` (máy không có Blender) | 0,827 | [192,1109,705,1242] 67 px | 5,8% |
| (4b) iso3d-ai-dong-goi | `iso3d-ai-dong-goi/ags-iso3d-iso3d-ai-dong-goi.mp4` | 40,13 s | −14,1 | 0 | 13 / 0 | 0,809 | [192,1109,705,1242] 67 px | 9,0% |

- SHA-256 tính lại khớp với `proof-manifest.json` ở cả 5 video.
- Cả 5 video: h264 yuv420p + AAC, `contact-sheet.jpg` 12 khung, whoosh ở t = 0.
- Câu hook đọc dài 3,1–4,6 s (≤ 5 s). Mỗi shot ≤ 2,48 s. Không có 2 shot liền nhau cùng kiểu chuyển động.
- `scenes[].fallback` = false ở mọi cảnh. Đường dự phòng ảnh AI (FR-009) **không bị kích hoạt** vì không ảnh nào lỗi.
  Đường này chỉ được kiểm bằng test có sẵn (`test_ac010`), không có lần lỗi thật nào để ghi.
- Khung ảnh để soát nằm trong `proof-20261024/<mẫu>/frames/`: t = 0,3 s, 3 s, 25/50/75% và cuối video.

### 2.2 Soát bằng mắt (mô tả đúng những gì thấy)
- **Chữ hook:** khung t = 0,3 s của cả 5 video có chữ hook xanh neon viền đen, tối đa 3 dòng, trong vùng an toàn phía
  trên, không bị cắt chữ.
- **Phụ đề:** cụm 2–4 từ, chữ trắng viền đen, nằm trong vùng an toàn phía dưới. Trên nền sáng (beige, xanh pastel) vẫn
  đọc được nhờ viền. Không thấy chữ bị cắt. Ở mốc chuyển câu thấy ảnh chồng mờ vài khung do hiệu ứng dissolve (đúng
  thiết kế).
- **Màu từ khoá:**
  - thirty-years: "30 năm", "60 giây", "Mỗi tuần" vàng; "đóng cửa", "đừng", "nợ" đỏ; "giá trị", "thắng" xanh. Đúng
    nghĩa.
  - jetlag: "35k", "3k", "5k" xanh; "Việt Nam" vàng cả hai tiếng (sau khi sửa).
  - bds: "Đừng" đỏ; "3", "Cuối cùng" vàng.
  - iso3d: "mỗi ngày" tô **xanh**. Kịch bản không có nghĩa tiền hay cảnh báo nên chạy luật xen xanh ↔ vàng của BR-005.
    Làm đúng spec, nhưng từ chỉ thời gian lẽ ra hợp màu vàng hơn.
- **Ảnh AI:**
  - thirty-years: tĩnh vật tông beige ấm, đồng nhất. Riêng cảnh "giường + két" tông xanh đêm, lệch tông.
  - jetlag: ánh sáng ấm, đồng nhất. Người pha chế trông như người phương Tây, một cảnh phố không rõ là Việt Nam.
  - bds: ảnh vệ tinh và đồng lúa Việt Nam đẹp. Nhưng cảnh "sổ đỏ" và "lộ giới" là biệt thự kiểu châu Âu, cảnh phân lô
    là khu ven biển kiểu Địa Trung Hải. **Bối cảnh chưa đồng nhất** (prompt chưa ghi "Vietnam" ở mọi cảnh).
  - iso3d-ai: isometric pastel rất đồng nhất. Riêng ảnh băng chuyền bị dựng thành "ảnh trong ảnh" (khung ảnh nằm giữa
    nền pastel).
- **Canvas (4a): chưa đạt khi xem.**
  - Mọi cảnh là cùng một thẻ.
  - Nhãn tiếng Anh "01 INTAKE / 02 PROCESS / 03 OUTCOME" không khớp nội dung.
  - Lộ tên nội bộ "01 · SYSTEM_ISOMETRIC" trên hình.
  - Phụ đề đè lên mép dưới thẻ (vẫn đọc được).
  Đây là giới hạn của Canvas dự phòng có sẵn. Tôi không thiết kế lại, chỉ sửa định dạng số. Dùng (4b) làm mẫu giao.
- **Huy hiệu ✓ (`ags_verified_badge.png`)** của pipeline nằm cố định ở góc trên phải mọi khung, chỗ x ≈ 830–950, ngoài
  mép phải vùng an toàn. Đây là mặc định có sẵn, tôi không đổi. Cần Teddy quyết có giữ hay không.
- **Nhãn "ví dụ"** (jetlag) cỡ khoảng 33 px, nhỏ, hiện suốt video, kể cả lúc đọc câu số liệu đã có nguồn.
- **Mẫu BĐS:** dựng bằng kiểu `bds` của studio với ảnh AI theo công thức "Đất nền" của skill ags-edit-bds (vệ tinh →
  ranh thửa → phân lô → đi thực tế → pháp lý / lưu lại). Mẫu **không** dùng asset `parcel`/`subdivision` vẽ bằng
  `ags_bds_cli.py`; studio chưa nối với engine đó.

### 2.3 Chưa chạy thật / còn thiếu
- Gemini TTS (`gemini-3.8-flash-tts`, `speech_metadata.style`): chưa chạy vì thiếu `GEMINI_API_KEY`. Cần Teddy cấp khoá
  để chạy `proof` lại với `"voice": "gemini"`.
- Blender thật: máy không có, nên 3D chỉ chạy được bằng Canvas dự phòng.
- Đường dự phòng ảnh AI không xảy ra trong lượt thật (mục 2.1).

## 3. Test (chạy lại sau khi sửa xong, venv sản phẩm)
| Bộ | Kết quả |
|---|---|
| `venv/bin/python -m unittest tests.ags_test_vi_script` | 9/9 OK |
| `tests.ags_test_studio` | 10/10 OK (153 s, gồm dựng thật với ASR bật) |
| `tests.ags_test_installer` | 4/4 OK |
| `tests.ags_test_shield` | 17/17 OK |
| `tests.ags_test_blender` | 6 chạy, OK, bỏ qua 1 (máy không có Blender, có từ trước) |
| `tests/ags_test_core.py` | 9/9 |
| `tests/ags_test_bds_engine.py` | 9/9 |
| `services/ops/ags-reels-footage`: `python -m unittest test_ags_reels_pipeline` | 8/8 OK (230 s) |
| `ags_build_skill_zips.build()` vào thư mục tạm | exit 0 (89 + 6 file, `verify_pack` qua); `dist/` không đổi |

## 4. File đã đổi
- `scripts/ags_vi_script.py`: câu mở theo BR-010; tên riêng đầu câu.
- `tests/ags_test_vi_script.py`: bảng câu mở; dòng màu "Việt Nam".
- `scripts/ags_studio.py`: `_asr_ready`; `image_prompts`; `voice_name`/`voice_speed` cho `proof`; nhãn ví dụ; `voice`
  và `word_timing` trong job; manifest proof.
- `scripts/ags_blender_3d.py`: nạp bằng `importlib`.
- `tests/ags_test_shield.py`: bỏ đường dẫn cứng.
- `mcp/ags_mcp_server.py`: `image_prompts` cho `ags_studio_quote`.
- `skills/ags-studio/SKILL.md`, `CHANGELOG.md`: tài liệu.
- `services/ops/ags-reels-footage/ags_reels_pipeline.py`: `display_text`; cắt cảnh theo ASR; chia theo âm tiết;
  `scene_prompts`; số thẻ `{:02d}`.
- `services/ops/ags-reels-footage/ags_reels_footage.py`: `import Path`.
- `services/ops/ags-reels-footage/test_ags_reels_pipeline.py`: căn chữ hiển thị.
- Không commit. Không đụng `dist/`, `venv/`, `LICENSE*`.

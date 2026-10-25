---
type: srs
feature: "ags-video-studio-10x"
status: in-review
version: 1.0.0
owner: "@ags-ba"
updated: 2026-10-24
links:
  - srs/user-flow.md
  - ascii-screen/main.md
  - html-design/prototype.html
  - api/api-map.md
  - userstories/us-001.md
changelog:
  - "2026-10-24 | /init | Khởi tạo tài liệu chuẩn AGS-BA"
  - "2026-10-24 | ba | Điền đầy đủ SRS từ handoff 01a16c71 (Teddy chốt)"
---

# Đặc Tả Yêu Cầu Phần Mềm — AGS Video Studio 10x

> **Mục tiêu kinh doanh (hũ 3 — cắt giờ & chi phí):** khách không biết kỹ thuật nói 1 câu bằng lời thường trên Claude Code / Codex / Antigravity / Cursor → nhận video 9:16 thành phẩm + ảnh lưới duyệt bằng mắt, sửa bằng lời thường. Vượt OmniReel & ReelCrew ở 3 điểm: (1) AI hỏi ngược dẫn dắt + báo chi phí trước khi chạy, (2) mẫu ăn tiền Business Thinking / Jetlag Việt hoá 100%, (3) có bằng chứng render thật cho từng mẫu.
> **Nền đã có (KHÔNG làm lại):** `ags_reels_pipeline.py::run_one_prompt_reels_pipeline` (TTS, karaoke ASS, safe zone, AI B-roll `cx/gpt-image-2`, LUT, `-14 LUFS`), `ags_tts.py` (`--engine gemini`, chuẩn hoá số), `ags_editorial_sub.py`, `ags_anti_slop_guard.py`, `ags_client_license.py`, `scripts/ags_setup.py --install-all-clients`.
> **Phạm vi đụng tới:** `products/ags-video-editing/` (skill, preset, hướng dẫn, validator) và `services/ops/ags-reels-footage/` (preset dispatch trong pipeline).

## 1. Tổng quan Hệ thống & Phạm vi Tính năng

| Mã ID | Tham chiếu Nguồn | Nội dung Đặc tả | Điều kiện / Ràng buộc | Ưu tiên |
|---|---|---|---|---|
| `FR-ags-video-studio-10x-001` | `UR-ags-video-studio-10x-001` | Hệ thống gồm 4 khối: (A) Hỏi ngược dẫn dắt + bảng chọn món, (B) Preset Việt hoá `business-thinking-60s` và `jetlag-vi`, (C) Hình ảnh AI + chuyển động + giọng Gemini TTS, (D) Phụ đề chuẩn vùng an toàn 9:16 + màu từ khoá. | Mọi khối chạy cục bộ trong bản `ags-client-protected`; chỉ ảnh AI và Gemini TTS gọi dịch vụ ngoài. | `P0` |
| `FR-ags-video-studio-10x-002` | `UR-ags-video-studio-10x-001` | Phạm vi KHÔNG làm: không sinh video bằng mô hình text-to-video bên ngoài (chưa có nhà cung cấp được duyệt); "video AI" = ảnh AI + chuyển động Ken Burns/parallax/wipe dựng bằng ffmpeg. | Thêm nhà cung cấp T2V cần Teddy duyệt riêng (OQ-001, đã chốt). | `P0` |

## 2. Yêu cầu Chức năng Chi tiết

| Mã ID | Tham chiếu Nguồn | Nội dung Đặc tả | Điều kiện / Ràng buộc | Ưu tiên |
|---|---|---|---|---|
| `FR-ags-video-studio-10x-003` | `UR-ags-video-studio-10x-001` | **Bảng chọn món**: đầu `SKILL.md`, `README.md`, `HUONG-DAN-SU-DUNG.md` có bảng "Anh/chị muốn gì → nói câu nào → ra gì" cho ≥ 8 món theo ý tưởng/ngành (BĐS, F&B, giáo dục, y tế–làm đẹp, thương mại điện tử, tư duy kinh doanh, du lịch, dịch vụ B2B). | Mỗi dòng có câu mẫu 1 câu, không thuật ngữ kỹ thuật. Lỗi thiếu bảng: `E-ags-video-studio-10x-001`. | `P0` |
| `FR-ags-video-studio-10x-004` | `UR-ags-video-studio-10x-001` | **Hỏi ngược dẫn dắt**: lệnh `ags_studio.py intake` trả đúng 3 câu hỏi ngắn theo thứ tự: (1) Ngành/chủ đề gì? (2) Phong cách mẫu nào (liệt kê preset)? (3) Giọng đọc miễn phí trên máy (`synth`/`vieneu`) hay Google AI / Gemini TTS? Câu đã được khách nêu trong yêu cầu đầu thì bỏ qua, không hỏi lại. | Tối đa 3 câu/lượt; câu trả lời không hợp lệ → hỏi lại đúng câu đó kèm lựa chọn. Mã lỗi `E-ags-video-studio-10x-002`. | `P0` |
| `FR-ags-video-studio-10x-005` | `UR-ags-video-studio-10x-001` | **Báo chi phí trước khi chạy**: sau 3 câu, `ags_studio.py quote` in bảng chi phí ước tính (số ảnh AI × đơn giá, ký tự Gemini TTS, thời gian render ước tính) bằng VND/lời thường và CHỜ khách trả lời "chạy" mới render. | Không render, không gọi dịch vụ ngoài khi chưa có xác nhận. Giọng miễn phí + ảnh stock/archetype = "0 đồng". `E-ags-video-studio-10x-003` nếu chạy khi chưa xác nhận. | `P0` |
| `FR-ags-video-studio-10x-006` | `UR-ags-video-studio-10x-002` | **Preset `business-thinking-60s`**: nhận chủ đề hoặc link/bài tham khảo từ fanpage Business Thinking ("30 years of business thinking in 60 seconds") → kịch bản 60 giây (±5 s) gồm hook ≤ 8 từ + 5–7 ý + CTA, văn phong kinh doanh Việt Nam. | Chỉ nhận ý tưởng/cấu trúc; xem BR-003. Lỗi nguồn: `E-ags-video-studio-10x-004`. | `P0` |
| `FR-ags-video-studio-10x-007` | `UR-ags-video-studio-10x-002` | **Preset `jetlag-vi`**: nhận chủ đề/link từ kênh Jetlag → kịch bản kể chuyện–giải thích (45–75 s) Việt hoá 100%, ví dụ/đơn vị tiền/địa danh đổi sang bối cảnh Việt Nam. | Như FR-006. | `P0` |
| `FR-ags-video-studio-10x-008` | `UR-ags-video-studio-10x-002` | **Trình kiểm kịch bản Việt hoá** `ags_vi_script.py validate`: chấm kịch bản theo BR-001/BR-002 và trả danh sách lỗi cụ thể từng câu; agent (Claude/Codex/…) viết lại tới khi đạt. | Là hàm tất định, không gọi mạng. `E-ags-video-studio-10x-005`. | `P0` |
| `FR-ags-video-studio-10x-009` | `UR-ags-video-studio-10x-003` | **Ảnh AI đồng nhất phong cách**: mỗi ý sinh 1 ảnh qua `cx/gpt-image-2` (9router) với khung prompt phong cách preset (tối giản, sang trọng, ẩn dụ thị giác, 1 chủ thể, nền đơn sắc, chừa vùng an toàn cho chữ), cố định "style seed" văn bản trong cả video. | Ảnh lỗi/không qua `verify_broll_clip_visuals` → thử lại 1 lần rồi dùng archetype dự phòng và ghi vào manifest. `E-ags-video-studio-10x-006`. | `P0` |
| `FR-ags-video-studio-10x-010` | `UR-ags-video-studio-10x-003` | **Chuyển động & chuyển cảnh**: mỗi ảnh thành clip 1080×1920 30 fps bằng 1 trong `push_in`, `pull_out`, `pan_left`, `pan_right`, `parallax`; không lặp 2 cảnh liền nhau cùng kiểu; đổi cảnh ≤ 3 s (BR-011); chuyển cảnh `dissolve`/`wipe` rơi đúng mốc câu của giọng đọc. | Dùng ffmpeg (đã có). Tổng độ dài khớp giọng đọc ±0,3 s. | `P0` |
| `FR-ags-video-studio-10x-011` | `UR-ags-video-studio-10x-003` | **Giọng Google AI / Gemini TTS tiếng Việt** với `--engine gemini`, chuẩn hoá số đọc (`99k`, `1,9tr`, `60 giây`, `30 năm`, `40%`). | Thiếu khoá Gemini → tự báo rõ và đề nghị giọng miễn phí, không đổi giọng âm thầm. `E-ags-video-studio-10x-007`. | `P0` |
| `FR-ags-video-studio-10x-012` | `UR-ags-video-studio-10x-004` | **Phụ đề chuẩn kênh**: preset `bt_vi` — nhảy theo cụm 2–4 từ khớp mốc từ của giọng đọc, font đậm hiện đại (Bricolage Grotesque ưu tiên, dự phòng Be Vietnam Pro), chữ trắng viền đen, căn giữa theo tâm màn hình (x = 540), cỡ ưu tiên 6,7% cạnh ngắn (72 px) khi vừa 2 dòng, chỉ hạ tới 5,8% (≥ 62 px); chữ hook ≥ 84 px, tối đa 3 dòng, chỉ hạ tới 72 px khi không vừa; nằm trong `SAFE_ZONE_9X16` (BR-006). *(Sửa 24/10/2026: chữ cũ 62–67 px, hook 66 px quá nhỏ khi xem trên điện thoại.)* | Không đè lên vùng giao diện Reels/TikTok. `E-ags-video-studio-10x-008`. | `P0` |
| `FR-ags-video-studio-10x-013` | `UR-ags-video-studio-10x-004` | **Tô màu từ khoá tự động** theo BR-005 (3 màu có nghĩa); nối bước chọn từ khoá vào pipeline (hiện `ags_reels_pipeline.py` truyền `keywords=()` nên chưa tô tự động); khách đổi màu bằng lời thường ("đổi sub sang vàng"). | Tối đa 1 từ khoá nổi bật mỗi cụm; số/tiền/% luôn ưu tiên. | `P0` |
| `FR-ags-video-studio-10x-014` | `UR-ags-video-studio-10x-005` | **Ảnh lưới xem trước** `contact-sheet.jpg` (≥ 12 khung đều theo thời gian, có mốc giây) xuất cùng mp4; khách duyệt bằng mắt. | Xuất kể cả khi chạy giọng/ảnh miễn phí. `E-ags-video-studio-10x-009`. | `P0` |
| `FR-ags-video-studio-10x-015` | `UR-ags-video-studio-10x-005` | **Sửa bằng lời thường**: `ags_studio.py revise --say "<câu>"` ánh xạ câu tiếng Việt sang tham số (màu sub, cỡ chữ, tốc độ giọng, đổi cảnh N, đổi giọng, bỏ/thêm CTA), chỉ render lại phần bị ảnh hưởng. | Câu không hiểu → hỏi lại 1 câu kèm 3 gợi ý; không đoán. `E-ags-video-studio-10x-010`. | `P1` |
| `FR-ags-video-studio-10x-016` | `UR-ags-video-studio-10x-006` | **Bằng chứng thực tế**: `ags_studio.py proof` render đủ 3 nhóm mẫu → ≥ 4 file `.mp4` (Business Thinking, Jetlag, BĐS, Editorial/Isometric 3D) 1080×1920, 30 fps, `-14 LUFS` ±1, cùng `contact-sheet.jpg` và `proof-manifest.json` (SHA-256, thông số ffprobe, exit của anti-slop guard). | Mọi mp4 qua `ags_anti_slop_guard.py` exit `0`. `E-ags-video-studio-10x-011`. | `P0` |
| `FR-ags-video-studio-10x-017` | `UR-ags-video-studio-10x-001` | **Cài 1 chạm**: `--install-all-clients` hiện có phải nạp được skill mới (bảng chọn món + lệnh `ags_studio.py`) vào Claude Code, Codex, Antigravity, Cursor; bản `dist/ags-client-protected.zip` đóng lại gồm phần mới và vẫn qua niêm phong/giấy phép. | Test installer hiện có (3/3) và shield (17/17) vẫn PASS. | `P0` |
| `FR-ags-video-studio-10x-018` | `UR-ags-video-studio-10x-007` | **Thư viện 8 loại hook tiếng Việt** `config/hooks-vi.json`: nỗi đau · nghịch lý/sự thật gây sốc · hứa kết quả cụ thể · câu hỏi mở · cảnh báo · trước–sau · POV · nửa câu/preview-flash. Mỗi loại có khung điền chỗ trống, 3 ví dụ KHÔNG chứa số liệu cá nhân thật (BR-012). `ags_vi_script.py hook` sinh/chấm hook theo BR-010. | Hook chỉ nhận loại hợp lệ; `E-ags-video-studio-10x-012`. | `P0` |
| `FR-ags-video-studio-10x-019` | `UR-ags-video-studio-10x-007` | **Hook hiện ngay frame 0**: chữ hook ≤ 8 từ bật ở 0,0–0,5 s (preset `highlight_hook` hiện có), âm "whoosh" từ `ags_sfx` ở t=0 (tuỳ chọn, mặc định bật), tuỳ chọn preview-flash 0,5–1,0 s của cảnh đắt nhất trước khi vào thân bài. | Hook không che vùng an toàn; không dùng âm có bản quyền ngoài bộ Kenney CC0. | `P0` |
| `FR-ags-video-studio-10x-020` | `UR-ags-video-studio-10x-002` | **Hiệu chỉnh theo mẫu thật của khách**: khách dán 1–5 link/văn bản mẫu → `ags_vi_script.py profile` chỉ đo số từ/giây, độ dài câu, độ dài hook, loại hook, số nhóm ý (KHÔNG tải hay dùng lại hình/tiếng gốc), rồi đề xuất tham số cho mẫu series. | URL qua kiểm SSRF (NFR-002); trùng nguồn > 8 từ liên tiếp → `E-ags-video-studio-10x-004`. | `P1` |
| `FR-ags-video-studio-10x-021` | `UR-ags-video-studio-10x-002` | **6 mẫu series có beat-sheet** `config/formats-vi.json`: (1) `thirty-years-60s` — "N năm kinh nghiệm trong 60 giây" chuỗi 5–7 nguyên tắc đối lập; (2) `sai-lam-90` — cảnh báo 3 sai lầm + cách sửa; (3) `truoc-sau` — trước–sau có con số của khách; (4) `nghich-ly` — hot take có lập luận; (5) `pov` — tình huống người xem; (6) `jetlag-vi` — kể chuyện–giải thích "thế giới vận hành" có con số/bản đồ. Mỗi mẫu: ngân sách giây theo khối (hook / thân / chốt / CTA), số cảnh, kiểu chuyển động ưu tiên, màu từ khoá mặc định. `business-thinking-60s` = bí danh của (1). | Mẫu phải qua BR-001/002/010/012 khi chạy. | `P0` |
| `FR-ags-video-studio-10x-022` | `UR-ags-video-studio-10x-007` | **Kết vòng lặp + CTA mềm**: câu cuối gọi lại ý hook; CTA ≤ 10 từ ưu tiên hành động nhẹ ("Lưu lại để áp dụng", "Gửi cho người cần"); CTA bán hàng chỉ khi khách bật. | Theo BR-011. | `P1` |
| `FR-ags-video-studio-10x-023` | `UR-ags-video-studio-10x-007` | **3 biến thể hook (A/B)** cho cùng video: render 3 bản chỉ khác 3 giây đầu (khác loại hook, dùng lại cảnh/giọng thân bài), xuất `variants/` + bảng gợi ý đo giữ-chân-giây-đầu (<40% sửa lớn, 40–55 trung bình, 55–70 tốt, ≥70 rất tốt — mốc tham khảo của blog bên thứ ba, KHÔNG cam kết). | Chỉ khi khách yêu cầu "làm 3 bản thử"; báo chi phí thêm trước (FR-005). | `P1` |
| `FR-ags-video-studio-10x-024` | `UR-ags-video-studio-10x-003` | **Giọng Gemini có chỉ dẫn phong cách**: gửi kèm chỉ dẫn nhịp/giọng theo mẫu (ví dụ "đanh, chắc, nhấn con số, nhịp nhanh vừa") qua tham số phong cách của API; mô hình mặc định đọc từ `AGS_GEMINI_TTS_MODEL`, và `proof` phải chạy thật với mô hình hiện hành (tài liệu Google ghi `gemini-3.8-flash-tts`; mặc định cũ `gemini-2.5-flash-preview-tts`) và ghi mô hình đã dùng vào manifest. | Lỗi mô hình → `E-ags-video-studio-10x-014`, không tự đổi giọng. | `P1` |

## 3. Quy tắc Nghiệp vụ & Công thức Tính toán

| Mã ID | Tham chiếu Nguồn | Nội dung Đặc tả | Điều kiện / Ràng buộc | Ưu tiên |
|---|---|---|---|---|
| `BR-ags-video-studio-10x-001` | `UR-ags-video-studio-10x-002` | **Việt hoá thật, không dịch từng chữ**: mỗi câu ≤ 16 từ (trung bình ≤ 11); tỉ lệ từ không phải tiếng Việt (trừ danh từ riêng/viết tắt trong danh sách cho phép) ≤ 3%; cấm cấu trúc dịch máy trong danh sách `CALQUE_PATTERNS` ("là một trong những", "chính là việc", "nó là", "bạn có thể" ≥ 2 lần/kịch bản…). | Vi phạm → `E-ags-video-studio-10x-005`, kèm câu và lý do. | `P0` |
| `BR-ags-video-studio-10x-002` | `UR-ags-video-studio-10x-002` | **Nhịp đọc**: số từ mục tiêu = `thời_lượng_giây × 2,4` (≈ 144 từ/phút ±10%); 60 s ⇒ 130–158 từ. Câu mở đầu của kịch bản chính là hook và theo BR-010 (không có luật hook riêng ở BR-002). Kết bằng 1 CTA ≤ 10 từ. Số/tiền viết theo dạng chuẩn hoá được (`99k`, `1,9tr`). | Sai nhịp → `E-ags-video-studio-10x-005`. | `P0` |
| `BR-ags-video-studio-10x-003` | `UR-ags-video-studio-10x-002` | **Nguồn tham khảo & bản quyền**: link Business Thinking/Jetlag chỉ để học chủ đề + cấu trúc ý. CẤM dùng lại hình/clip/âm thanh gốc; CẤM chép nguyên văn quá 8 từ liên tiếp (kiểm bằng n-gram với văn bản nguồn nếu có). Manifest ghi `source_url` và `transcreated=true`. | Vi phạm → `E-ags-video-studio-10x-004`, không render. | `P0` |
| `BR-ags-video-studio-10x-004` | `UR-ags-video-studio-10x-003` | **Chi phí báo trước** = `số_ảnh_AI × giá_ảnh + ký_tự_TTS × giá_ký_tự`; đơn giá đọc từ `config/pricing.json` (người bán sửa được), không có đơn giá → hiển thị "chưa có bảng giá" và vẫn bắt xác nhận. Giọng miễn phí và `broll_mode=archetype/stock` = 0. | Làm tròn lên 1.000 đ. | `P0` |
| `BR-ags-video-studio-10x-005` | `UR-ags-video-studio-10x-004` | **Chọn & tô màu từ khoá theo nghĩa** (ngữ pháp 3 màu): xanh `#A8FF3E` = tiền/lợi nhuận/thắng/kết quả tốt; vàng `#FFD166` = nhấn mạnh, số, thời gian; đỏ `#FF5A5F` = cảnh báo/sai lầm/mất mát. Ưu tiên (1) số/tiền/%/thời gian, (2) từ trong `config/keywords-vi.json` (kèm nhãn màu), (3) danh từ riêng; không tô từ chức năng; tối đa 1 từ/cụm 2–4 từ; không dùng cùng màu 2 cụm liên tiếp trừ khi nghĩa giống nhau. Chủ đề không có nghĩa tiền/cảnh báo → xen xanh ↔ vàng như yêu cầu ban đầu. | Tương phản chữ–nền ≥ 4,5:1 nhờ viền đen. | `P0` |
| `BR-ags-video-studio-10x-006` | `UR-ags-video-studio-10x-004` | **Vùng an toàn 9:16 = dùng lại `SAFE_ZONE_9X16` trong `ags_common.py` (trái 18,5% = 200 px, phải 18,5% = 200 px, trên 15% ≈ 288 px, dưới 35%), KHÔNG định nghĩa số mới ở nơi khác.** Sửa 24/10/2026: bản cũ bất đối xứng (trái 11,1%, phải 27,8% theo cột nút TikTok TopView) làm tâm hộp chữ nằm ở x ≈ 450/1080 → người xem thấy chữ lệch trái; đổi sang lề đối xứng theo mẫu chung 3 nền tảng (đối chiếu Clipzi, Meta Reels, TikTok, YouTube Shorts) để chữ căn giữa x = 540. Đã đối chiếu: Meta Reels chừa trên 14%, dưới 35%, hai bên 6%; mẫu chung 3 nền tảng dòng chữ cuối kết thúc trên y≈1240/1920. Khung chữ nằm trọn trong vùng, tối đa 2 dòng, cỡ chữ ≥ 5,8% cạnh ngắn (≥ 62 px ở 1080). | Chạm ngoài vùng → `E-ags-video-studio-10x-008`. | `P0` |
| `BR-ags-video-studio-10x-007` | `UR-ags-video-studio-10x-005` | **Sửa bằng lời thường** chỉ đổi tham số trong whitelist (`sub_color`, `sub_size`, `voice_engine`, `voice_speed`, `scene_swap`, `cta_text`); mọi thay đổi ghi vào `revisions[]` của manifest. | Không cho câu lệnh sinh shell tự do. | `P1` |
| `BR-ags-video-studio-10x-008` | `UR-ags-video-studio-10x-006` | **Đạt chuẩn video**: 1080×1920, 30 fps, h264 yuv420p, AAC, độ ồn −14 LUFS ±1, thời lượng khớp giọng ±0,3 s, không khung đen > 0,2 s. | Sai → `E-ags-video-studio-10x-011`. | `P0` |
| `BR-ags-video-studio-10x-009` | `UR-ags-video-studio-10x-001` | **Giấy phép**: mọi lệnh mới gọi `assert_client_licensed()` như pipeline hiện có; không thêm đường tắt bỏ qua giấy phép; không ghi khoá/bí mật vào manifest hay log. | Vi phạm = chặn nghiệm thu. | `P0` |
| `BR-ags-video-studio-10x-010` | `UR-ags-video-studio-10x-007` | **Chấm hook**: lời nói ≤ 14 từ (≈ 6 s ở 2,4 từ/giây; Reels trung vị 14 từ), chữ trên màn hình ≤ 8 từ và hiện trong ≤ 0,5 s đầu; PHẢI có ≥ 1 trong: con số cụ thể, câu hỏi, mâu thuẫn/nghịch lý, cảnh báo, POV, trước–sau; CẤM mở bằng lời chào/giới thiệu bản thân/logo. Ở cấp series (gợi ý, không kiểm tự động trong `score_hook`): luân phiên ≥ 3 loại hook; `variants` (FR-023) dùng 3 loại khác nhau. | Vi phạm → `E-ags-video-studio-10x-012`. | `P0` |
| `BR-ags-video-studio-10x-011` | `UR-ags-video-studio-10x-007` | **Nhịp phá khuôn**: đổi cảnh hoặc kiểu chuyển động ≤ 3,0 s một lần (trung bình ≤ 2,5 s); không 2 cảnh liền cùng kiểu chuyển động; câu cuối nối lại ý hook (kết vòng lặp). | Đo trên `scenes[]` của manifest; sai → cảnh báo trong `proof`. | `P1` |
| `BR-ags-video-studio-10x-012` | `UR-ags-video-studio-10x-007` | **Không bịa kết quả**: số liệu thuộc kết quả/thu nhập/khách hàng của CHÍNH khách chỉ được dùng khi khách cung cấp (`claim_source`: do khách nhập, hoặc tài liệu); nếu không, mẫu hook phải dùng số minh hoạ có nhãn "ví dụ" hoặc số công khai có nguồn. Mẫu hook của hệ thống KHÔNG chứa số liệu cá nhân cố định. | Vi phạm → `E-ags-video-studio-10x-013`, không render. | `P0` |

## 4. Yêu cầu Phi Chức năng

| Mã ID | Tham chiếu Nguồn | Nội dung Đặc tả | Điều kiện / Ràng buộc | Ưu tiên |
|---|---|---|---|---|
| `NFR-ags-video-studio-10x-001` | `UR-ags-video-studio-10x-006` | Hiệu năng: `intake`, `quote`, `validate` phản hồi < 1 s; render mẫu 60 s bằng giọng/ảnh miễn phí < 6 phút trên MacBook Apple Silicon. | Đo bằng `time` thật khi chạy `proof`. | `P1` |
| `NFR-ags-video-studio-10x-002` | `UR-ags-video-studio-10x-001` | Bảo mật: thư mục đầu ra không chứa khoá API; URL nguồn chỉ nhận `http(s)` công khai (dùng lại `_resolve_validated_public_ip` chống SSRF). | Có test URL nội bộ bị chặn. | `P0` |
| `NFR-ags-video-studio-10x-003` | `UR-ags-video-studio-10x-001` | Tương thích: Python 3.9+, macOS và Windows; không thêm phụ thuộc nặng (chỉ dùng stdlib, ffmpeg, Pillow đã có). | `requirements.txt` không đổi trừ khi bắt buộc. | `P1` |
| `NFR-ags-video-studio-10x-004` | `UR-ags-video-studio-10x-001` | Ngôn ngữ giao tiếp với khách: tiếng Việt lời thường; thông báo lỗi nói "chuyện gì xảy ra + làm gì tiếp", không in stack trace. | Có trong bảng mã lỗi mục 5. | `P1` |

## 5. Ma trận Mã lỗi & Thông báo Hiển thị

| Mã ID | Tham chiếu Nguồn | Thông báo hiển thị cho khách | Điều kiện kích hoạt | Ưu tiên |
|---|---|---|---|---|
| `E-ags-video-studio-10x-001` | `FR-ags-video-studio-10x-003` | "Bộ cài thiếu bảng chọn món — chạy lại cài đặt." | Bảng chọn món vắng trong SKILL/README/HUONG-DAN. | `P1` |
| `E-ags-video-studio-10x-002` | `FR-ags-video-studio-10x-004` | "Em chưa hiểu câu trả lời. Chọn 1 trong: …" | Trả lời ngoài danh sách preset/giọng. | `P1` |
| `E-ags-video-studio-10x-003` | `FR-ags-video-studio-10x-005` | "Anh/chị chưa bấm đồng ý chi phí nên em chưa chạy." | `run` khi chưa `confirmed=true`. | `P0` |
| `E-ags-video-studio-10x-004` | `BR-ags-video-studio-10x-003` | "Nguồn không đọc được / kịch bản trùng nguồn quá 8 từ — em viết lại bằng lời của mình." | URL lỗi/không công khai; trùng n-gram. | `P0` |
| `E-ags-video-studio-10x-005` | `BR-ags-video-studio-10x-001` | "Câu số N còn nghe như dịch máy hoặc sai nhịp (nêu rõ lý do từng câu)." | Vi phạm BR-001/BR-002. | `P0` |
| `E-ags-video-studio-10x-006` | `FR-ags-video-studio-10x-009` | "Cảnh N tạo ảnh AI chưa được, em dùng hình dự phòng." | Ảnh AI lỗi sau 1 lần thử lại. | `P1` |
| `E-ags-video-studio-10x-007` | `FR-ags-video-studio-10x-011` | "Chưa có khoá Google AI — chọn giọng miễn phí hoặc dán khoá." | Thiếu khoá Gemini. | `P0` |
| `E-ags-video-studio-10x-008` | `BR-ags-video-studio-10x-006` | "Chữ phụ đề lấn vùng giao diện — em đã thu nhỏ/đổi dòng." | Hộp chữ ngoài vùng an toàn. | `P0` |
| `E-ags-video-studio-10x-009` | `FR-ags-video-studio-10x-014` | "Chưa tạo được ảnh lưới xem trước." | ffmpeg trích khung lỗi. | `P1` |
| `E-ags-video-studio-10x-010` | `FR-ags-video-studio-10x-015` | "Em chưa chắc ý anh/chị: đổi màu chữ, đổi giọng hay đổi cảnh nào?" | Câu sửa không khớp whitelist. | `P1` |
| `E-ags-video-studio-10x-011` | `BR-ags-video-studio-10x-008` | "Video chưa đạt chuẩn: nêu rõ chỉ số lệch (độ ồn, thời lượng, khung hình)." | Sai thông số ffprobe hoặc anti-slop guard exit ≠ 0. | `P0` |
| `E-ags-video-studio-10x-012` | `BR-ags-video-studio-10x-010` | "Câu mở đầu chưa đủ lực: nêu lý do (quá dài / mở bằng lời chào / thiếu số, câu hỏi hay mâu thuẫn)." | Hook vi phạm BR-010. | `P0` |
| `E-ags-video-studio-10x-013` | `BR-ags-video-studio-10x-012` | "Câu này nói về kết quả thật của anh/chị nhưng em chưa có số liệu — anh/chị đưa số hoặc em đổi thành ví dụ minh hoạ." | Hook/câu có số kết quả cá nhân không kèm `claim_source`. | `P0` |
| `E-ags-video-studio-10x-014` | `FR-ags-video-studio-10x-024` | "Giọng Google AI mô hình cũ/không chạy — em thử mô hình mới hoặc đề nghị giọng miễn phí." | Gọi Gemini TTS lỗi 4xx/model not found. | `P1` |

## 6. Giả định, Phụ thuộc & Câu hỏi Mở

- Phụ thuộc: ffmpeg, Pillow, 9router `cx/gpt-image-2` (key trong môi trường người bán), khoá Gemini TTS của khách (tuỳ chọn), `ai-sdlc` cho cổng BA/Builder.
- Giả định đã chốt: "video AI" = ảnh AI + chuyển động dựng ffmpeg (FR-002); fanpage Business Thinking/Jetlag chỉ là nguồn cảm hứng ý/cấu trúc (BR-003).
- Fonts Bricolage Grotesque / Be Vietnam Pro: lấy từ `assets/fonts` nếu có, thiếu thì dùng font đậm có sẵn của `ags_common.font_path` và ghi vào manifest.

## 7. Câu hỏi Mở (OQ)

- [x] **OQ-001** *(Owner: `@po`, Mức độ: `Blocking`, ĐÃ CHỐT 2026-10-24)*: Sinh video bằng T2V ngoài? → Option A (chốt): ảnh AI + chuyển động ffmpeg, chưa tích hợp T2V; Option B (hoãn): chỉ làm khi Teddy duyệt nhà cung cấp và ngân sách.
- [x] **OQ-002** *(Owner: `@po`, Mức độ: `Blocking`, ĐÃ CHỐT 2026-10-24)*: Ai viết kịch bản Việt hoá? → Option A (chốt): agent của khách (Claude/Codex/…) viết, `ags_vi_script.py validate` kiểm tất định; Option B (loại): script tự gọi LLM riêng, tăng chi phí và phụ thuộc khoá.
- [x] **OQ-003** *(Owner: `@po`, Mức độ: `Medium`, MẶC ĐỊNH ĐÃ CHỌN 2026-10-24, Teddy đổi được)*: "Jetlag" là gì? Tra cứu không tìm thấy kênh short-form tên Jetlag; kết quả là *Jet Lag: The Game* và Wendover Productions (explainer "thế giới vận hành"). → Option A (chọn): preset `jetlag-vi` = kể chuyện–giải thích có con số/bản đồ, bối cảnh Việt Nam; Option B: Teddy gửi link kênh đúng → chỉnh preset theo đó. Xem `research/viral-concepts.md`.
- [x] **OQ-004** *(Owner: `@po`, Mức độ: `Medium`, MẶC ĐỊNH ĐÃ CHỌN 2026-10-24)*: "Business Thinking 110k followers" chưa xác minh được (chỉ thấy reel thể loại cùng tên "30 years of business advice in 30 seconds" của Dan Martell). → Option A (chọn): làm theo ngữ pháp thể loại, không nhái tài khoản, không ghi số 110k vào tài liệu bán; Option B: Teddy gửi 3–5 link reel mẫu để hiệu chỉnh nhịp/độ dài.

## 8. Checklist Tự Kiểm Tra Trước Khi Chuyển `in-review`

- [x] 100% yêu cầu gắn mã định danh chuẩn và liên kết ngược về `UR-ags-video-studio-10x-NNN`.
- [x] Mọi trường hợp lỗi gắn mã `E-ags-video-studio-10x-NNN`.
- [x] Mọi câu hỏi mở `OQ-NNN` đã chốt.

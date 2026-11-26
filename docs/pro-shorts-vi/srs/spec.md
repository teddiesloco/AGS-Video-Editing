<!-- ags-ba-profile: minimal -->
---
type: srs
feature: pro-shorts-vi
status: approved
version: 1.0.0
owner: Teddy
updated: 2026-11-26
links: [../api/api-map.md, ../userstories/us-001.md]
---
# Pro Shorts VI — video dài của PRO nước ngoài thành short 9:16 lồng tiếng Việt + kho kiến thức

Nguồn: lời Teddy 26/11/2026 trong brief `_project/cos/briefs/reels-pro.md` (repo AgentSea): "biến video dài của PRO thành video ngắn, chia ra shorts trên dưới, kèm voice over ... nhất quán 1 giọng ... subtitle chuẩn chỉnh, sound effect đầy đủ ... vừa làm nội dung, vừa học và nạp kiến thức từ các top PRO". Quyết định đã chốt ở hub COS cùng ngày: VieNeu v3 Turbo (Apache-2.0) chạy local; Gemini TTS/LLM chỉ dùng khi có khoá hợp lệ; chọn đoạn + dịch được cấp qua `plan.json` khi chưa có khoá.

## 1. Yêu cầu chức năng

| Mã ID | Tham chiếu Nguồn | Nội dung | Điều kiện / Ràng buộc | Ưu tiên |
|---|---|---|---|---|
| `FR-pro-shorts-vi-001` | Brief 26/11 | Một lệnh `ags_pro_shorts` nhận URL video công khai hoặc file MP4 cục bộ và xuất 3–5 short (`--n`, mặc định 3) vào thư mục `out/<pro>-<tiêu đề>-<mã video>/`. | File cục bộ cần `.info.json` của yt-dlp cạnh nó hoặc `--channel/--url`; lỗi `E-pro-shorts-vi-001`, `E-pro-shorts-vi-002`. | `P0` |
| `FR-pro-shorts-vi-002` | Brief 26/11 | Bóc băng video gốc theo từng từ bằng faster-whisper (dùng lại `ags_clip_shorts transcript`), lưu `transcript.json` trong thư mục làm việc, lần chạy sau dùng lại. | Model mặc định `base`, đổi bằng `--whisper-model`. | `P0` |
| `FR-pro-shorts-vi-003` | Brief 26/11 | Kế hoạch `plan.json`: mỗi short có `name`, `start`, `end`, `hook` 3–8 chữ, `segments` (≥2 câu lời Việt); `knowledge` có `summary` + 5–10 `lessons` {`title`, `body`, `t`}. Nguồn: `--plan` hoặc Gemini theo `skills/ags-clip-shorts/references/chon-doan-short.md`. | Kiểm trước khi render; lỗi `E-pro-shorts-vi-003`, `E-pro-shorts-vi-004`, `E-pro-shorts-vi-005`. | `P0` |
| `FR-pro-shorts-vi-004` | Brief 26/11 | Lồng tiếng Việt MỘT giọng cố định cho cả lần chạy (`--voice vieneu|gemini`, `--voice-name`); `--ab-first engine:giọng` render thêm short #1 giọng thứ hai để so sánh. | TTS lỗi thì dừng, lỗi `E-pro-shorts-vi-008`. | `P0` |
| `FR-pro-shorts-vi-005` | Brief 26/11 | Bố cục 1080x1920 chia đôi ở y=960: nửa trên clip gốc cắt 9:8 bám mặt; nửa dưới nền `#f4f4ef` có hook (Bricolage Grotesque, nền neon `#a8ff3e`), phụ đề Việt (Be Vietnam Pro, chữ `#0e1116`, số tô `#1f6f3d`), dòng nguồn hiện suốt video. | Mọi hộp chữ nằm dưới y=960, không che mặt. | `P0` |
| `FR-pro-shorts-vi-006` | Brief 26/11 | Phụ đề lấy mốc từ CHÍNH giọng Việt đã tổng hợp (bóc băng lại file giọng rồi căn từng từ của lời đọc); mỗi cụm ≤2 dòng. | Lệch tối đa bằng độ trễ mở đầu 0,2 s. | `P0` |
| `FR-pro-shorts-vi-007` | Brief 26/11 | Tiếng gốc giảm -21 dB khi clip gốc và giọng Việt lệch ≤4 s, ngược lại tắt; SFX nhẹ ở hook và tối đa 3 lần chuyển ý; chuẩn hoá -14 LUFS. | Ducking ngoài -24..-18 dB: `E-pro-shorts-vi-007`. | `P0` |
| `FR-pro-shorts-vi-008` | Brief 26/11 | Mỗi short có `short-NN.mp4`, `short-NN_sheet.jpg`, `short-NN.caption.txt`; cả lần chạy có `plan.json`, `knowledge.md`, `report.json`. | Short sai định dạng: `E-pro-shorts-vi-009`; guard báo lỗi: `E-pro-shorts-vi-011`. | `P0` |
| `FR-pro-shorts-vi-009` | Brief 26/11 | `knowledge.md` có tên PRO, kênh, link gốc, tóm tắt Việt, 5–10 bài học cho chủ HKD/OPC Việt kèm link mốc `?t=<giây>s`, danh sách short đã dựng. | Lấy từ `knowledge` của plan. | `P0` |
| `FR-pro-shorts-vi-010` | Teddy 26/11 (mẫu Nhật Dương) | `--layout square-bilingual` (cần `--plan`): khung vuông 1080x1080, GIỮ tiếng gốc (không TTS, ducking, SFX, nhạc); tiêu đề 2 dòng (`title_lines`, vế hook trong cặp `*`, tô `#1f6f3d`) trên nền `#f4f4ef`; clip 16:9 viền mảnh; phụ đề đôi đốt cứng (Việt to `#a8ff3e` ≤2 dòng, Anh nhỏ 1 dòng bên dưới); dải đáy `#1f6f3d` + vạch neon, chứa dòng nguồn suốt video và chỗ để logo/CTA. | Mỗi short ≤60 s; tiêu đề ≤9 chữ; mỗi cue có `t0`,`t1`,`vi`,`en` trong đoạn; lỗi `E-pro-shorts-vi-012`, `E-pro-shorts-vi-013`. Không dùng màu cam của mẫu. | `P0` |

## 2. Quy tắc nghiệp vụ

| Mã ID | Tham chiếu Nguồn | Nội dung | Điều kiện / Ràng buộc | Ưu tiên |
|---|---|---|---|---|
| `BR-pro-shorts-vi-001` | Brief 26/11 (bản quyền) | Mỗi short ≤60 s; dòng nguồn hiện từ giây 0 tới hết; không xuất lại nguyên video; caption gợi ý ghi nguồn và link gốc. Không đăng bài, không đăng nhập tài khoản. | Vượt 60 s: `E-pro-shorts-vi-006`. | `P0` |
| `BR-pro-shorts-vi-002` | Brief 26/11 | Lời Việt và kiến thức chỉ dùng ý có trong băng gốc; không bịa con số, giá, cam kết; hook viết lại ý chính của chính đoạn đó. | Plan sai khuôn: `E-pro-shorts-vi-003`. | `P0` |
| `BR-pro-shorts-vi-003` | Brief 26/11 | Một lần chạy dùng đúng một giọng cho mọi short (trừ bản A/B short #1); TTS lỗi thì dừng, không đổi giọng khác; giọng nén tối đa x1.20 để vừa 60 s. | `E-pro-shorts-vi-006`, `E-pro-shorts-vi-008`. | `P0` |
| `BR-pro-shorts-vi-004` | Brief 26/11 | H.264 1080x1920 30 fps yuv420p + AAC 48 kHz; -14 ±1 LUFS; true peak ≤ -1 dBTP; kiểm bằng ffprobe + ebur128 sau render. | Sai: `E-pro-shorts-vi-009`. | `P0` |
| `BR-pro-shorts-vi-005` | CLAUDE.md AgentSea | Chỉ dùng màu `#f4f4ef`, `#ffffff`, `#0e1116`, `#1f6f3d`, `#a8ff3e`; font Be Vietnam Pro và Bricolage Grotesque (OFL, trong `assets/fonts`). Không dùng tím `#6366f1`, không dùng Inter. | Kiểm bằng test bố cục + contact sheet. | `P0` |
| `BR-pro-shorts-vi-006` | Hub COS 26/11 | Khoá Gemini chỉ đọc từ biến môi trường, không in, không ghi ra file hay log; thiếu khoá thì báo lỗi rõ. | `E-pro-shorts-vi-005`. | `P0` |

## 3. Yêu cầu phi chức năng

| Mã ID | Tham chiếu Nguồn | Nội dung | Điều kiện / Ràng buộc | Ưu tiên |
|---|---|---|---|---|
| `NFR-pro-shorts-vi-001` | AGENTS.md mục 4 | Chạy local trên CPU trong container builder vps-cloud (1.5 CPU/8 GB); không thêm web server hay cơ sở dữ liệu. Lệnh trả 0 chỉ khi mọi short qua kiểm định dạng và guard. | Không render trên host hay Mac. | `P0` |
| `NFR-pro-shorts-vi-002` | Brief 26/11 nghiệm thu 1 | Test unit không mạng: bố cục dưới đường chia, phụ đề ≤2 dòng theo mốc giọng, khoảng ducking, nén giọng, dòng thời gian, kiểm plan, `plan_with_llm` với LLM giả; chạy trong builder exit 0. | `tests/ags_test_pro_shorts.py`. | `P0` |
| `NFR-pro-shorts-vi-003` | Brief 26/11 | Kiểm tự động chỉ chứng minh thuộc tính kỹ thuật; nghĩa bản dịch, độ hay của giọng do người duyệt. Bản Gemini chưa có khoá: ghi NOT_CHECKED. | Không coi là đạt khi chưa nghe. | `P1` |

## 4. Mã lỗi

| Mã ID | Tham chiếu Nguồn | Thông báo / Khi nào | Cách xử lý | Ưu tiên |
|---|---|---|---|---|
| `E-pro-shorts-vi-001` | `FR-pro-shorts-vi-001` | Nguồn không phải URL/file, hoặc yt-dlp tải lỗi. | Gợi ý tải bằng máy khác nếu YouTube chặn IP máy chủ. | `P0` |
| `E-pro-shorts-vi-002` | `FR-pro-shorts-vi-001` | File cục bộ thiếu `.info.json` và thiếu `--channel/--url`. | Thêm info.json hoặc cờ nguồn. | `P0` |
| `E-pro-shorts-vi-003` | `FR-pro-shorts-vi-003` | Plan sai: thiếu shorts, sai số lượng, mốc ngoài video, đoạn ngoài 20–58 s, hook ngoài 3–8 chữ, thiếu lời Việt/name, chồng lấn. | Nêu đúng short và trường lỗi. | `P0` |
| `E-pro-shorts-vi-004` | `FR-pro-shorts-vi-009` | Knowledge thiếu summary, không đủ 5–10 bài học, bài học thiếu title/body/mốc t hợp lệ. | Sửa plan. | `P0` |
| `E-pro-shorts-vi-005` | `BR-pro-shorts-vi-006` | Cần Gemini nhưng thiếu khoá, hoặc Gemini không trả JSON dùng được. | Truyền `--plan` hoặc cấp khoá. | `P0` |
| `E-pro-shorts-vi-006` | `BR-pro-shorts-vi-003` | Giọng Việt cần nén >x1.20, short vượt 60 s, hoặc video nguồn ngắn hơn short. | Rút lời Việt của short đó. | `P0` |
| `E-pro-shorts-vi-007` | `FR-pro-shorts-vi-007` | Mức ducking ngoài -24..-18 dB. | Sửa cấu hình. | `P1` |
| `E-pro-shorts-vi-008` | `FR-pro-shorts-vi-004` | TTS thất bại (provider lỗi, thiếu model, giọng không có trong preset). | Xem danh sách `voices`, kiểm khoá/model. | `P0` |
| `E-pro-shorts-vi-009` | `BR-pro-shorts-vi-004` | MP4 sai định dạng, dài quá 60 s, loudness ngoài -14 ±1 LUFS, true peak > -1 dBTP, hoặc không đo được. | Giữ file để chẩn đoán, lệnh trả mã khác 0. | `P0` |
| `E-pro-shorts-vi-010` | `NFR-pro-shorts-vi-001` | Thiếu ffmpeg/ffprobe trong PATH. | Cài ffmpeg có libass. | `P0` |
| `E-pro-shorts-vi-011` | `FR-pro-shorts-vi-008` | Guard chất lượng (`harness/ags_anti_slop_guard.py`) báo lỗi trên short. | In tên short, giữ MP4 + contact sheet, lệnh trả mã khác 0. | `P0` |
| `E-pro-shorts-vi-012` | `FR-pro-shorts-vi-010` | `--layout` lạ, thiếu `--plan`/dùng `--ab-first` với layout vuông, plan vuông sai cấu trúc (title_lines, cues, mốc), short >60 s hoặc <5 s. | Sửa lệnh/plan; thoát trước khi render. | `P0` |
| `E-pro-shorts-vi-013` | `FR-pro-shorts-vi-010` | Chữ tiêu đề hoặc phụ đề Việt (≤2 dòng)/Anh (1 dòng) không vừa khung vuông. | Rút ngắn hoặc tách cue. | `P0` |

Local commands: `ags_pro_shorts` (scripts/ags_pro_shorts.py) chạy trọn chuỗi tải → bóc băng → kế hoạch → lồng tiếng → dựng → kiểm → kho kiến thức; `voices` (scripts/ags_tts.py voices --engine vieneu) liệt kê giọng preset để chọn `--voice-name`.

## 5. Checklist

- [x] Mọi yêu cầu có mã `FR/BR/NFR-pro-shorts-vi-NNN` và nguồn.
- [x] Mọi lỗi có mã `E-pro-shorts-vi-NNN`.
- [x] Không còn câu hỏi mở.

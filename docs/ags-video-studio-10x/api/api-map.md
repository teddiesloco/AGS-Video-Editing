---
type: api-map
feature: "ags-video-studio-10x"
status: in-review
version: 1.0.0
owner: "@ags-ba"
updated: 2026-10-24
links:
  - srs/spec.md
  - ascii-screen/main.md
changelog:
  - "2026-10-24 | /init | Khởi tạo tài liệu chuẩn AGS-BA"
  - "2026-10-24 | ba | Điền ánh xạ UI <-> API <-> manifest"
---

# Ma Trận Ánh Xạ 3 Tầng (UI <-> API <-> Lưu trữ) — AGS Video Studio 10x

> Không có CSDL máy chủ. "Table" = tệp `studio-job.json` (manifest) trong thư mục đầu ra của từng video; "column" = khoá JSON cấp 1. Cùng một lõi `ags_studio.py` được lộ ra 3 đường: CLI (`ags_studio.py <lệnh>`), MCP tool `ags_studio_*`, và HTTP cục bộ `127.0.0.1:8792` (dispatcher sẵn có của `ags_reels_footage.py`).

## 1. Chiều Gửi lên (UI Input -> API Request JSON -> studio_job.column)

| Mã ID | Tham chiếu | UI element → Request → `studio_job.column` | Ràng buộc / Lỗi | Ưu tiên |
|---|---|---|---|---|
| `AMP-ags-video-studio-10x-001` | `FR-ags-video-studio-10x-004` | `ags-vs-question` → `POST /api/v1/studio/intake` `{"answers":{"topic","preset","voice"}}` → `studio_job.answers` | preset ∈ {business-thinking-60s, jetlag-vi, bds, editorial, isometric-3d}; `E-ags-video-studio-10x-002` | `P0` |
| `AMP-ags-video-studio-10x-002` | `FR-ags-video-studio-10x-005` | `ags-vs-quote-run` (xem chi phí) → `POST /api/v1/studio/quote` `{"job_id"}` → `studio_job.quote` | Đọc `config/pricing.json` (BR-004) | `P0` |
| `AMP-ags-video-studio-10x-003` | `FR-ags-video-studio-10x-005` | `ags-vs-quote-run` (bấm Chạy) → `POST /api/v1/studio/run` `{"job_id","confirmed":true}` → `studio_job.status` | `confirmed` bắt buộc; `E-ags-video-studio-10x-003` | `P0` |
| `AMP-ags-video-studio-10x-004` | `FR-ags-video-studio-10x-008` | (agent) → `POST /api/v1/studio/validate-script` `{"script","duration_sec","source_text?"}` → `studio_job.script_report` | BR-001/002/003; `E-ags-video-studio-10x-004/005` | `P0` |
| `AMP-ags-video-studio-10x-005` | `FR-ags-video-studio-10x-015` | `ags-vs-revise` → `POST /api/v1/studio/revise` `{"job_id","say"}` → `studio_job.revisions[]` | Whitelist BR-007; `E-ags-video-studio-10x-010` | `P1` |

## 2. Chiều Hiển thị (studio_job.column -> API Response JSON -> UI Element)

| Mã ID | Tham chiếu | `studio_job.column` → Response → UI element | Ràng buộc / Lỗi | Ưu tiên |
|---|---|---|---|---|
| `AMP-ags-video-studio-10x-006` | `FR-ags-video-studio-10x-004` | `studio_job.next_question` → `GET /api/v1/studio/jobs/{id}` `.next_question` → `ags-vs-question` | Rỗng khi đủ 3 câu | `P0` |
| `AMP-ags-video-studio-10x-007` | `FR-ags-video-studio-10x-005` | `studio_job.quote.total_vnd` → `.quote.total_vnd` → `ags-vs-quote-run` | Số nguyên VND, làm tròn lên 1.000 | `P0` |
| `AMP-ags-video-studio-10x-008` | `FR-ags-video-studio-10x-014` | `studio_job.contact_sheet` → `.contact_sheet` → `ags-vs-contact-sheet` | Đường dẫn tương đối; `E-ags-video-studio-10x-009` | `P0` |
| `AMP-ags-video-studio-10x-009` | `FR-ags-video-studio-10x-016` | `studio_job.output.mp4`, `studio_job.output.ffprobe`, `studio_job.output.guard_exit` → `.output` → `ags-vs-result` | `guard_exit` = 0; `E-ags-video-studio-10x-011` | `P0` |
| `AMP-ags-video-studio-10x-010` | `FR-ags-video-studio-10x-009` | `studio_job.scenes[].fallback` → `.scenes[]` → thông báo cảnh | `E-ags-video-studio-10x-006` | `P1` |

## 3. Quy tắc Biến đổi Định dạng

| Mã ID | Tham chiếu | Quy tắc | Ràng buộc | Ưu tiên |
|---|---|---|---|---|
| `AMP-ags-video-studio-10x-011` | `BR-ags-video-studio-10x-004` | Tiền VND: số nguyên trong JSON; UI hiển thị `12.000 đ`. | Không dùng số thực. | `P1` |
| `AMP-ags-video-studio-10x-012` | `BR-ags-video-studio-10x-009` | Masking: không ghi `GEMINI_API_KEY`/key 9router/`vsec` vào `studio_job`; chỉ ghi `voice.engine` và `key_present:true/false`. | Test quét manifest. | `P0` |
| `AMP-ags-video-studio-10x-013` | `FR-ags-video-studio-10x-003` | Enum preset → nhãn món tiếng Việt (ví dụ `business-thinking-60s` → "Business Thinking 60 giây"). | Nhãn nằm trong `config/menu.json`. | `P1` |
| `AMP-ags-video-studio-10x-014` | `FR-ags-video-studio-10x-018` | `ags-vs-question` (hook) → `POST /api/v1/studio/hook` `{"script","type?"}` → `studio_job.hook_report` | BR-010; `E-ags-video-studio-10x-012` | `P0` |
| `AMP-ags-video-studio-10x-015` | `FR-ags-video-studio-10x-020` | (khách dán mẫu) → `POST /api/v1/studio/profile` `{"samples":[url|text]}` → `studio_job.profile` | SSRF-safe; chỉ đo số liệu, không tải hình/tiếng; `E-ags-video-studio-10x-004` | `P1` |
| `AMP-ags-video-studio-10x-016` | `FR-ags-video-studio-10x-023` | `ags-vs-revise` ("làm 3 bản thử") → `POST /api/v1/studio/variants` `{"job_id","count":3}` → `studio_job.variants[]` | Báo chi phí thêm trước; `E-ags-video-studio-10x-003` | `P1` |
| `AMP-ags-video-studio-10x-017` | `BR-ags-video-studio-10x-012` | `studio_job.claims[].claim_source` → `.claims[]` → nhãn "ví dụ" trên video | Thiếu nguồn → `E-ags-video-studio-10x-013` | `P0` |

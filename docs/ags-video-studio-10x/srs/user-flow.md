---
type: user-flow
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
  - "2026-10-24 | ba | Điền luồng"
---

# Luồng Màn Hình — AGS Video Studio 10x

## 1. Điểm vào & Điểm kết thúc

| Mã ID | Tham chiếu | Nội dung | Ràng buộc | Ưu tiên |
|---|---|---|---|---|
| `UFL-ags-video-studio-10x-001` | `UR-ags-video-studio-10x-001` | Vào: khách gõ 1 câu trong Claude Code / Codex / Antigravity / Cursor (skill tự kích hoạt). Ra: mp4 + ảnh lưới được duyệt, hoặc khách huỷ. | Cần giấy phép hợp lệ (BR-009). | `P0` |

## 2. Sơ đồ Luồng Màn hình (Pele Flowchart)

```pele
flowchart TD
  Entry([Khách gõ 1 câu]) --> Menu[SCR-001 Bảng chọn món]
  Menu --> Q[Hỏi ngược tối đa 3 câu]
  Q -->|E-ags-video-studio-10x-002| Q
  Q --> Script{Preset Việt hoá?}
  Script -->|có| Val[Agent viết kịch bản và validate]
  Val -->|E-ags-video-studio-10x-005 hoặc E-ags-video-studio-10x-004| Val
  Script -->|không| Quote
  Val --> Quote[Báo chi phí BR-004]
  Quote -->|chưa đồng ý: E-ags-video-studio-10x-003| Quote
  Quote -->|khách nói chạy| Run[Render ảnh AI, giọng, phụ đề]
  Run -->|E-ags-video-studio-10x-007| Q
  Run --> Sheet[Ảnh lưới xem trước]
  Sheet -->|khách sửa lời thường| Rev[Revise BR-007]
  Rev -->|E-ags-video-studio-10x-010| Rev
  Rev --> Run
  Sheet -->|khách duyệt| Check{BR-008 đạt?}
  Check -->|không: E-ags-video-studio-10x-011| Run
  Check -->|đạt| Done([Exit: mp4 thành phẩm])
  Sheet -->|khách huỷ| Cancel([Exit: huỷ])
```

## 3. Điều kiện Chuyển bước & Quyền

| Mã ID | Tham chiếu | Nội dung | Ràng buộc | Ưu tiên |
|---|---|---|---|---|
| `UFL-ags-video-studio-10x-003` | `BR-ags-video-studio-10x-004` | Chỉ sang `Run` khi `confirmed=true`. Chỉ sang `Done` khi guard exit 0 và khách đã duyệt. Quyền: 1 giấy phép = số máy theo gói (Creator 1, Studio 2, Agency 5). | Hết hạn lease → dừng ở `Entry` với thông báo giấy phép. | `P0` |

## 4. Back, Reload, Deep-link & Hết phiên

| Mã ID | Tham chiếu | Nội dung | Ràng buộc | Ưu tiên |
|---|---|---|---|---|
| `UFL-ags-video-studio-10x-004` | `FR-ags-video-studio-10x-015` | Đóng chat giữa chừng: `studio-job.json` giữ trạng thái; khách nói "làm tiếp video hôm qua" → nạp lại job gần nhất theo `job_id`. Chạy dở bị ngắt: cảnh đã xong được giữ, chỉ render phần còn thiếu. | Job quá 30 ngày bị coi hết hạn, hỏi lại từ câu 1. | `P1` |

## 5. Câu hỏi Mở

- [x] **OQ-001** *(Owner: `@po`, Mức độ: `Blocking`, ĐÃ CHỐT)*: Xem `srs/spec.md` mục 7.

## 6. Checklist

- [x] Mã định danh chuẩn; [x] lỗi gắn mã; [x] OQ đã chốt.

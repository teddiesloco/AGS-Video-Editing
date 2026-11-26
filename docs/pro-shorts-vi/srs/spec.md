<!-- ags-ba-profile: minimal -->
---
type: srs
feature: "pro-shorts-vi"
status: draft
version: 1.0.0
owner: "@ags-ba"
updated: 2026-11-26
links: []
changelog:
  - "2026-11-26 | /init | Khởi tạo tài liệu chuẩn AGS-BA"
---

# Đặc Tả Yêu Cầu Phần Mềm — Tài Liệu Chính (SRS Spec) — Pro Shorts VI

> **Mục đích tài liệu:** Đặc tả chi tiết FR-pro-shorts-vi-{NNN}, NFR-pro-shorts-vi-{NNN}, BR-pro-shorts-vi-{NNN} và Ma trận Lỗi E-pro-shorts-vi-{NNN}.
> **Quy chuẩn áp dụng:** `.claude/rules/ba-conventions.md`, `.claude/rules/naming-conventions.md`, `.claude/rules/approval-gate.md`, `.claude/rules/ba-conventions.md`.

## 1. 1. Tổng quan Hệ thống & Phạm vi Tính năng

| Mã ID | Tham chiếu Nguồn | Nội dung Đặc tả / Quy tắc Nghiệp vụ | Điều kiện / Ràng buộc | Trạng thái / Ưu tiên |
|---|---|---|---|---|
| `FR-pro-shorts-vi-001` | `UR-pro-shorts-vi-001` | Mô tả chi tiết nội dung mục *1. Tổng quan Hệ thống & Phạm vi Tính năng* bằng ngôn ngữ nghiệp vụ rõ ràng, kiểm chứng được. | Nêu rõ điều kiện biên, phân quyền và mã lỗi `E-pro-shorts-vi-001` (nếu có). | `P0` |

## 2. 2. Yêu cầu Chức năng Chi tiết (FR-pro-shorts-vi-{NNN})

| Mã ID | Tham chiếu Nguồn | Nội dung Đặc tả / Quy tắc Nghiệp vụ | Điều kiện / Ràng buộc | Trạng thái / Ưu tiên |
|---|---|---|---|---|
| `FR-pro-shorts-vi-002` | `UR-pro-shorts-vi-001` | Mô tả chi tiết nội dung mục *2. Yêu cầu Chức năng Chi tiết (FR-pro-shorts-vi-{NNN})* bằng ngôn ngữ nghiệp vụ rõ ràng, kiểm chứng được. | Nêu rõ điều kiện biên, phân quyền và mã lỗi `E-pro-shorts-vi-002` (nếu có). | `P0` |

## 3. 3. Quy tắc Nghiệp vụ & Công thức Tính toán (BR-pro-shorts-vi-{NNN})

| Mã ID | Tham chiếu Nguồn | Nội dung Đặc tả / Quy tắc Nghiệp vụ | Điều kiện / Ràng buộc | Trạng thái / Ưu tiên |
|---|---|---|---|---|
| `BR-pro-shorts-vi-001` | `UR-pro-shorts-vi-001` | Mô tả chi tiết nội dung mục *3. Quy tắc Nghiệp vụ & Công thức Tính toán (BR-pro-shorts-vi-{NNN})* bằng ngôn ngữ nghiệp vụ rõ ràng, kiểm chứng được. | Nêu rõ điều kiện biên, phân quyền và mã lỗi `E-pro-shorts-vi-003` (nếu có). | `P0` |

## 4. 4. Yêu cầu Phi Chức năng: Hiệu năng, Bảo mật, Độ sẵn sàng (NFR-pro-shorts-vi-{NNN})

> **Quy mô (tính năng có backend giữ dữ liệu):** ghi ước lượng trước khi thiết kế: số người dùng/ngày, yêu cầu mỗi giây ở giờ cao điểm (trung bình nhân vài lần), dung lượng tăng mỗi ngày, băng thông ra nếu có tệp lớn. Ước lượng nhỏ hơn tưởng là kết quả hợp lệ. Sau đó tick checklist SC-1..SC-6 ở mục 9 của `data-model.md` (hoặc tick ngay tại đây); `ai-sdlc ba --audit` kiểm.

| Mã ID | Tham chiếu Nguồn | Nội dung Đặc tả / Quy tắc Nghiệp vụ | Điều kiện / Ràng buộc | Trạng thái / Ưu tiên |
|---|---|---|---|---|
| `NFR-pro-shorts-vi-001` | `UR-pro-shorts-vi-001` | Mô tả chi tiết nội dung mục *4. Yêu cầu Phi Chức năng: Hiệu năng, Bảo mật, Độ sẵn sàng (NFR-pro-shorts-vi-{NNN})* bằng ngôn ngữ nghiệp vụ rõ ràng, kiểm chứng được. | Nêu rõ điều kiện biên, phân quyền và mã lỗi `E-pro-shorts-vi-004` (nếu có). | `P0` |

## 5. 5. Ma trận Mã lỗi & Thông báo Hiển thị (E-pro-shorts-vi-{NNN})

| Mã ID | Tham chiếu Nguồn | Nội dung Đặc tả / Quy tắc Nghiệp vụ | Điều kiện / Ràng buộc | Trạng thái / Ưu tiên |
|---|---|---|---|---|
| `E-pro-shorts-vi-001` | `UR-pro-shorts-vi-001` | Mô tả chi tiết nội dung mục *5. Ma trận Mã lỗi & Thông báo Hiển thị (E-pro-shorts-vi-{NNN})* bằng ngôn ngữ nghiệp vụ rõ ràng, kiểm chứng được. | Nêu rõ điều kiện biên, phân quyền và mã lỗi `E-pro-shorts-vi-005` (nếu có). | `P0` |

## 6. 6. Giả định, Phụ thuộc & Câu hỏi Mở (OQ-{NNN})

| Mã ID | Tham chiếu Nguồn | Nội dung Đặc tả / Quy tắc Nghiệp vụ | Điều kiện / Ràng buộc | Trạng thái / Ưu tiên |
|---|---|---|---|---|
| `FR-pro-shorts-vi-006` | `UR-pro-shorts-vi-001` | Mô tả chi tiết nội dung mục *6. Giả định, Phụ thuộc & Câu hỏi Mở (OQ-{NNN})* bằng ngôn ngữ nghiệp vụ rõ ràng, kiểm chứng được. | Nêu rõ điều kiện biên, phân quyền và mã lỗi `E-pro-shorts-vi-006` (nếu có). | `P0` |

## 7. Danh sách Câu hỏi Mở (Open Questions — OQ)

- [ ] **OQ-001** *(Owner: `@po`, Hạn: `2026-11-26`, Mức độ: `Blocking`)*: Nêu câu hỏi nghiệp vụ còn chờ xác nhận kèm 2 phương án đề xuất (Option A / Option B).

## 8. Checklist Tự Kiểm Tra Trước Khi Chuyển `in-review`

- [ ] 100% các mục yêu cầu đã gắn mã định danh chuẩn (`FR-pro-shorts-vi-NNN`) và liên kết ngược về tài liệu thượng nguồn.
- [ ] Không còn từ ngữ định tính mơ hồ; mọi trường hợp lỗi đều đã gắn mã `E-pro-shorts-vi-NNN`.
- [ ] Đã giải quyết hoặc gắn người phụ trách cho toàn bộ các câu hỏi mở `OQ-NNN`.

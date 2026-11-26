---
type: api-map
feature: "pro-shorts-vi"
status: draft
version: 1.0.0
owner: "@ags-ba"
updated: 2026-11-26
links: []
changelog:
  - "2026-11-26 | /init | Khởi tạo tài liệu chuẩn AGS-BA"
---

# Ma Trận Ánh Xạ Dữ Liệu 3 Tầng (UI <-> API <-> Database Mapping) — Pro Shorts VI

> **Mục đích tài liệu:** Liên kết từng trường trên màn hình với JSON payload và cột cơ sở dữ liệu.
> **Quy chuẩn áp dụng:** `.claude/rules/ba-conventions.md`, `.claude/rules/naming-conventions.md`, `.claude/rules/approval-gate.md`, `.claude/rules/ba-conventions.md`.

## Chọn hợp đồng interface trước khi điền

Mặc định HTTP: giữ các phần bên dưới; tối thiểu một dòng phải chứa HTTP method, `/api/...` và `table.column` thực. Không thêm endpoint hoặc DB giả cho sản phẩm local.

Với CLI/MCP local: thay các bảng HTTP bằng bảng đúng 7 cột dưới đây, và thêm một HTML comment có nội dung `ags-ba-interface: local-cli-mcp` (mở `<!--`, đóng `-->`). Không chép marker vào ví dụ HTTP. Xem `.claude/rules/api-conventions.md` mục 3 để biết kiểm định đầy đủ.

```text
| Surface | CLI | MCP | Input | Output | Persistence | Errors |
|---|---|---|---|---|---|---|
| pro-shorts-vi-surface | command | tool_name | input_field | result.json | state.json | E-pro-shorts-vi-001 |
```

Thay ví dụ bằng dữ liệu thật: mỗi Surface là ID ASCII/prototype, bao phủ mọi ID; CLI khớp tên lệnh trong backtick ở SRS; MCP là identifier hoặc một transport ghi `none` (không cả hai). Input/Output phải nêu trường/artifact, Persistence là tệp local hoặc `none (read-only)`, Errors là mã SRS đã khai báo. Không có dòng hợp lệ hoặc còn placeholder thì FAIL; builder giữ đầy đủ hợp đồng local trong kế hoạch.

## 1. Bảng Ánh xạ Chiều Gửi lên (UI Input Field -> API Request JSON -> DB Table.Column)

| Mã ID | Tham chiếu Nguồn | Nội dung Đặc tả / Quy tắc Nghiệp vụ | Điều kiện / Ràng buộc | Trạng thái / Ưu tiên |
|---|---|---|---|---|
| `AMP-pro-shorts-vi-001` | `UR-pro-shorts-vi-001` | Mô tả chi tiết nội dung mục *Bảng Ánh xạ Chiều Gửi lên (UI Input Field -> API Request JSON -> DB Table.Column)* bằng ngôn ngữ nghiệp vụ rõ ràng, kiểm chứng được. | Nêu rõ điều kiện biên, phân quyền và mã lỗi `E-pro-shorts-vi-001` (nếu có). | `P0` |

## 2. Bảng Ánh xạ Chiều Hiển thị (DB Table.Column -> API Response JSON -> UI Element)

| Mã ID | Tham chiếu Nguồn | Nội dung Đặc tả / Quy tắc Nghiệp vụ | Điều kiện / Ràng buộc | Trạng thái / Ưu tiên |
|---|---|---|---|---|
| `AMP-pro-shorts-vi-002` | `UR-pro-shorts-vi-001` | Mô tả chi tiết nội dung mục *Bảng Ánh xạ Chiều Hiển thị (DB Table.Column -> API Response JSON -> UI Element)* bằng ngôn ngữ nghiệp vụ rõ ràng, kiểm chứng được. | Nêu rõ điều kiện biên, phân quyền và mã lỗi `E-pro-shorts-vi-002` (nếu có). | `P0` |

## 3. Quy tắc Biến đổi Định dạng (Timezone, Tiền tệ, Masking, Enum Mapping)

| Mã ID | Tham chiếu Nguồn | Nội dung Đặc tả / Quy tắc Nghiệp vụ | Điều kiện / Ràng buộc | Trạng thái / Ưu tiên |
|---|---|---|---|---|
| `AMP-pro-shorts-vi-003` | `UR-pro-shorts-vi-001` | Mô tả chi tiết nội dung mục *Quy tắc Biến đổi Định dạng (Timezone, Tiền tệ, Masking, Enum Mapping)* bằng ngôn ngữ nghiệp vụ rõ ràng, kiểm chứng được. | Nêu rõ điều kiện biên, phân quyền và mã lỗi `E-pro-shorts-vi-003` (nếu có). | `P0` |

## 4. Danh sách Trường Phái sinh (Calculated Fields) & Trường Mặc định

| Mã ID | Tham chiếu Nguồn | Nội dung Đặc tả / Quy tắc Nghiệp vụ | Điều kiện / Ràng buộc | Trạng thái / Ưu tiên |
|---|---|---|---|---|
| `AMP-pro-shorts-vi-004` | `UR-pro-shorts-vi-001` | Mô tả chi tiết nội dung mục *Danh sách Trường Phái sinh (Calculated Fields) & Trường Mặc định* bằng ngôn ngữ nghiệp vụ rõ ràng, kiểm chứng được. | Nêu rõ điều kiện biên, phân quyền và mã lỗi `E-pro-shorts-vi-004` (nếu có). | `P0` |

## 5. Danh sách Câu hỏi Mở (Open Questions — OQ)

- [ ] **OQ-001** *(Owner: `@po`, Hạn: `2026-11-26`, Mức độ: `Blocking`)*: Nêu câu hỏi nghiệp vụ còn chờ xác nhận kèm 2 phương án đề xuất (Option A / Option B).

## 6. Checklist Tự Kiểm Tra Trước Khi Chuyển `in-review`

- [ ] 100% các mục yêu cầu đã gắn mã định danh chuẩn (`AMP-pro-shorts-vi-NNN`) và liên kết ngược về tài liệu thượng nguồn.
- [ ] Không còn từ ngữ định tính mơ hồ; mọi trường hợp lỗi đều đã gắn mã `E-pro-shorts-vi-NNN`.
- [ ] Đã giải quyết hoặc gắn người phụ trách cho toàn bộ các câu hỏi mở `OQ-NNN`.

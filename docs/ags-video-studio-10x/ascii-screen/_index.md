---
type: screen-index
feature: "ags-video-studio-10x"
status: in-review
version: 1.0.0
owner: "@ags-ba"
updated: 2026-10-24
links:
  - ascii-screen/main.md
changelog:
  - "2026-10-24 | /init | Khởi tạo tài liệu chuẩn AGS-BA"
  - "2026-10-24 | ba | Điền danh mục màn hình"
---

# Danh Mục Màn Hình — AGS Video Studio 10x

## 1. Bảng Master Danh mục Màn hình

| Mã ID | Tham chiếu Nguồn | Nội dung | Điều kiện / Ràng buộc | Ưu tiên |
|---|---|---|---|---|
| `SCR-ags-video-studio-10x-001` | `UR-ags-video-studio-10x-001` | Khung trò chuyện Studio (`ascii-screen/main.md`): bảng chọn món, câu hỏi ngược, giọng, chi phí, ảnh lưới, ô sửa, kết quả. | Chạy trong ô chat của 4 phần mềm khách; không có web riêng. | `P0` |

## 2. Liên kết Màn hình <-> FR <-> User Story

| Mã ID | Tham chiếu Nguồn | Nội dung | Điều kiện / Ràng buộc | Ưu tiên |
|---|---|---|---|---|
| `SCR-ags-video-studio-10x-002` | `UR-ags-video-studio-10x-001` | SCR-001 ↔ `FR-ags-video-studio-10x-003..015` ↔ `US-ags-video-studio-10x-001`. | Mỗi phần tử có `data-testid` trong `html-design/prototype.html`. | `P0` |

## 3. Trạng thái Đồng bộ ASCII / HTML Prototype

| Mã ID | Tham chiếu Nguồn | Nội dung | Điều kiện / Ràng buộc | Ưu tiên |
|---|---|---|---|---|
| `SCR-ags-video-studio-10x-003` | `UR-ags-video-studio-10x-001` | ASCII = prototype (8 phần tử, 4 trạng thái). Không có Figma. | Cập nhật cả hai khi đổi. | `P1` |

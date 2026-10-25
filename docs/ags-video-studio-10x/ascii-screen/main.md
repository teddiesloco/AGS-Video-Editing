# Màn hình — Khung trò chuyện AGS Video Studio (SCR-ags-video-studio-10x-001)

Bề mặt thật: ô chat của Claude Code / Codex / Antigravity / Cursor + cửa sổ xem ảnh lưới. Khách chỉ gõ lời thường.

## 1. Wireframe ASCII

Trạng thái bắt buộc: `Loading` · `Empty` · `Error` · `Populated`.
Responsive bắt buộc: Desktop >=1280px · Tablet 768-1279px · Mobile <768px.

```text
Populated (Desktop >=1280px)
+------------------------------------------------------------------------+
| [1] AGS Video Studio — Anh/chị muốn làm video gì?                      |
| [2] Bảng chọn món:  BĐS | F&B | Giáo dục | Làm đẹp | TMĐT | Business   |
|                     Thinking | Jetlag | B2B                             |
+------------------------------------+-----------------------------------+
| [3] Câu hỏi ngược (1/3)            | [6] Ảnh lưới xem trước (12 khung) |
|     Ngành/chủ đề gì?               |  [01][02][03][04]                 |
|     (•) Business Thinking ( ) ...  |  [05][06][07][08]                 |
| [4] Giọng: (•) Miễn phí ( ) Google |  [09][10][11][12]                 |
| [5] Chi phí: 0 đ | [ Chạy ] [Sửa]  | [7] Ô sửa bằng lời thường          |
+------------------------------------+-----------------------------------+
| [8] Video thành phẩm: ags-bt-30nam.mp4  [Mở] [Xem lưới]                |
+------------------------------------------------------------------------+
Loading: [3] skeleton "Em đang dựng..." + tiến độ % | [6] khung xám
Empty: [1] + [2] hiển thị, [3] "Anh/chị gõ 1 câu là em bắt đầu" | [6] "Chưa có video"
Error: banner đỏ trên [1] nêu lỗi E-ags-video-studio-10x-NNN bằng lời thường + nút [Thử lại]
Tablet 768-1279px: [3][4][5] xếp trên, [6] xuống dưới, 2 cột × 6 hàng
Mobile <768px: 1 cột, [Chạy] full-width, lưới 3 cột × 4 hàng
```

## 2. Đặc tả Thành phần & Logic (Screen Specification)

| # | Thành phần (Element) | Kiểu (Type) | Quy tắc Hiển thị, Ràng buộc & Xử lý Sự kiện (Logic & Validation) |
|---|---|---|---|
| 1 | Tiêu đề & lời chào `data-testid="ags-vs-title"` | Text | • Luôn hiển thị<br>• Mô tả bằng lời thường, không thuật ngữ (NFR-004) |
| 2 | Bảng chọn món `data-testid="ags-vs-menu"` | List | • ≥ 8 món (FR-003)<br>• Bấm/gõ tên món điền sẵn câu trả lời 1<br>• Thiếu bảng: `E-ags-video-studio-10x-001` |
| 3 | Câu hỏi ngược `data-testid="ags-vs-question"` | Radio/Text | • Tối đa 3 câu, bỏ câu đã biết (FR-004)<br>• Sai lựa chọn: `E-ags-video-studio-10x-002` |
| 4 | Chọn giọng `data-testid="ags-vs-voice"` | Radio | • Miễn phí (`synth`/`vieneu`) hoặc Google AI/Gemini (FR-011)<br>• Thiếu khoá: `E-ags-video-studio-10x-007` |
| 5 | Chi phí & nút Chạy `data-testid="ags-vs-quote-run"` | Button | • Hiện chi phí VND theo BR-004<br>• Chỉ bật sau khi đủ 3 câu trả lời; bấm = xác nhận<br>• Chưa xác nhận mà chạy: `E-ags-video-studio-10x-003` |
| 6 | Ảnh lưới xem trước `data-testid="ags-vs-contact-sheet"` | Image grid | • 12 khung có mốc giây (FR-014)<br>• Lỗi: `E-ags-video-studio-10x-009` |
| 7 | Ô sửa bằng lời thường `data-testid="ags-vs-revise"` | Text + Button | • Whitelist tham số BR-007 (FR-015)<br>• Không hiểu: `E-ags-video-studio-10x-010` |
| 8 | Video thành phẩm `data-testid="ags-vs-result"` | File link | • Hiện sau khi đạt BR-008<br>• Không đạt: `E-ags-video-studio-10x-011` |

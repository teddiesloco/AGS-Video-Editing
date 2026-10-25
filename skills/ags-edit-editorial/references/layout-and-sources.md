# ags-edit-editorial — Bố cục chữ, vùng bảo vệ, font và nguồn

Tài liệu hướng dẫn cho agent/người dùng đọc khung hình rồi quyết định. Đây là **heuristic có nguồn**, không phải "luật" dựng phim,
và **không mô tả thêm chức năng của code**. Phần "Code hiện làm gì" bên dưới là phạm vi thật của `scripts/ags_editorial_sub.py`.

## 1. Vai trò chữ: title khác caption

| | Title / hook chữ | Caption / phụ đề |
|---|---|---|
| Vai trò | Nêu lời hứa hoặc chủ đề của đoạn; người xem đọc một lần | Chuyển lời nói thành chữ liên tục, đồng bộ với giọng |
| Thời lượng hiện | Vài giây, đổi theo nhịp cảnh | Theo từng cụm lời, thay liên tục |
| Cỡ / trọng lượng | Lớn hơn, nặng hơn caption | Vừa đủ đọc nhanh, nhất quán suốt video |
| Vị trí | Chọn theo khung hình cụ thể (xem mục 2–3) | Vị trí ổn định để mắt không phải tìm lại |
| Rủi ro | Che chủ thể, tranh chấp với caption | Che mặt/sản phẩm, rơi vào vùng UI nền tảng |

Quy ước nội bộ (không phải luật): title và caption không cùng lúc chiếm cùng một dải; nếu cả hai xuất hiện thì tách vùng rõ ràng
hoặc để title kết thúc trước khi caption vào. Đây là lựa chọn dựng để tránh nhiễu, chưa có nguồn nào trong tài liệu này chứng minh
một con số khoảng cách hay thời lượng chuẩn.

## 2. Ba khái niệm vùng — không gộp làm một

1. **Loại trừ giao diện nền tảng (UI exclusion):** vùng nút, avatar, caption/CTA gốc của app che lên video. Là thuộc tính của
   nền tảng/định dạng, thay đổi theo ứng dụng, phiên bản, thiết bị, ads hay bài organic.
2. **Vùng bảo vệ chủ thể / key visual (subject protected area):** mặt, tay đang thao tác, sản phẩm, số liệu trên màn hình, logo.
   Là thuộc tính của **từng khung hình**, không có trong tài liệu nền tảng. Chữ không được che những thứ người xem cần thấy.
3. **Không gian trống (negative space):** phần khung ít chi tiết, nơi chữ có thể nằm mà không tranh với chủ thể. Là kết quả
   của bố cục cảnh (và của reframe), cũng khác nhau từng khung.

Chữ hợp lệ khi **ngoài (1)**, **ngoài (2)**, và ưu tiên nằm trong **(3)**. Thiếu (3) thì đổi cảnh/crop/đổi thời điểm, hoặc chọn
đặt chữ ở nơi che ít nhất — không tự chế ra vùng "an toàn" thứ tư.

## 3. Mắt người xem: đường quét động, không phải "eye zone" cố định

- Hướng nhìn thay đổi theo mặt người, chuyển động, tương phản, chữ mới xuất hiện và nội dung đang nói. Một vùng "mắt nhìn vào
  đây" cố định cho mọi video thì **không có căn cứ trong tài liệu này**.
- Task này **không xác minh được nghiên cứu eye-tracking nào**, nên không trích số liệu, tên "quy tắc" hay vị trí pixel cụ thể
  từ nguồn thứ cấp. Mọi câu về đường mắt trong skill chỉ là hướng dẫn kiểm tra: đặt chữ gần điểm người xem đang nhìn (thường
  là mặt/vật đang được nói tới) nhưng không đè lên nó; xem lại bằng contact sheet thay vì tin vào vị trí tính sẵn.
- Video Every Frame a Painting "Drive Quadrant System" (https://www.youtube.com/watch?v=wsI8UES59TM; kênh Every Frame a
  Painting, 3:34): parent đã xác nhận chỉ **metadata và mô tả**, **không có transcript**. Không dùng làm nguồn cho quy tắc hay
  timestamp nào ở đây.

## 4. Code hiện làm gì (phạm vi thật) và giới hạn

- `safe_box` / `SAFE_ZONE_9X16` trong `scripts/ags_common.py` dùng **một hộp an toàn duy nhất**: trên/dưới lấy lề lớn nhất từ ba
  tài liệu **quảng cáo dọc** (Meta Reels ads, YouTube vertical video ads, TikTok TopView in-feed); hai bên đối xứng 18,5%
  (200 px ở 1080) để chữ căn giữa x = 540. Hiện: trái 18,5%, trên 15%, phải 18,5%, dưới 35% khung; video không dọc dùng lề đều 8%.
- **Giới hạn, không phải luật cho nội dung organic:** hộp này là hợp (union) chặt của các mẫu ads. Giao diện của bài organic
  chưa được đo ở đây và có thể khác. Đây là lựa chọn bảo thủ để chữ không bị che trên cả ba nền tảng, không phải khẳng định
  "vùng chuẩn".
- Code **không** có profile theo nền tảng/loại nội dung, **không** nhận diện mặt, chủ thể hay không gian trống, **không** tự né
  chữ khỏi key visual. Vị trí chữ do code đặt theo hộp `safe_box`, không theo nội dung khung hình.
- Vì vậy việc kiểm tra mặt/sản phẩm/UI nền tảng trong từng khung do **agent hoặc người dùng** làm: xem contact sheet
  (`harness/ags_anti_slop_guard.py ... --contact-sheet`) và các khung then chốt, rồi chọn vị trí/dòng/thời điểm cho chữ. Khi
  muốn đặt overlay ở vị trí code không hỗ trợ, ghi nhận đó là **khoảng trống chưa hỗ trợ** (gap): nói rõ với người dùng, đề
  xuất cách làm tay (CapCut, hoặc cắt/đổi cảnh), không giả vờ code đã làm.

## 5. Font: 1–2 họ, có kiểm tra tiếng Việt và giấy phép

- Dùng **tối đa 1–2 họ chữ** cho cả video (ví dụ một Sans cho caption và title, hoặc thêm một Serif cho điểm nhấn tạp chí).
  Thêm họ thứ ba làm tăng nhiễu và rủi ro thiếu glyph.
- Vai trò trọng lượng là heuristic: bold/semi-bold cho chữ phải đọc nhanh trên nền biến động; regular cho phần phụ nếu nền sạch.
  Không có số chuẩn "đúng" cho mọi video — tự xem khung thật.
- **Kiểm tra glyph tiếng Việt:** render thử câu có đủ dấu (`ă â ê ô ơ ư đ`, dấu thanh chồng như `ệ ầ ữ ộ`, hoa + thường) và xem
  contact sheet; dấu không được thành ô vuông, rớt dòng, hoặc bị cắt. Không suy ra hỗ trợ tiếng Việt từ tên font.
- **Kiểm tra giấy phép** trước khi đóng gói hoặc phát hành: AGS không đóng gói font (`THIRD_PARTY_NOTICES.md`), nên font do máy
  người dùng có sẵn. Hai nguồn font mở đã xác minh giấy phép (OFL-1.1) qua GitHub API khi viết tài liệu này:
  - Montserrat — https://github.com/JulietaUla/Montserrat (OFL-1.1; README không nêu rõ Vietnamese, hãy kiểm tra bằng render).
  - Be Vietnam Pro — https://github.com/bettergui/BeVietnamPro (OFL-1.1; README giới thiệu là họ font cho tiếng Việt).
  Cài thêm font là việc của người dùng; đây là ghi chú nguồn, không phải phụ thuộc mới của repo.

## 6. CapCut: ba việc khác nhau

Đã đọc README/license chính trên GitHub. Xem chi tiết phần "Bằng chứng CapCut" trong
`skills/ags-edit-bds/references/asset-va-xuat.md`.

| Việc | Công cụ | Bằng chứng |
|---|---|---|
| Sửa draft (JSON cục bộ) | `capcut-cli` | README: đọc/ghi `draft_content.json`/`draft_info.json`; MIT |
| Xem trước | `capcut render` (proxy ffmpeg) | README: "low-res ffmpeg proxy — not CapCut's final render" |
| Export bằng giao diện CapCut | người dùng, hoặc `pyCapCut` (tự động hoá UI trên Windows) | README pyCapCut: bản draft sinh ra vẫn cần export trên CapCut bản Windows |

Việc mở draft trong **ứng dụng CapCut hiện hành** chưa được kiểm chứng ở đây (khớp với dòng "Chưa kiểm chứng" đã có của
`ags_bds_cli.py draft`). Không thêm dependency hay vendor nào vào repo từ hai dự án này.

## 7. Nguồn và giới hạn truy cập

Truy cập khi viết tài liệu này (2026-10-08). Chỉ nguồn đã mở được mới được ghi là đã xác minh.

| Nguồn | Trạng thái |
|---|---|
| https://www.facebook.com/business/ads-guide/update/video/instagram-reels/outcome-engagement | Mở được; văn bản nêu 14% trên, 35% dưới, 6% mỗi cạnh bên (cho Reels ads) |
| https://support.google.com/google-ads/answer/13547298 | Mở được (HTTP 200) nhưng **không đối chiếu được** con số 288/672/48/192 px trong HTML tĩnh; số đó lấy từ chú thích trong `ags_common.py` |
| https://ads.tiktok.com/help/article/tiktok-reservation-topview | Mở được; mục "Safe zone specifications" tồn tại, số px nằm trong file ZIP đính kèm — **chưa tải/đối chiếu** |
| https://github.com/renezander030/capcut-cli | README đã đọc; license MIT (README + GitHub API + LICENSE) |
| https://github.com/GuanYixuan/pyCapCut | README đã đọc; **không thấy file LICENSE ở thư mục gốc, GitHub API báo license = null** → xem như chưa rõ giấy phép, không sao chép mã/asset |
| https://github.com/JulietaUla/Montserrat, https://github.com/bettergui/BeVietnamPro | OFL-1.1 theo GitHub API |
| https://www.youtube.com/watch?v=wsI8UES59TM | Chỉ metadata/mô tả do parent xác nhận; không có transcript; không dùng làm căn cứ |

Chưa có nguồn nào ở đây xác minh: số liệu lượt xem, timestamp, "quy tắc" của editor chuyên nghiệp, nghiên cứu eye-tracking,
hay kích thước UI phổ quát theo pixel cho organic. Báo cáo nghiên cứu thô chứa các tuyên bố đó đang ở trạng thái chưa xác minh.

# Chọn đoạn làm short từ transcript

Áp dụng sau bước `transcript`. Đầu vào: danh sách `sentences` (id, start, end, text). Đầu ra: `ranges.json`.

## Căn cứ chính thức
- TikTok (Creative best practices for performance ads): đưa thông điệp chính vào **3 giây đầu**; dùng phụ đề / chữ trên
  hình để người xem hiểu ngữ cảnh; cấu trúc có **hook → điểm giá trị → lời kêu gọi hành động (CTA)**.
  https://ads.tiktok.com/resources/help/article/creative-best-practices
- YouTube: Shorts dài **tối đa 3 phút** (video vuông hoặc dọc). https://support.google.com/youtube/answer/15424877
  → script từ chối đoạn dài hơn 180 s.

## Quy tắc chọn (kinh nghiệm dựng của AGS, không phải số liệu nền tảng)
1. **Câu mở đầu là hook:** câu nêu vấn đề, con số, câu hỏi, tuyên bố trái chiều, kết quả. Không mở bằng chào hỏi,
   giới thiệu bản thân, "như đã nói ở trên", "thứ hai là", "cái này".
2. **Trọn một ý:** người xem không cần xem video gốc vẫn hiểu. Kết thúc ở câu chốt (kết luận, mẹo, CTA), không dừng giữa ý.
3. **Độ dài:** thường 20–60 s; ý dài có thể tới 180 s. Dưới 10 s thường thiếu ngữ cảnh.
4. **Ưu tiên** đoạn có: con số cụ thể, danh sách bước, sai lầm thường gặp, so sánh trước/sau, câu chuyện có kết quả.
5. **Không chồng lấn** giữa các short; video 10 phút thường ra 3–5 short tốt — ít mà chắc hơn nhiều mà loãng.
6. **Hook** 3–8 chữ, viết lại ý chính của chính đoạn đó (in hoa được); không thêm thông tin video không nói.
   BĐS: không bịa giá, diện tích, pháp lý.
7. **Mốc thời gian:** `start` = `start` của câu mở, `end` = `end` của câu chốt (script tự nắn về ranh giới từ).

## Mẫu ranges.json
```json
[
  {"start": 12.4, "end": 51.8, "hook": "ĐỪNG XUỐNG TIỀN KHI CHƯA XEM SỔ", "name": "xem-so-truoc"},
  {"start": 188.0, "end": 236.5, "hook": "3 BƯỚC KIỂM TRA QUY HOẠCH", "name": "kiem-tra-quy-hoach"}
]
```
Sau khi xuất: chạy harness cho từng short; short nào hook yếu hoặc thiếu ngữ cảnh thì chỉnh `start`/`hook` rồi xuất lại.

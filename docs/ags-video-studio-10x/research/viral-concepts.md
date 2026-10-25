# Nghiên cứu mẫu viral — AGS Video Studio 10x (24/10/2026)

Nguồn đọc thật trong phiên (không phải trí nhớ). Mức tin cậy: **[Đ]** đã đọc trang nguồn; **[T]** chỉ thấy trong kết quả tìm kiếm; **[?]** chưa kiểm chứng được. Số liệu của blog công cụ AI là tham khảo, không phải dữ liệu nền tảng — dùng làm giả thuyết cần đo, không làm cam kết với khách.

## 1. Hai "mẫu nguồn" Teddy nêu — điều kiểm chứng được

| Mẫu | Kết quả tra cứu | Quyết định |
|---|---|---|
| Business Thinking "30 years of business thinking in 60 seconds", 110k followers | **[?]** Không mở được trang tài khoản. Tìm thấy cùng thể loại: reel "30 years of business advice in 30 seconds" của Dan Martell (Instagram, 26/07/2026, 4.988 thích) — **[T]** chỉ có tiêu đề + từ khoá (outcome-based pricing, hiring for skills, premium clients). | Làm theo **ngữ pháp thể loại** "N năm kinh nghiệm trong N giây: chuỗi nguyên tắc ngắn, đối lập, mỗi câu 1 ý", không nhái tài khoản. Con số 110k chưa xác minh → không đưa vào tài liệu bán hàng. |
| "Jetlag" | **[?]** Không có kênh short-form tên Jetlag được xác định. Kết quả là *Jet Lag: The Game* (show thi đấu du lịch, 20–82 phút, Wikipedia **[Đ]**) và Wendover Productions (4,92M sub, "giải thích thế giới vận hành: du lịch, kinh tế, địa lý" **[Đ]**). | Hiểu là thể loại **"giải thích thế giới vận hành bằng câu chuyện + bản đồ/con số"**. Preset `jetlag-vi` = kể chuyện–giải thích bối cảnh Việt Nam. **Cần Teddy xác nhận nếu ý khác (OQ-003).** |

## 2. Cái gì giữ người xem

**Hook** (ClipSpeed **[Đ]**, VitAgency **[Đ]**, Tinh tế **[Đ]**, Captain Hook **[Đ]**):
- Quyết định lướt/ở lại trong ~0,3–0,8 s; 40–60% rời ở giây 0–1. Chỉ cần **một** trigger: khoảng trống tò mò, cảm xúc, nhận diện bản thân, phá khuôn.
- 8 công thức mở: nửa câu, cú sốc hình ảnh, **text hook**, đỉnh cảm xúc, nói thẳng với người xem, **preview-flash**, **phát biểu nghịch lý**, âm thanh. Nội dung kinh doanh/giáo dục: text hook + nghịch lý mạnh nhất.
- Công thức tiếng Việt: đánh thẳng nỗi đau · nghịch lý/sự thật gây sốc · hứa hẹn kết quả **cụ thể** · câu hỏi mở · cảnh báo (loss aversion) · trước–sau · POV.
- Lỗi mở đầu: chào hỏi ("Xin chào các bạn…"), logo/intro, hook >5 s, hook không liên quan thân bài, dùng 1 loại hook mãi.
- Reels: hook trung vị 14 từ, 51/161 mẫu ≤ 10 từ **[Đ]**.

**Phụ đề** (Blitzcut **[Đ]**, OpenClip **[Đ]**):
- Word-by-word / nhóm 2–4 từ, từ đang đọc đổi màu = kiểu giữ chân tốt nhất cho giáo dục–kinh doanh; ~85% người xem có lúc tắt tiếng.
- "Ngữ pháp Hormozi" (công khai, không bản quyền): chữ đậm, 2–4 từ/nhóm, màu theo nghĩa — **vàng = nhấn, xanh = tiền/thắng, đỏ = cảnh báo/sai lầm**.
- Cỡ chữ 50–60 pt ở 1080×1920; trắng + viền đen an toàn nhất; tránh pastel.
- Vùng an toàn (Clipzi **[Đ]**, dẫn Meta/TikTok/Google): Meta Reels chừa trên 14%, dưới 35%, hai bên 6%; mẫu chung 3 nền tảng: trên ~290, dưới ~680, trái ~120, phải ~200 px; dòng chữ cuối kết thúc trên y≈1240. → `SAFE_ZONE_9X16` hiện có (trái 11,1%, trên 15%, phải 27,8%, dưới 35%) **đã đạt/nghiêm hơn** — dùng lại, không định nghĩa số mới. (Bản nháp đầu của spec ghi dưới 22% là sai, yếu hơn chuẩn Meta; đã sửa.)

**Hình ảnh faceless AI** (faceless.so, clipcreator **[T]**): nhất quán phong cách là cốt lõi — khoá một "khung phong cách" văn bản, lặp mô-típ giữa các video thành nhận diện series; 2–4 cảnh cho 1 ý; chuyển động nhẹ chống cảm giác ảnh tĩnh.

**Giọng Gemini TTS** (ai.google.dev **[Đ]**): hỗ trợ Tiếng Việt; điều khiển phong cách/nhịp bằng lời (`speech_metadata.style`); mô hình hiện hành `gemini-3.8-flash-tts`. Code hiện tại mặc định `gemini-2.5-flash-preview-tts` (env `AGS_GEMINI_TTS_MODEL`) → phải kiểm khi chạy `proof` (FR-024).

## 3. Giá trị thêm rút ra (đã đưa vào spec)

| # | Ý tưởng viral | Vì sao tăng giá trị cho khách Việt | Vào spec |
|---|---|---|---|
| 1 | **Thư viện 8 loại hook tiếng Việt** + bộ chấm hook (≤ 14 từ nói, ≤ 8 từ chữ, có số/câu hỏi/mâu thuẫn, cấm chào hỏi) | Khách không giỏi viết hook; hook quyết định retention | FR-018, BR-010 |
| 2 | **Hook hiện ngay frame 0** + âm "whoosh" t=0 + preview-flash tuỳ chọn | Chặn rớt 40–60% giây đầu; ~85% xem tắt tiếng | FR-019 |
| 3 | **Ngữ pháp màu 3 nghĩa** (xanh `#A8FF3E` tiền/thắng, vàng `#FFD166` nhấn, đỏ `#FF5A5F` cảnh báo) | Người xem hiểu ý trước khi đọc; đúng yêu cầu xanh/vàng của Teddy | FR-013, BR-005 |
| 4 | **6 mẫu series có beat-sheet** | Khách chọn "món" đã có cấu trúc thị trường kiểm chứng | FR-021 |
| 5 | **Nhịp phá khuôn**: đổi cảnh/chuyển động ≤ 3 s | Giữ retention 3–10 s | FR-010, BR-011 |
| 6 | **Kết vòng lặp + CTA mềm** | Tăng xem lại, lưu, chia sẻ | FR-022 |
| 7 | **Chống số liệu bịa**: hook kết quả cá nhân chỉ dùng số khách cung cấp | Quảng cáo gian dối hại uy tín/pháp lý của khách | BR-012 |
| 8 | **Giọng có chỉ dẫn phong cách** cho Gemini | Bớt giọng robot | FR-024 |
| 9 | **3 biến thể hook (A/B)** cho cùng video | Khách tự đo giữ-chân-giây-đầu rồi chọn | FR-023 |

## 4. Giới hạn
- Không xem được video gốc Business Thinking/Jetlag; không đo retention thật. Ngưỡng 40/55/70% và "65% lướt trước giây 4" là số blog bên thứ ba.
- Muốn chắc: Teddy gửi 3–5 link reel mẫu thật → phân tích số từ/nhịp để hiệu chỉnh preset (không tải/dùng lại hình–tiếng gốc).

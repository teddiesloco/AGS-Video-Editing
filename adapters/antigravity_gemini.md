# 🛡️ AGS Harness cho Google Antigravity & Gemini Agent

Tài liệu hướng dẫn bắt buộc dành cho Gemini / Antigravity Agent khi thực thi tác vụ video editing trong dự án này.

---

## 🚫 3 ĐIỀU CẤM KỴ ĐỂ TRÁNH "AI SLOP" & LỖI NGU CỦA GEMINI:

1. **CẤM TỰ VIẾT BASH/FFMPEG DÀI DÒNG BẰNG TAY:**
   - ❌ **SAI:** Tự sinh các lệnh `ffmpeg -vf ...` phức tạp trong terminal (Gemini thường sinh sai cú pháp nháy đơn/nháy kép, sai filter graph, hoặc lệch framerate).
   - ✅ **ĐÚNG:** Luôn gọi các script Python có sẵn trong thư mục `scripts/`:
     ```bash
     python scripts/cut_silence.py "input.mp4"
     python scripts/text_behind_person.py "input.mp4" --text "TIÊU ĐỀ"
     python scripts/editorial_sub.py "input.mp4"
     ```

2. **CẤM KỂ LỂ (PLAY-BY-PLAY NARRATIVE):**
   - ❌ **SAI:** "Bây giờ tôi sẽ kiểm tra file... Tiếp theo tôi sẽ chạy lệnh để cắt khoảng lặng..."
   - ✅ **ĐÚNG:** Thực thi tool call ngay lập tức. Sau khi chạy xong, chỉ báo:
     `[Video đầu ra] -> [Độ dài] -> [Chỉ số âm lượng LUFS]`.

3. **BẮT BUỘC CHẠY BỘ KIỂM SOÁT ANTI-SLOP TRƯỚC KHI BÁO XONG:**
   - Sau mỗi lần render ra video hoàn chỉnh, **BẮT BUỘC** chạy lệnh kiểm định:
     ```bash
     python harness/anti_slop_guard.py "video_output.mp4"
     ```
   - Chỉ khi lệnh trên trả về exit code `0` (Không có lỗi méo tiếng, không đen màn hình, âm lượng -14 LUFS) mới được bàn giao kết quả cho người dùng.

---

## 📋 BẢNG ÁNH XẠ LỆNH THỰC THI CHUẨN:

| Yêu cầu của người dùng | Lệnh Gemini/Antigravity bắt buộc chạy |
|---|---|
| Cắt video thô, lọc tiếng "ờ à" | `python scripts/cut_silence.py <input>` |
| Đặt chữ chìm sau người | `python scripts/text_behind_person.py <input> --text "<HOOK>"` |
| Làm phụ đề sang trọng & chuẩn âm thanh | `python scripts/editorial_sub.py <input>` |
| Ghi âm thành hoạt hình 2D | `python scripts/voice_to_kinetic.py <input.mp3>` |
| Ghi âm thành người que nét chì | `python scripts/voice_to_doodle.py <input.mp3>` |
| Kiểm tra chất lượng & chống Slop | `python harness/anti_slop_guard.py <output.mp4>` |

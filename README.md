# 🎬 AGS-Video-Editing — AgentSea Video Editing Suite

Bộ 5 công cụ tự động hóa video độc quyền thuộc hệ sinh thái AgentSea, giúp tiết kiệm 90% thời gian biên tập video hàng ngày.

---

## 🚀 Tính Năng Chính
1. **Cắt Lọc Tự Động (`/ags-edit-az`):** Cắt bỏ sạch sẽ tiếng "ờ, à", từ lặp và khoảng nghỉ chết.
2. **Chữ Chìm Sau Người (`/ags-edit-hook`):** AI tách nền 3 lớp, tạo hiệu ứng giật tít chuyên nghiệp như editor triệu view.
3. **Phụ Đề Tạp Chí (`/ags-edit-editorial`):** Typography thanh lịch, né mặt thông minh, âm lượng chuẩn `-14 LUFS`.
4. **Hoạt Hình Chữ 2D (`/ags-voice-kinetic`):** Chỉ cần audio ghi âm là có video ngắn đăng Reels/TikTok.
5. **Người Que Nét Chì (`/ags-voice-doodle`):** Kể chuyện giấu mặt trên nền giấy vintage mộc mạc.

---

## 🛡️ Đồ Nghề Chống AI Slop & Tương Thích Đa Nền Tảng AI
- **Google Antigravity & Gemini:** Tích hợp bộ quy tắc tại `adapters/antigravity_gemini.md` giúp Gemini chạy thẳng lệnh kỹ thuật, cấm nói nhảm, cấm sinh bash lỗi.
- **Claude Desktop & Code:** Adapter chuẩn slash command tại `adapters/claude_rules.md`.
- **ChatGPT Custom GPT:** System prompt chuẩn hoá tại `adapters/chatgpt_custom_instructions.md`.
- **Harness Kiểm Định Chất Lượng Tự Động:**
  ```bash
  python harness/anti_slop_guard.py "video_output.mp4"
  ```
  Tự động quét: Lệch âm thanh A/V Sync, phụ đề rác, lặp từ ảo giác, đen màn hình và kiểm tra chuẩn âm lượng phát thanh `-14 LUFS`.

---

## 💻 Cài Đặt

### 🍎 Dành cho macOS:
1. Mở Terminal tại thư mục này.
2. Chạy lệnh:
   ```bash
   chmod +x CAI-DAT-MAC.sh && ./CAI-DAT-MAC.sh
   ```

### 🪟 Dành cho Windows:
1. Bấm đúp vào file `CAI-DAT-WIN.bat` để chạy cài đặt tự động.

---

## 🛠️ Cách Sử Dụng Trong Claude Code / Terminal:

- **Cắt video thô:**
  ```bash
  python scripts/cut_silence.py "video_quay_tho.mp4"
  ```

- **Đặt chữ chìm sau người:**
  ```bash
  python scripts/text_behind_person.py "video.mp4" --text "90 NGÀY KIẾM 1 TỶ"
  ```

- **Làm phụ đề sang trọng & chuẩn âm thanh:**
  ```bash
  python scripts/editorial_sub.py "video.mp4"
  ```

- **Làm hoạt hình từ đoạn ghi âm:**
  ```bash
  python scripts/voice_to_kinetic.py "audio.mp3"
  ```

- **Làm video người que kể chuyện:**
  ```bash
  python scripts/voice_to_doodle.py "audio.mp3"
  ```

---
*Bản quyền phát triển: AgentSea Studio · 100% Clean-Room Architecture*

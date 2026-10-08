# 📖 HƯỚNG DẪN SỬ DỤNG TOÀN NĂNG — AGS-VIDEO-EDITING

Tài liệu hướng dẫn chi tiết cách sử dụng bộ 5 Skill Edit Video Tự Động trên **mọi môi trường**: từ **Coding Agents (Claude Code, OpenAI Codex, Google Antigravity, Cursor)** cho đến **Giao diện Web thông thường (chatgpt.com, claude.ai)**.

---

## 🎯 PHẦN 1: DÀNH CHO CODING AGENTS (TỰ ĐỘNG HÓA 100%)

Nếu bạn đang dùng các trợ lý lập trình có khả năng chạy terminal (Claude Code, Codex, Antigravity, Cursor, Windsurf):

### 1. Claude Code / OMP
- **Cài đặt:**
  ```bash
  git clone https://github.com/teddiesloco/AGS-Video-Editing.git
  cd AGS-Video-Editing
  # Mac:
  ./CAI-DAT-MAC.sh
  # Windows:
  ./CAI-DAT-WIN.bat
  ```
- **Sử dụng:** Trong cửa sổ chat của Claude Code, gõ trực tiếp các slash commands:
  - `/ags-edit-az "video_quay_tho.mp4"`: Tự cắt sạch tiếng "ờ, à", khoảng nghỉ và xuất video dọc + ngang.
  - `/ags-edit-hook "video.mp4" --text "90 NGÀY KIẾM 1 TỶ"`: AI tách nền đặt chữ to chìm sau lưng.
  - `/ags-edit-editorial "video.mp4"`: Làm sub nét Serif sang trọng né mặt và cân âm -14 LUFS.
  - `/ags-voice-kinetic "audio.mp3"`: Biến file ghi âm thành hoạt hình chữ 2D.
  - `/ags-voice-doodle "audio.mp3"`: Biến file ghi âm thành video người que nét chì.

---

### 2. Google Antigravity (Gemini Code Agent)
- Antigravity đã được cấu hình sẵn Harness chống lỗi tại `adapters/antigravity_gemini.md`.
- **Cách chat:** Kéo thả video vào workspace và chat câu lệnh ngắn gọn:
  > *"Chạy skill ags-edit-az cho file video1.mp4, sau đó chạy harness anti_slop_guard để kiểm tra."*
- Gemini sẽ tự động gọi script Python trong `scripts/` và trả về kết quả đạt chuẩn exit code 0.

---

### 3. OpenAI Codex / Cursor / Windsurf
- Mở thư mục `AGS-Video-Editing` trong Cursor hoặc VS Code.
- Mở Composer / Chat (Ctrl+L hoặc Ctrl+I) và chat:
  > *"@scripts/cut_silence.py hãy chạy xử lý video clip_raw.mp4 giúp tôi."*
- Agent sẽ tự kích hoạt virtualenv và render video ra thư mục hiện tại.

---

## 🌐 PHẦN 2: DÀNH CHO GIAO DIỆN WEB (CHATGPT.COM & CLAUDE.AI)

Nếu bạn là **người dùng thông thường**, không biết dùng dòng lệnh hay terminal, bạn vẫn có thể dùng `chatgpt.com` hoặc `claude.ai` làm "Đạo diễn AI":

### 1. Dùng trên Claude.ai (Web)
1. Vào **Claude.ai** $\rightarrow$ Tạo một **Project** mới (đặt tên: *Video Editor Pro*).
2. Trong phần **Project Knowledge** (Tài liệu dự án), tải file `SKILL.md` và `README.md` từ repo này lên.
3. Trong phần **Custom Instructions** của Project, dán đoạn hướng dẫn sau:
   ```text
   Bạn là Chuyên gia Đạo diễn & Biên tập Video của AgentSea (AGS-Video-Editing).
   Khi tôi tải lên một file video, file ghi âm hoặc kịch bản:
   1. Bạn hãy nghe/đọc và bóc băng lời thoại chính xác.
   2. Bạn hãy lọc bỏ các từ đệm, nói lắp, từ vấp ("ờ", "à", "ừm", "thì mà là").
   3. Bạn hãy gợi ý câu Hook ngắn 3-5 từ giật tít để đặt chìm sau lưng tôi.
   4. Bạn hãy xuất cho tôi mã lệnh hoặc kịch bản cắt ghép chi tiết từng giây.
   ```
4. **Cách dùng:** Kéo file âm thanh/video hoặc dán kịch bản vào chat $\rightarrow$ Claude trên web sẽ biên tập kịch bản và sinh phụ đề chuẩn xác cho bạn.

---

### 2. Dùng trên ChatGPT.com (Web / Custom GPT)
1. Vào **ChatGPT** $\rightarrow$ **Explore GPTs** $\rightarrow$ **Create a GPT** (hoặc cài vào Custom Instructions cá nhân).
2. Sao chép toàn bộ nội dung trong file `adapters/chatgpt_custom_instructions.md` và dán vào ô **Instructions**.
3. **Cách dùng:**
   - Bạn chỉ cần nhắn: *"Tôi vừa quay một video chia sẻ 45 giây, đây là nội dung nói... hãy tạo cho tôi kịch bản cắt từ thừa và 1 câu hook chữ chìm sau lưng thật viral."*
   - ChatGPT sẽ đóng vai trò đạo diễn, phân tích từng nhịp câu và viết sẵn phụ đề cũng như câu hook đắt giá nhất cho bạn.

---

## 📊 BẢNG TRA CỨU NHANH CÂU LỆNH MẪU

| Bạn muốn làm gì? | Bạn chat câu gì với AI? | Công cụ ngầm chạy |
|---|---|---|
| **Cắt bỏ đoạn nói vấp, im lặng** | *"Dùng ags-edit-az cắt video quay thô này"* | `faster-whisper` + `ffmpeg concat` |
| **Tạo chữ chìm sau người** | *"Tách nền và đặt câu '90 NGÀY KIẾM 1 TỶ' sau lưng"* | `rembg human matting` + `3-layer overlay` |
| **Làm sub phong cách tạp chí** | *"Làm sub tạp chí sang trọng và cân âm -14 LUFS"* | `editorial_sub.py` + `loudnorm` |
| **Ghi âm thành video chữ 2D** | *"Biến file ghi âm này thành video 2D chữ nhảy"* | `voice_to_kinetic.py` |
| **Ghi âm thành video người que** | *"Kể câu chuyện này bằng người que trên giấy kraft"* | `voice_to_doodle.py` |
| **Kiểm tra chất lượng video** | *"Chạy kiểm định chống AI Slop cho video vừa xuất"* | `harness/anti_slop_guard.py` |

---
*Tài liệu được biên soạn bởi AgentSea Studio · Chia sẻ tự do mã nguồn mở.*

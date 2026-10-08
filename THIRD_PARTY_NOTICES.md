# Thông báo thành phần bên thứ ba (Third-Party Notices)

AGS Video Editing của AGS (Agent Space) **không đóng gói kèm** các thành phần dưới đây. Chúng được cài riêng (qua `pip`, Homebrew, winget…) hoặc tự tải về khi chạy lần đầu, và luôn thuộc giấy phép riêng của từng dự án. `LICENSE` của AGS không áp dụng cho chúng.

| Thành phần | Dùng để | Giấy phép |
|---|---|---|
| [FFmpeg](https://ffmpeg.org/legal.html) | Cắt, ghép, render, đo loudness | LGPL-2.1+ (một số bản build có phần GPL-2.0+) |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (+ CTranslate2, PyAV) | Bóc băng giọng nói | MIT (CTranslate2: MIT, PyAV: BSD-3-Clause) |
| Model Whisper (OpenAI, bản chuyển đổi CTranslate2) | Tự tải từ Hugging Face khi chạy lần đầu | MIT |
| [rembg](https://github.com/danielgatis/rembg) (+ onnxruntime) | Tách người khỏi nền | MIT (onnxruntime: MIT) |
| Model U²-Net `u2net_human_seg` | Tự tải khi chạy lần đầu | Apache-2.0 |
| [OpenCV](https://opencv.org/license/) (`opencv-python-headless`) | Đọc/ghi khung hình mask | Apache-2.0 |
| [Pillow](https://github.com/python-pillow/Pillow/blob/main/LICENSE) | Vẽ chữ, card, ảnh BĐS | MIT-CMU (HPND) |
| [NumPy](https://numpy.org/doc/stable/license.html) | Xử lý mảng audio/khung hình | BSD-3-Clause |
| [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) (`mcp`, tuỳ chọn) | MCP server | MIT |

Font chữ: script dùng font có sẵn trong hệ điều hành (Arial, Georgia, DejaVu, Noto, Liberation hoặc Montserrat nếu đã cài) — không đóng gói font nào.

CapCut là nhãn hiệu của chủ sở hữu tương ứng. AGS không liên kết với CapCut; định dạng draft được sinh để tương thích, ở mức thử nghiệm.

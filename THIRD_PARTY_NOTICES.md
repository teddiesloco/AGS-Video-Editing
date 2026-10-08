# Thông báo thành phần bên thứ ba (Third-Party Notices)

AGS Video Editing của AGS (Agent Space) **không đóng gói kèm** các thành phần dưới đây. Chúng được cài riêng (qua `pip`, Homebrew, winget…) hoặc tự tải về khi chạy lần đầu, và luôn thuộc giấy phép riêng của từng dự án. `LICENSE` của AGS không áp dụng cho chúng.

| Thành phần | Dùng để | Giấy phép |
|---|---|---|
| [FFmpeg](https://ffmpeg.org/legal.html) | Cắt, ghép, render, đo loudness | LGPL-2.1+ (một số bản build có phần GPL-2.0+) |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (+ CTranslate2, PyAV) | Bóc băng giọng nói | MIT (CTranslate2: MIT, PyAV: BSD-3-Clause) |
| Model Whisper (OpenAI, bản chuyển đổi CTranslate2) | Tự tải từ Hugging Face khi chạy lần đầu | MIT |
| [rembg](https://github.com/danielgatis/rembg) (+ onnxruntime) | Tách người khỏi nền | MIT (onnxruntime: MIT) |
| Model U²-Net `u2net_human_seg` | Tự tải khi chạy lần đầu | Apache-2.0 |
| [OpenCV](https://opencv.org/license/) (`opencv-python-headless`) | Đọc/ghi khung hình mask, dò khuôn mặt (`FaceDetectorYN`) | Apache-2.0 |
| Model [YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet) `face_detection_yunet_2023mar.onnx` | Dò khuôn mặt cho reframe; tự tải từ opencv_zoo khi chạy lần đầu, kiểm SHA-256 | MIT |
| [Pillow](https://github.com/python-pillow/Pillow/blob/main/LICENSE) | Vẽ chữ, card, ảnh BĐS | MIT-CMU (HPND) |
| [NumPy](https://numpy.org/doc/stable/license.html) | Xử lý mảng audio/khung hình | BSD-3-Clause |
| [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) (`mcp`, tuỳ chọn) | MCP server | MIT |

Font chữ: script dùng font có sẵn trong hệ điều hành (Arial, Georgia, DejaVu, Noto, Liberation hoặc Montserrat nếu đã cài) — không đóng gói font nào.

Ý tưởng tham khảo (không chép mã): dò khoảng lặng theo ngưỡng dB ([auto-editor](https://github.com/WyattBlue/auto-editor), Unlicense), reframe bám mặt có làm mượt ([auto-vertical-reframe](https://github.com/KazKozDev/auto-vertical-reframe), MIT). Dò beat, crossfade, ducking, karaoke đều tự viết hoặc dùng bộ lọc có sẵn của FFmpeg — không thêm thư viện Python nào ngoài `requirements.txt`.

CapCut là nhãn hiệu của chủ sở hữu tương ứng. AGS không liên kết với CapCut; định dạng draft được sinh để tương thích, ở mức thử nghiệm.

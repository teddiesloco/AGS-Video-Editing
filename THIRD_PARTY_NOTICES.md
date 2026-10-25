# Thông báo thành phần bên thứ ba (Third-Party Notices)

Giấy phép `LICENSE` (PolyForm Strict 1.0.0) của AGS (Agent Space) chỉ áp dụng cho **mã nguồn và tài liệu do AGS viết**. Mọi thành
phần dưới đây thuộc giấy phép riêng của từng dự án; `LICENSE` của AGS không áp dụng cho chúng.

## 1. Có đóng gói trong thư mục skill (tài nguyên, không phải mã AGS)

| Thành phần | Dùng để | Giấy phép |
|---|---|---|
| [Kenney — Interface Sounds 1.0](https://kenney.nl/assets/interface-sounds): `assets/sfx/click_001.ogg`, `close_001.ogg`, `confirmation_001.ogg`, `error_001.ogg`, `open_001.ogg`, `pluck_001.ogg` (+ bản sao giấy phép `assets/sfx/License.txt`) | Hiệu ứng âm thanh cho `ags_sfx.py` | **CC0 1.0** (Public Domain) — dùng cá nhân, giáo dục, thương mại; ghi nguồn Kenney không bắt buộc. **Đây là ngoại lệ riêng so với PolyForm Strict:** các file này không chịu hạn chế phi thương mại/không phân phối lại của AGS. |

## 2. Không đóng gói — cài vào `venv/` hoặc tự tải khi chạy

Thư viện Python do `scripts/ags_setup.py` cài vào `venv/` trong thư mục skill (phiên bản ghim ở `requirements*.txt`); model tải từ
Internet ở lần dùng đầu, **không kèm trong gói**.

| Thành phần | Dùng để | Giấy phép |
|---|---|---|
| [FFmpeg](https://ffmpeg.org/legal.html) (người dùng tự cài: Homebrew, winget, apt) | Cắt, ghép, render, đo loudness, trộn SFX | LGPL-2.1+ (một số bản build có phần GPL-2.0+) |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (+ CTranslate2, PyAV) | Bóc băng giọng nói | MIT (CTranslate2: MIT, PyAV: BSD-3-Clause) |
| Model Whisper (OpenAI, bản chuyển đổi CTranslate2; ~150 MB với `base`) | Tự tải từ Hugging Face khi chạy lần đầu | MIT |
| [rembg](https://github.com/danielgatis/rembg) | Tách người khỏi nền | MIT |
| [ONNX Runtime](https://github.com/microsoft/onnxruntime) (ghim `1.23.2`; bản 1.30 từ chối dữ liệu ONNX ngoài qua symlink của Hugging Face) | Chạy model ONNX (rembg, TTS) | MIT |
| Model U²-Net `u2net_human_seg` (~170 MB) | Tự tải khi chạy lần đầu | Apache-2.0 |
| [OpenCV](https://opencv.org/license/) (`opencv-python-headless`) | Đọc/ghi khung hình mask, dò khuôn mặt (`FaceDetectorYN`) | Apache-2.0 |
| Model [YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet) `face_detection_yunet_2023mar.onnx` | Dò khuôn mặt cho reframe; tự tải từ opencv_zoo khi chạy lần đầu, kiểm SHA-256 | MIT |
| [Pillow](https://github.com/python-pillow/Pillow/blob/main/LICENSE) | Vẽ chữ, card, ảnh BĐS | MIT-CMU (HPND) |
| [NumPy](https://numpy.org/doc/stable/license.html) | Xử lý mảng audio/khung hình | BSD-3-Clause |
| [cryptography](https://github.com/pyca/cryptography/blob/main/LICENSE) | Giải mã vault tài nguyên (AES-256-GCM) trong gói đã đóng | Apache-2.0 OR BSD-3-Clause |
| [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) (`mcp`) | MCP server | MIT |
| Thư viện phụ trợ kéo theo khi cài `venv/` (`huggingface_hub`, `scipy`, `scikit-image`, `pymatting`, `librosa`, `pydub`, `kaldi-native-fbank`, `sea-g2p`, `soxr`, `certifi`, `orjson`, `tqdm`) | Tải model, xử lý tín hiệu âm thanh/ảnh trong `rembg` và `vieneu` | Apache-2.0 / MIT / BSD-3-Clause / ISC / MPL-2.0 (`certifi`, `orjson`, `tqdm`) / LGPL-2.1+ (`soxr`, nạp động qua wheel) |

### Giọng đọc tiếng Việt cục bộ (TTS) — hai engine, giấy phép mã / model / giọng tách biệt
Chạy hoàn toàn trên CPU của máy bạn (ONNX, không PyTorch), chỉ dùng giọng có sẵn; AGS không bật và không dùng clone giọng, không
có fallback dịch vụ từ xa. Model chỉ tải khi gọi lần đầu từ Hugging Face (cần Internet).

| | VieNeu (`vieneu==3.8.3`) | ZeroTTS (`zerotts==0.1.5`) |
|---|---|---|
| Nguồn | [pnnbao97/VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS); model `pnnbao-ump/VieNeu-TTS-v3-Turbo` | [zeroweight-ai/ZeroTTS](https://github.com/zeroweight-ai/ZeroTTS); model `zeroweight-ai/ZeroTTS` |
| Giấy phép mã | Apache-2.0 | MIT |
| Giấy phép model + giọng có sẵn | Apache-2.0 (theo model card; người đọc đồng ý cho huấn luyện/tạo giọng tổng hợp; cho phép thương mại) | MIT cho mã và trọng số; **giọng đi kèm ghi là "for evaluation and demos"**, cấm mạo danh/lừa dối, phải nói rõ là giọng tổng hợp |
| Thành phần con | MOSS-Audio-Tokenizer-Nano (Apache-2.0), sea-g2p | decoder ONNX MOSS-Audio-Tokenizer-Nano (Apache-2.0, nằm trong repo trọng số), soe-vinorm (MIT, chuẩn hoá văn bản) |
| Dung lượng tải lần đầu | ~1,0 GB (đo trên macOS) | ~1,7 GB đo thực tế (README upstream ghi ~900 MB) |
| Giọng | 23–25 giọng tuỳ bản model card, mặc định `Hải Đăng` · 48 kHz mono | 8 giọng: `maichi` (mặc định), `baotrang`, `kimoanh`, `hamy`, `giahuy`, `huuduc`, `quangminh`, `tiendat` · 48 kHz |

- Dấu watermark Perth của VieNeu chỉ được SDK áp dụng nếu cài thêm `resemble-perth` — AGS không cài gói này.
- Bộ dữ liệu benchmark của ZeroTTS (CC-BY-NC) không được tải hay dùng.
- Dùng nội dung giọng tổng hợp để công bố: ưu tiên VieNeu; giọng ZeroTTS chỉ cho đánh giá/demo. Bạn tự chịu trách nhiệm tuân thủ
  giấy phép model và luật về nội dung tổng hợp tại nơi đăng.
- Đã chạy thực tế trên macOS Apple Silicon, Python 3.11, CPU. Windows/Linux chưa được chạy thử.

## 3. Ghi chú khác
Font chữ: script dùng font có sẵn trong hệ điều hành (Arial Bold cho kiểu `clean`/`karaoke`, Georgia cho `editorial`, hoặc DejaVu, Noto, Liberation, Montserrat nếu đã cài) — không đóng gói font nào.

Ý tưởng tham khảo (không chép mã): dò khoảng lặng theo ngưỡng dB ([auto-editor](https://github.com/WyattBlue/auto-editor), Unlicense), reframe bám mặt có làm mượt ([auto-vertical-reframe](https://github.com/KazKozDev/auto-vertical-reframe), MIT). Dò beat, crossfade, ducking, karaoke đều tự viết hoặc dùng bộ lọc có sẵn của FFmpeg.

Ngoại lệ tương thích định dạng (Interoperability Exception): `scripts/bds/ags_capcut_template.json` chỉ chứa bộ khung trường JSON tối thiểu để xuất thư mục nháp (`draft_info.json`, `draft_content.json`, `draft_meta_info.json`) mở được trên ứng dụng desktop. CapCut là nhãn hiệu của chủ sở hữu tương ứng; AGS (Agent Space) không liên kết hay được bảo trợ bởi CapCut.

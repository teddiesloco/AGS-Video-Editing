---
name: ags-voice-sfx
description: "AGS (Agent Space) — đọc văn bản tiếng Việt thành file WAV bằng giọng cục bộ trên máy (VieNeu hoặc ZeroTTS, chỉ giọng có sẵn, không clone, không gọi dịch vụ từ xa) và trộn hiệu ứng âm thanh CC0 (click, open, close, pluck, confirmation, error) vào video đúng mốc thời gian mà không thay tiếng gốc. Dùng khi cần lồng tiếng/đọc voice-over tiếng Việt từ văn bản, làm video chữ có tiếng đọc, hoặc chèn tiếng click/whoosh nhẹ vào video."
compatibility: "Cần venv do installer dựng cả hai thư viện TTS (mặc định có; --core thì không), FFmpeg, Internet ở lần đầu để tải model (VieNeu ~1,0 GB, ZeroTTS ~1,7 GB). Chỉ kiểm chứng trên macOS Apple Silicon, Python 3.11, CPU."
license: "PolyForm Strict 1.0.0 — xem LICENSE"
---

# /ags-voice-sfx — Giọng Đọc Tiếng Việt Cục Bộ + Hiệu Ứng Âm Thanh CC0

> Lệnh chạy từ thư mục gốc skill (hai cấp trên file này) bằng Python của venv (`venv/bin/python`, Windows
> `venv\Scripts\python.exe`). Đường dẫn có dấu cách phải đặt trong ngoặc kép.

## 1. Giọng đọc (TTS)
```bash
python scripts/ags_tts.py voices --engine vieneu|zerotts
python scripts/ags_tts.py synthesize --engine vieneu|zerotts --text-file <van-ban.txt> --out <giong.wav> [--voice <ten>]
```
- `--text-file` là UTF-8 (agent ghi văn bản người dùng đưa vào một file `.txt` tạm rồi truyền vào). `--out` phải là file
  `.wav` **chưa tồn tại** (không ghi đè). Kết quả JSON: `{"engine","output","sample_rate","seconds"}`; `voices` in danh sách giọng.
- Hai engine chạy CPU, hoàn toàn trên máy; không có fallback dịch vụ từ xa, **không clone giọng**.
- **Chọn engine:** `vieneu` (mặc định nên dùng: 25 giọng, giọng mặc định `Hải Đăng`, mã nguồn + model + giọng đều Apache-2.0).
  `zerotts` (8 giọng: `maichi` mặc định, `baotrang`, `kimoanh`, `hamy`, `giahuy`, `huuduc`, `quangminh`, `tiendat`):
  tác giả ghi giọng đi kèm **chỉ để đánh giá/demo**, cấm giả mạo/lừa dối và yêu cầu nói rõ là giọng tổng hợp —
  không dùng cho nội dung công bố thương mại. Chi tiết giấy phép: `THIRD_PARTY_NOTICES.md`.
- **Văn bản dài:** VieNeu tự cắt câu (≤ 256 ký tự/đoạn, nghỉ theo dấu câu). ZeroTTS: script tự chuẩn hoá số/viết tắt tiếng
  Việt, cắt đoạn ≤ 15 giây, ghép lại cách nhau 0,15 giây.
- **Lần đầu tải model từ Hugging Face** (VieNeu ~1,0 GB, ZeroTTS ~1,7 GB, đo trên macOS; cần Internet). Gọi trực tiếp
  trên terminal có thể mất vài phút; client MCP có thể hết giờ trước khi tải xong — nên chạy trước
  `python scripts/ags_setup.py --warmup-tts` rồi mới dùng tool MCP `tts_voices`/`tts_synthesize`.
- Thiếu thư viện (cài `--core`) → exit `1`, thông báo `Missing optional TTS dependency`: chạy lại installer không kèm `--core`.

## 2. Hiệu ứng âm thanh (SFX, CC0)
```bash
python scripts/ags_sfx.py list
python scripts/ags_sfx.py mix <video.mp4> --events <events.json> --out <video_sfx.mp4>
```
`list`: 6 file Kenney "Interface Sounds" 1.0 trong `assets/sfx/` (`click_001`, `close_001`, `confirmation_001`, `error_001`,
`open_001`, `pluck_001`, `.ogg`). `events.json` — mảng UTF-8:
```json
[{"file": "click_001.ogg", "time": 2.0, "gain": 0.3}, {"file": "confirmation_001.ogg", "time": 5.5}]
```
- `file`: tên file có sẵn, hoặc đường dẫn file âm thanh của bạn (đường dẫn tương đối tính từ thư mục chứa `events.json`).
- `time`: giây ≥ 0 và nhỏ hơn thời lượng video; `gain`: 0–1 (mặc định 0,25). Không nhận khoá khác, NaN/Inf, boolean.
- Giữ nguyên hình (copy video stream), giữ tiếng gốc và trộn thêm, không rút ngắn video; bộ giới hạn đỉnh -2 dBFS.
  Video không có tiếng thì thêm nền im lặng. Đầu ra là file mới (từ chối ghi đè); đầu vào hỏng → exit `1` kèm lý do.
- Âm lượng gợi ý: 0,2–0,4 so với giọng nói để không át lời.

## 3. Quy trình mẫu: văn bản → video chữ có tiếng đọc → hiệu ứng
1. Ghi văn bản vào `loi.txt` (UTF-8), `ags_tts.py synthesize --engine vieneu --text-file loi.txt --out loi.wav`.
2. `python scripts/ags_voice_to_kinetic.py loi.wav` (hoặc `ags_voice_to_doodle.py`) → video chữ khớp tiếng đọc.
3. Viết `events.json` theo mốc cần nhấn (ví dụ lúc đổi ý), `ags_sfx.py mix <video> --events events.json --out <video_sfx.mp4>`.
4. Kiểm định: `python harness/ags_anti_slop_guard.py <video_sfx.mp4> --contact-sheet <video_sfx>_sheet.jpg`,
   mở ảnh soát theo `harness/QUY-TRINH-KIEM-DINH.md`.

## 4. MCP
`tts_voices(engine)`, `tts_synthesize(engine, text_path, output_path, voice?)`, `sfx_list()`, `sfx_mix(input_path, events[], output_path)`.
Mỗi tool trả `output`, `exit_code`, `stderr_tail`, `stdout_tail`. `events[]` của `sfx_mix` dùng đường dẫn tuyệt đối cho file âm thanh riêng.

## 5. Giấy phép tài nguyên
`assets/sfx` là CC0-1.0 (Kenney, https://kenney.nl/assets/interface-sounds; bản sao giấy phép `assets/sfx/License.txt`) — ngoại lệ
riêng so với giấy phép PolyForm Strict của phần mã AGS. Model/thư viện TTS theo giấy phép riêng: `THIRD_PARTY_NOTICES.md`.

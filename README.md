# 🎬 AGS Video Editing — bộ skill edit video tự động của AGS (Agent Space)

6 skill edit video chạy bằng Python + FFmpeg trên macOS và Windows, dùng được từ Claude Code, Codex, Google Antigravity / Gemini, Cursor (gọi script trực tiếp hoặc qua MCP server).

> 📘 **Hướng dẫn chi tiết:** [HUONG-DAN-SU-DUNG.md](HUONG-DAN-SU-DUNG.md) — cài đặt, dùng trên từng coding agent, cấu hình MCP, dùng trên chatgpt.com / claude.ai.

---

## 🚀 6 Skill
| Skill | Script | Làm gì |
|---|---|---|
| `/ags-edit-az` | `scripts/ags_cut_silence.py` | Bỏ khoảng lặng dài và từ đệm "ờ, à, ừm", cắt chính xác từng khung hình, chuẩn -14 LUFS |
| `/ags-edit-hook` | `scripts/ags_text_behind_person.py` | Tách người bằng rembg, đặt câu hook chìm sau lưng người nói |
| `/ags-edit-editorial` | `scripts/ags_editorial_sub.py` | Phụ đề Serif phong cách tạp chí + chuẩn âm lượng -14 LUFS |
| `/ags-voice-kinetic` | `scripts/ags_voice_to_kinetic.py` | File ghi âm → video chữ 2D bật nảy 1080x1920 |
| `/ags-voice-doodle` | `scripts/ags_voice_to_doodle.py` | File ghi âm → video người que nét chì trên giấy kraft |
| `/ags-edit-bds` | `scripts/ags_bds_cli.py` | Video Bất Động Sản: viền thửa đất, lưới phân lô, ticker, cắt theo beat, draft CapCut (thử nghiệm) hoặc render MP4 |

Mô tả từng bước nằm trong `skills/<tên-skill>/SKILL.md`.

## 🛡️ Anti-AI-Slop Guard (bắt buộc trước khi bàn giao)
```bash
python harness/ags_anti_slop_guard.py "video_output.mp4"
```
Kiểm tra: file đọc được và ≥ 1s, có tiếng, độ dài hình/tiếng lệch ≤ 0.25s, âm lượng -14 ± 2 LUFS, không có đoạn đen màn hình ≥ 0.5s.
Exit `0` = đạt · `2` = có cảnh báo · `1` = lỗi nghiêm trọng.

---

## 💻 Cài Đặt
Yêu cầu: Python 3.10+, FFmpeg. Lần chạy đầu, faster-whisper tự tải model Whisper và rembg tự tải model tách người (cần Internet).

- **macOS:** mở Terminal tại thư mục này: `chmod +x CAI-DAT-MAC.sh && ./CAI-DAT-MAC.sh`
- **Windows:** bấm đúp `CAI-DAT-WIN.bat`

Installer tạo `venv/` và cài `requirements.txt`; MCP server là tuỳ chọn (`requirements-mcp.txt`, installer sẽ hỏi).

## 🛠️ Chạy Trực Tiếp
macOS dùng `./venv/bin/python`, Windows dùng `venv\Scripts\python`:
```bash
python scripts/ags_cut_silence.py "video_quay_tho.mp4"
python scripts/ags_text_behind_person.py "video.mp4" --text "90 NGÀY KIẾM 1 TỶ"
python scripts/ags_editorial_sub.py "video.mp4"
python scripts/ags_voice_to_kinetic.py "audio.mp3"
python scripts/ags_voice_to_doodle.py "audio.mp3"
python scripts/ags_bds_cli.py render --images parcel.jpg grid.jpg --bpm 120 --music nhac.mp3 --out video_bds.mp4
```

## 🔌 MCP Server
`mcp/ags_mcp_server.py` (stdio) mở 8 tool: `cut_silence`, `text_behind_person`, `editorial_sub`, `voice_to_kinetic`, `voice_to_doodle`, `bds_draft`, `bds_render`, `anti_slop_guard`. Mỗi tool trả về `output`, `exit_code`, `stderr_tail`, `stdout_tail`. Cấu hình cho Claude Code, Claude Desktop, Codex, Antigravity / Gemini, Cursor: xem [HUONG-DAN-SU-DUNG.md](HUONG-DAN-SU-DUNG.md#phần-3-mcp-server).

## 🧪 Kiểm Thử Engine BĐS
```bash
python tests/ags_test_bds_engine.py            # thư mục tạm, tự xoá
python tests/ags_test_bds_engine.py --out kq/  # giữ ảnh/video/draft để xem
```

---

## ⚖️ Giấy Phép
Mã nguồn xem được (source-available), **chỉ dùng cá nhân, phi thương mại** — theo [AGS Personal Use License](LICENSE). Không phân phối lại, không bán, không dùng cho dịch vụ edit thu phí hay khoá học/sản phẩm trả phí khi chưa có văn bản cho phép. Cấp phép thương mại: liên hệ Agent Space (AGS). Thành phần bên thứ ba: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Copyright © 2026 Agent Space (AGS) / Teddy.

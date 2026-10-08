# 🎬 AGS Video Editing — bộ skill edit video tự động của AGS (Agent Space)

8 skill edit video chạy bằng Python + FFmpeg trên macOS, Windows, Linux; dùng được từ Claude Code, Codex, Google
Antigravity, Gemini CLI, Cursor (gọi script trực tiếp hoặc qua MCP server) và claude.ai (zip skill).

> 📘 **Hướng dẫn chi tiết:** [HUONG-DAN-SU-DUNG.md](HUONG-DAN-SU-DUNG.md) · **Quy tắc cho agent:** [AGENTS.md](AGENTS.md) ·
> **Thay đổi:** [CHANGELOG.md](CHANGELOG.md)

---

## 🚀 8 Skill
| Skill | Script | Làm gì |
|---|---|---|
| `/ags-edit-az` | `scripts/ags_cut_silence.py` | Bỏ khoảng lặng (đo độ to) và từ đệm "ờ, à, ừm", cắt chính xác từng khung, crossfade tiếng, -14 LUFS |
| `/ags-edit-hook` | `scripts/ags_text_behind_person.py` | Tách người bằng rembg, câu hook chìm sau lưng người nói, hiện ngay khung 0 |
| `/ags-edit-editorial` | `scripts/ags_editorial_sub.py` | Phụ đề tạp chí hoặc karaoke (tô màu từng từ, từ khoá), trong vùng an toàn 9:16, -14 LUFS |
| `/ags-voice-kinetic` | `scripts/ags_voice_to_kinetic.py` | File ghi âm → video chữ 2D bật nảy 1080x1920 |
| `/ags-voice-doodle` | `scripts/ags_voice_to_doodle.py` | File ghi âm → video người que nét chì trên giấy kraft |
| `/ags-reframe` | `scripts/ags_reframe.py` | Video ngang → dọc 9:16, khung bám khuôn mặt chính (OpenCV YuNet), lia mượt |
| `/ags-clip-shorts` | `scripts/ags_clip_shorts.py` | Video dài → nhiều short: bóc băng ra JSON, agent chọn đoạn, xuất short có hook + phụ đề karaoke + bám mặt |
| `/ags-edit-bds` | `scripts/ags_bds_cli.py` | Video Bất Động Sản: viền thửa đất, lưới phân lô, ticker, cắt theo beat (tự dò từ nhạc), wipe, nhạc tự nhỏ dưới giọng đọc, draft CapCut (thử nghiệm) |

Mô tả từng bước: `skills/<tên-skill>/SKILL.md`. Chữ trên video dọc luôn nằm trong vùng an toàn 9:16 định nghĩa một lần ở
`scripts/ags_common.py` (`SAFE_ZONE_9X16`, lấy từ tài liệu chính thức của Meta, Google và TikTok).

## 🛡️ Anti-AI-Slop Guard (bắt buộc trước khi bàn giao)
```bash
python harness/ags_anti_slop_guard.py "video_output.mp4" --contact-sheet "video_output_sheet.jpg"
```
- **Lỗi (exit `1`):** không đọc được / không có hình / ngắn hơn 1 s; đen, đứng hình hoặc câm ≥ 90% thời lượng.
- **Cảnh báo (exit `2`):** không có tiếng; lệch hình-tiếng > 0.25 s; ngoài -14 ± 2 LUFS; true peak > -1 dBTP; đoạn đen ≥ 0.5 s;
  đứng hình ≥ 5 s; khoảng lặng (dưới -50 dBFS) ≥ 2 s.
- **Đạt (exit `0`):** không lỗi, không cảnh báo.
- `--contact-sheet` (+ `--frames N`) xuất ảnh lưới khung hình (khung 0 + rải đều, có khung hồng vùng an toàn) để soát bằng
  mắt hoặc model thị giác — quy trình: [harness/QUY-TRINH-KIEM-DINH.md](harness/QUY-TRINH-KIEM-DINH.md).

---

## 💻 Cài Đặt
Yêu cầu: Python 3.10+, FFmpeg. Lần đầu chạy cần Internet: faster-whisper tải model Whisper, rembg tải model tách người,
reframe tải model YuNet (~230 KB).
```bash
git clone https://github.com/teddiesloco/AGS-Video-Editing.git ags-video-editing
cd ags-video-editing
```
- **macOS:** `chmod +x CAI-DAT-MAC.sh && ./CAI-DAT-MAC.sh` · **Windows:** bấm đúp `CAI-DAT-WIN.bat`
- Installer tạo `venv/` và cài `requirements.txt`; MCP server là tuỳ chọn (`requirements-mcp.txt`, installer sẽ hỏi).

## 🛠️ Chạy Trực Tiếp
macOS dùng `./venv/bin/python`, Windows dùng `venv\Scripts\python`:
```bash
python scripts/ags_cut_silence.py "video_quay_tho.mp4"
python scripts/ags_text_behind_person.py "video.mp4" --text "90 NGÀY KIẾM 1 TỶ"
python scripts/ags_editorial_sub.py "video.mp4" --style karaoke --keywords "bất động sản"
python scripts/ags_voice_to_kinetic.py "audio.mp3"
python scripts/ags_voice_to_doodle.py "audio.mp3"
python scripts/ags_reframe.py "podcast_ngang.mp4"
python scripts/ags_clip_shorts.py transcript "livestream.mp4"
python scripts/ags_clip_shorts.py cut "livestream.mp4" --transcript livestream_transcript.json --ranges ranges.json
python scripts/ags_bds_cli.py render --images parcel.jpg grid.jpg --music nhac.mp3 --auto-beat --transition wipe --out video_bds.mp4
```

## 🤖 Dùng với coding agent
| Agent | File trong repo |
|---|---|
| Codex, Google Antigravity, Cursor | [`AGENTS.md`](AGENTS.md) (quy tắc chung) |
| Claude Code | `SKILL.md` + `skills/` (skill), `.mcp.json` (MCP, dự án) |
| Gemini CLI | `gemini-extension.json` + `GEMINI.md` (`gemini extensions link .`) |
| Cursor | `.cursor/rules/ags-video-editing.mdc` + `.cursor/mcp.json` |
| claude.ai (web) | `python scripts/ags_build_skill_zips.py` → `dist/<skill>.zip` để tải lên Skills |

## 🔌 MCP Server
`mcp/ags_mcp_server.py` (stdio) mở 11 tool: `cut_silence`, `text_behind_person`, `editorial_sub`, `voice_to_kinetic`,
`voice_to_doodle`, `reframe`, `clip_shorts_transcript`, `clip_shorts_cut`, `bds_draft`, `bds_render`, `anti_slop_guard`.
Mỗi tool trả về `output`, `exit_code`, `stderr_tail`, `stdout_tail`. Cấu hình từng client:
[HUONG-DAN-SU-DUNG.md](HUONG-DAN-SU-DUNG.md#phần-3-mcp-server).

## 🧪 Kiểm Thử
```bash
python tests/ags_test_core.py                  # vùng an toàn, NFC, cắt lặng + crossfade, karaoke, harness 0/1/2
python tests/ags_test_bds_engine.py            # engine BĐS (thư mục tạm, tự xoá)
python tests/ags_test_bds_engine.py --out kq/  # giữ ảnh/video/draft để xem
```

---

## ⚖️ Giấy Phép
[PolyForm Strict License 1.0.0](LICENSE) (giải thích tiếng Việt: [LICENSE-VI.md](LICENSE-VI.md)): mã nguồn xem được,
**chỉ dùng cho mục đích phi thương mại; không phân phối lại, không sửa đổi**. Cấp phép thương mại: liên hệ Agent Space (AGS).
Thành phần bên thứ ba: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Required Notice: Copyright © 2026 Agent Space (AGS)

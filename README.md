# 🎬 AGS Video Editing — bộ skill edit video tự động của AGS (Agent Space)

9 skill edit video chạy bằng Python + FFmpeg **trên máy của bạn** (macOS, Linux, Windows): cắt lặng, phụ đề karaoke, reframe 9:16,
cắt short, video BĐS, giọng đọc tiếng Việt cục bộ + hiệu ứng âm thanh CC0. Dùng từ Claude Code, Google Antigravity, Codex,
Gemini CLI, Cursor (agent chạy lệnh thay bạn). **claude.ai và ChatGPT web không render được** — xem bảng bên dưới.

> 📘 **Hướng dẫn chi tiết:** [HUONG-DAN-SU-DUNG.md](HUONG-DAN-SU-DUNG.md) · **Quy tắc cho agent:** [AGENTS.md](AGENTS.md) ·
> **Thay đổi:** [CHANGELOG.md](CHANGELOG.md)

---

## ⚡ Cài nhanh (một bước cho người dùng)
1. Giải nén `ags-video-editing.zip` để được thư mục `ags-video-editing/` (đường dẫn có dấu cách cũng được) và đặt vào thư mục skill
   của agent, ví dụ Claude Code: `~/.claude/skills/` (toàn máy) hoặc `<dự án>/.claude/skills/`. Antigravity / Codex / Gemini CLI /
   Cursor: [HUONG-DAN-SU-DUNG.md](HUONG-DAN-SU-DUNG.md), Phần 2.
2. Mở agent và nói việc cần làm, ví dụ *"cắt lặng ~/Desktop/quay-tho.mp4 rồi làm phụ đề karaoke"*. Lần đầu agent đọc `SKILL.md`,
   xin bạn **một** câu đồng ý rồi tự cài môi trường (venv riêng trong thư mục skill, không đụng pip toàn cục, kiểm tra FFmpeg).

Tự cài bằng tay (cùng kết quả): macOS/Linux `bash CAI-DAT-MAC.sh` · Windows `CAI-DAT-WIN.bat` (chưa kiểm chứng trên Windows thật).
- Mặc định cài **đầy đủ**: lõi + MCP + cả hai giọng đọc (VieNeu, ZeroTTS) + SFX. `--core` bỏ thư viện TTS. `--yes` cho phép
  installer tự cài Python 3.11 / FFmpeg còn thiếu (Homebrew, uv, winget). `python scripts/ags_setup.py --check` kiểm tra không đổi gì.
- Yêu cầu: Python 3.11 (3.12 cho phép, chưa kiểm chứng) và FFmpeg có libass. Thư viện trong venv ~0,9 GB (có TTS).
- **Model không kèm trong gói; tải ở lần dùng đầu (cần Internet):** Whisper `base` ~150 MB, rembg ~170 MB, YuNet ~230 KB,
  VieNeu ~1,0 GB, ZeroTTS ~1,7 GB. Tải trước TTS: `python scripts/ags_setup.py --warmup-tts`.
- Dời/đổi tên thư mục skill → chạy lại installer (venv và cấu hình MCP chứa đường dẫn tuyệt đối).

### Nền tảng nào chạy được gì
| Nền tảng | Trạng thái |
|---|---|
| Claude Code · Antigravity · Codex · Gemini CLI · Cursor (agent có terminal) | Chạy cục bộ bằng zip cài đặt. Đã chạy thực tế trên macOS Apple Silicon + Python 3.11; client khác và Windows/Linux chưa chạy thử |
| claude.ai | **Không render.** Tải `ags-video-editing-web.zip` (Customize → Skills) để lên kịch bản, chọn đoạn short, soát contact sheet và nhận lệnh chạy trên máy |
| ChatGPT (web) | **Không render.** Dán `adapters/chatgpt_custom_instructions.md` vào Custom GPT để lên kế hoạch và nhận lệnh |

---

## 🚀 9 Skill
| Skill | Script | Làm gì |
|---|---|---|
| `/ags-edit-az` | `scripts/ags_cut_silence.py` | Bỏ khoảng lặng (đo độ to) và từ đệm "ờ, à, ừm", cắt chính xác từng khung, crossfade tiếng, -14 LUFS |
| `/ags-edit-hook` | `scripts/ags_text_behind_person.py` | Tách người bằng rembg, câu hook chìm sau lưng người nói, hiện ngay khung 0 |
| `/ags-edit-editorial` | `scripts/ags_editorial_sub.py` | Phụ đề clean (Sans đậm, từ khoá vàng cát), tạp chí hoặc karaoke (tô màu từng từ, từ khoá), trong vùng an toàn 9:16, -14 LUFS |
| `/ags-voice-kinetic` | `scripts/ags_voice_to_kinetic.py` | File ghi âm → video chữ 2D bật nảy 1080x1920 |
| `/ags-voice-doodle` | `scripts/ags_voice_to_doodle.py` | File ghi âm → video người que nét chì trên giấy kraft |
| `/ags-reframe` | `scripts/ags_reframe.py` | Video ngang → dọc 9:16, khung bám khuôn mặt chính (OpenCV YuNet), lia mượt |
| `/ags-clip-shorts` | `scripts/ags_clip_shorts.py` | Video dài → nhiều short: bóc băng ra JSON, agent chọn đoạn, xuất short có hook + phụ đề karaoke + bám mặt |
| `/ags-edit-bds` | `scripts/ags_bds_cli.py` | Video Bất Động Sản: viền thửa đất, lưới phân lô, ticker, cắt theo beat (tự dò từ nhạc), wipe, nhạc tự nhỏ dưới giọng đọc, draft CapCut (thử nghiệm) |
| `/ags-voice-sfx` | `scripts/ags_tts.py`, `scripts/ags_sfx.py` | Văn bản tiếng Việt → WAV bằng giọng cục bộ (VieNeu/ZeroTTS, chỉ giọng có sẵn, không clone); trộn SFX CC0 vào video đúng mốc thời gian, giữ nguyên hình và tiếng gốc |

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

## 🛠️ Chạy Trực Tiếp
Dùng Python của venv trong thư mục skill (macOS/Linux `venv/bin/python`, Windows `venv\Scripts\python.exe`), cwd = thư mục skill:
```bash
python scripts/ags_cut_silence.py "video_quay_tho.mp4"
python scripts/ags_text_behind_person.py "video.mp4" --text "90 NGÀY KIẾM 1 TỶ"
python scripts/ags_editorial_sub.py "video.mp4" --style karaoke --keywords "bất động sản"
python scripts/ags_voice_to_kinetic.py "audio.mp3"
python scripts/ags_voice_to_doodle.py "audio.mp3"
python scripts/ags_reframe.py "podcast_ngang.mp4"
python scripts/ags_clip_shorts.py transcript "livestream.mp4"
python scripts/ags_clip_shorts.py cut "livestream.mp4" --transcript livestream_transcript.json --ranges ranges.json
python scripts/ags_bds_cli.py render --clips clip1.mp4 clip2.mp4 anh.jpg --seconds 4 --transition dissolve --zoom subtle --voice loi.wav --out video.mp4
python scripts/ags_tts.py synthesize --engine vieneu --text-file loi.txt --out loi.wav
python scripts/ags_sfx.py mix "video.mp4" --events events.json --out "video_sfx.mp4"
```

## 🤖 Dùng với coding agent
| Agent | File trong thư mục skill |
|---|---|
| Claude Code | `SKILL.md` (skill gốc, tự kiểm tra/cài môi trường) + `skills/` (9 skill con) |
| Codex, Google Antigravity, Cursor | [`AGENTS.md`](AGENTS.md) (quy tắc chung); Cursor còn có `.cursor/rules/ags-video-editing.mdc` |
| Gemini CLI | `gemini-extension.json` + `GEMINI.md` (`gemini extensions link .`) |
| claude.ai (web, chỉ lập kế hoạch) | `ags-video-editing-web.zip` do `python scripts/ags_build_skill_zips.py` dựng cùng bản cài đặt |

## 🔌 MCP Server (tuỳ chọn)
`mcp/ags_mcp_server.py` (stdio) mở 15 tool: `cut_silence`, `text_behind_person`, `editorial_sub`, `voice_to_kinetic`,
`voice_to_doodle`, `reframe`, `clip_shorts_transcript`, `clip_shorts_cut`, `bds_draft`, `bds_render`, `anti_slop_guard`,
`tts_voices`, `tts_synthesize`, `sfx_list`, `sfx_mix`. Mỗi tool trả về `output`, `exit_code`, `stderr_tail`, `stdout_tail`.
Installer sinh `.mcp.json` / `.cursor/mcp.json` với đường dẫn tuyệt đối (không dùng biến `${...}`); cấu hình cho client khác:
`python scripts/ags_setup.py --print-mcp` — xem [HUONG-DAN-SU-DUNG.md](HUONG-DAN-SU-DUNG.md#phần-3-mcp-server).

## 🧪 Kiểm Thử
```bash
python tests/ags_test_core.py                  # vùng an toàn, NFC, cắt lặng + crossfade, karaoke, harness 0/1/2
python tests/ags_test_bds_engine.py            # engine BĐS (thư mục tạm, tự xoá)
```

---

## ⚖️ Giấy Phép
[PolyForm Strict License 1.0.0](LICENSE) (giải thích tiếng Việt: [LICENSE-VI.md](LICENSE-VI.md)): mã nguồn xem được,
**chỉ dùng cho mục đích phi thương mại; không phân phối lại, không sửa đổi**. Cấp phép thương mại: liên hệ Agent Space (AGS).
Hiệu ứng âm thanh `assets/sfx` (Kenney, CC0) và thư viện/model bên thứ ba (kể cả giấy phép mã, model và giọng của VieNeu / ZeroTTS)
theo giấy phép riêng: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Required Notice: Copyright © 2026 Agent Space (AGS)

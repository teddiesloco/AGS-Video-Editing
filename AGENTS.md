# AGENTS.md — AGS Video Editing (AGS — Agent Space)

Bộ script Python + FFmpeg edit video tự động, chạy cục bộ. Hướng dẫn chung cho mọi coding agent: Codex, Google Antigravity,
Cursor đọc trực tiếp file này; Gemini CLI nạp qua `GEMINI.md`; Claude Code dùng `SKILL.md` (trỏ về đây).

## Môi trường (agent tự lo, không hỏi người dùng về Python/venv)
- `SKILL_DIR` = thư mục chứa `AGENTS.md`/`SKILL.md`, đường dẫn tuyệt đối — có thể có dấu cách, luôn đặt trong ngoặc kép.
  `PY` = Python của venv trong skill: macOS/Linux `SKILL_DIR/venv/bin/python`, Windows `SKILL_DIR\venv\Scripts\python.exe`.
  "Python" trong bảng dưới nghĩa là `PY`, cwd = `SKILL_DIR`, đường dẫn video truyền tuyệt đối. Không dùng pip toàn cục.
- Kiểm tra: `"PY" scripts/ags_setup.py --check` (JSON; `ready_core`, `ready_tts`). Chưa có venv hoặc chưa sẵn sàng → hỏi
  người dùng một câu đồng ý cài (thư viện ~0,9 GB + tải model TTS ~2,7 GB ở lần dùng đầu) rồi chạy
  `bash "SKILL_DIR/CAI-DAT-MAC.sh" --yes` (macOS/Linux) hoặc `"SKILL_DIR\CAI-DAT-WIN.bat" --yes` (Windows, chưa kiểm chứng
  trên Windows thật). Mặc định cài cả hai giọng đọc (VieNeu, ZeroTTS); `--core` bỏ TTS. Cần Python 3.11 (3.12 được phép) và
  FFmpeg — `--yes` cho phép installer tự cài bằng Homebrew/uv/winget; exit `3` là thiếu mà không tự cài được: báo đúng lệnh trong stderr.
- Dời/đổi tên thư mục skill → chạy lại installer (venv và cấu hình MCP chứa đường dẫn tuyệt đối).
- Lần đầu cần Internet: faster-whisper tải model Whisper (~150 MB), rembg tải `u2net_human_seg` (~170 MB), reframe tải YuNet
  (~230 KB), TTS tải VieNeu (~1,0 GB) / ZeroTTS (~1,7 GB). Tải trước TTS bằng `python scripts/ags_setup.py --warmup-tts`.

## Việc → lệnh
| Việc | Lệnh | Chi tiết |
|---|---|---|
| Cắt lặng, bỏ từ đệm | `python scripts/ags_cut_silence.py <video>` | `skills/ags-edit-az/SKILL.md` |
| Chữ chìm sau người | `python scripts/ags_text_behind_person.py <video> --text "<HOOK>"` | `skills/ags-edit-hook/SKILL.md` |
| Phụ đề tạp chí / karaoke | `python scripts/ags_editorial_sub.py <video> [--style karaoke]` | `skills/ags-edit-editorial/SKILL.md` |
| Ghi âm → chữ 2D | `python scripts/ags_voice_to_kinetic.py <audio>` | `skills/ags-voice-kinetic/SKILL.md` |
| Ghi âm → người que | `python scripts/ags_voice_to_doodle.py <audio>` | `skills/ags-voice-doodle/SKILL.md` |
| Ngang → dọc 9:16 bám mặt | `python scripts/ags_reframe.py <video>` | `skills/ags-reframe/SKILL.md` |
| Video dài → nhiều short | `python scripts/ags_clip_shorts.py transcript\|cut ...` | `skills/ags-clip-shorts/SKILL.md` |
| Video Bất Động Sản | `python scripts/ags_bds_cli.py <draft\|render\|parcel\|subdivision\|ticker\|beats\|prompt>` | `skills/ags-edit-bds/SKILL.md` |
| Văn bản → giọng đọc WAV | `python scripts/ags_tts.py synthesize --engine vieneu\|zerotts --text-file <txt> --out <wav>` | `skills/ags-voice-sfx/SKILL.md` |
| Trộn SFX CC0 theo mốc | `python scripts/ags_sfx.py mix <video> --events <json> --out <video_moi>` | `skills/ags-voice-sfx/SKILL.md` |
| Kiểm định | `python harness/ags_anti_slop_guard.py <video> --contact-sheet <anh.jpg>` | `harness/QUY-TRINH-KIEM-DINH.md` |

## Quy tắc bắt buộc
1. Gọi script hoặc tool MCP có sẵn; không tự viết lệnh FFmpeg dài; không sửa script (giấy phép không cho sửa đổi) — script
   lỗi thì báo người dùng kèm stderr.
2. Sau mỗi lần render: chạy harness với `--contact-sheet`, mở ảnh và soát theo `harness/QUY-TRINH-KIEM-DINH.md`.
   Exit `0` mới bàn giao · `2` phải xử lý hoặc báo rõ từng cảnh báo · `1` không bàn giao. Sửa tối đa 3 vòng.
3. Không kể lể từng bước. Xong báo: `[Video đầu ra] -> [Thời lượng] -> [LUFS] -> [Kết quả guard] -> [Contact sheet]`.
4. Vị trí chữ để script tự đặt: vùng an toàn 9:16 định nghĩa một lần ở `scripts/ags_common.py` (`SAFE_ZONE_9X16`).
5. Không bịa số liệu: giá, diện tích, pháp lý BĐS; hook của short phải đúng nội dung đoạn đó. Thiếu thì hỏi.
6. Video dài → short: bóc băng trước, chọn đoạn theo `skills/ags-clip-shorts/references/chon-doan-short.md`, rồi mới cắt.
7. Giọng đọc tổng hợp: chỉ giọng có sẵn (không clone), chạy cục bộ. Ưu tiên `vieneu` (Apache-2.0); giọng `zerotts` chỉ để
   đánh giá/demo, phải nói rõ là giọng tổng hợp (`THIRD_PARTY_NOTICES.md`). Không ghi đè file đầu ra — đặt tên mới.

## MCP server (tuỳ chọn — chạy script trực tiếp qua terminal là đủ)
`mcp/ags_mcp_server.py` (stdio; thư viện `mcp` đã nằm trong venv). Tool: `cut_silence`, `text_behind_person`, `editorial_sub`,
`voice_to_kinetic`, `voice_to_doodle`, `reframe`, `clip_shorts_transcript`, `clip_shorts_cut`, `bds_draft`, `bds_render`,
`anti_slop_guard`, `tts_voices`, `tts_synthesize`, `sfx_list`, `sfx_mix` — mỗi tool trả `output`, `exit_code`, `stderr_tail`,
`stdout_tail`. Cấu hình **do installer sinh** với đường dẫn tuyệt đối của máy này: `.mcp.json` (Claude Code, OMP),
`.cursor/mcp.json` (Cursor), `gemini-extension.json` (Gemini CLI, cập nhật interpreter theo hệ điều hành). Dùng ở mọi dự án /
Antigravity / Codex / Claude Desktop: `python scripts/ags_setup.py --print-mcp` (hoặc `--register-claude-code`);
chi tiết `HUONG-DAN-SU-DUNG.md`, Phần 3. Tải model TTS lần đầu lâu hơn giới hạn thời gian tool của nhiều client — chạy
`--warmup-tts` trong terminal trước.

## Giới hạn nền tảng
Chạy cục bộ: Claude Code, Antigravity, Codex, Gemini CLI, Cursor (đã chạy thực tế trên macOS Apple Silicon, Python 3.11;
Windows/Linux chưa chạy thử). claude.ai và ChatGPT web không render được — xem `HUONG-DAN-SU-DUNG.md`, Phần 4.

## Giấy phép
PolyForm Strict 1.0.0 (`LICENSE`; giải thích tiếng Việt: `LICENSE-VI.md`): chỉ dùng cho mục đích phi thương mại;
không phân phối lại, không sửa đổi. Không đẩy repo hay file zip của bộ này lên nơi khác. Các hạn chế này áp dụng cho bên
nhận giấy phép, không tước quyền sửa và phát hành của chủ sở hữu bản quyền. Hiệu ứng âm thanh `assets/sfx` (CC0) và thư
viện/model bên thứ ba theo giấy phép riêng của chúng — `THIRD_PARTY_NOTICES.md`.

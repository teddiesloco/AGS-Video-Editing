# AGENTS.md — AGS Video Editing (AGS — Agent Space)

Bộ script Python + FFmpeg edit video tự động. Đây là hướng dẫn chung cho mọi coding agent: Codex, Google Antigravity,
Cursor đọc trực tiếp file này; Gemini CLI nạp qua `GEMINI.md`; Claude Code dùng `SKILL.md` (trỏ về đây).

## Môi trường
- Python của venv trong repo: macOS/Linux `./venv/bin/python`, Windows `venv\Scripts\python` (tạo bằng `CAI-DAT-MAC.sh` /
  `CAI-DAT-WIN.bat`). Cần FFmpeg trong PATH. Mọi lệnh chạy từ thư mục gốc repo.
- Lần đầu cần Internet: faster-whisper tải model Whisper, rembg tải `u2net_human_seg`, reframe tải YuNet (~230 KB).

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
| Kiểm định | `python harness/ags_anti_slop_guard.py <video> --contact-sheet <anh.jpg>` | `harness/QUY-TRINH-KIEM-DINH.md` |

## Quy tắc bắt buộc
1. Gọi script hoặc tool MCP có sẵn; không tự viết lệnh FFmpeg dài; không sửa script trong repo (giấy phép không cho
   sửa đổi) — script lỗi thì báo người dùng kèm stderr.
2. Sau mỗi lần render: chạy harness với `--contact-sheet`, mở ảnh và soát theo `harness/QUY-TRINH-KIEM-DINH.md`.
   Exit `0` mới bàn giao · `2` phải xử lý hoặc báo rõ từng cảnh báo · `1` không bàn giao. Sửa tối đa 3 vòng.
3. Không kể lể từng bước. Xong báo: `[Video đầu ra] -> [Thời lượng] -> [LUFS] -> [Kết quả guard] -> [Contact sheet]`.
4. Vị trí chữ để script tự đặt: vùng an toàn 9:16 định nghĩa một lần ở `scripts/ags_common.py` (`SAFE_ZONE_9X16`).
5. Không bịa số liệu: giá, diện tích, pháp lý BĐS; hook của short phải đúng nội dung đoạn đó. Thiếu thì hỏi.
6. Video dài → short: bóc băng trước, chọn đoạn theo `skills/ags-clip-shorts/references/chon-doan-short.md`, rồi mới cắt.

## MCP server
`mcp/ags_mcp_server.py` (stdio, cần `pip install -r requirements-mcp.txt`). Tool: `cut_silence`, `text_behind_person`,
`editorial_sub`, `voice_to_kinetic`, `voice_to_doodle`, `reframe`, `clip_shorts_transcript`, `clip_shorts_cut`,
`bds_draft`, `bds_render`, `anti_slop_guard` — mỗi tool trả `output`, `exit_code`, `stderr_tail`, `stdout_tail`.
Cấu hình có sẵn: `.mcp.json` (Claude Code), `.cursor/mcp.json` (Cursor), `gemini-extension.json` (Gemini CLI);
Antigravity, Codex, Claude Desktop, Windows: `HUONG-DAN-SU-DUNG.md`, Phần 3.

## Giấy phép
PolyForm Strict 1.0.0 (`LICENSE`; giải thích tiếng Việt: `LICENSE-VI.md`): chỉ dùng cho mục đích phi thương mại;
không phân phối lại, không sửa đổi. Không đẩy repo hay file zip của bộ này lên nơi khác.

---
name: ags-clip-shorts
description: "AGS (Agent Space) — cắt video dài (podcast, livestream, bài giảng, phỏng vấn) thành nhiều short 9:16: bước 1 bóc băng ra JSON có mốc từng từ, agent đọc và chọn đoạn có hook; bước 2 xuất từng short 1080x1920 với khung bám mặt, phụ đề karaoke, câu hook hiện ngay khung đầu, -14 LUFS. Dùng khi người dùng muốn làm short, reels, clip highlight, cắt viral từ video dài."
compatibility: "Cần Python 3.10+, FFmpeg và thư viện trong requirements.txt; lần đầu tải model Whisper và YuNet (cần Internet)."
license: "PolyForm Strict 1.0.0 — xem LICENSE"
---

# /ags-clip-shorts — Video Dài → Nhiều Short 9:16

> Lệnh chạy từ thư mục gốc repo AGS Video Editing (hai cấp trên file này) — hoặc từ thư mục của skill nếu dùng bản zip
> (đã kèm `scripts/`, `harness/`) — bằng Python có đủ thư viện (venv của repo: macOS `./venv/bin/python`, Windows `venv\Scripts\python`).

## Bước 1 — Bóc băng
```bash
python scripts/ags_clip_shorts.py transcript <video_dai.mp4> [--model base|small|large-v3-turbo] [--out transcript.json]
```
JSON gồm `duration`, `sentences` (`id`, `start`, `end`, `text` — câu ngắt ở dấu câu, tối đa ~15 s) và `words`
(`start`, `end`, `word`). Transcript là nguồn sự thật cho cả chọn đoạn lẫn phụ đề — không bóc băng lại ở bước 2.

## Bước 2 — Chọn đoạn (việc của agent)
Đọc `sentences`, chọn đoạn theo [references/chon-doan-short.md](references/chon-doan-short.md). Tóm tắt:
- Mở đầu bằng chính câu nêu vấn đề / con số / câu hỏi (thông điệp trong 3 giây đầu), bỏ chào hỏi, dạo đầu.
- Mỗi short trọn một ý, kết thúc ở cuối câu; thường 20–60 s, tối đa 180 s.
- Viết `hook` 3–8 chữ từ đúng nội dung đoạn đó (không hứa điều video không nói).

Ghi `ranges.json` (mốc lấy từ `start` câu đầu và `end` câu cuối; nhận cả dạng `"1:15.5"`):
```json
[{"start": 75.2, "end": 118.9, "hook": "3 SAI LẦM KHI MUA ĐẤT", "name": "sai-lam-mua-dat"}]
```

## Bước 3 — Xuất short
```bash
python scripts/ags_clip_shorts.py cut <video_dai.mp4> --transcript transcript.json --ranges ranges.json \
  [--style karaoke|editorial|none] [--keywords "sổ hồng, pháp lý"] [--highlight-color "#FFD60A"] \
  [--hook-seconds 3] [--no-reframe] [--out-dir shorts/]
# hoặc nhanh: --range 75.2-118.9 --range 4:02-4:41
```
Mỗi đoạn → `shorts/<name>.mp4` (mặc định `<tên>_short_NN.mp4`), cuối cùng in JSON danh sách file.
- Mép đoạn được nắn về ranh giới từ (không cắt giữa chữ), chừa 0.10 s trước / 0.20 s sau mà không lấn sang từ kề bên.
- Video ngang: khung 9:16 bám khuôn mặt (như `/ags-reframe`); `--no-reframe` thì thu nhỏ vừa khung dọc, thêm viền.
- Phụ đề lấy từ transcript, nằm trong vùng an toàn; hook ở đỉnh vùng an toàn, đủ đậm từ khung 0, hiện `--hook-seconds` giây.

## Bước 4 — Kiểm định từng short (bắt buộc)
```bash
python harness/ags_anti_slop_guard.py shorts/<name>.mp4 --contact-sheet shorts/<name>_sheet.jpg
```
Ô `#0 (khung 0)` phải thấy hook; mặt người nói trong khung; chữ trong khung hồng. Exit `0` đạt · `2` cảnh báo · `1` lỗi.
Vòng soát: `harness/QUY-TRINH-KIEM-DINH.md`. Qua MCP: `clip_shorts_transcript` rồi `clip_shorts_cut`.

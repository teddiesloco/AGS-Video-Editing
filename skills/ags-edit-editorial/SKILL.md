---
name: ags-edit-editorial
description: "AGS (Agent Space) — đốt phụ đề tiếng Việt vào video và chuẩn âm lượng -14 LUFS: kiểu editorial (Serif tạp chí) hoặc karaoke (chữ đậm, từ đang nói đổi màu theo đúng mốc từng từ), tô màu từ khoá, chữ luôn nằm trong vùng an toàn 9:16. Dùng khi cần phụ đề, sub, caption, chữ chạy theo giọng, highlight từ khoá cho TikTok/Reels/Shorts hoặc video ngang."
compatibility: "Cần Python 3.10+, FFmpeg (có libass) và thư viện trong requirements.txt; lần đầu tải model Whisper (cần Internet)."
license: "PolyForm Strict 1.0.0 — xem LICENSE"
---

# /ags-edit-editorial — Phụ Đề Tạp Chí / Karaoke & Cân Âm -14 LUFS

> Lệnh chạy từ thư mục gốc repo AGS Video Editing (hai cấp trên file này) — hoặc từ thư mục của skill nếu dùng bản zip
> (đã kèm `scripts/`, `harness/`) — bằng Python có đủ thư viện (venv của repo: macOS `./venv/bin/python`, Windows `venv\Scripts\python`).

```bash
python scripts/ags_editorial_sub.py <video> [--style editorial|karaoke] [--highlight-color "#FFD60A"] \
  [--keywords "bất động sản, sổ hồng"] [--model base] [--out <video_xuat.mp4>]
```
Mặc định xuất `<tên>_<style>.mp4`.

## Hai kiểu phụ đề
| `--style` | Font | Cụm chữ | Hiệu ứng |
|---|---|---|---|
| `editorial` (mặc định) | Serif (Georgia/DejaVu Serif), ~5% cạnh ngắn | ≤ 42 ký tự / ≤ 4 s | câu tĩnh trắng viền đen |
| `karaoke` | Sans đậm, ~6.5% cạnh ngắn | ≤ 24 ký tự / ≤ 2.5 s | từ đang nói đổi sang `--highlight-color` đúng mốc từng từ |

`--keywords` (cách nhau bằng dấu phẩy, nhận cả cụm nhiều từ) được tô `--highlight-color` ở cả hai kiểu.

## Chức năng
1. Faster-Whisper bóc băng theo từng từ, lọc rác Whisper (nhãn `[nhạc]`, từ lặp ≥ 3 lần), chữ chuẩn hoá Unicode NFC.
2. File `.ASS` theo đúng kích thước hiển thị (kể cả video điện thoại có metadata xoay). Video dọc: chữ nằm trong vùng an
   toàn 9:16 định nghĩa trong `scripts/ags_common.py` (`SAFE_ZONE_9X16`, lấy từ tài liệu chính thức của Meta, Google, TikTok);
   video ngang: lề 8%.
3. Chuẩn hoá âm lượng `loudnorm=I=-14:LRA=11:TP=-2.0`, AAC 48 kHz.

## Kiểm định (bắt buộc)
```bash
python harness/ags_anti_slop_guard.py <video_xuat.mp4> --contact-sheet <video_xuat>_sheet.jpg
```
Trên contact sheet: chữ phải nằm trong khung hồng (vùng an toàn), đủ dấu tiếng Việt, kiểu karaoke thấy từ được tô màu.
Exit `0` đạt · `2` cảnh báo · `1` lỗi. Vòng soát: `harness/QUY-TRINH-KIEM-DINH.md`.

---
name: ags-edit-editorial
description: "AGS (Agent Space) — đốt phụ đề tiếng Việt vào video và chuẩn âm lượng -14 LUFS: kiểu clean (Sans đậm trắng, bóng mềm, từ khoá vàng cát; mặc định), editorial (Serif tạp chí) hoặc karaoke (chữ đậm, từ đang nói đổi màu theo đúng mốc từng từ), tô màu từ khoá, chữ luôn nằm trong vùng an toàn 9:16. Dùng khi cần phụ đề, sub, caption, chữ chạy theo giọng, highlight từ khoá cho TikTok/Reels/Shorts hoặc video ngang."
compatibility: "Cần Python 3.10+, FFmpeg (có libass) và thư viện trong requirements.txt; lần đầu tải model Whisper (cần Internet)."
license: "PolyForm Strict 1.0.0 — xem LICENSE"
---

# /ags-edit-editorial — Phụ Đề Tạp Chí / Karaoke & Cân Âm -14 LUFS

> Lệnh chạy từ thư mục gốc skill AGS Video Editing (hai cấp trên file này) bằng Python của venv trong skill
> (macOS/Linux `venv/bin/python`, Windows `venv\Scripts\python.exe`; đường dẫn có dấu cách thì đặt trong ngoặc kép).
> Chưa có venv → làm theo `SKILL.md` ở gốc (`scripts/ags_setup.py --check`, rồi installer).

```bash
python scripts/ags_editorial_sub.py <video> [--style clean|editorial|karaoke] [--highlight-color "#E3C285"] \
  [--keywords "bất động sản, sổ hồng"] [--script <loi.txt>] [--model base] [--out <video_xuat.mp4>]
```
Mặc định xuất `<tên>_<style>.mp4`.

## Ba kiểu phụ đề
| `--style` | Font | Cụm chữ | Hiệu ứng |
|---|---|---|---|
| `clean` (mặc định) | Sans đậm (Montserrat Bold nếu đã cài, không thì Arial Bold/DejaVu Sans Bold/Noto Sans Bold), ~5,8% cạnh ngắn | ≤ 28 ký tự / ≤ 3 s | câu tĩnh chữ trắng, viền mảnh + bóng mềm, tối đa 2 dòng; từ khoá vàng cát `#E3C285` |
| `editorial` | Serif (Georgia/DejaVu Serif), ~5,6% cạnh ngắn | ≤ 34 ký tự / ≤ 4 s | câu tĩnh trắng viền đen |
| `karaoke` | Sans đậm, ~6.5% cạnh ngắn | ≤ 24 ký tự / ≤ 2.5 s | từ đang nói đổi sang `--highlight-color` đúng mốc từng từ |

`--keywords` (cách nhau bằng dấu phẩy, nhận cả cụm nhiều từ) được tô `--highlight-color` ở cả ba kiểu; bỏ trống
`--highlight-color` thì dùng màu mặc định của kiểu (clean `#E3C285`, editorial/karaoke `#FFD60A`). Font là font có sẵn của hệ
điều hành — AGS không đóng gói font (xem `THIRD_PARTY_NOTICES.md`).

## Chức năng
1. Faster-Whisper bóc băng theo từng từ, lọc rác Whisper (nhãn `[nhạc]`, từ lặp ≥ 3 lần), chữ chuẩn hoá Unicode NFC.
   **`--script <loi.txt>`** (UTF-8, đúng lời đọc — ví dụ file đã đưa cho `ags_tts.py`): chữ hiện ĐÚNG theo script, không theo
   Whisper (Whisper `base` hay nghe sai từ tiếng Việt); Whisper chỉ cho mốc thời gian. Từ nghe sai/thiếu được chia mốc theo độ
   dài chữ giữa hai từ khớp liền kề; không từ nào bị sửa, lọc hay bỏ. Khi có lời đọc đã biết, luôn dùng `--script`.
2. File `.ASS` theo đúng kích thước hiển thị (kể cả video điện thoại có metadata xoay). Video dọc: chữ nằm trong hộp an
   toàn 9:16 định nghĩa trong `scripts/ags_common.py` (`SAFE_ZONE_9X16`/`safe_box`, hợp chặt từ tài liệu **quảng cáo** của Meta,
   Google, TikTok — **giới hạn bảo thủ**, không phải luật cho nội dung organic); video ngang: lề 8%. Code chỉ dùng hộp này,
   không có profile theo nền tảng và không tự né mặt/chủ thể.
3. Chữ xuống tối đa **2 dòng** (hook 3 dòng) ở đúng cỡ chữ của kiểu, từ tô màu giữ nguyên; chỉ khi không vừa mới hạ cỡ chữ
   (tối thiểu 75%), và chỉ từ dài hơn cả dòng mới bị thu hẹp riêng — không còn thu nhỏ cả câu cho vừa một dòng.
4. Chuẩn hoá âm lượng `loudnorm=I=-14:LRA=11:TP=-2.0`, AAC 48 kHz.

## Vị trí chữ: agent xem khung hình rồi chọn
Chữ do code đặt theo `safe_box`, **không** theo nội dung khung hình. Trước khi giao, agent mở contact sheet/khung then chốt và
tự kiểm ba thứ: (1) chữ ngoài vùng giao diện nền tảng, (2) chữ không che mặt, sản phẩm, số liệu, logo, (3) chữ ưu tiên nằm
ở không gian trống. Mắt người xem di chuyển theo nội dung từng khung — không có "eye zone" cố định. Title (nêu chủ đề, vài
giây) và caption (lời nói liên tục) là hai vai trò khác nhau; dùng tối đa 1–2 họ chữ, kiểm tra glyph tiếng Việt và giấy
phép font. Cần vị trí overlay mà code không hỗ trợ → báo là khoảng trống chưa hỗ trợ, đề xuất làm tay, không giả vờ đã làm.
Giải thích đầy đủ, nguồn và giới hạn truy cập: `references/layout-and-sources.md`.

## Kiểm định (bắt buộc)
```bash
python harness/ags_anti_slop_guard.py <video_xuat.mp4> --contact-sheet <video_xuat>_sheet.jpg --debug-zones
```
Trên contact sheet: chữ phải nằm trong khung hồng (vùng an toàn), đủ dấu tiếng Việt, kiểu karaoke thấy từ được tô màu.
Exit `0` đạt · `2` cảnh báo · `1` lỗi. Vòng soát: `harness/QUY-TRINH-KIEM-DINH.md`.

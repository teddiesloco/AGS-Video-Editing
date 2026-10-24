---
name: ags-edit-bds
description: "AGS (Agent Space) — dựng video dọc 9:16 (Bất Động Sản và footage bất kỳ) theo 6 bước: phân loại tư liệu, chọn công thức và nhịp cắt theo beat (BPM cho trước hoặc tự dò từ file nhạc), sinh asset (viền thửa đất, lưới phân lô, ticker bản tin, prompt AI hook), render MP4 từ video thật và/hoặc ảnh (giữ chuyển động clip, zoom nhẹ tuỳ chọn, cut/wipe/dissolve, nhạc tự nhỏ khi có giọng đọc; kết hợp giọng đọc TTS + phụ đề + SFX trong một lượt) hoặc draft CapCut thử nghiệm, kiểm định rồi bàn giao. Dùng khi cần video giới thiệu dự án, đất nền phân lô, bản tin quy hoạch, hoặc ghép clip stock/quay tay thành video có lời đọc."
compatibility: "Cần Python 3.10+, FFmpeg và thư viện trong requirements.txt (Pillow, NumPy)."
license: "PolyForm Strict 1.0.0 — xem LICENSE"
---

# /ags-edit-bds — Dựng Video Bất Động Sản (AGS)

> Lệnh chạy từ thư mục gốc skill AGS Video Editing (hai cấp trên file này) bằng Python của venv trong skill
> (macOS/Linux `venv/bin/python`, Windows `venv\Scripts\python.exe`; đường dẫn có dấu cách thì đặt trong ngoặc kép).
> Chưa có venv → làm theo `SKILL.md` ở gốc (`scripts/ags_setup.py --check`, rồi installer).

```bash
python scripts/ags_bds_cli.py <draft|render|parcel|subdivision|ticker|beats|prompt> --help
```
Lệnh chi tiết từng asset, mẫu `lots.json`, prompt AI hook, công thức kỹ xảo làm tay và draft CapCut:
[references/asset-va-xuat.md](references/asset-va-xuat.md).

## Bước 1 — Phân loại tư liệu
| Nhóm | Tư liệu khách có | Công thức |
|---|---|---|
| **A — Dự án đô thị / chung cư / nhà phố** | Video flycam, máy cơ, người review | Cinematic |
| **B — Đất nền / phân lô / tách thửa** | Tọa độ, trích lục sổ, sơ đồ phân lô, ảnh điện thoại | Đất nền (GIS) |
| **C — Bản tin BĐS** | Ảnh flycam / vệ tinh + tin quy hoạch, hạ tầng | Khung bản tin (ticker) |

Thiếu diện tích, giá, pháp lý, trạng thái lô → hỏi lại người dùng. Không tự bịa số liệu.

## Bước 2 — Công thức & nhịp cắt
- **Cinematic (45–90 s):** hook AI 0–3 s → tổng quan & vị trí → tiện ích, nội thất cắt theo beat → CTA (giá, ưu đãi, hotline).
- **Đất nền (45–60 s):** hook vệ tinh → viền thửa (`parcel`) → phân lô (`subdivision`) → ảnh thực tế, pháp lý, hotline.
- **Bản tin:** ảnh nền + `ticker` + giọng đọc.

Mốc cắt theo nhạc:
```bash
python scripts/ags_bds_cli.py beats --music nhac.mp3 --beat-step 4          # tự dò BPM + mốc beat
python scripts/ags_bds_cli.py beats --bpm 120 --beat-step 4 --duration 60   # BPM cho trước
```
Dò beat bằng numpy (onset 30 Hz–4 kHz + tự tương quan 60–180 BPM): hợp nhạc nhịp đều; nhạc đổi tempo thì dùng `--bpm`.
Chữ do engine vẽ tự nằm trong vùng an toàn 9:16 (khung 1080x1920: x 120–780, y 288–1248); tọa độ polygon/ô lô do bạn
đặt — để trong vùng này để không bị nút và caption của TikTok/Reels/Shorts che.

## Bước 3 — Sinh asset
`parcel` (viền thửa phát sáng), `subdivision` (lưới lô Đã bán đỏ / Còn trống xanh / Đang cọc vàng), `ticker`
(bản tin), `prompt` (prompt image-to-video cho Kling/Runway/Luma — engine chỉ sinh prompt). Lệnh đầy đủ: references.

## Bước 4 — Xuất
**Render MP4 (khuyên dùng)** — nhận cả video thật lẫn ảnh, theo đuôi file:
```bash
python scripts/ags_bds_cli.py render --clips out/flycam.mp4 out/grid.jpg out/ticker.jpg \
  --music nhac.mp3 --auto-beat --beat-step 4 [--voice giong_doc.m4a] [--transition wipe|dissolve] [--zoom subtle] [--grade natural|warm] --out out/video_bds.mp4
```
(`--images` là tên cũ của `--clips`, vẫn dùng được.)
- Mỗi clip/ảnh dài đúng `--beat-step` beat (`--auto-beat` dò từ `--music`, hoặc `--bpm`, hoặc `--seconds`). Thời lượng, BPM,
  `--transition-seconds` phải là số hữu hạn > 0; file không tồn tại/không có hình/không có tiếng → báo lỗi trước khi render.
- **Video thật:** giữ nguyên chuyển động (không trích khung tĩnh), phủ kín khung 9:16, lấy từ giây 0 đủ thời lượng cần, bỏ
  tiếng gốc. File ngắn hơn thời lượng cần → báo lỗi nêu tên file (không lặp, không đứng hình): rút thời lượng hoặc chọn clip dài hơn.
- `--zoom`: `auto` (mặc định: ảnh Ken Burns chậm, video giữ nguyên) · `none` · `subtle` (đẩy vào nhẹ 1.06x suốt clip, cả ảnh lẫn video).
- `--grade`: `none` (mặc định, giữ nguyên màu) · `natural` (tương phản +5%, bão hoà +5%) · `warm` (như `natural` + ấm nhẹ ở
  trung tính/vùng sáng). Cùng một công thức cho mọi clip để nhiều nguồn khác nhau nhìn đồng nhất; không đẩy bão hoà.
- **30 giây = 10 nguồn × 3 s:** `--seconds 3 --transition dissolve --transition-seconds 0.5` với đúng 10 file khác nhau. Tổng
  hình đúng 30,00 s (900 khung/30 fps); mỗi clip (trừ clip cuối) phải dài ≥ 3,5 s vì 0,5 s chồng sang cảnh sau, clip cuối ≥ 3 s.
  Giọng đọc ≤ 30 s (ngắn hơn thì đệm im lặng, không kéo giãn tiếng; dài hơn thì báo lỗi); đầu ra được cắt đúng độ dài hình.
- `--transition`: `cut` (mặc định) · `wipe` (quét trái → phải) · `dissolve` (hoà mờ), mỗi chuyển `--transition-seconds` (0.5 s,
  phải ngắn hơn cảnh ngắn nhất); tổng độ dài và mốc beat giữ nguyên.
- `--voice`: giọng đọc; có cả nhạc thì nhạc tự nhỏ xuống khi có giọng (sidechaincompress; đo thử: nhạc giảm ~16 dB
  lúc có giọng, trở lại bình thường khi hết giọng). Giọng ngắn hơn hình thì cuối video im lặng; **giọng dài hơn hình → báo
  lỗi kèm `--seconds` tối thiểu, không bao giờ cắt giọng** — nâng thời lượng hoặc thêm clip rồi chạy lại. Âm lượng cuối -14 LUFS, AAC 48 kHz.
- JSON in ra có `cut_times` (giây bắt đầu mỗi chuyển cảnh) và `total_seconds` để đặt SFX đúng chỗ.

**Draft CapCut (thử nghiệm):** `draft --name ... --clips ... --out drafts/` hoặc `--capcut` — xem references.

### Bước 4b — Một câu tự nhiên → video có footage, lời đọc, chữ và SFX
Người dùng nói kiểu: *"Ghép các clip trong thư mục này thành video dọc 30 giây, có giọng đọc tiếng Việt đọc lời này, hoà
mờ giữa các cảnh, zoom nhẹ, có phụ đề và tiếng click khi chuyển cảnh."* Bạn tự chạy chuỗi sau (đường dẫn tuyệt đối,
`out/` là thư mục đầu ra mới; không hỏi lại người dùng về công cụ):
1. **Footage:** chỉ dùng clip người dùng có quyền dùng (tự quay, hoặc kho miễn phí cho phép chỉnh sửa — đọc giấy phép từng
   clip và ghi nguồn/tác giả vào bàn giao). Không dùng clip chưa rõ quyền. Kiểm số clip `N` và độ dài từng clip (`ffprobe`).
2. **Lời đọc:** viết lời từ thông tin người dùng đưa (không bịa số liệu/giá/pháp lý), ghi UTF-8 vào `out/loi.txt`, rồi
   `python scripts/ags_tts.py synthesize --engine vieneu --text-file out/loi.txt --out out/loi.wav` → JSON có `seconds` = `S`.
3. **Thời lượng mỗi clip:** `T = ceil((S + 0.5) / N * 10) / 10` (tổng hình ≥ giọng + 0,5 s). Mọi clip phải dài ≥ `T` (+ 0,5 s nếu
   có chuyển wipe/dissolve ở clip đó); clip nào ngắn hơn thì thay bằng clip dài hơn hoặc thêm clip rồi tính lại.
4. **Render hình + giọng:**
   ```bash
   python scripts/ags_bds_cli.py render --clips /abs/a.mp4 /abs/b.mp4 /abs/c.mp4 --seconds T \
     --transition dissolve --zoom subtle --voice out/loi.wav [--music /abs/nhac.mp3] --out out/video_raw.mp4
   ```
5. **Chữ (phụ đề theo giọng đọc):**
   `python scripts/ags_editorial_sub.py out/video_raw.mp4 --out out/video_sub.mp4 --style clean --script out/loi.txt --keywords "từ khoá, cụm khác"`
   (`--script out/loi.txt` làm chữ hiện đúng lời đã viết thay vì lời Whisper nghe sai; bỏ `--keywords` nếu không cần; `--style karaoke` cho kiểu từ đang nói đổi màu, `--style editorial` cho Serif tạp chí). Mở contact sheet kiểm chữ đúng chính tả.
6. **SFX tại các chỗ chuyển:** ghi `out/events.json` — mỗi phần tử `cut_times` của bước 4 thành
   `{"file": "pluck_001.ogg", "time": <giây>, "gain": 0.2}` — rồi
   `python scripts/ags_sfx.py mix out/video_sub.mp4 --events out/events.json --out out/video_final.mp4`.
7. **Kiểm định + bàn giao:** Bước 5–6 trên `out/video_final.mp4`; kèm nguồn/giấy phép từng clip và nêu rõ giọng là giọng tổng hợp.

## Bước 5 — Kiểm định
```bash
python harness/ags_anti_slop_guard.py out/video_bds.mp4 --contact-sheet out/video_bds_sheet.jpg
```
Exit `0` đạt · `2` cảnh báo (đọc và xử lý) · `1` lỗi (không bàn giao). Draft CapCut: xuất MP4 từ CapCut rồi chạy guard.
Vòng soát: `harness/QUY-TRINH-KIEM-DINH.md`.

## Bước 6 — Bàn giao
`[File] -> [Thời lượng] -> [LUFS] -> [Kết quả guard]`, kèm danh sách asset, đường dẫn draft (nếu có) và phần cần làm tay
trong CapCut (clip AI hook, SFX, radar tiện ích). Qua MCP: tool `bds_render`, `bds_draft`.
Tool `bds_render` nhận `clips` (hoặc `images`), `zoom`, `grade`, `transition` (`cut|wipe|dissolve`) và `voice`; chuỗi 4b dùng thêm
`tts_synthesize`, `editorial_sub`, `sfx_mix`, `anti_slop_guard`.

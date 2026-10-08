---
name: ags-edit-bds
description: "AGS (Agent Space) — dựng video Bất Động Sản dọc 9:16 theo 6 bước: phân loại tư liệu, chọn công thức và nhịp cắt theo beat (BPM cho trước hoặc tự dò từ file nhạc), sinh asset (viền thửa đất, lưới phân lô, ticker bản tin, prompt AI hook), render MP4 (Ken Burns, wipe trước/sau, nhạc tự nhỏ khi có giọng đọc) hoặc draft CapCut thử nghiệm, kiểm định rồi bàn giao. Dùng khi cần video giới thiệu dự án, đất nền phân lô, bản tin quy hoạch."
compatibility: "Cần Python 3.10+, FFmpeg và thư viện trong requirements.txt (Pillow, NumPy)."
license: "PolyForm Strict 1.0.0 — xem LICENSE"
---

# /ags-edit-bds — Dựng Video Bất Động Sản (AGS)

> Lệnh chạy từ thư mục gốc repo AGS Video Editing (hai cấp trên file này) — hoặc từ thư mục của skill nếu dùng bản zip
> (đã kèm `scripts/`, `harness/`) — bằng Python có đủ thư viện (venv của repo: macOS `./venv/bin/python`, Windows `venv\Scripts\python`).

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
**Render MP4 (khuyên dùng):**
```bash
python scripts/ags_bds_cli.py render --images out/parcel.jpg out/grid.jpg out/ticker.jpg \
  --music nhac.mp3 --auto-beat --beat-step 4 [--voice giong_doc.m4a] [--transition wipe] --out out/video_bds.mp4
```
- Ken Burns chậm; mỗi ảnh dài đúng `--beat-step` beat (`--auto-beat` dò từ `--music`, hoặc `--bpm`, hoặc `--seconds`).
- `--transition wipe`: quét trái → phải 0.5 s (`--transition-seconds`), hợp cặp ảnh trước/sau; tổng độ dài và mốc beat giữ nguyên.
- `--voice`: giọng đọc; có cả nhạc thì nhạc tự nhỏ xuống khi có giọng (sidechaincompress; đo thử: nhạc giảm ~16 dB
  lúc có giọng, trở lại bình thường khi hết giọng). Âm lượng cuối -14 LUFS, AAC 48 kHz.

**Draft CapCut (thử nghiệm):** `draft --name ... --clips ... --out drafts/` hoặc `--capcut` — xem references.

## Bước 5 — Kiểm định
```bash
python harness/ags_anti_slop_guard.py out/video_bds.mp4 --contact-sheet out/video_bds_sheet.jpg
```
Exit `0` đạt · `2` cảnh báo (đọc và xử lý) · `1` lỗi (không bàn giao). Draft CapCut: xuất MP4 từ CapCut rồi chạy guard.
Vòng soát: `harness/QUY-TRINH-KIEM-DINH.md`.

## Bước 6 — Bàn giao
`[File] -> [Thời lượng] -> [LUFS] -> [Kết quả guard]`, kèm danh sách asset, đường dẫn draft (nếu có) và phần cần làm tay
trong CapCut (clip AI hook, SFX, radar tiện ích). Qua MCP: tool `bds_render`, `bds_draft`.

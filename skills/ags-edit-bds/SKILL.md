---
name: ags-edit-bds
description: "AGS (Agent Space) — dựng video Bất Động Sản theo 6 bước: phân loại tư liệu (Nhóm A/B/C), chọn công thức & timeline theo beat, sinh asset (viền ranh giới thửa đất, lưới phân lô, ticker bản tin, mốc cắt beat, prompt AI hook), xuất draft CapCut (thử nghiệm) hoặc render MP4 9:16 bằng FFmpeg, kiểm định Anti-Slop rồi bàn giao."
---

# /ags-edit-bds — Dựng Video Bất Động Sản (AGS)

Dành cho khi: cần video dọc 9:16 giới thiệu dự án, đất nền phân lô hoặc bản tin quy hoạch — kể cả khi tư liệu chỉ có ảnh điện thoại, ảnh vệ tinh và sơ đồ phân lô.

Mọi lệnh chạy từ thư mục gốc repo AGS Video Editing (hai cấp trên thư mục chứa file này) bằng Python của venv (macOS `./venv/bin/python`, Windows `venv\Scripts\python`):
```bash
python scripts/ags_bds_cli.py <draft|render|parcel|subdivision|ticker|beats|prompt> --help
```
Tọa độ (polygon, ô lô) tính theo khung đầu ra 1080x1920. Ảnh nền được cắt cho vừa khung, không bị kéo méo.

---

## Bước 1 — Phân loại tư liệu (Nhóm A / B / C)

| Nhóm | Tư liệu khách có | Công thức |
|---|---|---|
| **A — Dự án đô thị / chung cư / nhà phố** | Video flycam, máy cơ, người review (A-roll) | Công thức Dự án Đô thị (Cinematic) |
| **B — Đất nền / phân lô / tách thửa** | Tọa độ Google Maps, trích lục sổ đỏ, sơ đồ phân lô, ảnh điện thoại | Công thức Đất nền (GIS) |
| **C — Bản tin BĐS** | Ảnh flycam / vệ tinh + bài báo quy hoạch, hạ tầng | Khung Bản tin (ticker) |

Thiếu thông tin (diện tích, giá, pháp lý, trạng thái lô) → hỏi lại người dùng. Không tự bịa số liệu.

## Bước 2 — Chọn công thức & timeline

**Công thức Dự án Đô thị (Cinematic), 45–90 giây**
- `0–3s` Hook: clip AI "Hiệu ứng Tòa nhà rơi" (Bước 3) + SFX va chạm.
- `3–15s` Tổng quan & vị trí: flycam lượn 360°, chữ tiêu đề.
- `15–45s` Tiện ích & nội thất: cắt theo beat, nhịp 1 toàn : 2 cận, clip Virtual Staging.
- `45–60s` CTA: chính sách giá, ưu đãi, hotline.

**Công thức Đất nền (GIS), 45–60 giây**
- `0–5s` Hook vệ tinh: zoom từ bản đồ xuống thửa đất.
- `5–20s` Ranh giới & quy hoạch: viền polygon phát sáng (`parcel`).
- `20–45s` Mặt bằng phân lô: Đã bán (đỏ) / Còn trống (xanh) / Đang cọc (vàng) + diện tích, giá (`subdivision`).
- `45–60s` Thực tế & pháp lý: ảnh chụp thực tế, sổ hồng, hotline.

**Khung Bản tin (Nhóm C):** ảnh nền + thanh tiêu đề đỏ + thanh nội dung (`ticker`), giọng đọc thuyết minh.

**Nhịp cắt theo nhạc** — tính mốc cắt từ BPM của bài nhạc nền:
```bash
python scripts/ags_bds_cli.py beats --bpm 120 --beat-step 4 --duration 60
```
- Cảnh toàn giữ 2–3s, cảnh cận 0.8–1.2s; không để 3 cảnh toàn (hoặc 3 cảnh cận) liên tiếp.
- Chuỗi gợi ý: Toàn → Cận chi tiết → Trung → Cận góc nghệ thuật → Toàn.
- Chữ: font không chân đậm, vàng kim `#F7B503` hoặc trắng, viền đen; đặt trong vùng an toàn 9:16 (tránh ~150px trên, ~370px dưới, ~120px mép phải — nơi nút và caption của TikTok/Reels).

## Bước 3 — Sinh asset

```bash
# Viền ranh giới thửa đất phát sáng (neon đỏ, nhãn ở tâm)
python scripts/ags_bds_cli.py parcel --image vetinh.jpg \
  --points "300,700 800,750 750,1200 250,1150" --label "LÔ ĐẤT 500M² SỔ ĐỎ" --out out/parcel.jpg

# Lưới phân lô đổi màu theo trạng thái
python scripts/ags_bds_cli.py subdivision --image matbang.jpg --lots lots.json --out out/grid.jpg

# Khung bản tin BĐS
python scripts/ags_bds_cli.py ticker --image flycam.jpg --headline "Cao tốc mới" \
  --text "Khởi công mở rộng nút giao kết nối khu dân cư" --out out/ticker.jpg
```
`lots.json` — `status` là `SOLD`, `AVAILABLE` hoặc `DEPOSITED`; `rect` = `[x1, y1, x2, y2]`:
```json
[
  {"code": "Lô 01", "status": "SOLD", "rect": [150, 600, 480, 850], "area": "120m²", "price": "1.2 Tỷ"},
  {"code": "Lô 02", "status": "AVAILABLE", "rect": [520, 600, 850, 850], "area": "115m²", "price": "1.15 Tỷ"}
]
```

**Prompt AI hook** cho công cụ image-to-video bên ngoài (Kling / Runway / Luma — người dùng tự chạy, engine chỉ sinh prompt):
```bash
python scripts/ags_bds_cli.py prompt --type falling_building --name "Dự án Mẫu" --location "Đồng Nai"
# --type: falling_building | virtual_staging | day_to_night
```

### Công thức kỹ xảo AI (làm tay trong CapCut)
1. **Hiệu ứng Tòa nhà rơi:** cắt khung hình cuối của cảnh người đứng ở bãi đất trống → chạy prompt `falling_building` → ghép lại, thêm hiệu ứng `Shake` 0.5s đúng lúc tiếp đất + SFX `Explosion Impact`, `Low Earth Thud`, `Whoosh`.
2. **Virtual Staging (nội thất bay vào nhà trống):** chụp góc phòng thô → prompt `virtual_staging` → SFX `Magic Swoosh`, `Wood Click` theo nhịp đồ đạc lắp vào.
3. **Radar tiện ích:** vòng sóng lan từ tâm lô đất (1 / 2 / 5 km) + ghim trường học, bệnh viện, chợ, nút giao; SFX `Digital Ping` / `Sonar Sweep`.

## Bước 4 — Xuất: draft CapCut (thử nghiệm) HOẶC render MP4

**4a. Draft CapCut — THỬ NGHIỆM**
```bash
python scripts/ags_bds_cli.py draft --name "DuAn_Mau" \
  --clips intro.mp4 out/parcel.jpg out/grid.jpg out/ticker.jpg \
  --bpm 120 --beat-step 4 --title "ĐẤT NỀN SỔ ĐỎ" --music nhac.mp3 --out drafts/
# hoặc ghi thẳng vào thư mục draft của CapCut desktop:
python scripts/ags_bds_cli.py draft --name "DuAn_Mau" --clips ... --capcut
```
- Sinh thư mục `<tên>/` gồm `draft_info.json` (CapCut macOS đọc), `draft_content.json` (CapCut Windows đọc, cùng nội dung) và `draft_meta_info.json`.
- Timeline: track video (clip/ảnh nối liền, mỗi clip = `--beat-step` beat hoặc `--seconds`; không truyền thì video giữ nguyên độ dài, ảnh 3s), track chữ (tiêu đề 4s đầu, vàng kim viền đen), track audio (nhạc kéo bằng track hình).
- Media được tham chiếu bằng đường dẫn tuyệt đối — không di chuyển file sau khi tạo draft. Không bao giờ ghi đè thư mục đã tồn tại.
- Thư mục draft CapCut: macOS `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/`, Windows `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\`.
- **Đã kiểm chứng:** JSON hợp lệ; bộ trường top-level, materials, track, segment và `draft_meta_info.json` trùng khớp với một draft thật của CapCut desktop (macOS, định dạng `version` 360000); tham chiếu material/segment đầy đủ; đã tạo thử trong thư mục draft thật rồi xoá. **Chưa kiểm chứng:** mở draft trong giao diện CapCut. Nếu CapCut không hiện hoặc báo lỗi draft → dùng 4b.

**4b. Render MP4 9:16 trực tiếp bằng FFmpeg**
```bash
python scripts/ags_bds_cli.py render --images out/parcel.jpg out/grid.jpg out/ticker.jpg \
  --bpm 120 --beat-step 4 --music nhac.mp3 --out out/video_bds.mp4
```
Mỗi ảnh zoom chậm Ken Burns, cắt cứng đúng nhịp; có nhạc thì chuẩn hoá -14 LUFS (AAC 48 kHz), nhạc ngắn hơn được đệm im lặng, dài hơn bị cắt theo hình.

## Bước 5 — Kiểm định Anti-Slop
```bash
python harness/ags_anti_slop_guard.py out/video_bds.mp4
```
Exit `0` = đạt · `2` = có cảnh báo (đọc và xử lý trước khi bàn giao) · `1` = lỗi nghiêm trọng (không bàn giao).
Với draft CapCut: xuất video từ CapCut xong thì chạy guard trên file MP4 đó.

## Bước 6 — Bàn giao
Báo ngắn gọn: `[File] -> [Thời lượng] -> [LUFS] -> [Kết quả guard]`, kèm danh sách asset (parcel / grid / ticker), đường dẫn draft (nếu có) và các phần cần làm tay trong CapCut (clip AI hook, SFX, radar tiện ích).

**Qua MCP:** tool `bds_draft` và `bds_render` (xem HUONG-DAN-SU-DUNG.md).

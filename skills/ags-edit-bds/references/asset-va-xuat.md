# ags-edit-bds — Lệnh asset, prompt AI và draft CapCut

Lệnh chạy từ thư mục gốc repo (hoặc thư mục skill khi dùng bản zip). Tọa độ tính theo khung đầu ra 1080x1920; ảnh nền
được cắt cho vừa khung, không kéo méo.

## Asset
```bash
# Viền ranh giới thửa đất phát sáng (neon đỏ, nhãn ở tâm, nhãn luôn trong vùng an toàn)
python scripts/ags_bds_cli.py parcel --image vetinh.jpg \
  --points "300,700 760,750 700,1200 250,1150" --label "LÔ ĐẤT 500M² SỔ ĐỎ" --out out/parcel.jpg

# Lưới phân lô đổi màu theo trạng thái
python scripts/ags_bds_cli.py subdivision --image matbang.jpg --lots lots.json --out out/grid.jpg

# Khung bản tin: thanh tiêu đề đỏ + thanh nội dung, đáy thanh chạm đáy vùng an toàn
python scripts/ags_bds_cli.py ticker --image flycam.jpg --headline "Cao tốc mới" \
  --text "Khởi công mở rộng nút giao kết nối khu dân cư" --out out/ticker.jpg
```
`lots.json` — `status`: `SOLD` (đỏ, ĐÃ BÁN) · `AVAILABLE` (xanh, CÒN TRỐNG) · `DEPOSITED` (vàng, ĐANG CỌC); `rect` = `[x1, y1, x2, y2]`:
```json
[
  {"code": "Lô 01", "status": "SOLD", "rect": [150, 600, 440, 850], "area": "120m²", "price": "1.2 Tỷ"},
  {"code": "Lô 02", "status": "AVAILABLE", "rect": [470, 600, 760, 850], "area": "115m²", "price": "1.15 Tỷ"}
]
```

## Prompt AI hook (công cụ image-to-video bên ngoài — người dùng tự chạy)
```bash
python scripts/ags_bds_cli.py prompt --type falling_building --name "Dự án Mẫu" --location "Đồng Nai"
# --type: falling_building | virtual_staging | day_to_night
```
Công thức làm tay trong CapCut:
1. **Tòa nhà rơi:** lấy khung cuối cảnh bãi đất trống → prompt `falling_building` → ghép lại, thêm `Shake` 0.5 s lúc
   tiếp đất + SFX va chạm.
2. **Virtual Staging:** ảnh phòng thô → prompt `virtual_staging`; cặp ảnh trước/sau dùng `render --transition wipe`.
3. **Radar tiện ích:** vòng sóng lan từ tâm lô đất (1 / 2 / 5 km) + ghim trường học, bệnh viện, chợ, nút giao.

## Draft CapCut — THỬ NGHIỆM
```bash
python scripts/ags_bds_cli.py draft --name "DuAn_Mau" \
  --clips intro.mp4 out/parcel.jpg out/grid.jpg out/ticker.jpg \
  --music nhac.mp3 --auto-beat --beat-step 4 --title "ĐẤT NỀN SỔ ĐỎ" --out drafts/
# hoặc ghi thẳng vào thư mục draft của CapCut desktop:
python scripts/ags_bds_cli.py draft --name "DuAn_Mau" --clips ... --capcut
```
- Sinh `<tên>/` gồm `draft_info.json` (CapCut macOS đọc), `draft_content.json` (CapCut Windows đọc, cùng nội dung),
  `draft_meta_info.json`. Không bao giờ ghi đè thư mục đã có.
- Timeline: track video (clip/ảnh nối liền, mỗi clip = `--beat-step` beat, `--seconds`, hoặc độ dài gốc; ảnh mặc định 3 s),
  track chữ (tiêu đề 4 s đầu, vàng kim viền đen), track audio (nhạc kéo bằng track hình).
- Media tham chiếu bằng đường dẫn tuyệt đối — không di chuyển file sau khi tạo draft.
- Thư mục draft CapCut: macOS `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/`,
  Windows `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\`.
- **Đã kiểm chứng:** JSON hợp lệ; bộ trường trùng khớp một draft thật của CapCut desktop (macOS, `version` 360000);
  tham chiếu material/segment đầy đủ. **Chưa kiểm chứng:** mở draft trong giao diện CapCut — lỗi thì dùng `render`.

### Bằng chứng CapCut (đã đọc README/license chính, 2026-10-08)
Ba việc khác nhau — đừng gộp:
1. **Sửa draft (JSON cục bộ):** `capcut-cli` — https://github.com/renezander030/capcut-cli (MIT: README, GitHub API, file LICENSE).
   README nói công cụ đọc/ghi trực tiếp `draft_content.json`/`draft_info.json`; draft mở ra trong CapCut/JianYing để chỉnh
   tiếp. Chính README ghi: khi populate dự án app tạo sẵn, "desktop acceptance on your app build remains unverified".
2. **Xem trước:** `capcut render` là proxy ffmpeg độ phân giải thấp, README ghi rõ "not CapCut's final render" — không dùng
   làm bản export cuối.
3. **Export bằng giao diện CapCut:** `pyCapCut` — https://github.com/GuanYixuan/pyCapCut sinh draft và có module tự động hoá UI
   để export (phụ thuộc `uiautomation` trên Windows); README nói draft vẫn cần export trên CapCut bản Windows và module batch
   export đang di chuyển (thử nghiệm). **Không thấy file LICENSE ở gốc repo, GitHub API báo license = null** → giấy phép chưa rõ,
   không sao chép mã.

Chưa kiểm chứng: mở draft do AGS sinh trong bản CapCut hiện hành. AGS không thêm dependency hay vendor nào từ hai dự án trên.

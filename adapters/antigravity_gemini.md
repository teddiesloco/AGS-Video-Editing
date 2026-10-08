# 🛡️ AGS Harness cho Google Antigravity & Gemini Agent

Quy tắc bắt buộc cho Gemini / Antigravity khi chạy tác vụ edit video trong repo AGS Video Editing của AGS (Agent Space).

---

## 🚫 3 ĐIỀU CẤM ĐỂ TRÁNH "AI SLOP"

1. **CẤM TỰ VIẾT LỆNH FFMPEG DÀI BẰNG TAY**
   - ❌ **SAI:** tự sinh `ffmpeg -vf ...` phức tạp trong terminal (dễ sai nháy đơn/nháy kép, sai filter graph, lệch framerate).
   - ✅ **ĐÚNG:** gọi script có sẵn trong `scripts/` bằng Python của venv (`./venv/bin/python` trên macOS, `venv\Scripts\python` trên Windows):
     ```bash
     python scripts/ags_cut_silence.py "input.mp4"
     python scripts/ags_text_behind_person.py "input.mp4" --text "TIÊU ĐỀ"
     python scripts/ags_editorial_sub.py "input.mp4"
     ```
   - Nếu workspace đã cấu hình MCP server `ags` (xem HUONG-DAN-SU-DUNG.md, Phần 3), ưu tiên gọi tool MCP thay vì terminal.

2. **CẤM KỂ LỂ TỪNG BƯỚC**
   - ❌ **SAI:** "Bây giờ tôi sẽ kiểm tra file... Tiếp theo tôi sẽ chạy lệnh..."
   - ✅ **ĐÚNG:** chạy tool ngay. Xong chỉ báo: `[Video đầu ra] -> [Thời lượng] -> [LUFS] -> [Kết quả guard]`.

3. **BẮT BUỘC CHẠY ANTI-SLOP GUARD TRƯỚC KHI BÁO XONG**
   ```bash
   python harness/ags_anti_slop_guard.py "video_output.mp4"
   ```
   - Exit `0`: đạt (đọc được, có tiếng, hình-tiếng khớp, -14 ± 2 LUFS, không đen màn hình ≥ 0.5s) → được bàn giao.
   - Exit `2`: có cảnh báo → đọc từng cảnh báo, sửa hoặc báo rõ cho người dùng.
   - Exit `1`: lỗi nghiêm trọng → không bàn giao.

---

## 📋 BẢNG ÁNH XẠ LỆNH

| Yêu cầu của người dùng | Lệnh terminal | Tool MCP |
|---|---|---|
| Cắt video thô, lọc "ờ à", bỏ khoảng lặng | `python scripts/ags_cut_silence.py <input>` | `cut_silence` |
| Chữ chìm sau người | `python scripts/ags_text_behind_person.py <input> --text "<HOOK>"` | `text_behind_person` |
| Phụ đề tạp chí & chuẩn âm thanh | `python scripts/ags_editorial_sub.py <input>` | `editorial_sub` |
| Ghi âm thành chữ 2D | `python scripts/ags_voice_to_kinetic.py <audio>` | `voice_to_kinetic` |
| Ghi âm thành người que nét chì | `python scripts/ags_voice_to_doodle.py <audio>` | `voice_to_doodle` |
| Video BĐS: ảnh viền thửa / phân lô / ticker | `python scripts/ags_bds_cli.py parcel\|subdivision\|ticker ...` | — |
| Video BĐS: render MP4 9:16 | `python scripts/ags_bds_cli.py render --images ... --out ...` | `bds_render` |
| Video BĐS: draft CapCut (thử nghiệm) | `python scripts/ags_bds_cli.py draft --name ... --clips ... --out ...` | `bds_draft` |
| Kiểm tra chất lượng | `python harness/ags_anti_slop_guard.py <output.mp4>` | `anti_slop_guard` |

Quy trình BĐS đầy đủ (6 bước): `skills/ags-edit-bds/SKILL.md`.

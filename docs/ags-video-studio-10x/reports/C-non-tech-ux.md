# Báo cáo lát C — Trải nghiệm không-kỹ-thuật (FR-003, FR-017, NFR-004)

## File đã đổi / tạo
| File | Thay đổi |
|---|---|
| `skills/ags-studio/SKILL.md` (mới) | Frontmatter chuẩn như các skill trong `skills/` (`name`, `description` 705 ký tự, `compatibility`, `license`; `check_skill` không lỗi). Bảng chọn món 9 món; mẫu gợi ý của từng món lấy từ `ags_studio.py menu --json` (`config/menu.json`, không lặp bảng ánh xạ thứ hai). Quy tắc lời thường; quy trình 6 bước gọi đúng CLI đã có: `ags_studio.py intake/quote/run/revise/variants/menu`, `ags_vi_script.py validate/hook/claims/profile`; hỏi ngược đúng 3 câu theo thứ tự, bỏ câu đã có trong `answers`, ảnh AI chỉ khi khách tự nhắc (`--images ai`, không thành câu thứ 4); agent viết kịch bản Việt hoá (câu đầu = câu mở đọc, `--duration` = `duration_sec` của mẫu) rồi `validate`/`hook`/`claims` tới khi đạt (OQ-002); `quote --script-file --hook-text [--claims-file --source-url --source-file]` báo VND + CHỜ "chạy" (chỉ khi đó mới `--confirmed`); ảnh lưới để duyệt; `revise --say` nguyên văn; `variants --hook ×3`; luật nội dung (3 màu `#A8FF3E/#FFD166/#FF5A5F`, BR-012 `claim_source`, không hứa thu nhập/lượt xem, không nhái tài khoản/không ghi số người theo dõi, không ghi khoá); bảng E-001..014 lời theo đặc tả + việc agent làm tiếp; bảng tool MCP. |
| `SKILL.md` | Bảng chọn món 3 cột ngay sau tiêu đề; mô tả frontmatter cập nhật (759 ký tự); danh sách thành 10 skill, thêm `ags-studio`. |
| `README.md` | Bảng chọn món + đoạn "Nói xong thì sao?" ở đầu; 10 skill; lệnh trực tiếp; MCP 27 tool (16 cũ + 11 `ags_studio_*`); đổi ví dụ hook "90 NGÀY KIẾM 1 TỶ" (hứa thu nhập) thành "3 SAI LẦM KHI MUA ĐẤT". |
| `HUONG-DAN-SU-DUNG.md` | Bảng chọn món + quy trình 6 bước cho khách + bảng "anh/chị nói → trợ lý đổi" + màu chữ + cam kết nội dung + giọng Google AI (đặt `GEMINI_API_KEY` trên máy, không dán vào chat) + bảng lỗi lời thường E-001..014 ở đầu; ghi chú trung thực "hội thoại trong từng client chưa thử tay"; Phần 2/3 thêm lệnh và tool studio. |
| `AGENTS.md` | Định tuyến "làm video cho ngành X" → `skills/ags-studio/SKILL.md`; 2 dòng lệnh mới; quy tắc 7 cho phép giọng `gemini` khi khách chọn + đã đồng ý chi phí; quy tắc 8 (không hứa, không bịa số, không nhái kênh, không ghi khoá); danh sách tool MCP. (Codex và Antigravity đọc file này.) |
| `.cursor/rules/ags-video-editing.mdc` | Mô tả + gạch đầu dòng trỏ `@skills/ags-studio/SKILL.md`. |
| `gemini-extension.json` | Mô tả có AGS Video Studio. |
| `mcp/ags_mcp_server.py` | Tách `_exec` (giấy phép + subprocess) dùng chung cho `_run` và `_studio`; 11 tool: `ags_studio_menu/intake/quote/run/revise/variants/proof/validate_script/hook/claims/profile`, trả `exit_code`, `result` (JSON đầy đủ của lệnh, không cắt đuôi), `stderr_tail`, `stdout_tail`. `run/revise/variants/proof` chỉ thêm `--confirmed` khi `confirmed=true`; `claims`/`source_text` ghi ra file tạm rồi truyền `--claims-file`/`--source-file`. |
| `scripts/ags_build_skill_zips.py` | `TOP_DIRS` thêm `config` (menu/bảng giá/mẫu câu vào gói — `ags_build_protected_client.py` dùng chung danh mục này nên bản niêm cũng có `config/`); docstring 10 skill. KHÔNG đóng gói lại `dist/`. |
| `tests/ags_test_installer.py` | Thêm `test_studio_skill_reaches_all_four_clients`. |
| `CHANGELOG.md` | Mục "Chưa phát hành". |

`scripts/ags_setup.py` **không cần sửa**: `skill_payloads()` đã quét `skills/*/SKILL.md` có tên `ags-*`, nên `ags-studio` tự được chép vào `~/.claude/skills`, `~/.codex/skills`, `~/.gemini/antigravity/skills`; khối `~/.codex/AGENTS.md` và extension Antigravity trỏ về `AGENTS.md` đã cập nhật. Cursor: theo cursor.com/docs/skills Cursor nạp cả `~/.claude/skills` và `~/.codex/skills` (mục tương thích), cộng rule `~/.cursor/rules/ags-video-editing.mdc` trỏ tới skill. Không có `CLAUDE.md`/`CODEX.md` trong sản phẩm. Danh mục niêm (`embed_origin_seal`) áp cho mọi `.md` lúc dựng, không có file danh mục riêng cần sửa.

## Kết quả chạy (venv của sản phẩm, `venv/bin/python -m unittest ...`, sau khi A/B đã ghi file)
- `tests.ags_test_installer`: **4/4 OK** (3 test cũ + `test_studio_skill_reaches_all_four_clients`). Trước khi lát B ghi `ags_studio.py`, test mới FAIL đúng chỗ "skill trỏ tới lệnh phải có trong gói" — chứng minh test bắt được.
- `tests.ags_test_shield`: **17/17 OK**. Trước khi A/B ghi script, 3 test đóng gói ERROR vì tài liệu nhắc `scripts/ags_studio.py`/`ags_vi_script.py` chưa tồn tại (cổng `validate` của bộ đóng gói hoạt động đúng).
- Chạy thật 12 lời gọi tool MCP `ags_studio_*` trên thư mục việc tạm (không mạng): `menu` 0; `intake` câu "30 năm tư duy kinh doanh… về dòng tiền, kiểu Business Thinking" → tự điền chủ đề + mẫu, chỉ hỏi câu 3 (giọng); trả lời "lung tung" → exit 2 `E-...-002` kèm lựa chọn; `quote` 0 (0 đồng, chưa có bảng giá); `run` không xác nhận → exit 2 `E-...-003`; `hook` không `spoken` → thư viện 8 loại; câu chào → `E-...-012`; `validate` kịch bản 5 từ → `E-...-005`; `claims` "Tôi kiếm 50 triệu…" không nguồn → `E-...-013`; `revise` "làm đẹp hơn" → `E-...-010` + 3 gợi ý; `variants` khi chưa có video → `E-...-011`.
- Không chạy: core/bds/blender/reels (lát C không đụng file của chúng); không đóng gói `dist/`; không render video (lát D).
- `ags_build_skill_zips.validate()` trên cây nguồn đầy đủ còn 2 lỗi CÓ SẴN, không do lát C: `scripts/ags_blender_3d.py` import `ags_reels_pipeline` (ngoài gói) và `tests/ags_test_shield.py` chứa chuỗi cấm `/Users/` — làm `python scripts/ags_build_skill_zips.py` dừng; bản niêm (`ags_build_protected_client.py`) loại 2 file đó nên vẫn qua.

## Điểm lệch / diễn giải spec
1. FR-003 liệt kê "du lịch"; giao việc liệt kê "Jetlag-Việt hoá" thay chỗ — bảng có cả hai (9 món).
2. E-007 ghi "dán khoá": tài liệu hướng dẫn hiểu là đặt `GEMINI_API_KEY` trong môi trường máy khách, không dán vào khung chat (giữ AC-010 không rò khoá).
3. FR-017 nói `dist/ags-client-protected.zip` "đóng lại" — theo giao việc KHÔNG đóng gói lại `dist/`; danh mục gói (`TOP_DIRS`) đã có `config/`.
4. Spec không chốt cờ CLI ngoài tên lệnh; dùng đúng `argparse` thật của `scripts/ags_studio.py` (lát B) và `scripts/ags_vi_script.py` (lát A) sau khi hai lát ghi file.
5. Đơn giá VND không ghi cứng trong tài liệu (lấy từ `config/pricing.json` của lát B, hiện để `null` = "chưa có bảng giá"); chỉ ghi "0 đồng" cho giọng miễn phí + hình miễn phí theo BR-004.
6. Cursor không được chép thư mục skill riêng (`~/.cursor/skills`) để tránh trùng tên với thư mục tương thích Claude/Codex mà Cursor đã nạp; chạy `--targets cursor` đơn lẻ thì Cursor chỉ có rule trỏ tới skill.
7. `config/menu.json` (lát B) có 8 món, ghép "Jetlag" vào món giáo dục/du lịch; bảng trong tài liệu có 9 dòng (thêm dòng Jetlag-Việt hoá theo giao việc). Ánh xạ món → mẫu chỉ nằm ở `menu.json`.

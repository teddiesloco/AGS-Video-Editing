# Báo cáo lát A — Ngôn ngữ & hook (24/10/2026)

## File đã tạo
| File | Nội dung |
|---|---|
| `scripts/ags_vi_script.py` | `validate_script`, `score_hook`, `check_claims`, `pick_keywords`, `profile_samples` + CLI `validate|hook|claims|profile --json`. Chỉ stdlib, Python 3.9+ (đã chạy test bằng `/usr/bin/python3` 3.9.6). CLI gọi `assert_client_licensed()` (BR-009). Mã thoát 0 đạt / 1 chưa đạt / 2 sai tham số. |
| `config/hooks-vi.json` | 8 loại hook (noi-dau, nghich-ly, ket-qua, cau-hoi, canh-bao, truoc-sau, pov, nua-cau), mỗi loại khung + 3 ví dụ ≤ 8 từ, không số liệu cá nhân; `rules` (14/8 từ, ≤1 s, ≤5 s, luân phiên ≥ 3 loại). |
| `config/formats-vi.json` | 6 mẫu (`thirty-years-60s`, `sai-lam-90`, `truoc-sau`, `nghich-ly`, `pov`, `jetlag-vi`), bí danh `business-thinking-60s → thirty-years-60s`. Mỗi mẫu: `beats` hook/body/close/cta (tổng giây = `duration_sec`, hook ≤ 5 s), `duration_range`, `ideas`, `scenes` (≥ thời lượng/2,5), `images`, `motions`, `transitions`, `keyword_color`, `hook_types` (≥ 3), `voice_style` (cho Gemini FR-024). |
| `config/keywords-vi.json` | `colors` (tien `#A8FF3E`, nhan `#FFD166`, canh-bao `#FF5A5F`), cụm từ khoá theo nhãn, đơn vị tiền/thời gian, từ chức năng. |
| `tests/ags_test_vi_script.py` | 9 test (unittest, không mạng). |
| `tests/fixtures/vi_script_good.txt` (144 từ), `vi_script_calque.txt`, `source_overlap.txt` | Dữ liệu mẫu theo US-003. |

## Hành vi chính
- **Đếm từ** = token tách bằng dấu cách sau khi bỏ dấu câu hai đầu (tức là đếm theo tiếng; `99k`, `1,9tr`, `40%` = 1 từ). Câu tách ở `. ! ? …` + khoảng trắng hoặc xuống dòng.
- **validate** (E-005 / E-004; `sentence` = số câu từ 1, 0 = lỗi cả bài; thêm trường `rule` cho máy đọc): câu > 16 từ; TB > 11; từ không-Việt > 3% (kiểm âm tiết tiếng Việt sau khi bỏ dấu; viết tắt toàn chữ hoa và `ALLOWED_FOREIGN` được miễn); `CALQUE_PATTERNS` (là một trong những, chính là việc, nó là, bạn có thể ≥ 2 lần, điều này có nghĩa là, đóng (một) vai trò quan trọng, vào cuối ngày); số không đọc được (chỉ nhận `99k`, `1,9tr`, `40%`, `1.000`, `24/7`…); nhịp `ceil(d·2,4·0,9)…floor(d·2,4·1,1)` (60 s ⇒ 130–158); câu mở ≤ 8 từ có số/câu hỏi/mâu thuẫn; câu cuối ≤ 10 từ; trùng nguồn ≥ 9 từ liên tiếp (gộp thành 1 lỗi mỗi đoạn chép).
- **score_hook** (E-012): lời ≤ 14 từ, chữ ≤ 8 từ, cấm mở bằng lời chào/giới thiệu bản thân, phải có ≥ 1 dấu hiệu; `type` ∈ pov | truoc-sau | cau-hoi | canh-bao | nghich-ly | con-so.
- **check_claims** (E-013): câu có ngôi thứ nhất + con số + từ chỉ kết quả/tiền/khách phải khớp 1 claim có `claim_source`; trả thêm `claims[]` với `label: "ví dụ"` khi `claim_source = "vi-du"` để lát B in nhãn.
- **pick_keywords**: ưu tiên số/tiền/%/thời gian → cụm trong `keywords-vi.json` → danh từ riêng; 2 từ khoá cách nhau ≥ 4 từ (mọi cụm phụ đề ≤ 4 từ có tối đa 1 từ khoá); cụm nhiều từ trả mỗi từ 1 cặp cùng màu; không có nghĩa tiền/cảnh báo ⇒ xen xanh ↔ vàng.
- **profile_samples**: 1–5 mẫu; văn bản hoặc link http(s). Link: chặn đuôi media, phân giải DNS 1 lần và chặn mọi IP không `is_global` (nội bộ, loopback, link-local, metadata 169.254.169.254, 0.0.0.0, CGNAT…), nối thẳng IP đã kiểm (chống DNS rebinding), kiểm lại từng lần chuyển hướng (≤ 3), chỉ đọc `text/html|text/plain` ≤ 512 KB; đo trên `og:description`/`description` (hoặc `<p>`), từ/giây khi trang có `og:video:duration`/JSON-LD `duration`. Chỉ trả số đo + `suggested`, không trả chữ nguồn.

## Kiểm thử (kết quả thật, chạy trong `products/ags-video-editing`)
| Lệnh | Kết quả |
|---|---|
| `venv/bin/python -m unittest tests.ags_test_vi_script -v` | **9/9 OK** (0,15 s) |
| `/usr/bin/python3 tests/ags_test_vi_script.py` (Python 3.9.6) | 9/9 OK |
| `venv/bin/python tests/ags_test_core.py` | 9/9 |
| `venv/bin/python tests/ags_test_bds_engine.py` | 9/9 |
| `venv/bin/python -m unittest tests.ags_test_blender` | 6 chạy, OK (1 skipped — có sẵn, không do lát A) |
| `venv/bin/python -m unittest tests.ags_test_installer` | 4/4 OK (lát C đã thêm test thứ 4) |
| `venv/bin/python -m unittest tests.ags_test_shield` | **14/17 — 3 lỗi do lát B**: `scripts/ags_studio.py` import `ags_reels_pipeline`, `ags_director_engine` không có trong gói (đã báo SliceB). `ags_vi_script.py` không còn gây lỗi. |
| `services/ops/ags-reels-footage`: `python -m unittest test_ags_reels_pipeline` | 8/8 OK (207 s) |
| CLI tay: `profile --sample http://example.com` (mạng thật) | đọc được, 25 từ; `…/x.mp4` → `media`; `http://[::ffff:127.0.0.1]/` → `ssrf` |

Test phủ: AC-006 (129/130/158/159 từ), AC-005 (kịch bản dịch máy: câu 22 từ, calque, từ ngoại, nhịp, hook; chép nguồn 9 từ → E-004, 8 từ → đạt), AC-011 (lời 14/15, chữ 8/9, lời chào, thiếu dấu hiệu), AC-012 (thiếu nguồn, nguồn rỗng, khách nhập, ví dụ → nhãn), AC-013 (500 triệu xanh, 3 tháng vàng, mất khách đỏ; chế độ xen xanh/vàng), config 6 mẫu + 8 loại hook đạt luật, 7 link nội bộ/`file://` bị chặn, đo văn bản không trả chữ nguồn, CLI `--json` + mã thoát.

## Điểm lệch / mâu thuẫn spec (không sửa spec)
1. **AC-011** gọi "Chỉ 1 sai lầm này khiến dòng tiền cạn" là 8 từ; đếm theo tiếng là **9**. Đạt khi là lời nói (≤ 14), sẽ lỗi nếu dùng làm chữ trên màn hình (≤ 8).
2. **BR-002 vs BR-010**: BR-002 bắt câu mở của kịch bản ≤ 8 từ và chỉ nhận số/câu hỏi/mâu thuẫn; BR-010 cho lời nói ≤ 14 từ và 6 dấu hiệu. `validate` áp BR-002 cho câu 1, `score_hook` áp BR-010 ⇒ hook chỉ có cảnh báo/POV qua `hook` nhưng trượt `validate`.
3. **BR-010** "hook ≤ 5 s" mâu thuẫn với 14 từ ở 2,4 từ/giây (= 5,8 s). `ags_vi_script` không có âm thanh nên không đo giây; lát B/D đo trên mp4.
4. **BR-010** "mỗi series luân phiên ≥ 3 loại hook" không kiểm được qua chữ ký `score_hook(spoken, on_screen)`; đã ghi `hook_types` (≥ 3) mỗi mẫu + `rules.series_rotation_min_types` cho lát B (variants).
5. **NFR-002** ghi "dùng lại `_resolve_validated_public_ip`": script trong gói khách import `ags_reels_pipeline` bị `ags_build_skill_zips.validate` chặn (shield đỏ) và gói khách không mang pipeline ⇒ viết kiểm tra riêng tối giản (`_public_ip` + `_fetch_public_page`), cùng luật, chặt hơn (`is_global`) và thêm kiểm `Content-Type`.
6. **FR-020** nhắc trùng nguồn > 8 từ ở `profile`; theo giao việc `profile` chỉ trả số đo, nên kiểm trùng nguồn nằm ở `validate(source_text=…)`. Với nguồn là link, agent phải tự có chữ nguồn để truyền vào (chưa có hàm trả chữ trang).
7. Nhịp 2,4 từ/giây đếm theo tiếng. [INFERENCE] Giọng TTS tiếng Việt có thể đọc nhanh hơn thế; lát D nên so thời lượng mp4 thật với `duration_range` khi chạy `proof`.

## Chưa làm / blocker
- `CHANGELOG.md` dùng chung (đang có thay đổi của lát khác) — chưa thêm mục cho lát A; để coordinator gộp.
- Không có blocker; lát A không gọi dịch vụ cần khoá.

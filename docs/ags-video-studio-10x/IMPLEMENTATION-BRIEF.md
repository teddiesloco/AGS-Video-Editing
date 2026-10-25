# Implementation brief — AGS Video Studio 10x (cho `opus-coder`)

Spec khoá: `srs/spec.md` (FR-003..024, BR-001..012, NFR, E-001..014), `userstories/us-001.md` (AC-001..014), `api/api-map.md`, `research/viral-concepts.md`. BA audit 100/100 PASS; `builder-plan.json` đã sinh. `builder-plan.md` mặc định thiên về web (frontend/backend) — bề mặt thật ở đây là **skill + CLI + MCP trong ô chat của Claude Code/Codex/Antigravity/Cursor**; "màn hình" = lời thoại + ảnh lưới. KHÔNG dựng web server/UI mới. HTTP chỉ là dispatcher cục bộ sẵn có `127.0.0.1:8792` (`services/ops/ags-reels-footage/ags_reels_footage.py`), thêm route `/api/v1/studio/*` bằng cùng kiểu.

## Nền ĐÃ CÓ — dùng lại, không viết lại
- `services/ops/ags-reels-footage/ags_reels_pipeline.py::run_one_prompt_reels_pipeline` (TTS, karaoke ASS, B-roll AI `_render_ai_image_broll`, LUT, loudnorm, `assert_client_licensed`). Hiện truyền `keywords=()` vào phụ đề (dòng ~1158) → phải nối từ khoá tự động.
- `products/ags-video-editing/scripts/`: `ags_common.py` (`SAFE_ZONE_9X16` = trái .111/trên .15/phải .278/dưới .35 — **dùng lại, cấm số mới**), `ags_editorial_sub.py` (`--keywords`, `--highlight-color`, style karaoke), `ags_tts.py` (engine gemini; `normalize` số), `ags_sfx.py`, `ags_text_behind_person.py`/preset `highlight_hook`.
- `harness/ags_anti_slop_guard.py` (exit 0 = đạt), `scripts/ags_client_license.py::assert_client_licensed`, `scripts/ags_setup.py --install-all-clients`, `scripts/ags_build_protected_client.py`.
- Test hiện có phải còn PASS: installer 3/3, blender 6/6, shield 17/17, core 9/9, bds 9/9, reels 8/8.

## Hợp đồng giao diện giữa các lát (KHÓA — ba lát dựa vào đây)
`products/ags-video-editing/scripts/ags_vi_script.py` (stdlib, tất định, không mạng):
```python
validate_script(script: str, duration_sec: float, source_text: str | None = None) -> dict
  # {"ok": bool, "errors": [{"code": "E-ags-video-studio-10x-005|004", "sentence": int, "reason": str}],
  #  "stats": {"words": int, "target_range": [lo, hi], "avg_sentence_words": float, "max_sentence_words": int}}
score_hook(spoken: str, on_screen: str | None = None) -> dict
  # {"ok": bool, "type": str | None, "errors": [{"code": "E-ags-video-studio-10x-012", "reason": str}]}
check_claims(script: str, claims: list[dict]) -> dict   # BR-012; claims=[{"text","claim_source"}]; lỗi E-...-013
pick_keywords(words: list[str]) -> list[tuple[int, str]]   # (chỉ số từ, "#A8FF3E"|"#FFD166"|"#FF5A5F") theo BR-005
profile_samples(samples: list[str]) -> dict   # FR-020: chỉ số đo, không tải media
```
CLI: `ags_vi_script.py validate|hook|claims|profile ... --json`.
`products/ags-video-editing/scripts/ags_studio.py` — lệnh: `intake`, `quote`, `run`, `revise`, `variants`, `proof`, `menu`; mọi lệnh `--json`; trạng thái ở `studio-job.json` (khoá cấp 1 theo `api-map.md`); `run` bắt `--confirmed`; gọi `assert_client_licensed()`.
Config (JSON, người bán sửa được) ở `products/ags-video-editing/config/`: `menu.json`, `pricing.json`, `hooks-vi.json`, `formats-vi.json`, `keywords-vi.json`.

## Lát việc (song song được, file rời nhau)
- **A — Ngôn ngữ & hook** (`ags_vi_script.py`, `config/hooks-vi.json|formats-vi.json|keywords-vi.json`, `tests/ags_test_vi_script.py`): FR-008/018/020/021(beat-sheet), BR-001/002/003/005/010/012. Test: AC-005, AC-006 (129/130/158/159 từ), AC-011, AC-012, AC-013 (chọn màu), trùng nguồn > 8 từ.
- **B — Lõi Studio & pipeline** (`ags_studio.py`, `config/menu.json|pricing.json`, route `/api/v1/studio/*`, sửa `ags_reels_pipeline.py`, `ags_reels_footage.py`, `tests/ags_test_studio.py`): FR-004/005/009/010/011/013/014/015/016/019/022/023/024, BR-004/006/007/008/009/011. Gồm: intake 3 câu bỏ câu đã biết; quote + chặn khi chưa xác nhận (E-003); nối `pick_keywords`→phụ đề; hook chữ hiện ≤0,5 s + whoosh t=0; chuyển động xen kẽ ≤3 s; `contact-sheet.jpg` ≥12 khung; `revise` whitelist; `variants` 3 bản; Gemini style + model từ env, ghi model vào manifest; manifest không chứa khoá (AC-010). Giao diện tới lát A theo hợp đồng trên (nếu A chưa xong, import trễ, không copy logic).
- **C — Trải nghiệm không-kỹ-thuật** (`SKILL.md`, `README.md`, `HUONG-DAN-SU-DUNG.md`, `skills/ags-studio/SKILL.md`, `gemini-extension.json`/`AGENTS.md`/`GEMINI.md` nếu cần, `scripts/ags_setup.py` + `ags_build_skill_zips.py` để skill mới được nạp vào cả 4 client; `mcp/ags_mcp_server.py` thêm tool `ags_studio_*`): FR-003/017, NFR-004. Bảng chọn món ≥ 8 ngành đặt ĐẦU 3 file; kịch bản hỏi ngược đúng 3 câu + báo chi phí + chờ "chạy"; lời văn lời thường, không thuật ngữ; không hứa thu nhập/lượt xem.
- **D — Render bằng chứng thật** (sau A+B): `ags_studio.py proof` → thư mục `proof/` gồm ≥4 mp4 (thirty-years-60s Việt hoá, jetlag-vi, BĐS, editorial/isometric 3D) 1080×1920/30fps/−14 LUFS, mỗi mp4 có `contact-sheet.jpg`, `proof-manifest.json` (SHA-256, ffprobe, guard exit 0, model TTS đã dùng, `claim_source`). Kiểm từng khung t=0,3 s có chữ hook; kiểm chữ phụ đề trong `SAFE_ZONE_9X16`. Kịch bản Việt hoá do agent viết (OQ-002), phải qua `validate`.

## Luật cứng
1. Không `git commit`/push, không đụng `dist/`, `venv/`, `LICENSE*`. Không in/ghi khoá API (9router/Gemini) vào file, log, manifest, báo cáo. Nếu thiếu khoá để chạy ảnh AI/Gemini thật: dùng giọng/ảnh miễn phí cho phần tất định, ghi rõ trong báo cáo phần nào CHƯA chạy thật vì thiếu khoá — KHÔNG làm giả đầu ra.
2. Tối giản (AGENTS §5B): stdlib + ffmpeg + Pillow có sẵn; không abstraction/shim mới; không thêm phụ thuộc. Giữ test hiện có xanh.
3. Test theo skill `test-audit`: mỗi hợp đồng 1 test ở biên mạnh nhất, ưu tiên bảng dữ liệu; không test private/mocks tautology; không mạng trong test tất định.
4. Nội dung nguồn: không tải/dùng hình–tiếng gốc của Business Thinking/Jetlag/Dan Martell; chỉ chép ngữ pháp thể loại (OQ-003/004). Không ghi số "110k" vào tài liệu bán.
5. Ghi báo cáo đầy đủ vào `docs/ags-video-studio-10x/reports/<lát>.md`; trả lại ≤ 10 dòng + đường dẫn (giữ phiên coordinator gọn).

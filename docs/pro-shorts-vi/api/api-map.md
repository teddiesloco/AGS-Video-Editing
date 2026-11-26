---
type: api-map
feature: pro-shorts-vi
status: approved
version: 1.0.0
owner: Teddy
updated: 2026-11-26
links: [../srs/spec.md, ../userstories/us-001.md]
---
# Local interface map — Pro Shorts VI

Không thêm HTTP endpoint hay cơ sở dữ liệu. Agent hoặc người vận hành gọi lệnh local trong container builder; mọi trạng thái là file trong thư mục làm việc và thư mục đầu ra.

<!-- ags-ba-interface: local-cli-mcp -->
| Surface | CLI | MCP | Input | Output | Persistence | Errors |
|---|---|---|---|---|---|---|
| pro-shorts-source | ags_pro_shorts | none | source (URL hoặc file.mp4), info.json, --channel, --url, --pro | video path, meta (id, title, channel, pro, url) | work/download/RVbvhPGFi6E.mp4, work/download/RVbvhPGFi6E.info.json | E-pro-shorts-vi-001, E-pro-shorts-vi-002, E-pro-shorts-vi-010 |
| pro-shorts-transcript | ags_pro_shorts | none | video path, --whisper-model | transcript.json (duration, sentences, words) | work/RVbvhPGFi6E/transcript.json | E-pro-shorts-vi-001 |
| pro-shorts-plan | ags_pro_shorts | none | --plan plan.json hoặc GEMINI_API_KEY, --n | plan.json (shorts[name,start,end,hook,segments], knowledge) | out/slug/plan.json | E-pro-shorts-vi-003, E-pro-shorts-vi-004, E-pro-shorts-vi-005 |
| pro-shorts-render | ags_pro_shorts | none | plan.json, --voice, --voice-name, --ab-first, --align-model | short-NN.mp4, short-NN_sheet.jpg, short-NN.caption.txt | out/slug/short-01.mp4, out/slug/short-01_sheet.jpg, out/slug/short-01.caption.txt | E-pro-shorts-vi-006, E-pro-shorts-vi-007, E-pro-shorts-vi-008 |
| pro-shorts-check | ags_pro_shorts | none | short-NN.mp4 | report.json (ffprobe, lufs, true_peak, guard_exit) | out/slug/report.json | E-pro-shorts-vi-009, E-pro-shorts-vi-011 |
| pro-shorts-knowledge | ags_pro_shorts | none | plan.json knowledge, meta | knowledge.md | out/slug/knowledge.md | E-pro-shorts-vi-004 |
| pro-shorts-square | ags_pro_shorts | none | video path, --layout square-bilingual, --plan plan.json (shorts[name,start,end,title_lines,cues[t0,t1,vi,en]]) | reel-NN-slug.mp4 (1080x1080), reel-NN-slug_sheet.jpg, reel-NN-slug.caption.txt, report.json | out/slug/reel-01.mp4, out/slug/reel-01_sheet.jpg, out/slug/reel-01.caption.txt | E-pro-shorts-vi-012, E-pro-shorts-vi-013, E-pro-shorts-vi-009, E-pro-shorts-vi-011 |
| pro-shorts-voices | voices | none | --engine vieneu | danh sách [nhãn, tên giọng] | none (read-only) | E-pro-shorts-vi-008 |

Thư mục `out/slug` là `out/<pro>-<tiêu đề>-<mã video>` (vd `out/alex-hormozi-after-closing-4000-sales-RVbvhPGFi6E`); `work/RVbvhPGFi6E` theo mã video.

Engine `scripts/ags_pro_shorts.py` sở hữu các hàm `acquire`, `transcribe`, `validate_plan`, `plan_with_llm`, `render_short`, `check_output`, `knowledge_md`; lệnh CLI chỉ điều phối chúng. Lời trong transcript và plan là dữ liệu không tin cậy: không nội suy vào lệnh shell (mọi ffmpeg gọi bằng danh sách đối số), chỉ đưa vào file ASS/JSON. Khoá Gemini chỉ đi qua biến môi trường. Mã lỗi khớp SRS từ E-pro-shorts-vi-001 tới E-pro-shorts-vi-013.

Bảng trên là hợp đồng triển khai; bằng chứng chạy thật nằm ở `report.json` và báo cáo của lần chạy, không suy ra từ bảng này.

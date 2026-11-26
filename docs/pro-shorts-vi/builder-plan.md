# Builder plan — pro-shorts-vi

BA audit: PASS

## Phase 1 — Architecture & Plan Lock

Agents: planner, ags-advisor, advisor
Skills: ags-plan, ags-advise, ags-fable-thinking, ags-vibe, ags-context-engineering

- [ ] Lock scope from docs/pro-shorts-vi/srs/spec.md: 6 BR, 13 error codes
- [ ] Confirm 0 screen(s), 8 local CLI/MCP interface(s), 1 user story file(s) before coding

## Phase 2 — Frontend UX/UI

Agents: ui-ux-designer
Skills: ags-frontend-design, ags-ui-ux-pro-max, ags-ui-styling, ags-frontend-development, ags-page-builder, ags-remotion, ags-hyperframes, ags-preview


## Phase 3 — Backend API & DB

Agents: fullstack-developer
Skills: ags-backend-development, ags-databases, ags-better-auth, ags-devops, ags-deploy, ags-security

- [ ] Implement local CLI/MCP interface: Surface: pro-shorts-source; CLI: ags_pro_shorts; MCP: none; Input: source (URL hoặc file.mp4), info.json, --channel, --url, --pro; Output: video path, meta (id, title, channel, pro, url); Persistence: work/download/RVbvhPGFi6E.mp4, work/download/RVbvhPGFi6E.info.json; Errors: E-pro-shorts-vi-001, E-pro-shorts-vi-002, E-pro-shorts-vi-010
- [ ] Implement local CLI/MCP interface: Surface: pro-shorts-transcript; CLI: ags_pro_shorts; MCP: none; Input: video path, --whisper-model; Output: transcript.json (duration, sentences, words); Persistence: work/RVbvhPGFi6E/transcript.json; Errors: E-pro-shorts-vi-001
- [ ] Implement local CLI/MCP interface: Surface: pro-shorts-plan; CLI: ags_pro_shorts; MCP: none; Input: --plan plan.json hoặc GEMINI_API_KEY, --n; Output: plan.json (shorts[name,start,end,hook,segments], knowledge); Persistence: out/slug/plan.json; Errors: E-pro-shorts-vi-003, E-pro-shorts-vi-004, E-pro-shorts-vi-005
- [ ] Implement local CLI/MCP interface: Surface: pro-shorts-render; CLI: ags_pro_shorts; MCP: none; Input: plan.json, --voice, --voice-name, --ab-first, --align-model; Output: short-NN.mp4, short-NN_sheet.jpg, short-NN.caption.txt; Persistence: out/slug/short-01.mp4, out/slug/short-01_sheet.jpg, out/slug/short-01.caption.txt; Errors: E-pro-shorts-vi-006, E-pro-shorts-vi-007, E-pro-shorts-vi-008
- [ ] Implement local CLI/MCP interface: Surface: pro-shorts-check; CLI: ags_pro_shorts; MCP: none; Input: short-NN.mp4; Output: report.json (ffprobe, lufs, true_peak, guard_exit); Persistence: out/slug/report.json; Errors: E-pro-shorts-vi-009, E-pro-shorts-vi-011
- [ ] Implement local CLI/MCP interface: Surface: pro-shorts-knowledge; CLI: ags_pro_shorts; MCP: none; Input: plan.json knowledge, meta; Output: knowledge.md; Persistence: out/slug/knowledge.md; Errors: E-pro-shorts-vi-004
- [ ] Implement local CLI/MCP interface: Surface: pro-shorts-square; CLI: ags_pro_shorts; MCP: none; Input: video path, --layout square-bilingual, --plan plan.json (shorts[name,start,end,title_lines,cues[t0,t1,vi,en]]); Output: reel-NN-slug.mp4 (1080x1080), reel-NN-slug_sheet.jpg, reel-NN-slug.caption.txt, report.json; Persistence: out/slug/reel-01.mp4, out/slug/reel-01_sheet.jpg, out/slug/reel-01.caption.txt; Errors: E-pro-shorts-vi-012, E-pro-shorts-vi-013, E-pro-shorts-vi-009, E-pro-shorts-vi-011
- [ ] Implement local CLI/MCP interface: Surface: pro-shorts-voices; CLI: voices; MCP: none; Input: --engine vieneu; Output: danh sách [nhãn, tên giọng]; Persistence: none (read-only); Errors: E-pro-shorts-vi-008
- [ ] Enforce business rules: BR-pro-shorts-vi-001, BR-pro-shorts-vi-002, BR-pro-shorts-vi-003, BR-pro-shorts-vi-004, BR-pro-shorts-vi-005, BR-pro-shorts-vi-006
- [ ] Return error codes: E-pro-shorts-vi-001, E-pro-shorts-vi-002, E-pro-shorts-vi-003, E-pro-shorts-vi-004, E-pro-shorts-vi-005, E-pro-shorts-vi-006, E-pro-shorts-vi-007, E-pro-shorts-vi-008, E-pro-shorts-vi-009, E-pro-shorts-vi-010, E-pro-shorts-vi-011, E-pro-shorts-vi-012, E-pro-shorts-vi-013

## Phase 4 — BDD Verification & Review

Agents: tester, code-reviewer, code-simplifier
Skills: ags-test, ags-web-testing, ags-agent-browser, ags-code-review, ags-review-pr, ags-skill-creator, ags-ship

- [ ] Automate docs/pro-shorts-vi/userstories/us-001.md: 11 Given/When/Then scenario(s) via E2E
- [ ] Review diff against srs/spec.md, api-map.md and the prototype before merge

## Generated from

- docs/pro-shorts-vi/api/api-map.md
- docs/pro-shorts-vi/srs/spec.md
- docs/pro-shorts-vi/userstories/us-001.md

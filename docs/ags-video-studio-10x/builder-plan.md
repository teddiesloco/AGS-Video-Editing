# Builder plan — ags-video-studio-10x

BA audit: PASS

## Phase 1 — Architecture & Plan Lock

Agents: planner, ags-advisor
Skills: ags-plan, ags-advise

- [ ] Lock scope from docs/ags-video-studio-10x/srs/spec.md: 12 BR, 14 error codes
- [ ] Confirm 1 screen(s), 9 endpoint(s), 1 user story file(s) before coding

## Phase 2 — Frontend UX/UI

Agents: ui-ux-designer
Skills: ags-frontend-design, ags-ui-ux-pro-max, ags-ui-styling, ags-frontend-development, ags-react-best-practices

- [ ] Build screen main (docs/ags-video-studio-10x/ascii-screen/main.md) with Loading/Empty/Error/Populated states; data-testid: ags-vs-contact-sheet, ags-vs-menu, ags-vs-question, ags-vs-quote-run, ags-vs-result, ags-vs-revise, ags-vs-title, ags-vs-voice

## Phase 3 — Backend API & DB

Agents: fullstack-developer
Skills: ags-backend-development, ags-databases, ags-better-auth, ags-payment-integration, ags-security

- [ ] Implement endpoint: `AMP-ags-video-studio-10x-001` `FR-ags-video-studio-10x-004` `ags-vs-question` → `POST /api/v1/studio/intake` `{"answers":{"topic","preset","voice"}}` → `studio_job.answers` preset ∈ {business-thinking-60s, jetlag-vi, bds, editorial, isometric-3d}; `E-ags-video-studio-10x-002` `P0`
- [ ] Implement endpoint: `AMP-ags-video-studio-10x-002` `FR-ags-video-studio-10x-005` `ags-vs-quote-run` (xem chi phí) → `POST /api/v1/studio/quote` `{"job_id"}` → `studio_job.quote` Đọc `config/pricing.json` (BR-004) `P0`
- [ ] Implement endpoint: `AMP-ags-video-studio-10x-003` `FR-ags-video-studio-10x-005` `ags-vs-quote-run` (bấm Chạy) → `POST /api/v1/studio/run` `{"job_id","confirmed":true}` → `studio_job.status` `confirmed` bắt buộc; `E-ags-video-studio-10x-003` `P0`
- [ ] Implement endpoint: `AMP-ags-video-studio-10x-004` `FR-ags-video-studio-10x-008` (agent) → `POST /api/v1/studio/validate-script` `{"script","duration_sec","source_text?"}` → `studio_job.script_report` BR-001/002/003; `E-ags-video-studio-10x-004/005` `P0`
- [ ] Implement endpoint: `AMP-ags-video-studio-10x-005` `FR-ags-video-studio-10x-015` `ags-vs-revise` → `POST /api/v1/studio/revise` `{"job_id","say"}` → `studio_job.revisions[]` Whitelist BR-007; `E-ags-video-studio-10x-010` `P1`
- [ ] Implement endpoint: `AMP-ags-video-studio-10x-006` `FR-ags-video-studio-10x-004` `studio_job.next_question` → `GET /api/v1/studio/jobs/{id}` `.next_question` → `ags-vs-question` Rỗng khi đủ 3 câu `P0`
- [ ] Implement endpoint: `AMP-ags-video-studio-10x-014` `FR-ags-video-studio-10x-018` `ags-vs-question` (hook) → `POST /api/v1/studio/hook` `{"script","type?"}` → `studio_job.hook_report` BR-010; `E-ags-video-studio-10x-012` `P0`
- [ ] Implement endpoint: `AMP-ags-video-studio-10x-015` `FR-ags-video-studio-10x-020` (khách dán mẫu) → `POST /api/v1/studio/profile` `{"samples":[url text]}` → `studio_job.profile` SSRF-safe; chỉ đo số liệu, không tải hình/tiếng; `E-ags-video-studio-10x-004` `P1`
- [ ] Implement endpoint: `AMP-ags-video-studio-10x-016` `FR-ags-video-studio-10x-023` `ags-vs-revise` ("làm 3 bản thử") → `POST /api/v1/studio/variants` `{"job_id","count":3}` → `studio_job.variants[]` Báo chi phí thêm trước; `E-ags-video-studio-10x-003` `P1`
- [ ] Enforce business rules: BR-ags-video-studio-10x-001, BR-ags-video-studio-10x-002, BR-ags-video-studio-10x-003, BR-ags-video-studio-10x-004, BR-ags-video-studio-10x-005, BR-ags-video-studio-10x-006, BR-ags-video-studio-10x-007, BR-ags-video-studio-10x-008, BR-ags-video-studio-10x-009, BR-ags-video-studio-10x-010, BR-ags-video-studio-10x-011, BR-ags-video-studio-10x-012
- [ ] Return error codes: E-ags-video-studio-10x-001, E-ags-video-studio-10x-002, E-ags-video-studio-10x-003, E-ags-video-studio-10x-004, E-ags-video-studio-10x-005, E-ags-video-studio-10x-006, E-ags-video-studio-10x-007, E-ags-video-studio-10x-008, E-ags-video-studio-10x-009, E-ags-video-studio-10x-010, E-ags-video-studio-10x-011, E-ags-video-studio-10x-012, E-ags-video-studio-10x-013, E-ags-video-studio-10x-014

## Phase 4 — BDD Verification & Review

Agents: tester, code-reviewer, code-simplifier
Skills: ags-test, ags-web-testing, ags-code-review, ags-ship

- [ ] Automate docs/ags-video-studio-10x/userstories/us-001.md: 6 Given/When/Then scenario(s) via E2E
- [ ] Review diff against srs/spec.md, api-map.md and the prototype before merge

## Generated from

- docs/ags-video-studio-10x/api/api-map.md
- docs/ags-video-studio-10x/ascii-screen/_index.md
- docs/ags-video-studio-10x/ascii-screen/main.md
- docs/ags-video-studio-10x/html-design/prototype.html
- docs/ags-video-studio-10x/research/viral-concepts.md
- docs/ags-video-studio-10x/srs/spec.md
- docs/ags-video-studio-10x/srs/user-flow.md
- docs/ags-video-studio-10x/userstories/us-001.md

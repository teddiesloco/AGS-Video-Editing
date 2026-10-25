# Builder plan — ags-marketing-editor

BA audit: PASS

## Phase 1 — Architecture & Plan Lock

Agents: planner, ags-advisor
Skills: ags-plan, ags-advise

- [ ] Lock scope from docs/ags-marketing-editor/srs/spec.md: 6 BR, 6 error codes
- [ ] Confirm 1 screen(s), 5 local CLI/MCP interface(s), 1 user story file(s) before coding

## Phase 2 — Frontend UX/UI

Agents: ui-ux-designer
Skills: ags-frontend-design, ags-ui-ux-pro-max, ags-ui-styling, ags-frontend-development, ags-react-best-practices

- [ ] Build screen main (docs/ags-marketing-editor/ascii-screen/main.md) with Loading/Empty/Error/Populated states; data-testid: marketing-approval, marketing-draft, marketing-goal, marketing-plan, marketing-status

## Phase 3 — Backend API & DB

Agents: fullstack-developer
Skills: ags-backend-development, ags-databases, ags-better-auth, ags-payment-integration, ags-security

- [ ] Implement local CLI/MCP interface: Surface: marketing-goal; CLI: inspect; MCP: marketing_editor_inspect; Input: source, transcript_path, model; Output: transcript.json; Persistence: transcript.json; Errors: E-ags-marketing-editor-001
- [ ] Implement local CLI/MCP interface: Surface: marketing-plan; CLI: validate; MCP: marketing_editor_validate; Input: plan_path; Output: plan_hash, duration, words, role_durations; Persistence: none (read-only); Errors: E-ags-marketing-editor-001
- [ ] Implement local CLI/MCP interface: Surface: marketing-approval; CLI: approve; MCP: marketing_editor_approve; Input: plan_path, stage, reason; Output: approval.json; Persistence: approval.json; Errors: E-ags-marketing-editor-002
- [ ] Implement local CLI/MCP interface: Surface: marketing-draft; CLI: render; MCP: marketing_editor_render; Input: plan_path, output_dir, stage; Output: video.mp4, subtitles.srt, report.json; Persistence: report.json; Errors: E-ags-marketing-editor-004
- [ ] Implement local CLI/MCP interface: Surface: marketing-status; CLI: validate; MCP: marketing_editor_validate; Input: plan_path; Output: status, error, artifact_paths; Persistence: none (read-only); Errors: E-ags-marketing-editor-001
- [ ] Enforce business rules: BR-ags-marketing-editor-001, BR-ags-marketing-editor-002, BR-ags-marketing-editor-003, BR-ags-marketing-editor-004, BR-ags-marketing-editor-005, BR-ags-marketing-editor-006
- [ ] Return error codes: E-ags-marketing-editor-001, E-ags-marketing-editor-002, E-ags-marketing-editor-003, E-ags-marketing-editor-004, E-ags-marketing-editor-005, E-ags-marketing-editor-006

## Phase 4 — BDD Verification & Review

Agents: tester, code-reviewer, code-simplifier
Skills: ags-test, ags-web-testing, ags-code-review, ags-ship

- [ ] Automate docs/ags-marketing-editor/userstories/us-001.md: 11 Given/When/Then scenario(s) via E2E
- [ ] Review diff against srs/spec.md, api-map.md and the prototype before merge

## Generated from

- docs/ags-marketing-editor/api/api-map.md
- docs/ags-marketing-editor/ascii-screen/_index.md
- docs/ags-marketing-editor/ascii-screen/main.md
- docs/ags-marketing-editor/diagrams/data-model.md
- docs/ags-marketing-editor/diagrams/sequence-flows.md
- docs/ags-marketing-editor/diagrams/state-machine.md
- docs/ags-marketing-editor/html-design/prototype.html
- docs/ags-marketing-editor/implementation-plan.md
- docs/ags-marketing-editor/srs/spec.md
- docs/ags-marketing-editor/srs/user-flow.md
- docs/ags-marketing-editor/userstories/us-001.md

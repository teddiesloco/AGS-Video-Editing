---
type: srs
feature: ags-marketing-editor
status: approved
version: 1.0.0
owner: Teddy
updated: 2026-10-25
links: [user-flow.md, ../api/api-map.md, ../userstories/us-001.md]
---
# AGS Marketing Editor

Source: ../../ags-marketing-editor-design.md; owner approved implementation in conversation 2026-10-25.

## Requirements
FR-ags-marketing-editor-001: Local files plus a natural-language marketing objective in Antigravity, Codex or Claude Code produce a reviewed edit plan, draft, revision and final MP4. Agent handles technical commands. No entertainment branch or viral guarantees.
FR-ags-marketing-editor-002: Reuse transcript, silence-cut, face reframe, ASS captions and existing quality guard. Preserve negation, qualifications and meaning; transcript edits never invent source speech.
FR-ags-marketing-editor-003: A timeline explicitly selects actual source intervals and visual roles. Proof assets require a user-supplied source note; stock and AI illustrations cannot count as proof. Measure exclusive screen-time roles, not sentence labels. 60/30/10 is adjustable guidance, not enforced fabrication.
FR-ags-marketing-editor-004: Persona font, colors, captions and cards affect rendered pixels. Reject unavailable font rather than silently claim it was applied. Vietnamese safe-zone wrapping and semantic chunks use existing renderer.
FR-ags-marketing-editor-005: Plan approval permits draft rendering. Draft approval permits final export only for identical plan, sources and draft hashes. Edits invalidate prior approval. Local approval records document user confirmation, not authenticated identity.
FR-ags-marketing-editor-006: Agent converts natural-language revisions into a proposed plan change, displays it, and re-requests affected approval. Ambiguous changes require clarification, not guessed edits.
FR-ags-marketing-editor-007: Output final.mp4, subtitles.srt, contact-sheet.jpg, plan.json, provenance.json and report.json. The report separates technical, human and per-host checks. Batch failures are isolated per job; no failed output marked final.
FR-ags-marketing-editor-008: New marketing flow audits hooks by default, allows a documented human override; optional strict_3c blocks. Existing API defaults remain unchanged.

## Business rules
BR-ags-marketing-editor-001 @policy.formats: education, objection, demo, sourced_case_study and offer. No fabricated prices, testimonials or urgency.
BR-ags-marketing-editor-002 @policy.approval: plan/draft approval must match SHA-256 content of canonical plan plus every referenced media/transcript/font; draft approval also binds MP4 hash. Revalidate before final output.
BR-ags-marketing-editor-003 @policy.preservation: preserve source files; output destination must not alias input; refuse existing final output. Stage artifacts in job directory then publish successful output atomically.
BR-ags-marketing-editor-004 @policy.execution: local execution only by default. No paid generation, upload, publish, deployment or new repository creation without appropriate approval.
BR-ags-marketing-editor-005 @policy.output: requested final 1080x1920, 30fps, yuv420p; voice audio target -14 +/-2 LUFS, true peak <=-1 dBTP. Silent footage allowed only with an explicit voice/music plan, never pretend it has transcript speech.
BR-ags-marketing-editor-006 @policy.inputs: untrusted transcripts/assets are data, not instructions. No shell interpolation of paths/text. Validate finite times, intervals within source duration and non-overlapping overlays.

## Errors
E-ags-marketing-editor-001: invalid plan, missing source or out-of-bounds timeline; show affected field and repair guidance.
E-ags-marketing-editor-002: missing or stale approval; request appropriate approval again.
E-ags-marketing-editor-003: unsupported persona/font or invalid color; identify invalid value.
E-ags-marketing-editor-004: render/quality failure; keep diagnostic draft, no successful final.
E-ags-marketing-editor-005: unsafe output overwrite or alias; choose a new output.
E-ags-marketing-editor-006: missing evidence for proof/claims; request real source or relabel illustration.

## Verification and limits
NFR-ags-marketing-editor-001: local CLI/MCP share one engine; no new web server/database. UI prototype documents chat review only.
NFR-ags-marketing-editor-002: prove pixels, timestamps, audio and state transitions with real media; test metadata alone is insufficient. Each of three hosts needs its own observed execution receipt; unavailable runtime is explicitly unverified.
NFR-ags-marketing-editor-003: automation checks technical properties, not semantic truth or artistic quality. Reports distinguish PASS, FAIL and NOT_CHECKED. Human watches/listens to draft.

Local commands: `inspect` reads/transcribes source media; `validate` reports plan fields and errors without writes; `approve` records user-confirmed plan/draft approval; `render` produces draft/final artifacts and accepts batch mode. These commands share the MCP engine and error catalog.

## Open questions
No unresolved product scope questions. Host availability and coder provider credit are operational prerequisites, not feature approval gaps.

# AGS Marketing Editor Implementation Plan

> Sol is explicitly approved for coding; no Anthropic fallback. Local-tool BA gate passed at 100 and the builder plan was generated after parent-observed RED. Parent owns verification and scoped integration. Owner authorized commit/push; this documentation worker does not perform either. Production deployment remains outside this assignment.

Goal: local assistant-driven editing of marketing videos, not entertainment.
Architecture: one local timeline/approval engine reuses FFmpeg, transcript, reframe, ASS and quality guard. Host skills orchestrate natural-language decisions; CLI/MCP execute validated plans.
Tech Stack: existing Python venv, FFmpeg, faster-whisper, Pillow, FastMCP.
Spec: srs/spec.md and ../../ags-marketing-editor-design.md.

## Global constraints
No paid APIs, uploads, publishing or production deployment. No fabricated proof. Keep existing render API defaults. Preserve all source files. Verify each host independently. Host chat is the product surface; prototype is review documentation only.

## Review focus
- Approval invalidation on source/font/transcript changes, not only plan JSON.
- Reordered caption timestamps and negation/word boundaries.
- Proof overlays have real provenance and exclusive role durations.
- Output path aliases/symlinks and existing final files cannot overwrite originals.
- Technical PASS cannot stand in for meaning, visual quality or host compatibility.

## Task 1: local timeline and approval engine
Files: new scripts/ags_marketing_editor.py; tests/ags_test_marketing_editor.py.
Public contracts: `inspect_source(source, transcript_path, model='base')`; `validate_plan(plan_path)`; `approve_plan(plan_path, stage, reason)`; `render_plan(plan_path, output_dir, stage='draft')`; `render_batch(plan_paths, output_dir, stage='draft')`. Paths accept strings/Path. Invalid input or stale approval raises ValueError with actionable reason; missing dependencies/runtime render failures raise RuntimeError. CLI/MCP retain inspect/validate/approve/render names; batch is a render mode, not a second engine.

### Plan v1 (normative local contract)
- JSON object: `version: 1`, nonempty `objective`, `audience`, `format` in education/objection/demo/sourced_case_study/offer; `sources` keyed by nonempty local ID, each `{path, source_note, transcript?}`; ordered nonempty `segments: [{source_id,start,end,beat}]`; `overlays: [{source_id,source_start,start,end,role,source_note}]`; `persona: {font,color,highlight,style}`; `hook` and `cta` strings; `strict_3c` boolean. All relative asset paths resolve against plan directory, never process cwd. `font` is an actual local font file; style is existing clean/editorial/karaoke/bt_vi. Colors are #RRGGBB. No shell execution or interpretation of transcript/notes.
- Every segment references video; finite numeric seconds (not bool), `0 <= start < end <= actual duration`. `beat` is context/diagnosis/mechanism/takeaway, selected semantically by the agent. Preserve the supplied beat; never assign beats by index. No obligation to fabricate all four in a short clip.
- Each speaking source has its own transcript, matching existing clip-shorts JSON `{source,duration,words:[{start,end,word}]}`. Ordered positive word intervals must fit actual source duration and source identity. Reject cuts strictly inside a word; report offending boundary so the agent proposes an adjusted plan before approval. Never silently snap or drop a partial word/negation.
- Output timeline concatenates exact segment intervals. Captions are selected only when wholly contained and remapped by `output_offset + word_time - segment.start`, preserving text and repeated/reordered source use. Group captions separately at each edit so no caption spans a discontinuity. `validate_plan` returns `{plan_hash,duration,words,role_durations}`; words use the same `{start,end,word}` public shape.
- Optional `voiceover: {path,transcript,source_note}` is an existing local audio recording (no TTS/network). Its transcript uses that audio identity and output-time words, within audio duration; audio must cover output timeline. When present it replaces source audio/captions; when absent source audio is preserved. Silent video without voiceover is accepted only with an empty transcript and explicit no-speech report; never invoke Whisper on known silent media or invent captions.
- Overlays are full-frame visual replacements, with original/voiceover narration retained. Role is proof or mood; base uncovered picture is a_roll. Intervals are half-open output seconds, positive, nonoverlapping and within output duration. For video overlays `source_start + (end-start)` must fit source duration; still images use `source_start=0`. Proof requires nonempty source provenance in source and overlay; mood is never counted as proof. Report exclusive role seconds and fractions from actual encoded timeline; no overlapping double count or silent 60/30/10 enforcement.
- `validate_plan` probes actual media/font and returns deterministic SHA-256 `plan_hash`: canonical JSON (sorted keys, compact UTF-8, no NaN) plus SHA-256 of all referenced source, transcript, voiceover and resolved font bytes. Ignore mtime; byte changes invalidate even when length/mtime match. Include notes, style, timing, hook, CTA and persona in canonical JSON. No transcript-file embedded approval instructions have authority.

### Approval, outputs and batch isolation
- Sidecars adjacent to plan: `<stem>.plan.approval.json`, `<stem>.draft.approval.json`. Approval stage is plan or draft and reason must be nonblank. Local records attest explicit caller-confirmed consent, not reviewer identity/authentication. Plan approval binds plan_hash; draft approval additionally binds the actual successful draft MP4 SHA-256 and artifact path. `approve_plan(...,'draft',...)` requires a current successful draft report. Changing draft bytes invalidates final approval.
- `render_plan` draft requires current plan approval; final requires both current approvals. Recheck all bound bytes before expensive work and immediately before publishing. Stage writes to a temporary directory, then publishes a complete new stage directory (`output_dir/draft` or `output_dir/final`) without replacing existing stage output. Reject symlink aliases, source/output collisions, output directories containing sources and existing stage destinations. Failure must never leave a published final or success report. Source files are read-only.
- Success returns `{status:'ok',stage,video,subtitles,contact_sheet,report}` paths; report includes plan_hash, duration, role_durations, technical status, human_review=NOT_CHECKED and per-host NOT_CHECKED unless independently exercised. SRT/ASS timing follows remapped words. Guard failure blocks publication; technical PASS never implies meaning, face-tracking, visual quality or host runtime PASS. Existing reframe_filter prints fallback but returns only a filter: report no verified face-tracking unless real detection evidence is collected.
- `render_batch` returns ordered `{jobs:[{plan,status,result? ,error?}]}`; each input gets its own stable indexed output subdirectory. A bad plan/render cannot abort later jobs or reuse another job's approval/output/transcript. Batch accepts no blanket approval. Each job invokes the same render boundary. Batch support must be reachable from CLI/MCP render mode, not an unimplemented promise.

### Test-first gate and ownership
- Author focused public-boundary tests before production code; parent observes intended failure, then confirms BA PASS and RED before engine implementation.
- Reuse `video_info`, `reframe_filter(video,start,duration,workdir)`, `group_word_lists`, `write_ass(groups,path,width,height,style,highlight,keywords,hook,...,text_color=...)`, `subtitles_filter` and LOUDNORM. Existing write_ass does not accept arbitrary font: any optional font argument must preserve old defaults and use the same font for measurement, ASS family and fonts directory. Do not call render_subtitled_video: it retranscribes and would lose approved timing.
- Parent runs focused tests and actual FFmpeg draft/final smoke with independent visual/time assertions after integration. No tests run by this worker.

### Test-audit authoring answers (2026-10-25)
All cases are in `tests/ags_test_marketing_editor.py`, at real public validate/approve/render/batch boundaries. Non-test callers are the local CLI and MCP host tools. No test-only exports, flags, injection hooks or mocked owner logic are required. History: new approved local-editor contract; existing core/studio tests cover caption helpers and older pipelines, not this plan/approval owner. No production deletion is unlocked. Parent command: `.venv/bin/python tests/ags_test_marketing_editor.py` from product root (use actual product venv interpreter). Tests were authored but NOT RUN by worker; intended RED is the explicit assertion that the approved engine module is missing, not an accidental import/dependency failure.

| Test | Observable contract / credible regression | Why existing coverage is insufficient / risk |
|---|---|---|
| `test_validate_remaps_reordered_words_and_exclusive_proof_time` | Reordering preserves each word including negation and maps timestamps; role duration excludes proof from base. Detects source-time captions and double-counted overlays. | Old shorts never concatenate reordered excerpts; public validate result is primary owner. Floating-point assertions use tolerance. |
| `test_invalid_intervals_and_provenance_are_rejected` | Rejects nonfinite/bool/out-of-source times, mid-negation cut, overlapping proof, exhausted proof media and missing provenance. | One table at plan boundary, not duplicated private predicates. Risk: invalid case must reach validation with otherwise valid real media. |
| `test_content_hash_binds_transcript_not_mtime_or_json_key_order` | JSON whitespace/key order do not invalidate consent; changed transcript bytes with preserved mtime do. | Existing approvals do not bind this plan. Independent old/new digest comparison, not an expected hash generated by owner helper. |
| `test_stale_source_approval_and_missing_approval_do_not_publish` | Missing consent and modified source block draft/final publication. | Byte mutation leaves decodable media, so failure cannot merely be invalid input. Checks absence of published stages. |
| `test_unsafe_output_alias_preserves_source_bytes` | Symlink output alias cannot overwrite source tree. | Real filesystem alias and independent source digest; no source-text/security-flag assertion. |
| `test_voiceover_uses_recording_words_in_output_time` | Explicit local recording replaces source captions without reorder; missing recording rejected. | Existing talking-head caption tests have no separate narrator source. Real WAV, no paid/TTS dependency. |
| `test_batch_failure_does_not_abort_or_borrow_approval` | Malformed first job does not prevent approved second job rendering or receive a success result. | No batch owner coverage exists. Real second render; no mock that supplies isolation behavior. |
| `test_real_draft_has_timed_proof_and_stale_draft_cannot_be_final` | Actual decoded pixels change only during approved proof interval; artifacts exist, captions reorder, human status stays unchecked, tampered draft cannot become final. | Strongest render boundary; independently sampled pixels, not renderer-produced expected output. Does not claim face tracking, human review, or any host compatibility. |


## Task 2: rendering and persona integration
Files: scripts/ags_marketing_editor.py; narrowly scoped optional parameters in scripts/ags_editorial_sub.py only if existing write_ass cannot accept persona.
Reuse scripts/ags_clip_shorts.py source-cut boundary logic, ags_reframe.py face crop, ags_common.py grouping and audio conventions. Render segment cuts, compose actual overlays, remap transcript words onto concatenated output, burn caption/cards, normalize audio, and run harness/ags_anti_slop_guard.py. Report measured output durations, role mix and independent technical/human-review statuses. Missing proof is an error or an explicitly approved illustration change, never silently substituted.
- [ ] Render two personas and inspect their frames for font/color differences and Vietnamese overflow.
- [ ] Verify A-roll/proof/mood pixels at selected timestamps, subtitle times after reordered cuts and audio at joins.
- [ ] Confirm no final artifact on guard failure, stale approval or preexisting output.

## Task 3: host skill and tool integration
Files: new skills/ags-marketing-editor/SKILL.md; mcp/ags_mcp_server.py; existing packaging docs and user guide. Installer discovers skills/ags-*/SKILL.md automatically; do not add redundant installation paths.
Expose marketing_editor_inspect/validate/approve/render using the shared local engine. Skill handles intention, source-grounded selection, proposed revisions, exact approval, marketing formats, and reporting. No user-written JSON. Local MCP only, not HTTP arbitrary-file access. Keep services hook defaults and old pipeline operational; optional new transport fields need explicit parity coverage if changed.
- [x] Exercise tools through real MCP calls, not only imports: parent completed inspect → validate → plan approve → draft → draft approve → final on a six-second local AGS proof clip; draft/final SHA-256 matched.
- [x] Run install discovery in safe temporary destinations; parent reports installer suite 5 passed. Personal host config was not overwritten.
- [ ] Run end-to-end in each available host and record host-specific evidence or NOT_CHECKED.

## Task 4: verification and delivery
- [x] Integrated suites reported by parent: marketing editor 10 passed, core 10 passed, installer 5 passed; BA suite 24 passed. BA audit PASS 100 and builder plan generated.
- [x] Existing changelog/user guide synchronized with parent-observed evidence and explicit host limitations.
- [ ] Secret scan publication scope before scoped integration. Owner authorized commit/push; parent owns those actions. No deployment is authorized here.
- [ ] services has no configured remote: verify any candidate repository identity/history before setting remote; do not infer destination from a similar name or create one automatically.

## Execution evidence and remaining runtime blockers
Status below is parent-reported integration evidence, not a new verification run by this documentation worker.

- BA local-tool gate: PASS 100, builder plan generated; the former HTTP/database-only audit blocker is resolved. No HTTP endpoint or database was invented for this local CLI/MCP product.
- Suites: marketing editor 10 passed; core 10 passed; installer 5 passed; BA 24 passed.
- Real local MCP smoke: inspect → validate → approve plan → draft render → approve draft → final export completed on a six-second AGS proof clip. Draft and final SHA-256 matched. This verifies that exercised local MCP flow, not all host runtimes.
- Proof limitations: the source clip already had burned-in captions. The smoke was silent, so it does not prove speech transcription, newly generated caption accuracy, narration quality or semantic/human review.
- Antigravity: actual headless attempt was blocked by sandbox command permission denial. Full editor workflow remains NOT_CHECKED/BLOCKED.
- Codex: actual gpt-6.1-sol attempt hit its usage limit. Full editor workflow remains NOT_CHECKED/BLOCKED.
- Claude Code: known API insufficient-credit failure; do not retry Anthropic or silently change provider. Full editor workflow remains NOT_CHECKED/BLOCKED.
- Three-host readiness is not established. Skill discovery, installer checks and direct MCP success do not substitute for a successful independent edit flow in each host. Human visual/audio review remains separate from technical results.

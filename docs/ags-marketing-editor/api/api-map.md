# Local interface map
No HTTP endpoints or database are added. Agent converts natural language to local commands, displays proposed edits, and invokes approved actions.

<!-- ags-ba-interface: local-cli-mcp -->
| Surface | CLI | MCP | Input | Output | Persistence | Errors |
|---|---|---|---|---|---|---|
| marketing-goal | inspect | marketing_editor_inspect | source, transcript_path, model | transcript.json | transcript.json | E-ags-marketing-editor-001 |
| marketing-plan | validate | marketing_editor_validate | plan_path | plan_hash, duration, words, role_durations | none (read-only) | E-ags-marketing-editor-001 |
| marketing-approval | approve | marketing_editor_approve | plan_path, stage, reason | approval.json | approval.json | E-ags-marketing-editor-002 |
| marketing-draft | render | marketing_editor_render | plan_path, output_dir, stage | video.mp4, subtitles.srt, report.json | report.json | E-ags-marketing-editor-004 |
| marketing-status | validate | marketing_editor_validate | plan_path | status, error, artifact_paths | none (read-only) | E-ags-marketing-editor-001 |

Engine scripts/ags_marketing_editor.py owns public functions inspect_source, validate_plan, approve_plan, render_plan; same contracts used by CLI/MCP. Objective and audience belong in the plan, not fabricated inspection results. Approve only follows actual user confirmation, not agent inference. Errors map directly to SRS E-ags-marketing-editor-001 through E-ags-marketing-editor-006. Existing HTTP render keeps its no-local-file policy; do not expose these local tools through HTTP.

Batch orchestration calls render_batch(plan_paths, output_dir, stage='draft') with independent per-job results. This is not an HTTP route or an additional persistence layer.

These are intended implementation contracts, not evidence that tools are installed or exercised. No database exists: persistence names real local artifacts. The local mapping variant is validated by the shared BA/builder parser; it does not bypass other BA checks.

Inspection transcription uses the existing source/duration/words JSON shape, with each word containing start, end and word. A source entry may reference its own transcript path. Local asset and transcript text is untrusted data; paths must never be interpolated into shell commands. Reporting a successful response alone is not artifact verification.

# Local marketing editor sequence

This is the intended BA contract, not a runtime receipt. References: ../srs/spec.md, ../api/api-map.md and ../userstories/us-001.md.

```mermaid
sequenceDiagram
  actor Owner
  participant Host as Antigravity / Codex / Claude Code
  participant Engine as Shared local engine
  participant Files as Local workspace
  Owner->>Host: Source, audience and marketing goal
  Host->>Engine: inspect_source(source, transcript_path, model)
  Engine->>Files: Read media; reuse/provide timed transcript
  Engine-->>Host: Source facts and transcript
  Host->>Files: Write proposed plan with sourced cuts, proof and CTA
  Host->>Engine: validate_plan(plan_path)
  Engine-->>Host: Hash, duration, words and exclusive role durations
  Host-->>Owner: Review proposed plan and limitations
  Owner->>Host: Explicitly approve identified plan
  Host->>Engine: approve_plan(plan_path, plan, reason)
  Engine->>Files: Persist plan approval bound to referenced bytes
  Host->>Engine: render_plan(plan_path, output_dir, draft)
  Engine->>Files: Validate approval, render draft and quality artifacts
  Engine-->>Host: Draft paths and technical findings
  Host-->>Owner: Video/contact sheet; request watch/listen review
  alt Revision requested
    Owner->>Host: Natural-language revision
    Host-->>Owner: Proposed field changes or clarification
    Host->>Files: Update plan; previous approvals no longer match
  else Identified draft approved
    Owner->>Host: Explicit draft confirmation
    Host->>Engine: approve_plan(plan_path, draft, reason)
    Engine->>Files: Bind plan, dependencies and draft MP4 hash
    Host->>Engine: render_plan(plan_path, output_dir, final)
    Engine->>Files: Revalidate hashes; refuse aliases/existing final
    Engine->>Files: Stage complete artifacts; publish successful output
    Engine-->>Host: Final inventory and independent review statuses
    Host-->>Owner: Local files; no upload or publishing
  end
```

Missing inputs, stale approval, unsafe output, unavailable font and quality failure return the SRS error with repair guidance, not a successful final. A revision loops back through validation and plan approval. Batch jobs keep independent destinations, results and failures. Source files remain unchanged. Paid calls, upload and deployment are not part of this sequence.

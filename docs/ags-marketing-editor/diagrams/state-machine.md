# Review lifecycle

These are conceptual workflow states computed from artifacts and valid hashes, not a database enum or an assertion of implemented runtime behavior. Loading/Empty/Error/Populated are presentation states and do not authorize rendering.

```mermaid
stateDiagram-v2
  [*] --> awaiting_source
  awaiting_source --> proposed: inspect and select source-grounded edits
  proposed --> plan_approved: explicit owner confirmation and current dependency hash
  plan_approved --> draft_ready: render and inspect draft
  draft_ready --> draft_approved: owner watches/listens and approves identified draft
  draft_approved --> final_ready: current hashes and successful guarded export
  final_ready --> [*]
  proposed --> proposed: clarify ambiguous revision
  plan_approved --> proposed: plan or referenced bytes changed
  draft_ready --> proposed: revise plan or dependencies
  draft_approved --> proposed: plan or referenced bytes changed
  draft_approved --> draft_ready: draft bytes changed
  plan_approved --> error: render fails
  draft_approved --> error: unsafe output or quality failure
  error --> proposed: repair requires changed plan or source
  error --> plan_approved: retry draft with still-valid approval
  error --> draft_approved: retry final with still-valid approval
```

Every transition that consumes approval rechecks bytes, including resolved font, media, transcript and any referenced voiceover. Recheck immediately before final publication to prevent changes during work from producing an incorrectly approved final. Old sidecars can remain for diagnostics but never authorize a changed revision. A stored boolean is neither identity authentication nor evidence of owner confirmation.

Errors preserve diagnostics and sources, not a falsely successful final. Returning from error requires the relevant approval still to match; the diagram is not permission to skip validation. Technical PASS, human review and host execution status are reported separately. A present host installation never implies that its acceptance flow was exercised.

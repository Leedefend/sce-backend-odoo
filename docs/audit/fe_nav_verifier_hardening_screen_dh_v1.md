# FE Nav Verifier Hardening Screen DH

```json
{
  "next_candidate_family": "verifier_skip_audit_observability_hardening",
  "family_scope": [
    "scripts/verify/unified_system_menu_click_usability_smoke.mjs",
    "artifacts/codex/unified-system-menu-click-usability-smoke/20260420T125254Z/summary.json",
    "artifacts/codex/unified-system-menu-click-usability-smoke/20260420T125254Z/cases.json"
  ],
  "reason": "The verifier now matches product navigation semantics and passes cleanly, but the artifact surface still collapses discovery and execution counts into a single `leaf_count`. The script filters explained-nav leaves by visibility, clickability, and resolved route, yet the summary does not expose how many raw leaves were discovered, how many were skipped, or which skip reasons dominated. That leaves an auditability gap: a future PASS could silently shrink scope without visible evidence. The strongest next low-risk family is verifier_skip_audit_observability_hardening, limited to exposing discovered-versus-executed leaf counts and bounded skip-reason breakdown in the smoke artifact."
}
```

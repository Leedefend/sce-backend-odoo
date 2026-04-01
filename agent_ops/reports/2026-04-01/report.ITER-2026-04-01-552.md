# ITER-2026-04-01-552

- status: PASS
- mode: scan
- layer_target: Frontend Layer
- module: native metadata list toolbar scan
- risk: low

## Candidate JSON

```json
[
  {
    "path": "frontend/apps/web/src/components/page/PageToolbar.vue",
    "module": "active-condition reset affordance",
    "feature": "reset-all wording clarity",
    "reason": "The current reset CTA clears route preset, search, quick filter, saved filter, and group-by together. Renaming the CTA from `重置条件` to wording that explicitly signals a full clear would address the hidden-state ambiguity without changing behavior."
  },
  {
    "path": "frontend/apps/web/src/components/page/PageToolbar.vue",
    "module": "active-condition reset affordance",
    "feature": "scope hint for hidden clears",
    "reason": "A small caption or hint next to the reset CTA could clarify that hidden route/group/filter state is also cleared. This stays display-only but is broader than a label-only change."
  },
  {
    "path": "frontend/apps/web/src/components/page/PageToolbar.vue",
    "module": "primary toolbar visibility",
    "feature": "sort-summary fallback visibility",
    "reason": "showPrimaryToolbar could be decomposed into a smaller rule that preserves the primary toolbar when sort summary remains relevant even if search is hidden. This is narrower than full section-gating redesign but is still more structural than a wording-only slice."
  }
]
```

## Scan Boundaries

- files read: 2
- repo-wide scan: no
- conclusions made: no implementation choice in this batch

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-552.yaml`: PASS

## Next Iteration Suggestion

- open a low-cost `screen` batch that picks the label-only `reset-all wording clarity` slice first, because it re-enters the display-only lane without touching behavior

# ITER-2026-04-01-544

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
    "module": "high-frequency filters header",
    "feature": "subset count ambiguity",
    "reason": "Optimized mode labels the section as `高频筛选（N）` using only prioritizedQuickFilters.length, while the remaining quick filters move under advanced filters. The count is technically correct for the subset but can read like the total quick-filter inventory because the non-optimized toolbar uses full quick filter totals."
  },
  {
    "path": "frontend/apps/web/src/components/page/PageToolbar.vue",
    "module": "primary toolbar visibility",
    "feature": "search-section-coupled sort visibility",
    "reason": "showPrimaryToolbar only checks whether the optimization composition keeps the `search` section visible. If a future composition hides search but still expects the sort summary block, the entire primary toolbar would disappear with it."
  },
  {
    "path": "frontend/apps/web/src/components/page/PageToolbar.vue",
    "module": "active-condition reset affordance",
    "feature": "hidden-state reset ambiguity",
    "reason": "resetActiveConditions clears route preset, search, quick filter, saved filter, and group-by together, but the optimized active-condition section can hide some of those dimensions via include rules. The reset CTA may therefore clear state that is not visibly represented in the current section."
  },
  {
    "path": "frontend/apps/web/src/views/ActionView.vue",
    "module": "route-preset provenance wording",
    "feature": "cross-surface source label divergence",
    "reason": "ListPage/PageToolbar now normalizes route-derived sources to `路由上下文`, while the non-native ActionView route-preset banner still prints the raw source value directly. The same preset provenance can therefore read differently across surfaces."
  }
]
```

## Scan Boundaries

- files read: 5
- repo-wide scan: no
- conclusions made: no implementation choice in this batch

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-544.yaml`: PASS

## Next Iteration Suggestion

- open a low-cost `screen` batch that picks one candidate family from this fresh bounded scan; cross-surface provenance wording and high-frequency subset count currently look like the cleanest display-only options

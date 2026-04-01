# ITER-2026-04-01-531

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
    "module": "optimized secondary metadata section",
    "feature": "count parity gap",
    "reason": "The optimized toolbar collapses searchable fields and search-panel metadata into a single '辅助信息' section, while the non-optimized toolbar exposes explicit totals like '可搜索字段（N）' and '分面维度（N）'. Count visibility is lost exactly in the optimized mode now used by the native list."
  },
  {
    "path": "frontend/apps/web/src/components/page/PageToolbar.vue",
    "module": "active condition summary",
    "feature": "default sort appears as an active condition",
    "reason": "activeStateChips always includes the current sort label when sortLabel exists, so '当前条件' can look non-empty even when the user only sees the native default sort. This is a display-only semantics mismatch and remains within the toolbar slice."
  },
  {
    "path": "frontend/apps/web/src/components/page/PageToolbar.vue",
    "module": "advanced filters toggle",
    "feature": "toggle count mixes actionable and static items",
    "reason": "advancedFilterCountText sums quick filters, saved filters, and static search-panel dimensions into one number for '展开高级筛选（N）'. The CTA may overstate how many real filter actions are behind the fold."
  },
  {
    "path": "frontend/apps/web/src/components/page/PageToolbar.vue",
    "module": "route preset provenance label",
    "feature": "source suppression for route-derived presets",
    "reason": "routePresetSourceText intentionally blanks scene/route/query/url sources, which keeps the label compact but can hide why a preset was applied when it came from route context rather than a menu recommendation."
  }
]
```

## Scan Boundaries

- files read: 5
- repo-wide scan: no
- conclusions made: no implementation choice in this batch

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-531.yaml`: PASS

## Next Iteration Suggestion

- open a low-cost `screen` batch that picks one candidate family from this list, with count-parity and active-condition semantics currently looking like the strongest display-only options

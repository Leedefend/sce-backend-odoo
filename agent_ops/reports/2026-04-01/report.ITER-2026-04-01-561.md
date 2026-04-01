# ITER-2026-04-01-561

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
    "module": "advanced-filter toggle count",
    "feature": "hidden facet options omitted from CTA inventory",
    "reason": "The advanced-filter CTA count is derived from advanced quick filters and saved filters only, but the expanded advanced panel can also render `advancedSearchPanelOptions`. When hidden facet options exist, the button undercounts the inventory it will reveal."
  },
  {
    "path": "frontend/apps/web/src/components/page/PageToolbar.vue",
    "module": "optimized route-preset visibility",
    "feature": "recommended preset can disappear from optimized toolbar sections",
    "reason": "The non-optimized toolbar has a dedicated `推荐筛选` block, but the optimized toolbar has no route-preset section and active-condition chips never create a preset chip. A route preset can therefore become invisible when optimization composition excludes it from visible active conditions."
  },
  {
    "path": "frontend/apps/web/src/components/page/PageToolbar.vue",
    "module": "search section visibility",
    "feature": "primary toolbar still renders search input when composition hides search",
    "reason": "Optimization mode now keeps the primary toolbar mounted when sort summary remains visible, but the search input itself is not gated by the `search` section visibility config. A composition that hides `search` can therefore still render the search box."
  },
  {
    "path": "frontend/apps/web/src/components/page/PageToolbar.vue",
    "module": "sort summary fallback visibility",
    "feature": "default sort summary keeps the sort block truthy even without explicit sort metadata",
    "reason": "The sort summary fallback text defaults to `默认`, and `showSortBlock` only checks whether any sort label text exists. This can keep the sort block visible even when no explicit sort controls or descriptive sort metadata are provided."
  }
]
```

## Scan Boundaries

- files read: 5
- repo-wide scan: no
- conclusions made: no implementation choice in this batch

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-561.yaml`: PASS

## Next Iteration Suggestion

- open a low-cost `screen` batch that selects one candidate family from this fresh bounded scan; advanced-filter toggle count alignment is currently the cleanest display-only option

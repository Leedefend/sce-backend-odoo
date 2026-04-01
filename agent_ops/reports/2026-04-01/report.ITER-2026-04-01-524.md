# ITER-2026-04-01-524

- status: PASS
- mode: scan
- layer_target: Frontend Layer
- module: native metadata list usability scan
- files_scanned: 7
- risk: low

## Structured Scan Output

```json
[
  {
    "path": "frontend/apps/web/src/components/page/PageToolbar.vue",
    "module": "native metadata list toolbar consumer",
    "feature": "route preset duplication cleanup",
    "reason": "The route preset is shown both in active-condition chips and in a dedicated recommendation group, which adds cognitive repetition without adding new state."
  },
  {
    "path": "frontend/apps/web/src/pages/ListPage.vue",
    "module": "grouped list usability",
    "feature": "group result header summary",
    "reason": "Grouped list controls expose sample-limit, paging, and sort actions, but the grouped header still presents weak current-state summary for the active grouping context."
  },
  {
    "path": "frontend/apps/web/src/components/page/PageToolbar.vue",
    "module": "native metadata list toolbar consumer",
    "feature": "searchable field preview density",
    "reason": "Searchable field chips can expand into a wide static block and currently rely on count text only, leaving the preview density unmanaged in narrow list surfaces."
  },
  {
    "path": "frontend/apps/web/src/pages/ListPage.vue",
    "module": "list status and summary strip",
    "feature": "summary strip relation to active list mode",
    "reason": "Summary cards sit outside the toolbar and current-condition area, so the relation between high-level metrics and the current filtered/grouped list state stays implicit."
  },
  {
    "path": "frontend/apps/web/src/views/ActionView.vue",
    "module": "native list surface handoff",
    "feature": "non-list and native-list route preset consistency",
    "reason": "ActionView preserves a separate non-native route-preset block while the native list surface also renders route preset state, creating a consistency candidate on the handoff boundary."
  }
]
```

## Risk Summary

- no forbidden paths touched
- no repo-wide scan used
- no implementation decision taken in this batch

## Next Suggestion

- open a `screen` stage that reads this report only and picks the next single low-risk usability batch candidate

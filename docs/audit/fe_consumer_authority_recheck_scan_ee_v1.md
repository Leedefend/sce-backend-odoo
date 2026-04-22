# FE Consumer Authority Recheck Scan EE

```json
[
  {
    "path": "frontend/apps/web/src/views/MenuView.vue",
    "module": "menu consumer scene resolution",
    "feature": "scene-first menu leaf and redirect consumption",
    "reason": "Current bounded read shows MenuView resolving carried scene key or action-derived scene first and degrading unresolved cases to workbench diagnostics rather than direct action-route authority."
  },
  {
    "path": "frontend/apps/web/src/views/MenuView.vue",
    "module": "menu consumer fallback surface",
    "feature": "workbench diagnostic fallback when scene identity is missing",
    "reason": "Current bounded read shows `replaceToWorkbenchMissingScene(...)` and other workbench-based fallbacks, so the strongest remaining question is whether any residual product-authority drift still exists beyond diagnostic downgrade."
  },
  {
    "path": "frontend/apps/web/src/views/RecordView.vue",
    "module": "record consumer action reopen",
    "feature": "scene-first reopen through findSceneByEntryAuthority",
    "reason": "Current bounded read shows `pushSceneOrAction(...)` already preferring scene route resolution and degrading scene-unprovable paths to workbench diagnostics instead of action-route authority."
  },
  {
    "path": "frontend/apps/web/src/views/RecordView.vue",
    "module": "record consumer record navigation",
    "feature": "scene-first form or record reopen with diagnostic fallback",
    "reason": "Current bounded read shows `resolveSceneFirstFormOrRecordLocation(...)` on record reopen and button-effect navigation, with `CONTRACT_CONTEXT_MISSING` workbench fallback when scene identity cannot be proven."
  },
  {
    "path": "docs/frontend/native_route_authority_audit_screen_v1.md",
    "module": "governance evidence drift",
    "feature": "older screen may overstate current consumer misalignment",
    "reason": "The older screen still describes MenuView and RecordView as direct action-route consumers, but the current bounded code read suggests those paths may already have converged, so a fresh screen is needed before more implementation."
  }
]
```

# project.management Route Context Protocol v1

## 1. Primary Route Context Protocol
- Primary protocol (fixed in v1):
  - `/s/project.management?project_id=<id>`
- Route layer responsibilities:
  - resolve scene entry
  - extract query `project_id`
  - forward `project_id` into intent context
  - do not execute business aggregation

## 2. Disallowed Mixed Route Schemes (v1)
- Do not introduce `/s/project.management/<id>` in v1.
- Do not rely on “route without params + random action-context only” as a parallel primary scheme.
- Keep one primary protocol to avoid runtime drift.

## 3. Context Injection Priority
`project.dashboard` resolves `project_id` in this order:
1. route query / request `params.project_id`
2. action/context payload `project_id`
3. user default/current project resolver
4. stable empty-state dashboard response

## 4. Runtime Bridge
- Scene runtime calls intent `project.dashboard`.
- Minimum request example:
```json
{
  "intent": "project.dashboard",
  "params": {
    "project_id": 123
  },
  "context": {
    "scene_key": "project.management",
    "page_key": "project.management.dashboard"
  }
}
```

## 5. Fallback Behavior
- If project cannot be resolved by `project_id` and user resolver:
  - return `ok=true`
  - return stable scene/page/project/zones contract
  - mark each block as `empty`/`forbidden`/`error` by block state rules

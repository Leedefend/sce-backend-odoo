# project.dashboard Contract v1

## 1. Intent
- Intent key: `project.dashboard`

## 2. Request
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

## 3. Response Envelope
```json
{
  "ok": true,
  "data": {
    "scene": {
      "key": "project.management",
      "page": "project.management.dashboard"
    },
    "page": {
      "key": "project.management.dashboard",
      "title": "项目驾驶舱",
      "route": "/s/project.management"
    },
    "route_context": {
      "primary_protocol": "/s/project.management?project_id=<id>",
      "query_key": "project_id",
      "scene_route": "/s/project.management",
      "project_route_template": "/s/project.management?project_id={project_id}",
      "project_route": "/s/project.management?project_id=123"
    },
    "project": {},
    "zones": {
      "header": {"zone_key": "zone.header", "blocks": []},
      "metrics": {"zone_key": "zone.metrics", "blocks": []},
      "progress": {"zone_key": "zone.progress", "blocks": []},
      "contract": {"zone_key": "zone.contract", "blocks": []},
      "cost": {"zone_key": "zone.cost", "blocks": []},
      "finance": {"zone_key": "zone.finance", "blocks": []},
      "risk": {"zone_key": "zone.risk", "blocks": []}
    }
  },
  "meta": {
    "intent": "project.dashboard",
    "trace_id": "",
    "contract_version": "v1"
  }
}
```

## 4. Block Common Fields
- `block_key`
- `block_type`
- `title`
- `state`: `ready | empty | error | forbidden`
- `visibility`: `{allowed, reason_code, reason}`
- `data`: typed payload by block type
- `error`: `{code, message}`

## 5. Stability Rules
- `scene`, `page`, `route_context`, `project`, `zones` are always present.
- Seven zones are always present.
- Each zone always has `blocks` list.
- Missing upstream data cannot change envelope shape.
- `route_context.primary_protocol` must stay `/s/project.management?project_id=<id>` in v1.

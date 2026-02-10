# Frontend v0.6 Release Notes (Draft)

## MVP Anchor (Business)
- model: project.project
- write_fields: name, description, date_start

## Write Contract (v0.6)
Response shape:
```
{
  "ok": true,
  "data": {
    "id": <number>,
    "model": "project.project",
    "written_fields": ["name"],
    "values": { "name": "..." }
  },
  "meta": {
    "trace_id": "...",
    "write_mode": "create|update",
    "source": "portal-shell"
  }
}
```

## Verification (System-bound)
### Verification Plane
Official release gate is **container plane** only.

### Gate Sequence (Container Plane)
1. `make verify.portal.view_state`
2. `make verify.portal.fe_smoke.container`
3. `make verify.portal.v0_6.container`

### Gate Command (template)
```
make verify.portal.v0_6.container \
  DB_NAME=sc_demo \
  MVP_MODEL=project.project \
  ROOT_XMLID=smart_construction_core.menu_sc_root \
  E2E_LOGIN=svc_project_ro \
  E2E_PASSWORD='***' \
  ARTIFACTS_DIR=artifacts/codex/portal-shell-v0_6/<TIMESTAMP>
```

### Verification Output (2026-02-03)
- [x] `make verify.portal.view_state` (PASS)
- [x] `make verify.portal.fe_smoke.container DB_NAME=sc_demo E2E_LOGIN=svc_project_ro E2E_PASSWORD=***` (PASS)
- [x] `make verify.portal.v0_6.container DB_NAME=sc_demo MVP_MODEL=project.project ROOT_XMLID=smart_construction_core.menu_sc_root E2E_LOGIN=svc_project_ro E2E_PASSWORD=*** ARTIFACTS_DIR=artifacts/codex/portal-shell-v0_6/20260203T065521` (PASS)

## MVP Trace
- write_status: ok
- read_back_match: true
- trace_id: aa44be5c0b20
- record_id: 44

## Artifacts
- fe_mvp_write_smoke logs: artifacts/codex/portal-shell-v0_6/20260203T065521/

## Attempts (Fail)
- (none)

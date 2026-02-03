# Frontend v0.5 Release Notes (Draft)

## MVP Anchor (Business)
- menu_id: 280
- menu_xmlid: smart_construction_core.menu_sc_project_project
- action_id: 495
- model: project.project
- view_mode: kanban,tree,form

## Verification (System-bound)
- [x] `MVP_MENU_XMLID=smart_construction_core.menu_sc_project_project DB_NAME=sc_demo ROOT_XMLID=smart_construction_core.menu_sc_root E2E_LOGIN=svc_project_ro E2E_PASSWORD=*** node scripts/verify/fe_mvp_list_smoke.js` (PASS)
- [x] `make bsi.create DB_NAME=sc_demo SERVICE_LOGIN=svc_project_ro SERVICE_PASSWORD=*** GROUP_XMLIDS=smart_construction_core.group_project_ro`
- [x] `make bsi.verify DB_NAME=sc_demo SERVICE_LOGIN=svc_project_ro MENU_XMLID=smart_construction_core.menu_sc_project_project ROOT_XMLID=smart_construction_core.menu_sc_root`
- [x] `make verify.portal.v0_5 DB_NAME=sc_demo MVP_MENU_XMLID=smart_construction_core.menu_sc_project_project ROOT_XMLID=smart_construction_core.menu_sc_root E2E_LOGIN=svc_project_ro E2E_PASSWORD=***` (PASS)
- [x] `make verify.portal.v0_5.container DB_NAME=sc_demo MVP_MENU_XMLID=smart_construction_core.menu_sc_project_project ROOT_XMLID=smart_construction_core.menu_sc_root E2E_LOGIN=svc_project_ro E2E_PASSWORD=***` (PASS)
- [x] `make verify.portal.view_state` (PASS)
- [ ] `make verify.portal.fe_smoke BASE_URL=http://localhost:8069 DB_NAME=sc_demo` (FAIL: status=000, AUTH_REQUIRED, curl connect)
- [ ] `make verify.portal.v0_5 DB_NAME=sc_demo MVP_MENU_XMLID=smart_construction_core.menu_sc_project_project ROOT_XMLID=smart_construction_core.menu_sc_root E2E_LOGIN=svc_project_ro E2E_PASSWORD=*** ARTIFACTS_DIR=artifacts/codex/portal-shell-v0_5/20260203T055140` (FAIL: connect EPERM 127.0.0.1:8070)

### Verification Output (2026-02-03)
`make verify.portal.view_state`
```text
PASS: Action ok
PASS: Action empty
PASS: Action error
PASS: Record ok
PASS: Record empty
PASS: Record error
```

`make verify.portal.fe_smoke BASE_URL=http://localhost:8069 DB_NAME=sc_demo`
```text
[14:05:59] fe_smoke: base=http://localhost:8069 db=sc_demo
[14:05:59] FAIL: status=000
response:
{"ok": false, "error": {"code": "AUTH_REQUIRED", "message": "认证失败或 token 无效"}, "meta": {"trace_id": "263a1fc09060", "api_version": "v1", "contract_version": "v0.1"}}curl: (7) Couldn't connect to server
make: *** [Makefile:430: verify.portal.fe_smoke] Error 1
```

`make verify.portal.v0_5 DB_NAME=sc_demo MVP_MENU_XMLID=smart_construction_core.menu_sc_project_project ROOT_XMLID=smart_construction_core.menu_sc_root E2E_LOGIN=svc_project_ro E2E_PASSWORD=*** ARTIFACTS_DIR=artifacts/codex/portal-shell-v0_5/20260203T055140`
```text
[fe_mvp_list_smoke] login: svc_project_ro db=sc_demo
FAIL: connect EPERM 127.0.0.1:8070 - Local (undefined:undefined)
make: *** [Makefile:435: verify.portal.v0_5] Error 1
```

## MVP Trace
- record_id: 22
- nav_version: 36
- list_status: ok
- record_status: ok
- list_empty_reason:

## Artifacts
- fe_mvp_list.log: artifacts/codex/portal-shell-v0_5/20260203T055140/fe_mvp_list.log
- fe_mvp_record.log: artifacts/codex/portal-shell-v0_5/20260203T055140/fe_mvp_record.log
- summary.md: artifacts/codex/portal-shell-v0_5/20260203T055140/summary.md

## Fixes Included in v0.5 PASS
- `addons/smart_core/handlers/system_init.py`: use `sudo()` for group xmlid resolution; fixes menu filtering for service users (reason: BSI groups unreadable caused root/menu not found; impact: all env).
- `addons/smart_core/app_config_engine/services/dispatchers/nav_dispatcher.py`: use `sudo()` for menu/group xmlid lookup; fixes missing `menu_xmlid` in nav tree (reason: anchor lookup failed; impact: all env).
- `addons/smart_core/handlers/load_view.py`: allow extra kwargs in handler signature; fixes `load_view` intent TypeError during record read (reason: client passes extra params; impact: all env).
- `addons/smart_core/view/universal_parser.py`: guard missing `ui.dynamic.config` model; fixes view parsing crash when model not installed (reason: env lookup error; impact: all env).

## Attempts (Fail)
- `MVP_MENU_XMLID=smart_construction_core.menu_sc_project_project DB_NAME=sc_demo ROOT_XMLID=smart_construction_core.menu_sc_root node scripts/verify/fe_mvp_list_smoke.js`
  - result: FAIL (Root menu not found: smart_construction_core.menu_sc_root)
  - trace_id: 2538051b3c5a
- `MVP_MENU_XMLID=smart_construction_core.menu_sc_project_project DB_NAME=sc_demo ROOT_XMLID= node scripts/verify/fe_mvp_list_smoke.js`
  - result: FAIL (menu not found for MVP anchor)

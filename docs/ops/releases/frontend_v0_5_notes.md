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

# Runtime Priority Matrix (Phase F-2 / Screen)

- Stage: `screen` (classification from existing scan artifacts only)
- Inputs: `http_route_inventory.md`, `http_route_classification.md`, `platform_entry_occupation.md`, `frontend_runtime_dependency.md`
- Method: map route objects to runtime chain and P-level using declared checklist criteria

| Route Object | Source File | Runtime Chain | Priority | Basis |
|---|---|---|---|---|
| `/api/capabilities/export` | `addons/smart_construction_core/controllers/capability_catalog_controller.py` | 治理辅助链 | P2 | 治理/运维/模板导入导出低频链 |
| `/api/capabilities/lint` | `addons/smart_construction_core/controllers/capability_catalog_controller.py` | 治理辅助链 | P2 | 治理/运维/模板导入导出低频链 |
| `/api/capabilities/search` | `addons/smart_construction_core/controllers/capability_catalog_controller.py` | 治理辅助链 | P2 | 治理/运维/模板导入导出低频链 |
| `/api/contract/capability_matrix` | `addons/smart_construction_core/controllers/capability_matrix_controller.py` | page/block fetch 链 | P1 | 核心交互/契约/高频能力链 |
| `/api/contract/portal_dashboard` | `addons/smart_construction_core/controllers/portal_dashboard_controller.py` | page/block fetch 链 | P1 | 核心交互/契约/高频能力链 |
| `/api/contract/portal_execute_button` | `addons/smart_construction_core/controllers/portal_execute_button_controller.py` | page/block fetch 链 | P1 | 默认归入核心运行链待后续细化 |
| `/api/execute_button` | `addons/smart_construction_core/controllers/execute_controller.py` | execute/action 链 | P1 | 核心交互/契约/高频能力链 |
| `/api/insight` | `addons/smart_construction_core/controllers/insight_controller.py` | 其他运行链 | P1 | 默认归入核心运行链待后续细化 |
| `/api/login` | `addons/smart_construction_core/controllers/frontend_api.py` | 登录链 | P0 | 登录/init/menu/scene 主链证据 |
| `/api/logout` | `addons/smart_construction_core/controllers/frontend_api.py` | 其他运行链 | P1 | 默认归入核心运行链待后续细化 |
| `/api/menu/tree` | `addons/smart_construction_core/controllers/frontend_api.py` | menu/nav 链 | P0 | 登录/init/menu/scene 主链证据 |
| `/api/meta/describe_model` | `addons/smart_construction_core/controllers/meta_controller.py` | 其他运行链 | P1 | 核心交互/契约/高频能力链 |
| `/api/meta/project_capabilities` | `addons/smart_construction_core/controllers/meta_controller.py` | 其他运行链 | P1 | 核心交互/契约/高频能力链 |
| `/api/ops/audit/search` | `addons/smart_construction_core/controllers/ops_controller.py` | 治理辅助链 | P2 | 治理/运维/模板导入导出低频链 |
| `/api/ops/job/status` | `addons/smart_construction_core/controllers/ops_controller.py` | 治理辅助链 | P2 | 治理/运维/模板导入导出低频链 |
| `/api/ops/packs/batch_rollback` | `addons/smart_construction_core/controllers/ops_controller.py` | 治理辅助链 | P2 | 治理/运维/模板导入导出低频链 |
| `/api/ops/packs/batch_upgrade` | `addons/smart_construction_core/controllers/ops_controller.py` | 治理辅助链 | P2 | 治理/运维/模板导入导出低频链 |
| `/api/ops/subscription/set` | `addons/smart_construction_core/controllers/ops_controller.py` | 治理辅助链 | P2 | 治理/运维/模板导入导出低频链 |
| `/api/ops/tenants` | `addons/smart_construction_core/controllers/ops_controller.py` | 治理辅助链 | P2 | 治理/运维/模板导入导出低频链 |
| `/api/packs/catalog` | `addons/smart_construction_core/controllers/pack_controller.py` | 治理辅助链 | P2 | 治理/运维/模板导入导出低频链 |
| `/api/packs/install` | `addons/smart_construction_core/controllers/pack_controller.py` | 治理辅助链 | P2 | 治理/运维/模板导入导出低频链 |
| `/api/packs/publish` | `addons/smart_construction_core/controllers/pack_controller.py` | 治理辅助链 | P2 | 治理/运维/模板导入导出低频链 |
| `/api/packs/upgrade` | `addons/smart_construction_core/controllers/pack_controller.py` | 治理辅助链 | P2 | 治理/运维/模板导入导出低频链 |
| `/api/portal/execute_button` | `addons/smart_construction_core/controllers/portal_execute_button_controller.py` | execute/action 链 | P1 | 核心交互/契约/高频能力链 |
| `/api/preferences/get` | `addons/smart_construction_core/controllers/preference_controller.py` | 其他运行链 | P2 | 治理/运维/模板导入导出低频链 |
| `/api/preferences/set` | `addons/smart_construction_core/controllers/preference_controller.py` | 其他运行链 | P2 | 治理/运维/模板导入导出低频链 |
| `/api/scenes/export` | `addons/smart_construction_core/controllers/scene_template_controller.py` | scene open 链 | P2 | 治理/运维/模板导入导出低频链 |
| `/api/scenes/import` | `addons/smart_construction_core/controllers/scene_template_controller.py` | scene open 链 | P2 | 治理/运维/模板导入导出低频链 |
| `/api/scenes/my` | `addons/smart_construction_core/controllers/scene_controller.py` | scene open 链 | P0 | 登录/init/menu/scene 主链证据 |
| `/api/session/get` | `addons/smart_construction_core/controllers/frontend_api.py` | 登录链 | P0 | 登录/init/menu/scene 主链证据 |
| `/api/ui/contract` | `addons/smart_construction_core/controllers/ui_contract_controller.py` | page/block fetch 链 | P1 | 核心交互/契约/高频能力链 |
| `/api/user_menus` | `addons/smart_construction_core/controllers/frontend_api.py` | menu/nav 链 | P3 | 兼容或边缘入口 |
| `/sc/auth/activate/<string:token>` | `addons/smart_construction_core/controllers/auth_signup.py` | 其他运行链 | P3 | 兼容或边缘入口 |
| `/web/signup` | `addons/smart_construction_core/controllers/auth_signup.py` | 其他运行链 | P3 | 兼容或边缘入口 |

## Priority Summary

- `P0`: `4` routes
- `P1`: `10` routes
- `P2`: `17` routes
- `P3`: `3` routes

## Screening Notes

- This matrix is a staging classification output for governance planning.
- Ownership finalization and migration sequencing are deferred to subsequent batches.

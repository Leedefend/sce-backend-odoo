# smart_construction_core HTTP Route Classification (Phase A / Screen)

- Stage: `screen` (classification only; no repository rescan)
- Input: `docs/audit/boundary/http_route_inventory.md`
- Rule set: A/B/C/D/E/F from user-provided boundary checklist

## Category Count

- `A`: `2`
- `B`: `12`
- `C`: `3`
- `D`: `13`
- `E`: `0`
- `F`: `4`

| File | Method | Route | Category | Classification Basis | Boundary Signal |
|---|---|---|---|---|---|
| `addons/smart_construction_core/controllers/auth_signup.py` | `sc_activate_account` | `/sc/auth/activate/<string:token>` | `B` | auth/session bootstrap entry | 疑似越界 |
| `addons/smart_construction_core/controllers/auth_signup.py` | `web_auth_signup` | `/web/signup` | `B` | auth/session bootstrap entry | 疑似越界 |
| `addons/smart_construction_core/controllers/capability_catalog_controller.py` | `export_capabilities` | `/api/capabilities/export` | `D` | catalog/governance capability surface | 疑似越界 |
| `addons/smart_construction_core/controllers/capability_catalog_controller.py` | `lint_capabilities` | `/api/capabilities/lint` | `D` | catalog/governance capability surface | 疑似越界 |
| `addons/smart_construction_core/controllers/capability_catalog_controller.py` | `search_capabilities` | `/api/capabilities/search` | `D` | catalog/governance capability surface | 疑似越界 |
| `addons/smart_construction_core/controllers/capability_matrix_controller.py` | `capability_matrix` | `/api/contract/capability_matrix` | `B` | ui contract/runtime entry | 疑似越界 |
| `addons/smart_construction_core/controllers/execute_controller.py` | `execute_button` | `/api/execute_button` | `F` | mixed meta/runtime/action surface | 疑似越界 |
| `addons/smart_construction_core/controllers/frontend_api.py` | `api_login` | `/api/login` | `B` | platform runtime entry | 明显越界 |
| `addons/smart_construction_core/controllers/frontend_api.py` | `api_logout` | `/api/logout` | `B` | platform runtime entry | 疑似越界 |
| `addons/smart_construction_core/controllers/frontend_api.py` | `api_menu_tree` | `/api/menu/tree` | `B` | platform runtime entry | 明显越界 |
| `addons/smart_construction_core/controllers/frontend_api.py` | `api_session_get` | `/api/session/get` | `B` | platform runtime entry | 明显越界 |
| `addons/smart_construction_core/controllers/frontend_api.py` | `api_user_menus` | `/api/user_menus` | `B` | platform runtime entry | 疑似越界 |
| `addons/smart_construction_core/controllers/insight_controller.py` | `get_insight` | `/api/insight` | `A` | domain insight entry | 待后续核验 |
| `addons/smart_construction_core/controllers/meta_controller.py` | `describe_model` | `/api/meta/describe_model` | `F` | mixed meta/runtime/action surface | 疑似越界 |
| `addons/smart_construction_core/controllers/meta_controller.py` | `describe_project_capabilities` | `/api/meta/project_capabilities` | `A` | industry business fact entry | 待后续核验 |
| `addons/smart_construction_core/controllers/ops_controller.py` | `audit_search` | `/api/ops/audit/search` | `D` | ops/pack governance entry | 疑似越界 |
| `addons/smart_construction_core/controllers/ops_controller.py` | `job_status` | `/api/ops/job/status` | `D` | ops/pack governance entry | 疑似越界 |
| `addons/smart_construction_core/controllers/ops_controller.py` | `batch_rollback` | `/api/ops/packs/batch_rollback` | `D` | ops/pack governance entry | 疑似越界 |
| `addons/smart_construction_core/controllers/ops_controller.py` | `batch_upgrade` | `/api/ops/packs/batch_upgrade` | `D` | ops/pack governance entry | 疑似越界 |
| `addons/smart_construction_core/controllers/ops_controller.py` | `set_subscription` | `/api/ops/subscription/set` | `D` | ops/pack governance entry | 疑似越界 |
| `addons/smart_construction_core/controllers/ops_controller.py` | `tenants` | `/api/ops/tenants` | `D` | ops/pack governance entry | 疑似越界 |
| `addons/smart_construction_core/controllers/pack_controller.py` | `catalog` | `/api/packs/catalog` | `D` | ops/pack governance entry | 疑似越界 |
| `addons/smart_construction_core/controllers/pack_controller.py` | `install_pack` | `/api/packs/install` | `D` | ops/pack governance entry | 疑似越界 |
| `addons/smart_construction_core/controllers/pack_controller.py` | `publish_pack` | `/api/packs/publish` | `D` | ops/pack governance entry | 疑似越界 |
| `addons/smart_construction_core/controllers/pack_controller.py` | `upgrade_pack` | `/api/packs/upgrade` | `D` | ops/pack governance entry | 疑似越界 |
| `addons/smart_construction_core/controllers/portal_dashboard_controller.py` | `portal_dashboard` | `/api/contract/portal_dashboard` | `B` | ui contract/runtime entry | 疑似越界 |
| `addons/smart_construction_core/controllers/portal_execute_button_controller.py` | `portal_execute_button_contract` | `/api/contract/portal_execute_button` | `B` | ui contract/runtime entry | 疑似越界 |
| `addons/smart_construction_core/controllers/portal_execute_button_controller.py` | `portal_execute_button` | `/api/portal/execute_button` | `B` | ui contract/runtime entry | 疑似越界 |
| `addons/smart_construction_core/controllers/preference_controller.py` | `pref_get` | `/api/preferences/get` | `C` | scene/template runtime entry | 疑似越界 |
| `addons/smart_construction_core/controllers/preference_controller.py` | `pref_set` | `/api/preferences/set` | `C` | scene/template runtime entry | 疑似越界 |
| `addons/smart_construction_core/controllers/scene_controller.py` | `my_scenes` | `/api/scenes/my` | `C` | scene/template runtime entry | 疑似越界 |
| `addons/smart_construction_core/controllers/scene_template_controller.py` | `export_scenes` | `/api/scenes/export` | `F` | scene + pack/template mixed surface | 疑似越界 |
| `addons/smart_construction_core/controllers/scene_template_controller.py` | `import_scenes` | `/api/scenes/import` | `F` | scene + pack/template mixed surface | 疑似越界 |
| `addons/smart_construction_core/controllers/ui_contract_controller.py` | `ui_contract` | `/api/ui/contract` | `B` | platform runtime entry | 疑似越界 |

## Category Definition Snapshot

- `A`: 行业业务事实入口
- `B`: 平台运行时入口（login/session/menu/app/nav/ui contract）
- `C`: 场景/模板入口
- `D`: 治理/发布/运维入口（ops/pack/catalog）
- `E`: 观测/遥测入口（telemetry/usage）
- `F`: 混合型入口（同时触碰多个语义面）

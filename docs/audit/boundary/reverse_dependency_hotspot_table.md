# Reverse Dependency Hotspot Table

| Rank | Hotspot File | Cross-Module Count | Target Summary | Impact Scope |
|---|---|---|---|---|
| `1` | `addons/smart_construction_core/core_extension.py` | `6` | `smart_construction_scene:6` | scene-coupling |
| `2` | `addons/smart_construction_core/handlers/cost_tracking_enter.py` | `4` | `smart_construction_scene:1, smart_core:3` | intent-router, platform-coupling, scene-coupling |
| `3` | `addons/smart_construction_core/handlers/payment_slice_enter.py` | `4` | `smart_construction_scene:1, smart_core:3` | intent-router, platform-coupling, scene-coupling |
| `4` | `addons/smart_construction_core/handlers/project_dashboard_enter.py` | `4` | `smart_construction_scene:1, smart_core:3` | intent-router, platform-coupling, scene-coupling |
| `5` | `addons/smart_construction_core/handlers/project_execution_enter.py` | `4` | `smart_construction_scene:1, smart_core:3` | intent-router, platform-coupling, scene-coupling |
| `6` | `addons/smart_construction_core/handlers/project_plan_bootstrap_enter.py` | `4` | `smart_construction_scene:1, smart_core:3` | intent-router, platform-coupling, scene-coupling |
| `7` | `addons/smart_construction_core/handlers/settlement_slice_enter.py` | `4` | `smart_construction_scene:1, smart_core:3` | intent-router, platform-coupling, scene-coupling |
| `8` | `addons/smart_construction_core/handlers/app_open.py` | `3` | `smart_core:3` | intent-router, platform-coupling |
| `9` | `addons/smart_construction_core/handlers/my_work_summary.py` | `3` | `smart_construction_scene:1, smart_core:2` | intent-router, platform-coupling, scene-coupling |
| `10` | `addons/smart_construction_core/handlers/payment_request_approval.py` | `3` | `smart_core:3` | intent-router, platform-coupling |
| `11` | `addons/smart_construction_core/tests/test_api_data_batch_contract_backend.py` | `3` | `smart_core:3` | platform-coupling |
| `12` | `addons/smart_construction_core/tests/test_api_data_write_unlink_idempotency_backend.py` | `3` | `smart_core:3` | platform-coupling |
| `13` | `addons/smart_construction_core/tests/test_user_role_profile_backend.py` | `3` | `smart_core:3` | platform-coupling |
| `14` | `addons/smart_construction_core/controllers/frontend_api.py` | `2` | `smart_core:2` | http-entry, platform-coupling |
| `15` | `addons/smart_construction_core/handlers/capability_describe.py` | `2` | `smart_core:2` | intent-router, platform-coupling |
| `16` | `addons/smart_construction_core/handlers/cost_tracking_block_fetch.py` | `2` | `smart_core:2` | intent-router, platform-coupling |
| `17` | `addons/smart_construction_core/handlers/my_work_complete.py` | `2` | `smart_core:2` | intent-router, platform-coupling |
| `18` | `addons/smart_construction_core/handlers/payment_request_available_actions.py` | `2` | `smart_core:2` | intent-router, platform-coupling |
| `19` | `addons/smart_construction_core/handlers/payment_request_execute.py` | `2` | `smart_core:2` | intent-router, platform-coupling |
| `20` | `addons/smart_construction_core/handlers/payment_slice_block_fetch.py` | `2` | `smart_core:2` | intent-router, platform-coupling |

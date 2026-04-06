# File Dependency Hotspots (Phase D-1 / Scan)

- Stage: `scan` (fact-only; outbound cross-module import hotspots)

| File | Cross-Module Import Count | Target Summary |
|---|---|---|
| `addons/smart_construction_core/core_extension.py` | `6` | `smart_construction_scene:6` |
| `addons/smart_construction_core/handlers/cost_tracking_enter.py` | `4` | `smart_construction_scene:1, smart_core:3` |
| `addons/smart_construction_core/handlers/payment_slice_enter.py` | `4` | `smart_construction_scene:1, smart_core:3` |
| `addons/smart_construction_core/handlers/project_dashboard_enter.py` | `4` | `smart_construction_scene:1, smart_core:3` |
| `addons/smart_construction_core/handlers/project_execution_enter.py` | `4` | `smart_construction_scene:1, smart_core:3` |
| `addons/smart_construction_core/handlers/project_plan_bootstrap_enter.py` | `4` | `smart_construction_scene:1, smart_core:3` |
| `addons/smart_construction_core/handlers/settlement_slice_enter.py` | `4` | `smart_construction_scene:1, smart_core:3` |
| `addons/smart_construction_core/handlers/app_open.py` | `3` | `smart_core:3` |
| `addons/smart_construction_core/handlers/my_work_summary.py` | `3` | `smart_construction_scene:1, smart_core:2` |
| `addons/smart_construction_core/handlers/payment_request_approval.py` | `3` | `smart_core:3` |
| `addons/smart_construction_core/tests/test_api_data_batch_contract_backend.py` | `3` | `smart_core:3` |
| `addons/smart_construction_core/tests/test_api_data_write_unlink_idempotency_backend.py` | `3` | `smart_core:3` |
| `addons/smart_construction_core/tests/test_user_role_profile_backend.py` | `3` | `smart_core:3` |
| `addons/smart_construction_core/controllers/frontend_api.py` | `2` | `smart_core:2` |
| `addons/smart_construction_core/handlers/capability_describe.py` | `2` | `smart_core:2` |
| `addons/smart_construction_core/handlers/cost_tracking_block_fetch.py` | `2` | `smart_core:2` |
| `addons/smart_construction_core/handlers/my_work_complete.py` | `2` | `smart_core:2` |
| `addons/smart_construction_core/handlers/payment_request_available_actions.py` | `2` | `smart_core:2` |
| `addons/smart_construction_core/handlers/payment_request_execute.py` | `2` | `smart_core:2` |
| `addons/smart_construction_core/handlers/payment_slice_block_fetch.py` | `2` | `smart_core:2` |
| `addons/smart_construction_core/handlers/project_dashboard.py` | `2` | `smart_core:2` |
| `addons/smart_construction_core/handlers/project_dashboard_block_fetch.py` | `2` | `smart_core:2` |
| `addons/smart_construction_core/handlers/project_execution_block_fetch.py` | `2` | `smart_core:2` |
| `addons/smart_construction_core/handlers/project_plan_bootstrap_block_fetch.py` | `2` | `smart_core:2` |
| `addons/smart_construction_core/handlers/risk_action_execute.py` | `2` | `smart_core:2` |
| `addons/smart_construction_core/handlers/settlement_slice_block_fetch.py` | `2` | `smart_core:2` |
| `addons/smart_construction_core/services/capability_registry.py` | `2` | `smart_construction_scene:2` |
| `addons/smart_construction_core/tests/test_project_plan_bootstrap_backend.py` | `2` | `smart_core:2` |
| `addons/smart_construction_core/controllers/capability_catalog_controller.py` | `1` | `smart_core:1` |
| `addons/smart_construction_core/controllers/execute_controller.py` | `1` | `smart_core:1` |
| `addons/smart_construction_core/controllers/ops_controller.py` | `1` | `smart_core:1` |
| `addons/smart_construction_core/controllers/pack_controller.py` | `1` | `smart_core:1` |
| `addons/smart_construction_core/controllers/preference_controller.py` | `1` | `smart_core:1` |
| `addons/smart_construction_core/controllers/scene_controller.py` | `1` | `smart_core:1` |
| `addons/smart_construction_core/controllers/scene_template_controller.py` | `1` | `smart_core:1` |
| `addons/smart_construction_core/handlers/app_catalog.py` | `1` | `smart_core:1` |
| `addons/smart_construction_core/handlers/app_nav.py` | `1` | `smart_core:1` |
| `addons/smart_construction_core/handlers/business_evidence_trace.py` | `1` | `smart_core:1` |
| `addons/smart_construction_core/handlers/capability_visibility_report.py` | `1` | `smart_core:1` |
| `addons/smart_construction_core/handlers/cost_tracking_record_create.py` | `1` | `smart_core:1` |

## Hotspot Evidence (Top 20)

- `addons/smart_construction_core/core_extension.py`
  - `addons/smart_construction_core/core_extension.py:490` -> `smart_construction_scene` via `from odoo.addons.smart_construction_scene.services.scene_package_service import ...`
  - `addons/smart_construction_core/core_extension.py:499` -> `smart_construction_scene` via `from odoo.addons.smart_construction_scene.services.scene_governance_service import ...`
  - `addons/smart_construction_core/core_extension.py:507` -> `smart_construction_scene` via `from odoo.addons.smart_construction_scene.scene_registry import ...`
  - `addons/smart_construction_core/core_extension.py:518` -> `smart_construction_scene` via `from odoo.addons.smart_construction_scene.scene_registry import ...`
  - `addons/smart_construction_core/core_extension.py:530` -> `smart_construction_scene` via `from odoo.addons.smart_construction_scene.scene_registry import ...`
  - `addons/smart_construction_core/core_extension.py:542` -> `smart_construction_scene` via `from odoo.addons.smart_construction_scene.scene_registry import ...`
- `addons/smart_construction_core/handlers/cost_tracking_enter.py`
  - `addons/smart_construction_core/handlers/cost_tracking_enter.py:7` -> `smart_core` via `from odoo.addons.smart_core.core.base_handler import ...`
  - `addons/smart_construction_core/handlers/cost_tracking_enter.py:8` -> `smart_core` via `from odoo.addons.smart_core.core.scene_contract_builder import ...`
  - `addons/smart_construction_core/handlers/cost_tracking_enter.py:12` -> `smart_core` via `from odoo.addons.smart_core.orchestration.cost_tracking_contract_orchestrator import ...`
  - `addons/smart_construction_core/handlers/cost_tracking_enter.py:15` -> `smart_construction_scene` via `from odoo.addons.smart_construction_scene.services.project_management_entry_target import ...`
- `addons/smart_construction_core/handlers/payment_slice_enter.py`
  - `addons/smart_construction_core/handlers/payment_slice_enter.py:7` -> `smart_core` via `from odoo.addons.smart_core.core.base_handler import ...`
  - `addons/smart_construction_core/handlers/payment_slice_enter.py:8` -> `smart_core` via `from odoo.addons.smart_core.core.scene_contract_builder import ...`
  - `addons/smart_construction_core/handlers/payment_slice_enter.py:12` -> `smart_core` via `from odoo.addons.smart_core.orchestration.payment_slice_contract_orchestrator import ...`
  - `addons/smart_construction_core/handlers/payment_slice_enter.py:15` -> `smart_construction_scene` via `from odoo.addons.smart_construction_scene.services.project_management_entry_target import ...`
- `addons/smart_construction_core/handlers/project_dashboard_enter.py`
  - `addons/smart_construction_core/handlers/project_dashboard_enter.py:7` -> `smart_core` via `from odoo.addons.smart_core.core.base_handler import ...`
  - `addons/smart_construction_core/handlers/project_dashboard_enter.py:8` -> `smart_core` via `from odoo.addons.smart_core.core.scene_contract_builder import ...`
  - `addons/smart_construction_core/handlers/project_dashboard_enter.py:12` -> `smart_core` via `from odoo.addons.smart_core.orchestration.project_dashboard_scene_orchestrator import ...`
  - `addons/smart_construction_core/handlers/project_dashboard_enter.py:15` -> `smart_construction_scene` via `from odoo.addons.smart_construction_scene.services.project_management_entry_target import ...`
- `addons/smart_construction_core/handlers/project_execution_enter.py`
  - `addons/smart_construction_core/handlers/project_execution_enter.py:7` -> `smart_core` via `from odoo.addons.smart_core.core.base_handler import ...`
  - `addons/smart_construction_core/handlers/project_execution_enter.py:8` -> `smart_core` via `from odoo.addons.smart_core.core.scene_contract_builder import ...`
  - `addons/smart_construction_core/handlers/project_execution_enter.py:12` -> `smart_core` via `from odoo.addons.smart_core.orchestration.project_execution_scene_orchestrator import ...`
  - `addons/smart_construction_core/handlers/project_execution_enter.py:15` -> `smart_construction_scene` via `from odoo.addons.smart_construction_scene.services.project_management_entry_target import ...`
- `addons/smart_construction_core/handlers/project_plan_bootstrap_enter.py`
  - `addons/smart_construction_core/handlers/project_plan_bootstrap_enter.py:7` -> `smart_core` via `from odoo.addons.smart_core.core.base_handler import ...`
  - `addons/smart_construction_core/handlers/project_plan_bootstrap_enter.py:8` -> `smart_core` via `from odoo.addons.smart_core.core.scene_contract_builder import ...`
  - `addons/smart_construction_core/handlers/project_plan_bootstrap_enter.py:9` -> `smart_core` via `from odoo.addons.smart_core.orchestration.project_plan_bootstrap_scene_orchestrator import ...`
  - `addons/smart_construction_core/handlers/project_plan_bootstrap_enter.py:12` -> `smart_construction_scene` via `from odoo.addons.smart_construction_scene.services.project_management_entry_target import ...`
- `addons/smart_construction_core/handlers/settlement_slice_enter.py`
  - `addons/smart_construction_core/handlers/settlement_slice_enter.py:7` -> `smart_core` via `from odoo.addons.smart_core.core.base_handler import ...`
  - `addons/smart_construction_core/handlers/settlement_slice_enter.py:8` -> `smart_core` via `from odoo.addons.smart_core.core.scene_contract_builder import ...`
  - `addons/smart_construction_core/handlers/settlement_slice_enter.py:12` -> `smart_core` via `from odoo.addons.smart_core.orchestration.settlement_slice_contract_orchestrator import ...`
  - `addons/smart_construction_core/handlers/settlement_slice_enter.py:15` -> `smart_construction_scene` via `from odoo.addons.smart_construction_scene.services.project_management_entry_target import ...`
- `addons/smart_construction_core/handlers/app_open.py`
  - `addons/smart_construction_core/handlers/app_open.py:6` -> `smart_core` via `from odoo.addons.smart_core.core.base_handler import ...`
  - `addons/smart_construction_core/handlers/app_open.py:10` -> `smart_core` via `from odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher import ...`
  - `addons/smart_construction_core/handlers/app_open.py:11` -> `smart_core` via `from odoo.addons.smart_core.app_config_engine.services.contract_service import ...`
- `addons/smart_construction_core/handlers/my_work_summary.py`
  - `addons/smart_construction_core/handlers/my_work_summary.py:7` -> `smart_core` via `from odoo.addons.smart_core.core.base_handler import ...`
  - `addons/smart_construction_core/handlers/my_work_summary.py:8` -> `smart_core` via `from odoo.addons.smart_core.utils.reason_codes import ...`
  - `addons/smart_construction_core/handlers/my_work_summary.py:27` -> `smart_construction_scene` via `from odoo.addons.smart_construction_scene.services.my_work_scene_targets import ...`
- `addons/smart_construction_core/handlers/payment_request_approval.py`
  - `addons/smart_construction_core/handlers/payment_request_approval.py:6` -> `smart_core` via `from odoo.addons.smart_core.core.base_handler import ...`
  - `addons/smart_construction_core/handlers/payment_request_approval.py:7` -> `smart_core` via `from odoo.addons.smart_core.handlers.reason_codes import ...`
  - `addons/smart_construction_core/handlers/payment_request_approval.py:17` -> `smart_core` via `from odoo.addons.smart_core.utils.idempotency import ...`
- `addons/smart_construction_core/tests/test_api_data_batch_contract_backend.py`
  - `addons/smart_construction_core/tests/test_api_data_batch_contract_backend.py:7` -> `smart_core` via `from odoo.addons.smart_core.handlers.reason_codes import ...`
  - `addons/smart_construction_core/tests/test_api_data_batch_contract_backend.py:11` -> `smart_core` via `from odoo.addons.smart_core.handlers.api_data_batch import ...`
  - `addons/smart_construction_core/tests/test_api_data_batch_contract_backend.py:12` -> `smart_core` via `from odoo.addons.smart_core.utils.idempotency import ...`
- `addons/smart_construction_core/tests/test_api_data_write_unlink_idempotency_backend.py`
  - `addons/smart_construction_core/tests/test_api_data_write_unlink_idempotency_backend.py:7` -> `smart_core` via `from odoo.addons.smart_core.handlers.api_data_unlink import ...`
  - `addons/smart_construction_core/tests/test_api_data_write_unlink_idempotency_backend.py:8` -> `smart_core` via `from odoo.addons.smart_core.handlers.api_data_write import ...`
  - `addons/smart_construction_core/tests/test_api_data_write_unlink_idempotency_backend.py:9` -> `smart_core` via `from odoo.addons.smart_core.handlers.reason_codes import ...`
- `addons/smart_construction_core/tests/test_user_role_profile_backend.py`
  - `addons/smart_construction_core/tests/test_user_role_profile_backend.py:8` -> `smart_core` via `from odoo.addons.smart_core.handlers.api_data import ...`
  - `addons/smart_construction_core/tests/test_user_role_profile_backend.py:9` -> `smart_core` via `from odoo.addons.smart_core.handlers.ui_contract import ...`
  - `addons/smart_construction_core/tests/test_user_role_profile_backend.py:10` -> `smart_core` via `from odoo.addons.smart_core.identity.identity_resolver import ...`
- `addons/smart_construction_core/controllers/frontend_api.py`
  - `addons/smart_construction_core/controllers/frontend_api.py:6` -> `smart_core` via `from odoo.addons.smart_core.core.trace import ...`
  - `addons/smart_construction_core/controllers/frontend_api.py:7` -> `smart_core` via `from odoo.addons.smart_core.core.exceptions import ...`
- `addons/smart_construction_core/handlers/capability_describe.py`
  - `addons/smart_construction_core/handlers/capability_describe.py:4` -> `smart_core` via `from odoo.addons.smart_core.core.base_handler import ...`
  - `addons/smart_construction_core/handlers/capability_describe.py:5` -> `smart_core` via `from odoo.addons.smart_core.handlers.system_init import ...`
- `addons/smart_construction_core/handlers/cost_tracking_block_fetch.py`
  - `addons/smart_construction_core/handlers/cost_tracking_block_fetch.py:7` -> `smart_core` via `from odoo.addons.smart_core.core.base_handler import ...`
  - `addons/smart_construction_core/handlers/cost_tracking_block_fetch.py:11` -> `smart_core` via `from odoo.addons.smart_core.orchestration.cost_tracking_contract_orchestrator import ...`
- `addons/smart_construction_core/handlers/my_work_complete.py`
  - `addons/smart_construction_core/handlers/my_work_complete.py:9` -> `smart_core` via `from odoo.addons.smart_core.core.base_handler import ...`
  - `addons/smart_construction_core/handlers/my_work_complete.py:17` -> `smart_core` via `from odoo.addons.smart_core.utils.idempotency import ...`
- `addons/smart_construction_core/handlers/payment_request_available_actions.py`
  - `addons/smart_construction_core/handlers/payment_request_available_actions.py:6` -> `smart_core` via `from odoo.addons.smart_core.core.base_handler import ...`
  - `addons/smart_construction_core/handlers/payment_request_available_actions.py:7` -> `smart_core` via `from odoo.addons.smart_core.handlers.reason_codes import ...`
- `addons/smart_construction_core/handlers/payment_request_execute.py`
  - `addons/smart_construction_core/handlers/payment_request_execute.py:6` -> `smart_core` via `from odoo.addons.smart_core.core.base_handler import ...`
  - `addons/smart_construction_core/handlers/payment_request_execute.py:7` -> `smart_core` via `from odoo.addons.smart_core.handlers.reason_codes import ...`
- `addons/smart_construction_core/handlers/payment_slice_block_fetch.py`
  - `addons/smart_construction_core/handlers/payment_slice_block_fetch.py:7` -> `smart_core` via `from odoo.addons.smart_core.core.base_handler import ...`
  - `addons/smart_construction_core/handlers/payment_slice_block_fetch.py:11` -> `smart_core` via `from odoo.addons.smart_core.orchestration.payment_slice_contract_orchestrator import ...`

# Module Dependency Graph (Phase D-1 / Scan)

- Stage: `scan` (fact-only; import-direction evidence)
- Scope: `addons/smart_construction_core/**`, `addons/smart_core/**`, `addons/smart_construction_scene/**`

## Directed Edge Counts

| Source Module | Target Module | Import Evidence Count |
|---|---|---|
| `smart_construction_core` | `smart_construction_core` | `174` |
| `smart_construction_core` | `smart_core` | `99` |
| `smart_construction_core` | `smart_construction_scene` | `18` |
| `smart_core` | `smart_construction_core` | `7` |
| `smart_core` | `smart_core` | `174` |
| `smart_core` | `smart_construction_scene` | `0` |
| `smart_construction_scene` | `smart_construction_core` | `0` |
| `smart_construction_scene` | `smart_core` | `1` |
| `smart_construction_scene` | `smart_construction_scene` | `4` |

## Edge Evidence Samples

- `smart_construction_core -> smart_construction_core`
  - `addons/smart_construction_core/core_extension.py:258` → `from odoo.addons.smart_construction_core.handlers.system_ping_construction import ...`
  - `addons/smart_construction_core/core_extension.py:261` → `from odoo.addons.smart_construction_core.handlers.capability_describe import ...`
  - `addons/smart_construction_core/core_extension.py:264` → `from odoo.addons.smart_construction_core.handlers.my_work_summary import ...`
  - `addons/smart_construction_core/core_extension.py:267` → `from odoo.addons.smart_construction_core.handlers.my_work_complete import ...`
  - `addons/smart_construction_core/core_extension.py:271` → `from odoo.addons.smart_construction_core.handlers.usage_track import ...`
  - `addons/smart_construction_core/core_extension.py:274` → `from odoo.addons.smart_construction_core.handlers.telemetry_track import ...`
  - `addons/smart_construction_core/core_extension.py:277` → `from odoo.addons.smart_construction_core.handlers.usage_report import ...`
  - `addons/smart_construction_core/core_extension.py:280` → `from odoo.addons.smart_construction_core.handlers.usage_export_csv import ...`
- `smart_construction_core -> smart_construction_scene`
  - `addons/smart_construction_core/core_extension.py:490` → `from odoo.addons.smart_construction_scene.services.scene_package_service import ...`
  - `addons/smart_construction_core/core_extension.py:499` → `from odoo.addons.smart_construction_scene.services.scene_governance_service import ...`
  - `addons/smart_construction_core/core_extension.py:507` → `from odoo.addons.smart_construction_scene.scene_registry import ...`
  - `addons/smart_construction_core/core_extension.py:518` → `from odoo.addons.smart_construction_scene.scene_registry import ...`
  - `addons/smart_construction_core/core_extension.py:530` → `from odoo.addons.smart_construction_scene.scene_registry import ...`
  - `addons/smart_construction_core/core_extension.py:542` → `from odoo.addons.smart_construction_scene.scene_registry import ...`
  - `addons/smart_construction_core/handlers/cost_tracking_enter.py:15` → `from odoo.addons.smart_construction_scene.services.project_management_entry_target import ...`
  - `addons/smart_construction_core/handlers/my_work_summary.py:27` → `from odoo.addons.smart_construction_scene.services.my_work_scene_targets import ...`
- `smart_construction_core -> smart_core`
  - `addons/smart_construction_core/controllers/capability_catalog_controller.py:8` → `from odoo.addons.smart_core.security.auth import ...`
  - `addons/smart_construction_core/controllers/execute_controller.py:7` → `from odoo.addons.smart_core.handlers.ui_contract import ...`
  - `addons/smart_construction_core/controllers/frontend_api.py:6` → `from odoo.addons.smart_core.core.trace import ...`
  - `addons/smart_construction_core/controllers/frontend_api.py:7` → `from odoo.addons.smart_core.core.exceptions import ...`
  - `addons/smart_construction_core/controllers/ops_controller.py:7` → `from odoo.addons.smart_core.security.auth import ...`
  - `addons/smart_construction_core/controllers/pack_controller.py:7` → `from odoo.addons.smart_core.security.auth import ...`
  - `addons/smart_construction_core/controllers/preference_controller.py:8` → `from odoo.addons.smart_core.security.auth import ...`
  - `addons/smart_construction_core/controllers/scene_controller.py:12` → `from odoo.addons.smart_core.security.auth import ...`
- `smart_construction_scene -> smart_construction_scene`
  - `addons/smart_construction_scene/models/scene_governance_wizard.py:5` → `from odoo.addons.smart_construction_scene.services.scene_governance_service import ...`
  - `addons/smart_construction_scene/services/capability_scene_targets.py:6` → `from odoo.addons.smart_construction_scene import ...`
  - `addons/smart_construction_scene/services/project_management_entry_target.py:6` → `from odoo.addons.smart_construction_scene.scene_registry import ...`
  - `addons/smart_construction_scene/services/scene_package_service.py:10` → `from odoo.addons.smart_construction_scene import ...`
- `smart_construction_scene -> smart_core`
  - `addons/smart_construction_scene/services/scene_package_service.py:325` → `from odoo.addons.smart_core.handlers.system_init import ...`
- `smart_core -> smart_construction_core`
  - `addons/smart_core/orchestration/cost_tracking_contract_orchestrator.py:4` → `from odoo.addons.smart_construction_core.services.cost_tracking_service import ...`
  - `addons/smart_core/orchestration/payment_slice_contract_orchestrator.py:4` → `from odoo.addons.smart_construction_core.services.payment_slice_service import ...`
  - `addons/smart_core/orchestration/project_dashboard_contract_orchestrator.py:7` → `from odoo.addons.smart_construction_core.services.project_dashboard_service import ...`
  - `addons/smart_core/orchestration/project_dashboard_scene_orchestrator.py:4` → `from odoo.addons.smart_construction_core.services.project_dashboard_service import ...`
  - `addons/smart_core/orchestration/project_execution_scene_orchestrator.py:4` → `from odoo.addons.smart_construction_core.services.project_execution_service import ...`
  - `addons/smart_core/orchestration/project_plan_bootstrap_scene_orchestrator.py:4` → `from odoo.addons.smart_construction_core.services.project_plan_bootstrap_service import ...`
  - `addons/smart_core/orchestration/settlement_slice_contract_orchestrator.py:4` → `from odoo.addons.smart_construction_core.services.settlement_slice_service import ...`
- `smart_core -> smart_core`
  - `addons/smart_core/adapters/odoo_nav_adapter.py:6` → `from odoo.addons.smart_core.utils.extension_hooks import ...`
  - `addons/smart_core/app_config_engine/controllers/contract_api.py:9` → `from odoo.addons.smart_core.app_config_engine.services.contract_service import ...`
  - `addons/smart_core/app_config_engine/controllers/contract_api.py:10` → `from odoo.addons.smart_core.core.trace import ...`
  - `addons/smart_core/app_config_engine/controllers/contract_api.py:11` → `from odoo.addons.smart_core.core.exceptions import ...`
  - `addons/smart_core/app_config_engine/models/app_view_config.py:19` → `from odoo.addons.smart_core.app_config_engine.services.native_parse_service import ...`
  - `addons/smart_core/app_config_engine/models/app_view_config.py:20` → `from odoo.addons.smart_core.app_config_engine.services.parse_fallback_service import ...`
  - `addons/smart_core/app_config_engine/models/app_view_config.py:21` → `from odoo.addons.smart_core.app_config_engine.services.contract_governance_filter import ...`
  - `addons/smart_core/app_config_engine/services/contract_service.py:25` → `from odoo.addons.smart_core.app_config_engine.utils.http import ...`

# Smart Core Inventory

## Scope
This document inventories smart_core assets and where contract dependencies (`app.*.config`) are defined and used.

## Module entry points
- Module: `addons/smart_core/__manifest__.py`
- Main package: `addons/smart_core/__init__.py`

## Controllers
- `addons/smart_core/controllers/dashboard_controller.py`
- `addons/smart_core/controllers/enhanced_intent_dispatcher.py`
- `addons/smart_core/controllers/frontend_api.py`
- `addons/smart_core/controllers/intent_dispatcher.py`
- App config engine controller:
  - `addons/smart_core/app_config_engine/controllers/contract_api.py`

## Handlers (contract/intent)
- `addons/smart_core/handlers/ui_contract.py`
- `addons/smart_core/handlers/enhanced_ui_contract.py`
- `addons/smart_core/handlers/execute_button.py`
- `addons/smart_core/handlers/api_data.py`
- `addons/smart_core/handlers/load_contract.py`
- `addons/smart_core/handlers/load_metadata.py`
- `addons/smart_core/handlers/load_view.py`
- `addons/smart_core/handlers/app_open.py`
- `addons/smart_core/handlers/app_nav.py`
- `addons/smart_core/handlers/app_catalog.py`
- `addons/smart_core/handlers/meta_describe.py`
- `addons/smart_core/handlers/system_init.py`
- `addons/smart_core/handlers/login.py`

## Core services
- Contract service:
  - `addons/smart_core/app_config_engine/services/contract_service.py`
- Assemblers:
  - `addons/smart_core/app_config_engine/services/assemblers/page_assembler.py`
  - `addons/smart_core/app_config_engine/services/assemblers/client_url_report.py`
- Dispatchers:
  - `addons/smart_core/app_config_engine/services/dispatchers/action_dispatcher.py`
  - `addons/smart_core/app_config_engine/services/dispatchers/menu_dispatcher.py`
  - `addons/smart_core/app_config_engine/services/dispatchers/nav_dispatcher.py`
- Resolvers:
  - `addons/smart_core/app_config_engine/services/resolvers/action_resolver.py`

## Models
App config engine models:
- `addons/smart_core/app_config_engine/models/app_model_config.py` (`app.model.config`)
- `addons/smart_core/app_config_engine/models/app_view_config.py` (`app.view.config`)
- `addons/smart_core/app_config_engine/models/app_action_config.py` (`app.action.config`)
- `addons/smart_core/app_config_engine/models/app_search_config.py` (`app.search.config`)
- `addons/smart_core/app_config_engine/models/app_permission_config.py` (`app.permission.config`)
- `addons/smart_core/app_config_engine/models/app_report_config.py` (`app.report.config`)
- `addons/smart_core/app_config_engine/models/app_workflow_config.py` (`app.workflow.config`)
- `addons/smart_core/app_config_engine/models/app_validator_config.py` (`app.validator.config`)
- Other configs:
  - `addons/smart_core/app_config_engine/models/app.rule.config.py`
  - `addons/smart_core/app_config_engine/models/app.ui.config.py`
  - `addons/smart_core/app_config_engine/models/app.nav.config.py`
  - `addons/smart_core/app_config_engine/models/app.kpi.config.py`

Misc models:
- `addons/smart_core/models/dashboard.py`
- `addons/smart_core/models/dashboard_widget.py`
- `addons/smart_core/model/ui_dynamic_config.py`

## Security and data
- Security:
  - `addons/smart_core/security/smart_core_security.xml`
  - `addons/smart_core/security/ir.model.access.csv`
  - `addons/smart_core/app_config_engine/security/ir.model.access.csv`
- Views:
  - `addons/smart_core/views/dashboard_views.xml`
- Registry:
  - `addons/smart_core/app_registry/project_management.yaml`

## Contract docs and specs
- `addons/smart_core/docs/Contract-2.0-Spec.md`
- `addons/smart_core/docs/契约手册.md`
- `addons/smart_core/contract.schema.json`

## app.*.config usage (key call sites)
- `addons/smart_core/app_config_engine/services/assemblers/page_assembler.py`
  - app.model.config
  - app.view.config
  - app.search.config
  - app.permission.config
  - app.action.config
  - app.report.config
  - app.workflow.config
  - app.validator.config

## Contract entry points
- `addons/smart_core/app_config_engine/controllers/contract_api.py`
- `addons/smart_core/handlers/ui_contract.py`
- `addons/smart_core/handlers/enhanced_ui_contract.py`
- `addons/smart_core/app_config_engine/services/contract_service.py`

## Known risks
- Missing app.*.config models can break contract assembly (handled via degrade fallback in page_assembler).
- Contract output stability depends on deterministic ordering and consistent default data (snapshots can drift).


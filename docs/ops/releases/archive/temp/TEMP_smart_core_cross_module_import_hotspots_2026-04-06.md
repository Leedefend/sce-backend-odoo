# TEMP smart_core cross-module import hotspots (2026-04-06)

## Scope

- target scan path:
  - `addons/smart_core/orchestration`
  - `addons/smart_core/core`
  - `addons/smart_core/controllers`
- pattern:
  - `odoo.addons.smart_construction_core`
- source evidence:
  - `artifacts/smart_core_cross_module_import_hotspots_2026-04-06.txt`

## Hotspot Inventory

| # | path | import target | hotspot type | stop-condition tag | migration priority |
|---|------|---------------|--------------|--------------------|--------------------|
| 1 | `addons/smart_core/orchestration/project_execution_scene_orchestrator.py` | `...services.project_execution_service` | orchestration direct service import | none | P1 |
| 2 | `addons/smart_core/orchestration/project_dashboard_scene_orchestrator.py` | `...services.project_dashboard_service` | orchestration direct service import | none | P1 |
| 3 | `addons/smart_core/orchestration/project_plan_bootstrap_scene_orchestrator.py` | `...services.project_plan_bootstrap_service` | orchestration direct service import | none | P1 |
| 4 | `addons/smart_core/orchestration/project_dashboard_contract_orchestrator.py` | `...services.project_dashboard_service` | orchestration direct service import | none | P1 |
| 5 | `addons/smart_core/orchestration/cost_tracking_contract_orchestrator.py` | `...services.cost_tracking_service` | orchestration direct service import | none | P1 |
| 6 | `addons/smart_core/orchestration/settlement_slice_contract_orchestrator.py` | `...services.settlement_slice_service` | orchestration direct service import | `*settlement*` forbidden-touch trigger | HOLD |
| 7 | `addons/smart_core/orchestration/payment_slice_contract_orchestrator.py` | `...services.payment_slice_service` | orchestration direct service import | `*payment*` forbidden-touch trigger | HOLD |

## Audit Conclusions

- controllers/core path has been cleaned in current chain; residual direct imports are concentrated in orchestration.
- two hotspots are currently blocked by repository hard stop rules (`*payment*`, `*settlement*`) and require dedicated high-risk task authorization before modification.
- remaining five non-forbidden hotspots can enter next low-risk migration line (protocol adapter or extension-provider pattern) without touching forbidden path patterns.

## Next Suggested Batch

- batch type: implementation (low-risk)
- target set:
  - `project_execution_scene_orchestrator.py`
  - `project_dashboard_scene_orchestrator.py`
  - `project_plan_bootstrap_scene_orchestrator.py`
  - `project_dashboard_contract_orchestrator.py`
  - `cost_tracking_contract_orchestrator.py`
- non-target (blocked):
  - `payment_slice_contract_orchestrator.py`
  - `settlement_slice_contract_orchestrator.py`

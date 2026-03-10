# Project Management Capability Mapping v1

## 1. Mapping Purpose
- Provide explicit traceability between:
  - scene/page/zone/block
  - capability key
  - source model
  - source action/menu
  - runtime intent

## 2. Scene/Page
- `scene_key`: `project.management`
- `page_key`: `project.management.dashboard`

## 3. Zone/Block Mapping

| Zone Key | Block Key | Existing Capability Key | Source Model | Source Action XMLID | Intent |
| --- | --- | --- | --- | --- | --- |
| `zone.header` | `block.project.header` | `project.dashboard.open` | `project.project` | `smart_construction_core.action_sc_project_kanban_lifecycle` | `ui.contract` |
| `zone.metrics` | `block.project.metrics` | `project.dashboard.open` | `project.project` | `smart_construction_core.action_project_dashboard` | `ui.contract` |
| `zone.progress` | `block.project.progress` | `cost.progress.report` | `project.progress.entry` / `project.task` | `smart_construction_core.action_project_progress_entry` | `ui.contract` |
| `zone.contract` | `block.project.contract` | `contract.center.open` | `construction.contract` | `smart_construction_core.action_construction_contract_my` | `ui.contract` |
| `zone.cost` | `block.project.cost` | `cost.ledger.open` | `project.cost.ledger` / `project.budget` | `smart_construction_core.action_project_cost_ledger` | `ui.contract` |
| `zone.finance` | `block.project.finance` | `finance.payment_request.list` | `payment.request` / `sc.settlement.order` | `smart_construction_core.action_payment_request` | `ui.contract` |
| `zone.risk` | `block.project.risk` | `project.risk.list` | `project.project` (+ derived risk rules in v1) | `smart_construction_core.action_project_dashboard` | `ui.contract` |

## 4. Planned Alias Capability Keys (not introduced yet)
- `capability.project.overview`
- `capability.project.progress`
- `capability.project.contract`
- `capability.project.cost`
- `capability.project.finance`
- `capability.project.risk`

These aliases are product-level naming suggestions and are intentionally not added yet to avoid breaking existing capability governance and guard rules.

## 5. Guardrail
- v1 implementation reuses current capability registry keys.
- Any future capability alias onboarding must pass:
  - capability naming lint
  - scene-capability mapping guard
  - role variance guard

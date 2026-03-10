# Project Management Capability Mapping v2

## 1. Purpose
- Standardize `project.management` block capability naming to existing runtime registry keys.
- Keep compatibility with current capability governance (`sc.capability` + `capability_registry`).

## 2. Naming Rule
- Capability key format: `<domain>.<object>.<action>`
- Use existing keys only in v2 mapping (no alias key activation in this round).

## 3. Scene/Page
- `scene_key`: `project.management`
- `page_key`: `project.management.dashboard`

## 4. Zone/Block/Capability Mapping

| zone_key | block_key | capability_key | reason |
| --- | --- | --- | --- |
| `zone.header` | `block.project.header` | `project.dashboard.open` | Header follows dashboard scene entry permission. |
| `zone.metrics` | `block.project.metrics` | `project.dashboard.open` | KPI block belongs to dashboard capability scope. |
| `zone.progress` | `block.project.progress` | `cost.progress.report` | Progress data path reuses existing progress-report capability. |
| `zone.contract` | `block.project.contract` | `contract.center.open` | Contract block follows contract-center permission gate. |
| `zone.cost` | `block.project.cost` | `cost.ledger.open` | Cost block follows cost-ledger permission gate. |
| `zone.finance` | `block.project.finance` | `finance.payment_request.list` | Finance block follows payment-request list permission gate. |
| `zone.risk` | `block.project.risk` | `project.risk.list` | Risk block follows project-risk capability scope. |

## 5. Context and Action Reference
- Route scene target:
  - `/s/project.management`
- Data intent:
  - `project.dashboard`
- Context carrier:
  - `project_id` via route/query/intent params/context (details in ops doc)

## 6. Compatibility Notes
- v2 does not create new capability keys.
- v2 keeps all keys compliant with existing regex and guard rules.
- Future alias keys (e.g. `capability.project.overview`) remain backlog items.

# Demo Data Round 1 Plan

## 1. Target Pages

Ensure readable demo data on:

- `project.management`
- `projects.ledger`
- `projects.list`
- `task.center`
- `risk.center`
- `cost.project_boq`

## 2. Data Strategy

- No large-scale noisy fake data.
- Reuse existing demo/scenario XML where possible.
- Only add minimum records required for complete demo flow.

## 3. Data Completion

1. Task data (`project.task`): minimum set for in-progress/done/blocked.
2. Contract + payment data: enable scenario files under `s10_contract_payment`.
3. BOQ data: reuse existing `s00_min_path/10_project_boq.xml`.
4. Project links: keep existing `s00_min_path/20_project_links.xml`.

## 4. Models and Files

- Models: `project.project`, `project.task`, `construction.contract`, `payment.request`, `project.boq.line`
- Files:
  - `addons/smart_construction_demo/data/base/25_project_tasks.xml` (new)
  - `addons/smart_construction_demo/data/scenario/s10_contract_payment/10_contracts.xml` (added to manifest)
  - `addons/smart_construction_demo/data/scenario/s10_contract_payment/20_payment_requests.xml` (added to manifest)

## 5. Validation Pages

- Dashboard KPI/risk blocks are not empty.
- Ledger/list pages show status/owner/key amount.
- Task center has readable task rows.
- Risk center has signals from payment-related data.
- BOQ page has readable BOQ rows.

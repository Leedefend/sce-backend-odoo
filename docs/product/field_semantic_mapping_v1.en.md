# Field Semantic Mapping v1

## 1. Scope

Display-layer product semantics for status, boolean, stage, amount, and percentage fields.

## 2. Technical -> Product Mapping

### 2.1 Status

- `draft` -> 草稿
- `open` / `active` / `in_progress` / `01_in_progress` -> 进行中
- `done` / `approved` / `paid` -> 已完成
- `pending` / `todo` / `to_do` -> 待处理
- `blocked` / `overdue` / `risk` / `high_risk` -> 风险
- `cancel` / `cancelled` / `rejected` -> 已取消/已驳回

### 2.2 Boolean

- `true` -> 是
- `false` -> 否

### 2.3 Stage

- Stage-like technical values use status mapping first.
- Chinese stage names pass through directly.

### 2.4 Amount

- `>= 1e8` -> `x.xx亿`
- `>= 1e4` -> `x.xx万`
- else -> `x.xx`

### 2.5 Percentage

- `*_percent` / `*_rate` -> `N%`

## 3. Frontend vs Backend Boundary

- Frontend (implemented this round): status/boolean localization, amount and percentage formatting.
- Backend contract (unchanged this round): technical raw values and envelope structure stay stable.

## 4. Integrated Pages (This Round)

- `project.management`
- `projects.ledger`
- `projects.list`
- `task.center`
- `risk.center`
- `cost.project_boq`

## 5. Suggested Next Types

- Risk severity fields (`risk_level` / `severity`)
- SLA/deadline fields (`deadline_status`)
- Approval state fields (`approval_state`)

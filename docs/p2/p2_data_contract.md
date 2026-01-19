# P2 Data Contract (Draft)

Scope: Define authoritative objects/fields/state constraints for P2 execution control.

## Model Mapping (technical names)
| Logical Name         | Technical Model            | Evidence |
|----------------------|----------------------------|----------|
| construction.contract| construction.contract      | `addons/smart_construction_core/models/support/contract_center.py:20` |
| settlement.line      | sc.settlement.order.line   | `addons/smart_construction_core/models/core/settlement_order.py:379` |
| payment.request      | payment.request            | `addons/smart_construction_core/models/core/payment_request.py:10` |

## Boundary (P2 scope lock)
- P2 本轮不做财务入账 / 不做审批流程重构 / 不做移动端
- 仅覆盖执行管控闭环：任务 / WBS / BOQ / 进度 / 结算单 / 付款申请 + 审计链路

## 1) project.task
### Core Fields
- id (readonly)
- name (required)
- project_id (required)
- work_id (optional, required when cost allocation enabled)
- boq_line_id (optional)
- planned_start, planned_end (optional)
- actual_start, actual_end (readonly/derived)
- progress_rate (readonly/derived)
- state (state machine)

### State Machine
- draft -> ready -> in_progress -> done

### Constraints
- If project lifecycle is paused/closed, tasks cannot move to in_progress.
- If wbs_required, work_id must be set before ready.

### Errors
- TASK_GUARD_MISSING_FIELDS
- TASK_GUARD_PROJECT_BLOCKED
- TASK_GUARD_NOT_COMPLETE
- TASK_GUARD_ROLE_REQUIRED

### Transition API Table (project.task)
| From -> To           | Method / Action                  | Guard (Error Code)            | Audit Event |
|----------------------|----------------------------------|-------------------------------|------------|
| draft -> ready       | project.task.action_prepare_task | TASK_GUARD_MISSING_FIELDS     | task_ready |
| ready -> in_progress | project.task.action_start_task   | TASK_GUARD_PROJECT_BLOCKED    | task_started |
| in_progress -> done  | project.task.action_mark_done    | TASK_GUARD_NOT_COMPLETE       | task_done |
| any -> cancel        | project.task.action_cancel_task  | TASK_GUARD_ROLE_REQUIRED      | task_cancelled |

## 2) construction.work.breakdown
### Core Fields
- id (readonly)
- name (required)
- project_id (required)
- parent_id (optional)
- code (required, unique per project)
- level (readonly/derived)
- active (bool)

### Constraints
- code uniqueness within project
- active=false nodes cannot receive new tasks

## 3) project.boq.line
### Core Fields
- id (readonly)
- project_id (required)
- code (required)
- name (required)
- amount_total (readonly/derived)
- task_id (optional)
- work_id (optional)

### Constraints
- Import creates immutable source snapshot.
- Manual edits require manager role; audit logged.

## 4) project.cost.ledger
### Core Fields
- id (readonly)
- project_id (required)
- work_id (optional)
- task_id (optional)
- amount (required)
- period_id (required)
- locked (readonly/derived)

### Constraints
- locked period blocks create/write.

## 5) construction.contract
### Core Fields
- id (readonly)
- project_id (required)
- amount_total (required)
- state (state machine)

### State Machine
- draft -> confirmed -> running -> closed

## 6) sc.settlement.order
### Core Fields
- id (readonly)
- name (required)
- project_id (required)
- contract_id (required)
- partner_id (required)
- settlement_type (required)
- date_settlement (required)
- currency_id (required)
- amount_total (readonly/derived)
- line_ids (one2many)
- payment_request_ids (one2many, readonly)
- state (state machine)

### State Machine
- draft -> submit -> approve -> done
- submit/approve/done -> cancel

### Constraints
- contract consistency with linked payment requests
- purchase order checks required for approve
- cancel blocked if linked payment requests are in approve/approved/done

### Errors
- P0_SETTLEMENT_CANCEL_BLOCKED
- SETTLEMENT_CONTRACT_MISMATCH
- SETTLEMENT_PURCHASE_MISSING
- SETTLEMENT_PURCHASE_INVALID

### Transition API Table (sc.settlement.order)
| From -> To      | Method / Action                     | Guard (Error Code)              | Audit Event |
|-----------------|-------------------------------------|---------------------------------|------------|
| draft -> submit | sc.settlement.order.action_submit   | SETTLEMENT_CONTRACT_MISMATCH / SETTLEMENT_PURCHASE_MISSING | settlement_submitted |
| submit -> approve | sc.settlement.order.action_approve | SETTLEMENT_PURCHASE_INVALID     | settlement_approved |
| approve -> done | sc.settlement.order.action_done     | (n/a)                           | settlement_done |
| any -> cancel   | sc.settlement.order.action_cancel   | P0_SETTLEMENT_CANCEL_BLOCKED    | settlement_cancelled |

## 7) sc.settlement.order.line
### Core Fields
- id (readonly)
- settlement_id (required)
- name (required)
- qty (required)
- price_unit (required)
- amount (readonly/derived)
- currency_id (readonly/derived)

### Constraints
- Line is scoped to its settlement order; contract/project context inherits from order.

## 8) payment.request
### Core Fields
- id (readonly)
- project_id (required)
- contract_id (optional, required for pay)
- settlement_id (optional)
- amount (required)
- attachments (required on submit)
- tier_state (readonly/derived)
- state (state machine)

### State Machine
- draft -> submit -> approve -> approved -> done
- submit/approve/approved -> rejected
- any -> cancel

### Constraints
- submit requires attachments and funding gate
- approve/approved/done blocked if project lifecycle terminal
- settlement must be in approve/done before submit/approve

### Errors
- P0_PROJECT_TERMINAL_BLOCKED
- P0_PAYMENT_SETTLEMENT_NOT_READY
- P0_PAYMENT_STATE_BYPASS_BLOCKED
- P0_PAYMENT_OVER_BALANCE

### Transition API Table (payment.request)
| From -> To         | Method / Action                      | Guard (Error Code)                 | Audit Event |
|--------------------|--------------------------------------|------------------------------------|------------|
| draft -> submit    | payment.request.action_submit        | P0_PAYMENT_SETTLEMENT_NOT_READY    | payment_submitted |
| submit -> approve  | payment.request.action_approve       | P0_PAYMENT_OVER_BALANCE            | payment_approve_started |
| approve -> approved| payment.request.action_set_approved  | P0_PAYMENT_STATE_BYPASS_BLOCKED    | payment_approved |
| submit -> rejected | payment.request.action_on_tier_rejected | (n/a)                           | payment_rejected |
| approved -> done   | payment.request.action_done          | P0_PAYMENT_STATE_BYPASS_BLOCKED    | payment_done |
| any -> cancel      | payment.request.action_cancel        | (n/a)                              | payment_cancelled |

## Visibility Rules
- read access by role groups per existing ACL.
- derived fields never writable by user.

Notes:
- Fields labeled “derived” must be computed server-side only.
- Errors should be stable codes to support UI guidance.

## AuditRecord v1 (schema)
Required fields:
- event_code (e.g. P2-TASK-READY / settlement_done)
- action (method/xmlid)
- model, res_id
- actor_uid, actor_login
- ts (UTC ISO8601)
- before (json, optional, diff only)
- after (json, optional, diff only)
- reason (required for override/unlock/revert)
- trace_id (request correlation id)
- company_id, project_id

Write requirements:
- MUST write audit for all execute_button transitions.
- SHOULD write audit for manual overrides.
- OPTIONAL for pure read intents.

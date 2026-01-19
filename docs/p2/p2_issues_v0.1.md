# P2 Implementation Issues (v0.1)

Each item includes scope, acceptance, concrete file path(s), required methods/guards/audit, and suggested commit message.

- [ ] **P2-TASK-READY — readiness + guarded transitions**
  - Scope: compute readiness, enforce state transitions via actions, emit audit events.
  - Acceptance: Transition API table in `docs/p2/p2_data_contract.md` enforced; no direct state write.
  - Models/paths: `addons/smart_construction_core/models/support/task_extend.py:6` (project.task extension)
  - Methods: `project.task.action_prepare_task`, `action_start_task`, `action_mark_done`, `action_cancel_task`
  - Guards: TASK_GUARD_MISSING_FIELDS, TASK_GUARD_PROJECT_BLOCKED, TASK_GUARD_NOT_COMPLETE, TASK_GUARD_ROLE_REQUIRED
  - Audit: task_ready/task_started/task_done/task_cancelled
  - Commit msg: `feat(p2-task): add readiness transitions and audit`

- [ ] **P2-WBS-LINK — WBS link enforcement**
  - Scope: require WBS linkage before cost allocation; unlink requires manager; audit link/unlink.
  - Acceptance: cost allocation blocked if missing WBS; unlink emits audit.
  - Models/paths: `addons/smart_construction_core/models/support/work_breakdown.py:5` (construction.work.breakdown)
  - Methods: `action_link_wbs_task`, `action_unlink_wbs_task`
  - Guards: WBS_GUARD_REQUIRED, WBS_GUARD_ROLE_REQUIRED
  - Audit: wbs_link_created/wbs_link_removed
  - Commit msg: `feat(p2-wbs): enforce wbs link and audit`

- [ ] **P2-BOQ-TRACE — traceability + manual override policy**
  - Scope: define override fields; BOQ sync must not overwrite manual overrides; audit sync.
  - Acceptance: override preserved; sync writes audit event.
  - Models/paths: `addons/smart_construction_core/models/core/boq.py:15` (project.boq.line)
  - Methods: `action_sync_boq_budget`
  - Guards: BOQ_GUARD_OVERRIDE_LOCK
  - Audit: boq_budget_synced
  - Commit msg: `feat(p2-boq): traceability sync with override safeguards`

- [ ] **P2-PROGRESS-ENTRY — immutable submission**
  - Scope: lock submitted entries; revert requires reason + audit.
  - Acceptance: submitted entries immutable; revert logs reason + audit.
  - Models/paths: `addons/smart_construction_core/models/core/cost_domain.py:425` (project.progress.entry)
  - Methods: `action_submit_progress`, `action_revert_progress`
  - Guards: PROGRESS_INVALID, PROGRESS_GUARD_ROLE_REQUIRED
  - Audit: progress_submitted/progress_reverted
  - Commit msg: `feat(p2-progress): lock submissions and audit revert`

- [ ] **P2-COST-LEDGER-LOCK — period lock enforcement**
  - Scope: block create/write/unlink in locked period.
  - Acceptance: locked period blocks all edits; unlock logs reason.
  - Models/paths: `addons/smart_construction_core/models/core/cost_domain.py:304` (project.cost.ledger)
  - Methods: `action_lock_period`, `action_unlock_period`
  - Guards: PERIOD_LOCKED
  - Audit: period_locked/period_unlocked
  - Commit msg: `feat(p2-ledger): enforce period lock with audit`

- [ ] **P2-CONTRACT-LINK — settlement binding rule**
  - Scope: settlement order must bind contract; line inherits contract/project context.
  - Acceptance: mismatch blocked; bind/unbind emits audit.
  - Models/paths: `addons/smart_construction_core/models/core/settlement_order.py:10` (sc.settlement.order)
  - Methods: `action_bind_settlement`, `action_unbind_settlement`
  - Guards: SETTLEMENT_CONTRACT_MISMATCH
  - Audit: contract_bound/contract_unbound
  - Commit msg: `feat(p2-contract): enforce settlement-contract binding`

- [ ] **P2-PAYMENT-REQUEST — submit/approve/done gates**
  - Scope: submit requires settlement ready + funding gate; approve/approved/done guard; audit all transitions.
  - Acceptance: guards per Data Contract; errors use existing codes; audit recorded.
  - Models/paths: `addons/smart_construction_core/models/core/payment_request.py:10` (payment.request)
  - Methods: `action_submit`, `action_approve`, `action_set_approved`, `action_done`, `action_cancel`, `action_on_tier_rejected`
  - Guards: P0_PROJECT_TERMINAL_BLOCKED, P0_PAYMENT_SETTLEMENT_NOT_READY, P0_PAYMENT_OVER_BALANCE, P0_PAYMENT_STATE_BYPASS_BLOCKED
  - Audit: payment_submitted/payment_approve_started/payment_approved/payment_done/payment_rejected/payment_cancelled
  - Commit msg: `feat(p2-payment): enforce submission guards and audit`

- [ ] **P2-AUDIT-READINESS — audit model + writer**
  - Scope: add AuditRecord v1 model + writer utility; enforce on execute_button.
  - Acceptance: all execute_button actions write audit with trace_id.
  - Models/paths: `addons/smart_construction_core/models/support/state_guard.py:1` (audit hook location TBD)
  - Methods: `audit_log.write_event(...)` (new)
  - Guards: n/a
  - Audit: event_code per capability
  - Commit msg: `feat(p2-audit): add audit log schema and writer`

- [ ] **P2-API-ENVELOPE — unify execute_button responses**
  - Scope: standardize responses to {ok,data,error}; wrap action dict in data.action.
  - Acceptance: no raw action dicts returned.
  - Paths: `addons/smart_construction_core/controllers/insight_controller.py:1`
  - Commit msg: `feat(p2-api): standardize action response envelope`

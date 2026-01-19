# P2 Capability Map (Draft)

Scope: P2 core execution control across project/task/progress/cost/contract/settlement/payment.

## Capability Entries
Format: Code | Goal | Roles | Model(s) | Action(s) | Audit Points | Acceptance

1) P2-TASK-READY
- Goal: Task execution readiness is visible and actionable.
- Roles: project_user, project_manager
- Model(s): project.task
- Action(s): action_view_tasks, execute_button:action_prepare_task
- Audit Points: readiness_check, readiness_override
- Acceptance: readiness status computed; override is logged; no write to task unless explicit action.

2) P2-WBS-LINK
- Goal: WBS nodes are linked to tasks and cost lines.
- Roles: cost_user, cost_manager
- Model(s): construction.work.breakdown, project.task, project.cost.ledger
- Action(s): action_open_wbs, execute_button:action_link_wbs_task
- Audit Points: wbs_link_created, wbs_link_removed
- Acceptance: WBS → task link must exist before cost allocation; unlink requires manager role.

3) P2-BOQ-TRACE
- Goal: BOQ lines trace to tasks and budgets.
- Roles: cost_user, cost_manager
- Model(s): project.boq.line, project.task, project.budget
- Action(s): action_open_boq_import, execute_button:action_sync_boq_budget
- Audit Points: boq_imported, boq_budget_synced
- Acceptance: BOQ import generates traceable links; sync does not overwrite manual overrides.

4) P2-PROGRESS-ENTRY
- Goal: Progress entry captured with audit trail.
- Roles: cost_user, cost_manager
- Model(s): project.progress.entry
- Action(s): action_open_progress_entries, execute_button:action_submit_progress
- Audit Points: progress_submitted, progress_reverted
- Acceptance: submissions create immutable records; revert requires manager and logs reason.

5) P2-COST-LEDGER-LOCK
- Goal: Cost ledger enforces period lock.
- Roles: cost_manager
- Model(s): project.cost.ledger, project.cost.period
- Action(s): execute_button:action_lock_period
- Audit Points: period_locked, period_unlocked
- Acceptance: locked period blocks edits; unlock logs actor + reason.

6) P2-CONTRACT-LINK
- Goal: Contracts are bound to project and settlement.
- Roles: contract_user, contract_manager
- Model(s): construction.contract, sc.settlement.order, sc.settlement.order.line
- Action(s): action_project_contract_overview, execute_button:action_bind_settlement
- Audit Points: contract_bound, contract_unbound
- Acceptance: settlement lines must reference contract via order; unbind requires manager.

7) P2-PAYMENT-REQUEST
- Goal: Payment requests follow workflow and tiers.
- Roles: finance_user, finance_manager
- Model(s): payment.request
- Action(s): execute_button:action_submit, execute_button:action_approve
- Audit Points: payment_submitted, payment_approved, payment_rejected
- Acceptance: submit enforces required attachments; tier approval required for payout.

8) P2-AUDIT-READINESS
- Goal: P2 actions are audit-ready with minimal log schema.
- Roles: system, auditor
- Model(s): sc.audit.log (new)
- Action(s): n/a (implicit)
- Audit Points: action, actor, target, before/after, reason
- Acceptance: every P2 action writes audit record with stable schema.

## Notes
- Keep codes stable; map to gate rules later.
- Use acceptance as CI gate criteria.

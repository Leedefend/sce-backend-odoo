# History Continuity Replay Contract v1

Status: READY_FOR_SERVER_REPLAY

Task: `ITER-2026-04-24-HISTORY-CONTINUITY-REPLAY-CONTRACT-001`

## Scope

Provide one one-click contract for:

- historical replay rehearsal in `sc_demo`
- bounded replay into `sc_demo`
- server-side fresh production initialization

This contract is the canonical entry. It must not be replaced by isolated
importer scripts.

## Entry Points

Rehearsal:

```bash
DB_NAME=sc_demo make history.continuity.rehearse
```

Replay:

```bash
DB_NAME=<target_db> make history.continuity.replay
```

Fresh production initialization:

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=<target_db> PROD_DANGER=1 \
  make history.production.fresh_init
```

Resume from a failed step:

```bash
DB_NAME=<target_db> HISTORY_CONTINUITY_START_AT=<step_name> make history.continuity.replay
```

Optional artifact override:

```bash
DB_NAME=<target_db> RUN_ID=<run_id> MIGRATION_ARTIFACT_ROOT=<artifact_root> make history.continuity.replay
```

Default Odoo-shell artifact root:

```bash
/tmp/history_continuity/<db>/<run_id>
```

## Included Steps

Rehearsal mode:

1. replay manifest dry-run
2. historical user asset verify
3. replay payload precheck
4. usability probe

Replay mode:

1. historical users rebuild
2. replay payload precheck
3. partner anchor replay
4. project anchor replay
5. contract counterparty partner adapter
6. contract counterparty partner replay
7. receipt counterparty partner adapter
8. receipt counterparty partner replay
9. project-member neutral carrier replay
10. contract header replay
11. contract missing partner anchors replay
12. special 12-row contract partner anchor supplement
13. special 12-row contract replay
14. contract retry-57 replay
15. contract unreached-ready replay
16. contract partner recovery
17. partner/contract direction defer recovery
18. receipt core replay
19. receipt partner targeted replay
20. receipt parent recovery
21. receipt invoice line replay
22. receipt invoice attachment replay
23. project-member attachment targeted replay
24. outflow partner targeted replay
25. outflow request replay
26. actual outflow replay
27. outflow request line replay
28. legacy attachment backfill replay
29. receipt-income partner targeted replay
30. legacy receipt income replay
31. expense-deposit partner targeted replay
32. legacy expense deposit replay
33. legacy invoice tax replay
34. legacy workflow audit replay
35. outflow request state recovery
36. outflow request approved recovery
37. outflow request done recovery and ledger fact materialization
38. project lifecycle continuity replay
39. legacy financing loan replay
40. legacy fund daily snapshot replay
41. usability probe

Supported resume step names:

- `user_rebuild`
- `replay_payload_precheck`
- `partner_l4_anchor_completed`
- `project_anchor_completed`
- `contract_counterparty_partner_adapter`
- `contract_counterparty_partner_completed`
- `receipt_counterparty_partner_adapter`
- `receipt_counterparty_partner_completed`
- `project_member_neutral_completed`
- `contract_header_completed_1332`
- `contract_missing_partner_anchors`
- `contract_12_missing_partner_anchors`
- `contract_header_special_12`
- `contract_header_retry_57`
- `contract_line_adapter`
- `contract_line_completed`
- `supplier_contract_adapter`
- `supplier_partner_targeted_adapter`
- `supplier_partner_targeted_replay`
- `supplier_contract_completed`
- `supplier_contract_line_adapter`
- `supplier_contract_line_completed`
- `contract_unreached_ready_adapter`
- `contract_unreached_ready_replay`
- `partner_master_targeted_adapter`
- `partner_master_targeted_replay`
- `contract_partner_recovery_adapter`
- `contract_partner_recovery_replay`
- `partner_master_direction_defer_adapter`
- `partner_master_direction_defer_replay`
- `contract_direction_defer_recovery_adapter`
- `contract_direction_defer_recovery_replay`
- `receipt_header_pending`
- `receipt_partner_targeted_adapter`
- `receipt_partner_targeted_replay`
- `receipt_parent_recovery_adapter`
- `receipt_parent_recovery_replay`
- `receipt_invoice_line_adapter`
- `receipt_invoice_line_replay`
- `receipt_invoice_attachment_adapter`
- `receipt_invoice_attachment_replay`
- `project_member_attachment_targeted_adapter`
- `project_member_attachment_targeted_replay`
- `outflow_partner_targeted_adapter`
- `outflow_partner_targeted_replay`
- `outflow_request_adapter`
- `outflow_request_replay`
- `actual_outflow_adapter`
- `actual_outflow_partner_targeted_adapter`
- `actual_outflow_partner_targeted_replay`
- `actual_outflow_replay`
- `outflow_request_line_adapter`
- `outflow_request_line_replay`
- `legacy_attachment_backfill_adapter`
- `legacy_attachment_backfill_replay`
- `receipt_income_partner_targeted_adapter`
- `receipt_income_partner_targeted_replay`
- `legacy_receipt_income_adapter`
- `legacy_receipt_income_replay`
- `expense_deposit_partner_targeted_adapter`
- `expense_deposit_partner_targeted_replay`
- `legacy_expense_deposit_adapter`
- `legacy_expense_deposit_replay`
- `legacy_invoice_tax_adapter`
- `legacy_invoice_tax_replay`
- `legacy_workflow_audit_adapter`
- `legacy_workflow_audit_replay`
- `payment_request_outflow_state_activation_adapter`
- `payment_request_outflow_state_activation_replay`
- `payment_request_outflow_approved_recovery_adapter`
- `payment_request_outflow_approved_recovery_replay`
- `payment_request_outflow_done_recovery_adapter`
- `payment_request_outflow_done_recovery_replay`
- `project_lifecycle_continuity_adapter`
- `project_lifecycle_continuity_replay`
- `legacy_financing_loan_adapter`
- `legacy_financing_loan_replay`
- `legacy_fund_daily_snapshot_adapter`
- `legacy_fund_daily_snapshot_replay`
- `usability_probe`

## Included Lanes

- users historical asset lane
- `partner_l4_anchor_completed`
- `project_anchor_completed`
- `contract_counterparty_partner_sc_v1`
- `receipt_counterparty_partner_sc_v1`
- `contract_counterparty_partner_completed`
- `receipt_counterparty_partner_completed`
- `project_member_neutral_completed`
- `contract_header_completed_1332`
- `contract_missing_partner_anchors`
- `contract_header_special_12`
- `contract_header_retry_57`
- `receipt_header_pending`
- `receipt_invoice_line_sc_v1`
- `receipt_invoice_attachment_sc_v1`
- `legacy_attachment_backfill_sc_v1`
- `legacy_receipt_income_sc_v1`
- `legacy_expense_deposit_sc_v1`
- `legacy_invoice_tax_sc_v1`
- `legacy_workflow_audit_sc_v1`
- `outflow_request_core`
- `actual_outflow_core`
- `outflow_request_state_recovery`
- `outflow_request_ledger_fact`
- `project_lifecycle_continuity`
- `supplier_contract`
- `supplier_contract_line`
- `outflow_request_line`
- `legacy_financing_loan_sc_v1`
- `legacy_fund_daily_snapshot_sc_v1`

## Default-Excluded / Opt-In Lanes

- `contract_partner_source_12_anchor_design`
- `payment_settlement_accounting`
- only if future business promotion needs them:
  - `payment_settlement_accounting`

To isolate core headers only and skip detail fact lanes, set:

```bash
HISTORY_CONTINUITY_INCLUDE_DETAIL_FACTS=0
```

`HISTORY_CONTINUITY_INCLUDE_BLOCKED_GROUP_B` is deprecated.

## Guardrails

- dev/test by default
- production requires `history.production.fresh_init`, `PROD_DANGER=1`, and
  `HISTORY_CONTINUITY_ALLOW_PROD=1` inside the production entry script
- DB allowlist:
  - `sc_migration_fresh`
  - `sc_demo`
  - production entry defaults the allowlist to the explicit `DB_NAME`
- artifact root must be isolated per run
- `project_member_neutral_completed` remains carrier-only
- receipt replay is contract-anchored:
  - `type/project/partner` follow the resolved contract first
  - runtime ids are fallback only
- no settlement/account.move side effects are allowed
- ledger facts are allowed only for recovered historical done-state outflow
  requests and must keep migration evidence

## Acceptance

Rehearsal acceptance:

- one-click rehearse command exits successfully
- manifest dry-run passes
- payload precheck completes
- usability probe completes

Replay acceptance:

- only allowed lanes execute
- high-risk line-level lanes remain untouched unless explicitly enabled
- usability probe produces runtime/carrier evidence
- historical facts are visible even when old-system data does not satisfy new
  workflow rules
- new business smoke is not globally blocked by historical gaps

## Current Validation

- `DB_NAME=sc_demo make history.continuity.rehearse`: `PASS`
- `FRESH_DB_REPLAY_RUNNER_DRY_RUN`: `PASS`
- `FRESH_DB_REPLAY_PAYLOAD_PRECHECK`: `PASS`
- `HISTORY_CONTINUITY_USABILITY_PROBE`: `PASS`
- `zero_critical_counts = 0`

## Server Use

Server deployment should call the same Make target:

```bash
DB_NAME=<server_db> make history.continuity.replay
```

Fresh production deployment should call:

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=<server_db> PROD_DANGER=1 \
  make history.production.fresh_init
```

No ad-hoc server-only importer should be introduced.

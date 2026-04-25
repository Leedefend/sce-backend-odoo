# History Continuity Replay Contract v1

Status: READY_FOR_SERVER_REPLAY

Task: `ITER-2026-04-24-HISTORY-CONTINUITY-REPLAY-CONTRACT-001`

## Scope

Provide one one-click contract for:

- historical replay rehearsal in `sc_demo`
- bounded replay into `sc_demo`
- future server-side one-click execution

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
15. receipt core replay
16. receipt partner targeted replay
17. receipt parent recovery
18. receipt invoice line replay
19. receipt invoice attachment replay
20. project-member attachment targeted replay
21. legacy attachment backfill replay
22. receipt-income partner targeted replay
23. legacy receipt income replay
24. expense-deposit partner targeted replay
25. legacy expense deposit replay
26. legacy invoice tax replay
27. legacy workflow audit replay
28. legacy financing loan replay
29. legacy fund daily snapshot replay
30. usability probe

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
- `legacy_financing_loan_sc_v1`
- `legacy_fund_daily_snapshot_sc_v1`

## Default-Excluded / Opt-In Lanes

- `contract_partner_source_12_anchor_design`
- `payment_settlement_accounting`
- only if future business promotion needs them:
  - `payment_settlement_accounting`

To force blocked Group B lanes into the one-click path, set:

```bash
HISTORY_CONTINUITY_INCLUDE_BLOCKED_GROUP_B=1
```

## Guardrails

- dev/test only
- DB allowlist:
  - `sc_migration_fresh`
  - `sc_demo`
- artifact root must be isolated per run
- `project_member_neutral_completed` remains carrier-only
- receipt replay is contract-anchored:
  - `type/project/partner` follow the resolved contract first
  - runtime ids are fallback only
- no ledger/settlement/account.move side effects are allowed

## Acceptance

Rehearsal acceptance:

- one-click rehearse command exits successfully
- manifest dry-run passes
- payload precheck completes
- usability probe completes

Replay acceptance:

- only allowed lanes execute
- excluded lanes remain untouched
- usability probe produces runtime/carrier evidence

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

No separate server-only replay script should be introduced.

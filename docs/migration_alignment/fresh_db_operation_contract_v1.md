# Fresh DB Replay Operation Contract v1

Status: READY_FOR_APPROVAL

Task: `ITER-2026-04-23-FRESH-DB-REPLAY-OP-CONTRACT-001`

## Scope

Provide one auditable operation contract for replaying customer legacy business
data on a fresh database. This document does not execute any database command.

## Target Database

- database: `sc_migration_fresh`
- environment: `dev/test only`
- demo policy: `WITHOUT_DEMO=--without-demo=all`

## Destructive Boundary

The following step recreates the target database and is destructive for that
database:

```bash
DB=sc_migration_fresh WITHOUT_DEMO=--without-demo=all make db.reset
```

Do not run this command without explicit task approval for the current batch.

## Approved Replay Chain (After Reset)

1. Install required business modules without demo:
```bash
DB=sc_migration_fresh MODULE=smart_construction_custom WITHOUT_DEMO=--without-demo=all make mod.install
```
2. Run replay payload precheck:
```bash
DB=sc_migration_fresh make odoo.shell.exec < scripts/migration/fresh_db_replay_payload_precheck.py
```
3. Execute replay writes in dependency order:
```bash
DB=sc_migration_fresh make odoo.shell.exec < scripts/migration/fresh_db_partner_l4_replay_write.py
DB=sc_migration_fresh make odoo.shell.exec < scripts/migration/fresh_db_project_anchor_replay_write.py
DB=sc_migration_fresh make odoo.shell.exec < scripts/migration/fresh_db_project_member_neutral_replay_write.py
DB=sc_migration_fresh make odoo.shell.exec < scripts/migration/fresh_db_contract_partner_12_anchor_replay_recovery_write.py
DB=sc_migration_fresh make odoo.shell.exec < scripts/migration/fresh_db_contract_57_retry_write.py
DB=sc_migration_fresh make odoo.shell.exec < scripts/migration/fresh_db_contract_missing_partner_anchor_write.py
DB=sc_migration_fresh make odoo.shell.exec < scripts/migration/fresh_db_contract_remaining_write.py
DB=sc_migration_fresh make fresh_db.construction_contract.income_count_alignment.write
DB=sc_migration_fresh make fresh_db.construction_contract.income_count.probe
DB=sc_migration_fresh make fresh_db.construction_contract.visible_trace.write
DB=sc_migration_fresh make fresh_db.construction_contract.attachment.write
DB=sc_migration_fresh make fresh_db.construction_contract.attachment.probe
DB=sc_migration_fresh make odoo.shell.exec < scripts/migration/fresh_db_receipt_core_write.py
```
4. Refresh construction contract manifest lanes and validate runner dry-run:
```bash
DB=sc_migration_fresh make fresh_db.construction_contract.replay_manifest.refresh
python3 scripts/migration/fresh_db_replay_runner_dry_run.py
```

## Guardrails

- Always execute through Makefile for DB lifecycle and shell entry.
- Keep `default_run=false` in replay manifest until explicit batch approval.
- Exclude high-risk lane (`payment/settlement/accounting`) from this contract.
- `fresh_db.construction_contract.income_count_alignment.write` depends on
  `tmp/raw/contract/contract.csv` mounted read-only at `/mnt/tmp/raw/contract/contract.csv`.
  Its legacy-visible filter is `DEL<>1 AND DJZT IN ('2','1','') AND HTBT<>'' AND FBF<>''`,
  matching the old system `施工合同` visible count of `1532`.
- The user-visible `合同金额` column uses `visible_contract_amount`: legacy rows prefer the old
  `T_ProjectContract_Out` contract amount and new rows fall back to the platform line amount.
- The platform split amount remains available after the user columns as `平台合同金额`, with
  `原系统合同金额` and `口径差额` retained for reconciliation.
- Visible invoices and receipts are replayed from the explicit user columns `累计开票` and
  `累计收款`. `未收款` is retained as the user-visible balance; if it does not reconcile to
  `合同金额 - 累计收款`, the replay records the balance reconciliation delta instead of inventing
  receipt facts.
- Visible approval text is replayed as `sc.contract.event(event_type=legacy_approval)`.
  The visible-surface filename matcher can be enabled only as a fallback; by default it clears
  old visible-surface attachment artifacts and leaves attachment creation to the full-data join.
- Full construction contract attachment replay uses the deterministic join
  `T_ProjectContract_Out.f_FJ = legacy_file_index.bill_id`. The Excel filename matcher is only
  a visible-surface fallback and must not be used as the full-data attachment contract.

## Acceptance

- `artifacts/migration/fresh_db_replay_runner_dry_run_result_v1.json` is `PASS`.
- `artifacts/migration/fresh_db_construction_contract_replay_manifest_refresh_result_v1.json`
  reports `status=PASS`, `refreshed_lanes=5`, and `default_run_lanes=0`.
- `artifacts/migration/fresh_db_construction_contract_income_count_probe_result_v1.json` is `PASS`
  and reports `income_action_visible_rows=1532`, `user_visible_contract_amount_sum=3212021996.74`,
  `amount_difference_event_count=18`, and `positive_amount_without_line_count=0`.
- `artifacts/migration/fresh_db_construction_contract_visible_surface_write_result_v1.json`
  reports `visible_surface_mismatch_count=0` for the user acceptance Excel surface.
- `artifacts/migration/fresh_db_construction_contract_visible_business_fact_write_result_v1.json`
  reports `status=PASS` for invoice and receipt facts sourced from explicit visible columns.
- `artifacts/migration/fresh_db_construction_contract_visible_trace_write_result_v1.json`
  reports `status=PASS` and approval event counts.
- `artifacts/migration/fresh_db_construction_contract_attachment_write_result_v1.json`
  reports full visible-contract attachment coverage through the `f_FJ -> bill_id` join.
- `artifacts/migration/fresh_db_construction_contract_attachment_probe_result_v1.json` is `PASS`
  and reports `target_contract_rows=1532`, `full_attachment_count=3728`,
  `visible_surface_attachment_count=0`, `approval_event_count=20`, and `db_writes=0`.
- No command in this contract implies automatic execution.
- Any new replay batch must reference this contract and declare command scope.

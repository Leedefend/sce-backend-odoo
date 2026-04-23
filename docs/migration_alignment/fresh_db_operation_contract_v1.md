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
DB=sc_migration_fresh make odoo.shell.exec < scripts/migration/fresh_db_receipt_core_write.py
```
4. Refresh manifest and validate runner dry-run:
```bash
python3 scripts/migration/fresh_db_replay_manifest_execution_refresh.py
python3 scripts/migration/fresh_db_replay_runner_dry_run.py
```

## Guardrails

- Always execute through Makefile for DB lifecycle and shell entry.
- Keep `default_run=false` in replay manifest until explicit batch approval.
- Exclude high-risk lane (`payment/settlement/accounting`) from this contract.

## Acceptance

- `artifacts/migration/fresh_db_replay_runner_dry_run_result_v1.json` is `PASS`.
- No command in this contract implies automatic execution.
- Any new replay batch must reference this contract and declare command scope.

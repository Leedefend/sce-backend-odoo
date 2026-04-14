# ITER-2026-04-13-1849 Report

Task: Res partner legacy identity and safe field slice v1

Status: `PASS`

Decision: `partner creation remains NO-GO`

## Architecture

- Layer Target: `Business Fact Model Field Alignment`
- Module: `res.partner legacy identity`
- Module Ownership: `addons/smart_construction_core/models/support + docs/migration_alignment + agent_ops`
- Kernel or Scenario: `scenario`
- Reason: 为完整新库可重复重建补齐 partner legacy identity，支持后续幂等与精确回滚。

## Changes

Added `res.partner` fields:

- `legacy_partner_id`
- `legacy_partner_source`
- `legacy_partner_name`
- `legacy_credit_code`
- `legacy_tax_no`
- `legacy_deleted_flag`
- `legacy_source_evidence`

## Non-Changes

- no partner creation
- no contract import
- no partner_id backfill
- no supplier merge
- no menu, ACL, manifest, frontend changes

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-13-1849.yaml`: PASS
- `python3 -m py_compile addons/smart_construction_core/models/support/partner_legacy.py`: PASS
- `make verify.native.business_fact.static`: PASS
- `CODEX_NEED_UPGRADE=1 CODEX_MODULES=smart_construction_core DB_NAME=sc_demo MODULE=smart_construction_core make mod.upgrade`: PASS
- `make restart`: PASS
- `DB_NAME=sc_demo make odoo.shell.exec`: PASS
- `DB_NAME=sc_demo make odoo.shell.exec` after restart: PASS
- `python3 -m json.tool agent_ops/state/task_results/ITER-2026-04-13-1849.json`: pending

## Next Step

Open a no-DB partner rebuild importer promotion batch before any partner write. Real partner creation remains blocked.

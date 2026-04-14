# ITER-2026-04-13-1844 Report

Task: Legacy DB partner and contract counterparty fact probe v1

Status: `PASS_WITH_IMPORT_BLOCKED`

Decision: `partner and contract import remain NO-GO`

## Architecture

- Layer Target: `Legacy Partner Business Fact Probe`
- Module: `res.partner and construction.contract migration fact support`
- Module Ownership: `scripts/migration + artifacts/migration + docs/migration_alignment + agent_ops`
- Kernel or Scenario: `scenario`
- Reason: 通过 LegacyDb 只读业务引用关系，还原 partner 主源和合同相对方强证据路径，避免继续依赖名称猜测。

## Probe Result

旧库只读探针：`PASS`

主源判断：

- company rows: 7864
- supplier rows: 3041
- company credit-code rows: 3964
- supplier credit-code rows: 0
- supplier bank-account rows: 2521

业务引用：

- `C_ZFSQGL.f_GYSID -> company`: 13478
- `C_ZFSQGL.f_GYSID -> supplier`: 7148
- `C_JFHKLR.WLDWID -> company`: 7084
- `C_JFHKLR.WLDWID -> supplier`: 127

合同相对方：

- `FBF` text rows: 1628
- `FBF` company matched rows: 1533
- `FBF` company single rows: 908
- `CBF` text rows: 1600
- `CBF` company matched rows: 1581
- `CBF` company ambiguous rows: 1554

回款反推：

- linked contracts: 676
- linked repayment rows: 1857
- single-counterparty contracts: 628
- multi-counterparty contracts: 48

## Decision

`T_Base_CooperatCompany` is the primary partner source. `T_Base_SupplierInfo` is a supplemental source. The next useful batch is strong-evidence contract counterparty candidate generation using `C_JFHKLR.SGHTID` and `WLDWID`.

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-13-1844.yaml`: PASS
- `python3 -m py_compile scripts/migration/partner_legacy_db_fact_probe.py`: PASS
- `python3 scripts/migration/partner_legacy_db_fact_probe.py`: PASS
- `python3 -m json.tool artifacts/migration/partner_import_decision_support_v1.json`: PASS
- `python3 -m json.tool agent_ops/state/task_results/ITER-2026-04-13-1844.json`: PASS
- `make verify.native.business_fact.static`: PASS

## Next Step

Generate the 628-contract strong-evidence candidate table. Do not create partners or contracts yet.

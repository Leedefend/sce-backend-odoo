# ITER-2026-04-13-1838 Report

Task: 合同数据导入启动盘点专项 v1

Status: `PASS`

Decision: `NO-GO for direct import`

Next state: `CONTRACT_MAPPING_DRY_RUN_REQUIRED`

## Architecture

- Layer Target: `Migration Source Baseline`
- Module: `construction.contract migration readiness`
- Module Ownership: `docs/migration_alignment + artifacts/migration + agent_ops`
- Kernel or Scenario: `scenario`
- Reason: 按项目导入同样的受控路径启动合同数据迁移，但第一步只做旧导出数据与现有合同模型的只读基线盘点。

## Source Result

| Item | Result |
|---|---:|
| Source file | `tmp/raw/contract/contract.csv` |
| Rows | 1694 |
| Fields | 146 |
| Legacy contract id `Id` populated | 1694 |
| Legacy project id `XMID` populated | 1694 |
| `XMID` rows matching raw project export | 1606 |
| `XMID` matches known written project skeleton IDs | 121 |
| Existing `construction.contract` in `sc_demo` | 71 |
| Existing `construction.contract.line` in `sc_demo` | 83 |

## Key Findings

- Current target model is `construction.contract`.
- Current line model is `construction.contract.line`.
- Required write blockers include `subject`, `type`, `project_id`, `partner_id`, `tax_id`, `company_id`, and `currency_id`.
- Old file has strong identity `Id`, but target model currently has no documented legacy contract identity field in this batch.
- Old project relation `XMID` must map to `project.project.legacy_project_id`; only 121 rows currently match known written project skeleton IDs from artifacts.
- Partner relation requires text matching from `FBF` / `CBF`.
- Tax and amount semantics are not safe for direct import because target amounts are computed from contract lines and tax rules.
- `DEL=1` appears on 65 rows and must be filtered or explicitly handled before any write.

## Deliverables

- `agent_ops/tasks/ITER-2026-04-13-1838.yaml`
- `artifacts/migration/contract_source_profile_v1.json`
- `docs/migration_alignment/contract_migration_source_inventory_v1.md`
- `docs/migration_alignment/contract_legacy_field_baseline_v1.md`
- `docs/migration_alignment/contract_model_current_inventory_v1.md`
- `docs/migration_alignment/contract_import_initial_gate_v1.md`
- `agent_ops/reports/2026-04-13/report.ITER-2026-04-13-1838.md`
- `agent_ops/state/task_results/ITER-2026-04-13-1838.json`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-13-1838.yaml`: PASS
- `python3 -m json.tool artifacts/migration/contract_source_profile_v1.json`: PASS
- `python3 -m json.tool agent_ops/state/task_results/ITER-2026-04-13-1838.json`: PASS
- `make verify.native.business_fact.static`: PASS

## Risk

No database write was performed.

No contract model, view, menu, ACL, frontend, importer, payment, settlement, or accounting file was changed.

Direct contract import remains blocked until mapping dry-run and safe import slice are complete.

## Next Step

Open `ITER-2026-04-13-1839 合同数据映射干跑与安全切片专项 v1`.

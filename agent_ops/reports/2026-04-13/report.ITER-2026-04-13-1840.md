# ITER-2026-04-13-1840 Report

Task: 合同模型字段对齐与 legacy identity 专项 v1

Status: `PASS`

Decision: `contract write remains NO-GO`

## Architecture

- Layer Target: `Business Fact Model Field Alignment`
- Module: `construction.contract legacy identity`
- Module Ownership: `addons/smart_construction_core/models/support + addons/smart_construction_core/views/core + docs/migration_alignment + agent_ops`
- Kernel or Scenario: `scenario`
- Reason: 解决 1839 识别出的首个写入阻塞项：目标合同模型缺少旧系统合同身份字段，无法精确 rollback/upsert。

## Changes

Model fields added to `construction.contract`:

- `legacy_contract_id`
- `legacy_project_id`
- `legacy_document_no`
- `legacy_contract_no`
- `legacy_external_contract_no`
- `legacy_status`
- `legacy_deleted_flag`
- `legacy_counterparty_text`

View change:

- contract form adds read-only `legacy_contract_id`
- contract form adds read-only `迁移对照` notebook page

## Explicit Non-Changes

- no data import
- no importer script
- no partner creation
- no tax logic change
- no amount logic change
- no payment or settlement logic change
- no workflow state change
- no ACL/security/menu/frontend change

## Runtime Validation

`sc_demo` validation:

- missing model fields: none
- missing `ir.model.fields`: none
- missing form view refs: none
- existing contract count: 71
- non-empty `legacy_contract_id` count: 0

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-13-1840.yaml`: PASS
- `python3 -m py_compile addons/smart_construction_core/models/support/contract_center.py`: PASS
- `make verify.native.business_fact.static`: PASS
- `CODEX_NEED_UPGRADE=1 CODEX_MODULES=smart_construction_core DB_NAME=sc_demo MODULE=smart_construction_core make mod.upgrade`: PASS
- `make restart`: PASS
- `DB_NAME=sc_demo make odoo.shell.exec`: PASS
- `python3 -m json.tool agent_ops/state/task_results/ITER-2026-04-13-1840.json`: PASS

## Remaining Blockers

Contract write is still blocked by:

- partner matching
- tax/default tax policy
- computed amount and line policy
- project coverage limit
- workflow state replay policy
- `DEL=1` filter policy

## Next Step

Open `ITER-2026-04-13-1841 合同 partner 主数据匹配与安全候选重算专项 v1`.

# ITER-2026-04-07-1287 Report

## Summary of change
- 完成用户指定 6 条历史项目公司归属（统一归属 `company_id=80`）：
  - id=28 `SCENE-CONTRACT-9c7c4042`
  - id=29 `SCENE-CONTRACT-5720ce48`
  - id=30 `SCENE-CONTRACT-c0a4f1bc`
  - id=31 `SCENE-CONTRACT-d02a6c6b`
  - id=32 `SCENE-CONTRACT-50065a8a`
  - id=33 `SCENE-CONTRACT-f3ac1651`
- 审计时发现额外 3 条新增空公司项目（运行态临时数据）并按既定优先级补齐（项目经理→负责人→创建人）：
  - id=114 `ITER1279_MATRIX_1775547784` -> company 84（项目经理归属）
  - id=117 `P13B-EXEC-99b4f1db` -> company 80
  - id=120 `P13B-EXEC-73aa6c3c` -> company 80
- 升级 `scripts/verify/native_business_fact_budget_cost_member_visibility_verify.py`：
  - 将 `budget.project_without_company`、`cost.project_without_company` 从观测项升级为硬阻塞项。
- 数据同步修复：
  - `project_budget.company_id` 同步 2 条
  - `project_cost_ledger.company_id` 同步 2 条

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1287.yaml`
- PASS: 项目公司空值审计 `audit.project_company_null=0`
- PASS: budget/cost `project_without_company` 审计 `=0/0`
- PASS: `DB_NAME=sc_prod_sim E2E_BASE_URL=http://localhost:18069 ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo python3 scripts/verify/native_business_fact_budget_cost_member_visibility_verify.py`
- PASS: `ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo ROLE_PM_LOGIN=xiaohuijiu ROLE_PM_PASSWORD=demo ROLE_FINANCE_LOGIN=shuiwujingbanren ROLE_FINANCE_PASSWORD=demo ROLE_EXECUTIVE_LOGIN=wennan ROLE_EXECUTIVE_PASSWORD=demo E2E_BASE_URL=http://localhost:18069 make verify.native.business_fact.stage_gate DB_NAME=sc_prod_sim`

## Risk analysis
- 本轮仅调整数据与 verify 脚本，无财务语义、ACL CSV、manifest 变更。
- 严格模式启用后，预算/成本锚点缺口会直接阻断后续验收，符合“全量严格模式”目标。

## Rollback suggestion
- `git restore scripts/verify/native_business_fact_budget_cost_member_visibility_verify.py`
- 若需回滚数据修复：恢复 `sc_prod_sim` 本轮执行前数据库快照。

## Next iteration suggestion
- 启动下一轮“全新数据库防再生验证”专项：fresh install + seed + stage gate，确认 `project/company` 与 budget/cost 锚点不会在新库重生缺口。

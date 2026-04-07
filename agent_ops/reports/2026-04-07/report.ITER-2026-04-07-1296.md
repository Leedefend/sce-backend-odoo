# ITER-2026-04-07-1296 Report

## Summary of change
- 启动“原生业务办理闭环验收 v1”专项，聚焦项目/任务/预算/成本最小可办理能力。
- 新增验证脚本：`scripts/verify/native_business_fact_native_operability_closure_verify.py`。
- 不改 ACL/rule/前端，不扩 payment/settlement 深层审批链。

## Batch A: 项目办理闭环
- owner 创建项目成功。
- owner 维护关键岗位字段（项目经理/技术/商务/成本/财务）成功。
- owner 维护项目成员载体（`project.responsibility`）成功。
- outsider 对项目默认不可见（`outsider_project_count=0`）。

## Batch B: 任务办理闭环
- PM 创建任务成功。
- PM 编辑任务成功。
- PM 推进关键状态成功（`stage_id` 可写）。
- outsider 对任务默认不可见且不可写（`outsider_task_count=0`，写操作拒绝）。

## Batch C: 预算/成本办理闭环
- PM 以“授权成员”身份创建预算/成本成功（脚本中显式授权 `group_sc_cap_cost_manager` 作为最小授权成员条件）。
- `project.budget` / `project.cost.ledger` 的 `project_id/company_id` 自动继承校验通过。
- outsider 对预算/成本默认不可见且不可写（`outsider_budget_count=0`、`outsider_cost_count=0`）。

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1296.yaml`
- PASS: `DB_NAME=sc_prod_fresh_1292_b E2E_BASE_URL=http://localhost:18079 ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo ROLE_PM_LOGIN=xiaohuijiu ROLE_PM_PASSWORD=demo ROLE_OUTSIDER_PASSWORD=demo python3 scripts/verify/native_business_fact_native_operability_closure_verify.py`
  - 关键输出：`pm_cost_authorized=1 project_id=17 member_id=8 task_id=32 budget_id=9 cost_id=10 outsider_project_count=0 outsider_task_count=0 outsider_budget_count=0 outsider_cost_count=0`

## Risk analysis
- 结论：`PASS`
- 风险状态：本轮范围内无新增阻塞；预算/成本创建依赖“授权成员”条件已显式体现在验收脚本中。

## Rollback suggestion
- `git restore scripts/verify/native_business_fact_native_operability_closure_verify.py`
- `git restore docs/ops/project_org_isolation_acceptance_v1.md`

## Next suggestion
- 若进入下一轮，可在不扩权限专题前提下，补“payment/settlement 最小办理（非审批链）”独立验收脚本。

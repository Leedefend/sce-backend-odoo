# ITER-2026-04-01-506

## Summary
- 选定下一条代表性非首批流程家族为 `tender / 招投标`
- 结论为 `PASS_WITH_RISK`
- 发现新的真实 residual：`finance` 在 runtime 上可见 `action_tender_bid`，但对 `tender.bid` 不具备 `read` 权限

## Scope
- 本批为 audit-first 分类批次
- 代表入口：
  - [tender_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/tender_views.xml#L165)
    的 `action_tender_bid`
- 角色样本：
  - `PM / hujun`
  - `finance / jiangyijiao`
  - `executive / wutao`
  - `business_admin / admin`

## Repository facts
- [tender_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/tender_views.xml#L165)
  将 `action_tender_bid` 配到了 `group_sc_cap_project_read`
- [ir.model.access.csv](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/ir.model.access.csv)
  对 `tender.bid` 及其子表 ACL 仅授予：
  - `group_sc_cap_project_user`
  - `group_sc_cap_project_manager`
- 仓库里不存在给 `project_read` 的 `tender.bid` 读取 ACL

## Runtime facts
- `action_tender_bid` 对四个样本角色都可成功读取，`res_model = tender.bid`
- `tender.bid` 模型权限在当前 `sc_odoo` runtime 上表现为：
  - `PM / executive / business_admin`：`read/write/create/unlink = True`
  - `finance`：`read/write/create/unlink = False`
- 因而当前 runtime 呈现的是：
  - `finance` action 可见
  - 但 follow-through 到模型层时没有最基本的 `read`

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-506.yaml` → `PASS`
- repository audit → `PASS`
- runtime audit on `sc_odoo` → `PASS_WITH_RISK`

## Conclusion
- `tender / 招投标` 目前不能作为 clean representative family
- 问题不是样本不足，而是明确的 action-to-model boundary mismatch：
  - action 在 `project_read`
  - 模型 ACL 不含 `project_read`
- 这属于新的真实 runtime residual

## Risk
- 结果：`PASS_WITH_RISK`
- 风险点：
  - 如果用户通过入口进入 `tender`，会在模型层直接撞权限
  - 不能继续把 `tender` 家族视为已收口
  - 下一步必须新开窄治理/实现批次，对齐 `action_tender_bid` 与 `tender.bid` 的边界语义

## Rollback
- 本批为审计批次，无业务代码需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-04-01-506.yaml`
  - `git restore agent_ops/reports/2026-04-01/report.ITER-2026-04-01-506.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-01-506.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 不能继续自动扩面
- 需要新开一张窄批次，只决定并收口以下二选一：
  - 收窄 `action_tender_bid`，不再给 `project_read`
  - 或补 `tender.bid` 的受控 `read` 语义给 `project_read`

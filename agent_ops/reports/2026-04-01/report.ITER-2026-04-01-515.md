# ITER-2026-04-01-515

## Summary
- 执行了 `workflow` 可见性假阳性诊断批次
- 结论为 `PASS`
- `workflow` 当前不是 delivered-role 用户面 residual，而是 `config_admin` 平台面；下一条真正值得继续审计的候选家族已收敛为 `business evidence`

## Scope
- 本批为 audit-only diagnosis
- 未修改任何实现、ACL 或 manifest

## Diagnosis facts
- `workflow` 菜单在当前 `sc_odoo` runtime 上对 delivered roles 的真实可见性为：
  - `PM / hujun`：`menu_sc_workflow_root = False`
  - `finance / jiangyijiao`：`menu_sc_workflow_root = False`
  - `executive / wutao`：`menu_sc_workflow_root = True`
  - `business_admin / admin`：`menu_sc_workflow_root = True`
- [action_groups_patch.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/action_groups_patch.xml)
  中 `action_sc_workflow_*` 的 materialized groups 仍收敛到 `group_sc_cap_config_admin`
- 这说明 `514` 中看到的 `PM / finance` 可读 workflow action 记录，并不等于用户面实际拿到 workflow 入口

## Candidate isolation
- `workflow` 应从当前“客户交付 secondary family”候选集中剥离，归入 `config_admin` 平台治理面
- 下一条更适合作为真实 secondary-flow 候选的家族是：
  - `business evidence`
- 其原因是：
  - [evidence_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/evidence_views.xml)
    提供了独立 canonical action
  - `PM / finance` 对 `sc.business.evidence` 是只读
  - `executive / business_admin` 持有更高权限
  - 这条家族比 `workflow` 更符合客户交付侧的读面/查询面审计逻辑

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-515.yaml` → `PASS`
- runtime diagnosis on `sc_odoo` → `PASS`

## Conclusion
- `workflow` 在这条主线下不应再被当成用户面 residual 继续追
- `514` 的风险点可以收束为 direct action-read 假阳性，不需要开 workflow 权限修复批次
- 下一步应直接转去 `business evidence` 家族的正式分类

## Risk
- 结果：`PASS`
- 剩余风险：
  - 这批只是把错误候选剥离掉，不等于新的 family 已经收口
  - 仍需新开一张正式批次，对 `business evidence` 做 repository/runtime 分类

## Rollback
- 本批为诊断批次，无业务代码需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-04-01-515.yaml`
  - `git restore agent_ops/reports/2026-04-01/report.ITER-2026-04-01-515.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-01-515.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 继续自动推进
- 新开 `business evidence` 家族分类批次

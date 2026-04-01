# ITER-2026-04-01-516

## Summary
- 选定并审计了 `business evidence` 家族
- 结论为 `PASS`
- 当前 evidence 家族可以作为新的 clean representative non-first-batch family

## Scope
- 本批为 audit-first classification
- 代表入口：
  - [evidence_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/evidence_views.xml)
    的 `action_sc_business_evidence`
- 角色样本：
  - `PM / hujun`
  - `finance / jiangyijiao`
  - `executive / wutao`
  - `business_admin / admin`

## Repository facts
- [evidence_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/evidence_views.xml)
  定义了标准 `tree,form` canonical action，目标模型为 `sc.business.evidence`
- 视图本身已固定为：
  - `create = false`
  - `edit = false`
  - `delete = false`
- [ir.model.access.csv](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/ir.model.access.csv)
  对 `sc.business.evidence` 的 ACL 梯度为：
  - `project_read / cost_read / finance_read`：只读
  - `config_admin`：可写
- [business_evidence.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/support/business_evidence.py)
  还进一步把模型定义为 immutable：
  - 非 `allow_evidence_mutation` 上下文下，`create/write/unlink` 都会抛 `UserError`

## Runtime facts
- `action_sc_business_evidence` 在四个样本角色下都可正常读取，`res_model = sc.business.evidence`
- `sc.business.evidence` 在当前 `sc_odoo` runtime 上表现为：
  - `PM / finance`：`read = True`, `create/write/unlink = False`
  - `executive / business_admin`：ACL 层为 `read/create/write/unlink = True`
- 但对 `executive / business_admin`，runtime 实际创建/修改仍会被模型的 immutable 规则拦住：
  - `create` → `UserError`
  - `write` → `UserError`

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-516.yaml` → `PASS`
- repository audit → `PASS`
- runtime audit on `sc_odoo` → `PASS`

## Conclusion
- `business evidence` 家族当前可以并入 clean representative non-first-batch family 集合
- 它的真实语义是：
  - delivered roles 拿到只读证据查询面
  - 即便高权限角色在 ACL 层有更宽权限，模型仍通过 immutable 规则保持审计面只读
- 这条家族没有发现新的 action-to-model 或 execution residual

## Risk
- 结果：`PASS`
- 剩余风险：
  - 本批只审计 canonical evidence action 与 immutable 语义
  - evidence 生产链、风险引擎、例外处理不在本批范围内；当前没有新的阻断 residual

## Rollback
- 本批为审计批次，无业务代码需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-04-01-516.yaml`
  - `git restore agent_ops/reports/2026-04-01/report.ITER-2026-04-01-516.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-01-516.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 继续自动推进
- 新开下一张低风险筛选批次，继续选择尚未覆盖的非首批 secondary family

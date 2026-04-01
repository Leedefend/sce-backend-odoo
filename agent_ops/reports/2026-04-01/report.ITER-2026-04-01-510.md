# ITER-2026-04-01-510

## Summary
- 选定下一条尚未覆盖的代表性非首批流程家族为 `合同管理 / 收入合同 / 支出合同`
- 结论为 `PASS`
- 当前 `contract` 家族的菜单、canonical action 与模型权限边界可归类为 clean family

## Scope
- 本批为 audit-first 分类批次
- 代表入口：
  - [contract_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/contract_views.xml)
    的 `action_construction_contract_income`
  - [contract_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/contract_views.xml)
    的 `action_construction_contract_expense`
- 角色样本：
  - `PM / hujun`
  - `finance / jiangyijiao`
  - `executive / wutao`
  - `business_admin / admin`

## Repository facts
- [contract_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/contract_views.xml)
  定义的 canonical action 都指向 `construction.contract`
- [ir.model.access.csv](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/ir.model.access.csv)
  对 `construction.contract` 的 ACL 是清晰梯度：
  - `contract_read`：`read = 1`, `write/create/unlink = 0`
  - `contract_user`：`read/write/create = 1`, `unlink = 0`
  - `contract_manager`：`read/write/create/unlink = 1`
  - `finance_read / finance_user / finance_manager`：只读
- [menu.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/menu.xml)
  的合同中心菜单与收入/支出合同子菜单在仓库层保持一致的合同域入口语义

## Runtime facts
- `action_construction_contract_income` 与 `action_construction_contract_expense`
  在四个样本角色下都可成功读取，`res_model = construction.contract`
- `construction.contract` 模型权限在当前 `sc_odoo` runtime 上表现为：
  - `PM / executive / business_admin`：`read/write/create/unlink = True`
  - `finance`：仅 `read = True`，`write/create/unlink = False`
- 合同中心菜单及收入/支出合同子菜单在四个样本角色下都能正常可见
- 本批未发现 action、menu 与模型 ACL 之间的 runtime residual

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-510.yaml` → `PASS`
- repository audit → `PASS`
- runtime audit on `sc_odoo` → `PASS`

## Conclusion
- `合同管理 / 收入合同 / 支出合同` 当前可以作为新的 clean representative non-first-batch family
- 至此已闭环的代表家族继续扩展为：
  - `material plan / 待我审批（物资计划）`
  - `BOQ import / task-from-BOQ / execution-structure / progress-entry`
  - `project document / 工程资料`
  - `tender / 招投标`
  - `contract / 收入合同 / 支出合同`

## Risk
- 结果：`PASS`
- 剩余风险：
  - 本批审计的是 canonical menu/action 与模型权限边界
  - 合同状态按钮、自动生成清单等更细执行语义尚未展开；当前未发现必须阻断的 residual

## Rollback
- 本批为审计批次，无业务代码需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-04-01-510.yaml`
  - `git restore agent_ops/reports/2026-04-01/report.ITER-2026-04-01-510.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-01-510.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 继续自动推进
- 新开下一张低风险审计批次，选择另一个尚未覆盖的非首批流程家族，优先考虑不与已闭环合同/招投标/执行结构重复的独立业务面

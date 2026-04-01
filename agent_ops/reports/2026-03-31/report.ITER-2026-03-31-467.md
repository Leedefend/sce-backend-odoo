# ITER-2026-03-31-467

## Summary
- 在 `ITER-2026-03-31-466` 收窄财务边界后，重新复审了四川保盛首批业务流程在 `sc_odoo` 上的角色可用性
- 这轮结论为 `PASS`
- 当前 `PM / finance / executive / business_admin` 的角色到业务能力映射已经与冻结后的交付口径一致

## Scope
- 环境：
  - `DB = sc_odoo`
  - 客户：`四川保盛建设集团有限公司`
- 样本用户：
  - `hujun` (`pm`)
  - `jiangyijiao` (`finance`)
  - `wutao` (`executive`)
  - `admin` (`owner + business_full`)

## Runtime facts

### PM
- `hujun / pm`
  - `contract_manager = True`
  - `cost_user = True`
  - `cost_manager = False`
  - `material_manager = True`
  - `purchase_manager = True`
  - `finance_user = False`
  - `finance_manager = False`

结论：
- `PM` 已符合“合同操作/审批 + 成本经办 + 物资/采购操作/审批 + 无财务权限”口径

### Finance
- `jiangyijiao / finance`
  - `contract_read = True`
  - `cost_read = True`
  - `material_read = True`
  - `purchase_read = True`
  - `finance_manager = True`
  - `contract_user = False`
  - `cost_user = False`
  - `material_user = False`
  - `purchase_user = False`

结论：
- `finance` 已符合“财务专属 + 跨域只读”口径
- 项目口经办能力已清空

### Executive
- `wutao / executive`
  - `contract_manager = True`
  - `cost_manager = True`
  - `material_manager = True`
  - `purchase_manager = True`
  - `finance_manager = True`
  - `base.group_system = False`
  - `group_sc_super_admin = False`

结论：
- `executive` 已符合“完整业务权限 + 无平台泄漏”口径

### Business admin
- `admin / sc_role_profile=owner`
  - `group_sc_business_full = True`
  - `contract_manager = True`
  - `cost_manager = True`
  - `material_manager = True`
  - `purchase_manager = True`
  - `finance_manager = True`

结论：
- 当前 `admin` 的产品角色字段仍是 `owner`，但由于叠加 `business_full`，运行态仍是业务系统管理员全能力路径
- 这不影响首批交付可用性，但后续若追求角色展示语义一致，可以再单开治理批次收敛显示层

## Conclusion
- 四川保盛首批业务流程在最终权限矩阵下已具备可用性
- 角色边界现状：
  - `PM`：项目口经办/审批成立，无财务权限
  - `finance`：财务专属 + 跨域只读成立
  - `executive`：完整业务权限成立，无平台泄漏
  - `business_admin`：完整业务管理员路径成立

## Risk
- 结果：`PASS`
- 观察项：
  - `admin` 的 `sc_role_profile` 显示仍为 `owner`，但运行态由 `business_full` 覆盖到业务管理员全能力
  - 这属于展示/语义治理点，不是当前业务可用性阻断

## Rollback
- 本轮为只读复审，无产品实现改动需要回滚
- 若要撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-03-31-467.yaml`
  - `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-467.md`
  - `git restore agent_ops/state/task_results/ITER-2026-03-31-467.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 可以直接继续更细的四川保盛业务流程验收
- 最优先建议：
  - 按 `PM / finance / executive / business_admin` 分角色验证具体页面与动作链
  - 若要再收治理点，则单开一张 `business_admin` 展示语义与 `sc_role_profile` 对齐批次

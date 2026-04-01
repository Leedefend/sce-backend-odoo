# ITER-2026-03-31-466

## Summary
- 对四川保盛 `finance` 角色做了窄权限治理收口，目标是把财务从 `owner` 的项目口经办路径里拆出来，只保留“财务专属 + 跨域只读”
- 本轮不仅收窄了角色矩阵定义，还补了 customer 授权数据的显式清旧组逻辑，确保历史库升级时可以重复收敛
- 结果为 `PASS`

## Scope
- 变更路径：
  - [role_matrix_groups.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/security/role_matrix_groups.xml)
  - [customer_user_authorization.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/data/customer_user_authorization.xml)
- 验证对象：
  - `jiangyijiao` (`finance`)
  - `hujun` (`pm`)
  - `wutao` (`executive`)

## Change

### 1. Role matrix upgrade semantics
- 将这些客户侧角色组的 `implied_ids` 从增量 `(4, ref(...))` 改为全量覆盖 `(6, 0, [...])`
  - `group_sc_role_owner`
  - `group_sc_role_pm`
  - `group_sc_role_finance`
  - `group_sc_role_executive`
- 目的：
  - 升级时清掉历史残留 implied 关系
  - 避免旧版本 `finance -> owner` 这类关系在数据库里继续保留

### 2. Customer authorization cleanup
- 对四川保盛 finance 用户补了显式组移除：
  - `group_sc_role_owner`
  - `group_sc_role_project_user`
  - `group_sc_role_contract_user`
  - `group_sc_cap_project_user`
  - `group_sc_cap_contract_user`
  - `group_sc_cap_cost_user`
  - `group_sc_cap_material_user`
  - `group_sc_cap_purchase_user`
  - `project.group_project_user`
  - `purchase.group_purchase_user`
  - `stock.group_stock_user`
- 覆盖用户：
  - `shuiwujingbanren`
  - `jiangyijiao`
  - `lina`
  - `luomeng`
- 目的：
  - 清除历史库中已经 materialize 到用户上的项目口经办组
  - 保证 `make mod.upgrade ... smart_construction_custom` 可重复再现最终授权边界

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-466.yaml` → `PASS`
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_custom DB_NAME=sc_odoo` → `PASS`
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_odoo` → `PASS`
- `make verify.smart_core` → `PASS`

### Runtime audit
- `finance / jiangyijiao`
  - `group_sc_role_owner = False`
  - `group_sc_role_project_user = False`
  - `group_sc_role_contract_user = False`
  - `group_sc_cap_project_read = True`
  - `group_sc_cap_contract_read = True`
  - `group_sc_cap_cost_read = True`
  - `group_sc_cap_material_read = True`
  - `group_sc_cap_purchase_read = True`
  - `group_sc_cap_finance_manager = True`
  - `group_sc_cap_contract_user = False`
  - `group_sc_cap_cost_user = False`
  - `group_sc_cap_material_user = False`
  - `group_sc_cap_purchase_user = False`
- `pm / hujun`
  - `group_sc_cap_contract_manager = True`
  - `group_sc_cap_cost_user = True`
  - `group_sc_cap_cost_manager = False`
  - `group_sc_cap_material_manager = True`
  - `group_sc_cap_purchase_manager = True`
  - `group_sc_cap_finance_manager = False`
- `executive / wutao`
  - `group_sc_cap_finance_manager = True`
  - `group_sc_cap_cost_manager = True`
  - `base.group_system = False`
  - `group_sc_super_admin = False`

## Conclusion
- `finance` 已从项目口经办路径解耦完成
- `finance` 当前语义已对齐为：
  - 财务专属操作/审批
  - 跨业务域只读
  - 无合同/成本/物资/采购经办
- `PM` 与 `executive` 的既有边界未回退

## Risk
- 结果：`PASS`
- 剩余观察点：
  - `finance` 仍保留 `project.group_project_user` 的基础项目读路径语义，但不再携带合同/成本/物资/采购经办能力
  - 这与“跨域只读”口径一致，不构成当前 stop condition

## Rollback
- `git restore addons/smart_construction_custom/security/role_matrix_groups.xml`
- `git restore addons/smart_construction_custom/data/customer_user_authorization.xml`
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_custom DB_NAME=sc_odoo`
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_odoo`

## Next
- 继续回到四川保盛首批业务流程可用性验证
- 当前最有效的下一步是复审：
  - `PM`
  - `finance`
  - `executive`
  - `business_admin`
  在新矩阵下的业务入口、动作、审批链是否全部按最终交付口径成立

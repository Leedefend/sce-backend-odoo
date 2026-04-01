# ITER-2026-03-31-464

## Summary
- 升级四川保盛项目口权限矩阵：
  - `owner/通用角色` 现在承接项目经办语义，获得项目、合同、成本、物资、采购操作权限
  - `pm` 在项目经办基础上获得合同、物资、采购审批权限
  - `pm` 保持成本经办，不获得成本审批
  - 财务经办/审批未下放到项目口
- 修复了一个入口不一致：`WBS/分部分项` 菜单不再隐藏，改为跟随成本经办/审批能力组

## Changed Files
- `addons/smart_construction_custom/security/role_matrix_groups.xml`
- `addons/smart_construction_core/views/menu.xml`
- `addons/smart_construction_core/tests/test_user_role_profile_backend.py`
- `addons/smart_construction_custom/tests/test_business_admin_authority_path.py`
- `agent_ops/tasks/ITER-2026-03-31-464.yaml`

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-464.yaml` PASS
- `make verify.smart_core` PASS
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_odoo` PASS
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_custom DB_NAME=sc_odoo` PASS

## Runtime Audit
- 聚合审计：
  - `owner_contract_user_users = 2`
  - `owner_cost_user_users = 2`
  - `owner_material_user_users = 2`
  - `owner_purchase_user_users = 2`
  - `owner_finance_user_users = 1`
  - `owner_finance_manager_users = 1`
  - `pm_contract_manager_users = 4`
  - `pm_cost_user_users = 4`
  - `pm_cost_manager_users = 0`
  - `pm_material_manager_users = 4`
  - `pm_purchase_manager_users = 4`
  - `pm_finance_user_users = 0`
  - `pm_finance_manager_users = 0`
  - `executive_with_base_group_system = 0`
  - `executive_with_super_admin = 0`
- 特例解释：
  - `owner` 中混入财务权限的唯一用户是 `admin`
  - 原因是其同时拥有 `group_sc_role_business_admin`
  - 纯 `owner` 审计结果：
    - `plain_owner_count = 1`
    - `plain_owner_contract_user = 1`
    - `plain_owner_cost_user = 1`
    - `plain_owner_material_user = 1`
    - `plain_owner_purchase_user = 1`
    - `plain_owner_finance_user = 0`
    - `plain_owner_finance_manager = 0`

## Risk
- 结果：`PASS`
- 未触发 stop condition：
  - 未新增 ACL / record rule
  - 未把财务经办/审批下放到 `pm`
  - `executive` 未重新卷入平台组
- 已知非阻断项：
  - `smart_scene` manifest 仍缺 `license`
  - `smart_construction_custom` README 仍有 docutils 缩进 warning

## Rollback
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_odoo`
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_custom DB_NAME=sc_odoo`
- `git restore addons/smart_construction_custom/security/role_matrix_groups.xml`
- `git restore addons/smart_construction_core/views/menu.xml`
- `git restore addons/smart_construction_core/tests/test_user_role_profile_backend.py`
- `git restore addons/smart_construction_custom/tests/test_business_admin_authority_path.py`

## Next
- 回到四川保盛首批业务流程可用性验证，按新的项目口/财务口/管理层矩阵重新验主流程。

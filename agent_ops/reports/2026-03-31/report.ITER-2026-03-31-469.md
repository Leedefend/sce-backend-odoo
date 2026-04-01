# ITER-2026-03-31-469

## Summary
- 对 `WBS` 做了一个最小读入口对齐修补
- 目标不是新增经办/审批，而是把 `WBS` 补齐到你已冻结的“只读是基本规则”口径
- 结果为 `PASS`

## Scope
- 变更路径：
  - [action_groups_patch.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/action_groups_patch.xml)
  - [menu.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/menu.xml)
  - [project_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/project_views.xml)
- 不涉及：
  - ACL
  - record rules
  - payment / settlement / account 语义

## Change

### 1. WBS action
- [action_groups_patch.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/action_groups_patch.xml)
  - `action_project_wbs` 增加 `group_sc_cap_cost_read`

### 2. WBS menu
- [menu.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/menu.xml)
  - `menu_sc_project_wbs_cost` 增加 `group_sc_cap_cost_read`

### 3. Project form WBS tab
- [project_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/project_views.xml)
  - `wbs_tab` 增加 `group_sc_cap_cost_read`

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-469.yaml` → `PASS`
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_odoo` → `PASS`
- `make verify.smart_core` → `PASS`

### Runtime audit
- `finance / jiangyijiao`
  - `cost_read = True`
  - `cost_user = False`
  - `action_project_wbs = True`
  - `menu_sc_project_wbs_cost = True`

结论：
- 财务现在可以通过 `cost_read` 进入 `WBS`
- 同时仍然没有 `cost_user`
- 所以这次补的是纯读面，不是经办面扩大

## Conclusion
- `WBS` 已与既有成本域只读口径对齐
- `finance` 的跨域只读现在在成本域内部也闭合了：
  - `预算` 可读
  - `进度` 可读
  - `WBS` 现在也可读
- 未发生任何 operator / approval 泄漏

## Risk
- 结果：`PASS`
- 观察项：
  - 这次只修补了 `WBS` 的入口和项目表单页签读面
  - 若后续发现更深层子视图仍有局部 `cost_user/cost_manager` 限制，需要单独按实际页面补齐

## Rollback
- `git restore addons/smart_construction_core/security/action_groups_patch.xml`
- `git restore addons/smart_construction_core/views/menu.xml`
- `git restore addons/smart_construction_core/views/core/project_views.xml`
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_odoo`

## Next
- 可以继续回到四川保盛更细的业务流程验收
- 当前最合理的下一步是继续审：
  - `executive`
  - `business_admin`
  的具体页面/动作链

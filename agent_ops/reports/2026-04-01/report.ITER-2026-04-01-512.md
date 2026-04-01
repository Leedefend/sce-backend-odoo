# ITER-2026-04-01-512

## Summary
- 执行了 `quota center` delivered-role 入口修复批次
- 结论为 `PASS`
- `menu_project_quota_center` 不再直接让 delivered roles 读取
  `ir.actions.client` 记录，而是改走安全的 server action 返回既有 client-action dict

## Scope
- 本批为 narrow entry-path implementation
- 未修改 ACL、security matrix、manifest 或 frontend `project_quota_center` tag

## Change
- [dictionary_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/dictionary_views.xml)
  新增 `action_project_quota_center_entry`：
  - `model = ir.actions.server`
  - `groups_id = group_sc_cap_data_read`
  - 执行 `env['project.dictionary'].action_open_quota_center()`
- [dictionary_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/dictionary_views.xml)
  将 `menu_project_quota_center` 从直接指向
  `action_project_quota_center` 改为指向
  `action_project_quota_center_entry`
- 新增回归
  [test_dictionary_quota_entry_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_dictionary_quota_entry_backend.py)
  锁定 `pm / finance / executive / business_admin` 四类 delivered-role
  都能通过入口拿到：
  - `type = ir.actions.client`
  - `tag = project_quota_center`

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-512.yaml` → `PASS`
- `make verify.smart_core` → `PASS`
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_odoo` → `PASS`
- runtime audit on `sc_odoo` → `PASS`

## Runtime facts
- `PM / hujun`
  - `menu_project_quota_center` 可见
  - `action_project_quota_center_entry.run()` → `ir.actions.client / project_quota_center`
- `finance / jiangyijiao`
  - `menu_project_quota_center` 可见
  - `action_project_quota_center_entry.run()` → `ir.actions.client / project_quota_center`
- `executive / wutao`
  - `menu_project_quota_center` 可见
  - `action_project_quota_center_entry.run()` → `ir.actions.client / project_quota_center`
- `business_admin / admin`
  - `menu_project_quota_center` 可见
  - `action_project_quota_center_entry.run()` → `ir.actions.client / project_quota_center`
- 对照事实：
  - 旧 `action_project_quota_center` 记录本身对 `PM / finance / executive` 仍然不可直接读取
  - 说明修复点确实是入口路径，而不是 ACL 被意外抬宽

## Conclusion
- `action_project_quota_center` 的 delivered-role 可执行性 residual 已闭环
- `project.dictionary` 原有读写边界保持不变，frontend `project_quota_center` consumer 也未被改动

## Risk
- 结果：`PASS`
- 剩余风险：
  - 本批只修 menu entry path，不重新设计 dictionary/quota 产品结构
  - 下一步应直接重开父审计批次，把 `dictionary / quota center / 业务字典` 家族按新 runtime 重新分类

## Rollback
- `git restore addons/smart_construction_core/views/support/dictionary_views.xml`
- `git restore addons/smart_construction_core/tests/test_dictionary_quota_entry_backend.py`
- `git restore agent_ops/tasks/ITER-2026-04-01-512.yaml`
- `git restore agent_ops/reports/2026-04-01/report.ITER-2026-04-01-512.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-01-512.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 继续自动推进
- 新开一张超窄 reclassification 批次，复判 `dictionary / quota center / 业务字典` 家族

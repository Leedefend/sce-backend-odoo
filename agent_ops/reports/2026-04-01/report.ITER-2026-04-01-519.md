# ITER-2026-04-01-519

## Summary
- 打开 `config_admin / 平台治理面` 新目标线
- 选定并审计了第一条代表性治理家族：`scene orchestration / subscription`
- 结论为 `PASS`

## Scope
- 本批为 audit-first representative family selection
- 代表入口：
  - [scene_orchestration_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/scene_orchestration_views.xml)
    的 `menu_sc_scene_root / action_sc_capability / action_sc_scene`
  - [subscription_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/subscription_views.xml)
    的 `action_sc_subscription_plan`
- 角色样本：
  - `PM / hujun`
  - `finance / jiangyijiao`
  - `executive / wutao`
  - `business_admin / admin`

## Repository facts
- [scene_orchestration_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/scene_orchestration_views.xml)
  对 `menu_sc_scene_root / menu_sc_capability / menu_sc_scene` 显式挂载
  `group_sc_cap_config_admin`
- [scene_orchestration_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/scene_orchestration_views.xml)
  中 `action_sc_capability` 与 `action_sc_scene` 的 `groups_id` 也显式收敛到
  `group_sc_cap_config_admin`
- [subscription_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/subscription_views.xml)
  中 `action_sc_subscription_plan` 与 `menu_sc_subscription_plan` 同样显式收敛到
  `group_sc_cap_config_admin`
- [ir.model.access.csv](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/ir.model.access.csv)
  对 `sc.capability / sc.scene / sc.subscription.plan` 保持统一梯度：
  - `group_sc_internal_user`：只读
  - `group_sc_cap_config_admin`：读写删全开

## Runtime facts
- `PM / hujun` 与 `finance / jiangyijiao`：
  - `menu_sc_scene_root / menu_sc_capability / menu_sc_scene / menu_sc_subscription_plan` 全部隐藏
  - 目标模型仍有 internal-user 只读能力
- `executive / wutao` 与 `business_admin / admin`：
  - 上述菜单全部可见
  - `sc.capability / sc.scene / sc.subscription.plan` 均为可写
- runtime 上 action 本身可被读取，但 delivered-role 用户面并未暴露对应治理菜单

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-519.yaml` → `PASS`
- repository audit → `PASS`
- runtime audit on `sc_odoo` → `PASS`

## Conclusion
- `scene orchestration / subscription` 可以作为第一条 clean representative config-admin governance family
- 当前没有发现 delivered-role 用户面上的菜单/action/模型边界残差
- 当前 family 的真实语义是：
  - delivered read roles 保留底层 internal-user 只读能力
  - config-admin 角色才暴露治理入口并持有写面

## Risk
- 结果：`PASS`
- 剩余风险：
  - 本批没有继续展开 capability/scene 深层 object-button 执行路径
  - 如需验证更细的 admin mutation path，应另开更窄治理批次

## Rollback
- 本批为审计批次，无业务代码需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-04-01-519.yaml`
  - `git restore agent_ops/reports/2026-04-01/report.ITER-2026-04-01-519.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-01-519.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 继续自动推进
- 新开下一张低风险 config-admin 批次，正式分类 `quota import` 家族

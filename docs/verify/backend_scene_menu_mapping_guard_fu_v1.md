# Backend Scene Menu Mapping Guard FU v1

状态：PASS  
批次：`ITER-2026-04-21-BE-SCENE-MENU-MAPPING-GUARD-VERIFY-FU`

## 1. 目标

把第一批高频 family 的 menu target 解释状态收成第三道机器门禁。

这一批冻结的是“当前真实解释结果”，不是理想化蓝图：

- 稳定 menu 映射必须继续稳定
- 已知 alias/gap 必须保持显式可观测，不能静默漂移

## 2. 校验方法

脚本：`python3 scripts/verify/backend_scene_menu_mapping_guard.py`

脚本会同时读取：

- `smart_construction_scene/core_extension.py` 的 `smart_core_nav_scene_maps`
- `scene_registry_content.py`
- 关键 menu XML
- `smart_core/delivery/menu_target_interpreter_service.py`

然后构造最小导航事实，复用同一解释器去判断：

- `target_type`
- `scene_key`
- `route`
- `entry_target`

## 3. 当前冻结的稳定 menu 映射

- `menu_sc_root` -> `projects.list`
- `menu_sc_project_project` -> `projects.ledger`
- `menu_sc_finance_center` -> `finance.center`
- `menu_payment_request` -> `finance.payment_requests`
- `menu_sc_tier_review_my_payment_request` -> `payments.approval`

## 4. 当前冻结的已知 gap

- `menu_sc_project_initiation` -> `projects.intake`
- `projects.detail` 当前仍无独立 menu 映射
- `task.center` 当前仍无独立 menu 映射，但 nav scene maps 中已经有 `project.action_view_all_task -> task.center` 的 direct action scene map
- `finance.workspace` 当前仍共享 finance root menu，不替代 `finance.center` 的 menu-root 解释

## 5. 本批意义

到这一批为止，第一批高频 family 的后端场景化已经形成三段基础治理闭环：

- authority guard
- canonical-entry guard
- menu-mapping guard

这意味着后续再推进 projects/task family 收口时，不会把已经稳定的 finance/payment 菜单解释链重新打散。

## 6. 下一步

下一批应优先回到剩余 gap 收口侧：

- 优先处理 `task.center` 的 menu authority 缺口
- 再决定 `projects.detail` 是否需要独立 menu/action authority 收口

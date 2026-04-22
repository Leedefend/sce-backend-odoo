# Backend Scene Canonical Entry Guard FT v1

状态：PASS  
批次：`ITER-2026-04-21-BE-SCENE-CANONICAL-ENTRY-GUARD-VERIFY-FT`

## 1. 目标

把高频 family 的 canonical-entry 规则从文档冻结推进到机器校验。

本批关注的不是 authority source 本身，而是：

- canonical scene action/route 是什么
- native menu/action 是什么
- 二者是一致还是故意不一致
- compatibility fallback 是否仍符合当前治理口径

## 2. 校验来源

脚本：`python3 scripts/verify/backend_scene_canonical_entry_guard.py`

读取两类事实：

- registry canonical entry：`addons/smart_construction_scene/profiles/scene_registry_content.py`
- native menu action：`addons/smart_construction_core/views/menu_root.xml`、`menu.xml`、`menu_finance_center.xml`、`core/payment_request_views.xml`

## 3. 当前冻结的 entry 语义

本批将第一批高频 family 分成四类：

- `native_only_transitional`

- `action_only_scene_work`
  - `task.center`（declared action-only stable slice）

- `route_only_compat_scene`
  - `task.board`

- `scene_work_with_shared_native_root`
  - `finance.center`
  - `finance.workspace`

- `scene_work_with_shared_native_compat`
  - `projects.detail`

- `scene_work_with_native_parity`
  - `projects.ledger`
  - `projects.list`
  - `projects.intake`
  - `payments.approval`

- `scene_work_with_native_fallback`
  - `finance.payment_requests`

## 4. 本批 guard 要求

- 每个 baseline scene 都必须命中预期 canonical action
- route 已冻结的 scene 必须保留显式 canonical route
- `native_only_transitional` scene 不允许偷偷长出 route
- `projects.list` 必须继续保持：
  - canonical route = `/s/projects.list`
  - canonical action = `action_sc_project_list`
  - 与 native root menu action 保持一致

- `projects.ledger` 必须继续保持：
  - canonical route = `/s/projects.ledger`
  - canonical action = `action_sc_project_kanban_lifecycle`
  - 与 project ledger native menu action 保持一致
  - 同时保留与 `projects.detail` 的 shared native action known gap
- `projects.detail` 必须继续保持：
  - canonical route = `/s/projects.detail`
  - canonical action = `action_sc_project_kanban_lifecycle`
  - 当前 shared native menu/action 只按 compatibility 解释，不代表 detail 拥有 collection native action
- `finance.payment_requests` 必须继续保持：
  - canonical action = `action_payment_request_my`
  - native menu action = `action_payment_request`

- `payments.approval` 必须继续保持：
  - canonical action = `action_sc_tier_review_my_payment_request`
  - 与 dedicated approval native menu action 保持一致
  - 同时与 payment request list native action 分离

- `finance.center` 必须继续保持：
  - canonical route = `/s/finance.center`
  - 与 finance root native action 保持一致
- `task.center` 必须继续保持：
  - canonical route = `/s/task.center`
  - canonical action = `project.action_view_all_task`
  - 不依赖 native menu authority
  - action-only 语义是稳定治理口径，不再视为待补 menu gap
- `task.board` 必须继续保持：
  - canonical route = `/s/task.board`
  - 不依赖 canonical action
  - 不依赖 native menu/action authority
  - 其语义是 authority-light 的 board-style compat scene，而不是 full native-authority scene

- `finance.center` 与 `finance.workspace` 必须继续共用 finance root native action

## 5. 产物

脚本运行后会输出：

- `artifacts/backend/backend_scene_canonical_entry_guard.json`
- `artifacts/backend/backend_scene_canonical_entry_guard.md`

## 6. 本批结论

这一批通过以后，后端场景化在第一批高频 family 上已经具备两道基础门禁：

- authority guard
- canonical-entry guard

这意味着后续 family 收口不再是“靠记忆维护语义”，而是已经有明确 verify surface。

## 7. 下一步

下一批应优先补：

- `menu_mapping_guard`

也就是把 `/api/menu/navigation` 的目标解释稳定性一起锁住，形成 authority -> canonical entry -> menu mapping 三段闭环。

# Backend Scene Authority Guard FS v1

状态：PASS  
批次：`ITER-2026-04-21-BE-SCENE-AUTHORITY-GUARD-VERIFY-FS`

## 1. 目标

把 `scene_family_inventory_v1.md` 里的第一批高频 family 基线变成机器校验。

这一批不修改后端运行时，只新增一个 verify surface：

- 已冻结 family 必须命中固定 authority 三元组
- 已知缺口 family 必须保持当前缺口状态，不允许静默漂移

## 2. 校验面

脚本：`python3 scripts/verify/backend_scene_authority_guard.py`

权威源：

- registry：`addons/smart_construction_scene/profiles/scene_registry_content.py`
- baseline：`docs/architecture/scene_family_inventory_v1.md`
- hierarchy：`docs/architecture/scene_authority_hierarchy_v1.md`

## 3. 当前 guard 规则

覆盖 family：

- `projects.*`
- `task.center`
- `task.board`
- `finance.center`
- `finance.workspace`
- `finance.payment_requests`
- `payments.approval`

本批冻结的机器规则：

- scene code 不允许重复
- 每个 baseline scene 都必须存在
- `route/menu_xmlid/action_xmlid` 必须符合 inventory 对应的当前 authority 状态
- `projects.list` 已升级为 canonical route 显式冻结态，并保持 native menu/action parity
- `projects.ledger` 已升级为 canonical route 显式冻结态，并保留与 `projects.detail` 的 shared native action 已知 gap
- `projects.detail` 已冻结为 detail-route authority，继续复用 shared native menu/action 仅作为 compatibility
- `finance.center` 已升级为 canonical route 显式冻结态，并与 `finance.workspace` 保持 shared native root
- `projects.intake` 已升级为 canonical route 显式冻结态，并保留 `project.initiation` 兼容 route
- `task.center` 已冻结为 declared action-only stable slice，且明确保持无 dedicated menu authority
- `task.board` 已冻结为 route-only compat scene，且明确保持无 native menu/action authority
- `finance.payment_requests` 与 `payments.approval` 必须继续分离 native menu、分离 canonical action
- `finance.center` 与 `finance.workspace` 必须继续共用 native root menu/action，且 `finance.workspace` 必须保留显式 route

## 4. 产物

脚本运行后会输出：

- `artifacts/backend/backend_scene_authority_guard.json`
- `artifacts/backend/backend_scene_authority_guard.md`

## 5. 本批结论

本批 guard 已通过，说明当前后端场景化 authority 至少具备以下治理能力：

- finance/payment 已收口切片不会再无声回漂
- projects 族当前 residual、projects.detail 的 compat-only shared-native 语义，以及 task family 下 task.center/task.board 的轻量入口语义都被显式冻结，不会被偶然修改成更混乱的半漂移状态
- 后续可以在不改现有 guard 口径的前提下继续开下一批 canonical-entry guard

## 6. 下一步

下一批应补：

- `canonical_entry_guard`

重点不是再做 repo-wide 扫描，而是把同一批 family 的 canonical entry 唯一性与 compatibility fallback 一起收成第二道门禁。

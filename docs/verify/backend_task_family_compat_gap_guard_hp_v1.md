# Backend Task Family Compat Gap Guard HP v1

状态：PASS  
批次：`ITER-2026-04-22-BE-TASK-BOARD-COMPAT-GUARD-IMPLEMENT-HP`

## 1. 目标

把 task family 最后一个显式 residual 从“日志里的已知事实”推进到机器校验。

本批不改变运行时映射，只新增一个 bounded verify surface：

- `project.task.list` 必须继续归 `task.center`
- `project.task.board` 必须归独立 compat carrier：`task.board`
- `task.board` 当前仍是 authority-light compat carrier，而不是 full native-authority scene

## 2. 校验面

脚本：`python3 scripts/verify/backend_task_family_compat_gap_guard.py`

读取事实：

- `addons/smart_construction_scene/services/capability_scene_targets.py`

实现约束：

- guard 只解析 `CAPABILITY_ENTRY_SCENE_MAP` 字面量
- guard 不加载 Odoo runtime，不依赖 `odoo` 模块
- guard 不执行 capability 模块内的其他逻辑

## 3. 当前冻结的治理口径

- `project.task.list` 已完成主入口收口，不允许回漂到 `projects.ledger`
- `project.task.board` 不应被误解释成 `task.center`
- `project.task.board` 当前不再借用 `projects.ledger`
- `task.board` 代表 dedicated backend compat target 已出现，但仍未拥有 native menu/action authority

## 4. 产物

脚本运行后会输出：

- `artifacts/backend/backend_task_family_compat_gap_guard.json`
- `artifacts/backend/backend_task_family_compat_gap_guard.md`

## 5. 本批结论

这一批通过以后，task family 的 board-style compat carrier 已经从“借用别人”升级为“独立 machine-visible carrier”。

后续该 guard 必须继续保持 pure Python 可运行，避免再次退化为环境依赖型验证。

后续如果：

- 把 `project.task.list` 静默打回 `projects.ledger`
- 把 `project.task.board` 静默吞进 `task.center`
- 把 `project.task.board` 再次静默打回 `projects.ledger`
- 或把 `task.board` 误包装成已经具备 native authority 的 full scene

都会被这道 guard 直接拦住。

# Scene Family Inventory v1

状态：Governance Baseline  
适用范围：高频 family authority freeze / canonical entry inventory

## 1. 目标

本文件用于给第一批高频 scene family 建一张统一治理表。

目标不是描述所有 scene，而是先冻结最容易影响用户入口稳定性的几类：

- `projects.*`
- `task.center`
- `finance.center`
- `finance.payment_requests`
- `payments.approval`

表内字段统一表达：

- family
- scene_key
- native menu
- native action
- canonical route
- canonical action
- compatibility fallback
- 当前 authority 缺口

## 2. Inventory

| family | scene_key | native menu | native action | canonical route | canonical action | compatibility fallback | authority gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| projects | `projects.list` | `smart_construction_core.menu_sc_root` | `smart_construction_core.action_sc_project_list` | `/s/projects.list` | `smart_construction_core.action_sc_project_list` | native menu/action can remain as compatibility source fact | registry 未显式写 route，当前 route authority 主要落在 scene profile |
| projects | `projects.ledger` | `smart_construction_core.menu_sc_project_project` | `smart_construction_core.action_sc_project_kanban_lifecycle` | `/s/projects.ledger` | `smart_construction_core.action_sc_project_kanban_lifecycle` | native menu/action compatibility retained | registry 未显式写 route，canonical route 主要由 list profile 冻结 |
| projects | `projects.intake` | `smart_construction_core.menu_sc_project_initiation` | `smart_construction_core.action_project_initiation` | `/s/projects.intake` | `smart_construction_core.action_project_initiation` | native create/form entry remains compatibility source; `project.initiation` retained as compat route alias | registry/menu/action/capability 已收口到 `projects.intake`，剩余 layout/profile alias 残留仍需后续治理 |
| projects | `projects.detail` | `smart_construction_core.menu_sc_project_project` | `smart_construction_core.action_sc_project_kanban_lifecycle` | `/s/projects.detail` | `smart_construction_core.action_sc_project_kanban_lifecycle` | record/detail compatibility still exists outside this table | detail family 与 ledger family 共享 native action，detail-vs-ledger semantic split 仍需长期治理 |
| tasks | `task.center` | _(none frozen in registry)_ | `project.action_view_all_task` | `/s/task.center` | `project.action_view_all_task` | action-first scene entry; no dedicated menu authority yet | canonical route 已补齐，但仍缺 native menu authority，属于 action-first family |
| finance_center | `finance.center` | `smart_construction_core.menu_sc_finance_center` | `smart_construction_core.action_sc_finance_dashboard` | `/s/finance.center` | `smart_construction_core.action_sc_finance_dashboard` | native finance center menu remains compatibility/source fact | root action 已对齐，但 scene page/layout/profile 仍需持续检查是否回漂 |
| finance_center | `finance.workspace` | `smart_construction_core.menu_sc_finance_center` | `smart_construction_core.action_sc_finance_dashboard` | `/s/finance.workspace` | `smart_construction_core.action_sc_finance_dashboard` | same native root menu as compatibility source | `finance.center` 与 `finance.workspace` 共用 native menu/action，双 scene 分化仍需 guard 约束 |
| payment_entry | `finance.payment_requests` | `smart_construction_core.menu_payment_request` | `smart_construction_core.action_payment_request` | `/s/finance.payment_requests` | `smart_construction_core.action_payment_request_my` | generic native payment list action kept as compatibility/native entry | canonical scene entry 已冻结为 `action_payment_request_my`，但原生 menu 默认仍指向 `action_payment_request`，必须依赖 authority 规则解释 |
| payment_approval | `payments.approval` | `smart_construction_core.menu_payment_request` | `smart_construction_core.action_sc_tier_review_my_payment_request` | `/s/payments.approval` | `smart_construction_core.action_sc_tier_review_my_payment_request` | menu shared with payment request list; approval action retained as scene-work identity | 与 `finance.payment_requests` 共用 menu，但 canonical entry 不同，必须依赖 entry semantics 和 mapping guard 防止漂移 |

## 3. 读表规则

### 3.1 `native menu`

表示原生 Odoo 菜单来源。

它是：

- source fact
- compatibility fact

它不是：

- scene canonical identity 的最高权威

### 3.2 `native action`

表示原生 menu 默认绑定的 act_window/action。

它可以与 canonical action 相同，也可以不同。

### 3.3 `canonical route`

表示产品化 scene work entry 对外正式 route。

如果这一列为空，表示当前 family 还未完成 route authority 冻结。

### 3.4 `canonical action`

表示 scene 编排层认定的正式工作入口动作。

如果与 native action 不同，必须按 `scene_entry_semantics_v1.md` 解释。

## 4. 当前治理判断

### 4.1 已相对稳定的 family

- `finance.center`
- `finance.workspace`
- `finance.payment_requests`
- `payments.approval`

这些 family 的 scene identity 与 canonical entry 已完成近期收口，但还缺 guard。

### 4.2 仍有明显 authority 缺口的 family

- `task.center`
- `projects.list`
- `projects.ledger`
- `projects.intake`
- `projects.detail`

其中最典型的问题是：

- registry 未显式冻结 canonical route
- detail/list/workspace 之间仍有 shared native action
- route authority 仍部分落在 profile/layout 而不是 registry

## 5. 下一步建议

基于这张 inventory，下一批治理应优先做两件事：

1. `authority_guard`
   - 检查同一 family/scene 是否存在 route/menu/action authority 冲突

2. `canonical_entry_guard`
   - 检查高频 family 是否都具备唯一 canonical entry

建议顺序：

1. 先给 `projects.*` 与 `task.center` 做 authority re-screen
2. 再补 guard

## 6. 本轮临时结论

这张表说明当前系统已经不再是“完全无序的 scene 集合”，而是：

- finance payment 族已经进入 canonical-entry 收口阶段
- projects/task 族仍处于 route authority 未完全冻结阶段

所以第二批治理的重心应该逐步转向：

> 给 family 建统一 authority inventory，并用 guard 锁住已收好的 payment/finance 族，再去继续收项目/任务族。

# Odoo 原生承载差距迭代进展（v0.2）

日期：2026-03-04  
分支：`feat/interaction-core-p1-v0_2`

## 本轮目标

基于《Odoo 原生视图系统承载能力评估（2026-03-03）》推进“可交付能力优先”的下一轮迭代，聚焦：

1. 搜索契约消费补齐：`saved_filters` / `group_by`
2. operation 网关闭环加固：`app.action.gateway` + dispatcher 稳定化
3. 回归守护补齐：新增专项 guard，避免回退

## 已完成改动（10 个独立提交）

1. `feat(action-view): consume saved_filters in search contract`
2. `feat(action-view): consume search.group_by with route-state sync`
3. `feat(action-view): persist list search/sort/filter in route query`
4. `feat(api.data): add group_by request field in frontend contract`
5. `feat(api.data): normalize group_by payload and apply to context`
6. `fix(dispatcher): harden operation gateway resolution and su_env wiring`
7. `feat(core): add app.action.gateway adapter for execute/onchange ops`
8. `test(verify): add search group_by/saved_filters runtime guard`
9. `test(verify): add operation gateway contract guard`
10. `docs(assessment): add v0.2 iteration progress report`

## 能力增量（本轮）

### 1) 搜索契约消费补齐

- `ActionView` 已消费 `search.saved_filters`，支持：
  - 首屏“已保存筛选”入口
  - `saved_filter` 路由参数持久化
  - domain/context 与既有契约筛选并行合并
- `ActionView` 已消费 `search.group_by`，支持：
  - 首屏“分组查看”入口
  - `group_by` 路由参数持久化
  - 请求 `context/group_by/context_raw` 一致注入

### 2) api.data 分组语义加固

- 前端 `ApiDataListRequest` 补齐 `group_by` 字段。
- 后端 `api.data` 补齐 `group_by` 归一化逻辑，统一写入 `ctx["group_by"]`，并在 `meta.group_by` 回传生效值。

### 3) operation 网关闭环

- 新增 `app.action.gateway`（AbstractModel）并提供：
  - `run_object_method`
  - `run_onchange`（复用 `ApiOnchangeHandler` 归一化输出）
- `action_dispatcher` 改为显式 `_resolve_action_gateway()`，并修复 server-action 二次分发时 `PageAssembler` 的 `su_env` 传递。

### 4) 回归防线

- 新增 guard：`search_groupby_savedfilters_guard`
- 新增 guard：`operation_gateway_contract_guard`
- `verify.frontend.quick.gate` 已纳入 `search_groupby_savedfilters_guard`

## 验证记录

已通过：

- `make verify.frontend.quick.gate`
- `make verify.smart_core`

## 仍存差距（下一轮优先）

1. `group_by` 目前完成“契约消费与请求语义闭环”，尚未在前端做真正“分组结果渲染”（当前仍为列表记录视图）。
2. x2many 虽有命令语义与 inline 能力，但距离 Odoo 原生子视图编辑（尤其复杂 one2many 内联）仍有差距。
3. scene catalog 覆盖仍偏窄（当前导出 `scene_count=5`），需扩大到关键业务域 20+ 场景并进入 CI 漂移检测。

## 建议下一轮范围（P1.5）

1. `api.data` 增加 `read_group` 风格契约返回，前端新增 grouped-list 渲染层（最小可用）。
2. many2one `search-more/create-edit` 一致化（契约与前端联动）。
3. 扩充 `docs/contract/cases.yml` 并执行 `contract.export_all`，将 `project/task/contract/cost/risk` 场景覆盖提升到 20+。

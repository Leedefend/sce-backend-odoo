# Odoo 原生承载差距迭代进展（v0.3）

日期：2026-03-04  
分支：`feat/interaction-core-p1-v0_3`

## 本轮目标

把 `group_by` 从“摘要可见”推进到“分组结果可读”，形成最小可用 grouped-list 体验。

## 已完成

1. `api.data` 增加 `grouped_rows`
   - 每个分组返回 `label/count/domain/sample_rows`
   - 保持原 `records/group_summary` 输出不变，向后兼容

2. 前端契约补齐
   - `ApiDataListResult` 新增 `grouped_rows` 类型定义

3. 列表渲染接入
   - `ActionView` 消费 `grouped_rows`
   - `ListPage` 新增分组块渲染（每组展示样本记录）
   - 与现有批量操作、行点击路径兼容

4. 治理防回退
   - 新增 `grouped_rows_runtime_guard`
   - 已接入 `verify.frontend.quick.gate`

5. 分组列表交互增强
   - `ListPage` 增加分组块排序（按计数升/降）与折叠开关
   - 每个分组新增“查看全部”入口，触发 `ActionView` 按组 domain 下钻
   - 下钻后保持现有列表语义（过滤、点击、批量操作）不变
   - 新增每组样本条数切换（3/5/8），并通过路由+请求参数同步到 `api.data.group_sample_limit`
   - 分组排序（asc/desc）与折叠键集合持久化到路由（`group_sort` / `group_collapsed`），刷新后可恢复

## 当前状态

- `group_by` 能力链路：
  - 请求：`group_by` + context 合并
  - 响应：`group_summary + grouped_rows`
  - 前端：摘要 + 分组样本可视化 + 下钻过滤

## 下一步建议

1. 将 grouped-list 从“样本记录”升级为“可分页组内记录”
2. 增加分组排序/折叠状态路由持久化
3. 把 `grouped_rows` 纳入 e2e 场景快照对比

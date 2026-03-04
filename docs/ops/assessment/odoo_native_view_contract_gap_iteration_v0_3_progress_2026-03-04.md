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
   - 增加“全部展开/全部收起”批量折叠控制，并在边界状态（已全收起/无分组）自动禁用
   - 列表重载后自动清理失效 `group_collapsed/group_value` 路由状态，避免历史参数污染分组交互

6. 分组组内分页（最小可用）
   - `ListPage` 每个分组新增“上一页/下一页”分页控制与范围显示（如 `1-3 / 24`）
   - `ActionView` 新增按组分页请求回调，基于组 `domain` 走 `api.data` 增量拉取（`limit/offset`）
   - 保持主列表与分组下钻行为不变，仅替换当前分组样本区块的数据页
   - `grouped_rows_runtime_guard` 新增分页链路标记校验，已接入 `verify.frontend.quick.gate`

7. `grouped_rows` 纳入 e2e 场景快照对比
   - `scripts/e2e/e2e_contract_smoke.py` 新增 project/contract/cost/risk 四域 `group_by` 采样请求
   - 输出 `api_data_grouped` 与 `api_data_grouped_signature` 到 e2e 快照
   - 新增基线 `scripts/verify/baselines/e2e_grouped_rows_signature.json`，默认执行对比
   - 支持 `E2E_GROUPED_SNAPSHOT_UPDATE=1` 更新基线；权限受限域记入 `skipped(PERMISSION_DENIED)` 以保持可审计性

## 当前状态

- `group_by` 能力链路：
  - 请求：`group_by` + context 合并
  - 响应：`group_summary + grouped_rows`
  - 前端：摘要 + 分组样本可视化 + 下钻过滤 + 组内分页
  - e2e：四域 grouped 签名已纳入快照基线对比

## 验收执行结果（2026-03-04）

1. `make verify.frontend.quick.gate`：通过
   - 包含 `group_summary_runtime_guard` 与 `grouped_rows_runtime_guard` 在内的前端契约守卫全部通过
   - 前端严格类型检查与构建通过
2. `make verify.smart_core`：通过
   - 结果：`[verify.smart_core] semantic checks OK`
   - 结果：`[verify.smart_core] PASS outdir=/tmp/smart_core_verify`
3. `make verify.e2e.contract`：通过
   - 产物：`artifacts/e2e/contract_smoke_*/snapshot.raw.json`
   - 产物：`artifacts/e2e/contract_smoke_*/snapshot.normalized.json`
   - grouped 签名基线：`scripts/verify/baselines/e2e_grouped_rows_signature.json`

## 下一步建议（下一轮）

1. 把组内分页从“上一页/下一页”升级为“页码 + 跳转 + 总页数”
2. 把分组分页状态（per-group offset）纳入路由持久化
3. 在 FE 场景 smoke 中加入组内翻页交互断言（不只合同 e2e 快照）

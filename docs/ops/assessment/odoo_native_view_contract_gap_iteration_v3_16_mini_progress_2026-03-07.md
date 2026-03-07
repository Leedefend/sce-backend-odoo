# Odoo 原生承载差距迭代进展（v3.16-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 已完成

1. 路由契约增强：
   - ActionView HUD 新增 `route_group_wid`
   - `applyRoutePreset/syncRouteListState` 新增 `group_wid` 读写同步
2. 状态重置闭环：
   - grouped 条件切换、分组切换、样本窗口切换、窗口翻页等路径均补齐 `group_wid` 清理
3. 运行时回正：
   - grouped 加载后对比 `route.query.group_wid` 与响应 `group_paging.window_id`
   - 非首窗口失配时自动回正到首窗口并重载
4. runtime guard 同步：
   - grouped_rows_runtime_guard 增加 `group_wid` 关键标记约束

## 验证结果

1. `make verify.grouped.governance.bundle`：PASS
2. `make verify.frontend.quick.gate`：PASS
3. `make verify.contract.preflight`：PASS

## 结论

grouped 窗口身份在路由层形成“读入-校验-回正-回写”闭环，窗口漂移导致的分页语义失真可被前端自动收敛。

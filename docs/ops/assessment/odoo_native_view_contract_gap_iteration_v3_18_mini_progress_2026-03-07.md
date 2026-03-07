# Odoo 原生承载差距迭代进展（v3.18-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 已完成

1. 路由契约增强：
   - ActionView HUD 新增 `route_group_wdg`
   - `applyRoutePreset/syncRouteListState` 新增 `group_wdg` 读写同步
2. 运行时回正：
   - grouped 加载后对比 `route.query.group_wdg` 与响应 `group_paging.window_digest`
   - 非首窗口失配时自动回正到首窗口并重载
3. 重置路径补齐：
   - grouped 切换/钻取/翻页/样本窗口切换路径统一清理 `group_wdg`
4. runtime guard 同步：
   - grouped_rows_runtime_guard 增加 `group_wdg` 关键标记约束
5. 文档同步：
   - grouped pagination contract 新增 `group_wdg` 路由键与兼容规则

## 验证结果

1. `make verify.grouped.governance.bundle`：PASS
2. `make verify.frontend.quick.gate`：PASS
3. `make verify.contract.preflight`：PASS

## 结论

grouped 路由态已覆盖“查询指纹 + 窗口身份 + 窗口摘要”三层防漂移锚点，窗口语义在前端可自动收敛并保持可观测。

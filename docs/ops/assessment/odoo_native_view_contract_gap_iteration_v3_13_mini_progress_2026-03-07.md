# Odoo 原生承载差距迭代进展（v3.13-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 已完成

1. 分组路由语义增强：
   - 新增 `group_fp` 路由参数，承载 grouped 查询指纹
2. ActionView 过期保护落地：
   - 加载后比对 `route.group_fp` 与 `group_paging.query_fingerprint`
   - 指纹不一致且 `group_offset>0` 时自动重置窗口状态并回到首窗口
   - 首窗口场景下自动将最新指纹同步回 URL
3. 一致性处理：
   - group_by/group_value/group_sample_limit 等重置路径统一清理 `group_fp`
4. runtime guard 与文档同步：
   - grouped_rows_runtime_guard 增加 `group_fp` 关键标记
   - grouped contract 增加 `group_fp` 路由键说明

## 验证结果

1. `make verify.grouped.governance.bundle`：PASS
2. `make verify.frontend.quick.gate`：PASS
3. `make verify.contract.preflight`：PASS

## 结论

grouped 分组窗口已具备基于指纹的过期保护机制，深链回放在查询条件变化后可自动回归有效窗口，避免前端停留在过期偏移状态。

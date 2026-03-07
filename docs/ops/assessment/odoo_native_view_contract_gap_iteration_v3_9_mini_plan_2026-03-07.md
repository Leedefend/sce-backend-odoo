# Odoo 原生承载差距迭代计划（v3.9-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦契约消费侧落地：前端分组窗口导航从本地推导偏移切到后端权威偏移。

## 本轮目标

1. ActionView 请求 `group_offset` 改为路由态驱动
2. 消费 `group_paging.next_group_offset/prev_group_offset`
3. 分组摘要区域提供上一组/下一组窗口导航
4. 路由态补齐 `group_offset` 同步与归一化
5. 文档补齐“前端应优先使用后端导航偏移”规则

## 验收口径

1. 分组窗口翻页不依赖前端自行推导偏移
2. URL `group_offset` 可还原分组窗口
3. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`

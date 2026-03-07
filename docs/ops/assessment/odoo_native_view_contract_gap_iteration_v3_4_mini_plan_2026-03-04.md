# Odoo 原生承载差距迭代计划（v3.4-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

进入新一轮“契约实质性完善”，继续聚焦 grouped 分页/分组契约可消费性，不增加治理脚本。

## 本轮首批目标（已启动）

1. `group_summary` 增加稳定 `group_key`（由后端统一生成）
2. 前端消费优先使用后端 `group_key`，减少前端自行拼接 key 的歧义
3. schema 与契约文档同步

## 验收口径

1. `group_summary` / `grouped_rows` 均可使用同一 `group_key` 语义
2. 现有 grouped 回归链路保持通过

# Odoo 原生承载差距迭代计划（v3.0-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v2_8`

## 目标调整

本轮从“治理完善”切换为“契约本体完善”，不新增治理 guard，直接增强 `api.data(list)` grouped 分页契约表达能力。

## 本轮目标（执行项）

1. 后端契约增强：
   - 支持请求参数 `group_page_size`
   - `grouped_rows` 返回增加 `page_size`（并保留 `page_limit` 兼容）
2. 前端契约消费同步：
   - schema 类型声明增加 `group_page_size` / `page_size`
   - ActionView 读写 grouped 分页时优先消费 `page_size`
3. 契约文档同步：
   - 更新 grouped pagination contract 字段说明
4. 完成 grouped bundle + frontend quick gate + contract preflight 回归

## 验收口径

1. `api.data(list)` grouped 分页存在明确 page-size 契约键（请求/响应）
2. 前后端在 `page_size` 上完成向后兼容对齐
3. 以下命令通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`

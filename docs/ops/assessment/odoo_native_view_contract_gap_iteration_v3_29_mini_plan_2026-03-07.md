# Odoo 原生承载差距迭代计划（v3.29-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 `window_identity` 模型维度自描述：新增 `model` 字段，确保 identity 可独立声明所属业务模型。

## 本轮目标

1. `window_identity` 新增 `model`
2. schema 同步新增 `window_identity.model`
3. grouped smoke/guard 增加 `model` 与请求模型一致性校验
4. grouped 契约文档补齐 identity 模型字段定义
5. 完成回归与提交

## 验收口径

1. grouped 响应 `window_identity.model` 与请求模型一致
2. smoke/guard 可检测模型维度漂移
3. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`

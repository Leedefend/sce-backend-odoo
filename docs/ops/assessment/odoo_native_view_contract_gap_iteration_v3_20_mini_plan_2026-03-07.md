# Odoo 原生承载差距迭代计划（v3.20-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 grouped 窗口身份协议化：为 `window_identity` 增加 `version/algo` 元信息，明确摘要协议并为后续算法迁移预留演进位。

## 本轮目标

1. 后端 `window_identity` 增加 `version/algo`
2. schema 同步补齐 `window_identity.version/algo`
3. grouped smoke/guard 增加 identity 协议元信息校验
4. grouped 契约文档补齐协议语义与兼容规则
5. 完成回归与提交

## 验收口径

1. grouped 响应包含 `window_identity.version/algo`
2. smoke 可识别版本/算法字段存在且算法在当前支持集（sha1）
3. guards 能拦截协议字段缺失
4. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`

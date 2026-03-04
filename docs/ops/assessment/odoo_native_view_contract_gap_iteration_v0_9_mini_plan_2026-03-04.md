# Odoo 原生承载差距迭代计划（v0.9-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v0_9`

## 目标来源（评估报告映射）

在 v0.8 已完成 grouped pagination 主体契约后，继续做“契约治理收口”：把 grouped 语义纳入快照证据与跨层一致性校验，减少未来回归时的盲区。

## 本轮目标（执行项）

1. e2e grouped snapshot 增加 `page_window/page_has_prev/page_has_next/group_key` 能力签名
2. e2e grouped baseline 与 drift 检查升级到新签名
3. contract evidence 增加 grouped 语义一致性指标（window-range consistency）
4. 新增 grouped contract consistency guard（后端输出 vs smoke 语义摘要）
5. 前端 quick gate 接入该 guard
6. 更新 v0.9-mini 进展文档
7. 完成 tree smoke + frontend quick gate + contract preflight

## 验收口径

1. grouped 关键字段在 smoke + e2e snapshot 双证据链可见
2. 一致性 guard 通过且接入 quick gate
3. 以下命令通过：
   - `make verify.portal.tree_view_smoke.container`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`

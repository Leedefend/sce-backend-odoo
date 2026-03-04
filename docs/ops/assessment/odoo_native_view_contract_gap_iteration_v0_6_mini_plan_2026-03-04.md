# Odoo 原生承载差距迭代计划（v0.6-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v0_6`

## 目标来源（评估报告映射）

延续 P2 治理增强方向，聚焦“可视化覆盖结果可校验、可并入证据链、可在 preflight 中稳定收敛”。

## 本轮目标（执行项）

1. 为 `scene_contract_coverage_brief` 增加独立 schema guard（结构与类型）
2. 为 `scene_contract_coverage_brief` 增加 baseline guard（关键阈值与回退检测）
3. 将 scene coverage guard 接入 `verify.contract.preflight`
4. 细化 tree grouped 语义摘要：增加 consistency 字段（request/first-group 对齐）
5. 为 grouped 语义摘要新增专用 drift guard（防结构回退）
6. 将 grouped drift guard 接入 `verify.frontend.quick.gate`
7. 强化 contract evidence 对 `scene_contract_coverage` 区块的校验口径
8. 提供 scene coverage markdown 简报增强（layer 占比与拓扑摘要）
9. 补齐本轮进展文档与验证证据
10. 完成本轮合并前统一回归（frontend quick + tree smoke + contract preflight fast 参数）

## 提交节奏（约 10 个独立提交）

1. docs: v0.6-mini 计划文档
2. feat(verify): scene coverage schema guard
3. feat(verify): scene coverage baseline guard + baseline file
4. chore(make): preflight 接入 scene coverage guards
5. feat(smoke): grouped semantic summary consistency 字段
6. feat(verify): grouped semantic drift guard
7. chore(make): quick gate 接入 grouped drift guard
8. feat(verify): contract evidence guard 增强 scene coverage 约束
9. docs: v0.6-mini 进展文档
10. chore(verify): round gate 回归与收口

## 验收口径

1. `scene_contract_coverage_brief` 具备 schema + baseline 双 guard
2. `verify.contract.preflight`（快速参数）包含并通过 scene coverage guard
3. grouped 语义摘要新增字段有 guard 覆盖且在 quick gate 通过
4. `contract_evidence` 对 scene coverage 的校验不回退
5. 回归通过：
   - `make verify.frontend.quick.gate`
   - `make verify.portal.tree_view_smoke.container`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`

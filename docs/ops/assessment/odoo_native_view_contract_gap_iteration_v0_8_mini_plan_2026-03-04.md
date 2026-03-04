# Odoo 原生承载差距迭代计划（v0.8-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v0_8`

## 目标来源（评估报告映射）

延续“治理即契约能力”的策略，在 v0.7 的 grouped 分页字段落地后，补齐“可验证、可观测、可演进”的后端契约闭环，避免前后端语义漂移再次出现。

## 本轮目标（执行项）

1. 后端 grouped rows 契约补充 `page_window`（`start/end`）聚合字段（向前兼容已有离散字段）
2. 前端列表分页文案优先消费后端 `page_window`，仅在缺失时回退本地推导
3. smoke 基线增加 `page_window` 字段签名与类型断言
4. grouped runtime guard 增加 `page_window` 后端输出与前端消费链路标记
5. grouped semantic drift guard 增加 `page_window` 基线校验
6. contract evidence 导出补充 `grouped_pagination_contract.supports_page_window`
7. contract evidence schema guard 与 evidence guard 增加 `supports_page_window` 强约束
8. 增补一条 grouped pagination 语义说明文档（便于评审与后续扩展）
9. 执行 tree smoke + frontend quick gate + contract preflight 回归
10. 更新 v0.8-mini 进展并形成可合并 PR

## 提交节奏（约 10 个独立提交）

1. docs: v0.8-mini 计划
2. feat(contract): grouped rows 增加 page_window
3. feat(frontend): ListPage 消费 page_window
4. test(smoke): grouped signature 增加 page_window
5. test(guard): grouped_rows_runtime_guard 增加 page_window 标记
6. test(guard): grouped_pagination_semantic_drift_guard 增加 page_window 校验
7. feat(evidence): export_evidence 补充 supports_page_window
8. test(guard): contract evidence schema/guard 增强
9. docs: grouped pagination 语义说明
10. docs: v0.8-mini 进展 + 回归记录

## 验收口径

1. grouped 响应具备 `page_window`，前端成功消费且无兼容回归
2. `fe_tree_grouped_signature` 与 guard 全部通过
3. `phase11_1_contract_evidence` 包含 `supports_page_window` 且 guard 通过
4. 以下命令通过：
   - `make verify.portal.tree_view_smoke.container`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`

## 当前状态（2026-03-04）

- 已达成：目标 1-10 全部落地，进入可合并状态
- 当前分支累计独立提交：10（含 docs/test/feat 分层提交）

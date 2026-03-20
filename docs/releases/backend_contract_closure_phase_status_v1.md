# 后端契约收口阶段状态（Phase Status v1）

## 范围

- 目标阶段：Batch-E ~ Batch-N
- 主线目标：完成 P1/P2 契约收口，并固化防回归门禁。

## 已完成批次

- Batch-E：`system.init` 分层契约（`init_contract_v1`）
- Batch-F：`workspace_home` 按需加载（默认 `workspace_home_ref`）
- Batch-G：intent 目录独立化（`meta.intent_catalog` + `intent_catalog_ref`）
- Batch-H：capability 交付真实性字段（`delivery_level/target_scene_key/entry_kind`）
- Batch-I：`default_route` 语义补全（`scene_key/route/reason`）
- Batch-J：intent canonical/alias 可追溯体系
- Batch-K：`scene_governance_v1.surface_mapping` 差异做实
- Batch-L：scene 指标统一口径（四个统一字段）
- Batch-M：`workspace_home.blocks` block-first 结构
- Batch-N：后端契约收口防回归门禁（`verify.backend.contract.closure.guard`）

## 当前门禁状态

- 局部 guard：`python3 scripts/verify/backend_contract_closure_guard.py` PASS
- 前端严格类型：`pnpm -C frontend/apps/web typecheck:strict` PASS
- mainline 串联：已把 `verify.backend.contract.closure.guard` 接入 `verify.product.delivery.mainline`

## 下一步（建议）

- 在 CI 里将 `verify.product.delivery.mainline` 设为合并前必过。
- 增加 `meta.intent_catalog` 快照基线，监控 alias/canonical 漂移。
- 补一条回归规则：`default_route.reason` 只能取受控枚举。

# Contract Runtime Acceptance v1

## Scope
- 验证主题：Contract Runtime Verification v1（运行时一致性）
- 对象：`project.project` / `project.task` / `project.budget` / `project.cost.ledger` / `payment.request` / `sc.settlement.order`
- 角色：`owner` / `pm` / `finance` / `outsider`
- 表面：`list(tree)` + `form`

## Batch A 结论（运行时抓取）
- 已完成 48 条运行时样本抓取（4 角色 × 6 对象 × 2 表面）。
- 样本落盘：`docs/ops/contract_runtime_payload_samples_v1.json`。
- 抓取报告：`docs/ops/contract_runtime_capture_report_v1.md`。

## Batch B 结论（payload vs freeze）
- 冻结面中通用权限字段在样本内可得（`head.permissions.*`、`permissions.effective.rights.*`）。
- `op=model` 样本存在 runtime 字段系统性缺口（`can_create/can_edit/page_status`）。
- 已形成字段缺口、shape 差异、角色差异证据：`docs/ops/contract_runtime_freeze_compare_v1.md`。

## Batch C 结论（payload vs consumer）
- 前端基础依赖字段（model/view_type/rights）供给稳定。
- runtime/action 依赖字段在本批 `op=model` 样本不完整，存在 fallback 掩盖风险。
- 证据：`docs/ops/contract_runtime_consumer_compare_v1.md`。

## Runtime verdict
- 结论：`PASS`
- 说明：
  - `model-surface` contract 运行态一致性成立。
  - `scene-runtime-extension-surface` 已按 screen + dedicated capture 证据标注为 `intentional-not-in-surface`（当前 runtime baseline 下不作为根层必现项）。
  - `payment/settlement action-surface` 对称证据已完成收口（`ITER-2026-04-07-1316`）。

## Acceptance gate decision
- 当前阶段可判定：**静态基线 + model-surface 运行态** 已对齐。
- 当前阶段未判定：无。
- 后续变更必须引用 `docs/ops/contract_runtime_gap_list_v1.md` 并按修复通道推进。

# Baseline Freeze Policy

## 目的
- 冻结已稳定的基线链路，避免高频迭代阶段反复扰动 `verify/gate` 稳定性。
- 将迭代重心切换到业务能力增量，基线仅做 `P0` 修复。

## 冻结范围
- Scene observability 基线脚本与聚合命令。
- 与其直接绑定的 preflight/readiness 诊断脚本。
- 相关 gate 串联（`gate.full` 中的 observability 基线覆盖）。

说明：
- 冻结范围以 `scripts/verify/baselines/baseline_frozen_paths.json` 为唯一机器判定源。

## 允许的变更
- `P0` 级故障修复（阻塞 gate 或导致错误通过）。
- 安全/合规修复。
- 明确批准的例外变更（需在 PR 中说明原因与回滚方式）。

## 禁止的变更
- 无业务必要的重构。
- 无证据链的脚本行为改写。
- 将临时排障逻辑直接并入基线。

## 例外流程
1. 在 PR 描述中给出例外原因与影响面。
2. 提供回滚方案和验证命令。
3. 使用 `BASELINE_FREEZE_ALLOW=1` 执行一次 guard（仅限本次例外）。

## 执行命令
- 基线冻结 guard：
  - `make verify.baseline.freeze_guard`
- 例外执行（临时）：
  - `BASELINE_FREEZE_ALLOW=1 make verify.baseline.freeze_guard`

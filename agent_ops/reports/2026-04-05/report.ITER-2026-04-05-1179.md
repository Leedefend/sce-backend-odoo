# ITER-2026-04-05-1179

- status: PASS
- mode: execute
- layer_target: Governance Monitoring
- module: verify smoke stability
- risk: low
- publishability: internal

## Summary of Change

- 修复 `scripts/verify/scene_legacy_auth_smoke.py` 门禁语义：
  - `SCENE_LEGACY_AUTH_SMOKE_ALLOW_UNREACHABLE_FALLBACK` 默认值改为严格模式（`False`）。
  - 运行时不可达（timeout / connection refused / network unreachable / retries exhausted）且未显式开启 fallback 时，抛出包含 `base_url`、`endpoint`、原始异常文本的 `RuntimeError`。
  - 保留现有 401/403、error envelope、deprecation headers、`AUTH_REQUIRED/PERMISSION_DENIED` 校验。
- 新增原生语义验证脚本 `scripts/verify/scene_legacy_auth_smoke_semantic_verify.py`，覆盖：
  - runtime unreachable 默认 FAIL
  - 显式 fallback 时 PASS
  - 401/403 正常响应时 PASS
- 新增短门禁目标 `make verify.scene.legacy_auth.smoke.semantic`（不触发 CI 长链）。

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1179.yaml`: PASS
- `python3 scripts/verify/scene_legacy_auth_smoke_semantic_verify.py`: PASS
- `make verify.scene.legacy_auth.smoke.semantic`: PASS
- `SCENE_LEGACY_AUTH_SMOKE_ALLOW_UNREACHABLE_FALLBACK=true make verify.scene.legacy_auth.smoke`: PASS

## Risk Analysis

- 低风险：改动仅在 `scripts/verify/**` 与 `Makefile` 验证入口，未触达业务事实层代码。
- 预期行为变化：在 runtime 不可达且未显式开启 fallback 时，`make verify.scene.legacy_auth.smoke` 将严格 FAIL（符合门禁修复目标）。

## Rollback Suggestion

- `git restore scripts/verify/scene_legacy_auth_smoke.py`
- `git restore scripts/verify/scene_legacy_auth_smoke_semantic_verify.py`
- `git restore Makefile`
- `git restore agent_ops/tasks/ITER-2026-04-05-1179.yaml`

## Decision

- PASS
- next suggestion: 继续原生业务事实主线，进入下一个低风险阻塞点修复批次（保持短链 verify 策略）。

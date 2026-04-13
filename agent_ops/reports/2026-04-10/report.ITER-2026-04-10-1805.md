# ITER-2026-04-10-1805 Report

## Batch
- Batch: `FORM-Backend-R1`
- Mode: `implement`
- Stage: `action-specific form parser root path fix`

## Architecture declaration
- Layer Target: `Backend contract semantic layer`
- Module: `app.view.config parser routing`
- Module Ownership: `addons/smart_core`
- Kernel or Scenario: `kernel`
- Reason: action-specific form 被强制 fallback 解析，易导致结构收缩。

## Change summary
- 调整 `app_view_config._generate_from_fields_view_get` 路由：
  - 非 form 的 action-specific 仍可优先 fallback。
  - form 的 action-specific 改为 primary parser 优先，fallback 仅安全兜底。
- 增加 form surface 选择保护：
  - 当 action-bound form 比 runtime default form 更瘦时，优先采用 runtime default form。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1805.yaml` → `PASS`
- `rg -n "action-specific form view detected|prefer_richer_form_surface|runtime_default" addons/smart_core/app_config_engine/models/app_view_config.py` → `PASS`
- `make restart` → `PASS`

## Risk analysis
- 结论：`PASS`
- 风险级别：`medium`
- 风险说明：仅调整 form 解析路由与候选选择策略，不改业务模型。

## Rollback suggestion
- `git restore addons/smart_core/app_config_engine/models/app_view_config.py`

## Next suggestion
- 继续定位 user surface 页面丢失是否由治理层裁剪造成，并在不破坏权限语义前提下修正。

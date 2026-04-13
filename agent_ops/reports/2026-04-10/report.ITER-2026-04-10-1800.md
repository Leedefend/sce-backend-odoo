# ITER-2026-04-10-1800 Report

## Batch
- Batch: `FORM-Contract-RootFix-R3`
- Mode: `implement`
- Stage: `runtime-user-first form view retrieval`

## Architecture declaration
- Layer Target: `Backend contract semantic layer`
- Module: `app.view.config _safe_get_view_data`
- Module Ownership: `smart_core`
- Kernel or Scenario: `scenario`
- Reason: `sudo` 读取视图可能漏掉按用户组生效的 inherited form 视图，导致业务页签在 contract 缺失。

## Change summary
- 文件：`addons/smart_core/app_config_engine/models/app_view_config.py`
- 视图读取改为“runtime user 优先，sudo 回退”：
  - action-specific `get_view/fields_view_get`
  - 默认 `get_view`
  - fallback `fields_view_get`
- 保留原有容错能力：runtime user 失败时自动回退 `sudo`。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1800.yaml` → `PASS`
- `rg -n "ModelRuntime|ModelSudo|runtime user get_view|runtime user fields_view_get" addons/smart_core/app_config_engine/models/app_view_config.py` → `PASS`
- `make restart` → `PASS`
- `make frontend.restart` → `PASS`

## Risk analysis
- 结论：`PASS`
- 风险级别：`medium`
- 风险说明：不同用户组会得到不同 form 结构，符合原生行为但可能改变既有 contract 快照基线。

## Rollback suggestion
- 文件级回滚：
  - `git restore addons/smart_core/app_config_engine/models/app_view_config.py`
- 服务恢复：
  - `make restart && make frontend.restart`

## Next suggestion
- 以同一登录用户刷新 `structure_audit=1` 页面，验证业务 tab 是否进入 `views.form.layout`。

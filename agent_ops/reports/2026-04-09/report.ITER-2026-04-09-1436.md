# ITER-2026-04-09-1436 Report

## Batch
- Batch: `1/1`
- Mode: `implementation`

## Architecture declaration
- Layer Target: `Backend scene-orchestration semantic supply`
- Module: `api.data list param merge`
- Module Ownership: `smart_core handlers`
- Kernel or Scenario: `scenario`
- Reason: 修复 `api.data(list)` 搜索参数在运行链路中被吞掉的问题，恢复前端搜索到服务端过滤的语义映射。

## Root cause
- 参数合并链路存在双重问题：
  1. `_collect_params` 对内层 `params/payload` 使用“仅缺失才写入”，导致顶层空值可遮蔽真实入参；
  2. 标准搜索字段默认包含 `display_name`，在 `sc.dictionary` 上 `display_name ilike` 产生全匹配，导致搜索词无效化。

## Change summary
- 在 `api_data` 参数合并中加入“空值可被内层覆盖”规则（`None/空串/空集合`）。
- 标准搜索字段中剔除 `display_name`（以及从 `fields_safe` 注入时跳过），避免全匹配分支污染搜索结果。

## Changed files
- `addons/smart_core/handlers/api_data.py`

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1436.yaml` ✅
- `python3 -m py_compile addons/smart_core/handlers/api_data.py` ✅
- `make restart` ✅
- 运行态探针：`artifacts/playwright/iter-2026-04-09-1436/api_data_search_term_probe.json` ✅
  - `none=55`
  - `search_hit(系统)=1`
  - `search_miss(不存在关键字xyz)=0`
  - `domain_hit(name ilike 系统)=1`

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 风险说明：
  - 变更仅作用于 `api.data(list)` 搜索语义组装，不涉及 ACL/业务事实。
  - 运行态计数已与显式 domain 行为一致，修复目标达成。

## Rollback suggestion
- `git restore addons/smart_core/handlers/api_data.py`
- `git restore agent_ops/reports/2026-04-09/report.ITER-2026-04-09-1436.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-09-1436.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore artifacts/playwright/iter-2026-04-09-1436/api_data_search_term_probe.json`

## Next suggestion
- 开启 `1437`（verify）：复用 1435 的角色并行矩阵，验证搜索链路修复后在角色样本中的 UI/契约一致性，并补齐 outsider 可登录采样。

# ITER-2026-04-05-1120

- status: PASS
- mode: execute
- layer_target: Platform Layer
- module: smart_core.system_init
- risk: medium
- publishability: internal

## Summary of Change

- updated:
  - `addons/smart_core/core/system_init_extension_fact_merger.py`
  - `addons/smart_core/handlers/system_init.py`
  - `addons/smart_core/core/runtime_fetch_bootstrap_helper.py`
  - `agent_ops/tasks/ITER-2026-04-05-1120.yaml`
  - `agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1120.md`
  - `agent_ops/state/task_results/ITER-2026-04-05-1120.json`
  - `docs/ops/iterations/delivery_context_switch_log_v1.md`
- implementation:
  - `merge_extension_facts` 增加显式模式参数 `include_workspace_collections`，支持 startup/runtime 分离控制。
  - `system_init` 主链改为 `merge_extension_facts(data, include_workspace_collections=False)`，不再注入 task/payment/risk/project 重列表。
  - runtime fetch bootstrap 改为 `merge_extension_facts_fn(data, include_workspace_collections=True)`，保持工作台重列表在 runtime 路径可用。

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1120.yaml`: PASS
- `python3 -m py_compile addons/smart_core/core/system_init_extension_fact_merger.py addons/smart_core/handlers/system_init.py addons/smart_core/core/runtime_fetch_bootstrap_helper.py`: PASS
- `rg -n "merge_extension_facts\(data, include_workspace_collections=False\)" addons/smart_core/handlers/system_init.py`: PASS
- `rg -n "merge_extension_facts_fn\(data, include_workspace_collections=True\)" addons/smart_core/core/runtime_fetch_bootstrap_helper.py`: PASS
- `make verify.controller.boundary.guard`: PASS

## Risk Analysis

- medium: merge 行为从单一模式变为显式模式，若后续调用点未声明预期模式，可能出现 startup/runtime 行为差异。
- mitigated: 本批次已在主链与 runtime_fetch 两个关键入口分别固化参数，且通过边界门禁。

## Rollback Suggestion

- `git restore addons/smart_core/core/system_init_extension_fact_merger.py`
- `git restore addons/smart_core/handlers/system_init.py`
- `git restore addons/smart_core/core/runtime_fetch_bootstrap_helper.py`
- `git restore agent_ops/tasks/ITER-2026-04-05-1120.yaml`
- `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1120.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-05-1120.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- next stage suggestion: start dedicated audit task to enumerate all `merge_extension_facts` future callsites and enforce explicit mode selection guard.

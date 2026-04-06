# ITER-2026-04-05-1167

- status: FAIL
- mode: execute
- layer_target: Governance Monitoring
- module: smart_construction_core system.init extension hook
- risk: medium
- publishability: internal

## Summary of Change

- added compatibility hook `smart_core_extend_system_init` in `addons/smart_construction_core/core_extension.py`.
- ensured hook writes only into `data['ext_facts']` namespace and sources payload from `get_system_init_fact_contributions`.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1167.yaml`: PASS
- `make verify.backend.boundary_guard`: PASS
- `make ci.preflight.contract`: FAIL
  - failure gate: `verify.frontend.intent_channel.guard`
  - failure evidence: `frontend/apps/web/src/api/capabilityMatrix.ts` contains forbidden path `/api/contract/capability_matrix`

## Risk Analysis

- medium: backend boundary blocker is resolved, but preflight now reveals an upstream frontend intent-channel policy violation outside 1167 scope.
- repository stop rule triggered: required verify command failed.

## Rollback Suggestion

- `git restore addons/smart_construction_core/core_extension.py`
- `git restore agent_ops/tasks/ITER-2026-04-05-1167.yaml`
- `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1167.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-05-1167.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- stop required by policy: yes
- unblock suggestion: open dedicated frontend guard-remediation batch for `frontend_intent_channel_guard`, then rerun `make ci.preflight.contract`.


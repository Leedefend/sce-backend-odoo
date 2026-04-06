# ITER-2026-04-05-1164

- status: FAIL
- mode: execute
- layer_target: Governance Monitoring
- module: Makefile CI preflight wiring
- risk: medium
- publishability: internal

## Summary of Change

- created task contract and wired restricted default entry `ci.preflight.contract`
  to explicitly run `verify.architecture.capability_projection_governance_gate`
  before existing preflight checks.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1164.yaml`: PASS
- `make verify.architecture.capability_projection_governance_gate`: PASS
- `make ci.preflight.contract`: FAIL
  - failure gate: `verify.test_seed_dependency.guard`
  - failure evidence: `addons/smart_core/tests/test_action_dispatcher_server_mapping.py` contains `Missing demo` dependency pattern
- `make verify.controller.boundary.guard`: NOT RUN (stopped on previous verify failure)

## Risk Analysis

- medium: restricted default lane promotion is blocked by pre-existing CI preflight failure unrelated to this Makefile wiring.
- repository stop rule triggered: any required `make verify.*` failure requires immediate stop.

## Rollback Suggestion

- `git restore Makefile`
- `git restore agent_ops/tasks/ITER-2026-04-05-1164.yaml`
- `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1164.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-05-1164.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- stop required by policy: yes
- unblock suggestion: run dedicated verify batch to resolve `verify.test_seed_dependency.guard` failures first, then rerun 1164 acceptance.


# ITER-2026-04-05-1168

- status: FAIL
- mode: execute
- layer_target: Governance Monitoring
- module: frontend web api capability matrix fetch
- risk: medium
- publishability: internal

## Summary of Change

- migrated `frontend/apps/web/src/api/capabilityMatrix.ts` from direct contract path call to intent-channel call via `intentRequestRaw`.
- removed forbidden `/api/contract/capability_matrix` usage from web source and preserved matrix-shaped return payload.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1168.yaml`: PASS
- `make verify.frontend.intent_channel.guard`: PASS
- `make ci.preflight.contract`: FAIL
  - failure gate: `verify.scene.provider.guard`
  - failure evidence: `addons/smart_core/handlers/app_shell.py: scene_provider import is restricted to ['addons/smart_core/handlers/system_init.py']`

## Risk Analysis

- medium: target frontend intent-channel blocker is resolved, but restricted preflight now surfaces scene-provider guard violation outside 1168 frontend scope.
- repository stop rule triggered: required verify command failed.

## Rollback Suggestion

- `git restore frontend/apps/web/src/api/capabilityMatrix.ts`
- `git restore agent_ops/tasks/ITER-2026-04-05-1168.yaml`
- `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1168.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-05-1168.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- stop required by policy: yes
- unblock suggestion: open dedicated backend guard-remediation batch for `verify.scene.provider.guard` (app_shell scene_provider import boundary), then rerun `make ci.preflight.contract`.


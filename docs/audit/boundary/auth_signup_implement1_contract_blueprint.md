# auth_signup Implement-1 Contract Blueprint (ITER-2026-04-05-1038)

## Batch Objective

- execute first ownership handoff step at controller layer only.
- use delegation/shim strategy first, no policy/model migration in this batch.

## Proposed Contract Skeleton

### Task Meta
- type: `backend`
- mode: `implement`
- priority: `medium`
- depends_on: `ITER-2026-04-05-1037`

### Allowed Paths (Implement-1)
- `addons/smart_construction_core/controllers/auth_signup.py`
- `addons/smart_construction_core/controllers/__init__.py`
- target owner controller file under approved platform auth line (to be fixed in contract)
- `agent_ops/tasks/**`
- `agent_ops/reports/**`
- `agent_ops/state/task_results/**`
- `docs/ops/iterations/**`

### Forbidden Paths (carry-over hard lock)
- `security/**`
- `record_rules/**`
- `addons/**/security/**`
- `addons/**/__manifest__.py`
- financial domains (`*payment*`, `*settlement*`, `*account*`)

## Implementation Strategy

1. create target owner route-shell (or equivalent auth owner controller) with identical route signatures.
2. keep source controller as delegation shim (or remove route decorators only after parity is confirmed).
3. avoid changing signup policy internals in Implement-1.

## Required Acceptance Commands

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/<IMPLEMENT1_TASK>.yaml`
2. `python3 -m py_compile` for changed controller files
3. dedicated auth smoke check command (to be defined in task) for:
   - `/web/signup` reachability
   - `/sc/auth/activate/<token>` compatibility path

## PASS Criteria

- single active route owner after batch (or explicitly documented shim ownership).
- no change to signup behavior contract.
- compatibility anchors remain valid.
- no forbidden path touched.

## Rollback Recipe Template

- `git restore` all changed controller files
- `git restore` task/report/state/log artifacts of Implement-1
- re-run smoke check to confirm rollback integrity

## Stop Conditions

- target owner path ambiguity unresolved.
- need to modify ACL/security/manifest to proceed.
- compatibility check cannot be defined or fails.

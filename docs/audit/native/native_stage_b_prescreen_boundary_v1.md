# Native Stage-B Pre-Screen Boundary v1

## Objective

Define medium-risk execution boundaries for Stage-B extension work while preserving Phase 1/2 gains.

## Allowed Change Surface (Stage-B Execute Candidate)

1. Customer seed extension (non-transactional only)
   - `addons/smart_construction_custom/data/**`
   - `addons/smart_construction_custom/__manifest__.py` (append-only data load)

2. Evidence and governance tracking
   - `docs/audit/native/**`
   - `docs/ops/iterations/**`
   - `agent_ops/tasks/**`
   - `agent_ops/reports/**`
   - `agent_ops/state/task_results/**`

## Disallowed in Stage-B

- Any `security/**` expansion beyond already closed minimal scope
- Any `record_rules/**` or ACL broadening not tied to explicit high-risk contract
- Any payment/settlement/accounting transactional seed
- Any manifest dependency direction change
- Any frontend-specific branching logic

## Mandatory Gate Set (Stage-B Execute)

- `python3 agent_ops/scripts/validate_task.py <task.yaml>`
- `make verify.scene.legacy_contract.guard`
- `make verify.test_seed_dependency.guard`
- `make verify.scene.legacy_auth.smoke.semantic`

## Stage-B Execute Entry Criteria

1. Stage-A Batch1/2/3 evidence remains PASS.
2. Candidate change is non-transactional and additive.
3. File scope stays inside declared allowlist.

## Stop Criteria

- Gate failure on any mandatory command.
- Scope drift into forbidden files.
- Transactional/financial semantics introduced.

## Decision

- Stage-B can proceed as medium-risk only for controlled seed/dictionary extension.
- Any permission/record-rule expansion must open separate high-risk lane.

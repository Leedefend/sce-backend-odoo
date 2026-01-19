# P2 Gate & Audit Rules (Draft)

Scope: P2 execution control checks aligned with current gate/audit tooling.

## MUST
1) **No direct state writes**
- Rule: project.task, sc.settlement.order, payment.request `state` must only change via Transition API actions.
- Scriptable via:
  - unit tests that attempt direct write and expect guard error
  - extend `scripts/ci/assert_audit_tp08.py` to include state mutation checks

2) **Locked period blocks edits**
- Rule: project.cost.ledger create/write/unlink must fail when period is locked.
- Scriptable via:
  - add checks in `scripts/ci/gate_audit_tp08.sh` (call a validator test)

3) **execute_button must emit audit**
- Rule: all Transition API actions must write AuditRecord v1 with event_code, actor, ts, trace_id.
- Scriptable via:
  - `scripts/ops/audit_project_actions.sh` to export action coverage
  - `scripts/ci/assert_audit_tp08.py` to assert audit coverage for P2 actions

4) **Envelope shape enforced**
- Rule: execute_button responses must return `{ok,data,error}`; no raw action dicts.
- Scriptable via:
  - controller/service unit tests
  - static checks in `scripts/ci/assert_audit_tp08.py` (response schema list)

## SHOULD
1) **Audit reason for overrides/unlock/revert**
- Rule: when override/unlock/revert occurs, reason must be non-empty.
- Scriptable via:
  - targeted unit tests (expected reason field)

2) **WBS required before cost allocation**
- Rule: cost allocation blocked without WBS linkage.
- Scriptable via:
  - validator checks in cost ledger creation tests

## OPTIONAL
1) **Trace-id correlation**
- Rule: audit trace_id should match request_id when available.
- Scriptable via:
  - log correlation checks (optional, warnings only)

2) **Read-only intent audit**
- Rule: api.data reads may be logged for sensitive models.
- Scriptable via:
  - add read audit hooks if needed

## Gate Hooks (Current)
- `scripts/ci/gate_audit_tp08.sh` (calls `make audit.project.actions` and `scripts/ci/assert_audit_tp08.py`)
- `scripts/ops/audit_project_actions.sh` (exports audit CSVs to `docs/audit/`)

Notes:
- Gate rules must remain translatable to scripts; avoid non-testable language.

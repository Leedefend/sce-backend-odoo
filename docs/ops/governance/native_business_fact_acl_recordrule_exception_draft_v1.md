# Narrow Exception Draft v1

## Objective

Authorize a dedicated high-risk batch for native business-fact remediation limited to:

1. Removing duplicate ACL row(s) for `project.budget`.
2. Adding minimal record rules for project/task/budget/cost-ledger closure.

This draft is proposal-only and does not authorize implementation by itself.

## Proposed Exception Name

`Dedicated Native Business-Fact ACL and Record-Rule Closure Batch`

## Required Preconditions

- Active task contract explicitly declares this objective.
- User has explicitly authorized high-risk execution.
- The task allowlist includes exact target files only.
- Changes are additive/minimal and limited to closure goals above.

## Exact Path Allowlist (proposed)

- `addons/smart_construction_core/security/ir.model.access.csv`
- `addons/smart_construction_core/security/sc_record_rules.xml`
- `docs/audit/native/native_foundation_blockers_v1.md`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`
- `agent_ops/tasks/**`
- `agent_ops/reports/**`
- `agent_ops/state/task_results/**`

## Out-of-Scope

- `security/**` beyond the exact two files above
- `__manifest__.py`
- financial semantics and accounting logic
- frontend and scene rendering changes
- migration scripts

## Mandatory Verification in Same Batch

- `python3 agent_ops/scripts/validate_task.py <task.yaml>`
- `make verify.scene.legacy_auth.smoke.semantic`
- `make verify.scene.legacy_contract.guard`

## Immediate Stop Conditions

- Any path outside allowlist is touched.
- ACL scope expands beyond `project.budget` duplicate cleanup.
- record-rule logic exceeds minimal closure intent.
- Any verify command fails.

## Decision Note

- If approved, next batch should be `execute` mode and high-risk.
- If not approved, execution remains blocked on step-5/6.

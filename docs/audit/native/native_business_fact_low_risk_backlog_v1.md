# Native Business-Fact Low-Risk Backlog v1

## Entry Condition

- Current composite gate (`make verify.native.business_fact.stage_gate`) is PASS.
- Lane remains low-risk evidence/verify only.

## Executable Queue

| Priority | Task | Type | Suggested Command Pack |
|---|---|---|---|
| P0 | Runtime auth-gate stability sampling (N runs) | verify/evidence | `for i in 1 2 3; do make verify.native.business_fact.stage_gate; done` |
| P1 | Dictionary seed diff drift check against required types | verify/evidence | `python3 scripts/verify/native_business_fact_dictionary_completeness_verify.py` |
| P1 | Menu-action openability drift check after view/action edits | verify/evidence | `python3 scripts/verify/native_business_fact_action_openability_verify.py` |
| P2 | Weekly checkpoint refresh | governance | Update `native_business_fact_gate_dashboard_v1.md` + run stage gate |
| P2 | Pre-high-risk readiness proof pack | governance | bundle latest PASS outputs + blocker note |

## Stop Escalation Boundary

Stop low-risk queue and open dedicated high-risk contract if task needs:
- `security/**`
- `record_rules/**`
- `ir.model.access.csv`
- `__manifest__.py`

## Operator Note

Prefer running the one-shot gate first each round, then only run targeted sub-checks for drift isolation.

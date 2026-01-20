# P3 Contracts v0.1

Tag: `p3-contracts-v0.1`

Scope: reconciliation contract + audit query + gate draft (spec-only).

Docs:
- `docs/p3/p3_scope_boundary_v0.1.md`
- `docs/p3/p3_capability_map_v0.1.md`
- `docs/p3/p3_data_contract_v0.1.md`
- `docs/p3/p3_audit_query_contract_v0.1.md`
- `docs/p3/p3_gate_rules_v0.1.md`
- `docs/p3/p3_issues_v0.1.md`

Gate:
- `make ci.gate.tp08 DB=sc_demo` (PASS)

Next:
- P3 runtime R1: reconciliation summaries + minimal audit query + smoke baseline
- P3 runtime R2: consistency rules + audit gap fill
- P3 runtime R3: p3.smoke + p3.gate scripts + CI integration

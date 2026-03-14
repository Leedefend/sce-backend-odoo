# Native View Ecosystem Coverage Target v1

## Goal
Upgrade from “sample-level pass” to “ecosystem-level full coverage” as a hard backend-contract gate before broad frontend iteration.

## Scope
- View types: `form`, `tree`, `kanban`, `search`
- Contract surfaces: `native_view`, `semantic_page`, `actions`, `permission_verdicts`, `action_gating`
- Governance chain: `verify.contract.preflight`, `verify.phase_next.evidence.bundle`

## Ecosystem-Level Definition
All conditions below must be satisfied:

1. Sample coverage
- Cover `20+` model samples across at least `6` domains (project, task, contract, cost, finance, collaboration/attachment).
- At least `4` samples per view type (`form/tree/kanban/search`).

2. Structural completeness
- `semantic_page` must pass both `shape + schema` guards.
- `search_semantics` must include `filters/group_by/search_fields/search_panel/favorites/quick_filters`.
- `kanban_semantics` must include `title_field/card_fields/metric_fields`.
- `x2many` relation contract must include `items + editable + row_actions`.

3. Action/permission closure
- `permission_verdicts` keys are complete: `read/create/write/unlink/execute`.
- `action_gating` must include `record_state/policy/verdict`.
- Row/card actions must include `enabled + reason_code`.

4. Evidence-chain integration
- `native_view_semantic_guard` must be present in `phase11_1_contract_evidence.json`.
- `backend_evidence_manifest` summary must include:
  - `native_view_semantic_shape_ok`
  - `native_view_semantic_schema_ok`

## Exit Criteria (Go/No-Go)
- `verify.native_view.semantic_page`: PASS
- `verify.native_view.coverage.report`: PASS
- `verify.native_view.samples.compare`: PASS
- Ecosystem sample readiness report shows:
  - `total_case_count >= 20`
  - `ready_case_count == total_case_count`
  - `pass_ratio == 1.0`

After all criteria are met, proceed to “frontend deep productization iteration”.


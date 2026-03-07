# Odoo Native View Contract Gap - P1 Progress (2026-03-07)

## Scope
- Branch: `feat/interaction-core-p1-mini-v0_1`
- Focus: verify whether P1 gaps in the baseline assessment are now closed by enforceable guards.

## P1 Baseline Items
From `odoo_native_view_contract_gap_assessment_2026-03-03.md`, P1 includes:
1. Dual form-engine split (`RecordView` vs `ContractFormPage`)
2. x2many semantic gap
3. Search contract consumption gap (`group_by/saved_filters`)

## Evidence (Executed)
1. `make verify.frontend.search_groupby_savedfilters.guard` -> PASS
2. `make verify.frontend.x2many_command_semantic.guard` -> PASS
3. `make verify.frontend.view_type_render_coverage.guard` -> PASS
4. Router guard baseline check:
- `/f/:model/:id` -> `ContractFormPage`
- `/r/:model/:id` -> `ContractFormPage`
- forbidden token `component: RecordView` guarded by `scripts/verify/frontend_contract_route_guard.py`

## Current Judgement
- P1 item #1 (dual form-engine route split): **closed at routing contract level**.
- P1 item #2 (x2many semantic wiring): **guarded and passing**.
- P1 item #3 (search group_by/saved_filters consumption): **guarded and passing**.

## Residual Risk
- P1 is currently guarded by source-level/runtime-smoke style checks; higher-level behavior parity still depends on continued E2E maintenance.
- Remaining major risk center is now primarily P0/P2 long-tail areas rather than the three P1 baseline items.

## Next Step
- Keep P1 guards in preflight and proceed to next unresolved gap set (P0 long-tail / evidence hardening) without reopening P1 scope.

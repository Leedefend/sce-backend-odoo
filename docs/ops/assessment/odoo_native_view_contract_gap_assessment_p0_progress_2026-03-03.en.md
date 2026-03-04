# Odoo Native View Compatibility Assessment (P0 Progress)

中文版: [odoo_native_view_contract_gap_assessment_p0_progress_2026-03-03.md](./odoo_native_view_contract_gap_assessment_p0_progress_2026-03-03.md)

Date: 2026-03-03
Scope: `smart_core` contract pipeline + `frontend/apps/web` interaction runtime

## 1. Verdict (Can we fully carry native Odoo now?)

Verdict: **Not fully yet**, but P0 closed the critical interaction core loops. The system moved from “static usable” to “interactive core usable”.

- Completed: minimal runtime `modifiers`, frontend-backend `onchange` roundtrip, unified form entry path.
- Missing: x2many native command semantics, advanced view interactions (pivot/graph/calendar/gantt), broader attrs parity and cross-model consistency.

## 2. Delivered in P0

### 2.1 Modifier Engine (Frontend)

Implemented in:
- `frontend/apps/web/src/app/modifierEngine.ts`
- `frontend/apps/web/src/pages/ContractFormPage.vue`

Current capabilities:
- Runtime field state: `invisible` / `readonly` / `required`
- Expression support: `|` `&` `!` + domain-like tuples
- Render layer now reacts to modifier state dynamically

### 2.2 Onchange Roundtrip (Backend + Frontend)

Implemented in:
- Backend: `addons/smart_core/handlers/api_onchange.py`
- Frontend API: `frontend/apps/web/src/api/onchange.ts`
- Frontend wiring: `frontend/apps/web/src/pages/ContractFormPage.vue`

Current capabilities:
- Field change triggers debounced (300ms) `api.onchange`
- Backend returns `patch` / `modifiers_patch` / `warnings`
- Frontend merges patch into form state and refreshes relation options for domain updates

### 2.3 Single Form Engine Entry Convergence

Implemented in:
- `frontend/apps/web/src/router/index.ts`

Current capabilities:
- Both `/f/:model/:id` and `/r/:model/:id` use `ContractFormPage`
- Entry-level behavior drift between two form routes is removed

### 2.4 Regression Guards

Implemented in:
- `scripts/verify/modifiers_runtime_guard.py`
- `scripts/verify/onchange_roundtrip_guard.py`
- `Makefile` integration into `verify.frontend.quick.gate`

## 3. Remaining Gaps vs Native Odoo

### 3.1 x2many semantics gap (High)

Current many2many/one2many UX is still simplified and does not implement native Odoo command semantics:
- missing `(0,0,vals)/(1,id,vals)/(2,id)/(6,0,ids)` command lifecycle
- missing inline subview editing, row-level validation, draft command buffering

Impact: complex line editing, row-level onchange, and row-level ACL behavior remain non-native.

### 3.2 Modifier semantic coverage still minimal (Medium-High)

Stable only for `invisible/readonly/required` now.

Still needed:
- container/group/page-level modifiers
- broader expression edge-case parity
- deterministic conflict resolution with policy layers

### 3.3 Onchange contract hardening (Medium)

`api.onchange` is functional but should be hardened by:
- explicit schema contract for patch/domain/warning
- model-focused regressions (project/task/contract/cost/risk)
- performance strategy for large forms (field subset/incremental payload/observability)

### 3.4 Dual-engine code still exists (Medium)

Route is converged, but `RecordView` code still exists.

Recommended:
- downgrade `RecordView` to diagnostic-only or remove
- extract reusable `FormCore` for state/actions/modifiers/onchange

## 4. Capability Rating (as of 2026-03-03)

- Form rendering and action carrying: **A-**
- Native interaction parity (attrs/onchange/x2many): **B-**
- View system completeness (pivot/graph/calendar/gantt): **C**
- Regression/governance readiness: **B+**

Overall: **B (good for core business progress, not yet full native parity)**

## 5. Systematic Next Steps

1. P1: x2many command semantic layer first, then UI layer
2. P1: read-only renderers for pivot/graph/calendar/gantt
3. P1: container-level modifiers + precedence/conflict rules
4. P2: expand regression matrix to 20+ scenes across key domains

## 6. Validation Evidence in This Iteration

- `npm run typecheck` (frontend/apps/web) passed
- `npm run build` (frontend/apps/web) passed
- `make verify.frontend.quick.gate` passed (including new guards)
- `make verify.portal.dashboard` passed

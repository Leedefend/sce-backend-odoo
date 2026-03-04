# Odoo Native View-System Coverage Assessment (Contract/Frontend End-to-End)

Date: 2026-03-03  
Scope: backend `ui.contract` pipeline + portal frontend rendering/interaction pipeline.

## 1. Executive Summary

Conclusion: **the current contract stack does NOT fully carry native Odoo view system behavior and interaction logic**. It reliably carries a narrowed product subset.

- Stable subset today:
  - basic `tree/list + kanban + form` data surfaces
  - basic field editing (partial type coverage)
  - button execution (`execute_button`)
  - basic search filters (`search.filters`)
- Major gaps:
  - no runtime frontend execution of native `attrs/modifiers`
  - no complete `onchange` loop (backend entry exists, frontend not wired; gateway model appears missing)
  - incomplete x2many native semantics (command protocol / inline subview editing)
  - no full frontend rendering chain for pivot/graph/calendar/gantt/activity/dashboard
  - dual form engines (`RecordView` vs `ContractFormPage`) with semantic drift risk

## 2. Evidence Highlights

- Backend supports rich form parsing blocks (`header_buttons/button_box/stat_buttons/field_modifiers/subviews/chatter/attachments`):
  - `addons/smart_core/app_config_engine/models/app_view_config.py` (form block assembly)
- Frontend Action surface effectively branches to `kanban` or `tree` only:
  - `frontend/apps/web/src/views/ActionView.vue` (view mode branch)
- `onchange` operation path references `app.action.gateway`, but model definition is absent in repository:
  - dispatcher reference: `addons/smart_core/app_config_engine/services/dispatchers/action_dispatcher.py`
  - `_name = 'app.action.gateway'` not found in `addons/**.py`
- Modifiers extracted backend-side but not consumed frontend-side:
  - extraction: `addons/smart_core/app_config_engine/services/view_Parser/base.py`
  - no `field_modifiers/modifiers` usage in `frontend/apps/web/src/**`

## 3. Gap Severity

### P0
1. Missing runtime modifier engine (`attrs/modifiers`).
2. Missing onchange closed-loop (frontend + gateway model implementation).
3. View-type rendering gap beyond list/kanban/form flows.

### P1
1. Dual form engine divergence.
2. Weak x2many semantics compared to native Odoo.
3. Search contract fields (`group_by/saved_filters`) not consumed.

### P2
1. Contract/scene sample breadth remains limited for “native-equivalence” claims.

## 4. Systemic Remediation Plan

### Phase A (2-3 weeks)
- Implement frontend modifier runtime engine.
- Implement/restore `app.action.gateway` + frontend onchange wiring.
- Unify form runtime between `RecordView` and `ContractFormPage`.

### Phase B (2-4 weeks)
- Add dedicated pivot/graph/calendar/gantt renderers.
- Add x2many command-semantic layer.
- Add many2one search-more/create-edit/context-domain runtime behavior.

### Phase C (continuous)
- Expand contract/scene snapshot coverage across core domains.
- Add guards for modifier runtime, onchange roundtrip, view-type render coverage, x2many semantics.

## 5. Final Position

Current platform is a **contract-driven portal implementation**, not a full equivalent replacement of native Odoo web client behavior. To claim full native coverage, P0 gaps must be closed first.

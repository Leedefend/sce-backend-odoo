# v1.0 Workbench Backend Convergence Refactor Report (Current Round)

## 1. Goal and Scope

This round finalizes backend convergence refactor for `portal.dashboard` on `release/construction-system-v1.0`, shifting the workspace home from a "capability summary page" to a "business action hub".

Boundary constraints followed:

- No changes to login flow, ACL baseline, scene governance, or delivery policy core mechanisms.
- `page_orchestration_v1` remains the primary protocol.
- `page_orchestration` is retained for legacy compatibility.

## 2. Key Modified Files

- `addons/smart_core/core/workspace_home_contract_builder.py`
- `addons/smart_core/core/workspace_home_data_provider.py`
- `addons/smart_construction_core/core_extension.py`
- `addons/smart_construction_demo/__manifest__.py`
- `addons/smart_construction_demo/data/scenario/s10_contract_payment/25_workbench_actions.xml`
- `scripts/verify/workbench_extraction_hit_rate_report.py`
- `docs/product/workbench_purpose_and_model_v1.md`
- `docs/product/workbench_purpose_and_model_v1.en.md`
- `docs/product/workbench_product_acceptance_checklist_v1.md`
- `docs/product/workbench_product_acceptance_checklist_v1.en.md`
- `docs/demo/demo_data_round_2_plan.md`
- `docs/demo/demo_data_round_2_plan.en.md`
- `docs/releases/workbench_visibility_diagnosis_v1.md`
- `docs/releases/workbench_visibility_diagnosis_v1.en.md`

## 3. Structural Contract Changes (Before vs After)

### 3.1 Protocol ownership is explicit

- Added `contract_protocol.primary=page_orchestration_v1`.
- `page_orchestration` is explicitly marked as `legacy.compatibility`.

### 3.2 Homepage semantics: from capability-first to action-first

- `today_actions` evolved from pure capability mapping to:
  - business-action-first extraction (tasks/approvals/risks),
  - capability fallback when business data is insufficient.
- `risk.actions` follows the same business-first strategy with locked-capability fallback.
- Added `project_actions` as a PM-visible factual source to close PM workbench action gaps.

### 3.3 Metric separation

- `metrics`: business operational metrics (action pressure, risk load, execution status).
- `platform_metrics`: platform capability counts (ready/locked/preview/scene).
- Diagnostic/platform details are separated into `diagnostics`.
- Hit-rate metrics now use dual views:
  - `business_rate` (semantic business)
  - `factual_rate` (factual record)

### 3.4 Core four-zone shell remains stable

The four main zones are kept unchanged: `hero / today_focus / analysis / quick_entries`.

## 4. Product Expression Outcome

- Workspace subtitle changed to action-oriented wording: `先处理行动项，再关注风险与总体状态`.
- `hero` is downgraded to supporting context (provider-side priority reduction).
- A clearer action flow is formed: action first, then risk, then status, then entry.

## 5. Compatibility Notes

- Legacy consumers can still read `page_orchestration`.
- New frontend path remains on `page_orchestration_v1`.
- No changes to authentication, permission, governance, or delivery core paths.

## 6. Regression Verification

- `make verify.frontend.build`: PASS
- `make verify.frontend.typecheck.strict`: PASS
- `make verify.project.dashboard.contract`: PASS
- `make verify.phase_next.evidence.bundle`: PASS (under `ENV=test + .env.prod.sim`)
- `make verify.workbench.extraction_hit_rate.report`: PASS

## 7. Visibility Evidence and Fix Proof (Permission vs Ownership)

Based on `docs/releases/workbench_visibility_diagnosis_v1.en.md`:

- Root cause was factual-source visibility scarcity for PM (permission + demo ownership), not frontend rendering.
- Fix respected boundaries: no ACL baseline changes; PM-visible factual sources + demo backfill only.

Post-fix (`artifacts/backend/workbench_extraction_hit_rate_report.md`):

- `pm`: `today_factual_rate=83.33%`, `risk_factual_rate=100%`
- `finance`: `today_factual_rate=100%`, `risk_factual_rate=100%`
- `owner`: `today_factual_rate=100%`, `risk_factual_rate=100%`

## 8. Known Risks and Next Actions

### Risks

- Business data keys may differ across tenants/environments; extraction hit rate needs ongoing observation.

### Next round recommendations

1. Add an extraction hit-rate report by role and scene.
2. Standardize HUD exposure for `diagnostics` to prevent debug leakage into user view.
3. Add urgency factors (overdue/near-due) into `today_actions` ordering.

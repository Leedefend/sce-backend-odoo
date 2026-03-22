# Existing Implementation Risk Scan - Phase 16-B

## Scope
- Scan the current workspace for business-expansion work that conflicts with native alignment.
- This scan includes uncommitted work-in-progress because it still represents implementation risk.

## Summary
- Overall result: `blocked`
- Primary risk: the current payment slice draft is expanding through a `project.payment.*` shadow scene family instead of reusing native finance entry points.

## Findings

### High: Project-scoped payment scene family bypasses native finance anchor
- Evidence:
  - `addons/smart_construction_core/handlers/project_payment_enter.py`
  - `addons/smart_construction_core/handlers/project_payment_block_fetch.py`
  - `addons/smart_construction_core/handlers/project_payment_ensure_single.py`
  - `addons/smart_construction_core/services/project_payment_service.py`
  - `addons/smart_construction_core/services/project_payment_builders/project_payment_next_actions_builder.py`
  - `addons/smart_construction_core/services/project_payment_builders/project_payment_record_builder.py`
- Why this is risky:
  - it creates a finance-facing scene family under `project.*`
  - it encourages project-side duplication of finance records and actions
  - it makes orchestration own record creation policy instead of delegating to native finance flow
- Required correction:
  - route project next actions to native finance scene
  - keep project side as readiness / deep-link layer only

### High: Execution flow is being coupled to custom payment implementation
- Evidence:
  - `addons/smart_construction_core/services/project_execution_builders/project_execution_next_actions_builder.py`
  - `frontend/apps/web/src/views/ProjectManagementDashboardView.vue`
- Why this is risky:
  - execution next actions are becoming aware of a custom finance scene instead of a native finance target
  - dashboard begins to accumulate finance-specific rendering branches
- Required correction:
  - execution should expose a native finance handoff action
  - frontend should consume generic orchestration hints, not custom payment record rendering

### Medium: Custom smoke path is freezing the wrong product direction
- Evidence:
  - `scripts/verify/product_project_payment_flow_smoke.py`
  - `Makefile`
- Why this is risky:
  - once a custom flow smoke exists, later iterations tend to stabilize the wrong surface
  - the smoke currently validates `execution -> project.payment -> ensure_single`
- Required correction:
  - replace with native-handoff smoke after the corrected direction is approved

## Non-Findings
- Existing `payment.request`, `construction.contract`, `project.budget`, `project.cost.ledger`, and `account.move` usage remains valid as native/business carriers.
- The correction target is orchestration direction, not removal of all custom business models already settled in the repo.

## Decision
- Do not continue the current `project.payment.*` implementation path.
- Use it as a negative sample for gate rules and redesign.

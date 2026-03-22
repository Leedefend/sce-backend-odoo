# Product Project Creation Mainline Baseline v1

## Objective
- freeze the new stable baseline for project creation without reopening architecture ambiguity

## Mainline Split
- `projects.intake`
  - role: navigation/native-form scene
  - purpose: route user into the native create form experience
  - ownership: frontend scene/navigation layer
- `project.initiation.enter`
  - role: business creation truth
  - purpose: create the project record and hand off to the next product step
  - ownership: product/domain handler layer

## Frozen Mainline
1. user opens `projects.intake`
2. frontend routes into native project create form
3. business creation executes through `project.initiation.enter`
4. success handoff points to `project.dashboard.enter`
5. `contract_ref` remains `ui.contract` menu-first, model fallback only when menu target is unavailable

## Frontend Baseline
- `projects.intake` may only remain in:
  - `frontend/apps/web/src/views/ProjectsIntakeView.vue`
  - `frontend/apps/web/src/pages/ContractFormPage.vue`
- all project-creation scene/menu/intent identifiers must be sourced from shared constants

## Product Baseline
- `project.initiation.enter` must keep:
  - `suggested_action_payload.intent = project.dashboard.enter`
  - `contract_ref.intent = ui.contract`
  - `contract_ref.params.scene_key = project.dashboard`

## Verify
- `make verify.product.project_creation_mainline_guard`
- `make verify.product.project_initiation.full DB=sc_demo`
- `make verify.product.project_flow.initiation_dashboard DB=sc_demo`
- `make verify.product.v0_1_stability_baseline DB=sc_demo`

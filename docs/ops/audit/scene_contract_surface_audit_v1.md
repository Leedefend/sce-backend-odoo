# Scene Contract Surface Audit v1

## Scope

Released surface only:

- `projects.intake`
- `project.dashboard`
- `project.plan_bootstrap`
- `project.execution`
- `cost.tracking`
- `payment`
- `settlement`
- `my_work.workspace`

Product review mapping:

- FR-1: `projects.intake`
- FR-2: `project.dashboard` / `project.plan_bootstrap` / `project.execution`
- FR-3: `cost.tracking`
- FR-4: `payment`
- FR-5: `settlement`
- Utility: `my_work.workspace`

## Runtime Facts

Audit date: `2026-03-24`

Probe facts:

- live login: `demo_pm / demo`
- db: `sc_prod_sim`
- release gate base: `http://127.0.0.1`
- sample project id during audit: `164`

## Surface Classes

### 1. Route-only product entry

`projects.intake`

Actual runtime fact:

- released by `delivery_engine_v1.scenes`
- routed to `/s/projects.intake`
- frontend product page, not backend `*.enter` payload

Current shape:

- has route
- has product/capability binding
- does not have backend runtime `blocks/runtime_fetch_hints`

Conclusion:

- FR-1 must be standardized as a released route-entry contract, not forced into the same provider shape as lifecycle entry intents

### 2. Lifecycle entry intents

`project.dashboard` / `project.plan_bootstrap` / `project.execution` / `cost.tracking` / `payment` / `settlement`

Actual runtime fact:

- all returned by `*.enter`
- all have near-isomorphic payload shape

Observed top-level keys:

- `project_id`
- `scene_key`
- `scene_label`
- `state_fallback_text`
- `title`
- `summary`
- `blocks`
- `suggested_action`
- `runtime_fetch_hints`

Observed block behavior:

- blocks are placeholders for deferred runtime fetch
- block metadata is stable enough for standardization
- `suggested_action.reason_code` already carries release-state semantics

Conclusion:

- FR-2 to FR-5 can share one additive runtime adapter without rewriting existing orchestrators

### 3. Page-contract scene

`my_work.workspace`

Actual runtime fact:

- loaded through `page.contract`
- current page payload does not expose released scene contract directly
- main render carrier is `page_orchestration_v1`

Observed top-level keys:

- `schema_version`
- `texts`
- `sections`
- `page_orchestration_v1`

Conclusion:

- `my_work.workspace` must be standardized by wrapping `page.contract`, not by pretending it is a `*.enter` intent

## Field Classification

### Must Keep

- `scene_key`
- `title`
- `project_id` when project context is required
- `blocks`
- `runtime_fetch_hints.blocks`
- `suggested_action`
- `page_orchestration_v1` for page-contract scenes
- product/capability binding from `delivery_engine_v1.scenes`

### Compatibility Keep

- `scene_label`
- `summary`
- `state_fallback_text`
- legacy delivery scene fields:
  - `label`
  - `route`
  - `requires_project_context`
  - `state`

### Should Retire From Frontend Assumptions

- treating released scenes as one uniform provider type
- assuming every released scene is a backend `*.enter` payload
- hardcoding release entry copy without consulting released scene contract
- reading page layout only from ad hoc local constants when a standard released scene contract exists

## Frontend Implicit Dependencies Found

- `ReleaseProductEntryView.vue` used hardcoded product title/description
- `ProjectsIntakeView.vue` is still a static product page
- `ProjectManagementDashboardView.vue` uses `currentSceneKey` branches and runtime block hints directly
- `pageContract.ts` still reads legacy `scene_contract_v1` / `page_orchestration_v1` compatibility paths

## Audit Conclusion

Released scenes are already product-governed, but not yet scene-contract-governed.

The correct standardization strategy is:

1. keep existing business providers
2. add a released scene contract adapter
3. attach standard contract to delivery exposure and runtime payloads
4. move frontend release-entry consumption onto the standard contract first

This is an additive standardization batch, not a business-slice rewrite.

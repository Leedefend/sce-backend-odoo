# Frontend Semantic Inference Screen V1

## Purpose

This screen audits the remaining frontend logic that still reconstructs
business/scenario meaning instead of consuming explicit backend contract
semantics.

The boundary used for this screen is:

- platform transport carries identity
- platform generic governance shapes neutral contract
- scenario override injects scenario semantics
- frontend only consumes explicit semantics

## Scope

This batch only screened bounded frontend hotspots:

- `frontend/apps/web/src/pages/ContractFormPage.vue`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue`
- `frontend/apps/web/src/views/ActionView.vue`
- `frontend/apps/web/src/pages/ModelListPage.vue`

This was sufficient to classify the current high-value residuals without
opening an unbounded repo-wide scan.

## Findings

### Finding 1: `ContractFormPage` still keeps route-based intake fallback

Location:

- `frontend/apps/web/src/pages/ContractFormPage.vue:800`
- `frontend/apps/web/src/pages/ContractFormPage.vue:806`
- `frontend/apps/web/src/pages/ContractFormPage.vue:819`
- `frontend/apps/web/src/pages/ContractFormPage.vue:989`

Current fact:

- the page first reads `form_governance.create_flow_mode`
- but if that field is absent, it still falls back to:
  - `model === "project.project"`
  - `recordId` absent
  - `route.query.intake_mode === "quick"`
  - `route.query.scene_key === "projects.intake"`

Impact:

- frontend still owns residual project-intake scenario inference
- autosave scope and button behavior can still be decided from route state
  instead of contract semantics

Boundary judgment:

- this is a true contract-boundary violation
- the fallback branch should not survive long-term once backend scene
  governance exists

Required owner:

- `scene-orchestration / scenario override`

Required next fix:

- backend must always emit explicit create-flow semantics for every supported
  project intake create mode
- frontend should delete the route-based fallback after semantic supply is
  complete

### Finding 2: dashboard summary is still scene-key branching in frontend

Location:

- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:527`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:529`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:541`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:553`

Current fact:

- `summaryRows` is assembled by frontend branches such as:
  - `currentSceneKey === "cost.tracking"`
  - `currentSceneKey === "payment"`
  - dashboard default branch
- each branch chooses different labels and field mappings locally

Impact:

- frontend is acting as a scenario summary assembler
- different scene summaries are encoded in Vue instead of arriving as scene
  semantics

Boundary judgment:

- this is a high-value frontend overreach
- the issue is not transport; it is missing scenario-ready summary semantics

Required owner:

- `scene-orchestration layer`

Required next fix:

- backend should emit scene-ready summary descriptors/rows for dashboard scenes
- frontend should render the supplied descriptors instead of branching on
  `currentSceneKey`

### Finding 3: dashboard still aliases business facts locally

Location:

- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:555`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:576`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:589`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:1145`

Current fact:

- frontend still merges business fields through alias chains such as:
  - `execution_stage_label || stage_label || summary.stage_name`
  - `project_condition || status`
  - `execution_stage_explain || stage_explain`
  - `project_condition_explain || status_explain`

Impact:

- frontend is compensating for unclear business-fact and scene-field ownership
- "项目执行阶段" and "单据/状态类语义" can still be blurred locally

Boundary judgment:

- this is a contract clarity problem
- the frontend should not decide synonym precedence for business vocabulary

Required owner:

- primary: `business-fact layer`
- secondary: `scene-orchestration layer`

Decision rule:

- if the missing field is real business truth, fix business-fact supply first
- if the missing field is only scene-ready wording/organization, fix
  scene-orchestration supply

Required next fix:

- standardize one explicit field set for:
  - project execution stage
  - project condition / document state
  - explain text
- remove frontend synonym fallback once the canonical field set is supplied

### Finding 4: dashboard keeps fallback business copy in frontend

Location:

- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:522`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:581`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:589`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:607`

Current fact:

- frontend still emits fallback copy such as:
  - `项目场景`
  - `查看当前项目阶段与里程碑`
  - `查看当前项目执行阶段`
  - `查看当前项目情况`
  - `区块按需加载。`

Impact:

- some of these are harmless presentation placeholders
- but scene/business-facing copy can hide contract underspecification

Boundary judgment:

- neutral UI placeholders are acceptable
- business/scenario descriptive copy should come from backend when it carries
  meaning

Required owner:

- `scene-orchestration layer` for meaningful scene copy
- frontend may keep purely neutral technical placeholders

Required next fix:

- classify which copy is semantic and which copy is neutral chrome
- move semantic copy supply to backend scene contract

## Non-Finding / Not Current Priority

### `ActionView`

Observed facts:

- `ActionView` still reads `action_id`, `menu_id`, `scene_key`, and
  `scene_label` from route/query
- current high-value usages in this screen are mainly entry identity resolution
  and navigation continuity
- batch delete and record-open behavior already moved to explicit
  `surface_policies`

Judgment:

- this file is not the primary semantic-overreach hotspot in the current batch
- the remaining route consumption is mostly transport/entry continuity, not
  business fact fabrication

### `ModelListPage`

Observed facts:

- this page only redirects legacy list routes into `ActionView`

Judgment:

- not a current semantic inference hotspot

## Priority Order

Recommended next execution order:

1. remove the remaining intake route fallback from `ContractFormPage`
2. move dashboard summary assembly out of frontend scene-key branches
3. standardize project execution stage / project condition / explain fields so
   dashboard stops aliasing business vocabulary locally

## Final Screen Result

The current highest-value frontend semantic debt is concentrated in two areas:

- `ContractFormPage` residual intake fallback
- `ProjectManagementDashboardView` scene-specific summary assembly and business
  vocabulary aliasing

These should be fixed by backend semantic supply, not by adding more frontend
branches.

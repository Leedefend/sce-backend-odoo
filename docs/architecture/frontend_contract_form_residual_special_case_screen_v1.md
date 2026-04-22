# Frontend ContractForm Residual Special-Case Screen V1

## Scope

This screen covers the remaining high-value model-specific behavior branches in
`frontend/apps/web/src/pages/ContractFormPage.vue` after the previous cleanup
rounds.

Included candidates:

1. `project.project` intake/create mode branches
2. `res.users.password` onchange/save branches

## Candidate 1: `project.project` intake/create mode

Current behavior:

- frontend decides quick/standard intake mode by checking:
  - `model === "project.project"`
  - create route (`id === "new"`)
  - `route.query.intake_mode`
  - `route.query.scene_key === PROJECT_INTAKE_SCENE_KEY`
- frontend then changes:
  - submit button label
  - ready-state checks
  - autosave key
  - post-create redirect behavior

Ownership judgment:

- this is not raw rendering only
- it is create-flow orchestration for a scenario-specific project intake entry
- current frontend logic is reconstructing scenario mode from route + model

Classification:
- `requires_backend_semantic_supply`

Reason:

- frontend should not infer create-flow mode from concrete model name plus query
  combinations
- the page should consume an explicit scene/form governance signal such as:
  - `form_governance.create_flow_mode`
  - `form_governance.post_create_target`
  - `form_governance.autosave_scope`

Backend sub-layer:
- primary: `scene-orchestration layer`

Reason:
- quick intake vs standard intake is scenario-entry organization for form
  consumption
- it is not intrinsic business truth of the project record itself

Frontend follow-up after supply:

- remove model + route-driven intake mode inference
- consume explicit create-flow mode and post-create target from contract

## Candidate 2: `res.users.password` onchange/save branches

Current behavior:

- frontend skips onchange when:
  - `model === "res.users"`
  - `field === "password"`
- frontend save path applies password with a dedicated branch
- frontend clears `formData.password` after successful save

Ownership judgment:

- password is not a generic display concern
- this branch encodes field handling policy for a sensitive write-only field
- current behavior is still chosen from a concrete model name

Classification:
- `requires_backend_semantic_supply`

Reason:

- frontend should not discover sensitive-field policy from `res.users`
- the contract should declare field behavior explicitly, for example:
  - `write_only`
  - `skip_onchange`
  - `clear_after_save`
  - `sensitive_transport_mode`

Backend sub-layer:
- primary: `business-fact layer`
- optional envelope: `scene-orchestration layer`

Reason:
- whether a field is sensitive/write-only is a field truth / handling fact
- orchestration may wrap it for page consumption, but frontend must not invent
  it from model identity

Frontend follow-up after supply:

- replace `model === "res.users" && field === "password"` checks with field
  metadata or contract flags

## Decision Summary

Both remaining candidates are still invalid frontend-owned behavior decisions.

Summary:

- `project.project` intake/create mode:
  - owner = backend scene-orchestration
  - current frontend route/model inference should be removed after supply

- `res.users.password` field handling:
  - owner = backend field semantics / business-fact with optional orchestration
  - current frontend model-based branch should be removed after supply

## Recommended Next Batch Order

1. backend screen/contract for project intake create-flow mode
2. backend screen/contract for sensitive field handling policy
3. frontend consumer cleanup after those semantics land

# Backend Project Intake Create-Flow Contract Screen V1

## Problem

`ContractFormPage.vue` still reconstructs project intake create-flow mode from:

- `model === "project.project"`
- `route.params.id === "new"`
- `route.query.intake_mode`
- `route.query.scene_key === projects.intake`

The page then changes:

- primary button label
- required-ready logic
- autosave key
- post-create redirect target

This is invalid because create-flow mode is scene orchestration semantics, not a
frontend inference from route and model identity.

## Existing Fact

The backend already exposes adjacent semantics:

- `project.initiation.enter`
  - emits `suggested_action_payload.intent = "project.dashboard.enter"`
  - emits `contract_ref`
  - emits `lifecycle_hints`
- `form_governance`
  - already exists for enterprise enablement surfaces
- `sceneReadyFormSurface`
  - already exposes `nextSceneKey / nextSceneRoute`

What is missing is a dedicated create-flow contract surface that tells the form
page which scenario it is serving and which create-flow policy to use.

## Ownership

Owner:
- `scene-orchestration layer`

Reason:
- quick intake vs standard intake is entry-flow organization for one scenario
- it is not intrinsic business fact of `project.project`
- frontend must consume it, not infer it

## Minimum Contract Target

Recommended placement:

- `form_governance`

Minimum shape:

```json
{
  "form_governance": {
    "surface": "project_intake",
    "create_flow_mode": "quick",
    "autosave_scope": "project_intake_quick",
    "post_create_target": {
      "intent": "project.dashboard.enter",
      "route": "/s/project.management"
    }
  }
}
```

Alternative mode:

```json
{
  "form_governance": {
    "surface": "project_intake",
    "create_flow_mode": "standard",
    "autosave_scope": "project_intake_standard",
    "post_create_target": {
      "intent": "project.dashboard.enter",
      "route": "/s/project.management"
    }
  }
}
```

## Required Semantics

Per project create form surface:

- `form_governance.surface`
- `form_governance.create_flow_mode`
- `form_governance.autosave_scope`
- `form_governance.post_create_target`

Optional:

- `form_governance.primary_action_label`
- `form_governance.ready_policy`

## Frontend Consumption Rule

Frontend follow-up target:

- stop checking `model === "project.project"` to discover intake mode
- stop checking `route.query.intake_mode`
- stop checking `route.query.scene_key === projects.intake`
- derive create-flow behavior only from `form_governance`

Frontend may still use `project_id` after create for navigation bootstrap, but
not to infer create-flow mode.

## Recommended Implementation Order

1. backend governance emits project intake create-flow fields in
   `form_governance`
2. frontend removes route/model-driven intake mode inference
3. frontend uses `form_governance.create_flow_mode`, `autosave_scope`, and
   `post_create_target`
4. verify project intake create flow still lands in the correct dashboard path

## Decision Summary

The missing piece is not another frontend branch.

The missing piece is an explicit backend create-flow contract for the project
intake surface.

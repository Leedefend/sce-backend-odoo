# Project Intake Quick Mode Contract Screen V1

## Problem

We now know the frontend still keeps this fallback:

- `route.query.intake_mode === "quick"`

This fallback cannot be deleted blindly unless we first confirm whether quick
mode is:

- a real business/scene mode that still exists, or
- only a dead frontend residue

## Current Fact

### Quick mode is real in Odoo-side entry semantics

The repository still contains dedicated quick-mode assets:

- `addons/smart_construction_core/views/menu.xml`
  - `action_project_initiation_quick`
  - `menu_sc_project_quick_create`
  - action context includes:
    - `intake_mode = "quick"`
- `addons/smart_construction_core/views/core/project_views.xml`
  - create form changes visibility based on `context.get('intake_mode') == 'quick'`
- `addons/smart_construction_core/views/core/project_quick_create_wizard_views.xml`
  - quick-create wizard primary action text is
    `创建并进入项目驾驶舱`

Conclusion:

- quick mode is not a frontend invention
- it is a real scenario/business entry variant already present in native Odoo

### Current frontend handoff only carries standard intake identity

`frontend/apps/web/src/views/ProjectsIntakeView.vue` currently redirects to:

- `/f/project.project/new`

with query:

- `scene_key = projects.intake`
- `menu_xmlid = smart_construction_core.menu_sc_project_initiation`
- `intake_mode = undefined`

Conclusion:

- the scene handoff only points to the standard project initiation menu
- quick entry identity is not represented in the current handoff

### Current contract chain has no explicit quick-mode supply

Current contract governance already emits:

- `form_governance.surface = "project_intake"`
- `form_governance.create_flow_mode = "standard"`

for:

- `project.project + create + projects.intake`

But there is no equivalent quick-mode contract branch.

Conclusion:

- standard mode is now contract-supplied
- quick mode is still outside the current contract chain

## Ownership Classification

This gap contains two different missing pieces.

### Missing piece 1: entry identity transport

The current scene handoff does not carry quick entry identity into the contract
mainline.

This is a:

- `platform transport / entry-carrier` problem

Reason:

- the contract pipeline cannot emit quick semantics if it cannot tell whether
  the request came from standard or quick entry

### Missing piece 2: scenario semantic supply

Even after quick entry identity is available, the scenario layer still needs to
emit explicit quick semantics such as:

- `form_governance.create_flow_mode = "quick"`
- `form_governance.autosave_scope = "project_intake_quick"`
- quick-mode post-create target / primary action policy

This is a:

- `scene-orchestration / scenario override` problem

Reason:

- quick vs standard is scene-entry organization, not frontend logic

## Current Boundary Failure

The current frontend fallback exists because both backend layers are incomplete
for quick mode:

1. quick entry identity does not reach the contract pipeline
2. quick scenario semantics are not emitted once the contract is built

As a result, frontend fills the gap by reading:

- `route.query.intake_mode`

This is exactly the kind of semantic debt the frontend must not own long-term.

## Recommended Fix Order

### Step 1: restore legal quick entry identity

Introduce one stable quick-mode carrier into the contract path.

Allowed directions:

- use a dedicated quick menu/action identity in scene handoff
- or explicitly transport the quick entry marker through the contract request

Preferred direction:

- menu/action identity first

Reason:

- quick mode already exists as a real Odoo action/menu concept
- this keeps entry identity aligned with the existing mainline transport model

### Step 2: emit quick form governance in scenario override

Once quick entry identity is present, industry scene governance should emit:

- `surface = "project_intake"`
- `create_flow_mode = "quick"`
- `autosave_scope = "project_intake_quick"`
- quick post-create target and primary action semantics

### Step 3: delete frontend quick fallback

Only after steps 1 and 2 should frontend remove:

- `route.query.intake_mode === "quick"`

At that point the frontend can consume only:

- `form_governance.create_flow_mode`

## Decision Summary

Quick mode is real, but it is not yet in the contract chain.

So the next correction is not:

- deleting the frontend branch immediately

The next correction is:

- restoring quick entry identity into the contract pipeline
- then emitting quick semantics from scenario governance
- then deleting the frontend fallback

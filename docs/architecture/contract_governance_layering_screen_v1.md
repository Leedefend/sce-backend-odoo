# Contract Governance Layering Screen V1

## Purpose

This screen fixes one recurring ambiguity:

- what belongs to platform contract governance
- what belongs to scenario/industry contract governance
- what the frontend is allowed to do with those semantics

The target is a single layered ownership model so contract behavior can keep
converging without pushing industry semantics into platform core or forcing the
frontend to guess missing meaning.

## Layered Ownership

### Layer 1: platform transport

Owner:

- `addons/smart_core/handlers/ui_contract.py`
- `frontend/apps/web/src/api/contract.ts`

Responsibility:

- carry legal entry identity into `ui.contract`
- normalize request fields such as:
  - `action_id`
  - `menu_id`
  - `scene_key`
  - `render_profile`
- write those values back into contract `data/head` so downstream governance can
  consume a stable envelope

Must stay neutral:

- no industry business meaning
- no create-flow policy selection
- no frontend-specific page layout decision

Meaning:

- transport answers only "what entry identity reached the contract pipeline"
- transport must not answer "what this industry scene means"

### Layer 2: platform generic governance

Owner:

- `addons/smart_core/utils/contract_governance.py`

Responsibility:

- normalize generic user-facing contract structure
- apply shared governance that is model-generic or platform-generic
- keep user/native/hud contract shapes coherent
- expose neutral capability, action, field, and scene surfaces

Allowed scope:

- generic project form normalization
- generic user-mode stripping / projection
- generic action grouping or neutral form governance

Forbidden scope:

- industry scenario labels
- enterprise/customer delivery semantics
- scene-specific create-flow policy such as project intake standard/quick
- any behavior that only makes sense for one business scene

Meaning:

- generic governance may shape a contract
- generic governance must not explain one industry's workflow

### Layer 3: scenario or industry override governance

Owner:

- scenario/industry modules such as
  `addons/smart_construction_core/services/contract_governance_overrides.py`

Responsibility:

- inject scene-specific semantic governance only after legal entry identity is
  already available from platform transport
- translate entry identity into scenario-ready fields such as:
  - `form_governance.surface`
  - `form_governance.create_flow_mode`
  - `form_governance.autosave_scope`
  - `form_governance.post_create_target`

Activation rule:

- scenario override must be gated by explicit contract identity
- examples:
  - `model == "project.project"`
  - `render_profile == "create"`
  - `scene_key == "projects.intake"`

Forbidden scope:

- inventing business truth that backend does not own
- replacing platform transport
- returning frontend implementation structure

Meaning:

- scenario override answers "given a legal entry identity, what scenario
  semantics should the consumer follow"

### Layer 4: frontend semantic consumer

Owner:

- `frontend/apps/web`

Responsibility:

- render and interact from contract semantics
- consume `form_governance`, `sceneReadyFormSurface`, capabilities, and other
  explicit contract fields

Forbidden scope:

- inferring business/scenario mode from route fragments when the contract did
  not say so
- reconstructing missing backend semantics from:
  - `model`
  - `route.query.scene_key`
  - `route.query.intake_mode`
  - local fallback wording
- inventing project/business terminology as a fallback when the contract is
  underspecified

Meaning:

- frontend may route, display, and interact
- frontend must not decide scenario semantics on behalf of backend

## Current Repository Mapping

### Project intake create-flow

Current correct split:

- platform transport:
  - `contract.ts` sends `menu_id/action_id/scene_key`
  - `ui_contract.py` accepts them and writes them into contract payload
- scenario override:
  - `smart_construction_core` detects
    `project.project + create + projects.intake`
  - emits `form_governance.surface = "project_intake"`
  - emits `create_flow_mode = "standard"`
  - emits autosave and post-create target
- frontend consumer:
  - `ContractFormPage.vue` consumes `form_governance`
  - no longer uses `scene_key` as the semantic source of standard intake mode

This is the desired layering.

### Boundary mistake already corrected

Incorrect pattern:

- putting `project_intake` governance directly into
  `smart_core/utils/contract_governance.py`

Why incorrect:

- it mixes industry scenario semantics into platform generic governance
- it breaks the kernel freeze rule
- it makes later scenario growth collapse into the platform core

## Decision Rules For Future Batches

Use the following decision order when a contract gap appears.

### Rule 1: ask whether the gap is transport or meaning

If the missing piece is:

- action/menu/scene/render identity not reaching the pipeline

Then fix:

- platform transport

If the missing piece is:

- scenario meaning after identity is already present

Then fix:

- scenario/industry override governance

### Rule 2: generic governance cannot own single-scene policies

Do not add logic to `smart_core` generic governance when the answer depends on:

- one industry
- one scenario
- one workflow entry
- one customer delivery convention

Those belong to scenario/industry override modules.

### Rule 3: frontend cannot absorb semantic debt

If the frontend needs to branch on route/model/business wording to complete a
workflow, that is evidence the backend contract is incomplete.

Required response:

- open a backend semantic-supply batch

Forbidden response:

- keep a long-lived frontend inference branch

### Rule 4: scenario override cannot fabricate business fact

Scenario override may organize and label behavior, but it must not invent
business facts that should come from domain/business-fact layers, for example:

- real document status
- permission truth
- workflow truth not present in backend facts

If those are missing, open a business-fact supply batch first.

## Governance Gate Recommendation

Future review/gate checks should reject changes when any of these happen:

- platform generic governance introduces industry-scene labels or policy values
- frontend derives business scene mode from route/query/model instead of
  contract fields
- scenario override runs without explicit entry identity
- scenario override returns frontend layout structure instead of scenario
  semantics

## Final Boundary Statement

The single allowed flow is:

```text
frontend entry
  -> platform transport carries identity
  -> platform generic governance shapes neutral contract
  -> scenario/industry override injects scene semantics
  -> frontend consumes explicit semantics
```

The system should converge by strengthening this chain, not by letting any one
layer absorb the responsibilities of another.

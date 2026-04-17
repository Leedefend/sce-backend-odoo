# Backend Contract Layer Responsibility Freeze v1

Status: Architecture Boundary Freeze  
Scope: backend business fact to frontend contract delivery

## 1. Purpose

Recent project form regressions exposed the same architectural failure in
different shapes:

- legacy/system provenance fields reached the user form after the native page
  was already corrected
- `action_open` form contracts were misclassified as kanban because the action
  head carried `kanban,tree,form`
- notebook page labels such as `页签1` overrode native `string` values such as
  `投标管理`

The common root is not a missing frontend renderer. The common root is that
backend contract governance had too much freedom to reinterpret or overwrite
facts produced by earlier layers.

This document freezes the responsibility boundary. Future fixes must locate the
divergence in this chain before changing code:

```text
business facts
  -> native/Odoo structure facts
  -> contract assembly
  -> contract governance
  -> handler delivery envelope
  -> frontend generic consumer
```

## 2. Layer Ownership

### 2.1 Business Fact Layer

Owner:

- Odoo models, domain services, computed fields, permissions, workflow state.

Owns:

- record identity and edit/create truth
- business values, ownership, amount, state, lifecycle, workflow facts
- field existence and field type metadata
- access rights and record visibility

May:

- compute business values
- expose field metadata from the model
- decide whether a business fact exists

Must not:

- emit frontend layout structure
- create tabs, blocks, cards, or view-specific grouping
- hide a business truth to satisfy a renderer

Boundary test:

- If the requested change changes a value, state, permission, ownership, amount,
  workflow eligibility, or record visibility, it belongs here.
- If the requested change only changes how already-known facts are grouped for
  consumption, it does not belong here.

### 2.2 Native Structure Fact Layer

Owner:

- Odoo native view parser and view binding resolution.

Owns:

- native view `arch`
- `form/tree/kanban/search` structure
- notebook/page/group hierarchy
- native labels such as `string` and `attributes.string`
- action-bound view candidates and default runtime view selection

May:

- parse Odoo view structure into structured layout nodes
- choose the richer native form surface when an action-bound view is narrower
- preserve all native labels and structure facts

Must not:

- invent business fields
- apply user-surface noise reduction
- translate frontend design preferences into parser facts

Boundary test:

- If the requested change is about preserving Odoo `arch`, view order, native
  labels, or action-bound view candidates, it belongs here.
- If the requested change filters or prioritizes fields for a user surface, it
  does not belong here.

### 2.3 Contract Assembly Layer

Owner:

- `smart_core` contract service and assembler.

Owns:

- canonical contract shape
- normalized `views.*`
- `semantic_page.form_semantics.layout`
- fieldInfo synchronization from canonical `fields`
- delivery-ready structure that still preserves native facts

May:

- copy native structure into semantic contract surfaces
- fill missing structural envelopes
- normalize equivalent keys into the canonical contract vocabulary
- attach parser provenance and layout source metadata

Must not:

- remove native structure because a user profile is smaller
- replace native labels with placeholder labels
- decide business visibility or role permissions
- classify a multi-view action by raw action `head.view_type` when the current
  render view is already known

Boundary test:

- If the requested change normalizes equivalent parser output into canonical
  contract keys, it belongs here.
- If the requested change chooses which business facts are allowed or visible,
  it does not belong here.

### 2.4 Contract Governance Layer

Owner:

- `smart_core` contract governance policy.

Owns:

- user/hud/native surface projection
- noise reduction
- profile-specific visibility
- capability and action policy filtering
- semantic annotations and diagnostics

Allowed operations:

- add missing consumability metadata
- prune internal/debug/demo-only data from user surface
- classify fields into `core`, `advanced`, `hidden`
- backfill missing layout nodes only when the field is already selected by a
  valid backend fact
- align access policy with already-selected visible fields
- select render profile behavior from explicit record identity or payload facts

Forbidden operations:

- overwrite business facts
- overwrite native `string` labels with placeholders
- let `label/title/name` placeholders outrank native `string`
- reinterpret a form-detail contract as kanban/list because an action supports
  multiple view modes
- use frontend pain as proof that a business fact should change
- fabricate tabs, sections, fields, states, roles, or permissions
- drop full field maps merely because `visible_fields` is smaller
- run model-specific frontend assumptions through governance output

Hard rule:

> Governance may only constrain or annotate facts from earlier layers. It may
> not become a competing fact source.

Boundary test:

- If the requested change projects a user/hud/native surface from facts already
  present in the contract, it belongs here.
- If the requested change needs to query, compute, or invent business truth, it
  does not belong here.
- If the requested change builds scene-consumable envelopes from already
  governed semantic surfaces, it may belong here only when the envelope is
  additive and carries `owner_layer=scene_orchestration`.

### 2.5 Handler Delivery Envelope

Owner:

- intent handler and response envelope.

Owns:

- request parameter normalization
- `contract_mode`, `contract_surface`, `source_mode`
- ETag and response metadata
- final envelope shape

May:

- inject explicit render hints from payload such as `record_id` and
  `render_profile`
- call assembly and governance in the declared order
- expose diagnostics in hud/debug mode

Must not:

- perform business logic
- repair layout by model-specific branching
- silently change public contract schema

Boundary test:

- If the requested change concerns request aliases, mode/surface selection,
  trace metadata, ETag, or response wrapping, it belongs here.
- If the requested change decides layout, field visibility, list semantics, or
  business permissions, it does not belong here.

### 2.6 Frontend Consumer

Owner:

- `frontend/apps/web` generic contract renderer.

Owns:

- rendering
- interaction
- route-level API calls
- generic semantic consumption

May:

- render fields, tabs, groups, actions, and relation options from contract
- defer non-visible relation loading when the contract says a field is not part
  of the current surface
- expose debug state for smoke tests

Must not:

- infer business fields from concrete model names
- fix backend missing semantics with model-specific branches
- choose native labels over contract labels by guessing
- query ORM or database facts directly

Boundary test:

- If the requested change renders a generic contract shape that already exists,
  it belongs here.
- If the requested change requires `model === "project.project"` or another
  concrete model name to recover missing semantics, it does not belong here and
  must be redirected to backend supply.

## 2.7 Responsibility Matrix

| Question | Owner | Output | Forbidden |
| --- | --- | --- | --- |
| Is this value/state/permission true? | Business Fact | model/service fact | UI structure |
| What did native Odoo view declare? | Native Structure Fact | parsed arch/labels/order | business invention |
| How is native/meta output normalized? | Contract Assembly | canonical contract | policy pruning |
| How is a user/hud/native surface projected? | Contract Governance | additive projection/diagnostics | shadow facts |
| How is a scene-ready envelope supplied? | Scene Orchestration or additive governance bridge | `scene_contract_v1`/semantic envelopes | business fabrication |
| How is the intent response wrapped? | Handler Delivery Envelope | meta/etag/mode/surface | layout/business repair |
| How is it displayed? | Frontend Consumer | rendering/interaction | model-specific semantic repair |

## 2.8 Implementation Routing Rule

Every backend fix must start by selecting exactly one primary owner:

1. `business_fact`: missing or wrong business truth.
2. `native_structure_fact`: parser/view-binding lost native Odoo structure.
3. `contract_assembly`: canonical shape or native-to-contract mapping is wrong.
4. `contract_governance`: projection, pruning, diagnostics, or envelope bridge
   is wrong.
5. `scene_orchestration`: semantic organization for scene consumption is
   missing.
6. `handler_delivery_envelope`: request or response envelope is wrong.

Only after the primary owner is selected may a batch touch secondary layers.
Secondary changes must be mechanical propagation, not new decision ownership.

If the primary owner is unclear, run a `screen` task first and stop direct
implementation.

## 2.9 Contract Governance Special Rule

Contract governance is allowed to add `scene_contract_v1` only under all of the
following conditions:

- the source data already exists in the governed contract
- the new envelope is additive
- the envelope declares `contract_version = "v1"`
- the envelope declares `owner_layer = "scene_orchestration"`
- existing top-level fields remain available for compatibility
- no model-specific frontend fallback is required

Contract governance must not use this bridge to compute business values, alter
permissions, or replace native view structure.

## 3. Fact Precedence Rules

When multiple labels or view signals exist, precedence is fixed:

1. Business fact beats all derived labels.
2. Native view `string` / `attributes.string` beats parser-generated
   `label/title/name`.
3. Explicit current render view (`view_type=form`) beats raw action view mode
   strings (`kanban,tree,form`).
4. Explicit record identity (`id/res_id > 0`) beats generic create defaults.
5. `form_profile` and `visible_fields` must describe the same current form
   surface; kanban/list profiles must not overwrite form profiles.
6. `fields` may remain complete while `visible_fields` is a surface projection.
   A smaller `visible_fields` list must not prune native layout containers.

## 4. Required Debug Trace For Contract Divergence

Every custom frontend mismatch against native/business facts must be diagnosed
in this order:

1. Business fact:
   - field exists
   - record value exists
   - permission allows read/write
2. Native structure fact:
   - native view has the field/page/group/action
   - native `string` is present
3. Assembly:
   - `views.form.layout` preserves the native structure
   - `semantic_page.form_semantics.layout` mirrors the same structure
4. Governance:
   - `visible_fields` is correct for the render profile
   - governance did not apply a different view profile
   - placeholders did not override native facts
5. Handler delivery:
   - payload carries the intended `record_id`, `view_type`, and
     `render_profile`
   - output `contract_surface` and `source_mode` are expected
6. Frontend:
   - renderer consumes contract values without model-specific inference
   - page debug state confirms load completion

Skipping earlier steps and fixing the frontend first is an architecture
violation unless the backend contract already contains the exact generic
semantics required.

## 5. Stop Signals

Stop implementation and open a boundary task when any of the following appears:

- governance code wants to overwrite `string`, `view_type`, record identity, or
  permission facts
- a fix requires frontend code to branch on `project.project` or another
  concrete business model
- user-surface pruning would remove native layout containers
- a contract has both form and kanban/list signals and classification is not
  anchored on the current render view
- a smaller view profile changes business truth instead of only changing
  projection

## 6. Acceptance For Future Fixes

Any future backend contract fix touching project/detail/form semantics must
produce evidence for all applicable layers:

- direct backend contract summary
- `views.form.layout` or equivalent native structure proof
- `visible_fields` and `form_profile` consistency proof
- browser smoke proof when frontend output was user-visible
- explicit statement that frontend did not add model-specific semantic repair

## 6.1 Mandatory Guard

Backend responsibility closure is executable through:

```bash
python3 scripts/verify/backend_responsibility_boundary_guard.py
```

The guard checks that this document still contains the required ownership,
precedence, routing, and stop-signal anchors. It also checks high-risk source
patterns that would move layout/business ownership into the handler or frontend.

This guard is intentionally lightweight. It does not prove architectural
correctness by itself; it prevents the most common regressions from entering a
batch without a visible stop signal.

## 7. Non-Goals

This freeze does not:

- rename public contract fields
- introduce a new schema version
- move industry semantics into platform kernel
- change ACL, record rules, payment, settlement, account, or manifest behavior
- require frontend rewrites

The purpose is to prevent governance from becoming a shadow fact layer.

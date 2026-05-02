# Contract System Target Gap Audit v1

Date: 2026-05-01
Branch: `codex/contract-system-audit`
Baseline SHA: `3553fd90`

## 1. Scope

This audit evaluates whether the current repository contract system satisfies the target architecture:

```text
Odoo atomic capabilities
-> platform/domain/scene orchestration
-> unified full contract
-> client-specific trimming
-> Web / UniApp mini program / Harmony H5 rendering
```

Target contract pillars:

- `LayoutContract`: page structure, containers, widgets, recursive layout.
- `StatusContract`: permission, visibility, readonly, required, disabled states.
- `ActionContract`: interaction rules, linkage, refresh, validation, save, popup, chain actions.
- `DataContract`: page data bound to structure/status/action contracts.

This is an audit-only document. It does not define implementation as completed.

## 2. Current System Summary

The current system already has a real contract foundation, but it is not yet the final unified contract system described above.

Current mainline artifacts are:

- `Scene Contract v1`: documented in `docs/architecture/scene_contract_spec_v1.md`.
- `page_orchestration_v1`: consumed by frontend page contract helpers.
- `scene_ready_contract_v1`: built during `system.init`.
- `ui.contract`: still available for model/action/native contract paths, with frontend native delivery restrictions.
- `api.onchange`: incremental patch path for form field changes.

The current state is best classified as:

```text
Scene/Page/UI Contract transition architecture
```

It is not yet:

```text
Unified LayoutContract + StatusContract + ActionContract + DataContract architecture
```

## 3. Evidence

### 3.1 Architecture Direction Exists

The repository already states that `Scene Contract` is the frontend input authority.

Evidence:

- `docs/architecture/scene_orchestration_layer_design_v1.md`
- `docs/architecture/five_layer_core_boundary_v1.md`
- `docs/architecture/native_view_reuse_frontend_spec_v1.md`

Current declared flow:

```text
Business Truth
-> Native Expression
-> Native Parse
-> Contract Governance
-> Scene Orchestration
-> Frontend
```

This aligns with the target direction, especially the principle that frontend should render contracts instead of inferring business semantics.

### 3.2 Backend Scene Contract Builder Exists

`addons/smart_scene/core/scene_contract_builder.py` builds `scene_contract_v1` with:

- `contract_version`
- `scene`
- `page`
- `nav_ref`
- `zones`
- `blocks`
- `record`
- `permissions`
- `actions`
- `extensions`
- `diagnostics`

This covers part of the desired `LayoutContract`, `StatusContract`, `ActionContract`, and `DataContract`, but not under the final standard names or boundaries.

### 3.3 Startup Chain Already Carries Contract Surfaces

`addons/smart_core/handlers/system_init.py` builds and returns:

- `page_contracts`
- `scene_ready_contract_v1`
- `delivery_engine_v1`
- `release_navigation_v1`
- `role_surface`
- `default_route`

This means the startup chain has the correct architectural entry:

```text
login -> system.init -> ui.contract / scene route
```

But the response still contains multiple contract families rather than one canonical page contract package.

### 3.4 Frontend Contract Consumption Exists

Frontend receives and stores:

- `pageContracts`
- `sceneReadyContractV1`
- `roleSurface`
- `defaultRoute`

Frontend helpers consume:

- `page_orchestration_v1`
- `scene_contract_v1`
- action schemas
- data sources

Evidence:

- `frontend/apps/web/src/stores/session.ts`
- `frontend/apps/web/src/app/pageContract.ts`
- `frontend/apps/web/src/app/sceneContractV1.ts`

The frontend is partially contract-driven, but still contains fallback and compatibility consumers for `ui.contract` model/action paths.

### 3.5 Incremental Interaction Exists, But Is Not Unified

`api.onchange` returns:

- `patch`
- `modifiers_patch`
- `line_patches`
- `warnings`
- `applied_fields`

This is a valid incremental update mechanism for form field changes.

However, it is not yet a unified `ActionContract` runtime where all interactions are represented as:

```text
actionId -> triggerType -> targetIds -> actionType -> actionParams -> refreshMode
```

## 4. Target Fit Assessment

| Target Area | Current Status | Assessment |
| --- | --- | --- |
| Odoo atomic capability base | Odoo native view parse, model facts, actions, permissions exist | Partially aligned |
| Platform / industry split | `smart_core`, `smart_scene`, `smart_construction_scene` boundaries exist | Mostly aligned |
| Scene orchestration | Scene contracts and provider registry exist | Aligned but still evolving |
| Unified full contract package | Multiple contract families exist | Not aligned yet |
| LayoutContract | Covered by `zones/blocks/page/native layout` fragments | Partial |
| StatusContract | Spread across permissions, policies, modifiers, surfaces | Partial |
| ActionContract | Spread across actions, action policies, onchange, execute paths | Partial |
| DataContract | Spread across record, data sources, api.data, form runtime | Partial |
| Incremental update contract | `api.onchange` patch exists | Partial |
| Client type routing | No `client_type` standard found | Missing |
| Web PC | Existing frontend supports Web | Aligned |
| UniApp mini program | No code path found | Missing |
| Harmony H5 | No code path found | Missing |
| Infinite depth complex interaction | Recursive scene/page model exists conceptually; x2many and advanced views still incomplete | Partial |

Overall score:

```text
Contract foundation maturity: B+
Target unified contract architecture completion: 45%-55%
```

## 5. Gap List

### S1. Unified Contract Package Missing

Current response shapes are not consolidated into:

```json
{
  "pageInfo": {},
  "layoutContract": {},
  "statusContract": {},
  "actionContract": {},
  "dataContract": {}
}
```

Impact:

- Frontend cannot rely on one canonical parsing entry.
- Multiple compatibility surfaces remain active.
- Contract versioning is harder to govern.

### S1. StatusContract Boundary Missing

Status semantics are currently distributed across:

- `permissions`
- `field_policies`
- `action_policies`
- `modifiers_patch`
- `permission_surface`
- `access_policy`

Impact:

- Visibility/readonly/required/disabled rules are not owned by one schema.
- Cross-client state adaptation is hard.
- Frontend may need adapter logic to reconcile state sources.

### S1. ActionContract Runtime Missing

Current actions are represented by several mechanisms:

- `actions`
- `action_schema`
- `action_groups`
- `action_policies`
- `execute_button`
- `api.onchange`
- route targets

Impact:

- Field linkage, button click, popup open, partial refresh, validation, save, and chain actions do not share one behavior protocol.
- Complex deep interaction cannot be governed uniformly.

### S1. DataContract Boundary Missing

Current data is spread across:

- `record`
- `api.data`
- `page_orchestration_v1.data_sources`
- form local runtime
- dictionary/startup data

Impact:

- Layout and data binding are not expressed by one stable contract.
- Table/tree/gantt/dict data do not have one standard package.

### S1. Multi-Client Trimming Missing

No repository evidence was found for:

- `client_type`
- `web_pc`
- `wx_mini`
- `harmony_h5`
- UniApp mini program runtime
- Harmony H5 runtime

Impact:

- Current system is Web-first.
- There is no backend contract trimming layer for terminal-specific layout adaptation.
- Mobile/H5 adaptation would currently require new design work.

### S1. Compatibility Consumers Still Exist

Frontend still exposes and uses `ui.contract` action/model loading paths.

Impact:

- Scene-ready contract is not yet the only frontend authority.
- Native/action fallback paths remain a proof gap for full contract closure.

### S2. Frontend Page Assembly Layer Is Missing

Existing frontend audit already identifies the missing Page Assembly layer.

Impact:

- Large views still assemble runtime state directly.
- Contract consumption is not consistently isolated from page rendering.

### S2. Odoo Native Interaction Parity Is Incomplete

Existing native view assessment identifies gaps:

- x2many command semantics
- expanded modifiers/attrs coverage
- pivot/graph/calendar/gantt coverage
- stronger onchange schema and regression matrix

Impact:

- The system can support core business flows, but not full native-equivalent depth yet.

## 6. Target Architecture Recommendation

### 6.1 Freeze One Canonical Contract Package

Introduce `UnifiedPageContract v2` as the canonical frontend package:

```json
{
  "pageInfo": {
    "pageId": "",
    "pageName": "",
    "sceneKey": "",
    "model": "",
    "viewType": "",
    "contractVersion": "2.0.0"
  },
  "layoutContract": {},
  "statusContract": {},
  "actionContract": {},
  "dataContract": {},
  "meta": {
    "client_type": "web_pc",
    "schema_version": "2.0.0",
    "trace_id": ""
  }
}
```

Compatibility rule:

- Existing `scene_contract_v1`, `page_orchestration_v1`, and `ui.contract` may remain as inputs.
- Frontend default mode should consume only `UnifiedPageContract v2`.
- Compat mode may expose legacy fields under a clearly separated `compat` node.

### 6.2 Define Contract Source Chain

Canonical source chain:

```text
Odoo native model/view/action facts
-> UI base fact adapter
-> Contract governance
-> Scene orchestration
-> UnifiedPageContract assembler
-> client trimming
-> frontend renderer
```

Layer ownership:

- Business Truth Layer: business facts only.
- Native Parse Layer: Odoo structure facts only.
- Contract Governance Layer: schema, status, compatibility, client trimming.
- Scene Orchestration Layer: page composition, zones, blocks, action grouping.
- Frontend Layer: render and dispatch only.

### 6.3 Define Client Type Standard

Supported values:

```text
web_pc
wx_mini
harmony_h5
```

Rules:

- Client type changes layout and component adaptation only.
- Field names, widget IDs, action IDs, status IDs, and data keys remain globally stable.
- Business semantics must not branch by client.

Recommended request source:

```text
X-SC-Client-Type: web_pc | wx_mini | harmony_h5
```

Fallback:

```text
web_pc
```

### 6.4 Define Four Contract Boundaries

#### LayoutContract

Owns:

- page identity
- layout type
- containers
- recursive child containers
- widgets
- component config
- terminal adaptation hints

Must not own:

- business permissions
- action execution logic
- record data values

#### StatusContract

Owns:

- global page state
- container state
- widget state
- button state
- readonly/required/disabled/visible
- reason codes

Must not own:

- layout nesting
- data values
- action effects

#### ActionContract

Owns:

- action rules
- trigger type
- source widget
- target IDs
- action type
- params
- refresh mode
- server roundtrip policy

Must not own:

- frontend business branching
- direct ORM operations
- uncontrolled route fallback

#### DataContract

Owns:

- main record data
- table rows
- tree rows
- gantt data
- dictionary/options data
- relation data windows

Must not own:

- visibility rules
- action rules
- layout definitions

## 7. Migration Plan

### Batch A: Schema Freeze

Goal:

- Add `UnifiedPageContract v2` documentation and JSON schema.
- Define enums for client type, layout type, container type, widget type, trigger type, action type, refresh mode.

Do not:

- Refactor frontend runtime.
- Change public intent behavior.

Acceptance:

- Schema documented.
- Existing contracts mapped field-by-field to the new package.

### Batch B: Backend Assembler

Goal:

- Add backend assembler that converts existing `scene_contract_v1/page_orchestration_v1/ui_base facts` into `UnifiedPageContract v2`.

Do not:

- Remove legacy contracts.
- Change scene provider semantics.

Acceptance:

- `system.init` or scene page contract can expose v2 in debug/compat mode.
- Snapshot guard validates v2 shape.

### Batch C: Status Contract Consolidation

Goal:

- Normalize `permissions`, `field_policies`, `action_policies`, and `modifiers` into `StatusContract`.

Do not:

- Move business permission rules into frontend.

Acceptance:

- Create/edit/readonly field governance can be proven from `StatusContract` alone.

### Batch D: Action Contract Consolidation

Goal:

- Normalize onchange, execute button, route, save, popup, and refresh behaviors into `ActionContract`.

Do not:

- Remove existing `api.onchange` until action runtime has parity.

Acceptance:

- Field change and button click both use `actionId` dispatch.
- Backend returns partial update package.

### Batch E: Data Contract Consolidation

Goal:

- Normalize form, table, relation, tree, gantt, dict data into `DataContract`.

Do not:

- Duplicate data ownership in frontend stores.

Acceptance:

- Frontend can render form/list/tree from `DataContract` plus `LayoutContract`.

### Batch F: Client Trimming

Goal:

- Implement `client_type` request parsing and terminal-specific trimming.

Do not:

- Fork business rules by terminal.

Acceptance:

- Same page produces stable IDs across `web_pc`, `wx_mini`, and `harmony_h5`.
- Only layout/component adaptation changes.

### Batch G: Frontend Consumer Migration

Goal:

- Frontend default path consumes `UnifiedPageContract v2`.

Do not:

- Keep page-level business fallback as default mode.

Acceptance:

- `schema -> store -> page` path is enforced.
- Legacy `ui.contract` model/action paths are compat-only.

## 8. Final Judgment

Current result:

```text
Not passed for final target architecture.
Passed for foundational contract architecture.
```

The platform has the correct direction and several core building blocks:

- Odoo native fact extraction.
- Scene orchestration.
- Startup contract surfaces.
- Frontend contract consumption.
- Incremental onchange patches.

The remaining architectural work is consolidation:

```text
many contract surfaces
-> one canonical terminal-independent contract
-> client trimming
-> unified frontend renderer
```

The highest-priority next step is not more page feature work. It is to freeze `UnifiedPageContract v2` and map every existing contract source into it.


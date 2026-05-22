# Unified Page Contract v2+ Design

Date: 2026-05-01
Version: Draft 2.1
Status: Draft for schema freeze
Layer Target: Contract Governance Layer
Module: `smart_core` contract governance / `smart_scene` orchestration / frontend contract consumer

## 0. Normative Status

This document is the architecture and schema-freeze reference for `UnifiedPageContract v2+`.

Future JSON Schema, backend assemblers, frontend runtime adapters, and snapshot guards must treat this document as the governing source.

Normative keywords:

- `MUST`: required for the default protocol path.
- `SHOULD`: recommended; deferral requires a compatibility note and exit plan.
- `MAY`: optional; must not affect core protocol stability.

Protocol positioning:

```text
UnifiedPageContract v2+ = UI Runtime IR + Governed Patch Protocol
```

It is not:

```text
page JSON
low-code executor
frontend rule VM
business workflow engine
```

## 1. Purpose

`UnifiedPageContract v2+` is the next canonical frontend runtime protocol.

Its target level is:

```text
Enterprise Semantic UI Runtime Protocol
```

This means the contract is not only a static page description. It is a governed runtime protocol that defines:

- what to render
- what state is allowed
- what actions can be dispatched
- what data is bound
- what runtime capabilities are enabled
- how patches are applied
- how dependencies are evaluated
- how clients adapt without changing semantics

It consolidates the current transition surfaces:

- `scene_contract_v1`
- `page_orchestration_v1`
- `scene_ready_contract_v1`
- selected `ui.contract` model/action output
- `api.onchange` patch semantics

into one terminal-independent contract that can be trimmed for:

- `web_pc`
- `wx_mini`
- `harmony_h5`

The goal is not to remove existing contracts in one step. The goal is to define the single future default protocol that existing contracts must map into.

## 2. Design Principles

### 2.1 One Canonical Package

Frontend default mode must eventually consume one package:

```json
{
  "pageInfo": {},
  "layoutContract": {},
  "statusContract": {},
  "actionContract": {},
  "dataContract": {},
  "runtimeContract": {},
  "meta": {}
}
```

Legacy contracts may remain only under `compat`.

### 2.2 Four Fixed Subcontracts

The semantic subcontract set is fixed:

- `LayoutContract`
- `StatusContract`
- `ActionContract`
- `DataContract`

`RuntimeContract` is allowed as a protocol control plane, not a fifth semantic subcontract.

No new peer-level semantic contract families should be added after v2+. Future page semantics must expand inside Layout/Status/Action/Data. Future runtime governance must expand inside `RuntimeContract`.

### 2.3 Terminal Independent, Client Adapted

Contract IDs and behavior semantics must be globally stable across clients.

Allowed client differences:

- layout column count
- container collapse strategy
- component adapter selection
- size and density hints
- unsupported component fallback policy

Forbidden client differences:

- business rule branching
- permission branching
- action ID changes
- field/widget ID changes
- data key changes

### 2.4 Backend Owns Semantics

Frontend must not infer:

- role
- permission
- required/readonly/visible rules
- business action availability
- default route
- scene identity
- field linkage semantics

Frontend renders and dispatches by contract only.

### 2.5 Protocol, Not DSL VM

The contract must not become a general-purpose DSL virtual machine.

Allowed:

- declarative layout
- declarative status
- declarative action dispatch metadata
- declarative dependency edges
- declarative patch application rules
- backend-owned expression IDs or reason codes

Forbidden:

- arbitrary frontend-executed scripts
- custom expression language that reimplements business rules
- loops, variables, user-defined functions, or nested program flow in contract JSON
- client-side rule evaluation that changes business outcomes
- contract-defined component source code
- action chains that bypass backend permission and validation

Rule of thumb:

```text
Contract describes governed runtime facts.
Backend computes business decisions.
Frontend applies a small fixed protocol.
```

### 2.6 Contract Is IR

`UnifiedPageContract` is a UI intermediate representation.

It should be treated like:

- compiler IR
- virtual DOM
- render object tree
- low-code schema with governance

Therefore:

- IDs must be stable.
- Patch semantics must be stable.
- Action lifecycle must be stable.
- Compatibility must be explicit.
- Runtime behavior must be governed.

## 3. Source Chain

The v2 source chain is:

```text
Odoo model/view/action facts
-> UI base fact adapter
-> Contract governance
-> Scene orchestration
-> UnifiedPageContract v2+ assembler
-> client trimming
-> runtime protocol guard
-> frontend renderer
```

Layer ownership:

| Layer | Owns | Must Not Own |
| --- | --- | --- |
| Business Truth | model facts, lifecycle, business permissions | UI layout |
| Native Parse | normalized Odoo view/action/search/modifier facts | role scene composition |
| Contract Governance | schema, versioning, status normalization, compat, trimming, runtime protocol guard | business rule creation |
| Scene Orchestration | page composition, zones, blocks, action grouping, dependency metadata | ORM writes, parser private structures |
| Frontend | render, input, dispatch, local UI feedback | business semantics |

## 4. Top-Level Shape

```json
{
  "pageInfo": {
    "pageId": "projects.form",
    "pageName": "Project Form",
    "sceneKey": "projects.intake",
    "model": "project.project",
    "viewType": "form",
    "layoutType": "form",
    "renderMode": "governed",
    "contractVersion": "2.0.0"
  },
  "layoutContract": {},
  "statusContract": {},
  "actionContract": {},
  "dataContract": {},
  "runtimeContract": {},
  "meta": {
    "schemaVersion": "2.0.0",
    "contractVersion": "2.0.0",
    "clientType": "web_pc",
    "contractMode": "default",
    "traceId": "",
    "sourceRefs": {},
    "compat": {}
  }
}
```

Required top-level keys:

- `pageInfo`
- `layoutContract`
- `statusContract`
- `actionContract`
- `dataContract`
- `runtimeContract`
- `meta`

Governed optional top-level extensions:

- `formStructureContract`

`formStructureContract` is the only governed optional top-level extension in v2.
It describes product-level form structure orchestration only. It must not carry
business facts directly, and it must not be used as a precedent for arbitrary
peer-level protocol growth.

## 5. Client Type

Supported values:

```text
web_pc
wx_mini
harmony_h5
mobile_app
```

`mobile_app` is a future extension slot. Batch-A may freeze only `web_pc`, `wx_mini`, and `harmony_h5`; Batch-G must decide whether `mobile_app` enters the first guard matrix.

Request header:

```text
X-SC-Client-Type: web_pc | wx_mini | harmony_h5
```

Fallback:

```text
web_pc
```

Client trimming must preserve:

- `pageId`
- `sceneKey`
- `containerId`
- `widgetId`
- `fieldCode`
- `btnId`
- `actionId`
- `dataKey`

## 6. LayoutContract

### 6.1 Responsibility

`LayoutContract` describes what the page looks like:

- page layout type
- container hierarchy
- recursive child containers
- widget placement
- structural component config
- terminal adaptation hints

It must not own permission, action, or record data semantics.

### 6.2 Shape

```json
{
  "pageId": "projects.form",
  "layoutType": "form",
  "adaptMode": "pc",
  "containerList": [
    {
      "containerId": "main.group.basic",
      "containerType": "group",
      "title": "Basic",
      "span": 12,
      "styleConfig": {},
      "childrenContainer": [],
      "widgetList": [
        {
          "widgetId": "field.name",
          "widgetType": "input",
          "fieldCode": "name",
          "label": "Name",
          "span": 6,
          "defaultValue": "",
          "componentConfig": {}
        }
      ]
    }
  ],
  "layoutHints": {
    "density": "standard",
    "mobileColumns": 1,
    "pcColumns": 12
  }
}
```

### 6.3 Enums

`layoutType`:

- `form`
- `table`
- `kanban`
- `tree`
- `gantt`
- `calendar`
- `graph`
- `pivot`
- `combine`

`adaptMode`:

- `pc`
- `mobile`
- `h5`

`containerType`:

- `root`
- `group`
- `tab`
- `popup`
- `subTable`
- `card`
- `toolbar`
- `search`
- `tree`
- `gantt`
- `kanban`
- `custom`

`widgetType`:

- `input`
- `textarea`
- `select`
- `date`
- `datetime`
- `number`
- `money`
- `checkbox`
- `radio`
- `table`
- `upload`
- `button`
- `tag`
- `relation`
- `tree`
- `gantt`
- `kanban`
- `html`
- `custom`

## 7. StatusContract

### 7.1 Responsibility

`StatusContract` describes whether the page, container, widget, or button can be seen or used.

It owns:

- page auth
- visibility
- disabled
- readonly
- required
- placeholder
- reason codes

It must not own layout nesting, action effects, or data values.

### 7.2 Shape

```json
{
  "globalStatus": {
    "pageVisible": true,
    "pageAuth": "edit",
    "reasonCode": ""
  },
  "containerStatus": [
    {
      "containerId": "main.group.basic",
      "visible": true,
      "disabled": false,
      "reasonCode": ""
    }
  ],
  "widgetStatus": [
    {
      "widgetId": "field.name",
      "visible": true,
      "readonly": false,
      "required": true,
      "disabled": false,
      "placeholder": "",
      "reasonCode": ""
    }
  ],
  "buttonStatus": [
    {
      "btnId": "btn.save",
      "visible": true,
      "disabled": false,
      "reasonCode": ""
    }
  ]
}
```

### 7.3 Enums

`pageAuth`:

- `none`
- `read`
- `edit`
- `admin`

Status reason codes must use stable backend-defined codes. Frontend must not create business reason codes.

## 8. ActionContract

### 8.1 Responsibility

`ActionContract` describes every interaction rule:

- field change
- button click
- selection
- refresh
- add/delete
- validation
- save
- popup
- chain action

Frontend dispatches `actionId`; backend evaluates and returns either data/status/layout patches or a full contract.

### 8.2 Shape

```json
{
  "actionRuleList": [
    {
      "actionId": "project.name.change",
      "triggerType": "change",
      "sourceWidgetId": "field.name",
      "targetIds": ["field.display_name", "btn.save"],
      "actionType": ["assignValue", "changeStatus"],
      "actionParams": {},
      "refreshMode": "partial",
      "submitPolicy": "server"
    }
  ]
}
```

### 8.3 Enums

`triggerType`:

- `init`
- `change`
- `click`
- `select`
- `refresh`
- `add`
- `delete`
- `confirm`
- `save`
- `validate`

`actionType`:

- `assignValue`
- `filterData`
- `changeStatus`
- `refreshView`
- `openPopup`
- `closePopup`
- `validateForm`
- `saveData`
- `deleteData`
- `chainAction`
- `navigate`
- `download`
- `upload`

`refreshMode`:

- `none`
- `partial`
- `full`

`submitPolicy`:

- `local`
- `server`
- `serverDebounced`
- `serverBlocking`

## 9. DataContract

### 9.1 Responsibility

`DataContract` carries renderable page data and dictionary data.

It owns:

- main record data
- table rows
- relation rows
- tree data
- gantt data
- dictionary/options data
- pagination windows

It must not own visibility, required, readonly, or action rules.

### 9.2 Shape

```json
{
  "mainData": {},
  "tableRows": [],
  "relationRows": {},
  "treeData": [],
  "ganttData": [],
  "dictData": {},
  "dataSource": {},
  "pagination": {},
  "dataMeta": {
    "loadedAt": "",
    "etag": ""
  }
}
```

### 9.3 Data Source

`dataSource` reserves data access metadata for future realtime, streaming, BI, and AI context use.

```json
{
  "dataSource": {
    "project_list": {
      "query": "project.search",
      "cachePolicy": "etag",
      "consistency": "eventual",
      "subscription": true
    }
  }
}
```

Allowed uses:

- cache policy
- query identity
- pagination identity
- subscription flag
- consistency hint

Forbidden uses:

- raw SQL
- business rule code
- frontend-owned permission filtering

## 10. RuntimeContract

### 10.1 Responsibility

`RuntimeContract` is the protocol control plane. It describes how the frontend runtime should apply the four semantic contracts safely.

It owns:

- protocol version
- patch engine configuration
- dependency graph
- capability protocol
- component registry references
- selector status
- client adaptation policy
- trace and snapshot requirements
- AI integration constraints

It must not own:

- business rule decisions
- field values
- layout hierarchy
- permission verdicts
- executable frontend code

### 10.2 Shape

```json
{
  "protocolVersion": "2.0.0",
  "runtimeMode": "governed",
  "patchStrategy": "incremental",
  "cachePolicy": "etag",
  "optimistic": false,
  "lazyContainer": [],
  "virtualization": {},
  "retryPolicy": {},
  "patchEngine": {},
  "dependencyGraph": {},
  "capabilityProtocol": {},
  "componentRegistry": {},
  "selectorStatus": {},
  "clientGovernance": {},
  "tracePolicy": {},
  "snapshotPolicy": {},
  "aiIntegration": {}
}
```

### 10.3 Enums

`runtimeMode`:

- `governed`
- `readonly`
- `diagnostic`
- `compat`

Default mode:

```text
governed
```

## 11. Patch Engine

All interactive roundtrips must be applied by a fixed patch engine. The patch engine is not programmable by contract; the contract only selects from fixed operations.

All interactive roundtrips must return one of two shapes.

### 11.1 Partial Update

```json
{
  "updateType": "partial",
  "updateLayout": {},
  "updateStatus": {},
  "updateData": {},
  "updateActions": {},
  "meta": {
    "traceId": "",
    "actionId": ""
  }
}
```

### 11.2 Full Update

```json
{
  "updateType": "full",
  "contract": {}
}
```

Current `api.onchange` can map into `partial`:

- `patch` -> `updateData`
- `modifiers_patch` -> `updateStatus`
- `line_patches` -> `updateData.relationRows`
- `warnings` -> `updateStatus` or `meta.warnings`

### 11.3 Patch Operation Rules

Allowed patch operations:

- `replace`
- `merge`
- `append`
- `remove`
- `reorder`
- `invalidate`

Forbidden patch operations:

- arbitrary JavaScript execution
- path expressions with function calls
- cross-page mutation without backend-issued action result
- silent mutation of IDs

Patch paths must target only:

- `layoutContract`
- `statusContract`
- `actionContract`
- `dataContract`
- `runtimeContract.tracePolicy`
- `meta`

The runtime must also support:

- structural diff
- selector merge
- reactive propagation
- dependency scheduling
- minimal patch
- optimistic rollback
- patch ordering

## 12. Dependency Graph

### 12.1 Responsibility

`dependencyGraph` describes dependency edges between widgets, data keys, status nodes, and action rules.

It does not evaluate business rules. It tells the frontend which nodes must be invalidated or refreshed when a backend-confirmed action updates a source.

### 12.2 Shape

```json
{
  "nodes": [
    {"nodeId": "field.project_id", "nodeType": "widget"},
    {"nodeId": "data.contractRows", "nodeType": "data"},
    {"nodeId": "status.btn.save", "nodeType": "status"}
  ],
  "edges": [
    {
      "from": "field.project_id",
      "to": "data.contractRows",
      "edgeType": "filters",
      "refreshPolicy": "server"
    }
  ]
}
```

`nodeType`:

- `widget`
- `container`
- `button`
- `data`
- `status`
- `action`

`edgeType`:

- `dependsOn`
- `filters`
- `enables`
- `requires`
- `invalidates`
- `refreshes`

`refreshPolicy`:

- `local`
- `server`
- `serverDebounced`
- `manual`

## 13. Capability Protocol

### 13.1 Responsibility

`capabilityProtocol` declares which runtime capabilities the page needs and which are available for the current user, edition, product, and client.

It must be derived from backend entitlement and delivery policy. Frontend must not infer capabilities from groups.

### 13.2 Shape

```json
{
  "requiredCapabilities": [
    {
      "capabilityKey": "project.form.edit",
      "state": "allow",
      "reasonCode": "",
      "source": "entitlement"
    }
  ],
  "runtimeCapabilities": {
    "upload": true,
    "inlineEdit": true,
    "batchAction": false,
    "ganttRender": false
  }
}
```

`state`:

- `allow`
- `readonly`
- `deny`
- `hidden`

## 14. Component Registry

### 14.1 Responsibility

`componentRegistry` maps semantic widget/container types to approved frontend component adapters.

It prevents contracts from embedding component code while still allowing multi-client component adaptation.

### 14.2 Shape

```json
{
  "registryVersion": "2.0.0",
  "components": [
    {
      "semanticType": "input",
      "adapterKey": "field.input.basic",
      "clientTypes": ["web_pc", "wx_mini", "harmony_h5"],
      "fallbackAdapterKey": "field.readonly.text"
    }
  ]
}
```

Rules:

- Contract may reference `adapterKey`.
- Frontend owns adapter implementation.
- Backend owns semantic selection.
- Missing adapter must degrade by `fallbackAdapterKey`, never by frontend business inference.

## 15. Selector Status

### 15.1 Responsibility

`selectorStatus` governs global selectors and scoped selectors, especially project-level isolation.

It covers:

- current project selector
- company selector
- role surface selector
- scene selector
- record scope selector

### 15.2 Shape

```json
{
  "selectors": [
    {
      "selectorId": "current_project",
      "selectedValue": 1,
      "required": true,
      "locked": false,
      "source": "system.init",
      "reasonCode": ""
    }
  ]
}
```

Frontend must pass selector context back to backend action/data calls. Backend remains the final authority.

## 16. Multi-Client Governance

### 16.1 Rule

Client trimming must be a governance layer after v2+ assembly:

```text
UnifiedPageContract v2+
-> client trimming
-> client-specific payload
```

Trimming can alter:

- layout density
- columns
- component adapter key
- unsupported widget fallback
- default container collapse

Trimming cannot alter:

- permission result
- action ID
- field/widget/container/data IDs
- business value
- selector state

### 16.2 Required Matrix

Every representative page must have snapshots for:

- `web_pc`
- `wx_mini`
- `harmony_h5`

The matrix must prove stable IDs across all clients.

## 17. Trace and Snapshot

### 17.1 Trace Policy

Every contract and patch response must expose:

- `traceId`
- `requestId`
- `intent`
- `actionId` when applicable
- `contractVersion`
- `schemaVersion`
- `clientType`
- `sourceRefs`

### 17.2 Snapshot Policy

Snapshots must cover:

- full contract shape
- status contract
- action IDs
- data key stability
- client trimming matrix
- patch result shape

Snapshots must not include volatile data unless normalized.

## 17.3 Cache Policy

Every contract-producing path should support:

- `etag`
- `snapshotId`
- optional cache scope

`snapshotId` is used for:

- undo
- history replay
- debug
- trace
- collaboration

## 18. AI Integration

### 18.1 Allowed AI Roles

AI may assist with:

- contract draft generation
- layout recommendations
- action rule suggestions
- field grouping suggestions
- regression explanation
- snapshot diff explanation

AI must not be a runtime authority for:

- permission decisions
- business state changes
- financial calculations
- record scope checks
- final action execution

### 18.2 AI Contract Envelope

AI-produced suggestions must enter as suggestions, not executable contract:

```json
{
  "aiSuggestion": {
    "suggestionId": "ai.layout.project.form.001",
    "target": "layoutContract",
    "confidence": 0.82,
    "requiresReview": true,
    "payload": {}
  }
}
```

Human/backend governance must approve before the suggestion becomes contract output.

## 19. Anti-DSL VM Guardrail

The most important long-term risk is contract drift into an unmaintainable DSL VM.

### 19.1 Hard Limits

The contract must not contain:

- arbitrary expressions
- embedded scripts
- loops
- custom functions
- client-side business rules
- dynamic imports
- component implementation code
- nested action programs that behave like workflow code

### 19.2 Allowed Expression Model

If conditional behavior is required, the contract may reference backend-owned expression IDs:

```json
{
  "conditionRef": {
    "conditionId": "project.can_submit",
    "verdict": true,
    "reasonCode": ""
  }
}
```

Frontend may read `verdict`; frontend must not recompute `conditionId`.

### 19.3 Complexity Budget

Each contract should track:

- action count
- dependency edge count
- patchable node count
- maximum container depth
- unsupported widget count

Guard thresholds should fail or warn when a page exceeds maintainable runtime complexity.

## 19.4 ID Governance

The following IDs must remain stable:

- `pageId`
- `sceneKey`
- `containerId`
- `widgetId`
- `fieldCode`
- `btnId`
- `actionId`
- `dataKey`

IDs must not encode role, permission, or lifecycle variation.

Forbidden:

```text
field.price.admin
field.price.user
```

Required:

```text
field.price
+ statusContract
```

## 19.5 Frontend Runtime Architecture

The frontend runtime should be composed of:

```text
Contract Store
+ Patch Engine
+ Renderer
+ Action Dispatcher
+ Dependency Graph
+ Reactive Scheduler
```

Frontend must not own:

- role inference
- business inference
- permission inference
- linkage inference
- workflow inference

## 20. Compatibility Mapping

| Current Source | v2+ Target |
| --- | --- |
| `scene_contract_v1.scene/page` | `pageInfo` |
| `scene_contract_v1.zones/blocks` | `layoutContract.containerList` |
| `scene_contract_v1.permissions` | `statusContract.globalStatus` |
| `page_orchestration_v1.zones` | `layoutContract.containerList` |
| `page_orchestration_v1.action_schema` | `actionContract.actionRuleList` |
| `page_orchestration_v1.data_sources` | `dataContract` |
| `ui.contract.fields/views` | `layoutContract` + `dataContract.dictData` |
| `ui.contract.field_policies` | `statusContract.widgetStatus` |
| `ui.contract.action_policies` | `statusContract.buttonStatus` + `actionContract` |
| `api.onchange.patch` | `updateData` |
| `api.onchange.modifiers_patch` | `updateStatus` |
| `role_surface/default_route` | `runtimeContract.selectorStatus` + `pageInfo` |
| `capabilities/entitlement` | `runtimeContract.capabilityProtocol` |
| frontend component maps | `runtimeContract.componentRegistry` |

## 21. Versioning

`UnifiedPageContract v2+` must use semantic versioning:

```text
2.0.0
```

Rules:

- Additive optional fields: minor version.
- Required field changes: major version.
- Enum additions: minor version unless frontend must handle new default behavior.
- Behavior semantic changes: major version.

## 22. Governance Requirements

Every v2+-producing path must provide:

- `traceId`
- `contractVersion`
- `schemaVersion`
- source references
- compat mode separation
- snapshot support
- shape guard support
- complexity budget metrics
- client trimming matrix where applicable

Default mode must not expose debug fields outside `meta.debug`.

## 23. Evolution Roadmap

### Phase 1: Schema Freeze

Freeze top-level shape, four semantic subcontracts, `RuntimeContract`, enums, and examples.

### Phase 2: Assembler

Map existing contract families into v2+ behind debug/compat flags.

### Phase 3: Runtime Protocol

Implement patch engine, dependency graph, capability protocol, component registry, selector status, and tracing.

### Phase 4: Client Matrix

Add `web_pc`, `wx_mini`, and `harmony_h5` trimming with stable ID snapshots.

### Phase 5: Frontend Default Migration

Move frontend default path to v2+ schema -> store -> page. Keep legacy paths compat-only.

### Phase 6: AI-Assisted Contract Governance

Allow AI suggestions only as non-executable reviewed payloads.

## 24. Protocol Lifecycle

### 24.1 Contract Build Lifecycle

The full build chain is:

```text
native facts collected
-> semantic facts normalized
-> scene composed
-> unified contract assembled
-> client trimmed
-> shape guarded
-> snapshot recorded
-> frontend consumed
```

Every step MUST have explicit input and output. Private structures must not leak across layers.

### 24.2 Runtime Interaction Lifecycle

Every interaction MUST follow:

```text
frontend collect context
-> dispatch actionId
-> backend evaluate semantics
-> backend emit patch/full contract
-> frontend patch merge
-> dependency schedule
-> render commit
-> trace/snapshot update
```

Frontend may manage local loading, dirty, focus, and toast feedback. Frontend must not change business verdicts.

### 24.3 Compatibility Lifecycle

Legacy compatibility must follow:

```text
introduce
-> observe
-> default
-> deprecate
-> remove
```

`meta.compat` exists for migration only. It must not become the entry point for new features.

## 25. Schema Freeze Boundary

Batch-A MUST freeze:

- required top-level keys: `pageInfo/layoutContract/statusContract/actionContract/dataContract/runtimeContract/meta`
- governed optional top-level extension: `formStructureContract`
- ID rules: stable ID list and forbidden suffix rules
- client enum: first-release and deferred client values
- patch protocol: partial/full plus patch operation enum
- action lifecycle: standard phases and ownership
- component registry: `componentKey` and adapter constraints
- capability protocol: capability declaration and bounded `componentConfig`
- selector status: selector patch and inheritance rules
- trace/snapshot: minimum required fields
- Anti-DSL VM: forbidden fields and static guard rules

Backend assembler work must not start before the freeze boundary is accepted.

## 26. Open Decisions

| Decision | Candidate | Recommendation |
| --- | --- | --- |
| Whether `mobile_app` enters first-release enum | first-release / future extension slot | Future extension slot; freeze `web_pc/wx_mini/harmony_h5` first |
| `componentRegistry` placement | `layoutContract` / `runtimeContract` | Semantic reference in `layoutContract`, governance registry in `runtimeContract` |
| `dependencyGraph` placement | `actionContract` / `runtimeContract` | Runtime control plane, so `runtimeContract` |
| `selectorStatus` placement | `statusContract` / `runtimeContract` | Status verdict in `statusContract`, selector governance in `runtimeContract` |
| Whether AI suggestion enters standard contract | inline / independent envelope | Non-executable suggestion envelope only |

## 27. Guard Requirements

Minimum guard set:

- top-level shape guard
- enum guard
- stable ID guard
- no role/client suffix ID guard
- Anti-DSL VM guard
- compat leakage guard
- client trimming stable ID guard
- patch operation allowlist guard
- frontend private field guard
- snapshot volatility normalization guard

Any guard failure blocks v2+ from becoming the default frontend contract.

## 28. Risk Control

| Risk | Control |
| --- | --- |
| Contract becomes DSL VM | Anti-DSL guard, no scripts, no loops, no frontend business rule evaluation |
| Multiple contract families persist forever | v2+ default path, compat lifecycle, snapshot gates |
| Multi-client branches business logic | client trimming matrix and stable ID guard |
| Runtime becomes opaque | trace policy, snapshot policy, complexity budget |
| Frontend reintroduces semantic inference | schema -> store -> page guard |
| AI produces unsafe executable output | AI suggestions require backend/human governance |

## 29. Acceptance Criteria

The design is accepted when:

- The top-level package is frozen.
- The four subcontract boundaries are stable.
- `RuntimeContract` is defined as control plane, not semantic contract.
- Client type enum is stable.
- Existing contract families have a mapping path.
- Incremental update shape is defined.
- Patch engine, dependency graph, capability protocol, component registry, selector status, trace/snapshot, and AI integration boundaries are defined.
- Anti-DSL VM guardrails are explicit.
- The implementation plan can drive Batch-A without changing runtime behavior.

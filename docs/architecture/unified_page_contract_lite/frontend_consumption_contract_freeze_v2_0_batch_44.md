# Unified Semantic Page Contract Lite - Frontend Consumption Contract Freeze v2.0

Date: 2026-05-02
Status: frozen for frontend pilot implementation

## 1. Boundary

Layer Target: Contract Governance / Lite v2.0 Freeze

Module:

- `docs/architecture/unified_page_contract_lite`
- `scripts/verify`
- `Makefile`

Reason:

Frontend can only match a stable protocol. This batch freezes the minimum
Lite v2.0 contract surface that frontend may implement against.

This batch does not modify frontend implementation.

## 2. Decision

Decision:

```text
unified_page_contract_lite_v2_0_frontend_consumption_frozen
```

The frontend may now implement a controlled pilot against this frozen Lite
v2.0 surface.

## 3. Canonical Contract Shape

The only canonical Lite v2.0 full contract shape is:

```json
{
  "pageInfo": {},
  "layoutContract": {},
  "statusContract": {},
  "actionContract": {},
  "dataContract": {},
  "meta": {}
}
```

No other top-level contract key is allowed.

The authoritative schema is:

```text
docs/architecture/unified_page_contract_lite/unified_page_contract_lite.schema.json
```

The frontend matching baseline example is:

```text
docs/architecture/unified_page_contract_lite/project_form_lite.example.json
```

## 4. Frozen Version

The frozen version is:

```text
contractVersion = 2.0.0
```

Rules:

- `pageInfo.contractVersion` must be exactly `2.0.0`
- opt-in request `contractVersion` must be exactly `2.0.0`
- opt-in response `contractVersion` must be exactly `2.0.0`
- any incompatible change must use a new version
- no implicit version upgrade is allowed

## 5. Frozen Layer Responsibilities

### 5.1 PageInfo

Frozen fields:

```text
pageId
sceneKey
model
viewType
clientType
contractVersion
```

PageInfo only identifies the page and running client. It must not contain
data, status, action execution logic, cache strategy, or render strategy.

### 5.2 LayoutContract

Frozen shape:

```text
layoutType
containerList
```

Container frozen fields:

```text
containerId
containerType
title
children
widgetList
```

Widget frozen fields:

```text
widgetId
widgetType
fieldCode
label
component
props
```

LayoutContract only describes structure. It must not contain permission,
readonly, required, disabled, business rule, or data value.

### 5.3 StatusContract

Frozen shape:

```text
widgetStatus
buttonStatus
```

WidgetStatus frozen fields:

```text
widgetId
visible
readonly
required
disabled
```

ButtonStatus frozen fields:

```text
btnId
visible
disabled
```

StatusContract is fully backend generated. Frontend must not infer these
values from role, groups, model, workflow state, or field name.

### 5.4 ActionContract

Frozen shape:

```text
actionRuleList
```

ActionRule frozen fields:

```text
actionId
triggerType
sourceWidgetId
dispatchMode
refreshMode
```

Frozen rule:

```text
dispatchMode = server
```

Frontend must only dispatch `actionId` with context. It must not execute
business rules, condition branches, chained actions, loops, workflow DSL,
JSON logic, or local semantic linkage.

### 5.5 DataContract

Frozen shape:

```text
mainData
relationData
dictData
```

DataContract only carries renderable data. It must not carry permission,
readonly, required, workflow, or action execution semantics.

### 5.6 Meta

Frozen required fields:

```text
etag
traceId
```

Optional allowed field:

```text
semanticAdapter
```

Meta is for trace and adapter identity. It must not become a legacy payload
escape hatch or frontend-private extension area.

## 6. Frozen Patch Shape

The only Lite v2.0 partial patch shape is:

```json
{
  "updateType": "partial",
  "operation": "merge",
  "statusPatch": {},
  "dataPatch": {},
  "layoutPatch": {}
}
```

Allowed operations:

```text
merge
replace
```

Forbidden patch behavior:

- append operation
- reorder operation
- transition operation
- stream operation
- hydration operation
- scheduler operation

The authoritative patch example is:

```text
docs/architecture/unified_page_contract_lite/patch_lite.example.json
```

## 7. Frozen Opt-In Envelope

Frontend may only request Lite through an explicit opt-in preview envelope:

```json
{
  "contractMode": "lite_preview",
  "contractVersion": "2.0.0",
  "entryPoint": "load_contract",
  "clientType": "web_pc",
  "fallbackMode": "legacy_default"
}
```

The current frontend pilot source entry remains:

```text
load_contract opt-in preview
```

The current frontend pilot candidate remains:

```text
project.project:tree
```

## 8. Frozen Frontend Matching Rules

Frontend implementation must follow this order:

```text
schema/types -> store/adapter -> page renderer
```

Frontend must:

- validate or type the Lite v2.0 shape before page use
- consume only declared fields
- keep feature flag default-off
- keep legacy fallback
- keep the pilot allowlist narrow
- dispatch action by `actionId`
- apply only `merge` or `replace` patches

Frontend must not:

- infer permission, readonly, required, disabled, or workflow
- consume `ui.contract` for Lite
- touch `login`
- touch `system.init`
- make Lite the default page contract
- consume Lite outside the pilot allowlist
- parse or execute business DSL
- add frontend-private fields to the canonical contract

## 9. Explicitly Not Frozen

These are not part of Lite v2.0 and remain blocked:

```text
runtimeContract
componentRegistry
capabilities
selectorStatus
dependencyGraph
dataSource
subscription
stream
hydration
scheduler
AI envelope
workflow DSL
JSON logic
```

Any future addition requires a new bounded design batch and a compatibility
decision.

## 10. Required Gate

The frozen contract must remain guarded by:

```bash
make verify.unified_page_contract.lite.contract_freeze_v2_0
make verify.unified_page_contract.lite
make verify.unified_page_contract.lite.frontend_pilot_readiness
```

Before frontend implementation begins, also keep:

```bash
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.load_contract_live_scope.container
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.startup_negative.container
make verify.frontend.quick.gate
```

## 11. Compatibility Policy

Compatible changes:

- add enum values only after frontend declares support
- add optional fields only after a new schema version or explicit compat plan
- add new client types only after adapter coverage exists

Breaking changes:

- removing any frozen field
- renaming any frozen field
- changing `contractVersion=2.0.0` semantics
- changing ActionContract into a local rule engine
- moving status semantics into layout or data
- making Lite default without a migration phase

Breaking changes require a new version and cannot be shipped silently.

## 12. Rollback

This batch makes no frontend runtime change.

Rollback:

```text
remove this freeze document, guard, and Makefile target
```

Future frontend pilot rollback remains:

```text
set VITE_LITE_CONTRACT_PILOT=0 and redeploy frontend
```

# Unified Page Contract v2+ Implementation Plan

Date: 2026-05-01
Status: Direction pivoted to Unified Semantic Page Contract Lite
Layer Target: Contract Governance Layer
Module: `docs/architecture`, future `addons/smart_core`, `addons/smart_scene`, `frontend/apps/web`

## Direction Correction

The previous v2+ batches A-G are retained as exploratory governance assets, but the active implementation path is now `Unified Semantic Page Contract Lite`.

Current decision:

- Do not continue the runtime-heavy Batch-H migration.
- Do not make `runtimeContract` part of the active current-stage protocol.
- Defer component registry, selector status, dependency graph, realtime, collaboration, AI orchestration, hydration, virtualization, and scheduler work.
- Focus Phase 1 on Odoo Semantic Adapter, Lite contract, thin patch merge, and multi-terminal renderer.

Active Lite verification:

```bash
make verify.unified_page_contract.lite
```

## Lite Phase-1 Task Checklist

- [x] Freeze six-key top-level shape: `pageInfo/layoutContract/statusContract/actionContract/dataContract/meta`.
- [x] Remove `runtimeContract` from active current-stage protocol.
- [x] Simplify `LayoutContract` to `layoutType + containerList`.
- [x] Simplify widgets to `widgetId/widgetType/fieldCode/label/component/props`.
- [x] Keep `StatusContract` backend-owned with `widgetStatus/buttonStatus`.
- [x] Restrict `ActionContract` to event declaration and server dispatch.
- [x] Simplify `DataContract` to `mainData/relationData/dictData`.
- [x] Restrict patch operations to `replace/merge`.
- [x] Add Lite schema/example/patch guard.
- [ ] Implement Odoo XML semantic adapter closure.
- [ ] Normalize Odoo modifiers into `StatusContract`.
- [ ] Normalize onchange into partial patch.
- [ ] Normalize x2many patch semantics.
- [ ] Normalize ACL + record rule into `StatusContract`.
- [ ] Add thin frontend ContractStore/PatchMerge/Renderer/ActionDispatcher.

## Batch Information (Exploratory v2+ Track)

- Batch family: `UnifiedPageContract v2+`
- Goal: migrate from multiple transition contract surfaces to one canonical enterprise semantic UI runtime protocol.
- Scope: contract schema, backend assembler, status/action/data consolidation, runtime protocol, client trimming, frontend consumer migration.
- Not doing now: no runtime code change in this document batch, no public intent rename, no removal of legacy contract paths.

## Master Task Checklist

This checklist is the execution index for later batches. A task can be checked only after its own acceptance and verification criteria pass.

### Batch A: Schema Freeze

- [x] Add `UnifiedPageContract v2+` JSON schema.
- [x] Add enum registry for client, layout, status, action, and runtime fields.
- [x] Add ID governance rules and forbidden role/permission ID variants.
- [x] Freeze schema boundary for top-level keys, patch protocol, action lifecycle, component registry, capability protocol, selector status, trace/snapshot, and Anti-DSL VM rules.
- [x] Add form example payload.
- [x] Add table/list example payload.
- [x] Add tree example payload.
- [x] Add nested form plus relation table example payload.
- [x] Add compatibility mapping from existing contracts to v2+.
- [x] Add static schema parse validation.
- [x] Add anti-DSL VM guardrail section to schema comments/docs.
- [x] Add minimum guard list:
  - [x] top-level shape guard
  - [x] enum guard
  - [x] stable ID guard
  - [x] no role/client suffix ID guard
  - [x] compat leakage guard
  - [x] patch operation allowlist guard
  - [x] frontend private field guard
  - [x] snapshot volatility normalization guard

### Batch B: Backend Assembler

- [x] Add v2+ assembler module.
- [x] Map `scene_contract_v1` to v2+.
- [x] Map `page_orchestration_v1` to v2+.
- [x] Map selected `ui.contract` output to v2+.
- [x] Add v2+ shape guard.
- [x] Add representative v2+ snapshots.
- [x] Expose v2+ behind debug/compat flag only.

### Batch C: StatusContract Consolidation

- [x] Inventory all current status sources.
- [x] Define status precedence rules.
- [x] Generate `globalStatus`.
- [x] Generate `containerStatus`.
- [x] Generate `widgetStatus`.
- [x] Generate `buttonStatus`.
- [x] Add create/edit/readonly status regression samples.

### Batch D: ActionContract Consolidation

- [x] Map onchange behavior to `actionRuleList`.
- [x] Map button behavior to `actionRuleList`.
- [x] Map save/validate/delete behavior to `actionRuleList`.
- [x] Define partial update response mapper.
- [x] Preserve `api.onchange` compatibility.
- [x] Add chain action sample.
- [x] Add action ID uniqueness guard.

### Batch E: DataContract Consolidation

- [x] Map main record data to `mainData`.
- [x] Map list rows to `tableRows`.
- [x] Map relation rows to `relationRows`.
- [x] Map tree data to `treeData`.
- [x] Map dictionary/options to `dictData`.
- [x] Add `dataSource` metadata for query identity, cache policy, consistency, and subscription flags.
- [x] Add pagination and data meta.
- [x] Add data key stability guard.

### Batch F: RuntimeContract Protocol

- [x] Add `RuntimeContract` control-plane schema.
- [x] Add fixed Patch Engine operation registry.
- [x] Add Dependency Graph schema and guard.
- [x] Add Capability Protocol schema.
- [x] Add Component Registry schema.
- [x] Add Selector Status schema.
- [x] Add Trace/Snapshot policy schema.
- [x] Add AI suggestion envelope schema.
- [x] Add complexity budget metrics and thresholds.
- [x] Add anti-DSL VM static guard.

### Batch G: Client Trimming

- [x] Add `X-SC-Client-Type` resolver.
- [x] Default missing/invalid client to `web_pc`.
- [x] Add `web_pc` trimming policy.
- [x] Add `wx_mini` trimming policy.
- [x] Add `harmony_h5` trimming policy.
- [x] Decide whether `mobile_app` is a frozen enum or future extension slot for this release.
- [x] Add stable ID assertions across clients.
- [x] Add client snapshot matrix.

### Batch H: Frontend Consumer Migration

- [ ] Add frontend TypeScript types for v2+.
- [ ] Add schema-to-store mapper.
- [ ] Add v2+ page assembly model.
- [ ] Add fixed Patch Engine client adapter.
- [ ] Add runtime capability reader.
- [ ] Add component registry adapter resolver.
- [ ] Add Contract Store / Patch Engine / Renderer / Action Dispatcher / Dependency Graph / Reactive Scheduler boundary spec.
- [ ] Migrate one low-risk page path.
- [ ] Migrate primary form/list path.
- [ ] Move legacy `ui.contract` model/action consumers to compat-only.
- [ ] Add frontend v2+ consumer guards.

## Batch A: Schema Freeze

### Goal

Freeze the v2+ contract schema and field enums.

### Scope

- `docs/architecture`
- `docs/architecture/unified_page_contract_v2`
- `scripts/verify/unified_page_contract_v2_schema_guard.py`
- `Makefile` verification target wrapper
- No backend runtime implementation.
- No frontend runtime implementation.

### Tasks

1. Create `UnifiedPageContract v2+` JSON schema.
2. Add enum registry for:
   - `clientType`
   - `layoutType`
   - `adaptMode`
   - `containerType`
   - `widgetType`
   - `pageAuth`
   - `triggerType`
   - `actionType`
   - `refreshMode`
   - `submitPolicy`
   - `runtimeMode`
   - `patchOperation`
   - `dependencyNodeType`
   - `dependencyEdgeType`
   - `capabilityState`
3. Add ID governance section:
   - stable ID list
   - forbidden role/permission/lifecycle suffixes
   - mapping from state variants to `StatusContract`
4. Freeze schema boundary:
   - top-level keys
   - client enum
   - patch protocol
   - action lifecycle
   - component registry
   - capability protocol
   - selector status
   - trace/snapshot minimum fields
   - Anti-DSL VM forbidden field list
5. Add example payloads for:
   - form
   - table/list
   - tree
   - complex nested form with relation table
6. Add compatibility mapping table from current contracts to v2+.
7. Add `RuntimeContract` schema into the same top-level contract.
8. Add anti-DSL VM rules to the schema notes.
9. Add a static schema validation script plan or placeholder.
10. Add minimum guard plan and expected outputs.

### Acceptance

- v2+ schema exists and matches the design document.
- Example payloads validate against schema.
- Required top-level keys are fixed to `pageInfo/layoutContract/statusContract/actionContract/dataContract/runtimeContract/meta`.
- Governed optional top-level extension `formStructureContract` is explicitly documented and guarded.
- Schema freeze boundary is explicit enough to implement JSON Schema without new semantic decisions.
- No public intent behavior changes.
- `git diff --check` passes.

### Verification

- `make verify.unified_page_contract.v2.schema`
- `git diff --check`
- JSON schema parse check through the Makefile guard.
- Documentation link check where available.

### Rollback

- Revert only Batch-A documentation/schema files.

### Stop Conditions

- Any top-level key beyond the fixed seven keys is required.
- Any new semantic peer contract beside Layout/Status/Action/Data is proposed.
- `RuntimeContract` starts carrying business semantics.
- Client type changes action IDs or field IDs.
- ID naming encodes role, permission, lifecycle, or client variants.

## Batch B: Backend Assembler

### Goal

Build a backend assembler that maps existing contract sources into `UnifiedPageContract v2+`.

### Scope

- `addons/smart_core` contract governance helpers.
- `addons/smart_scene` adapter if needed.
- Snapshot/guard scripts.
- No frontend default migration.
- No public intent or startup chain response switch.

### Tasks

1. Add `UnifiedPageContractAssembler`.
2. Map `scene_contract_v1` to v2+.
3. Map `page_orchestration_v1` to v2+.
4. Map selected `ui.contract` model/action output to v2+.
5. Map `api.onchange` compatibility output to `UnifiedPagePatch v2+`.
6. Add `runtimeContract` assembly with empty safe defaults.
7. Add shape guard for v2+.
8. Add snapshots for representative pages.
9. Expose v2+ only in debug/compat mode first.

### Acceptance

- Representative form/list scenes produce v2+ payload.
- v2+ output does not remove legacy fields.
- Shape guard passes.
- Contract snapshot passes.

### Verification

- `make verify.unified_page_contract.v2`
- v2+ schema guard target
- v2+ assembler guard target
- Python compile for touched backend files through Makefile

### Rollback

- Disable v2+ assembler exposure flag.
- Revert assembler and guard files.

### Stop Conditions

- Assembler changes business permissions.
- Assembler mutates scene provider semantics.
- Legacy contract output changes unexpectedly.

## Batch C: StatusContract Consolidation

### Goal

Normalize permission and state sources into `StatusContract`.

### Scope

- Backend contract governance layer.
- Existing policy sources remain authoritative.
- Frontend still consumes old path unless explicitly gated.

### Tasks

1. Inventory current state sources:
   - `permissions`
   - `field_policies`
   - `action_policies`
   - `modifiers`
   - `permission_surface`
   - `access_policy`
2. Define precedence rules.
3. Generate `globalStatus`.
4. Generate `containerStatus`.
5. Generate `widgetStatus`.
6. Generate `buttonStatus`.
7. Generate `selectorStatus`.
8. Add create/edit/readonly regression samples.

### Acceptance

- Create/edit generated fields can be governed by `StatusContract`.
- Button enabled/disabled can be proven from `StatusContract`.
- No frontend business inference is introduced.

### Verification

- `make verify.unified_page_contract.v2`
- `make verify.unified_page_contract.v2.status`
- status contract snapshot baseline
- Python compile for touched backend files through Makefile

### Rollback

- Disable StatusContract emission flag.
- Revert status normalizer only.

### Stop Conditions

- Frontend needs to infer role or permission.
- Status source conflict cannot be resolved by documented precedence.

## Batch D: ActionContract Consolidation

### Goal

Unify interaction behavior under `ActionContract`.

### Scope

- Backend action rule builder.
- Existing `api.onchange`, `execute_button`, route actions remain available.
- Frontend dispatch adapter may be introduced behind a flag.

### Tasks

1. Map field onchange to `actionRuleList`.
2. Map button actions to `actionRuleList`.
3. Map save/validate/delete to `actionRuleList`.
4. Define partial update response mapper.
5. Preserve `api.onchange` as implementation detail.
6. Add chain action sample.
7. Add action ID uniqueness guard.

### Acceptance

- Field change can be represented by `actionId`.
- Button click can be represented by `actionId`.
- Backend returns `partial` update shape for onchange-compatible flows.
- Existing execute/onchange behavior remains compatible.

### Verification

- `make verify.unified_page_contract.v2`
- `make verify.unified_page_contract.v2.action`
- action contract snapshot baseline
- Python compile for touched backend files through Makefile

### Rollback

- Disable ActionContract runtime flag.
- Keep existing direct `api.onchange` and `execute_button` paths.

### Stop Conditions

- ActionContract starts executing business logic directly in frontend.
- Action IDs are generated differently per client.

## Batch E: DataContract Consolidation

### Goal

Normalize page data into `DataContract`.

### Scope

- Backend contract/data adapter.
- Existing `api.data` remains data execution path.
- No table rendering rewrite unless explicitly scheduled.

### Tasks

1. Map main record data to `mainData`.
2. Map list rows to `tableRows`.
3. Map relation rows to `relationRows`.
4. Map tree data to `treeData`.
5. Map dictionary/options to `dictData`.
6. Add `dataSource` metadata:
   - query identity
   - cache policy
   - consistency hint
   - subscription flag
7. Add pagination and data meta.
8. Add data key stability guard.

### Acceptance

- Form and list can be described by `LayoutContract + DataContract`.
- Dictionary data is available without frontend ad hoc mapping.
- Data keys remain stable across clients.
- `dataSource` contains only metadata, not SQL or business permission rules.

### Verification

- `make verify.unified_page_contract.v2`
- `make verify.unified_page_contract.v2.data`
- data contract snapshot baseline
- Python compile for touched backend files through Makefile

### Rollback

- Disable DataContract emission flag.
- Keep existing `api.data` and form runtime data paths.

### Stop Conditions

- DataContract duplicates business computation.
- Data keys differ by client type.
- `dataSource` exposes raw SQL or frontend-owned filtering semantics.

## Batch F: RuntimeContract Protocol

### Goal

Add the v2+ runtime control plane without turning the contract into a DSL VM.

### Scope

- Backend contract governance layer.
- Schema/guard/snapshot scripts.
- Optional frontend adapter only after backend shape is stable.
- No business rule execution in frontend.

### Tasks

1. Add `RuntimeContract` safe default builder.
2. Add fixed Patch Engine operation registry:
   - `replace`
   - `merge`
   - `append`
   - `remove`
   - `reorder`
   - `invalidate`
3. Add Dependency Graph schema.
4. Add Capability Protocol schema.
5. Add Component Registry schema.
6. Add Selector Status schema.
7. Add Trace/Snapshot policy schema.
8. Add AI suggestion envelope schema.
9. Add complexity budget metrics.
10. Add cache/snapshot policy:
    - `etag`
    - `snapshotId`
    - cache scope
11. Add anti-DSL VM static guard.

### Acceptance

- `runtimeContract` exists in v2+ payload.
- Runtime defaults are safe and non-executable.
- Patch operations are selected from fixed enum only.
- Dependency graph contains edges only, not business expressions.
- AI payloads are suggestions only, not executable contract.
- Complexity budget is emitted or computable.
- `etag` and `snapshotId` are defined for contract and patch traceability.

### Verification

- `make verify.unified_page_contract.v2`
- `make verify.unified_page_contract.v2.runtime`
- runtime pure unit tests and mobile compact contract tests
- runtime contract snapshot baseline
- anti-DSL VM guard
- schema parse check through Makefile

### Rollback

- Disable `runtimeContract` emission or emit empty safe defaults.
- Keep existing Layout/Status/Action/Data contract output.

### Stop Conditions

- Contract contains arbitrary expressions, scripts, loops, or functions.
- Frontend is required to recompute backend business conditions.
- Runtime graph changes permission, action, or data semantics.

## Batch G: Client Trimming

### Goal

Add terminal-specific contract trimming without changing semantics.

### Scope

- Request client type resolver.
- Contract trimming layer.
- Snapshot matrix for `web_pc`, `wx_mini`, `harmony_h5`.
- No UniApp app implementation yet unless separately scheduled.

### Tasks

1. Add `client_type` resolver from `X-SC-Client-Type`.
2. Default missing/invalid client to `web_pc`.
3. Add trimming policy:
   - PC keeps wide layout.
   - Mini program uses single-column/mobile components.
   - Harmony H5 reuses H5/mobile strategy.
4. Decide `mobile_app` status:
   - future extension slot, or
   - first-release supported client.
5. Add ID stability assertions.
6. Add unsupported widget fallback policy.
7. Add snapshot matrix.

### Acceptance

- Same page produces stable IDs across all clients.
- Only layout/component hints differ.
- Business/status/action/data semantics remain identical.
- `mobile_app` is either explicitly guarded or explicitly deferred.

### Verification

- `make verify.unified_page_contract.v2`
- `make verify.unified_page_contract.v2.client`
- client trimming snapshot matrix
- semantic signature guard across stable clients

### Rollback

- Disable client trimming and default to `web_pc`.

### Stop Conditions

- Client type changes permission, action IDs, or data keys.
- Terminal adaptation requires business branching.

## Batch H: Frontend Consumer Migration

### Goal

Make frontend default path consume `UnifiedPageContract v2+`.

### Scope

- `frontend/apps/web` schema/types.
- Store mapping.
- Page assembly layer.
- Render components.
- Compat paths remain under explicit compatibility mode.

### Tasks

1. Add TypeScript types for v2+.
2. Add schema-to-store mapper.
3. Add page assembly model for v2+.
4. Add fixed Patch Engine adapter.
5. Add runtime capability reader.
6. Add component registry adapter resolver.
7. Add frontend runtime boundary:
   - Contract Store
   - Patch Engine
   - Renderer
   - Action Dispatcher
   - Dependency Graph
   - Reactive Scheduler
8. Migrate one low-risk page path.
9. Migrate form/list primary path.
10. Move legacy `ui.contract` model/action consumers to compat-only.
11. Add frontend contract consumer guards.

### Acceptance

- Frontend page reads v2+ through schema -> store -> page.
- Page does not directly parse backend raw response.
- Frontend Patch Engine supports only fixed operations.
- Frontend does not evaluate business rule expressions.
- Existing startup chain remains `login -> system.init -> ui.contract/scene route`.
- Typecheck passes.

### Verification

- `make verify.unified_page_contract.v2`
- frontend typecheck
- frontend static build
- frontend contract consumer guard
- stable projection guard for backend formal V2 slots and frontend compatibility boundaries
- Playwright smoke for selected pages
- restricted backend gate if API response shape touched

### Rollback

- Restore frontend default consumer to existing contract path.
- Keep v2+ mapper disabled.

### Stop Conditions

- Page-level business inference is introduced.
- Frontend runtime becomes a DSL interpreter.
- Migration requires public intent rename.
- Startup chain is bypassed.

## Cross-Batch Rules

- Contract/schema changes precede backend implementation.
- Backend implementation precedes frontend consumption.
- Frontend consumption must follow schema -> store -> page.
- No batch may change public intent names.
- No batch may branch business semantics by client type.
- Every batch must leave legacy compatibility intact until explicit removal is approved.

## Final Target

The migration is complete when:

- `UnifiedPageContract v2+` is the default frontend contract package.
- `LayoutContract`, `StatusContract`, `ActionContract`, and `DataContract` are complete enough for form/list/tree/relation workflows.
- `RuntimeContract` provides patch, dependency, capability, component, selector, trace/snapshot, AI-suggestion, and complexity controls.
- `client_type` trimming is active and proven stable.
- Legacy `ui.contract` model/action paths are compat-only.
- Contract snapshots and guards cover representative scenes.
- Anti-DSL VM guard prevents executable scripts, loops, custom functions, and frontend business rule evaluation.

# Web Frontend Contract V2 Architecture Audit V1

Date: 2026-05-13 14:07:40 +0800

Branch: `codex/project-customer-relation-maintenance`

Layer Target: Frontend Architecture / Contract Consumer

Module: `frontend/apps/web`

Reason: the Web frontend still has multiple compatibility and inference paths. The target is a frontend that renders contract v2 faithfully and remains unchanged after v2 is finalized, unless the backend contract version is explicitly upgraded.

## Executive Decision

The Web frontend must be normalized to this rule:

> Backend owns business semantics, permissions, layout intent, data sources, actions, status, and relation behavior. Frontend owns only schema validation, normalized contract storage, rendering registry, interaction dispatch, and unsupported-contract reporting.

After contract v2 is finalized, frontend product code must not change for page-specific business needs. Any required change must be expressed as a contract v2 additive extension, or as a new contract major/minor version with explicit compatibility handling.

## Scope

Covered:

- Web startup and route entry points.
- Contract loading and v2 adapters.
- Form, list, kanban, relation, action, and record rendering paths.
- Frontend data/action/onchange execution paths.
- Permission and role consumption.
- Transitional lite/legacy preview paths.
- Future backend contract upgrade handling.

Not covered in this batch:

- Runtime code refactor.
- Backend contract implementation.
- Browser acceptance after future refactor batches.

## Current Topology

Current product flow is not a single v2 consumer:

```text
backend v2 contract
  -> api/contract.ts
     -> v2 raw envelope
     -> legacy action/form projection
     -> legacy/lite/compat fields
  -> ActionView / ContractFormPage / RecordView-like runtimes
     -> page-level data reads
     -> page-level permissions
     -> page-level layout/status/action inference
     -> component rendering
```

This lets the page work today, but the architecture still makes the frontend a semantic adapter instead of a faithful contract renderer.

## Target Topology

The normalized v2 flow should be:

```text
backend contract v2
  -> ContractV2Client
     -> strict version negotiation
     -> strict schema decode
     -> ContractV2Snapshot
  -> ContractV2Store
     -> normalized immutable page/view/action/data/status state
  -> ContractV2Runtime
     -> only declared dataSource/actionRule/onchange operations
  -> ContractV2Renderer
     -> pure widget/container/action registry
     -> unsupported widget/action/status surface
```

All compatibility code must be outside the default product path, with owner, expiry, and guard coverage.

## Key Findings

### P1. V2 Is Projected Back Into Legacy By Default

Evidence:

- `frontend/apps/web/src/api/contract.ts:68` infers field type from widget type, value, and field name suffix.
- `frontend/apps/web/src/api/contract.ts:87` builds legacy field descriptors from v2 widgets.
- `frontend/apps/web/src/api/contract.ts:127` synthesizes legacy form layout.
- `frontend/apps/web/src/api/contract.ts:154` walks v2 layout and synthesizes legacy buttons.
- `frontend/apps/web/src/api/contract.ts:249` builds legacy subviews and relation policies.
- `frontend/apps/web/src/api/contract.ts:308` builds a runtime legacy projection from v2.
- `frontend/apps/web/src/api/contract.ts:508` returns the projected legacy contract with `__unified_page_contract_v2` attached.

Impact:

- The frontend has two sources of truth: raw v2 and projected legacy.
- New backend contract fields can accidentally be ignored or reinterpreted by projection logic.
- Page code keeps consuming legacy-shaped fields, so cleanup never completes.

Required normalization:

- Default product path must stop using v2-to-legacy projection.
- Keep a short-lived `compat/v2ToLegacyProjection` only for explicit legacy routes, with guard rules preventing default imports.
- New code consumes `ContractV2Snapshot`, not `ActionContractLoose` or projected `views/fields/buttons`.

### P1. Frontend Still Synthesizes Contract Semantics

Evidence:

- `frontend/apps/web/src/app/contracts/unifiedPageContractV2.ts:142` synthesizes v2 widgets from mixed row shapes.
- `frontend/apps/web/src/app/contracts/unifiedPageContractV2.ts:190` validates only broad top-level fields and `contractVersion.startsWith("2.")`.
- `frontend/apps/web/src/pages/ContractFormPage.vue:3485` synthesizes field read names from native layout, toolbar, badges, visible fields, and first 40 fallback fields.
- `frontend/apps/web/src/pages/ContractFormPage.vue:3568` maps Chinese lifecycle labels back to status codes.
- `frontend/apps/web/src/pages/ContractFormPage.vue:3599` evaluates native/Odoo modifiers in frontend.

Impact:

- The frontend is still guessing missing backend intent.
- Business labels, lifecycle states, modifier logic, and data selection can drift from backend rules.

Required normalization:

- Contract v2 schema decode must fail closed for missing required semantics.
- Status labels, status codes, modifiers, visibility, required/readonly, badges, counters, and field read scope must come from contract v2.
- Unknown required semantics must render a visible unsupported-contract diagnostic, not a heuristic fallback.

### P1. Generic Form Page Contains Business-Specific Logic

Evidence:

- `frontend/apps/web/src/pages/ContractFormPage.vue:831` contains project quick/standard intake mode checks.
- `frontend/apps/web/src/pages/ContractFormPage.vue:3396` computes action badge labels/counts from form data.
- `frontend/apps/web/src/pages/ContractFormPage.vue:3791` builds field nodes by mixing descriptors, modifiers, rights, groups, and policies.
- `frontend/apps/web/src/pages/ContractFormPage.vue:4980` reads records directly and merges contract main data.

Impact:

- A generic contract form renderer still changes when a business page changes.
- The page has to know business modes and backend data shape.

Required normalization:

- Split `ContractFormPage` into a thin route host and a pure `ContractV2FormRenderer`.
- Move project/intake behavior to backend contract extensions or a named scene/product extension zone.
- The generic renderer only consumes typed view model fields emitted from `ContractV2Store`.

### P1. Action/List/Kanban Runtime Still Bypasses V2 Data Contracts

Evidence:

- `frontend/apps/web/src/views/ActionView.vue:960` defines `ActionContractLoose` with mixed legacy and v2 fields.
- `frontend/apps/web/src/views/ActionView.vue:1248` derives create rights from legacy permission shapes.
- `frontend/apps/web/src/views/ActionView.vue:1641` passes `session.user?.groups_xmlids` into action runtime.
- `frontend/apps/web/src/views/ActionView.vue:1665` applies v2 button status over legacy button conversion.
- `frontend/apps/web/src/views/ActionView.vue` imports and calls low-level `api.data` functions for list/read/write/delete flows.

Impact:

- List and kanban surfaces are not pure contract renderers.
- Data source, button status, and permissions can come from multiple places.

Required normalization:

- Replace `ActionContractLoose` with `ContractV2ActionSnapshot`.
- Only `ContractV2Runtime` may call low-level transport APIs.
- List/Kanban components remain as pure render components, receiving rows, columns, actions, aggregate display, and command callbacks from v2 store/runtime.

### P1. Permissions And Roles Leak Into Product Rendering

Evidence:

- `frontend/apps/web/src/pages/ContractFormPage.vue:802` falls back to legacy permission shapes and permissive defaults.
- `frontend/apps/web/src/views/ActionView.vue:1641` passes frontend session groups into action runtime.
- `frontend/apps/web/src/views/RecordView.vue:340` also reads `session.user?.groups_xmlids`.

Impact:

- Frontend can make authorization/display decisions from groups instead of backend entitlement contract.
- Role changes require frontend logic awareness.

Required normalization:

- Product rendering consumes only contract v2 `permission/status/action availability` surfaces.
- Session role/group details are available to debug tools only, never to product page decision logic.

### P1. Parallel Legacy Runtimes Remain In Source

Evidence:

- `frontend/apps/web/src/router/index.ts:83` maps `/a/:actionId` to `ActionViewShell`.
- `frontend/apps/web/src/router/index.ts:84` and `:85` map `/f/:model/:id` and `/r/:model/:id` to `ContractFormPage`.
- `frontend/apps/web/src/views/RecordView.vue:185` imports raw record/action APIs and keeps its own record runtime.
- `frontend/apps/web/src/pages/ModelListPage.vue` remains a legacy redirect shell.
- `frontend/apps/web/src/app/runtime/unifiedPageContractLitePilot.ts:12` defines a lite rollout pilot.
- `frontend/apps/web/src/app/contracts/unifiedPageContractLite.ts:84` has `fallbackMode: "legacy_default"`.

Impact:

- Even when routing is mostly converged, source-level alternatives keep reappearing as fallback paths.
- Lite and legacy pilots can accidentally become product behavior.

Required normalization:

- Product route matrix must have one default renderer per page class.
- `RecordView.vue`, lite pilot, and legacy redirect shells must move to `deprecated/` or `diagnostics/`, or be removed after migration.
- Guards must fail if product routes import deprecated runtimes.

### P2. Startup Is Close But Still Has Compat Drift

Evidence:

- `frontend/apps/web/src/stores/session.ts:890` accepts only `system.init` and `session.bootstrap` as login next intents.
- `frontend/apps/web/src/stores/session.ts:1094` normalizes role surface from backend.
- `frontend/apps/web/src/stores/session.ts:1189` uses backend default route when present.
- `frontend/apps/web/src/stores/session.ts:1201` still falls back to `/` if backend route is missing.
- `frontend/apps/web/src/stores/session.ts:1218` reads navigation candidates from multiple legacy result shapes.

Impact:

- Startup is substantially contract-first, but default route and navigation remain partially permissive.

Required normalization:

- Product startup must fail closed when required route/navigation contract is missing.
- Legacy nav candidates must be isolated under explicit compatibility mode.

## Non-Necessary Paths To Retire Or Isolate

| Path | Action | Reason |
| --- | --- | --- |
| `buildRuntimeProjectionFromV2` default use | retire from product default | v2 must not be converted into legacy before rendering |
| `buildLegacyFieldDescriptor`, `buildLegacyFormLayout`, `buildLegacySubViews`, `collectV2LayoutButtons` | move to explicit compat module | these synthesize backend semantics |
| `ActionContractLoose` | replace | mixed legacy/v2 contract type hides boundary drift |
| `RecordView.vue` | remove or diagnostics-only | parallel record runtime with raw reads/writes |
| `unifiedPageContractLitePilot.ts` | retire or convert to formal version harness | lite preview is transitional, not the stable product path |
| `ModelListPage.vue` legacy redirect shell | remove after route migration | keeps route-level compatibility behavior alive |
| page-level project intake logic in `ContractFormPage.vue` | move behind backend contract extension | generic renderer must not know project-specific modes |
| frontend lifecycle label-to-code mapping | remove | backend owns status semantics |
| frontend native modifier evaluator | remove from product path | backend owns effective visibility/readonly/required |
| direct `api.data` usage in page/views | restrict to runtime client | pages should dispatch declared v2 operations only |
| product code use of `groups_xmlids` | remove | permissions must come from backend entitlement contract |

## Contract V2 Frontend Invariants

These invariants should become enforceable guards:

1. Product pages may import only `ContractV2Client`, `ContractV2Store`, `ContractV2Runtime`, and renderer registry APIs for contract execution.
2. Product pages must not import low-level `api.data` directly.
3. Product pages must not read `groups_xmlids` for visibility, action, or permission decisions.
4. Product pages must not infer field type from field name, value shape, or widget label.
5. Product pages must not synthesize layout, buttons, relation policies, status codes, or required field lists.
6. Product pages must not consume `__unified_page_contract_v2` attached to a legacy projection.
7. Unsupported required contract features must render an explicit unsupported-contract state with trace id and version, not silently fallback.
8. Compatibility modules must live under a named `compat/` boundary and cannot be imported from default product routes.

## Future Contract Upgrade Design

### Version Negotiation

Every contract request should include client support information:

```json
{
  "accepted_contract_versions": ["2.0.x"],
  "client_type": "web_pc",
  "client_contract_capabilities": [
    "container_tree.v2",
    "data_source.v2",
    "action_rule.v2",
    "relation_entry.v2",
    "status_contract.v2"
  ]
}
```

Backend response must include:

```json
{
  "contractVersion": "2.0.0",
  "contractSchema": "unified_page_contract_v2",
  "requiredCapabilities": [],
  "optionalCapabilities": []
}
```

### Semver Policy

| Change Type | Backend Contract Change | Frontend Product Code |
| --- | --- | --- |
| Patch `2.0.x` | bugfix, additive optional metadata | no product change |
| Minor `2.1.0` | additive widget/action/status family with fallback contract | renderer registry may add plugin, default renderer stays stable |
| Major `3.0.0` | breaking schema/runtime semantics | side-by-side v3 client/store/runtime, feature flag, migration plan |

### Unknown Feature Handling

- Unknown optional metadata under `extensions`, `debug`, or `meta` is ignored.
- Unknown optional widget with declared fallback renderer uses fallback renderer.
- Unknown required widget/action/data source renders unsupported state.
- Unknown required capability blocks the page and reports contract version, page id, widget/action id, and trace id.
- Frontend must not guess a missing backend field from legacy names.

### Compatibility Lifecycle

Each compatibility path must have:

- owner
- reason
- supported source route
- default product import forbidden
- expiry condition
- static guard
- removal issue or batch

Lifecycle:

```text
introduce -> observe -> product default -> deprecate old path -> remove old path
```

No compatibility path should be allowed to become the implicit default again.

## Refactor Execution Plan

### Batch A: Architecture Guard And Inventory

Deliver:

- Static guard forbidding product imports of v2-to-legacy projection, `RecordView`, direct `api.data`, and `groups_xmlids` decision paths.
- Route matrix documenting default product renderer for `/a`, `/f`, `/r`.
- Current findings linked to this audit.

Acceptance:

- Guard fails on current violations.
- Guard allowlist includes only explicit compat/diagnostic paths.

Batch A execution note:

- `scripts/verify/web_contract_v2_frontend_architecture_guard.py` now provides the executable guard.
- `docs/ops/audits/web_frontend_contract_v2_route_runtime_matrix_v1.md` locks the current route/runtime matrix.
- The guard starts in debt-lock mode because the current product path still has known P1/P2 debt. It fails if counts grow, and `WEB_CONTRACT_V2_ARCH_GUARD_STRICT=1` is reserved for the cleanup-complete state.

### Batch B: Strict V2 Schema And Store

Deliver:

- `ContractV2Client` for load and version negotiation.
- Strict `ContractV2Snapshot` decode.
- `ContractV2Store` as normalized source for page/view/action/data/status.

Acceptance:

- No default code path consumes v2 through legacy projection.
- Missing required contract fields produce unsupported-contract state.

Batch B execution note:

- `frontend/apps/web/src/app/contracts/v2/types.ts` defines the typed snapshot/store boundary.
- `frontend/apps/web/src/app/contracts/v2/schema.ts` provides strict decode without widget/layout synthesis.
- `frontend/apps/web/src/app/contracts/v2/client.ts` loads `load_contract` directly and advertises accepted v2 versions/capabilities.
- `frontend/apps/web/src/app/contracts/v2/store.ts` indexes contract state without business inference.
- `frontend/apps/web/src/app/contracts/v2/runtime.ts` resolves declared action/data-source plans only.
- The architecture guard now verifies these files exist and do not import the legacy `api/contract` projection.

### Batch C: Form Renderer Convergence

Deliver:

- Thin route host plus pure `ContractV2FormRenderer`.
- Relation field rendering through one registry path.
- No page-level project intake, lifecycle label mapping, or modifier evaluation.

Acceptance:

- `/f/:model/:id` and `/r/:model/:id` use the same v2 snapshot path.
- Form page has no direct `api.data` imports.

Batch C shadow execution note:

- `ContractFormPage` now builds a `ContractV2Store` shadow after the current contract readiness check.
- Shadow mode does not change visible rendering or replace the existing legacy projection path.
- Decode failures are exposed only as shadow diagnostics so strictness can be measured before the default renderer is replaced.
- `web_contract_v2_frontend_architecture_guard.py` now verifies the form route host contains this v2 shadow boundary.
- `scripts/verify/web_contract_v2_form_shadow_browser_smoke.js` verifies the real browser form path with HUD diagnostics and stores screenshot/JSON artifacts.
- C.2 adds shadow field-code overlap diagnostics between `ContractV2Store.widgetsByFieldCode` and the current legacy `contract.fields` projection, still without changing visible rendering.
- C.3 routes readonly form field values through the v2 store data source when the field code and data key are both present; writable fields continue to use the current form state until action/data submission is moved to v2 runtime. Browser diagnostics assert v2 field/value coverage independently from the current record's editability profile.
- C.4 reads form `containerTree` and widget field status from the decoded v2 store first, with legacy resolver fallback retained only as migration protection.
- C.5 reads button status from the decoded v2 store first for form actions; legacy button-status extraction remains a fallback until action execution moves fully to the v2 runtime.
- C.6 reads page-level `globalStatus` and `sourceContext` from the decoded v2 store first so rights/profile/default context no longer default to the legacy resolver path.
- C.7 reads `dataContract.mainData` from the decoded v2 store first for statusbar, create defaults, and record initialization; legacy main-data extraction remains a fallback.
- C.8 moves v2 store selectors for field status, button status, global status, source context, and main data into `frontend/apps/web/src/app/contracts/v2/store.ts`, keeping page code on store APIs instead of direct snapshot parsing.
- C.9 locks the form v2 store selector boundary in `web_contract_v2_frontend_architecture_guard.py`: selector APIs must live in the v2 store module and `ContractFormPage` must not redefine local selector functions.
- C.10 moves form layout `containerTree` access behind `resolveContractV2ContainerTree`, so `ContractFormPage` no longer reads `snapshot.layoutContract.containerTree` directly.
- C.11 moves v2 value-source selection behind `resolveContractV2ValueSource`, centralizing the `mainData` versus `primary` coverage decision in the store boundary.
- C.12 removes the form-only `lifecycle_state` label-to-code fallback; statusbar writes now rely on backend selection/status contract codes instead of frontend business label inference.
- C.13 removes `groups_xmlids` reads from `ContractFormPage`; form fields/actions now rely on backend policy/status plus role/capability context instead of page-level group filtering.
- C.14 removes ActionView user-group forwarding into action button runtime; list/kanban action buttons no longer infer entitlement from `groups_xmlids`.
- C.16 removes `groups_xmlids` reads from the parallel `RecordView` diagnostics path; capability checks no longer receive page-level group inputs there.
- C.17 narrows the action metadata runtime's URL redirect contract type from a loose action contract alias to `ActionUrlContractShape`, removing the local loose-contract debt without changing ActionView's main runtime contract.
- C.18 replaces ActionView's local `ActionContractLoose` alias with `ActionViewRuntimeContract` based on the schema `ActionContract`, keeping the remaining legacy/v2 projection debt explicit in `api/contract.ts`.
- C.19 isolates `RecordView` raw read/write access behind `recordDiagnosticsDataRuntime`, keeping the direct `api/data` dependency out of the parallel diagnostics view.
- C.20 isolates `ViewRelationalRenderer` relation list/create/write/unlink access behind `relationRendererDataRuntime`, preparing the component boundary for a later v2 relation action executor.
- C.21 isolates `ActionView` list/write/delete/batch/favorite data access behind `actionViewDataRuntime`, keeping list runtime hook contracts unchanged while removing the page-level direct `api/data` dependency.
- C.22 isolates `ContractFormPage` form read/write/create and relation option data access behind `contractFormDataRuntime`, removing the remaining product form page direct `api/data` dependency without changing form behavior or backend contract semantics.
- C.23 moves the Lite preview `legacy_default` fallback token into `unifiedPageContractLiteCompat`, so the API adapter and Lite schema surface reference an explicit compatibility boundary instead of carrying the fallback literal in default files.
- C.24 moves the remaining v2-to-legacy runtime projection from `api/contract.ts` into `unifiedPageContractV2CompatProjection`, leaving the API adapter as request/error orchestration and reducing the architecture guard findings to zero.
- C.25 runs the strict/frontend quick gate closure after the debt count reached zero, aligns stale guard markers with the current renderer/schema paths, and restores the grouped rows sample-limit selector in `ListPage` so the grouped runtime controls remain user-reachable.

### Batch D: Action/List/Kanban Renderer Convergence

Deliver:

- `ContractV2ActionRenderer` and pure list/kanban render components.
- Data operations through declared `dataContract.dataSource`.
- Actions through declared `actionContract.actionRuleList`.

Acceptance:

- `ActionContractLoose` removed from product path.
- ActionView no longer reads groups or legacy permissions for product decisions.

### Batch E: Legacy And Lite Retirement

Deliver:

- Remove or diagnostics-isolate `RecordView.vue`, lite pilot, and legacy redirect shells.
- Remove default imports of legacy projection helpers.

Acceptance:

- Product route matrix has no parallel runtime.
- Compat guard passes.

### Batch F: Upgrade Harness

Deliver:

- Version negotiation tests.
- Unsupported required capability tests.
- Additive patch/minor compatibility examples.
- Contract fixture snapshots for v2.0.x and v2.1.0.

Acceptance:

- Backend can add optional v2 metadata without frontend product change.
- Backend can declare unsupported required features and frontend blocks visibly.
- Major version requires side-by-side runtime, not mutation of v2 renderer.

## Verification Gates For The Full Cleanup

Minimum gates for future implementation batches:

```bash
pnpm -C frontend/apps/web typecheck:strict
pnpm -C frontend/apps/web lint
ENV=dev ENV_FILE=.env.dev make verify.frontend.build
python3 scripts/verify/web_contract_v2_frontend_architecture_guard.py
make verify.unified_page_contract.v2
make verify.docs.all
```

Browser gates after runtime changes:

- `/a/:actionId` list view renders from v2 snapshot.
- `/a/:actionId` kanban view renders from v2 snapshot.
- `/f/:model/:id` and `/r/:model/:id` render from the same v2 form path.
- Relation field add/open/edit commands dispatch declared v2 actions only.
- Missing unsupported required widget/action shows unsupported-contract state with trace id.

## Closure Criteria

This topic is complete only when:

- Default product frontend path has one v2 contract source of truth.
- Legacy projection is not imported by product routes.
- Form/list/kanban/action surfaces do not infer backend semantics.
- Data and action execution happen only through v2 runtime declarations.
- Permissions come only from backend contract status/action availability.
- Future contract upgrades are handled through version negotiation and side-by-side runtimes, not page-specific patches.

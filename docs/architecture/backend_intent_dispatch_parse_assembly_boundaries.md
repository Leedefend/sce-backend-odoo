# Backend Intent-Dispatch-Parse-Assembly Boundaries

## Scope

This note refreshes the backend contract-delivery chain after the helper-alignment cleanup batches `248-253`.

Covered flow:

1. intent entry
2. protocol handler
3. dispatch and resolve
4. native parse and fallback parse
5. view-level API projection
6. page assembly
7. finalize and delivery-surface governance
8. auxiliary bootstrap entrypoints

Goal:

- state the current canonical path from the latest code
- mark which boundaries are now clear
- isolate the residual duplication and ambiguity that remain worth cleaning

## Current Canonical Chain

### 1. Intent entry

Primary external request path:

- `/api/v1/intent`
- `ui.contract(...)`

Current responsibility:

- transport envelope
- request decoding
- routing into backend handlers

Boundary:

- should stay protocol-only
- should not infer UI semantics or perform contract shaping

### 2. `UiContractHandler`

File:

- [ui_contract.py](/mnt/e/sc-backend-odoo/addons/smart_core/handlers/ui_contract.py)

Current responsibility:

- payload digging and normalization
- `op` routing: `nav/menu/model/action_open/view`
- contract mode and surface resolution
- dispatcher construction
- envelope shaping: `etag`, response `meta`, 304 handling

Current post-dispatch behavior:

- still injects render hints
- still applies final delivery-surface governance
- now delegates repeated model/view/action-form wrappers to helpers

Boundary judgment:

- thinner than before
- now mostly protocol/routing, but not yet a pure thin controller

Target boundary:

- keep routing, normalization, response envelope
- continue pushing canonical post-dispatch shaping toward `ContractService`

### 3. `ActionDispatcher` and `ActionResolver`

Files:

- [action_dispatcher.py](/mnt/e/sc-backend-odoo/addons/smart_core/app_config_engine/services/dispatchers/action_dispatcher.py)
- [action_resolver.py](/mnt/e/sc-backend-odoo/addons/smart_core/app_config_engine/services/resolvers/action_resolver.py)

Current responsibility:

- resolve action identity and action type
- route to page/report/client/url assemblers
- keep orchestration independent from delivery shaping

Boundary judgment:

- still the cleanest segment in the chain
- responsibilities are now clearly separated:
  - resolver = action identity and down-drill
  - dispatcher = orchestration and target selection

Target boundary:

- keep both free of finalize/governance policy

### 4. Parse and persistence path

Files:

- [native_parse_service.py](/mnt/e/sc-backend-odoo/addons/smart_core/app_config_engine/services/native_parse_service.py)
- [app_view_config.py](/mnt/e/sc-backend-odoo/addons/smart_core/app_config_engine/models/app_view_config.py)

Current responsibility:

- obtain merged Odoo view
- run native parser or fallback parser
- persist parsed contract cache
- expose stable view-level contract API

Boundary judgment:

- parser coordination remains acceptable
- `AppViewConfig` is still overloaded because it spans:
  - fetch
  - parse
  - fallback
  - persistence
  - API projection
  - runtime filter invocation

Target boundary:

- acceptable for now
- still the largest single-class lifecycle concentration in the chain

### 5. View-level API projection and runtime filter

Files:

- [app_view_config.py](/mnt/e/sc-backend-odoo/addons/smart_core/app_config_engine/models/app_view_config.py)
- [contract_governance_filter.py](/mnt/e/sc-backend-odoo/addons/smart_core/app_config_engine/services/contract_governance_filter.py)

Current responsibility:

- convert parsed blocks into stable per-view API shape
- apply user/group runtime filtering to view blocks

Boundary judgment:

- much clearer than before
- naming now reflects the real role:
  - `ContractGovernanceFilterService` = view-runtime filter
  - not final delivery governance

Target boundary:

- keep all view-runtime filtering here only

### 6. Page assembly

Files:

- [page_assembler.py](/mnt/e/sc-backend-odoo/addons/smart_core/app_config_engine/services/assemblers/page_assembler.py)
- [page_policy_service.py](/mnt/e/sc-backend-odoo/addons/smart_core/app_config_engine/services/page_policy_service.py)

Current responsibility split:

- `PageAssembler`
  - aggregate model/view/search/permission/action/report/workflow blocks
  - fetch initial data
  - shape page-level contract
- `PagePolicyService`
  - access-policy synthesis
  - form field restriction to layout
  - core field extraction
  - safe read checks

Boundary judgment:

- significantly cleaner than the earlier state
- page aggregation and page policy are now separated well enough for the current architecture

Target boundary:

- keep `PageAssembler` as aggregation layer
- keep policy helper growth inside `PagePolicyService`, not back in assembler

### 7. Canonical post-dispatch normalization

File:

- [contract_service.py](/mnt/e/sc-backend-odoo/addons/smart_core/app_config_engine/services/contract_service.py)

Current responsibility:

- `finalize_contract(...)`
- `finalize_data(...)`
- `inject_render_hints(...)`
- `govern_data(...)`
- `apply_delivery_surface_governance(...)`
- `finalize_and_govern_data(...)`

Boundary judgment:

- this is now the clearest canonical owner of post-dispatch shaping
- the main sequencing is explicit:
  - finalize
  - inject render hints when needed
  - apply delivery-surface governance

Target boundary:

- continue converging entrypoints on these helpers

### 8. Delivery-surface governance

File:

- [contract_governance.py](/mnt/e/sc-backend-odoo/addons/smart_core/utils/contract_governance.py)

Current responsibility:

- user/native/internal delivery-surface shaping
- decide what finalized contract is exposed to which surface

Boundary judgment:

- semantically distinct from view-runtime filtering
- boundary is now understandable after the naming cleanup

Target boundary:

- keep this as the last business-semantic shaping step before response delivery

### 9. Auxiliary bootstrap entrypoints

Files:

- [system_init_preload_builder.py](/mnt/e/sc-backend-odoo/addons/smart_core/core/system_init_preload_builder.py)
- [ui_base_contract_asset_producer.py](/mnt/e/sc-backend-odoo/addons/smart_core/core/ui_base_contract_asset_producer.py)
- [system_init_surface_context.py](/mnt/e/sc-backend-odoo/addons/smart_core/core/system_init_surface_context.py)
- [system_init_surface_builder.py](/mnt/e/sc-backend-odoo/addons/smart_core/core/system_init_surface_builder.py)
- [runtime_fetch_bootstrap_helper.py](/mnt/e/sc-backend-odoo/addons/smart_core/core/runtime_fetch_bootstrap_helper.py)
- [runtime_fetch_context_builder.py](/mnt/e/sc-backend-odoo/addons/smart_core/core/runtime_fetch_context_builder.py)

Current responsibility:

- preload and asset paths now reuse `finalize_data(...)`
- `system_init` and `runtime_fetch` now use delivery-surface terminology more explicitly

Boundary judgment:

- auxiliary entrypoints are no longer materially drifting from the main delivery path
- remaining issues are now mostly naming compatibility residue, not semantic duplication

## Residual Risk Matrix

### Low risk and worth another cleanup batch

1. `UiContractHandler` still calls `inject_render_hints(...)` and delivery governance directly.
   - Risk: protocol layer still owns part of business shaping.
   - Candidate cleanup: introduce a single service helper that performs the whole handler-side post-dispatch sequence.

2. `AppViewConfig` is still a lifecycle-heavy model.
   - Risk: parse, fallback, persistence, projection, and runtime filter are concentrated in one class.
   - Candidate cleanup: document-only if behavior stability is more important than refactor churn; otherwise extract projection orchestration later.

3. Compatibility naming residue remains in bootstrap context.
   - Example: `apply_contract_governance_fn` still exists as a compatibility field behind the explicit alias.
   - Risk: low; mainly readability debt.

### Medium risk but not urgent

1. `ContractService.handle_request()` and `UiContractHandler.handle()` still represent two HTTP-facing orchestration entrypoints.
   - Much less duplicated than before, but still not fully unified.
   - Another aggressive convergence batch could blur stable behavior if done too quickly.

2. `AppViewConfig` API projection and parser fallback remain tightly coupled.
   - This is still the densest concentration point in the backend chain.
   - A larger extraction here is feasible, but no longer low-risk.

## Removed Or Reduced Drift Since The Previous Audit

- `UiContractHandler` no longer repeats as much local finalize wrapping.
- `ContractService` is now the explicit canonical post-dispatch owner.
- `PageAssembler` no longer carries the main page-policy helpers inline.
- view-runtime filter and delivery-surface governance are now explicitly separated in naming.
- preload, asset, `system_init`, and `runtime_fetch` are now closer to the canonical delivery path.

## Current Decision

The backend chain is materially cleaner than it was at the start of this iteration line.

Recommended next step:

1. keep architecture unchanged
2. prefer one more low-risk convergence batch only if it keeps behavior stable
3. otherwise stop implementation cleanup here and commit the chain-refresh audit as the new baseline

Problem:

- both are called governance, but their levels differ
- boundary is conceptually correct, naming is fuzzy

Cleanup direction:

- rename or document them as:
  - `view_runtime_filter`
  - `delivery_surface_governance`

### C. Assembly vs policy in `PageAssembler`

Observed:

- page assembler does aggregation plus policy decisions

Problem:

- assembly and policy are mixed
- debugging layout/field issues requires reading both aggregation and gating logic together

Cleanup direction:

- gradually extract page policy helpers without changing output structure

### D. Parse lifecycle concentrated in `AppViewConfig`

Observed:

- `AppViewConfig` fetches views, decides parse path, persists cache, and projects contract API

Problem:

- persistence owner also acts as parse coordinator and API presenter

Cleanup direction:

- keep architecture unchanged
- but separate internal helpers conceptually:
  - view fetch
  - parser orchestration
  - persistence
  - API projection

## Boundary Matrix

| Layer | Primary owner | Should own | Should not own |
| --- | --- | --- | --- |
| Intent entry | transport route | request envelope, authentication handoff | contract semantics |
| UI handler | `UiContractHandler` | request normalization, op routing, response envelope | duplicated contract shaping |
| Dispatch | `ActionDispatcher` | subject/action orchestration | normalization, governance |
| Action resolution | `ActionResolver` | action identity, safe drill-down | page assembly |
| Parse | `NativeParseService` + parser/fallback | parser-native structure extraction | runtime ACL/user shaping |
| View API projection | `AppViewConfig.get_contract_api` | stable `views.*` blocks | page-level delivery policy |
| Page assembly | `PageAssembler` | block aggregation, initial data | deep delivery governance |
| Finalize | `ContractService.finalize_contract` | structural normalization and self-check | request transport concerns |
| Delivery governance | `apply_contract_governance` | user-surface shaping | parser/view-runtime filtering |

## Low-Risk Cleanup Order

1. Document the canonical chain explicitly in code comments and reports.
2. Collapse post-dispatch shaping into a single reusable pipeline callable by both handler and service entrypoints.
3. Rename or clearly separate view-level governance and delivery-level governance.
4. Extract page-level policy helpers from `PageAssembler` without changing outputs.
5. Split `UiContractHandler` into thinner helper methods so protocol, routing, and shaping are no longer interleaved.

## Do Not Change In This Cleanup Round

- overall architecture shape
- parser output schema
- finalized contract public schema
- user-facing endpoint names
- action model semantics

The target is boundary clarity and reduced duplication, not architecture replacement.

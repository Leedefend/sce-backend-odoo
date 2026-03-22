# system.init Startup Contract Layers v1

## Layer Target
- `Platform Layer + Frontend Startup Contract Layer`

## Module
- `system.init` startup protocol

## Reason
- Freeze the responsibility boundary between `boot`, `preload`, and `runtime` after Phase 12-D slimming.
- Prevent heavy fields and runtime payloads from flowing back into the default startup surface.
- Establish a stable contract baseline before Phase 12-E continues into formal preload and on-demand runtime fetch work.

## Core Rule
- `system.init` is a startup protocol, not a runtime aggregate endpoint.
- Startup data must be layered:
  - `boot`: minimum startup facts and references only
  - `preload`: minimum first-screen render surface only
  - `runtime`: all heavier scene/page/collection payloads must move to dedicated fetch intents

## Layer Definitions

### 1. Boot Layer
Intent shape:
- `intent=system.init`
- `params.with_preload=false`

Purpose:
- establish authenticated startup baseline
- deliver nav/default-route/role startup facts
- expose references for later preload/runtime fetch

Allowed top-level keys:
- `user`
- `nav`
- `nav_meta`
- `default_route`
- `intents`
- `feature_flags`
- `role_surface`
- `version`
- `init_meta`

Required metadata refs under `init_meta`:
- `contract_mode`
- `preload_requested=false`
- `scene_subset`
- `scene_subset_count`
- `workspace_home_preload_hint`
- `page_contract_meta.intent`

Boot must not include:
- `workspace_home`
- `scene_ready_contract_v1`
- `page_contracts`
- `workspace_collections`
- `runtime_collections`
- `scene_catalog`
- `scene_details`
- full scene/runtime aggregates such as `scenes`, `capabilities`, `capability_groups`, `ext_facts`
- heavy startup diagnostics such as nav-policy validation counts, delivery scene counts, asset bind counts

Responsibility boundary:
- boot can say where to fetch next
- boot must not inline what later layers should fetch

### 2. Preload Layer
Intent shape:
- `intent=system.init`
- `params.with_preload=true`

Purpose:
- provide the minimum contract surface required to render the landing screen
- remain startup-safe and smaller than runtime fetch surfaces

Allowed additions on top of Boot:
- `workspace_home`
- `scene_ready_contract_v1`

Required preload semantics:
- `init_meta.preload_requested=true`
- `workspace_home` must be non-empty
- `scene_ready_contract_v1` must be non-empty

Preload must not include:
- `page_contracts`
- `workspace_collections`
- `runtime_collections`
- `scene_catalog`
- `scene_details`
- full runtime aggregates such as `scenes`, `capabilities`, `capability_groups`, `ext_facts`

Responsibility boundary:
- preload is allowed to make the first screen renderable
- preload is not allowed to replace dedicated runtime fetch APIs

### 3. Runtime Layer
Intent shape:
- dedicated fetch endpoints after startup

Expected runtime entry family:
- `page.contract` / `scene.page_contract`
- `scene.detail`
- `scene.catalog`
- `workspace.collections`

Purpose:
- fetch heavy, page-specific, scene-specific, or collection-specific payloads on demand
- keep startup protocol stable and narrow

Runtime endpoint semantics:
- `page.contract`
  - returns a single page contract only (`data.page_contract`)
  - must not return `page_contracts.pages` aggregate wrapper
- `scene.catalog`
  - returns runtime-discoverable scene directory for on-demand navigation/catalog reads
- `scene.detail`
  - returns one resolved scene payload by `scene_key`
- `workspace.collections`
  - returns business collections only (`task_items/payment_requests/risk_actions/project_actions`)
  - must not return preload/page payloads such as `workspace_home` or `page_contracts`
- `system.init.inspect`
  - reserved for startup inspect/debug payloads
  - owns heavy nav/runtime diagnostic facts removed from default `system.init`

Runtime must not flow back into boot/preload by default.

## Consumption Order
1. `login`
2. `system.init` with `with_preload=false` for boot facts
3. optional `system.init` with `with_preload=true` for first-screen preload surface
4. dedicated runtime fetch intents for deeper page/scene/collection payloads

## Non-Goals For This Batch
- no preload semantic expansion beyond the current minimum render surface
- no runtime endpoint redesign beyond boundary freeze
- no dashboard/business-scene recovery in this document

## Guard Policy
This layer contract is enforced by:
- `make verify.system_init.startup_layer_contract`
- `make verify.system_init.minimal_surface`
- `make verify.smart_core.minimum_surface`
- `make verify.runtime.fetch_entrypoints`

The guard must fail when:
- boot returns preload/runtime payloads
- preload returns runtime-only payloads
- undocumented keys re-enter either boot or preload surface
- `init_meta` re-expands beyond the minimal startup contract

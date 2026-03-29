# AppViewConfig Lifecycle Boundary Audit

## Scope

This note focuses on [app_view_config.py](/mnt/e/sc-backend-odoo/addons/smart_core/app_config_engine/models/app_view_config.py) after backend cleanup batches `248-255`.

It answers three questions:

1. which responsibilities are still concentrated in `AppViewConfig`
2. which seams are now safe to extract
3. where cleanup should stop to avoid unnecessary risk

## Current Lifecycle Map

### 1. View acquisition

Main entry:

- `_safe_get_view_data(...)`

Current responsibility:

- follow action-bound view id when present
- call `get_view(...)`
- fall back to `fields_view_get(...)`
- normalize returned shape into `{arch, fields, toolbar, ...}`

Boundary judgment:

- operationally coherent
- still coupled to action-context interpretation and version compatibility

### 2. Parse orchestration

Main entry:

- `_generate_from_fields_view_get(...)`

Current responsibility:

- obtain merged Odoo view
- instantiate `NativeParseService`
- instantiate `ParseFallbackService`
- decide parser/fallback path
- merge tree default order / visible columns fallback
- clean unserializable objects
- compute stable hash
- write cache row and version

Boundary judgment:

- this is the densest lifecycle concentration point in the file
- it mixes orchestration, persistence, compatibility fallback, and post-parse cleanup

### 3. Fallback parse implementation

Main entry:

- `_fallback_parse(...)`

Current responsibility:

- implement concrete fallback parse logic for:
  - tree
  - kanban
  - form
- include helper extraction logic for header buttons, stat buttons, layout, modifiers, chatter, attachments, x2many subviews

Boundary judgment:

- this is still the largest behavior block inside the model
- the new `ParseFallbackService` only decides parser vs fallback; actual fallback semantics remain inside `AppViewConfig`

### 4. Final contract aggregation

Main entry:

- `build_final_contract(...)`

Current responsibility:

- clone persisted `arch_parsed`
- sanitize governed contract
- merge fragments
- merge variants
- apply runtime filter

Boundary judgment:

- this stage is conceptually coherent
- it is a good example of lifecycle orchestration that still belongs close to the persisted view config

### 5. API projection

Main entry:

- `get_contract_api(...)`

Current responsibility:

- call `build_final_contract(...)`
- project final per-view block shape by `view_type`
- provide default values per view type

Boundary judgment:

- acceptable as the stable view API projection edge
- not the main risk point, though it does add to total class size

### 6. Runtime filter adapter

Main entry:

- `_runtime_filter(...)`

Current responsibility:

- thin compatibility adapter into [contract_governance_filter.py](/mnt/e/sc-backend-odoo/addons/smart_core/app_config_engine/services/contract_governance_filter.py)

Boundary judgment:

- already thin enough
- not worth further cleanup in isolation

## Safe Extraction Seams

### Safe seam A: parse persistence writeback shell

Candidate:

- the writeback/hash/version branch inside `_generate_from_fields_view_get(...)`

Why safe:

- mostly persistence and bookkeeping
- input and output are already explicit:
  - parsed payload
  - stable hash
  - existing config row

Why not urgent:

- low readability gain compared with the risk of touching a mature cache path

### Safe seam B: post-parse cleanup helpers

Candidate:

- unserializable-object cleanup
- tree default-order merge
- tree visible-columns backfill

Why safe:

- these are deterministic normalization helpers
- they are structurally separate from ORM fetch and persistence

Why not urgent:

- moderate readability gain only

### Safe seam C: fallback parse helper families

Candidate:

- form fallback helper family inside `_fallback_parse(...)`
  - header buttons
  - button box
  - layout extraction
  - field modifiers
  - chatter and attachments
  - x2many subviews

Why safe:

- helper boundaries are already visible inside the method
- extraction could reduce method size without changing behavior

Why not immediate:

- still easy to introduce subtle parse drift if moved too aggressively

## Medium-Risk Areas

### 1. `_safe_get_view_data(...)`

Reason:

- action-specific view selection and version compatibility are intertwined
- a refactor here can easily change which bound view is chosen

Recommendation:

- document rather than refactor unless a concrete bug appears

### 2. `_generate_from_fields_view_get(...)`

Reason:

- it is the central lifecycle method for fetch, parse, normalize, hash, and persist
- even a “clean” split here can accidentally change version bumping or fallback conditions

Recommendation:

- only refactor in a dedicated batch with regression snapshots

### 3. `build_final_contract(...)`

Reason:

- this is stable and semantically important
- fragment + variant + runtime filter ordering should not be disturbed casually

Recommendation:

- keep as-is unless ordering bugs are discovered

## Stop-Or-Continue Recommendation

### Recommended stop line for low-risk cleanup

The low-risk backend cleanup line should stop before touching:

- `_safe_get_view_data(...)`
- parse/fallback decision ordering in `_generate_from_fields_view_get(...)`
- fragment/variant/runtime-filter ordering in `build_final_contract(...)`

### If one more implementation batch is still desired

The only remaining implementation batch that still looks reasonably safe is:

- extract fallback form helper families from `_fallback_parse(...)`

That batch should:

- keep behavior identical
- avoid touching fetch, persistence, hash, or runtime filter ordering

### Final judgment

`AppViewConfig` is still lifecycle-heavy, but the remaining cleanup is no longer obviously low-risk.

The current codebase is now in a state where:

- handler/service/assembler/bootstrap boundaries are substantially clearer
- `AppViewConfig` remains the main concentration point
- further cleanup should be driven by a concrete maintenance pain or bug, not by abstraction pressure alone

# Contract Governance Responsibility Map

Date: 2026-07-13
Owner: Platform owner
Target file: `addons/smart_core/utils/contract_governance.py`
Current size: 3,528 lines
Phase: staged responsibility split

## Purpose

`contract_governance.py` is the post-parser governance projection layer for
UI/native contracts. It must remain projection-only: it may normalize, annotate,
filter, and map contract payloads, but it must not become an authority for
business facts, permissions, workflow state, or ORM persistence.

Do not start mechanical extraction until these boundaries are covered by tests
and by a smaller public module layout.

## Public Entry Points

| Entry point | Responsibility | Boundary |
| --- | --- | --- |
| `apply_contract_governance(data, contract_mode, ...)` | Main pipeline: canonicalize, sanitize, semantic transforms, domain overrides, mode metadata, and surface mapping. | Must stay deterministic and side-effect-free except in-place contract shaping. |
| `resolve_contract_mode(params)` | Resolve `user` or `hud` mode from request params. | No request execution or persistence. |
| `resolve_contract_surface(params, contract_mode)` | Resolve `user`, `native`, or `hud` surface. | Native surface must skip user/hud policy transforms. |
| `normalize_capabilities(capabilities)` | Normalize capability rows for user surfaces. | No registry mutation during normalization. |
| `normalize_scenes(scenes)` | Normalize scene rows and semantic profile metadata. | No routing or menu lookup. |
| `register_legacy_standard_list_profile(...)` and `register_legacy_*` functions | Register legacy projection profiles and model policy hints. | Registry mutation only; no immediate contract transformation. |
| `register_contract_domain_override(...)` | Register controlled domain overrides for governed contracts. | Overrides are projection hints, not access enforcement. |

## Responsibility Bands

| Lines | Band | Current responsibility | Extraction candidate |
| --- | --- | --- | --- |
| imported | Constants and registries | Source authority metadata, user-surface allowlists, project/enterprise field profiles, render profiles, form policy constants, and contract key canonical map. | `contract_governance_registry.py`. |
| 1-446 | Source authority and registry API | Source authority descriptors, legacy profile registration, profile matching. | Keep facade wrappers until import-time compatibility is fully covered. |
| imported + 595-670 | User surface normalization | Capability and scene normalization are delegated; scene sanitization, search/action noise reduction, and user-surface policies remain in facade/user-surface helpers. | `contract_governance_capabilities.py`, `contract_governance_scenes.py`, and `contract_governance_user_surface.py`. |
| 1267-2178 | Project and enterprise governance | Scene list metadata, project form/list/kanban/task transforms, enterprise company/department/user forms. | `contract_governance_project_profiles.py` and `contract_governance_enterprise_profiles.py`. |
| 1591-1965 + imported | Standard list governance | Standard list profile application, delegated toolbar labels, tier-review list shaping. | `contract_governance_list_surface.py` plus future standard-list policy module. |
| imported | Native surface and scene bridge | Visible-field access realignment, native surface normalization, scene semantic surface normalization, scene contract v1 envelope, search/action bridge, business labels, native labels, and relation semantics are delegated. | `contract_governance_access_policy.py`, `contract_governance_native_bridge.py`, and `contract_governance_labels.py`. |
| 3047-4499 | Form policy and render semantics | Render profile, view capabilities, field groups, layout backfill, action policies, validation rules, create-profile noise hiding, canonical key mapping. | `contract_governance_form_policy.py`. |
| 4502-4742 | Domain override and diagnostics | Domain override registry/application, diagnostics, snapshots, surface mapping. | `contract_governance_diagnostics.py`. |
| 4745-4820 | Main pipeline | Orchestrates all projection transforms and attaches metadata. | Keep as thin facade in `contract_governance.py`. |

## Current Guards

| Guard | Coverage |
| --- | --- |
| `contract_governance_determinism_guard.py` | Repeated `apply_contract_governance` calls produce stable output for user and hud modes. |
| `contract_governance_coverage.py` | Runtime callers and governance metadata are wired through system init, ui contract, and contract service. |
| `contract_governance_brief.py` | Governance coverage feeds backend architecture reporting. |
| `test_contract_governance_project_form.py` | Project form/list/task/kanban and form governance behavior. |
| `test_contract_governance_record_context_registry.py` | Registry defaults, mutation APIs, capability and scene normalization. |
| `test_contract_governance_kanban_profile_registry.py` | Kanban profile registry behavior. |
| `test_contract_governance_task_form_profile_registry.py` | Task form profile registry behavior. |
| `test_odoo_native_alignment_boundaries.py` | Source authority and native alignment boundaries. |
| `list_batch_action_closure_guard.py` | Batch action policy behavior through governed list contracts. |
| `contract_governance_registry_split_guard.py` | Constants/registry extraction compatibility and line-budget lock. |
| `contract_governance_user_surface_split_guard.py` | User-surface sanitizer/action grouping extraction compatibility and purity lock. |
| `contract_governance_capabilities_split_guard.py` | Capability normalization extraction compatibility, shared registry behavior, and purity lock. |
| `contract_governance_scenes_split_guard.py` | Scene normalization extraction compatibility, shared semantic-profile registry behavior, and purity lock. |
| `contract_governance_list_surface_split_guard.py` | Standard list toolbar label extraction compatibility and row-open action behavior lock. |
| `contract_governance_native_bridge_split_guard.py` | Native/scene bridge extraction compatibility, envelope derivation, search surface, and action bridge behavior lock. |
| `contract_governance_labels_split_guard.py` | Business label normalization, shared field presentation registry, native layout labels, and relation-entry semantics lock. |
| `contract_governance_access_policy_split_guard.py` | Access policy visible-field realignment and warning marker behavior lock. |
| `contract_governance_canonicalization_split_guard.py` | Contract key canonicalization extraction compatibility, alias conflict behavior, and purity lock. |
| `contract_governance_surface_mapping_split_guard.py` | Surface snapshot collection and native-to-governed diff behavior lock. |
| `contract_governance_create_profile_split_guard.py` | Create-profile button, technical field, and state-ribbon cleanup behavior lock. |

## Extraction Order

1. Freeze public imports and add module-level compatibility tests.
2. Extract constants and registry storage/API first.
3. Extract pure user-surface normalization helpers.
4. Extract standard list governance.
5. Extract native bridge and scene contract envelope helpers.
6. Extract form policy/render semantics.
7. Extract project and enterprise profile packs last, because they carry the most legacy product semantics.
8. Leave `apply_contract_governance` as the only orchestration facade until all consumers are migrated.

## Do Not Move Yet

- `apply_contract_governance` orchestration order.
- Domain override registry side effects.
- Legacy profile registration APIs used by addons during import.
- Source authority contract functions.
- Any behavior that changes user/native/hud output shape without a before/after fixture.

## Invariants

- No ORM calls, HTTP calls, routing, file IO, or environment access inside governance transforms.
- Governance may hide, label, group, annotate, and map existing contract data; it must not invent backend permission truth.
- Native surface must keep parser-origin structure and skip user/hud policy transforms.
- User mode must strip diagnostic/internal fields not intended for users.
- HUD mode may emit diagnostics, but diagnostics must remain deterministic.
- Surface mapping must compare native and governed snapshots without mutating the native snapshot.

## Next Implementation Candidate

The first code PR should extract constants and registry storage into a small
module while keeping all public imports from `contract_governance.py` working.
Registry mutation APIs can remain in the facade until their helper dependencies
are extracted safely. The PR must include:

- module compatibility test for existing public imports;
- registry behavior tests;
- determinism guard;
- coverage guard;
- full `make ci`.

## Stage 1 Target

Stage 1 is complete when:

- `contract_governance_registry.py` owns source authority constants, mutable
  legacy registries, mode/surface constants, field profile constants, and render
  profile constants;
- `contract_governance.py` still exports all previous public and private
  registry symbols for compatibility;
- direct `spec_from_file_location` loading of `contract_governance.py` still
  works for existing tests;
- registry mutation through `contract_governance.py` updates the loaded registry
  storage object;
- `contract_governance.py` is locked at `<=4655` lines for this stage.

## Stage 2 Target

Stage 2 is complete when:

- `contract_governance_user_surface.py` owns recursive user-mode field stripping,
  allowed-key picking, user capability/scene sanitizers, noisy filter/action
  detection, action grouping, action-row trimming, and user-surface noise
  reduction;
- `contract_governance.py` keeps the old private helper names as compatibility
  wrappers;
- the extracted module remains pure: no ORM calls, HTTP calls, routing, file IO,
  or environment access;
- `normalize_capabilities`, `normalize_scenes`, and `_apply_user_surface_policies`
  remain in the facade until their registry and model-policy dependencies are
  isolated separately;
- `contract_governance.py` is locked at `<=4535` lines for this stage.

## Stage 3 Target

Stage 3 is complete when:

- `contract_governance_registry.py` also owns form policy constants, primary and
  readonly action keyword sets, disabled-reason copy, form scene profile names,
  capability group defaults, and the contract key canonical map;
- `contract_governance.py` continues to export those names via `_REGISTRY_EXPORTS`
  for direct import compatibility;
- the registry module remains static data plus mutable legacy registries: no ORM
  calls, HTTP calls, routing, file IO, or environment access;
- `contract_governance.py` is locked at `<=4490` lines for this stage.

## Stage 4 Target

Stage 4 is complete when:

- `contract_governance_capabilities.py` owns capability normalization, capability
  state derivation, default payload derivation, delivery-level derivation, and
  demo/internal capability filtering helpers;
- `contract_governance.py` keeps `normalize_capabilities`,
  `is_internal_or_smoke`, and `_has_demo_semantics` available through loaded
  module aliases for existing callers and the main pipeline;
- direct `spec_from_file_location` loading shares the capability group registry
  object with `contract_governance.py`, so `register_capability_group_profile`
  affects later normalization;
- the extracted module remains projection-only: no ORM calls, HTTP calls,
  routing, file IO, or environment access;
- `contract_governance.py` is locked at `<=4272` lines for this stage.

## Stage 5 Target

Stage 5 is complete when:

- `contract_governance_scenes.py` owns scene normalization, scene list-profile
  normalization, scene meta derivation, role relevance scoring, and normalized
  scene tags;
- `contract_governance.py` keeps `normalize_scenes`,
  `_normalize_scene_list_profile`, and `_derive_scene_meta` available through
  loaded module aliases for existing callers and the main pipeline;
- direct `spec_from_file_location` loading shares the scene semantic profile
  registry object with `contract_governance.py`, so
  `register_scene_semantic_profile` affects later normalization;
- the extracted module remains projection-only: no ORM calls, HTTP calls,
  routing, file IO, or environment access;
- `contract_governance.py` is locked at `<=4213` lines for this stage.

## Stage 6 Target

Stage 6 is complete when:

- `contract_governance_list_surface.py` owns standard list toolbar labels,
  search labels, and row-open action normalization;
- `_govern_standard_list_for_user` keeps field selection, schema enrichment,
  permissions, batch policy, list profile, and semantic-page assembly in the
  facade until standard-list behavior has narrower fixture coverage;
- the extracted module remains projection-only: no ORM calls, HTTP calls,
  routing, file IO, or environment access;
- `contract_governance.py` is locked at `<=4121` lines for this stage.

## Stage 7 Target

Stage 7 is complete when:

- `contract_governance_native_bridge.py` owns native and scene bridge normalization,
  native-view contract surface normalization, scene semantic surface
  normalization, search-surface derivation, scene action derivation, and scene
  contract v1 envelope construction;
- `contract_governance.py` keeps the previous private helper names as wrappers
  so the main pipeline order and direct helper references remain stable;
- visible-field access realignment, business labels, and relation-entry
  semantics remain in the facade until their behavior has narrower fixture
  coverage;
- the extracted module remains projection-only: no ORM calls, HTTP calls,
  routing, file IO, or environment access;
- `contract_governance.py` is locked at `<=3932` lines for this stage.

## Stage 8 Target

Stage 8 is complete when:

- `contract_governance_labels.py` owns business labels and relation semantics,
  including legacy field presentation labels, business label overrides, native
  page label preservation, and relation-entry semantic export;
- `contract_governance.py` keeps the previous private helper names as wrappers
  so the main pipeline order and direct helper references remain stable;
- direct `spec_from_file_location` loading shares the legacy field presentation
  registry object with `contract_governance.py`, so
  `register_legacy_field_presentation` affects later label normalization;
- the extracted module remains projection-only: no ORM calls, HTTP calls,
  routing, file IO, or environment access;
- `contract_governance.py` is locked at `<=3830` lines for this stage.

## Stage 9 Target

Stage 9 is complete when:

- `contract_governance_access_policy.py` owns access policy realignment against
  visible fields, blocked/degraded field filtering, mode/reason/message
  derivation, and warning marker refresh;
- `contract_governance.py` keeps `_realign_access_policy_with_visible_fields`
  as a wrapper so the main pipeline order remains stable;
- the extracted module remains projection-only: no ORM calls, HTTP calls,
  routing, file IO, or environment access;
- `contract_governance.py` is locked at `<=3780` lines for this stage.

## Stage 10 Target

Stage 10 is complete when:

- `contract_governance_canonicalization.py` owns recursive contract key
  canonicalization, alias replacement precedence, and conflict recording;
- `contract_governance.py` keeps `_canonicalize_contract_keys` as a wrapper so
  the main pipeline order and direct helper references remain stable;
- the extracted module remains projection-only: no ORM calls, HTTP calls,
  routing, file IO, or environment access;
- `contract_governance.py` is locked at `<=3769` lines for this stage.

## Stage 11 Target

Stage 11 is complete when:

- `contract_governance_surface_mapping.py` owns surface snapshot collection,
  layout/action signature extraction, and native-to-governed diff mapping;
- `contract_governance.py` keeps the previous private helper names as wrappers
  so the main pipeline order and direct helper references remain stable;
- the extracted module remains projection-only: no ORM calls, HTTP calls,
  routing, file IO, or environment access;
- `contract_governance.py` is locked at `<=3690` lines for this stage.

## Stage 12 Target

Stage 12 is complete when:

- `contract_governance_create_profile.py` owns create-profile projection cleanup:
  record-dependent native button hiding, technical/noise field hiding, state
  ribbon hiding, and create-profile detection;
- `contract_governance.py` keeps the previous private helper names as wrappers
  so the main pipeline order and direct helper references remain stable;
- the extracted module remains projection-only: no ORM calls, HTTP calls,
  routing, file IO, or environment access;
- `contract_governance.py` is locked at `<=3528` lines for this stage.

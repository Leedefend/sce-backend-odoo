# Contract Governance Responsibility Map

Date: 2026-07-13
Owner: Platform owner
Target file: `addons/smart_core/utils/contract_governance.py`
Current size: 4,820 lines
Phase: read-only responsibility audit

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
| 1-252 | Constants and registries | Source authority metadata, user-surface allowlists, project/enterprise field profiles, render profiles. | `contract_governance_constants.py` and typed registry definitions. |
| 253-591 | Source authority and registry API | Source authority descriptors, legacy profile registration, profile matching. | `contract_governance_registry.py`. |
| 615-1264 | User surface normalization | Capability normalization, scene sanitization, search/action noise reduction, user-surface policies. | `contract_governance_user_surface.py`. |
| 1267-2178 | Project and enterprise governance | Scene list metadata, project form/list/kanban/task transforms, enterprise company/department/user forms. | `contract_governance_project_profiles.py` and `contract_governance_enterprise_profiles.py`. |
| 2181-2596 | Standard list governance | Standard list profile application, toolbar labels, tier-review list shaping. | `contract_governance_list_surface.py`. |
| 2599-3044 | Native surface and scene bridge | Visible-field access realignment, native surface normalization, scene contract v1 bridge, labels, relation semantics. | `contract_governance_native_bridge.py`. |
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

The first code PR should extract constants and registry APIs into a small module
while keeping all public imports from `contract_governance.py` working. The PR
must include:

- module compatibility test for existing public imports;
- registry behavior tests;
- determinism guard;
- coverage guard;
- full `make ci`.

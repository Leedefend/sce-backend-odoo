# Construction Core Extension Responsibility Map

Date: 2026-07-14
Owner: Construction backend owner
Target file: `addons/smart_construction_core/core_extension.py`
Current size: 4,241 lines
Phase: staged responsibility split

## Purpose

`core_extension.py` is the construction-industry extension contribution surface.
It publishes owner-specific facts, policies, maps, runtime builders, and
compatibility hooks into smart_core. It must not become a platform authority for
generic app shell behavior, generic permissions, or persistence rules outside
construction-owned policy.

## Public Entry Points

| Entry point | Responsibility | Boundary |
| --- | --- | --- |
| `smart_core_finalize_unified_page_contract_v2` | Final projected-contract adjustments for construction-owned forms. | May shape contracts, must not query or persist. |
| `smart_core_normalize_projected_contract_data` | Normalize projected contract data before frontend consumption. | Projection-only. |
| `smart_core_normalize_unified_page_contract_v2` | Normalize unified page contract v2 payloads. | Projection-only. |
| `get_*_contributions` functions | Publish construction-owned policy, capability, route, and model facts. | Must return facts; no hidden side effects. |
| `smart_core_*` hook functions | Backward-compatible hook facade consumed by smart_core. | Keep compatibility wrappers thin. |

## Responsibility Bands

| Band | Current responsibility | Extraction candidate |
| --- | --- | --- |
| Import-time registration facts | Construction scope models, reason metadata, governance profiles, action maps. | Dedicated facts modules once import side effects are audited. |
| Project layout projection | Project form node relabeling, user_id pruning, responsibility/collaboration group injection. | `core_extension_project_layout.py`. |
| Contract normalizers | General tax form, enterprise/company form, diary form, workflow contract projection. | Small projection modules by form family. |
| Policy and maps | Role surfaces, nav maps, server actions, file/API allowlists, unlink policies. | Policy map modules with pure accessors. |
| Capability and system-init rows | Home blocks, role entries, task/payment/risk/project action rows. | Fact builder modules by screen family. |
| Compatibility hooks | smart_core hook wrappers. | Keep in `core_extension.py` as facade. |

## Current Guards

| Guard | Coverage |
| --- | --- |
| `construction_core_extension_project_layout_split_guard.py` | Project layout helper extraction, user_id pruning, relabeling, responsibility/collaboration group injection, and projection-only boundary. |
| `backend_boundary_guard.py` | Core backend ownership and extension-boundary constraints. |
| `owner_industry_isolation_probe.py` | Industry module isolation and required extension hooks. |

## Stage 1 Target

Stage 1 is complete when:

- `core_extension_project_layout.py` owns pure project form layout helpers:
  field-code resolution, project label rewriting, `user_id` pruning, generated
  responsibility/collaboration fields, and widget status injection;
- `core_extension.py` keeps `_sc_*` compatibility wrappers and hook
  orchestration, and delegates helper behavior into the extracted module;
- the extracted module remains projection-only: no ORM calls, HTTP calls,
  routing, file IO, environment access, or permission inference;
- `core_extension.py` is locked at `<=4241` lines for this stage.

## Next Candidate

Next candidates should be read-only first:

- contract normalizer helpers around construction diary/general contract form;
- policy map constants and pure accessors;
- capability row builders after their data/API dependencies are mapped.

Do not move import-time registration side effects until their module load order
and external hook consumers are explicitly locked by tests.

# Construction Core Extension Responsibility Map

Date: 2026-07-14
Owner: Construction backend owner
Target file: `addons/smart_construction_core/core_extension.py`
Current size: 1,809 lines
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
| `construction_core_extension_contract_helpers_split_guard.py` | Generic contract helper extraction, v2 layout/status mirrors, governance patch mirrors, content replacement, form layout governance, line lock, and projection-only boundary. |
| `construction_core_extension_policy_maps_split_guard.py` | Static policy/map extraction, role/nav/file/API/unlink maps, line lock, no import-time registration side effects, and pure-constant boundary. |
| `construction_core_extension_system_init_rows_split_guard.py` | System-init row/profile extraction, read-side search helpers, workspace action rows, enterprise enablement facts, role/home dictionary rows, workspace/page profile overrides, line lock, and no write/registration side effects. |
| `construction_core_extension_capability_rows_split_guard.py` | Capability row normalization extraction, identity/ownership/UI/binding/permission/runtime envelope preservation, line lock, and pure-normalization boundary. |
| `construction_core_extension_hook_facts_split_guard.py` | Static hook fact extraction, business config refs, low-code/menu delivery refs, product/app shell/scene facts, acceptance nav contract, line lock, and static-facts boundary. |
| `construction_core_extension_policy_accessors_split_guard.py` | Policy accessor extraction, file model contribution scan, API mutation/create/unlink/search-field policies, contract tax quick-create detection, line lock, and read-side policy boundary. |
| `construction_core_extension_contract_normalizers_split_guard.py` | Contract normalizer extraction, construction diary/general contract tax/company form projection, general contract form policy/alias helpers, helper delegation, workflow-injection boundary, line lock, and projection-only boundary. |
| `construction_core_extension_intent_handlers_split_guard.py` | Intent handler contribution extraction, lazy handler import mapping, approval-policy intent preservation, facade registry boundary, line lock, and no env/registry side effects. |
| `construction_core_extension_service_builders_split_guard.py` | Service builder extraction, lazy service class/factory imports, facade hook preservation, line lock, and no ORM/registry side effects. |
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

## Stage 2 Target

Stage 2 is complete when:

- `core_extension_contract_helpers.py` owns generic contract helper utilities:
  field-node collection, v2 container/status mirrors, governance patch mirrors,
  content replacement, and form layout governance resolution/application;
- `core_extension.py` keeps `_sc_*` compatibility wrappers and form normalizer
  orchestration, and delegates helper behavior into the extracted module;
- the helper remains projection-only: no ORM calls, HTTP calls, routing, file
  IO, environment access, or permission inference;
- `core_extension.py` is locked at `<=4180` lines for this stage.

## Stage 3 Target

Stage 3 is complete when:

- `core_extension_policy_maps.py` owns static construction policy/map facts:
  role surfaces, role groups, nav scene maps, file model allowlists, legacy
  visible column labels, API write/mutation policies, unlink policies, critical
  scene overrides, and create-field fallbacks;
- `core_extension.py` keeps public hook functions, import-time registration
  calls, and behavior that touches `env`, ACL, routing, services, or logging;
- the extracted module remains pure constants and local policy construction:
  no ORM calls, HTTP calls, routing, registration side effects, file IO,
  environment access, or permission inference;
- `core_extension.py` is locked at `<=3763` lines for this stage.

## Stage 4 Target

Stage 4 is complete when:

- `core_extension_system_init_rows.py` owns read-side system-init row builders:
  localized text normalization, safe `search_read`, model field probing,
  enterprise enablement mainline facts, task/payment/risk/project workspace
  rows, role entry dictionary rows, and home block dictionary rows;
- `core_extension.py` keeps public system-init hooks, ext-facts assembly,
  role/home block builders, and compatibility wrapper names used by remaining
  code;
- the extracted module remains read-side row assembly only: no ORM writes,
  creates, unlinks, commits, registration side effects, HTTP calls, file IO, or
  routing decisions;
- `core_extension.py` is locked at `<=3351` lines for this stage.

## Stage 5 Target

Stage 5 is complete when:

- `core_extension_capability_rows.py` owns capability row normalization:
  identity, ownership, UI, binding, permission, release, lifecycle, runtime, and
  audit envelopes;
- `core_extension.py` keeps capability registry imports, error handling,
  timing payload handling, and compatibility hook names;
- the extracted module remains pure normalization: no ORM access, registry
  imports, HTTP calls, file IO, registration side effects, or permission
  inference beyond copying required roles/groups into the envelope;
- `core_extension.py` is locked at `<=3145` lines for this stage.

## Stage 6 Target

Stage 6 is complete when:

- `core_extension_hook_facts.py` owns static hook facts: business config group
  XMLIDs, form/approval refs, native/low-code menu refs, product catalog facts,
  business nav order, app shell taxonomy, scene orchestrator specs, and user
  data acceptance nav contract;
- `core_extension.py` keeps the public `smart_core_*` hook names and delegates
  static fact bodies into the extracted module;
- the extracted module remains static facts only: no ORM access, HTTP calls,
  registry imports, registration side effects, file IO, user/group inspection,
  or routing decisions beyond returning configured identifiers;
- `core_extension.py` is locked at `<=2884` lines for this stage.

## Stage 7 Target

Stage 7 is complete when:

- `core_extension_policy_accessors.py` owns read-side policy accessors:
  server action maps, file upload/download model contribution scans, API write
  allowlists, mutation policies, contract tax quick-create detection, create
  execution policies, unlink policy maps, and model code mappings;
- `core_extension.py` keeps public contribution hook names and delegates policy
  access into the extracted module;
- the extracted module remains read-side policy access only: no ORM writes,
  creates, unlinks, commits, registration side effects, HTTP calls, file IO, or
  handler execution;
- `core_extension.py` is locked at `<=2780` lines for this stage.

## Stage 8 Target

Stage 8 is complete when:

- `core_extension_contract_normalizers.py` owns projection-only contract
  normalizers for construction diary form, general contract tax field
  migration, and general contract company form layout;
- `core_extension.py` keeps public normalizer wrappers and the workflow
  injection helper because workflow projection reads `env`, registry, records,
  and workflow services;
- the extracted module remains pure contract projection: no ORM access, HTTP
  calls, routing, registration side effects, file IO, permission inference, or
  workflow service access;
- `core_extension.py` is locked at `<=2440` lines for this stage.

## Stage 9 Target

Stage 9 is complete when:

- `core_extension_intent_handlers.py` owns lazy construction intent handler
  imports and the intent-to-handler contribution mapping;
- `core_extension.py` keeps the public `get_intent_handler_contributions`
  facade and `smart_core_register(registry)` because registry writes are the
  extension-loader transaction boundary;
- the extracted module remains contribution assembly only: no `env` access, ORM
  calls, registry mutation, HTTP calls, file IO, or import-time registration
  side effects;
- `core_extension.py` is locked at `<=2243` lines for this stage.

## Stage 10 Target

Stage 10 is complete when:

- `core_extension_hook_facts.py` also owns static menu delivery token policy:
  business config tokens, user/admin path tokens, hidden technical labels, and
  label rename facts;
- `core_extension.py` keeps the public `smart_core_menu_delivery_token_policy`
  facade and delegates to hook facts;
- the extracted policy remains static facts only: no `env` access, ORM calls,
  HTTP calls, routing, file IO, or registration side effects;
- `core_extension.py` is locked at `<=2120` lines for this stage.

## Stage 11 Target

Stage 11 is complete when:

- `core_extension_service_builders.py` owns lazy service class and service
  factory imports for scene services, dashboard/capability builders, project
  insight, execute button contracts, and project/cost/payment/settlement slice
  services;
- `core_extension.py` keeps the public `smart_core_*` hook names and delegates
  service construction into the extracted module;
- the extracted module remains service construction only: no direct ORM access,
  searches, writes, registry mutation, HTTP calls, file IO, or import-time
  registration side effects;
- `core_extension.py` is locked at `<=2065` lines for this stage.

## Stage 12 Target

Stage 12 is complete when:

- `core_extension_system_init_rows.py` also owns system-init workspace and page
  profile overrides: business action scene labels, token sets, source scene
  routes, collection keys, and login/home/my-work/action/record display text;
- `core_extension.py` keeps the public `smart_core_extend_system_init` facade,
  contribution assembly, and the `ext_facts` write boundary before delegating
  profile override application;
- the extracted profile override helper remains data-shaping only: no ORM
  writes, creates, unlinks, registry mutation, HTTP calls, file IO, or
  import-time registration side effects;
- `core_extension.py` is locked at `<=1858` lines for this stage.

## Stage 13 Target

Stage 13 is complete when:

- `core_extension_policy_accessors.py` also owns API data search-field
  contribution assembly from alias labels, compatibility labels, confirmed
  formal visible fields, model label overrides, and optional model `_fields`
  filtering;
- `core_extension.py` keeps the public `smart_core_api_data_search_fields`
  facade and delegates to policy accessors;
- the extracted helper remains read-side policy access only: no ORM writes,
  creates, unlinks, registry mutation, HTTP calls, file IO, or import-time
  registration side effects;
- `core_extension.py` is locked at `<=1820` lines for this stage.

## Stage 14 Target

Stage 14 is complete when:

- `core_extension_contract_normalizers.py` also owns pure form contract policy
  and field alias helpers for general contract tax migration;
- `core_extension.py` keeps the public `smart_core_model_specific_form_contract_policy`
  and `smart_core_form_field_aliases` facades and delegates to contract
  normalizers;
- the extracted helpers remain payload-only contract policy projection: no
  `env` access, ORM calls, writes, registry mutation, HTTP calls, file IO, or
  import-time registration side effects;
- `core_extension.py` is locked at `<=1809` lines for this stage.

## Next Candidate

Next candidates should be read-only first:

- import-time registration facts after module load order and consumers are
  locked by tests;
- relation entry policy after tax quick-create side effects are mapped.
- workflow contract projection after env/service transaction boundaries are
  documented and covered by behavior tests.

Do not move import-time registration side effects until their module load order
and external hook consumers are explicitly locked by tests.

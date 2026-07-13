# Core Extension Responsibility Map

Target file: `addons/smart_construction_core/core_extension.py`

Current line budget: `<=3875`.

## Role

`core_extension.py` is the construction-industry contribution facade consumed by
`smart_core` extension hooks. It registers construction ownership metadata,
contributes capabilities, injects system-init facts, shapes projected contracts,
and exposes compatibility hook names expected by the platform.

The file should remain an orchestration facade. It should not become the source
of truth for generic platform permissions, frontend route semantics, or
cross-industry policy.

## Public Hook Surface

| Hook | Responsibility | Boundary |
| --- | --- | --- |
| `smart_core_register(registry)` | Register construction intent handlers into the platform handler registry. | Keep import-tolerant and idempotent. |
| `smart_core_extend_system_init(data, env, user)` | Add construction facts and page text/profile overrides under `ext_facts`. | Do not mutate unrelated platform keys. |
| `smart_core_finalize_unified_page_contract_v2(env, contract, context)` | Apply construction-specific v2 contract normalization. | Preserve source contract shape and platform authority. |
| `smart_core_finalize_projected_contract_data(env, data, context)` | Final projected-contract polish for construction list/form surfaces. | Keep as facade until projection helpers are isolated. |
| `smart_core_*` contribution hooks | Return model allowlists, policy fragments, service classes, menu policies, and navigation contracts. | Hook names are public compatibility surface. |

## Current Responsibility Bands

| Lines | Area | Current Responsibility | Candidate Destination |
| ---: | --- | --- | --- |
| 1-409 | Imports and eager registrations | Register project scope, reason metadata, capability groups, semantic scene profiles, and legacy governance profiles. | `core_extension_bootstrap.py` or declarative registration specs. |
| 410-1120 | Contract projection helpers | Project field labeling, responsibility groups, v2 container/status patches, diary/company/tax form normalization, workflow injection. | `core_extension_contract_projection.py`. |
| 1121-1571 | Static policy/catalog data | Large dictionaries and state policy tables consumed by later hooks. | `core_extension_policy_catalog.py`. |
| 1782-2101 | Workspace collection builders | Safe ORM reads and construction workspace row builders for task, payment, risk, and project action surfaces. | `core_extension_workspace_facts.py`. |
| 2104-2436 | Basic contribution hooks | Identity, scene maps, surface aliases, record context, file/api policy contributions, role entries, and home blocks. | `core_extension_contributions.py`. |
| 2439-2659 | Intent handler registration | Import-tolerant handler mapping and registry compatibility loader. | `core_extension_intents.py`. |
| 2461-2938 | Capability and form action contributions | Capability payload normalization, group contributions, create fallbacks, and payment form business actions. | `core_extension_capabilities.py` and `core_extension_form_actions.py`. |
| 3046-3423 | System-init facade and wrapper hooks | Build `ext_facts`, page profile overrides, and thin `smart_core_*` wrappers for server action/file/API/model hooks. | `core_extension_system_init.py` plus wrappers retained in facade. |
| 3442-3586 | Projected contract finalization | User-confirmed action ids and final projected contract shaping. | `core_extension_projected_contracts.py`. |
| 3589-4372 | Service/menu/navigation policy hooks | Scene service classes, portal builders, business config refs, relation policy, menu token policy, role resolution, app shell, scene entry specs, acceptance nav. | `core_extension_navigation_policy.py` and service hook modules. |

## Extraction Order

1. Extract static policy/catalog data that has no ORM dependency.
2. Extract pure projected-contract helper functions while retaining facade names.
3. Extract intent handler mapping behind `get_intent_handler_contributions()`.
4. Extract system-init fact builders, leaving `smart_core_extend_system_init` as a thin writer.
5. Extract capability payload normalization after adding behavior tests for the duplicate timing/non-timing paths.
6. Extract menu/navigation policy hooks only after documenting their product ownership.

## Do Not Move Yet

- `smart_core_register(registry)`;
- `smart_core_extend_system_init(data, env, user)`;
- `smart_core_finalize_projected_contract_data(env, data, context)`;
- hooks that directly perform ORM reads until their data access behavior is covered;
- menu, permission, or industry semantic changes unrelated to mechanical extraction.

## Guarded Baseline

The Stage 0 baseline is intentionally documentation and guard only:

- no extraction in this stage;
- `core_extension.py` stays at `<=4372` lines;
- public hook names remain in the facade;
- the responsibility map records the first extraction order before code moves;
- future PRs from this branch should include multiple commits and open only when
  the branch-level split target is complete.

## Stage 1a Catalog Extraction

Stage 1a is complete when:

- `core_extension_policy_catalog.py` owns role surface overrides, role/group
  mappings, navigation scene maps, server action window maps, and file
  attachment allowlists;
- `core_extension.py` imports those names directly so legacy module-level
  consumers keep working;
- the extracted catalog remains pure static data: no ORM calls, HTTP calls,
  routing, file IO, or environment access;
- `core_extension.py` is locked at `<=4251` lines for this stage.

## Stage 1b Catalog Expansion

Stage 1b is complete when:

- `core_extension_policy_catalog.py` also owns legacy visible business column
  labels, model code mapping, critical scene target overrides, create-field
  fallbacks, and user-confirmed formal list action XMLIDs;
- `core_extension.py` imports those names directly so legacy module-level
  consumers keep working;
- API data unlink policy tables remain in the facade because they still depend
  on `_state_unlink_policy`;
- `core_extension.py` is locked at `<=4162` lines for this stage.

## Stage 1c API Catalog Extraction

Stage 1c is complete when:

- `core_extension_policy_catalog.py` owns API write allowlists, static mutation
  policies, and draft-delete state constants;
- `_state_unlink_policy`, `API_DATA_DRAFT_UNLINK_POLICIES`, and
  `API_DATA_UNLINK_POLICIES` remain in the facade until the policy builder is
  extracted with focused behavior tests;
- `core_extension.py` is locked at `<=4146` lines for this stage.

## Stage 2 Capability Payload Builder

Stage 2 is complete when:

- `core_extension_capabilities.py` owns the pure capability contribution payload
  builder shared by `get_capability_contributions` and
  `get_capability_contributions_with_timings`;
- the extracted builder does not import Odoo, read ORM state, perform IO, or
  swallow registry exceptions;
- the facade hooks still own registry loading, timing payload return shape, and
  exception boundaries;
- `core_extension.py` is locked at `<=3955` lines for this stage.

## Stage 3 Form Action Builder

Stage 3 is complete when:

- `core_extension_form_actions.py` owns pure normalization from payment available
  action handler data into form business action contracts;
- `smart_core_form_business_actions` keeps model filtering, record lookup,
  handler invocation, and exception boundaries in the facade;
- the extracted builder does not import Odoo, read ORM state, perform IO, or
  trigger notifications/routing;
- `core_extension.py` is locked at `<=3875` lines for this stage.

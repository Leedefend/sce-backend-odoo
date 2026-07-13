# Core Extension Responsibility Map

Target file: `addons/smart_construction_core/core_extension.py`

Current line budget: `<=958`.

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
| 1-708 | Imports and eager registrations | Register project scope, reason metadata, capability groups, semantic scene profiles, and legacy governance profiles. | `core_extension_bootstrap.py` or declarative registration specs. |
| imported | Contract projection helpers | Project field labeling, responsibility groups, v2 container/status patches, diary/company/tax form normalization, workflow injection. | `core_extension_contract_projection.py`. |
| imported | API data policy hooks | File upload/download allowlists, API write/mutation/create/unlink policies, search-field mapping, and download auth subject lookup. | `core_extension_api_policy.py`. |
| 758-776 | Intent handler registration | Registry compatibility loader delegates to imported handler contribution mapping. | `core_extension_intents.py`. |
| 779-883 | Capability and form action contributions | Capability registry reads, group contributions, create fallbacks, and payment form business actions. | Facade until registry/handler behavior has focused coverage. |
| 886-957 | System-init facade | Build `ext_facts`, then delegate page/profile override merge to `core_extension_system_init.py`. | `core_extension_system_init.py` plus wrappers retained in facade. |
| imported | Projected contract finalization | User-confirmed action ids and final projected contract shaping. | `core_extension_projected_contracts.py`. |
| imported | Service/menu/navigation policy hooks | Business config refs, relation policy, menu token policy, role resolution, app shell, scene entry specs, acceptance nav. | `core_extension_navigation_policy.py`. |

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
- capability/form action hooks that directly perform registry or handler reads until their behavior is covered;
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

## Stage 4 Intent Handler Contributions

Stage 4 is complete when:

- `core_extension_intents.py` owns import-tolerant construction intent handler
  mapping and contribution row assembly;
- `smart_core_register` remains in the facade and continues to populate the
  provided registry from `get_intent_handler_contributions()`;
- the extracted module may import Odoo handler classes, but must not perform ORM
  reads/writes or mutate the platform registry directly;
- `core_extension.py` is locked at `<=3675` lines for this stage.

## Stage 5 System Init Profile Overrides

Stage 5 is complete when:

- `core_extension_system_init.py` owns pure workspace keyword and page profile
  override merging;
- `smart_core_extend_system_init` keeps input validation, construction fact
  collection, `ext_facts` module insertion, and final helper invocation in the
  facade;
- the extracted helper does not import Odoo, read ORM state, perform IO, or call
  service handlers;
- `core_extension.py` is locked at `<=3471` lines for this stage.

## Stage 6 Workspace Fact Builders

Stage 6 is complete when:

- `core_extension_workspace_facts.py` owns safe workspace ORM reads and row
  builders for task, payment, risk, project, role-entry, home-block, and
  enterprise enablement facts;
- `get_system_init_fact_contributions` remains in the facade and still controls
  construction fact assembly, exception boundaries, and returned payload shape;
- shared helper functions such as `_safe_search_read`, `_model_has_field`, and
  `_as_text` are private to the workspace facts module;
- `core_extension.py` is locked at `<=3020` lines for this stage.

## Stage 7 Navigation Policy Hooks

Stage 7 is complete when:

- `core_extension_navigation_policy.py` owns business config refs, native/lowcode
  config menu refs, relation entry policy, menu delivery token policy, business
  nav order, product policy catalog hooks, release/usage role resolution, app
  shell taxonomy, scene entry orchestrator specs, and user data acceptance nav
  contracts;
- `core_extension.py` imports those public hook names directly so existing
  `smart_construction_core.__init__` exports keep working;
- the extracted module may perform read-only ORM searches required by relation
  entry policy, but must not write records or mutate registries;
- `core_extension.py` is locked at `<=2371` lines for this stage.

## Stage 8 Contract Projection Hooks

Stage 8 is complete when:

- `core_extension_contract_projection.py` owns construction-specific v2 contract
  projection helpers, project responsibility layout backfill, construction diary
  form shaping, general contract tax normalization, company contract form
  normalization, and workflow contract injection;
- `core_extension.py` imports the three public hook names directly:
  `smart_core_finalize_unified_page_contract_v2`,
  `smart_core_normalize_projected_contract_data`, and
  `smart_core_normalize_unified_page_contract_v2`;
- the extracted module may call the workflow contract service for read-only
  projection enrichment, but must not write records or mutate registries;
- `core_extension.py` is locked at `<=1662` lines for this stage.

## Stage 9 Projected Contract Finalization

Stage 9 is complete when:

- `core_extension_projected_contracts.py` owns user-confirmed formal list action
  lookup, project form projected governance finalization, tree-view contract
  locking, and list-profile lock backfill;
- `core_extension.py` imports `smart_core_finalize_projected_contract_data`
  directly so existing exports keep working;
- the extracted module may read views, actions, and generated contracts, but
  must not write records or mutate registries;
- `core_extension.py` is locked at `<=1517` lines for this stage.

## Stage 10 Service Hook Builders

Stage 10 is complete when:

- `core_extension_services.py` owns scene service class hooks, portal/dashboard
  builders, capability matrix/insight hooks, execute-button contract builder,
  and project/cost/payment/settlement service factories;
- `core_extension.py` imports those public hook names directly so existing
  exports keep working;
- lazy service imports remain inside hook functions;
- `core_extension.py` is locked at `<=1422` lines for this stage.

## Stage 11 API Policy Hooks

Stage 11 is complete when:

- `core_extension_api_policy.py` owns API data policy hooks, file
  upload/download model discovery, API unlink policy builders, account-tax
  quick-create ACL/execution policy, API search-field mapping, and payment
  request attachment auth subject lookup;
- `core_extension.py` imports API policy public hook names directly so existing
  module-level exports keep working;
- the extracted module may perform read-only ORM searches required by file
  model discovery and attachment subject lookup, but must not write records or
  mutate registries;
- `core_extension.py` is locked at `<=958` lines for this stage.

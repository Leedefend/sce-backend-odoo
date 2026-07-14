# Construction Core Extension Branch Closure

Date: 2026-07-14
Branch: `feature/contract-governance-responsibility-baseline`
Owner: Construction backend owner
Status: ready for unified PR once branch CI is green

## Decision

This branch stops mechanical splitting of
`addons/smart_construction_core/core_extension.py`.

The remaining large functions are transaction or integration boundaries rather
than pure helper clusters. Further movement should require behavior tests,
interface maps, or a specific bug fix, not a line-count target.

## Scope Delivered

The branch isolates construction extension responsibilities into owned helper
modules while keeping smart_core-facing compatibility hooks in
`core_extension.py`.

Delivered responsibility splits:

- `core_extension_contract_normalizers.py` owns projection-only contract
  normalizers and form policy aliases.
- `core_extension_intent_handlers.py` owns lazy intent handler contribution
  mapping.
- `core_extension_service_builders.py` owns lazy construction service builder
  contributions.
- `core_extension_actor_roles.py` owns actor-role resolver facts and release
  role normalization.
- `core_extension_hook_facts.py` owns static hook facts including menu delivery
  and low-code recovery identifiers.
- `core_extension_policy_accessors.py` owns read-side policy accessors including
  API search field policy.
- `core_extension_system_init_rows.py` owns system-init row builders and profile
  override assembly.

The branch intentionally excludes:

- Odoo model, migration, or schema changes.
- Menu, permission, or industry semantic changes unrelated to responsibility
  extraction.
- Frontend user-experience changes.
- Moving complete transaction flows out of `core_extension.py`.

## Metrics

Current branch evidence:

| File | Current size | Decision |
| --- | ---: | --- |
| `addons/smart_construction_core/core_extension.py` | 1,787 lines | Freeze after this branch. |
| `frontend/apps/web/src/pages/ContractFormPage.vue` | 5,939 lines | Keep frozen at `<= 6000`. |

The current split queue classifies `core_extension.py` as P2 at 1,787 lines.
It no longer blocks the active P0/P1 complexity queue.

## Active Guards

The branch adds or strengthens responsibility guards for:

- project layout helpers;
- generic contract helpers;
- static policy maps;
- system-init row/profile builders;
- capability row normalization;
- hook facts;
- policy accessors;
- contract normalizers;
- intent handler contributions;
- service builder contributions;
- actor role contributions;
- the responsibility map itself.

These guards are wired into local and full CI through the existing make targets.

## Frozen Transaction Boundaries

The following functions remain in `core_extension.py` by design:

| Boundary | Reason to keep in facade |
| --- | --- |
| `_sc_inject_workflow_contract` | Reads `env.registry`, browses the target record, calls workflow services, and mutates the projected contract in one integration step. |
| `smart_core_register` | Writes into the extension registry and is the loader-facing registration transaction. |
| `smart_core_form_business_actions` | Browses `payment.request`, invokes the available-actions handler, and maps action availability into form-contract actions. |
| `smart_core_file_download_auth_subject` | Resolves attachment ownership through `payment.request` and defines the download authorization subject. |
| `_user_confirmed_formal_list_action_ids` | Resolves XMLIDs through `env.ref` for the finalizer boundary. |
| `smart_core_finalize_projected_contract_data` | Reads action/window metadata, generates list contracts, parses view XML, and locks user-confirmed formal list columns. |
| `smart_core_relation_entry_policy` | Computes relation-entry policy from request payload plus ORM-backed company, tax, contractor, and partner data. |

These functions may be mapped or tested further, but should not be migrated as a
batch. Any future extraction should isolate pure payload or normalization logic
inside one boundary at a time.

## Verification Required

Before opening the unified PR, run:

- `git diff --check`
- `make ci.local.quick`
- `make ci`

The PR description should state that the branch is a pure responsibility split:
no business feature, migration, menu, permission, or frontend behavior changes
are intended.

## Next Step After Merge

After this branch merges, do not continue reducing `core_extension.py` line
count mechanically. Move to the next owner-reviewed complexity candidate, or add
behavior tests for a frozen transaction boundary if a concrete regression risk
is found.

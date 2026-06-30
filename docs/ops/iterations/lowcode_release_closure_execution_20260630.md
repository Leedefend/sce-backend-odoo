# Low-Code Release Closure Execution 2026-06-30

## Branch

- branch: `topic/lowcode-release-closure`
- source plan: `docs/ops/iterations/lowcode_release_closure_plan_20260630.md`
- current phase: P0 release-gate closure completed

## Current Baseline

The low-code release closure skeleton is already wired. `verify.business_config.full_acceptance`
aggregates the required inventory, unit, frontend build, coverage, snapshot, approval runtime,
browser acceptance, low-code browser checks, and user-menu reachability gates.

Initial evidence:

- `make verify.business_config.guard_inventory`: PASS
- `make verify.business_config.unit`: PASS
- `make verify.frontend.build`: PASS
- `make verify.docs.inventory`: PASS
- `make verify.docs.temp_guard`: PASS
- `make verify.business_config.coverage DB_NAME=sc_demo`: PASS
- `make verify.business_config.snapshot DB_NAME=sc_demo`: PASS
- `make verify.business_config.approval_runtime DB_NAME=sc_demo`: PASS

Closure evidence:

- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_demo`: PASS
- `make verify.user_menu.reachability.guard DB_NAME=sc_demo`: PASS (`checked_actions=118`, `relation_models=885`, `skipped=0`)
- `make verify.business_config.coverage DB_NAME=sc_demo`: PASS after fixing the `sc.business.entity` list/search contract gap
- `make verify.business_config.full_acceptance DB_NAME=sc_demo`: PASS

## Execution Scope

This topic branch treats low-code release closure as a product release surface, not a sequence of
single bug fixes. Work must stay inside the seven acceptance areas from the source plan:

| Area | Delivery Rule | Evidence Target |
| --- | --- | --- |
| Menu configuration | Business navigation must be driven by user menu configuration contracts. System menus are material and fallback only. | `verify.business_config.low_code_menu_navigation_alignment`, `verify.business_config.browser_acceptance` |
| Form configuration | Saved form configuration, preview, and runtime business page must render the same field/group/layout contract. | `verify.business_config.low_code_runtime_consistency`, `verify.business_config.low_code_group_matrix`, `verify.business_config.low_code_layout_runtime` |
| Contract v2 | Runtime must prefer standard v2 contract fields. Compat paths must be declared and auditable. | `verify.business_config.unit`, `verify.business_config.snapshot` |
| List/search | list/count/export/read must use consistent domains and alias fields. | `verify.business_config.coverage`, `verify.business_config.low_code_acceptance` |
| Permission and scope | Users must only configure and see capabilities inside their business role, company, and menu scope. | `verify.business_config.unit`, `verify.user_menu.reachability.guard` |
| Versioning | Users must see current version, changes, rollback path, and audit summary. | `verify.business_config.snapshot`, `verify.business_config.low_code_acceptance` |
| Release upgrade | Local acceptance must complete before any dev-server upgrade or release publish. | `verify.business_config.full_acceptance` |

## P0 Task Queue

1. Inventory gate verification
   - Status: done
   - Evidence: `make verify.business_config.guard_inventory` PASS
   - Output: The Makefile target inventory, capability matrix, boundary constants, and source markers are consistent.

2. Unit and static boundary verification
   - Status: done
   - Command: `make verify.business_config.unit`
   - Evidence: business-language guard, backend boundary guard, contract schema, API write ID boundaries, form config, surface, menu audit, and approval handler tests all pass.

3. Runtime evidence collection
   - Status: done
   - Commands:
     - `make verify.business_config.coverage DB_NAME=<db>`
     - `make verify.business_config.snapshot DB_NAME=<db>`
     - `make verify.business_config.approval_runtime DB_NAME=<db>`
   - Output files:
     - `artifacts/backend/business_config_coverage_gate.json`
     - `artifacts/backend/business_config_contract_snapshot.json`
   - Evidence:
     - `sc_demo` coverage scope count: 11
     - failed scope count: 0
     - initial business config contract count: 1069
     - initial published contract count: 1069
     - final business config contract count: 1071
     - final published contract count: 1071
     - snapshot diff: 0 changed, 0 added, 0 removed
     - approval runtime smoke: PASS

4. Browser acceptance pass
   - Status: done
   - Commands:
     - `make verify.business_config.browser_acceptance DB_NAME=sc_demo`
     - `make verify.business_config.low_code_acceptance DB_NAME=sc_demo`
     - `make verify.business_config.low_code_runtime_consistency DB_NAME=sc_demo`
     - `make verify.business_config.low_code_group_matrix DB_NAME=sc_demo`
     - `make verify.business_config.low_code_layout_runtime DB_NAME=sc_demo`
     - `make verify.business_config.low_code_menu_navigation_alignment DB_NAME=sc_demo`
     - `make verify.business_config.low_code_global_stability DB_NAME=sc_demo`
   - Evidence:
     - browser runtime routes: `51/51`, failed `0`
     - low-code acceptance: `ok=true`, warnings `[]`, errors `[]`
     - runtime consistency: `sc.general.contract` field `subcontract_mode` group/label changes match config and runtime
     - form group matrix: 5 groups, 20 group moves plus drag path, all config/runtime/DOM groups aligned
     - layout runtime: 2 samples, page columns/group columns/field size/group visibility restore paths pass
     - menu navigation alignment: expected `154`, actual `154`, no missing/unexpected/duplicate/label/parent mismatches
     - global stability: list/search, analysis, and approval runtime checks pass

5. Full release acceptance
   - Status: done
   - Command: `make verify.business_config.full_acceptance DB_NAME=sc_demo`
   - Evidence: PASS

## Fixes Applied

1. User menu reachability action metadata
   - File: `scripts/verify/user_menu_reachability_guard.py`
   - Change: action metadata reads now sudo-resolve technical `ir.actions.act_window` payloads while preserving target-user model and relation probes.
   - Reason: business users should not need direct read ACLs on technical action-view metadata for the reachability guard to inspect their runnable menus.

2. Business entity map relation ACL
   - File: `addons/smart_construction_core/security/ir.model.access.csv`
   - Change: added read access for `sc.legacy.business.entity.map` to `group_sc_cap_business_config_admin`.
   - Reason: the "业务核算主体" form exposes `map_ids`, so business configuration admins need read access to validate reachable relation fields.

3. Business entity list/search contracts
   - File: `addons/smart_construction_core/data/view_orchestration_contract_generated_data.xml`
   - Change: added generated `tree` and `search` contracts for `sc.business.entity`.
   - Reason: after menu/user preference regeneration, action `706` ("业务核算主体") is visible to `wutao`; coverage requires form, list, and search contracts for the runtime page.

## P1 Release Preflight Closure

Status: done

Release preflight evidence:

- `python3 -m py_compile addons/smart_core/models/release_management.py addons/smart_core/delivery/menu_service.py scripts/verify/platform_release_policy_runtime_probe.py`: PASS
- `python3 addons/smart_core/tests/test_backend_semantic_copy_supply.py`: PASS (`8` tests)
- `python3 addons/smart_core/tests/test_delivery_menu_entry_target.py`: PASS (`14` tests)
- `pnpm -C frontend/apps/web lint`: PASS
- `make verify.product.delivery.governance_truth DB_NAME=sc_demo`: PASS
- `DB_NAME=sc_demo SC_SCENE_ACTION_SURFACE_STRATEGY_PAYLOAD_REQUIRE_LIVE=1 python3 scripts/verify/scene_action_surface_strategy_payload_guard.py`: PASS
- `CI_SCENE_DELIVERY_PROFILE=strict make ci.scene.delivery.readiness DB_NAME=sc_demo`: PASS
- `CI_SCENE_DELIVERY_PROFILE=restricted make ci.scene.delivery.readiness DB_NAME=sc_demo`: PASS
- `make verify.release.v2_0_0.preflight DB_NAME=sc_demo`: PASS

Release fixes applied:

1. Product policy source authority
   - File: `addons/smart_core/models/release_management.py`
   - Change: `sc.product.policy.to_runtime_dict()` now emits `policy_source_authority`.
   - Reason: `ProductPolicyService.get_policy()` treats policies without source authority as untrusted and falls back to `minimal_default_product_policy_provider`.

2. Delivery menu native authorization boundary
   - Files:
     - `addons/smart_core/delivery/menu_service.py`
     - `addons/smart_core/tests/test_delivery_menu_entry_target.py`
   - Change: removed non-admin env group/model ACL fallback from policy menu authorization; added regression coverage proving empty native facts do not authorize policy menu delivery.
   - Reason: release policy runtime must not leak policy menus when native navigation has no corresponding authorization fact.

3. Release policy runtime probe comparison
   - File: `scripts/verify/platform_release_policy_runtime_probe.py`
   - Change: admin/user comparison now checks `stable_leaf_count` instead of total delivered leaf count.
   - Reason: user delivery can include native preview supplements outside the stable product policy surface; release policy parity should compare the released stable surface.

4. Frontend gate lint closure
   - Files:
     - `frontend/apps/web/src/app/contracts/v2/store.ts`
     - `frontend/apps/web/src/components/template/FormSection.vue`
     - `frontend/apps/web/src/views/BusinessConfigSurfaceView.vue`
   - Change: removed unused snapshot argument, renamed field-order drop placement helper to avoid prop key collision, and deleted two unused row action wrappers.
   - Reason: `verify.product.delivery.mainline` runs the frontend gate as part of release preflight.

5. Startup action-surface strategy payload
   - Files:
     - `addons/smart_core/core/system_init_payload_builder.py`
     - `addons/smart_core/tests/test_system_init_payload_builder_semantics.py`
   - Change: startup minimal surface now preserves the normalized `scene_action_surface_strategy` payload and has unit coverage for the passthrough.
   - Reason: strict scene readiness requires live `system.init` to expose the action-surface strategy governance payload, not only compute it internally for scene-ready assembly.

6. Local restricted verification environment repair
   - Runtime actions:
     - restored `demo_role_pm`, `demo_role_finance`, and `demo_role_executive` login/password posture for `sc_demo`
     - applied `sc.core.extension_modules` policy via `AUTO_FIX_EXTENSION_MODULES=1 make policy.ensure.extension_modules DB_NAME=sc_demo`
     - seeded secondary company access via `make ops.scene.company_secondary.seed DB_NAME=sc_demo APPLY=1 CREATE_COMPANY_IF_MISSING=1 CREATE_USER_IF_MISSING=1`
   - Reason: restricted scene readiness requires live role and company snapshots. The code gate was valid, but local `sc_demo` had stale role credentials, missing extension module entries, and missing secondary company access.

## Final Re-Run Evidence

Status: done

After the strict startup payload fix, the branch was re-validated against both the release preflight
and the original low-code acceptance surface.

- `python3 addons/smart_core/tests/test_system_init_payload_builder_semantics.py`: PASS (`16` tests)
- `DB_NAME=sc_demo SC_SCENE_ACTION_SURFACE_STRATEGY_PAYLOAD_REQUIRE_LIVE=1 python3 scripts/verify/scene_action_surface_strategy_payload_guard.py`: PASS
- `CI_SCENE_DELIVERY_PROFILE=strict make ci.scene.delivery.readiness DB_NAME=sc_demo`: PASS
- `make verify.release.v2_0_0.preflight DB_NAME=sc_demo`: PASS
- `make verify.business_config.full_acceptance DB_NAME=sc_demo`: PASS
  - runtime routes: `51/51`, failed `0`
  - low-code business config acceptance: `ok=true`, errors `[]`, warnings `[]`
  - runtime consistency: PASS
  - group matrix: PASS, 5 groups, 20 select moves plus drag path
  - layout runtime: PASS, 2 samples
  - menu navigation alignment: expected `154`, actual `154`, mismatches `0`
  - global stability: PASS
  - user menu reachability: PASS, `checked_actions=118`, `relation_models=885`, `skipped=0`

## Decision Rules

- If `guard_inventory` fails, fix wiring or matrix drift before touching runtime behavior.
- If `unit` fails, fix contract, boundary, or intent semantics before running browser checks.
- If coverage or snapshot fails, preserve generated artifacts and update this execution file with the failing capability, model/action scope, and reason code.
- If browser acceptance fails, classify it into menu, form, list/search, permission/scope, or versioning before applying code changes.
- Do not mark a capability release-ready just because its target exists. The target must pass and produce user-facing evidence.

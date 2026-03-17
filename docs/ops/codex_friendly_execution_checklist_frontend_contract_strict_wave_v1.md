# Codex Friendly Execution Checklist - Frontend Strict Contract Consumption Wave v1

## Branch and Objective
- Branch: `feature/product-closure-wave2-workbench-chain`
- Objective:
  - pilot scenes consume backend semantic contract as sole source in strict mode;
  - frontend business heuristics are disabled for pilot scenes;
  - runtime fallback is limited to UI-only neutral behavior.

## Source-of-Truth
- Preferred runtime source: backend `scene_ready`.
- Secondary source only when not yet materialized in `scene_ready`: backend `scene_contract`.
- Strict mode source:
  - `runtime_policy.strict_contract_mode=true` (highest priority)
  - `scene_tier=core` (secondary)
- Frontend must follow declared source priority and must not merge semantic truth by heuristic.
- Frontend must not create its own strict-scene registry.

## Execution Sequence
1. finalize docs/inventory/guardrail rules.
2. materialize scene surface contract into `scene_ready` for pilot scenes.
3. materialize action surface contract into `scene_ready` for pilot scenes.
4. materialize projection contract into `scene_ready` for pilot scenes.
5. frontend strict mode consumes backend policy only.
6. frontend strict mode exposes explicit contract-missing state.
7. remove ActionView semantic heuristics for pilot scenes.
8. unify mutation/refresh runtime across ActionView/Home/Form.
9. add verification coverage and pass gates.

## File-Level Task Map
- Frontend:
  - `frontend/apps/web/src/views/ActionView.vue`
  - `frontend/apps/web/src/views/HomeView.vue`
  - `frontend/apps/web/src/pages/ContractFormPage.vue`
  - `frontend/apps/web/src/app/contractStrictMode.ts`
  - `frontend/apps/web/src/app/sceneActionProtocol.ts`
  - `frontend/apps/web/src/app/projectionRefreshRuntime.ts`
  - `frontend/apps/web/src/app/sceneMutationRuntime.ts`
  - `frontend/apps/web/src/app/resolvers/sceneReadyResolver.ts`
  - `frontend/apps/web/src/app/pageContract.ts`
  - `frontend/apps/web/src/utils/semantic.ts`
- Backend:
  - `addons/smart_core/core/scene_ready_contract_builder.py`
  - `addons/smart_construction_scene/data/sc_scene_layout.xml`
  - `addons/smart_construction_scene/data/sc_scene_list_profile.xml`
  - `addons/smart_construction_scene/data/project_management_scene.xml`
  - `addons/smart_construction_scene/profiles/scene_registry_content.py`
  - `addons/smart_construction_core/core_extension.py`
- Tests:
  - `addons/smart_core/tests/test_scene_runtime_contract_chain.py`
  - `addons/smart_construction_core/tests/test_risk_action_execute_backend.py`

## Materialization Rule
- Contract fields required by pilot scenes must be materialized into `scene_ready`, not only declared in XML/config source.

## Forbidden Shortcuts
- Do not add frontend hardcoded core-scene sets as strict mode source.
- Do not reintroduce keyword-based semantic inference for pilot scenes.
- Do not keep old heuristic branches silently active behind new contract consumption.
- Do not satisfy backend contract work by config-only declaration without `scene_ready` materialization.
- Do not merge semantic truth from multiple sources by frontend guesswork.

## Gate Checklist (Deterministic)
- Gate 1:
  - no frontend hardcoded core-scene allowlist/set is referenced by strict mode runtime;
  - pilot scenes read strictness from `runtime_policy.strict_contract_mode` or `scene_tier=core` from backend payload only.
- Gate 2:
  - in strict mode, `summary_items`, `overview_strip`, and `group_summary` are read from backend payload;
  - frontend aggregation branches are not executed for pilot scenes.
- Gate 3:
  - in strict mode, ActionView grouping uses `action_surface.groups` or flat ordered actions only;
  - keyword grouping fallback branch is not executed for pilot scenes.
- Gate 4:
  - when required semantic contract is missing in strict mode, UI shows explicit contract-missing state;
  - frontend does not fabricate business labels, grouping, summaries, or semantic status.
- Gate 5:
  - lint/tests for changed modules pass.

## Commit Policy
- Keep independent commits by concern:
  - docs
  - backend contract
  - frontend runtime
  - tests/verify
- No mixed mega-commit.

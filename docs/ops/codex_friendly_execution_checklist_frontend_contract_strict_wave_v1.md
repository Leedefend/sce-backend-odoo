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

## Iteration Kanban (Close-out Tracker)

| ID | Phase | Item | Layer Target | Module | Status | Exit Criteria |
| --- | --- | --- | --- | --- | --- | --- |
| W1-01 | P0 | Freeze architecture/spec baseline | Frontend Layer (Docs) | `docs/architecture/frontend_contract_runtime_architecture_wave_v1.md` | DONE | six-layer boundary, data flow, forbidden shortcuts merged |
| W1-02 | P0 | Build executable checklist tracker | Frontend Layer (Docs) | `docs/ops/codex_friendly_execution_checklist_frontend_contract_strict_wave_v1.md` | DONE | itemized IDs, status, exit criteria maintained |
| W1-03 | P0 | Extract strict contract consumption module | Contract Consumption Layer | `frontend/apps/web/src/app/contracts/actionViewStrictContract.ts` | DONE | ActionView strict-mode contract parsing moved to dedicated module |
| W1-04 | P0 | Wire ActionView to strict module | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView no longer defines strict parsing branch inline |
| W1-05 | P1 | Add boundary verify for new module usage | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard enforces strict module usage and no regression |
| W1-06 | P1 | Run verify gates and publish evidence | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | targeted verify targets pass and reports updated |
| W2-01 | P1 | Extract view/surface contract resolvers | Contract Consumption Layer | `frontend/apps/web/src/app/contracts/actionViewSurfaceContract.ts` | DONE | view-mode + surface-intent resolution moved out of ActionView |
| W2-02 | P1 | Wire ActionView to new resolvers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView consumes shared resolver APIs for view/surface |
| W2-03 | P1 | Extend guard for resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires shared resolver tokens |
| W2-04 | P1 | Re-run verify gates after extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with resolver extraction |
| W3-01 | P1 | Extract projection/surface resolver module | Contract Consumption Layer | `frontend/apps/web/src/app/contracts/actionViewProjectionContract.ts` | DONE | surface-kind and projection metric parsing moved out of ActionView |
| W3-02 | P1 | Wire ActionView projection/surface to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView consumes projection/surface resolver APIs |
| W3-03 | P1 | Extend guard for projection resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires projection resolver tokens |
| W3-04 | P1 | Re-run verify gates after projection extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with projection extraction |
| W4-01 | P1 | Extract group-window route runtime module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupWindowRuntime.ts` | DONE | group page parse/serialize/offset normalization moved out of ActionView |
| W4-02 | P1 | Wire ActionView group-window runtime imports | Runtime Execution Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses shared runtime helpers for group window |
| W4-03 | P1 | Extend guard for runtime helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires runtime helper tokens |
| W4-04 | P1 | Re-run verify gates after runtime extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with runtime extraction |
| W5-01 | P1 | Extract advanced-view contract resolver | Contract Consumption Layer | `frontend/apps/web/src/app/contracts/actionViewAdvancedContract.ts` | DONE | advanced title/hint resolution moved out of ActionView |
| W5-02 | P1 | Wire ActionView advanced-view to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView consumes advanced-view resolver API |
| W5-03 | P1 | Extend guard for advanced resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires advanced-view resolver tokens |
| W5-04 | P1 | Re-run verify gates after advanced extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with advanced-view extraction |
| W6-01 | P1 | Extract contract sanitization helpers | Contract Consumption Layer | `frontend/apps/web/src/app/contracts/actionViewContractSanitizer.ts` | DONE | numeric/noise token filters moved out of ActionView |
| W6-02 | P1 | Wire ActionView sanitization helper usage | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses shared sanitization helper APIs |
| W6-03 | P1 | Extend guard for sanitizer adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires sanitizer helper tokens |
| W6-04 | P1 | Re-run verify gates after sanitizer extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with sanitizer extraction |
| W7-01 | P1 | Extract request-context runtime helpers | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRequestRuntime.ts` | DONE | filter/group/request context assembly helpers moved out of ActionView |
| W7-02 | P1 | Wire ActionView request runtime helper usage | Runtime Execution Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView delegates default sort and request context composition |
| W7-03 | P1 | Extend guard for request runtime adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires request runtime helper tokens |
| W7-04 | P1 | Re-run verify gates after request runtime extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with request runtime extraction |
| W8-01 | P1 | Extract route patch runtime helpers | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRouteRuntime.ts` | DONE | list/filter/group query patch builders moved out of ActionView |
| W8-02 | P1 | Wire ActionView route patch helper usage | Runtime Execution Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView delegates list/filter/group query patch construction |
| W8-03 | P1 | Extend guard for route runtime adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires route runtime helper tokens |
| W8-04 | P1 | Re-run verify gates after route runtime extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with route runtime extraction |
| W10-01 | P1 | Extract action meta runtime helpers | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewMetaRuntime.ts` | DONE | view_type/res_id parsing moved out of ActionView |
| W10-02 | P1 | Wire ActionView meta helper usage | Runtime Execution Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView delegates action view-type/res_id parsing |
| W10-03 | P1 | Extend guard for meta runtime adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires meta helper tokens |
| W10-04 | P1 | Re-run verify gates after meta extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with meta extraction |
| W11-01 | P1 | Extract group-drilldown route runtime helpers | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupDrilldownRuntime.ts` | DONE | group summary/window route patch builders moved out of ActionView |
| W11-02 | P1 | Wire ActionView group-drilldown helper usage | Runtime Execution Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView delegates group summary/window query patch construction |
| W11-03 | P1 | Extend guard for group-drilldown helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires group-drilldown helper tokens |
| W11-04 | P1 | Re-run verify gates after group-drilldown extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with group-drilldown extraction |
| W12-01 | P1 | Extract grouped-rows pagination helpers | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRowsRuntime.ts` | DONE | grouped rows field/page limit/window calculations moved out of ActionView |
| W12-02 | P1 | Wire ActionView grouped-rows helper usage | Runtime Execution Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView delegates grouped rows pagination calculations |
| W12-03 | P1 | Extend guard for grouped-rows helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires grouped-rows helper tokens |
| W12-04 | P1 | Re-run verify gates after grouped-rows extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with grouped-rows extraction |
| W13-01 | P1 | Extract group-shared state runtime helpers | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupStateRuntime.ts` | DONE | group reset/move shared state builders moved out of ActionView |
| W13-02 | P1 | Wire ActionView group-shared state helpers | Runtime Execution Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView delegates group reset/move state initialization |
| W13-03 | P1 | Extend guard for group-shared helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires group-shared helper tokens |
| W13-04 | P1 | Re-run verify gates after group-shared extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with group-shared extraction |
| W14-01 | P1 | Extract grouped-rows request builders | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRowsRuntime.ts` | DONE | grouped rows request payload/state patch builders moved out of ActionView |
| W14-02 | P1 | Wire ActionView grouped-rows request builders | Runtime Execution Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView delegates grouped rows request payload/state assembly |
| W14-03 | P1 | Extend guard for grouped-rows request builder adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires grouped-rows request builder tokens |
| W14-04 | P1 | Re-run verify gates after grouped-rows request extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with grouped-rows request extraction |
| W15-01 | P1 | Extract grouped-route normalize runtime helpers | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRouteNormalizeRuntime.ts` | DONE | grouped route normalization/patch/offset checks moved out of ActionView |
| W15-02 | P1 | Wire ActionView grouped-route normalize helper usage | Runtime Execution Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView delegates grouped route normalization and patch construction |
| W15-03 | P1 | Extend guard for grouped-route normalize helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires grouped-route normalize helper tokens |
| W15-04 | P1 | Re-run verify gates after grouped-route normalize extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with grouped-route normalize extraction |
| W16-01 | P1 | Extract requested-field normalization helpers | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRequestRuntime.ts` | DONE | unique/requested field normalization moved out of ActionView |
| W16-02 | P1 | Wire ActionView requested-field helper usage | Runtime Execution Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView delegates requested field and uniqueness normalization |
| W16-03 | P1 | Extend guard for requested-field helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires requested-field runtime helper tokens |
| W16-04 | P1 | Re-run verify gates after requested-field extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with requested-field extraction |
| W17-01 | P1 | Extract route-sync query builder helper | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRouteRuntime.ts` | DONE | route sync query construction moved out of ActionView |
| W17-02 | P1 | Wire ActionView route-sync helper usage | Runtime Execution Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView delegates route sync query composition |
| W17-03 | P1 | Extend guard for route-sync helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires route-sync runtime helper token |
| W17-04 | P1 | Re-run verify gates after route-sync extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with route-sync extraction |
| W18-01 | P1 | Extract route-patch query helper | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRouteRuntime.ts` | DONE | route patch query composition moved out of ActionView |
| W18-02 | P1 | Wire ActionView route-patch helper usage | Runtime Execution Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView delegates filter/group route patch query construction |
| W18-03 | P1 | Extend guard for route-patch helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires route-patch runtime helper token |
| W18-04 | P1 | Re-run verify gates after route-patch extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with route-patch extraction |
| W19-01 | P1 | Extract preset-clear route helper | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRouteRuntime.ts` | DONE | preset clear query construction moved out of ActionView |
| W19-02 | P1 | Wire ActionView preset-clear helper usage | Runtime Execution Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView delegates preset-clear query normalization |
| W19-03 | P1 | Extend guard for preset-clear helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires preset-clear runtime helper token |
| W19-04 | P1 | Re-run verify gates after preset-clear extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with preset-clear extraction |
| W20-01 | P1 | Extract grouped-page field bridge helper | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRowsRuntime.ts` | DONE | grouped page requested-field bridge moved out of ActionView |
| W20-02 | P1 | Wire ActionView grouped-page field helper usage | Runtime Execution Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView delegates grouped page field selection |
| W20-03 | P1 | Extend guard for grouped-page helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires grouped-page field helper token |
| W20-04 | P1 | Re-run verify gates after grouped-page extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with grouped-page extraction |
| W21-01 | P1 | Extract group-window route sync plan helper | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupWindowRuntime.ts` | DONE | group window route sync/reset plan moved out of ActionView |
| W21-02 | P1 | Wire ActionView to route sync plan helper | Runtime Execution Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView delegates route sync reset/sync patch decisions |
| W21-03 | P1 | Extend guard for route sync plan adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires route sync plan helper token |
| W21-04 | P1 | Re-run verify gates after route sync plan extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with route sync plan extraction |
| W22-01 | P1 | Extract group-drilldown transition state helpers | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupDrilldownRuntime.ts` | DONE | drilldown/open/clear state transitions moved out of ActionView |
| W22-02 | P1 | Wire ActionView drilldown state helper usage | Runtime Execution Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView delegates drilldown transition state calculation |
| W22-03 | P1 | Extend guard for drilldown state helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires drilldown state helper tokens |
| W22-04 | P1 | Re-run verify gates after drilldown state extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with drilldown state extraction |
| W23-01 | P1 | Extract group-window move target helper | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupDrilldownRuntime.ts` | DONE | prev/next move target decision moved out of ActionView |
| W23-02 | P1 | Wire ActionView unified group-window move handler | Runtime Execution Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses single move path for prev/next |
| W23-03 | P1 | Extend guard for group-window move helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires group-window move target helper token |
| W23-04 | P1 | Re-run verify gates after group-window move extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with group-window move extraction |
| W24-01 | P1 | Extract group-control transition helpers | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupDrilldownRuntime.ts` | DONE | sample-limit/sort/collapsed transition logic moved out of ActionView |
| W24-02 | P1 | Wire ActionView group-control transition helpers | Runtime Execution Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView delegates group control transition normalization |
| W24-03 | P1 | Extend guard for group-control transition adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires group-control transition helper tokens |
| W24-04 | P1 | Re-run verify gates after group-control extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with group-control extraction |
| W25-01 | P1 | Centralize route-patch reload execution path | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | route patch + reload flow consolidated into single helper |
| W25-02 | P1 | Refactor ActionView route-patch call sites | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | filter/group/drilldown clear handlers use unified route-patch helper |
| W25-03 | P1 | Extend guard for unified route-patch flow | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires unified route-patch helper token |
| W25-04 | P1 | Re-run verify gates after route-patch flow unification | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with unified route-patch flow |
| W26-01 | P1 | Extract group-window sync patch merge helper | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupWindowRuntime.ts` | DONE | route sync patch aggregation moved out of ActionView |
| W26-02 | P1 | Wire ActionView single group-window sync dispatch | Runtime Execution Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView sends merged sync patch once per response cycle |
| W26-03 | P1 | Extend guard for group-window sync merge adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires group-window sync merge helper token |
| W26-04 | P1 | Re-run verify gates after sync merge extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with sync merge extraction |
| W27-01 | P1 | Add unified sync-route-and-reload helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | sync+reload and restart-with-sync paths centralized |
| W27-02 | P1 | Refactor ActionView sync+reload call sites | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | group summary/open/move/limit handlers use unified sync+reload helper |
| W27-03 | P1 | Extend guard for unified sync+reload flow | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires sync+reload helper tokens |
| W27-04 | P1 | Re-run verify gates after sync+reload unification | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with unified sync+reload flow |
| W28-01 | P1 | Extract route-target builders for replace navigation | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRouteRuntime.ts` | DONE | workbench/path/model-form route target construction moved out of ActionView |
| W28-02 | P1 | Wire ActionView navigation to route-target builders | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView replaces inline route objects with shared builder outputs |
| W28-03 | P1 | Extend guard for route-target builder adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires route-target builder tokens |
| W28-04 | P1 | Re-run verify gates after route-target extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with route-target extraction |
| W29-01 | P1 | Extract route-query snapshot resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRouteRuntime.ts` | DONE | route query parsing normalized into shared runtime snapshot |
| W29-02 | P1 | Wire ActionView to route-query snapshot resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView reuses normalized snapshot across preset/group sync flows |
| W29-03 | P1 | Extend guard for route-query snapshot adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires route-query snapshot resolver token |
| W29-04 | P1 | Re-run verify gates after route-query snapshot extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with route-query snapshot extraction |
| W30-01 | P1 | Add normalized route-query map helper | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRouteRuntime.ts` | DONE | raw route query normalization moved to shared runtime helper |
| W30-02 | P1 | Batch replace ActionView route-query cast points | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView consumes normalized route-query map instead of repeated casts |
| W30-03 | P1 | Extend guard for normalized route-query helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires normalized route-query helper token |
| W30-04 | P1 | Re-run verify gates after route-query cast unification | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with route-query cast unification |
| W31-01 | P1 | Extract group runtime state container | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupRuntimeState.ts` | DONE | grouped runtime refs moved out of ActionView local declarations |
| W31-02 | P1 | Wire ActionView to externalized group runtime state | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView consumes grouped state via runtime state factory |
| W31-03 | P1 | Extend guard for group runtime state container adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires group runtime state factory token |
| W31-04 | P1 | Re-run verify gates after group runtime state extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with group runtime state extraction |
| W32-01 | P1 | Extract group shared-state applier into runtime state module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupRuntimeState.ts` | DONE | shared group state application moved out of ActionView |
| W32-02 | P1 | Wire ActionView shared-state apply to runtime module | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView delegates shared state application through runtime applier |
| W32-03 | P1 | Extend guard for shared-state applier adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires shared-state applier token |
| W32-04 | P1 | Re-run verify gates after shared-state applier extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with shared-state applier extraction |
| W33-01 | P1 | Keep group runtime state as single object | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | grouped runtime refs derive from one state object source |
| W33-02 | P1 | Simplify shared-state delegation call path | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView shared-state apply uses single runtime state object directly |
| W33-03 | P1 | Extend guard for single group runtime object adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires group runtime state object token |
| W33-04 | P1 | Re-run verify gates after group runtime object unification | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with group runtime object unification |
| W34-01 | P1 | Add group runtime capsule API | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupRuntimeState.ts` | DONE | runtime state factory upgraded to capsule with shared-state method |
| W34-02 | P1 | Wire ActionView to group runtime capsule | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView consumes grouped runtime via capsule state + methods |
| W34-03 | P1 | Extend guard for capsule adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires group runtime capsule tokens |
| W34-04 | P1 | Re-run verify gates after capsule migration | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with group runtime capsule migration |
| W35-01 | P1 | Extract group interaction handlers runtime composable | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/useActionViewGroupRuntime.ts` | DONE | group summary/window/limit/sort/collapsed handlers moved to runtime composable |
| W35-02 | P1 | Wire ActionView to group interaction runtime composable | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView delegates group interaction handlers to runtime composable |
| W35-03 | P1 | Extend guard for group interaction composable adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `useActionViewGroupRuntime` token and drops local drilldown token requirements |
| W35-04 | P1 | Re-run verify gates after group interaction extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with group interaction handler extraction |
| W36-01 | P1 | Extract contract load mode and route-selection resolvers | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewContractLoadRuntime.ts` | DONE | view-mode resolution and route filter/group selection reconciliation moved out of ActionView |
| W36-02 | P1 | Wire ActionView load preflight to contract-load runtime | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView `load()` uses shared resolvers for preferred mode and route selection state |
| W36-03 | P1 | Extend guard for contract-load runtime adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolvePreferredActionViewMode` and `resolveRouteSelectionState` tokens |
| W36-04 | P1 | Re-run verify gates after contract-load extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with contract-load resolver extraction |
| W37-01 | P1 | Extract load early-exit guard resolvers | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadGuardRuntime.ts` | DONE | contract-read/capability/missing-model guard payload derivation moved out of ActionView |
| W37-02 | P1 | Wire ActionView to load-guard runtime resolvers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView `load()` delegates early-exit guard decisions to runtime resolvers |
| W37-03 | P1 | Extend guard for load-guard runtime adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires load-guard resolver tokens |
| W37-04 | P1 | Re-run verify gates after load-guard extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with load-guard resolver extraction |
| W38-01 | P1 | Extract load sort/limit/request builders | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadRequestRuntime.ts` | DONE | sort seed, contract limit, and list request payload builders moved out of ActionView |
| W38-02 | P1 | Wire ActionView load request assembly to runtime builders | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView `load()` delegates sort seed, limit normalize, and list request payload construction |
| W38-03 | P1 | Extend guard for load-request runtime adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires load-request runtime resolver tokens |
| W38-04 | P1 | Re-run verify gates after load-request extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with load-request runtime extraction |
| W39-01 | P1 | Extract group paging/window identity parser | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupPagingRuntime.ts` | DONE | grouped paging offset/window identity parsing moved out of ActionView |
| W39-02 | P1 | Wire ActionView to group paging parser runtime | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView `load()` consumes parsed group paging state from runtime helper |
| W39-03 | P1 | Extend guard for group paging parser adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveActionViewGroupPagingState` token |
| W39-04 | P1 | Re-run verify gates after group paging extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with group paging parser extraction |
| W40-01 | P1 | Extract group route-sync payload adapter | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupRouteSyncRuntime.ts` | DONE | route-sync plan payload shaping moved out of ActionView |
| W40-02 | P1 | Wire ActionView route-sync planning to adapter | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView calls `buildGroupWindowRouteSyncPlan` with runtime-built payload |
| W40-03 | P1 | Extend guard for route-sync adapter adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `buildActionViewGroupRouteSyncPayload` token |
| W40-04 | P1 | Re-run verify gates after route-sync adapter extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with route-sync adapter extraction |
| W41-01 | P1 | Extract project-scope snapshot runtime loader | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewProjectScopeRuntime.ts` | DONE | list-mode scope totals/metrics concurrent loader moved out of ActionView |
| W41-02 | P1 | Wire ActionView project-scope loading to runtime | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView delegates scope totals/metrics loading to runtime snapshot loader |
| W41-03 | P1 | Extend guard for project-scope runtime adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `loadActionViewProjectScopeSnapshot` token |
| W41-04 | P1 | Re-run verify gates after project-scope extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with project-scope runtime extraction |
| W42-01 | P1 | Extract group-summary mapper runtime | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupSummaryRuntime.ts` | DONE | `group_summary` to summary-item mapping moved out of ActionView |
| W42-02 | P1 | Wire ActionView to group-summary mapper runtime | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView builds `groupSummaryItems` through runtime mapper |
| W42-03 | P1 | Extend guard for group-summary mapper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `mapActionViewGroupSummaryItems` token |
| W42-04 | P1 | Re-run verify gates after group-summary extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with group-summary mapper extraction |
| W43-01 | P1 | Extract group-window metrics resolver runtime | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupSummaryRuntime.ts` | DONE | group window count/start/end/next/prev metrics calculation moved out of ActionView |
| W43-02 | P1 | Wire ActionView to group-window metrics runtime | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView consumes runtime window metrics result to update window refs |
| W43-03 | P1 | Extend guard for group-window metrics adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveActionViewGroupWindowMetrics` token |
| W43-04 | P1 | Re-run verify gates after group-window metrics extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with group-window metrics extraction |
| W44-01 | P1 | Extract records resolver from load result | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadResultRuntime.ts` | DONE | list records parsing moved out of ActionView |
| W44-02 | P1 | Wire ActionView records assignment to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveActionViewRecords` for records state |
| W44-03 | P1 | Extend guard for records resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveActionViewRecords` token |
| W44-04 | P1 | Re-run verify gates after records resolver extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with records resolver extraction |
| W45-01 | P1 | Extract grouped-rows raw resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadResultRuntime.ts` | DONE | grouped_rows payload extraction moved out of ActionView |
| W45-02 | P1 | Wire ActionView grouped-rows source to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveActionViewGroupedRowsRaw` before grouped mapper |
| W45-03 | P1 | Extend guard for grouped-rows raw resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveActionViewGroupedRowsRaw` token |
| W45-04 | P1 | Re-run verify gates after grouped-rows raw extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with grouped-rows raw resolver extraction |
| W46-01 | P1 | Extract grouped-rows mapper runtime | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadResultRuntime.ts` | DONE | grouped rows normalize/map logic moved out of ActionView |
| W46-02 | P1 | Wire ActionView to grouped-rows mapper | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `mapActionViewGroupedRows` for grouped rows state |
| W46-03 | P1 | Extend guard for grouped-rows mapper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `mapActionViewGroupedRows` token |
| W46-04 | P1 | Re-run verify gates after grouped-rows mapper extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with grouped-rows mapper extraction |
| W47-01 | P1 | Extract active group-summary key resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadResultRuntime.ts` | DONE | route group_value to summary key matching moved out of ActionView |
| W47-02 | P1 | Wire ActionView active summary selection to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveActionViewActiveGroupSummaryKey` |
| W47-03 | P1 | Extend guard for active summary resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveActionViewActiveGroupSummaryKey` token |
| W47-04 | P1 | Re-run verify gates after active summary resolver extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with active summary resolver extraction |
| W48-01 | P1 | Extract selected-ids reconcile runtime | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadResultRuntime.ts` | DONE | selected IDs reconciliation against current records moved out of ActionView |
| W48-02 | P1 | Wire ActionView selected IDs reconcile to runtime | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `reconcileActionViewSelectedIds` |
| W48-03 | P1 | Extend guard for selected IDs reconcile adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `reconcileActionViewSelectedIds` token |
| W48-04 | P1 | Re-run verify gates after selected IDs reconcile extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with selected IDs reconcile extraction |
| W49-01 | P1 | Extract groupedRows page-change target resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRowsInteractionRuntime.ts` | DONE | groupedRows page-change limit/offset/skip decision moved out of ActionView |
| W49-02 | P1 | Wire ActionView page-change target to runtime resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveGroupedRowsPageChangeTarget` |
| W49-03 | P1 | Extend guard for page-change target resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveGroupedRowsPageChangeTarget` token |
| W49-04 | P1 | Re-run verify gates after page-change target extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with page-change target extraction |
| W50-01 | P1 | Extract groupedRows loading-state setter | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRowsInteractionRuntime.ts` | DONE | groupedRows loading state updates by key set moved out of ActionView |
| W50-02 | P1 | Wire ActionView loading-state updates to runtime setter | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `setGroupedRowsLoadingByKeys` |
| W50-03 | P1 | Extend guard for loading-state setter adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `setGroupedRowsLoadingByKeys` token |
| W50-04 | P1 | Re-run verify gates after loading-state setter extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with loading-state setter extraction |
| W51-01 | P1 | Extract groupedRows page-change success patcher | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRowsInteractionRuntime.ts` | DONE | groupedRows page update patching moved out of ActionView |
| W51-02 | P1 | Wire ActionView page-change success path to runtime patcher | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `applyGroupedRowsPageChangeSuccess` |
| W51-03 | P1 | Extend guard for page-change success patcher adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `applyGroupedRowsPageChangeSuccess` token |
| W51-04 | P1 | Re-run verify gates after page-change patcher extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with page-change patcher extraction |
| W52-01 | P1 | Extract groupedRows hydrate candidate resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRowsInteractionRuntime.ts` | DONE | hydrate candidate filtering moved out of ActionView |
| W52-02 | P1 | Wire ActionView hydrate candidates to runtime resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveGroupedRowsHydrateCandidates` |
| W52-03 | P1 | Extend guard for hydrate candidate resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveGroupedRowsHydrateCandidates` token |
| W52-04 | P1 | Re-run verify gates after hydrate candidate extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with hydrate candidate extraction |
| W53-01 | P1 | Extract groupedRows hydrate result applier | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRowsInteractionRuntime.ts` | DONE | hydrate update-map apply logic moved out of ActionView |
| W53-02 | P1 | Wire ActionView hydrate result path to runtime applier | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `applyGroupedRowsHydrateResults` |
| W53-03 | P1 | Extend guard for hydrate result applier adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `applyGroupedRowsHydrateResults` token |
| W53-04 | P1 | Re-run verify gates after hydrate result applier extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with hydrate result applier extraction |
| W54-01 | P1 | Extract grouped-route inactive reset resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRouteStateRuntime.ts` | DONE | inactive `group_by` reset decision and patch payloads moved out of ActionView |
| W54-02 | P1 | Wire ActionView inactive reset flow to runtime resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveGroupedRouteInactiveResetPlan` for early reset path |
| W54-03 | P1 | Extend guard for inactive reset resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveGroupedRouteInactiveResetPlan` token |
| W54-04 | P1 | Re-run verify gates after inactive reset extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with inactive reset extraction |
| W55-01 | P1 | Extract grouped-route normalize input builder | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRouteStateRuntime.ts` | DONE | grouped normalize input payload builder moved out of ActionView |
| W55-02 | P1 | Wire ActionView normalize input to runtime builder | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView calls `normalizeGroupedRouteCollections` with runtime-built input |
| W55-03 | P1 | Extend guard for normalize input builder adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `buildGroupedRouteNormalizeInput` token |
| W55-04 | P1 | Re-run verify gates after normalize input extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with normalize input extraction |
| W56-01 | P1 | Extract grouped-route selection reset resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRouteStateRuntime.ts` | DONE | active summary reset on invalid group value moved out of ActionView |
| W56-02 | P1 | Wire ActionView selection reset to runtime resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveGroupedRouteSelectionReset` |
| W56-03 | P1 | Extend guard for selection reset resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveGroupedRouteSelectionReset` token |
| W56-04 | P1 | Re-run verify gates after selection reset extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with selection reset extraction |
| W57-01 | P1 | Extract grouped-route sync decision resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRouteStateRuntime.ts` | DONE | grouped route sync decision boolean moved out of ActionView |
| W57-02 | P1 | Wire ActionView sync decision to runtime resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `shouldSyncGroupedRouteState` |
| W57-03 | P1 | Extend guard for sync decision resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `shouldSyncGroupedRouteState` token |
| W57-04 | P1 | Re-run verify gates after sync decision extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with sync decision extraction |
| W58-01 | P1 | Extract grouped-route active sync payload builder | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRouteStateRuntime.ts` | DONE | active grouped route patch payload builder moved out of ActionView |
| W58-02 | P1 | Wire ActionView active sync payload to runtime builder | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView calls `buildNormalizedGroupedRoutePatch` with runtime-built payload |
| W58-03 | P1 | Extend guard for active sync payload builder adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `buildGroupedRouteActiveSyncPayload` token |
| W58-04 | P1 | Re-run verify gates after active sync payload extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with active sync payload extraction |
| W59-01 | P1 | Extract contract-action open navigation resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewContractActionRuntime.ts` | DONE | open actionId/url navigation decision moved out of ActionView |
| W59-02 | P1 | Wire ActionView open action navigation to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveContractActionOpenNavigation` |
| W59-03 | P1 | Extend guard for open navigation resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveContractActionOpenNavigation` token |
| W59-04 | P1 | Re-run verify gates after open navigation extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with open navigation extraction |
| W60-01 | P1 | Extract contract-action execIds resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewContractActionRuntime.ts` | DONE | selection/context record execution IDs derivation moved out of ActionView |
| W60-02 | P1 | Wire ActionView execIds path to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveContractActionExecIds` |
| W60-03 | P1 | Extend guard for execIds resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveContractActionExecIds` token |
| W60-04 | P1 | Re-run verify gates after execIds extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with execIds extraction |
| W61-01 | P1 | Extract mutation runIds resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewContractActionRuntime.ts` | DONE | mutation fallback run IDs resolution moved out of ActionView |
| W61-02 | P1 | Wire ActionView mutation loop to runIds resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveContractActionRunIds` |
| W61-03 | P1 | Extend guard for runIds resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveContractActionRunIds` token |
| W61-04 | P1 | Re-run verify gates after runIds extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with runIds extraction |
| W62-01 | P1 | Extract contract-action selection message resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewContractActionRuntime.ts` | DONE | contract action selection validation outcome moved out of ActionView |
| W62-02 | P1 | Wire ActionView selection validation to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveContractActionSelectionMessage` |
| W62-03 | P1 | Extend guard for selection message resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveContractActionSelectionMessage` token |
| W62-04 | P1 | Re-run verify gates after selection message extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with selection message extraction |
| W63-01 | P1 | Extract executeButton request builder | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewContractActionRuntime.ts` | DONE | executeButton request payload builder moved out of ActionView |
| W63-02 | P1 | Wire ActionView executeButton calls to request builder | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `buildContractActionButtonRequest` |
| W63-03 | P1 | Extend guard for request builder adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `buildContractActionButtonRequest` token |
| W63-04 | P1 | Re-run verify gates after request builder extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with request builder extraction |
| W64-01 | P1 | Extract batch action guard resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchRuntime.ts` | DONE | batch action precheck (model/selection/active/delete_mode) moved out of ActionView |
| W64-02 | P1 | Wire ActionView batch action precheck to runtime resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveBatchActionGuard` |
| W64-03 | P1 | Extend guard for batch action guard resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveBatchActionGuard` token |
| W64-04 | P1 | Re-run verify gates after batch action guard extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with batch action guard extraction |
| W65-01 | P1 | Extract batch assign guard resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchRuntime.ts` | DONE | batch assign precheck moved out of ActionView |
| W65-02 | P1 | Wire ActionView batch assign precheck to runtime resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveBatchAssignGuard` |
| W65-03 | P1 | Extend guard for batch assign guard resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveBatchAssignGuard` token |
| W65-04 | P1 | Re-run verify gates after batch assign guard extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with batch assign guard extraction |
| W66-01 | P1 | Extract batch update request builder | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchRuntime.ts` | DONE | batchUpdateRecords request payload construction moved out of ActionView |
| W66-02 | P1 | Wire ActionView batch updates to request builder | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `buildBatchUpdateRequest` |
| W66-03 | P1 | Extend guard for batch request builder adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `buildBatchUpdateRequest` token |
| W66-04 | P1 | Re-run verify gates after batch request builder extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with batch request builder extraction |
| W67-01 | P1 | Extract batch success message resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchRuntime.ts` | DONE | archive/activate/delete success message resolution moved out of ActionView |
| W67-02 | P1 | Wire ActionView batch success path to runtime resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveBatchActionResultMessage` |
| W67-03 | P1 | Extend guard for batch success resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveBatchActionResultMessage` token |
| W67-04 | P1 | Re-run verify gates after batch success resolver extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with batch success resolver extraction |
| W68-01 | P1 | Extract batch failure/assign message resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchRuntime.ts` | DONE | batch failure and assign result message resolver moved out of ActionView |
| W68-02 | P1 | Wire ActionView failure/assign messages to runtime resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveBatchActionFailureMessage` |
| W68-03 | P1 | Extend guard for failure/assign resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveBatchActionFailureMessage` token |
| W68-04 | P1 | Re-run verify gates after failure/assign resolver extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with failure/assign resolver extraction |
| W69-01 | P1 | Extract assignee options mapper runtime | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewAssigneeExportRuntime.ts` | DONE | assignee candidate normalization moved out of ActionView |
| W69-02 | P1 | Wire ActionView assignee options mapping to runtime | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveAssigneeOptions` |
| W69-03 | P1 | Extend guard for assignee options mapper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveAssigneeOptions` token |
| W69-04 | P1 | Re-run verify gates after assignee options extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with assignee options extraction |
| W70-01 | P1 | Extract assignee selected-id reconcile runtime | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewAssigneeExportRuntime.ts` | DONE | selected assignee reconciliation moved out of ActionView |
| W70-02 | P1 | Wire ActionView selected assignee reconcile to runtime | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `reconcileSelectedAssigneeId` |
| W70-03 | P1 | Extend guard for selected assignee reconcile adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `reconcileSelectedAssigneeId` token |
| W70-04 | P1 | Re-run verify gates after selected assignee reconcile extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with selected assignee reconcile extraction |
| W71-01 | P1 | Extract assignee permission warning resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewAssigneeExportRuntime.ts` | DONE | permission-denied warning payload resolver moved out of ActionView |
| W71-02 | P1 | Wire ActionView assignee warning to runtime resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveAssigneePermissionWarning` |
| W71-03 | P1 | Extend guard for assignee warning resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveAssigneePermissionWarning` token |
| W71-04 | P1 | Re-run verify gates after assignee warning extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with assignee warning extraction |
| W72-01 | P1 | Extract export guard resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewAssigneeExportRuntime.ts` | DONE | export precheck (model/selection) moved out of ActionView |
| W72-02 | P1 | Wire ActionView export precheck to runtime resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveExportGuard` |
| W72-03 | P1 | Extend guard for export guard resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveExportGuard` token |
| W72-04 | P1 | Re-run verify gates after export guard extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with export guard extraction |
| W73-01 | P1 | Extract export request builder runtime | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewAssigneeExportRuntime.ts` | DONE | export request payload construction moved out of ActionView |
| W73-02 | P1 | Wire ActionView export request to runtime builder | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `buildExportRequest` |
| W73-03 | P1 | Extend guard for export request builder adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `buildExportRequest` token |
| W73-04 | P1 | Re-run verify gates after export request extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with export request extraction |
| W74-01 | P1 | Extract load UI reset state builder | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadResetRuntime.ts` | DONE | load UI reset defaults moved out of ActionView |
| W74-02 | P1 | Wire ActionView load UI reset to runtime apply helper | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `applyActionViewLoadResetState` for UI reset |
| W74-03 | P1 | Extend guard for load reset apply helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `applyActionViewLoadResetState` token |
| W74-04 | P1 | Re-run verify gates after load UI reset extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with load UI reset extraction |
| W75-01 | P1 | Extract load contract reset state builder | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadResetRuntime.ts` | DONE | load contract reset defaults moved out of ActionView |
| W75-02 | P1 | Wire ActionView load contract reset to runtime apply helper | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView reset flow delegated through runtime apply helper |
| W75-03 | P1 | Extend guard for load contract reset adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard continues enforcing runtime apply token |
| W75-04 | P1 | Re-run verify gates after load contract reset extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with load contract reset extraction |
| W76-01 | P1 | Extract load data reset state builder | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadResetRuntime.ts` | DONE | records/groupedRows/groupSummary reset defaults moved out of ActionView |
| W76-02 | P1 | Wire ActionView load data reset to runtime apply helper | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView data reset flow delegated through runtime apply helper |
| W76-03 | P1 | Extend guard for load data reset adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard continues enforcing runtime apply token |
| W76-04 | P1 | Re-run verify gates after load data reset extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with load data reset extraction |
| W77-01 | P1 | Extract load group-window reset state builder | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadResetRuntime.ts` | DONE | group window reset defaults moved out of ActionView |
| W77-02 | P1 | Wire ActionView group-window reset to runtime apply helper | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView group-window reset delegated through runtime apply helper |
| W77-03 | P1 | Extend guard for load group-window reset adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard continues enforcing runtime apply token |
| W77-04 | P1 | Re-run verify gates after load group-window reset extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with load group-window reset extraction |
| W78-01 | P1 | Extract load view-field reset state builder | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadResetRuntime.ts` | DONE | view field reset defaults moved out of ActionView |
| W78-02 | P1 | Wire ActionView view-field reset to runtime apply helper | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView view-field reset delegated through runtime apply helper |
| W78-03 | P1 | Extend guard for load view-field reset adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard continues enforcing runtime apply token |
| W78-04 | P1 | Re-run verify gates after load view-field reset extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with load view-field reset extraction |
| W79-01 | P1 | Extract batch failure preview rows resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchArtifactsRuntime.ts` | DONE | failure preview rows extraction moved out of ActionView |
| W79-02 | P1 | Wire ActionView failure preview handling to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveBatchFailurePreviewRows` |
| W79-03 | P1 | Extend guard for failure preview resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveBatchFailurePreviewRows` token |
| W79-04 | P1 | Re-run verify gates after failure preview extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with failure preview extraction |
| W80-01 | P1 | Extract batch failure paging state resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchArtifactsRuntime.ts` | DONE | failure offset/limit/has-more derivation moved out of ActionView |
| W80-02 | P1 | Wire ActionView failure paging state to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveBatchFailurePagingState` |
| W80-03 | P1 | Extend guard for failure paging resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveBatchFailurePagingState` token |
| W80-04 | P1 | Re-run verify gates after failure paging extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with failure paging extraction |
| W81-01 | P1 | Extract batch failure CSV artifact resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchArtifactsRuntime.ts` | DONE | failed csv artifact merge strategy moved out of ActionView |
| W81-02 | P1 | Wire ActionView failure CSV handling to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveBatchFailureCsvState` |
| W81-03 | P1 | Extend guard for failure CSV resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveBatchFailureCsvState` token |
| W81-04 | P1 | Re-run verify gates after failure CSV extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with failure CSV extraction |
| W82-01 | P1 | Extract load-more failures guard resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchArtifactsRuntime.ts` | DONE | load-more guard precheck moved out of ActionView |
| W82-02 | P1 | Wire ActionView load-more guard to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveLoadMoreFailuresGuard` |
| W82-03 | P1 | Extend guard for load-more guard resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveLoadMoreFailuresGuard` token |
| W82-04 | P1 | Re-run verify gates after load-more guard extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with load-more guard extraction |
| W83-01 | P1 | Extract load-more failures request builder | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchArtifactsRuntime.ts` | DONE | load-more retry request payload builder moved out of ActionView |
| W83-02 | P1 | Wire ActionView load-more API call to request builder | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `buildLoadMoreFailuresRequest` |
| W83-03 | P1 | Extend guard for load-more request builder adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `buildLoadMoreFailuresRequest` token |
| W83-04 | P1 | Re-run verify gates after load-more request extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with load-more request extraction |
| W84-01 | P1 | Extract batch failure detail-line mapper | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchArtifactsRuntime.ts` | DONE | failure preview to detail-line mapping moved out of ActionView |
| W84-02 | P1 | Wire ActionView failure-line mapping to runtime mapper | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `mapBatchFailureDetailLines` |
| W84-03 | P1 | Extend guard for failure-line mapper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `mapBatchFailureDetailLines` token |
| W84-04 | P1 | Re-run verify gates after failure-line mapper extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with failure-line mapper extraction |
| W85-01 | P1 | Extract batch failure detail merge resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchArtifactsRuntime.ts` | DONE | append/replace merge policy moved out of ActionView |
| W85-02 | P1 | Wire ActionView detail merge path to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveBatchDetailLinesMerge` |
| W85-03 | P1 | Extend guard for detail merge resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveBatchDetailLinesMerge` token |
| W85-04 | P1 | Re-run verify gates after detail merge extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with detail merge extraction |
| W86-01 | P1 | Extract batch artifacts reset-state resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchArtifactsRuntime.ts` | DONE | batch message/details/csv/failure reset state moved out of ActionView |
| W86-02 | P1 | Wire ActionView batch-action reset to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveBatchArtifactsReset` for batch-action entry |
| W86-03 | P1 | Extend guard for reset-state resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveBatchArtifactsReset` token |
| W86-04 | P1 | Re-run verify gates after reset-state extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with reset-state extraction |
| W87-01 | P1 | Wire batch-assign reset flow to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | batch-assign entry reset delegated to `resolveBatchArtifactsReset` |
| W87-02 | P1 | Wire export reset flow to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | export entry reset delegated to `resolveBatchArtifactsReset` |
| W87-03 | P1 | Keep guard enforcing unified reset resolver usage | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard continues requiring reset resolver token |
| W87-04 | P1 | Re-run verify gates after assign/export reset wiring | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with reset wiring |
| W88-01 | P1 | Extract batch failure retry-tag resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchArtifactsRuntime.ts` | DONE | retryable/non-retryable tag mapping moved out of ActionView |
| W88-02 | P1 | Compose failure-line mapper through retry-tag resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchArtifactsRuntime.ts` | DONE | detail-line mapper internally reuses retry-tag resolver |
| W88-03 | P1 | Keep guard enforcing batch-artifact resolver cluster | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard continues requiring batch artifact resolver tokens |
| W88-04 | P1 | Re-run verify gates after retry-tag resolver extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with retry-tag resolver extraction |
| W89-01 | P1 | Extract batch error-line builder runtime helper | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchRuntime.ts` | DONE | error context aggregation and error-line rendering moved out of ActionView |
| W89-02 | P1 | Extract batch action error-label resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchRuntime.ts` | DONE | action→error label mapping moved out of ActionView |
| W89-03 | P1 | Wire ActionView batch-action catch to runtime error helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveBatchActionErrorLabel` + `buildBatchErrorLine` |
| W89-04 | P1 | Extend guard for batch error helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires batch error helper tokens |
| W89-05 | P1 | Re-run verify gates after batch error helper extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with batch error helper extraction |
| W90-01 | P1 | Wire ActionView batch-assign catch to runtime error helper | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | batch-assign failure line delegated to `buildBatchErrorLine` |
| W90-02 | P1 | Wire ActionView export catch to runtime error helper | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | export failure line delegated to `buildBatchErrorLine` |
| W90-03 | P1 | Wire ActionView load-more catch to runtime error helper | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | load-more failure line delegated to `buildBatchErrorLine` |
| W90-04 | P1 | Keep guard enforcing catch-path runtime helper usage | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard continues requiring `buildBatchErrorLine` token |
| W90-05 | P1 | Re-run verify gates after catch-path wiring | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with catch-path wiring |
| W91-01 | P1 | Move batch error-context dependency into runtime module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchRuntime.ts` | DONE | runtime imports `collectErrorContextIssue`/`issueScopeLabel` and encapsulates usage |
| W91-02 | P1 | Remove page-level batch error-context import | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView no longer imports `errorContext` for batch errors |
| W91-03 | P1 | Keep guard enforcing runtime-side batch error handling | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires runtime batch error helper tokens |
| W91-04 | P1 | Re-run verify gates after error-context dependency move | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after dependency move |
| W91-05 | P1 | Document W89-W91 completion in checklist | Governance Layer | `docs/ops/codex_friendly_execution_checklist_frontend_contract_strict_wave_v1.md` | DONE | W89-W91 rows added and marked DONE |
| W92-01 | P1 | Consolidate catch hint resolution through runtime helper callback | Runtime Execution Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | catch paths pass unified `resolveHint` callback into `buildBatchErrorLine` |
| W92-02 | P1 | Keep guard enforcing unified catch callback pattern | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard continues requiring `buildBatchErrorLine` usage |
| W92-03 | P1 | Re-run verify gates after callback unification | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with callback unification |
| W92-04 | P1 | Document W92 completion in checklist | Governance Layer | `docs/ops/codex_friendly_execution_checklist_frontend_contract_strict_wave_v1.md` | DONE | W92 rows added and marked DONE |
| W92-05 | P1 | Preserve strict contract behavior with unchanged semantics | Contract Consumption Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | error display semantics unchanged while runtime ownership moved |
| W93-01 | P1 | Verify batch error runtime extraction with scene specialcase guard | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | specialcase guard passes after W89-W92 |
| W93-02 | P1 | Verify full scene delivery readiness after extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | delivery readiness passes after W89-W92 |
| W93-03 | P1 | Archive verification artifacts for traceability | Governance Layer | `artifacts/backend/*` + `docs/ops/audit/*` | DONE | fresh verify artifacts generated by make targets |
| W93-04 | P1 | Keep batch error helper tokens as required guard baseline | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | regression guard now enforces new runtime helper usage |
| W93-05 | P1 | Document W93 closure in checklist | Governance Layer | `docs/ops/codex_friendly_execution_checklist_frontend_contract_strict_wave_v1.md` | DONE | W93 rows added and marked DONE |
| W94-01 | P1 | Extract load missing-action error-state resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadErrorRuntime.ts` | DONE | missing action-id early exit state moved out of ActionView |
| W94-02 | P1 | Wire ActionView missing-action path to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveLoadMissingActionIdErrorState` |
| W94-03 | P1 | Extend guard for missing-action resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveLoadMissingActionIdErrorState` token |
| W94-04 | P1 | Re-run verify gates after missing-action extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with missing-action extraction |
| W95-01 | P1 | Extract load missing-view-type error-state resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadErrorRuntime.ts` | DONE | missing contract view_type early exit state moved out of ActionView |
| W95-02 | P1 | Wire ActionView missing-view-type path to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveLoadMissingContractViewTypeErrorState` |
| W95-03 | P1 | Extend guard for missing-view-type resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveLoadMissingContractViewTypeErrorState` token |
| W95-04 | P1 | Re-run verify gates after missing-view-type extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with missing-view-type extraction |
| W96-01 | P1 | Extract load missing-tree-columns guard resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadErrorRuntime.ts` | DONE | list/tree contract columns missing guard moved out of ActionView |
| W96-02 | P1 | Wire ActionView tree-columns guard to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveLoadMissingTreeColumnsErrorState` |
| W96-03 | P1 | Extend guard for missing-tree-columns resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveLoadMissingTreeColumnsErrorState` token |
| W96-04 | P1 | Re-run verify gates after tree-columns guard extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with tree-columns guard extraction |
| W97-01 | P1 | Extract load trace-id resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadErrorRuntime.ts` | DONE | response trace-id selection moved out of ActionView |
| W97-02 | P1 | Wire ActionView trace assignment to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveLoadTraceIdentity` |
| W97-03 | P1 | Extend guard for load trace resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveLoadTraceIdentity` token |
| W97-04 | P1 | Re-run verify gates after trace resolver extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with trace resolver extraction |
| W98-01 | P1 | Extract load catch-state resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadErrorRuntime.ts` | DONE | load catch fallback state projection moved out of ActionView |
| W98-02 | P1 | Wire ActionView catch branch to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveLoadCatchState` |
| W98-03 | P1 | Extend guard for load catch resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveLoadCatchState` token |
| W98-04 | P1 | Re-run verify gates after load catch extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with load catch extraction |
| W99-01 | P1 | Extract load success project-scope resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadSuccessRuntime.ts` | DONE | project scope success-state projection moved out of ActionView |
| W99-02 | P1 | Wire ActionView project-scope assignment to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveLoadSuccessProjectScopeState` |
| W99-03 | P1 | Extend guard for project-scope success resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveLoadSuccessProjectScopeState` token |
| W99-04 | P1 | Re-run verify gates after project-scope success extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with project-scope success extraction |
| W100-01 | P1 | Extract load success group-window resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadSuccessRuntime.ts` | DONE | group-window success-state projection moved out of ActionView |
| W100-02 | P1 | Wire ActionView group-window assignment to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveLoadSuccessWindowState` |
| W100-03 | P1 | Extend guard for group-window success resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveLoadSuccessWindowState` token |
| W100-04 | P1 | Re-run verify gates after group-window success extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with group-window success extraction |
| W101-01 | P1 | Extract load success status-input resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadSuccessRuntime.ts` | DONE | success status input mapping moved out of ActionView |
| W101-02 | P1 | Wire ActionView success status derivation to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveLoadSuccessStatusInput` |
| W101-03 | P1 | Extend guard for success status resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveLoadSuccessStatusInput` token |
| W101-04 | P1 | Re-run verify gates after success status extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with success status extraction |
| W102-01 | P1 | Extract load success trace-state resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadSuccessRuntime.ts` | DONE | trace state assignment policy moved out of ActionView |
| W102-02 | P1 | Wire ActionView trace assignment to success resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveLoadSuccessTraceState` |
| W102-03 | P1 | Extend guard for success trace resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveLoadSuccessTraceState` token |
| W102-04 | P1 | Re-run verify gates after success trace extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with success trace extraction |
| W103-01 | P1 | Extract load success latency resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadSuccessRuntime.ts` | DONE | success latency calculation moved out of ActionView |
| W103-02 | P1 | Wire ActionView success latency assignment to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveLoadSuccessLatencyMs` |
| W103-03 | P1 | Extend guard for success latency resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveLoadSuccessLatencyMs` token |
| W103-04 | P1 | Re-run verify gates after success latency extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with success latency extraction |
| W104-01 | P1 | Extract assignee-options load guard resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewAssigneeExportRuntime.ts` | DONE | assignee field precheck and reset defaults moved out of ActionView |
| W104-02 | P1 | Wire ActionView assignee load precheck to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveAssigneeOptionsLoadGuard` |
| W104-03 | P1 | Extend guard for assignee load guard adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveAssigneeOptionsLoadGuard` token |
| W104-04 | P1 | Re-run verify gates after assignee load guard extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with assignee load guard extraction |
| W105-01 | P1 | Extract assignee permission warning message resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewAssigneeExportRuntime.ts` | DONE | assignee permission warning message assembly moved out of ActionView |
| W105-02 | P1 | Wire ActionView permission warning message to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveAssigneePermissionWarningMessage` |
| W105-03 | P1 | Extend guard for assignee warning message resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveAssigneePermissionWarningMessage` token |
| W105-04 | P1 | Re-run verify gates after assignee warning message extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with assignee warning message extraction |
| W106-01 | P1 | Extract batch-action guard message resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchRuntime.ts` | DONE | batch action guard reason→message mapping moved out of ActionView |
| W106-02 | P1 | Wire ActionView batch-action guard message to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveBatchActionGuardMessage` |
| W106-03 | P1 | Extend guard for batch-action guard message resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveBatchActionGuardMessage` token |
| W106-04 | P1 | Re-run verify gates after batch-action guard message extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with batch-action guard message extraction |
| W107-01 | P1 | Extract batch-assign guard message resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchRuntime.ts` | DONE | batch assign guard reason→message mapping moved out of ActionView |
| W107-02 | P1 | Wire ActionView batch-assign guard message to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveBatchAssignGuardMessage` |
| W107-03 | P1 | Extend guard for batch-assign guard message resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveBatchAssignGuardMessage` token |
| W107-04 | P1 | Re-run verify gates after batch-assign guard message extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with batch-assign guard message extraction |
| W108-01 | P1 | Extract export guard message resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewAssigneeExportRuntime.ts` | DONE | export guard reason→message mapping moved out of ActionView |
| W108-02 | P1 | Wire ActionView export guard message to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveExportGuardMessage` |
| W108-03 | P1 | Extend guard for export guard message resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveExportGuardMessage` token |
| W108-04 | P1 | Re-run verify gates after export guard message extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with export guard message extraction |
| W109-01 | P1 | Extract row-click route target resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewInteractionRuntime.ts` | DONE | row click target model/id/query routing decision moved out of ActionView |
| W109-02 | P1 | Wire ActionView row-click navigation to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `buildActionViewRowClickTarget` |
| W109-03 | P1 | Extend guard for row-click resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `buildActionViewRowClickTarget` token |
| W109-04 | P1 | Re-run verify gates after row-click resolver extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with row-click resolver extraction |
| W110-01 | P1 | Extract list-control transition resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewInteractionRuntime.ts` | DONE | search/sort/filter transition reset policy moved out of ActionView |
| W110-02 | P1 | Wire ActionView search/sort/filter handlers to transition resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveListControlTransition` |
| W110-03 | P1 | Extend guard for list-control resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveListControlTransition` token |
| W110-04 | P1 | Re-run verify gates after list-control resolver extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with list-control resolver extraction |
| W111-01 | P1 | Extract single selection toggle resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewInteractionRuntime.ts` | DONE | selection set add/remove decision moved out of ActionView |
| W111-02 | P1 | Wire ActionView single selection handler to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveSelectionAfterToggle` |
| W111-03 | P1 | Extend guard for single selection resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveSelectionAfterToggle` token |
| W111-04 | P1 | Re-run verify gates after single selection extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with single selection extraction |
| W112-01 | P1 | Extract bulk selection toggle resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewInteractionRuntime.ts` | DONE | bulk selection set merge/remove decision moved out of ActionView |
| W112-02 | P1 | Wire ActionView bulk selection handler to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveSelectionAfterToggleAll` |
| W112-03 | P1 | Extend guard for bulk selection resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires `resolveSelectionAfterToggleAll` token |
| W112-04 | P1 | Re-run verify gates after bulk selection extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with bulk selection extraction |
| W113-01 | P1 | Keep interaction runtime resolver cluster centralized | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewInteractionRuntime.ts` | DONE | row-click/list-control/selection helpers co-located for reuse |
| W113-02 | P1 | Keep ActionView interaction handlers as thin orchestration | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | handlers now delegate interaction decisions to runtime helpers |
| W113-03 | P1 | Keep guard enforcing interaction runtime helper tokens | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | regression guard now enforces interaction resolver usage |
| W113-04 | P1 | Re-run verify gates after interaction runtime consolidation | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with interaction runtime consolidation |
| W114-01 | P1 | Extract contract-action missing-open-target message resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewContractActionRuntime.ts` | DONE | open action missing target message moved out of ActionView |
| W114-02 | P1 | Extract contract-action record-context-required message resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewContractActionRuntime.ts` | DONE | record context required message moved out of ActionView |
| W114-03 | P1 | Wire ActionView open/mutation early returns to message resolvers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses contract-action message resolvers for early exits |
| W114-04 | P1 | Extend guard for contract-action message resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires new contract-action message resolver tokens |
| W114-05 | P1 | Re-run verify gates after contract-action message extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with message resolver extraction |
| W115-01 | P1 | Extract contract-action missing-model message resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewContractActionRuntime.ts` | DONE | missing model message moved out of ActionView |
| W115-02 | P1 | Wire ActionView missing-model branch to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveContractActionMissingModelMessage` |
| W115-03 | P1 | Extend guard for missing-model resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires missing-model resolver token |
| W115-04 | P1 | Re-run verify gates after missing-model extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with missing-model extraction |
| W116-01 | P1 | Extract contract-action done-message resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewContractActionRuntime.ts` | DONE | contract action success/failure aggregate message moved out of ActionView |
| W116-02 | P1 | Wire ActionView mutation/object done messaging to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveContractActionDoneMessage` |
| W116-03 | P1 | Extend guard for done-message resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires done-message resolver token |
| W116-04 | P1 | Re-run verify gates after done-message extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with done-message extraction |
| W117-01 | P1 | Extract contract-action route-target builder | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewContractActionRuntime.ts` | DONE | next action route target assembly moved out of ActionView |
| W117-02 | P1 | Wire ActionView open/execute navigation to route-target builder | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `buildContractActionRouteTarget` |
| W117-03 | P1 | Extend guard for route-target builder adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires route-target builder token |
| W117-04 | P1 | Re-run verify gates after route-target builder extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with route-target extraction |
| W118-01 | P1 | Consolidate contract-action runtime helper cluster | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewContractActionRuntime.ts` | DONE | open/select/exec/message/route helpers centralized |
| W118-02 | P1 | Keep ActionView contract-action flow as thin orchestrator | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | runContractAction now delegates message and routing decisions |
| W118-03 | P1 | Keep guard enforcing contract-action helper cluster | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | regression guard enforces contract-action helper usage |
| W118-04 | P1 | Re-run verify gates after contract-action consolidation | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with contract-action consolidation |
| W119-01 | P1 | Extract contract-action selection-block message resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewContractActionRuntime.ts` | DONE | selection requirement message mapping moved out of ActionView |
| W119-02 | P1 | Wire ActionView selection block to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveContractActionSelectionBlockMessage` |
| W119-03 | P1 | Extend guard for selection-block resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires selection-block resolver token |
| W119-04 | P1 | Re-run verify gates after selection-block extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with selection-block extraction |
| W120-01 | P1 | Extract contract-action response action-id resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewContractActionRuntime.ts` | DONE | executeButton response action_id parsing moved out of ActionView |
| W120-02 | P1 | Extract contract-action navigation predicate resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewContractActionRuntime.ts` | DONE | action-id navigation guard moved out of ActionView |
| W120-03 | P1 | Wire ActionView execute response branch to resolvers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveContractActionResponseActionId` + `shouldNavigateContractAction` |
| W120-04 | P1 | Re-run verify gates after execute response extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with execute response extraction |
| W121-01 | P1 | Extract contract-action counters resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewContractActionRuntime.ts` | DONE | success/failure counter updates moved out of ActionView |
| W121-02 | P1 | Wire ActionView mutation/object loops to counters resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveContractActionCounters` in both loops |
| W121-03 | P1 | Extend guard for counters resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires counters resolver token |
| W121-04 | P1 | Re-run verify gates after counters extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with counters extraction |
| W122-01 | P1 | Keep contract-action response and counter helpers centralized | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewContractActionRuntime.ts` | DONE | response parse/navigation/counter helpers co-located |
| W122-02 | P1 | Keep runContractAction as thin orchestration over runtime helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | runContractAction delegates selection/response/counter decisions |
| W122-03 | P1 | Keep guard enforcing new contract-action helper cluster | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | regression guard enforces helper usage |
| W122-04 | P1 | Re-run verify gates after helper cluster consolidation | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with helper consolidation |
| W123-01 | P1 | Validate no functional regression for contract-action flows | Runtime Verification Layer | `make verify.frontend.actionview.scene_specialcase.guard` | DONE | specialcase guard stays green after W119-W122 |
| W123-02 | P1 | Validate scene delivery readiness after extraction batch | Runtime Verification Layer | `make verify.scene.delivery.readiness` | DONE | delivery readiness remains green after W119-W122 |
| W123-03 | P1 | Persist updated audit artifacts for traceability | Governance Layer | `artifacts/backend/*` + `docs/ops/audit/*` | DONE | latest verification artifacts generated |
| W123-04 | P1 | Document W119-W123 closure in checklist | Governance Layer | `docs/ops/codex_friendly_execution_checklist_frontend_contract_strict_wave_v1.md` | DONE | W119-W123 rows added and marked DONE |
| W124-01 | P1 | Extract assignee-load success state resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewAssigneeExportRuntime.ts` | DONE | assignee load success state reconciliation moved out of ActionView |
| W124-02 | P1 | Extract assignee-load failure state resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewAssigneeExportRuntime.ts` | DONE | assignee load failure fallback state moved out of ActionView |
| W124-03 | P1 | Wire ActionView assignee load success/failure paths to resolvers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveAssigneeLoadSuccessState` and `resolveAssigneeLoadFailureState` |
| W124-04 | P1 | Extend guard for assignee load state resolvers adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires assignee load state resolver tokens |
| W124-05 | P1 | Re-run verify gates after assignee load state extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with assignee load state extraction |
| W125-01 | P1 | Extract export no-content message resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewAssigneeExportRuntime.ts` | DONE | export empty-result message moved out of ActionView |
| W125-02 | P1 | Extract export done-message resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewAssigneeExportRuntime.ts` | DONE | export success message assembly moved out of ActionView |
| W125-03 | P1 | Extract export failed-message resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewAssigneeExportRuntime.ts` | DONE | export failure message moved out of ActionView |
| W125-04 | P1 | Wire ActionView export message branches to resolvers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses export message resolvers for no-content/success/failure |
| W125-05 | P1 | Re-run verify gates after export message extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with export message extraction |
| W126-01 | P1 | Remove page-level assignee selected-id reconcile dependency | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView no longer imports `reconcileSelectedAssigneeId` directly |
| W126-02 | P1 | Keep assignee selected-id reconciliation inside runtime resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewAssigneeExportRuntime.ts` | DONE | selected-id reconcile wrapped by `resolveAssigneeLoadSuccessState` |
| W126-03 | P1 | Extend guard baseline from old reconcile token to new state tokens | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard now enforces new assignee state helper tokens |
| W126-04 | P1 | Re-run verify gates after assignee reconcile ownership shift | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after ownership shift |
| W127-01 | P1 | Consolidate export message resolver cluster in runtime module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewAssigneeExportRuntime.ts` | DONE | guard/export/no-content/success/failure messages centralized |
| W127-02 | P1 | Keep ActionView export flow as thin orchestration | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | export flow now delegates message selection to runtime helpers |
| W127-03 | P1 | Keep guard enforcing export message resolver cluster | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires new export message resolver tokens |
| W127-04 | P1 | Re-run verify gates after export resolver consolidation | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with export resolver consolidation |
| W128-01 | P1 | Validate ActionView specialcase guard after W124-W127 | Runtime Verification Layer | `make verify.frontend.actionview.scene_specialcase.guard` | DONE | specialcase guard remains green after extraction batch |
| W128-02 | P1 | Validate scene delivery readiness after W124-W127 | Runtime Verification Layer | `make verify.scene.delivery.readiness` | DONE | delivery readiness remains green after extraction batch |
| W128-03 | P1 | Persist verification artifacts for W124-W128 | Governance Layer | `artifacts/backend/*` + `docs/ops/audit/*` | DONE | fresh artifacts generated by verify targets |
| W128-04 | P1 | Document W124-W128 closure in checklist | Governance Layer | `docs/ops/codex_friendly_execution_checklist_frontend_contract_strict_wave_v1.md` | DONE | W124-W128 rows added and marked DONE |
| W129-01 | P1 | Extract route preset search-term resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRoutePresetRuntime.ts` | DONE | route search/preset/group-value precedence moved out of ActionView |
| W129-02 | P1 | Extract route preset label resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRoutePresetRuntime.ts` | DONE | applied preset label decision moved out of ActionView |
| W129-03 | P1 | Wire ActionView route preset search/label to resolvers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveRoutePresetSearchTerm` + `resolveRoutePresetAppliedLabel` |
| W129-04 | P1 | Extend guard for route preset search/label resolvers | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires route preset search/label resolver tokens |
| W129-05 | P1 | Re-run verify gates after route preset search/label extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after route preset search/label extraction |
| W130-01 | P1 | Extract route preset group-window state resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRoutePresetRuntime.ts` | DONE | groupBy/offset/fingerprint/window identity mapping moved out of ActionView |
| W130-02 | P1 | Wire ActionView group-window preset state to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveRoutePresetGroupWindowState` |
| W130-03 | P1 | Extend guard for group-window preset resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires group-window preset resolver token |
| W130-04 | P1 | Re-run verify gates after group-window preset extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after group-window preset extraction |
| W131-01 | P1 | Extract route preset group visual-state resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRoutePresetRuntime.ts` | DONE | sample-limit/sort/collapsed parsing moved out of ActionView |
| W131-02 | P1 | Wire ActionView group visual preset state to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveRoutePresetGroupVisualState` |
| W131-03 | P1 | Extend guard for group visual preset resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires group visual preset resolver token |
| W131-04 | P1 | Re-run verify gates after group visual preset extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after group visual preset extraction |
| W132-01 | P1 | Extract route preset tracking-state resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRoutePresetRuntime.ts` | DONE | preset tracking apply/reset decision moved out of ActionView |
| W132-02 | P1 | Wire ActionView preset tracking to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveRoutePresetTrackingState` |
| W132-03 | P1 | Extend guard for preset tracking resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires preset tracking resolver token |
| W132-04 | P1 | Re-run verify gates after preset tracking extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after preset tracking extraction |
| W133-01 | P1 | Consolidate route preset resolver cluster | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRoutePresetRuntime.ts` | DONE | route preset search/label/window/visual/tracking helpers centralized |
| W133-02 | P1 | Keep applyRoutePreset as thin orchestration over runtime helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | applyRoutePreset now delegates branch decisions to runtime helpers |
| W133-03 | P1 | Keep guard enforcing route preset helper cluster | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | regression guard enforces route preset helper usage |
| W133-04 | P1 | Re-run verify gates after route preset consolidation | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after route preset consolidation |
| W134-01 | P1 | Extract route preset saved-filter value resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRoutePresetRuntime.ts` | DONE | saved filter route value normalization moved out of ActionView |
| W134-02 | P1 | Extract route preset active-filter value resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRoutePresetRuntime.ts` | DONE | active filter route value normalization moved out of ActionView |
| W134-03 | P1 | Wire ActionView saved/active filter preset mapping to resolvers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveRoutePresetSavedFilterValue` + `resolveRoutePresetActiveFilterValue` |
| W134-04 | P1 | Extend guard for route preset filter-value resolvers adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires route preset filter-value resolver tokens |
| W134-05 | P1 | Re-run verify gates after route preset filter-value extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after route preset filter-value extraction |
| W135-01 | P1 | Extract route preset group-summary reset resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRoutePresetRuntime.ts` | DONE | group summary reset decision moved out of ActionView |
| W135-02 | P1 | Wire ActionView group-summary reset to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveRoutePresetGroupSummaryResetState` |
| W135-03 | P1 | Extend guard for group-summary reset resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires group-summary reset resolver token |
| W135-04 | P1 | Re-run verify gates after group-summary reset extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after group-summary reset extraction |
| W136-01 | P1 | Extract route preset group-page change detector | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRoutePresetRuntime.ts` | DONE | parsed/current group page state diff detection moved out of ActionView |
| W136-02 | P1 | Extract route preset group-page next-state resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRoutePresetRuntime.ts` | DONE | next group page state resolution moved out of ActionView |
| W136-03 | P1 | Wire ActionView group-page state patch to resolvers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `hasRoutePresetGroupPageStateChanged` + `resolveRoutePresetGroupPageState` |
| W136-04 | P1 | Re-run verify gates after group-page resolver extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after group-page resolver extraction |
| W137-01 | P1 | Consolidate route preset filter/group-page helper cluster | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRoutePresetRuntime.ts` | DONE | preset filter/group-summary/group-page helpers centralized |
| W137-02 | P1 | Keep applyRoutePreset branching thin after resolver adoption | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | applyRoutePreset delegates remaining filter/group-page decisions |
| W137-03 | P1 | Keep guard enforcing route preset extended helper cluster | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard enforces new route preset helper tokens |
| W137-04 | P1 | Re-run verify gates after route preset extended consolidation | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after extended consolidation |
| W138-01 | P1 | Validate ActionView specialcase guard after W134-W137 | Runtime Verification Layer | `make verify.frontend.actionview.scene_specialcase.guard` | DONE | specialcase guard remains green after extraction batch |
| W138-02 | P1 | Validate scene delivery readiness after W134-W137 | Runtime Verification Layer | `make verify.scene.delivery.readiness` | DONE | delivery readiness remains green after extraction batch |
| W138-03 | P1 | Persist verification artifacts for W134-W138 | Governance Layer | `artifacts/backend/*` + `docs/ops/audit/*` | DONE | fresh artifacts generated by verify targets |
| W138-04 | P1 | Document W134-W138 closure in checklist | Governance Layer | `docs/ops/codex_friendly_execution_checklist_frontend_contract_strict_wave_v1.md` | DONE | W134-W138 rows added and marked DONE |
| W139-01 | P1 | Extract non-empty control-key normalizer | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewFilterGroupRuntime.ts` | DONE | key/field guard normalization moved out of ActionView |
| W139-02 | P1 | Extract contract-filter apply-state resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewFilterGroupRuntime.ts` | DONE | contract filter apply state + route patch moved out of ActionView |
| W139-03 | P1 | Wire ActionView contract-filter apply flow to resolvers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveNonEmptyControlKey` + `resolveContractFilterApplyState` |
| W139-04 | P1 | Extend guard for contract-filter apply resolvers adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires non-empty key and contract-filter resolver tokens |
| W139-05 | P1 | Re-run verify gates after contract-filter apply extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after contract-filter apply extraction |
| W140-01 | P1 | Extract saved-filter apply-state resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewFilterGroupRuntime.ts` | DONE | saved filter apply state + route patch moved out of ActionView |
| W140-02 | P1 | Wire ActionView saved-filter apply flow to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveSavedFilterApplyState` |
| W140-03 | P1 | Extend guard for saved-filter apply resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires saved-filter resolver token |
| W140-04 | P1 | Re-run verify gates after saved-filter apply extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after saved-filter apply extraction |
| W141-01 | P1 | Extract group-by apply-state resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewFilterGroupRuntime.ts` | DONE | group-by apply reset/selection/patch state moved out of ActionView |
| W141-02 | P1 | Wire ActionView group-by apply flow to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveGroupByApplyState` |
| W141-03 | P1 | Extend guard for group-by apply resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires group-by apply resolver token |
| W141-04 | P1 | Re-run verify gates after group-by apply extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after group-by apply extraction |
| W142-01 | P1 | Extract group-by clear-state resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewFilterGroupRuntime.ts` | DONE | group-by clear reset/selection/patch state moved out of ActionView |
| W142-02 | P1 | Wire ActionView group-by clear flow to resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView uses `resolveGroupByClearState` |
| W142-03 | P1 | Extend guard for group-by clear resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires group-by clear resolver token |
| W142-04 | P1 | Re-run verify gates after group-by clear extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after group-by clear extraction |
| W143-01 | P1 | Consolidate filter/group apply helper cluster | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewFilterGroupRuntime.ts` | DONE | contract/saved/group apply+clear helpers centralized |
| W143-02 | P1 | Keep ActionView filter/group handlers as thin orchestration | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | handlers now delegate decision state to runtime helper cluster |
| W143-03 | P1 | Keep guard enforcing filter/group helper cluster | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | regression guard enforces filter/group helper tokens |
| W143-04 | P1 | Re-run verify gates after filter/group consolidation | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after filter/group consolidation |
| W144-01 | P1 | Extract contract-filter clear-state resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewFilterGroupRuntime.ts` | DONE | contract filter clear state + route patch moved out of ActionView |
| W144-02 | P1 | Extract saved-filter clear-state resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewFilterGroupRuntime.ts` | DONE | saved filter clear state + route patch moved out of ActionView |
| W144-03 | P1 | Wire ActionView clear filter handlers to clear-state resolvers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | clear handlers now delegate to filter clear-state resolvers |
| W144-04 | P1 | Extend guard for filter clear-state resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires contract/saved clear-state resolver tokens |
| W144-05 | P1 | Re-run verify gates after filter clear-state extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after filter clear-state extraction |
| W145-01 | P1 | Extract route-sync payload builder for list state | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRouteSyncStateRuntime.ts` | DONE | syncRouteListState payload composition moved out of ActionView |
| W145-02 | P1 | Extract route-sync extra normalizer | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRouteSyncStateRuntime.ts` | DONE | syncRouteListState extra payload normalization moved out of ActionView |
| W145-03 | P1 | Wire ActionView syncRouteListState to route-sync payload helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | syncRouteListState uses `buildActionViewRouteSyncStatePayload` + `resolveRouteSyncExtra` |
| W145-04 | P1 | Extend guard for route-sync payload helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires route-sync payload helper tokens |
| W145-05 | P1 | Re-run verify gates after route-sync payload extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after route-sync payload extraction |
| W146-01 | P1 | Extract route-sync load mode resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRouteSyncStateRuntime.ts` | DONE | reload vs await decision helper moved out of ActionView |
| W146-02 | P1 | Wire ActionView syncRouteStateAndReload to mode resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | syncRouteStateAndReload uses `resolveRouteSyncShouldAwaitLoad` |
| W146-03 | P1 | Wire ActionView restartLoadWithRouteSync to mode resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | restartLoadWithRouteSync uses `resolveRouteSyncShouldAwaitLoad` |
| W146-04 | P1 | Re-run verify gates after route-sync mode extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after route-sync mode extraction |
| W147-01 | P1 | Consolidate route-sync helper cluster | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRouteSyncStateRuntime.ts` | DONE | list sync payload/extra/mode helpers centralized |
| W147-02 | P1 | Keep route sync handlers as thin orchestration | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | route sync handlers now delegate payload/mode decisions |
| W147-03 | P1 | Keep guard enforcing route-sync helper cluster | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | regression guard enforces route-sync helper tokens |
| W147-04 | P1 | Re-run verify gates after route-sync consolidation | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after route-sync consolidation |
| W148-01 | P1 | Validate ActionView specialcase guard after W144-W147 | Runtime Verification Layer | `make verify.frontend.actionview.scene_specialcase.guard` | DONE | specialcase guard remains green after extraction batch |
| W148-02 | P1 | Validate scene delivery readiness after W144-W147 | Runtime Verification Layer | `make verify.scene.delivery.readiness` | DONE | delivery readiness remains green after extraction batch |
| W148-03 | P1 | Persist verification artifacts for W144-W148 | Governance Layer | `artifacts/backend/*` + `docs/ops/audit/*` | DONE | fresh artifacts generated by verify targets |
| W148-04 | P1 | Document W144-W148 closure in checklist | Governance Layer | `docs/ops/codex_friendly_execution_checklist_frontend_contract_strict_wave_v1.md` | DONE | W144-W148 rows added and marked DONE |
| W149-01 | P1 | Extract grouped-rows page-change guard resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRowsInteractionRuntime.ts` | DONE | grouped rows page-change early-return guard moved out of ActionView |
| W149-02 | P1 | Extract grouped-rows page domain resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRowsInteractionRuntime.ts` | DONE | grouped rows request domain normalization moved out of ActionView |
| W149-03 | P1 | Wire ActionView grouped page-change guard/domain to resolvers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | grouped page-change path uses guard + domain resolvers |
| W149-04 | P1 | Extend guard for grouped page-change guard/domain adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires grouped page-change guard/domain resolver tokens |
| W149-05 | P1 | Re-run verify gates after grouped page-change guard/domain extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after grouped page-change guard/domain extraction |
| W150-01 | P1 | Extract grouped-rows payload rows resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRowsInteractionRuntime.ts` | DONE | grouped rows payload record extraction moved out of ActionView |
| W150-02 | P1 | Extract grouped-rows page offset-state resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRowsInteractionRuntime.ts` | DONE | grouped page offset update + query serialization moved out of ActionView |
| W150-03 | P1 | Wire ActionView grouped page payload/offset handling to resolvers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | grouped page-change success branch uses payload + offset resolvers |
| W150-04 | P1 | Extend guard for grouped page payload/offset resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires grouped page payload/offset resolver tokens |
| W150-05 | P1 | Re-run verify gates after grouped page payload/offset extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after grouped page payload/offset extraction |
| W151-01 | P1 | Extract grouped-rows page-change failure-state resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRowsInteractionRuntime.ts` | DONE | grouped rows loading clear-on-failure moved out of ActionView |
| W151-02 | P1 | Wire ActionView grouped page-change catch branch to failure resolver | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | catch branch now delegates to `applyGroupedRowsPageChangeFailure` |
| W151-03 | P1 | Extend guard for grouped page failure resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires grouped page failure resolver token |
| W151-04 | P1 | Re-run verify gates after grouped page failure extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after grouped page failure extraction |
| W152-01 | P1 | Consolidate grouped page-change helper cluster | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRowsInteractionRuntime.ts` | DONE | guard/domain/payload/offset/failure helpers centralized |
| W152-02 | P1 | Keep handleGroupedRowsPageChange as thin orchestration | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | grouped page-change now delegates branch decisions to runtime helpers |
| W152-03 | P1 | Keep guard enforcing grouped page-change helper cluster | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | regression guard enforces grouped page-change helper tokens |
| W152-04 | P1 | Re-run verify gates after grouped page-change consolidation | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after grouped page-change consolidation |
| W153-01 | P1 | Validate ActionView specialcase guard after W149-W152 | Runtime Verification Layer | `make verify.frontend.actionview.scene_specialcase.guard` | DONE | specialcase guard remains green after extraction batch |
| W153-02 | P1 | Validate scene delivery readiness after W149-W152 | Runtime Verification Layer | `make verify.scene.delivery.readiness` | DONE | delivery readiness remains green after extraction batch |
| W153-03 | P1 | Persist verification artifacts for W149-W153 | Governance Layer | `artifacts/backend/*` + `docs/ops/audit/*` | DONE | fresh artifacts generated by verify targets |
| W153-04 | P1 | Document W149-W153 closure in checklist | Governance Layer | `docs/ops/codex_friendly_execution_checklist_frontend_contract_strict_wave_v1.md` | DONE | W149-W153 rows added and marked DONE |
| W154-01 | P1 | Extract grouped hydrate guard + keys resolvers | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRowsInteractionRuntime.ts` | DONE | hydrate guard and key-set generation moved out of ActionView |
| W154-02 | P1 | Extract grouped hydrate page-state resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRowsInteractionRuntime.ts` | DONE | hydrate limit/offset calculation moved out of ActionView |
| W154-03 | P1 | Extract grouped hydrate update success/failure resolvers | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRowsInteractionRuntime.ts` | DONE | hydrate update payload shaping moved out of ActionView |
| W154-04 | P1 | Wire ActionView hydrate flow to runtime resolvers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | hydrate flow now delegates guard/page/update shaping to runtime helpers |
| W154-05 | P1 | Extend guard for grouped hydrate resolver adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires grouped hydrate helper tokens |
| W155-01 | P1 | Extract grouped-route local state resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRouteStateRuntime.ts` | DONE | grouped route selection+local state merge moved out of ActionView |
| W155-02 | P1 | Extract grouped-route sync plan resolver | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewGroupedRouteStateRuntime.ts` | DONE | grouped route sync payload + sync decision moved out of ActionView |
| W155-03 | P1 | Wire ActionView normalizeGroupedRouteState to route runtime plans | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | normalize flow delegates local state + sync decision to runtime helpers |
| W155-04 | P1 | Extend guard for grouped-route runtime plan adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires grouped-route local/sync plan tokens |
| W155-05 | P1 | Re-run verify gates after grouped-route plan extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after grouped-route plan extraction |
| W156-01 | P1 | Add load finalize runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadFinalizeRuntime.ts` | DONE | load finalize summary/selection/columns/status/trace helpers centralized |
| W156-02 | P1 | Wire ActionView load tail to finalize runtime helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | load success tail delegates finalize state shaping to runtime module |
| W156-03 | P1 | Remove direct load-tail helper imports from ActionView | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView no longer imports low-level trace/selection helper set directly |
| W156-04 | P1 | Extend guard for load-finalize runtime helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires load finalize helper tokens |
| W156-05 | P1 | Re-run verify gates after load-finalize extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after load-finalize extraction |
| W157-01 | P1 | Add load preflight runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadPreflightRuntime.ts` | DONE | load preflight contract/sort/limit/field/missing-code helpers centralized |
| W157-02 | P1 | Wire ActionView preflight branch to runtime preflight helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | preflight branch delegates contract flags/sort/limit/missing-code/field flags to runtime helpers |
| W157-03 | P1 | Remove direct sort/limit seed dependency from ActionView preflight | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView preflight no longer calls low-level sort/limit helpers directly |
| W157-04 | P1 | Extend guard for load preflight runtime helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires load preflight helper tokens |
| W157-05 | P1 | Re-run verify gates after load preflight extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after load preflight extraction |
| W158-01 | P1 | Add load route-request runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadRouteRequestRuntime.ts` | DONE | load request domain/context/payload and route-sync plan helpers centralized |
| W158-02 | P1 | Wire ActionView request build to load route-request runtime | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | load request now delegates domain/context/payload shaping to runtime helpers |
| W158-03 | P1 | Wire ActionView route-sync plan merge to load route-request runtime | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | load route-sync plan/patch now delegates to runtime helpers |
| W158-04 | P1 | Extend guard for load route-request runtime helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires load route-request helper tokens |
| W158-05 | P1 | Re-run verify gates after load route-request extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after load route-request extraction |
| W159-01 | P1 | Add load branch-decision runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadBranchRuntime.ts` | DONE | load read/capability/missing-model/no-model/form-resid branch helpers centralized |
| W159-02 | P1 | Wire ActionView load branch decisions to runtime branch helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | load branch redirects/errors/form-resid now delegate to runtime branch helpers |
| W159-03 | P1 | Remove direct missing-model code mapping from ActionView | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | missing-model redirect code mapping moved to runtime helper |
| W159-04 | P1 | Extend guard for load branch helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires load branch helper tokens |
| W159-05 | P1 | Re-run verify gates after load branch extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after load branch extraction |
| W160-01 | P1 | Add load success-apply runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadSuccessApplyRuntime.ts` | DONE | load success scope/summary/window/groupedRows/records apply helpers centralized |
| W160-02 | P1 | Wire ActionView load success branch to apply runtime helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | load success branch delegates scope/summary/window/groupedRows/records shaping to runtime helpers |
| W160-03 | P1 | Remove direct success-apply helper calls from ActionView | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView no longer calls project-scope/group-summary/group-window/grouped-rows low-level helpers directly |
| W160-04 | P1 | Extend guard for load success-apply helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires load success-apply helper tokens |
| W160-05 | P1 | Re-run verify gates after load success-apply extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after load success-apply extraction |
| W161-01 | P1 | Add load catch-apply runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadCatchApplyRuntime.ts` | DONE | load catch list/scope/trace/status/latency apply helpers centralized |
| W161-02 | P1 | Wire ActionView catch branch to catch-apply helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | catch branch delegates state apply mapping to runtime helpers |
| W161-03 | P1 | Create wave-next execution pack for W161 | Governance Layer | `docs/ops/audits/frontend_contract_strict_wave_next_execution_pack_v1.md` | DONE | next-wave entry package added with batch scope and acceptance |
| W161-04 | P1 | Extend guard for load catch-apply helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires load catch-apply helper tokens |
| W161-05 | P1 | Re-run verify gates after load catch-apply extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after load catch-apply extraction |
| W162-01 | P1 | Add load-trigger runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadTriggerRuntime.ts` | DONE | reload/search/sort/filter trigger plans centralized |
| W162-02 | P1 | Wire ActionView reload/search/sort/filter to trigger helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | load-trigger handlers delegate transition and group-offset mapping to runtime helpers |
| W162-03 | P1 | Remove direct list-control transition calls from ActionView handlers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | handler-level direct transition logic replaced by runtime plans |
| W162-04 | P1 | Extend guard for load-trigger helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires load-trigger helper tokens |
| W162-05 | P1 | Re-run verify gates after load-trigger extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after load-trigger extraction |
| W163-01 | P1 | Add selection-state runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewSelectionStateRuntime.ts` | DONE | clear/assignee/toggle/if-match selection state helpers centralized |
| W163-02 | P1 | Wire ActionView selection handlers to selection-state helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | selection handlers delegate state mapping to runtime helpers |
| W163-03 | P1 | Remove direct selection transition logic from ActionView | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | page no longer performs inline selection toggle/all/if-match mapping |
| W163-04 | P1 | Extend guard for selection-state helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires selection-state helper tokens |
| W163-05 | P1 | Re-run verify gates after selection-state extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after selection-state extraction |
| W164-01 | P1 | Add batch-action flow runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchActionFlowRuntime.ts` | DONE | batch target/delete-mode/guard/delete-seed/standard-seed helpers centralized |
| W164-02 | P1 | Wire ActionView batch-action preflight to flow helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | batch preflight now delegates target/delete-mode/guard and request seeds to runtime helpers |
| W164-03 | P1 | Remove direct batch-action inline seed calculations from ActionView | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | inline idempotency/if-match seed construction replaced by runtime helpers |
| W164-04 | P1 | Extend guard for batch-action flow helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires batch-action flow helper tokens |
| W164-05 | P1 | Re-run verify gates after batch-action flow extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after batch-action flow extraction |
| W165-01 | P1 | Add batch-assign flow runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchAssignFlowRuntime.ts` | DONE | batch-assign target/guard/seed/assignee/failure-message helpers centralized |
| W165-02 | P1 | Wire ActionView batch-assign flow to runtime helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | batch-assign flow delegates preflight, seed and message derivation to runtime helpers |
| W165-03 | P1 | Remove direct batch-assign inline seed/label mapping from ActionView | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | inline if-match/idempotency/assignee label construction replaced by runtime helpers |
| W165-04 | P1 | Extend guard for batch-assign flow helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires batch-assign flow helper tokens |
| W165-05 | P1 | Re-run verify gates after batch-assign flow extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after batch-assign flow extraction |
| W166-01 | P1 | Add batch-export flow runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchExportFlowRuntime.ts` | DONE | batch-export target/guard/domain/request/no-content helpers centralized |
| W166-02 | P1 | Wire ActionView export flow to runtime helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | export flow delegates preflight/domain/request/no-content checks to runtime helpers |
| W166-03 | P1 | Remove direct export guard/request construction from ActionView | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | inline export guard/build request logic replaced by runtime helpers |
| W166-04 | P1 | Extend guard for batch-export flow helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires batch-export flow helper tokens |
| W166-05 | P1 | Re-run verify gates after batch-export flow extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after batch-export flow extraction |
| W167-01 | P1 | Add batch-error-detail flow runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchErrorDetailFlowRuntime.ts` | DONE | batch error fallback/detail line helpers centralized |
| W167-02 | P1 | Wire ActionView batch/export/load-more catch detail rendering to runtime helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | catch branches delegate fallback/detail-line construction to runtime helpers |
| W167-03 | P1 | Remove inline batch fallback detail objects from ActionView catches | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | inline fallback objects replaced by runtime fallback resolvers |
| W167-04 | P1 | Extend guard for batch-error-detail helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires batch-error-detail flow helper tokens |
| W167-05 | P1 | Re-run verify gates after batch-error-detail extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after batch-error-detail extraction |
| W168-01 | P1 | Add load-more-failures flow runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadMoreFailuresFlowRuntime.ts` | DONE | load-more guard/request/apply/error-detail helpers centralized |
| W168-02 | P1 | Wire ActionView load-more-failures flow to runtime helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | load-more flow delegates guard/request/apply/error detail construction to runtime helpers |
| W168-03 | P1 | Remove direct load-more low-level helper calls from ActionView | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | direct `resolveLoadMoreFailuresGuard` and request builder calls replaced by flow helpers |
| W168-04 | P1 | Extend guard for load-more-failures flow helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires load-more flow helper tokens |
| W168-05 | P1 | Re-run verify gates after load-more-failures flow extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after load-more flow extraction |
| W169-01 | P1 | Add batch-request-seed runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchRequestSeedRuntime.ts` | DONE | idempotency payload/key and last-request seed helpers centralized |
| W169-02 | P1 | Wire ActionView idempotency key composition to request-seed helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | `buildIdempotencyKey` now delegates payload/key shaping to runtime helpers |
| W169-03 | P1 | Wire ActionView lastBatchRequest states to request-seed helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | batch action/assign last-request state mapping delegated to runtime helpers |
| W169-04 | P1 | Extend guard for batch-request-seed helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires batch-request-seed helper tokens |
| W169-05 | P1 | Re-run verify gates after batch-request-seed extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after batch-request-seed extraction |
| W170-01 | P1 | Add batch-failure-apply flow runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchFailureApplyFlowRuntime.ts` | DONE | batch failure preview/lines/merge/paging/csv apply helpers centralized |
| W170-02 | P1 | Wire ActionView batch failure artifact apply path to flow helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | apply path delegates preview/lines/merge/paging/csv mapping to runtime helper facade |
| W170-03 | P1 | Remove direct batch artifact low-level helper calls from ActionView apply path | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | direct `mapBatchFailureDetailLines` and merge/paging/csv helper calls replaced by flow helpers |
| W170-04 | P1 | Extend guard for batch-failure-apply flow helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires batch-failure apply flow helper tokens |
| W170-05 | P1 | Re-run verify gates after batch-failure-apply flow extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after batch-failure apply flow extraction |
| W171-01 | P1 | Add batch-artifact-state flow runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchArtifactStateFlowRuntime.ts` | DONE | batch reset/catch apply state helpers centralized for action/assign/export/load-more flows |
| W171-02 | P1 | Wire ActionView batch reset and catch paths to artifact-state helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | action/assign/export/load-more handlers delegate artifact state application to runtime helper facade |
| W171-03 | P1 | Remove direct reset/detail low-level calls from ActionView batch flows | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | direct `resolveBatchArtifactsReset` and direct error-detail application calls replaced by flow helpers |
| W171-04 | P1 | Extend guard for batch-artifact-state flow helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires batch artifact-state flow helper tokens |
| W171-05 | P1 | Re-run verify gates after batch-artifact-state flow extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after batch artifact-state flow extraction |
| W172-01 | P1 | Add batch-hint-resolver runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewBatchHintResolverRuntime.ts` | DONE | batch failure hint/action-meta/tag text resolvers centralized |
| W172-02 | P1 | Wire ActionView batch failure apply path to hint-resolver helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | apply path delegates hint/action-meta/tag-text mapping to runtime helper facade |
| W172-03 | P1 | Remove repeated inline batch error hint lambdas from ActionView catch paths | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | catch paths now consume shared batch error hint resolver helper |
| W172-04 | P1 | Extend guard for batch-hint-resolver helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires batch hint resolver helper tokens |
| W172-05 | P1 | Re-run verify gates after batch-hint-resolver extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after batch hint-resolver flow extraction |
| W173-01 | P1 | Add load-state-apply runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadStateApplyRuntime.ts` | DONE | route-selection/contract-flag/group-identity/project-scope/window-metrics apply helpers centralized |
| W173-02 | P1 | Wire ActionView load preflight/success apply blocks to state-apply helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | load path delegates state application blocks to runtime helper facade |
| W173-03 | P1 | Remove repeated inline load state assignment blocks from ActionView | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | repeated route/flag/group/scope/window state assignments replaced by runtime helper outputs |
| W173-04 | P1 | Extend guard for load-state-apply helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires load state-apply helper tokens |
| W173-05 | P1 | Re-run verify gates after load-state-apply extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after load state-apply extraction |
| W174-01 | P1 | Add load-redirect-error runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadRedirectErrorRuntime.ts` | DONE | load redirect target and early-error apply helpers centralized |
| W174-02 | P1 | Wire ActionView load early-error branches to redirect-error helpers | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | missing action/view-type/resolved-model branches delegate status apply to runtime helper facade |
| W174-03 | P1 | Wire ActionView capability/missing-model redirects to runtime helper targets | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | redirect target construction delegated to runtime helper facade |
| W174-04 | P1 | Extend guard for load-redirect-error helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires load redirect/error helper tokens |
| W174-05 | P1 | Re-run verify gates after load-redirect-error extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after load redirect/error extraction |
| W175-01 | P1 | Add load-view-field-state runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadViewFieldStateRuntime.ts` | DONE | kanban field apply/requested-field apply/missing-columns apply helpers centralized |
| W175-02 | P1 | Wire ActionView load view-field apply path to runtime helper facade | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | load path delegates kanban/advanced field and requested-field mapping to runtime helper outputs |
| W175-03 | P1 | Remove inline view-field assignment and missing-columns status branches from ActionView load | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | inline effective-kanban/requested-fields/missing-columns apply blocks replaced by runtime helper states |
| W175-04 | P1 | Extend guard for load-view-field-state helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires load view-field-state helper tokens |
| W175-05 | P1 | Re-run verify gates after load-view-field-state extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after load view-field-state extraction |
| W176-01 | P1 | Add load-domain-context-request runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadDomainContextRequestRuntime.ts` | DONE | domain/context/request-payload state helper facade centralized |
| W176-02 | P1 | Wire ActionView load domain/context apply path to helper facade | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | load path delegates domain/context state mapping to runtime helper outputs |
| W176-03 | P1 | Replace direct list request payload construction with request-state helper | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | request payload composition now uses runtime helper facade before listRecordsRaw |
| W176-04 | P1 | Extend guard for load-domain-context-request helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires domain/context/request helper tokens and drops legacy direct tokens |
| W176-05 | P1 | Re-run verify gates after load-domain-context-request extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after load domain/context/request extraction |
| W177-01 | P1 | Add load-success-state-apply runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadSuccessStateApplyRuntime.ts` | DONE | list-total/group-summary/grouped-rows/finalize/trace apply helpers centralized |
| W177-02 | P1 | Wire ActionView load success state applications to helper facade | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | success path delegates summary/grouped/finalize/trace apply blocks to runtime helper outputs |
| W177-03 | P1 | Remove repeated inline success-state assignments from ActionView load | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | inline list-total/group-summary/grouped-rows/finalize/trace apply blocks replaced by runtime helper states |
| W177-04 | P1 | Extend guard for load-success-state-apply helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires load success state-apply helper tokens |
| W177-05 | P1 | Re-run verify gates after load-success-state-apply extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after load success state-apply extraction |
| W178-01 | P1 | Add load-catch-state-apply runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadCatchStateApplyRuntime.ts` | DONE | catch list/scope/trace-status/latency apply helpers centralized |
| W178-02 | P1 | Wire ActionView load catch branch to catch-state helper facade | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | catch branch delegates state assignment blocks to runtime helper outputs |
| W178-03 | P1 | Remove repeated inline catch-state assignment blocks from ActionView load | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | inline list/scope/trace/status/latency assignments replaced by helper-driven apply states |
| W178-04 | P1 | Extend guard for load-catch-state-apply helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires load catch state-apply helper tokens |
| W178-05 | P1 | Re-run verify gates after load-catch-state-apply extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after load catch state-apply extraction |
| W179-01 | P1 | Add load-route-apply runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewLoadRouteApplyRuntime.ts` | DONE | route reset/sync apply helpers centralized |
| W179-02 | P1 | Wire ActionView load route reset/sync branch to helper facade | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | route reset and sync branches consume runtime helper apply states |
| W179-03 | P1 | Remove inline route reset/sync apply assignments from ActionView load | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | inline group window reset and sync patch checks replaced by helper outputs |
| W179-04 | P1 | Extend guard for load-route-apply helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires load route apply helper tokens |
| W179-05 | P1 | Re-run verify gates after load-route-apply extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after load route apply extraction |
| W180-01 | P1 | Add navigation-apply runtime helper module | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewNavigationApplyRuntime.ts` | DONE | route replace/focus push/url redirect/row-click apply helpers centralized |
| W180-02 | P1 | Wire ActionView route replace and focus navigation to helper facade | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | replaceCurrentRouteQuery/openFocusAction now consume navigation apply helper outputs |
| W180-03 | P1 | Wire ActionView url-redirect and row-click navigation to helper facade | Page Assembly Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | url unsupported/portal self redirects and row-click push now use helper states |
| W180-04 | P1 | Extend guard for navigation-apply helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires navigation apply helper tokens |
| W180-05 | P1 | Re-run verify gates after navigation-apply extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass after navigation apply extraction |
| W9-01 | P1 | Extract context merge runtime helper | Runtime Execution Layer | `frontend/apps/web/src/app/runtime/actionViewRequestRuntime.ts` | DONE | route/menu/request context merge moved out of ActionView |
| W9-02 | P1 | Wire ActionView context merge helper usage | Runtime Execution Layer | `frontend/apps/web/src/views/ActionView.vue` | DONE | ActionView delegates request context merge to runtime helper |
| W9-03 | P1 | Extend guard for context helper adoption | Runtime Verification Layer | `scripts/verify/frontend_actionview_scene_specialcase_guard.py` | DONE | guard requires context merge helper token |
| W9-04 | P1 | Re-run verify gates after context extraction | Runtime Verification Layer | `Makefile` + `docs/ops/audit/*` | DONE | verify targets pass with context merge extraction |

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

## Wave Closure
- Closure status: `PASS (ready to close this wave)`
- Closure audit: `docs/ops/audits/frontend_contract_strict_wave_closure_v1.md`
- Final gate evidence:
  - `make verify.frontend.actionview.scene_specialcase.guard` PASS
  - `make verify.scene.delivery.readiness` PASS
  - `docs/ops/audits/scene_ready_strict_gap_full_audit.md` (`strict_unresolved_count=0`)

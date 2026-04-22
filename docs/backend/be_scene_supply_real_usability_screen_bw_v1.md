# Backend Scene Supply Real Usability Screen BW

## Task

- Task: `ITER-2026-04-20-BE-SCENE-SUPPLY-REAL-USABILITY-SCREEN-BW`
- Date: `2026-04-20`
- Branch: `codex/next-round`
- Stage: `screen`
- Battlefield: `backend`
- Backend sub-layer: `scene_orchestration`

## Inputs

This screen is bounded to:

1. Real browser verify evidence from:
   - `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260420T030147Z/summary.json`
   - `artifacts/codex/unified-system-menu-click-usability-smoke/20260420T030241Z/summary.json`
   - `artifacts/codex/unified-system-menu-click-usability-smoke/20260420T030241Z/failed_cases.json`
2. Backend scene/menu supply reads from:
   - `addons/smart_core/delivery/menu_target_interpreter_service.py`
   - `addons/smart_construction_scene/profiles/scene_registry_content.py`
   - `addons/smart_construction_scene/core_extension.py`
   - `addons/smart_core/orchestration/project_dashboard_scene_orchestrator.py`
   - `addons/smart_construction_core/handlers/project_dashboard_enter.py`
   - `addons/smart_construction_core/views/menu.xml`

## Screen Result

- `PASS`
- The real usability failures are backend scene-orchestration supply gaps.
- They are not one single regression. They split into three bounded classes.

## Class A: Duplicate Project Dashboard Semantics Still Split

Frozen fact:

- Real menu verify shows:
  - `系统菜单/项目管理/项目驾驶舱` with `scene_key=project.management` and route
    `/s/project.management` is `PASS`.
  - `系统菜单/看板中心/项目驾驶舱` with `scene_key=project.dashboard` is `FAIL`.
- Primary-entry smoke on `/s/project.management` still records:
  - `backend_scene_key = project.dashboard`
  - `dashboard_profile = old`
  - final failure: `dashboard missing status explain`

Backend cause classification:

- `project.management` and `project.dashboard` are both kept as active scene
  identities in `scene_registry_content.py`.
- `project.dashboard.enter` still builds payload through
  `ProjectDashboardSceneOrchestrator`, whose `scene_key` remains
  `project.dashboard`.
- The custom frontend therefore reaches the project-management route through a
  mixed semantic chain: route points to `project.management`, but the entry
  payload is still anchored on `project.dashboard`.

Decision:

- This is a backend scene-orchestration convergence gap.
- The next implement batch must make one scene the authoritative semantic
  carrier for the project dashboard entry path, instead of keeping both
  `project.management` and `project.dashboard` active for ordinary PM runtime.

## Class B: Menu Nodes Missing Scene Identity Entirely

Frozen fact:

- Failed menu cases such as `合同汇总`, `投标管理`, and `待我审批（物资计划）`
  degrade to:
  - `reason=CONTRACT_CONTEXT_MISSING`
  - `diag=menu_route_missing_scene_identity`

Backend cause classification:

- These nodes still ship action-driven legacy menu facts, but the scene
  registry does not provide a scene identity for those exact menu/action pairs.
- Representative examples from current backend assets:
  - `menu_sc_project_contract_overview` / `action_project_contract_overview`
  - `menu_sc_project_tender` / `action_tender_bid`
  - `menu_sc_tier_review_my_material_plan` /
    `action_sc_tier_review_my_material_plan`
- `menu_target_interpreter_service.py` only emits a scene `entry_target` when
  it can resolve `scene_key`. Otherwise it falls back to compatibility payload.

Decision:

- These are direct backend menu-scene supply holes.
- The next implement batch must assign exact scene identities or additive
  scene-oriented entry targets for these menu leaves.

## Class C: Scene Key Exists, But Entry Supply Is Not Scene-Ready

Frozen fact:

- Failed menu cases such as `预算/成本`, `执行结构`, `成本台账`, `成本报表`,
  `经营利润`, `付款/收款申请`, `结算单`, `资金台账`, `我的工作` degrade to
  workbench with:
  - `reason=CONTRACT_CONTEXT_MISSING`
  - existing `scene=<scene_key>`

Backend cause classification:

- These menu nodes already receive a scene key, but backend supply is not yet a
  complete scene-oriented entry contract for direct consumption.
- Current registry content often anchors the scene to a different canonical
  menu than the failing leaf menu. Examples:
  - `cost.project_budget` points to `menu_sc_project_budget`, while the failing
    PM leaf is `menu_sc_project_budget_center`
  - `cost.analysis` points to `menu_sc_project_cost_ledger`, while there are
    multiple cost-entry leaves sharing related actions
  - `finance.payment_requests` points to `menu_payment_request`, but other
    finance leaves still route through legacy action-backed menus
- In these cases the backend currently provides scene identity, but not a
  unique scene-ready leaf entry target that the frontend can consume without
  recovering context locally.

Decision:

- This is also a backend scene-orchestration gap.
- The next implement batch must expand menu leaf delivery from
  `scene_key-only` to a complete scene-oriented entry target with enough route
  and compatibility context for direct consumption.

## Boundary Conclusion

The real usability verify invalidates the earlier “custom frontend route
boundary closed” claim.

Current boundary truth is:

1. The PM primary path is only partially scene-oriented.
2. Menu scene delivery is not leaf-complete.
3. The frontend is still being forced into recovery mode because backend output
   is not uniquely consumable for most real leaves.

## Next Implement Batch

Open one bounded backend implement batch with this exact target:

1. Converge the PM dashboard primary semantics so `project.management` becomes
   the unique ordinary entry scene, or formally retire `project.dashboard` from
   that path.
2. Add scene identities for the Class B action-backed menu leaves.
3. Upgrade Class C menu leaves from `scene_key-only` to full scene-oriented
   `entry_target` delivery, including exact route/context needed by the
   consumer.

Frontend changes should be deferred until this backend semantic supply batch is
complete and re-verified.

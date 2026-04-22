# Backend Scene Supply Real Usability Implement BX

## Task

- Task: `ITER-2026-04-20-BE-SCENE-SUPPLY-REAL-USABILITY-IMPLEMENT-BX`
- Date: `2026-04-20`
- Branch: `codex/next-round`

## Implemented Changes

1. `addons/smart_core/delivery/menu_target_interpreter_service.py`
   - Added scene-route resolution from explicit scene rows and scene registry
     targets instead of hard-forcing every scene to `/s/<scene_key>`.
   - Allowed explicit `entries` rows to derive `menu_id` / `action_id` from the
     nested `target` payload as well as top-level fields.
2. `addons/smart_construction_scene/services/capability_scene_targets.py`
   - Converged `project.dashboard.enter` and `project.dashboard.open` onto
     `project.management`.
3. `addons/smart_construction_scene/profiles/scene_registry_content.py`
   - Added stable routes for existing finance/cost scenes that were previously
     delivered as scene-key-only.
4. `addons/smart_core/orchestration/project_dashboard_scene_orchestrator.py`
   - Converged orchestrator scene ownership from `project.dashboard` to
     `project.management`.
5. Tests
   - Updated project dashboard backend expectations to `project.management`.
   - Added a route-preference test for menu target interpreter.
   - Added a capability-map convergence test for `project.dashboard.enter`.

## Code Result

- `PASS`

Evidence:

- targeted `py_compile` to `/tmp`: `PASS`
- `python3 addons/smart_core/tests/test_menu_target_interpreter_entry_target.py`: `PASS`
- `python3 addons/smart_construction_scene/tests/test_action_only_scene_semantic_supply.py`: `PASS`
- `make verify.smart_core DB_NAME=sc_demo`: `PASS`

## Contract Result

- `PARTIAL`

Recovered:

- Post-restart project dashboard browser smoke now freezes:
  - `backend_entry_route = /s/project.management`
  - `backend_scene_key = project.management`

This proves the backend semantic carrier convergence took effect.

Still failing:

- The same artifact still records `dashboard_profile = old` and ends with
  `dashboard missing status explain`.
- This means backend scene identity is now converged, but the runtime is still
  consuming an old dashboard profile path somewhere after route entry.

## Live Usability Result

- `FAIL`

Artifacts:

- Project dashboard primary entry:
  - `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260420T033848Z/summary.json`
- Unified menu click smoke:
  - `artifacts/codex/unified-system-menu-click-usability-smoke/20260420T034011Z/summary.json`
  - `artifacts/codex/unified-system-menu-click-usability-smoke/20260420T034011Z/failed_cases.json`

Measured improvement:

- Menu failure count improved from `28 / 31` to `22 / 31`.

Recovered classes:

- Some scene-key-existing finance/cost leaves now resolve instead of degrading.
- Backend scene ownership for the PM primary path is no longer split between
  `project.dashboard` and `project.management`.

Remaining blockers:

1. `project.management` still lands on `dashboard_profile=old`.
2. `22` leaf menus still fail.
3. The remaining failures are dominated by:
   - action-backed leaves still lacking scene identity
   - PM/cost/material leaves still lacking full scene-ready context even after
     route supply improvement

## Environment Result

- `trusted`

Reason:

- Runtime was restarted with `make restart`.
- Live browser verification was rerun against the active custom frontend
  `http://127.0.0.1:5174` and backend `http://127.0.0.1:8069`.

## Gate Result

- `validate_task`: `PASS`
- targeted Python validation: `PASS`
- `verify.smart_core`: `PASS`
- post-restart real browser verification: `FAIL`

Overall decision: `FAIL`

## Conclusion

This batch is effective but incomplete.

The backend fix is real and measurable:

- PM scene ownership converged correctly.
- Menu failures dropped by `6`.

But the user-visible objective is still not met, so the batch cannot be closed
as success.

## Next Step

Open the next bounded repair line on the two remaining blockers:

1. Trace why `/s/project.management` still resolves to `dashboard_profile=old`
   after backend scene convergence.
2. Continue backend-first menu scene supply for the remaining `22` leaves,
   especially the action-backed PM/material/finance entries still degrading to
   `CONTRACT_CONTEXT_MISSING` or missing scene identity.

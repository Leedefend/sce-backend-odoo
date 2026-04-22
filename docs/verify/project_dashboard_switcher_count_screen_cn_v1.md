# Project Dashboard Switcher Count Screen CN

## Goal

Classify why the live dashboard switcher still exposes only one project after
the dashboard surface and `当前状态说明` assertion were recovered.

## Evidence

1. Live browser smoke after `CM`
   - FAIL
   - Terminal assertion:
     - `project switcher should expose at least 2 projects, got 1`
2. Direct intent diagnosis against `project.entry.context.options`
   - PASS
   - With `project_context.project_id=925`, backend returned:
     - `options: []`
     - `suggested_action.reason_code=PROJECT_OPTIONS_EMPTY`
     - `diagnostics_summary.status=context_missing`
     - `diagnostics_summary.option_count=0`
3. Frontend consumer inspection
   - `frontend/apps/web/src/views/ProjectManagementDashboardView.vue`
   - `loadProjectSwitcherOptions()` falls back to the current project only when
     remote `options` is empty
   - Therefore the single switcher item seen in browser is a frontend fallback,
     not proof that frontend filtered out multiple backend options
4. Backend option-supply inspection
   - `addons/smart_construction_core/services/project_entry_context_service.py`
   - `list_options()` searches `project.project` from
     `ProjectDashboardService._project_domain_for_user()`
   - It keeps any project whose `_project_rank()` is greater than `0`
   - `_project_rank()` grants positive score to most non-noisy projects, so the
     empty result is more consistent with candidate search-domain starvation
     than with rank-based elimination
5. Backend domain inspection
   - `addons/smart_construction_core/services/project_dashboard_service.py`
   - `_project_domain_for_user()` only builds ownership/member-based OR
     conditions such as `manager_id/owner_id/user_id/create_uid/user_ids/...`
   - This is narrower than the fallback resolution logic used by
     `resolve_project_with_diagnostics()`, which can still recover an active
     project via `creator_domain`, `user_domain`, or even global fallback

## Conclusion

The switcher-count failure is classified as a backend option-supply problem,
not a frontend consumer/filtering problem.

The browser showed one project only because the frontend injected the current
project as a local fallback after backend `project.entry.context.options`
returned an empty list.

The next valid repair batch should stay on the backend battlefield and widen or
reconcile the dashboard option candidate selection path so that
`project.entry.context.options` can return at least two valid project options
for the existing demo runtime.

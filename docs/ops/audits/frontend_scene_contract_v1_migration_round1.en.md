# Frontend `scene_contract_v1` Migration Status (Round 1)

## Goal
- Migrate frontend pages from only consuming `page_orchestration_v1` to preferring orchestration output contract `scene_contract_v1`.
- Keep compatibility fallback to `page_orchestration_v1` when `scene_contract_v1` is not available.

## Completed pages in this round
- `home` (`frontend/apps/web/src/views/HomeView.vue`)
- `project.management.dashboard` (`frontend/apps/web/src/views/ProjectManagementDashboardView.vue`)
- `my_work` (`frontend/apps/web/src/views/MyWorkView.vue`)
- `workbench` (`frontend/apps/web/src/views/WorkbenchView.vue`)

## Guards added/upgraded
- `verify.frontend.scene_contract_v1.consumption.guard`
  - Covers token checks for the 4 migrated pages.
- `verify.frontend.actionview.scene_specialcase.guard`
  - Keeps `ActionView` from regressing to scene/model hardcoded branches.

## Validation results
- `make verify.frontend.scene_contract_v1.consumption.guard` PASS
- `python3 scripts/verify/frontend_actionview_scene_specialcase_guard.py` PASS
- `make verify.frontend.typecheck.strict` PASS
- `make verify.page_orchestration.target_completion.guard` PASS
- `make verify.workspace_home.orchestration_schema.guard` PASS
- `make verify.project.dashboard.contract` PASS

## Remaining migration backlog (next stage)

### P0 (highest priority)
- `action` (`frontend/apps/web/src/views/ActionView.vue`)
  - Target: consume `scene_contract_v1` (`zones[] + blocks{}`) as primary render source and reduce in-view semantic inference.
- `record` (`frontend/apps/web/src/views/RecordView.vue`)
  - Target: move action/zone decisions to contract-driven path.

### P1 (core navigation pages)
- `scene` (`frontend/apps/web/src/views/SceneView.vue`)
- `menu` (`frontend/apps/web/src/views/MenuView.vue`)

### P2 (supporting pages)
- `scene_health` (`frontend/apps/web/src/views/SceneHealthView.vue`)
- `scene_packages` (`frontend/apps/web/src/views/ScenePackagesView.vue`)
- `usage_analytics` (`frontend/apps/web/src/views/UsageAnalyticsView.vue`)
- `placeholder` (`frontend/apps/web/src/views/PlaceholderView.vue`)
- `login` (`frontend/apps/web/src/views/LoginView.vue`, evaluate if full contract consumption is needed)

## Boundary notes
- No scene key / page key / route protocol changes.
- No ACL baseline or business verdict logic changes.
- This round only optimizes frontend contract consumption path.

## Round conclusion
- First high-value batch is now on `scene_contract_v1` primary consumption path.
- Ready to start next batch (`ActionView` + `RecordView`) migration.

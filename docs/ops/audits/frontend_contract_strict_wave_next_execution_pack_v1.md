# Frontend Contract Strict Wave Next Execution Pack v1

## Wave Position
- Previous wave: closed (`frontend_contract_strict_wave_closure_v1`).
- Current wave goal: continue shrinking `ActionView.vue` by moving remaining load-branch apply logic to runtime helper modules.

## Batch Strategy
- Use homogeneous batches (`5` items per batch).
- Each batch must include:
  1. runtime helper extraction
  2. ActionView wiring
  3. guard token update
  4. checklist row update
  5. dual verify (`scene_specialcase_guard` + `scene.delivery.readiness`)

## Batch N+1 Scope (W161)
- Theme: `load()` catch-branch apply state extraction.
- Layer target: `Runtime Execution Layer` and `Page Assembly Layer`.
- Modules:
  - `frontend/apps/web/src/app/runtime/actionViewLoadCatchApplyRuntime.ts`
  - `frontend/apps/web/src/views/ActionView.vue`
  - `scripts/verify/frontend_actionview_scene_specialcase_guard.py`
  - `docs/ops/codex_friendly_execution_checklist_frontend_contract_strict_wave_v1.md`

## W161 Acceptance
- ActionView catch branch delegates list/project-scope/trace/status/latency apply mapping to runtime helpers.
- Guard requires new catch-apply helper tokens.
- Both verify gates pass.

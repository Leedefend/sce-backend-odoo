# ITER-2026-03-31-398 Report

## Summary

- Repaired the confirmed frontend-originated drift in `projects.intake`.
- Removed the two-card routing shell from the custom scene page.
- Changed the scene route to hand off directly to the existing project form
  handling surface at `/f/project.project/new`.

## Changed Files

- `frontend/apps/web/src/views/ProjectsIntakeView.vue`
- `agent_ops/tasks/ITER-2026-03-31-398.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-398.md`
- `agent_ops/state/task_results/ITER-2026-03-31-398.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-398.yaml` -> PASS
- `pnpm -C frontend/apps/web typecheck:strict` -> PASS

## Implementation

Frontend file:

- `frontend/apps/web/src/views/ProjectsIntakeView.vue`

What changed:

- the previous custom UI with:
  - `快速创建（推荐）`
  - `标准立项`
  was removed
- the scene route now performs a direct handoff to:
  - `/f/project.project/new`
- the handoff preserves:
  - `scene_key = projects.intake`
  - `scene_label = 项目立项`
  - workspace context query
- a minimal fallback card remains only as a recovery path if auto-redirect does
  not complete

## Why This Is Aligned

This repair follows the fact-layer conclusion from `397`:

- backend already publishes `projects.intake` as a form-oriented scene
- the custom drift was caused by the frontend routing-shell implementation
- the lowest-risk correction is to stop re-defining the page shell and reuse the
  existing form surface

This also follows the native-view reuse guard:

- do not create another bespoke page shell when an existing form handling
  surface already exists
- prefer handing the scene route to the form surface rather than inventing new
  frontend-only structure or business semantics

## User-Visible Outcome

- entering `/s/projects.intake` now immediately enters the form handling path
- the strongest current intake drift is reduced
- the page is now closer to the business-fact form surface

## Risk Analysis

- Risk remained low.
- Only one frontend view file was changed.
- No backend model, intent, contract, ACL, finance, or manifest paths were
  touched.
- The remaining caution is behavioral:
  - this batch improves alignment by direct handoff
  - it does not yet create a richer scene-native hero/checklist rendering inside
    `/s/projects.intake`

## Rollback

- `git restore frontend/apps/web/src/views/ProjectsIntakeView.vue`
- `git restore agent_ops/tasks/ITER-2026-03-31-398.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-398.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-398.json`

## Next Suggestion

- If the next batch stays on business-fact alignment, re-audit `projects.intake`
  after this handoff change and then decide whether the remaining gap is small
  enough to accept or whether a richer scene-native form shell is still needed.

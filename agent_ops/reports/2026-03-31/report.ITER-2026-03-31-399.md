# ITER-2026-03-31-399 Report

## Summary

- Re-audited `projects.intake` after the direct form handoff repair.
- Confirmed that the strongest previous drift has been removed.
- Reduced the remaining gap to a narrow residual difference rather than a major
  page-structure mismatch.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-31-399.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-399.md`
- `agent_ops/state/task_results/ITER-2026-03-31-399.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-399.yaml` -> PASS

## Re-Audit Basis

Fact-layer basis:

- `addons/smart_construction_scene/data/sc_scene_layout.xml:24`
- `addons/smart_construction_scene/data/sc_scene_layout.xml:32`
- `addons/smart_construction_scene/data/sc_scene_layout.xml:39`
- `addons/smart_construction_scene/data/sc_scene_layout.xml:62`
- `addons/smart_construction_scene/data/sc_scene_layout.xml:66`
- `addons/smart_construction_scene/data/sc_scene_layout.xml:73`
- `addons/smart_construction_scene/data/sc_scene_layout.xml:77`

Observed fact shape:

- `projects.intake` remains a `record/form` scene
- it still declares:
  - `hero`
  - `form_main`
  - `checklist`
- it still declares the primary form field surface for `project.project`

Current frontend behavior:

- `frontend/apps/web/src/views/ProjectsIntakeView.vue:2`
- `frontend/apps/web/src/views/ProjectsIntakeView.vue:11`
- `frontend/apps/web/src/views/ProjectsIntakeView.vue:44`
- `frontend/apps/web/src/views/ProjectsIntakeView.vue:51`

Observed frontend shape:

- the page no longer renders the old two-card business-choice shell
- on mount, it immediately redirects to:
  - `/f/project.project/new`
- it preserves:
  - `scene_key = projects.intake`
  - `scene_label = 项目立项`
  - workspace context
- the remaining on-page UI is only a fallback recovery card in case the redirect
  does not complete

## Updated Verdict

- `structure = partially_aligned`
- `fields = aligned_by_handoff`
- `delivery_logic = aligned`

## Why The Verdict Improved

Before `398`, the page itself replaced the fact-layer form surface with a
custom choice shell.

After `398`:

- the scene route now hands off to the existing form handling surface
- the field surface is no longer replaced by a bespoke page shell
- the delivery path is now directly tied to the form path instead of forcing the
  user through a frontend-defined business split

## Residual Gap

The remaining gap is narrow:

- `/s/projects.intake` still does not directly render the scene-declared
  `hero/form_main/checklist` shell itself
- instead, it delegates immediately to the form page

This is a residual structural difference, but it is no longer the earlier major
semantic drift.

## Main Conclusion

`projects.intake` is now close enough to treat the previous major alignment
problem as repaired for the current low-risk objective.

What remains is not a strong “frontend invented a different business page”
problem anymore. It is only a smaller question of whether a future
scene-native shell should exist on top of the handoff.

## Risk Analysis

- Risk remained low because this batch was audit-only.
- No implementation files were changed.
- The main caution is product-level only:
  - if later the team wants a richer scene-native intake shell, that should be a
    new explicit objective rather than treated as a current correctness defect

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-31-399.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-399.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-399.json`

## Next Suggestion

- Do not reopen `projects.intake` immediately.
- Move to the next active custom-frontend-vs-business-facts target unless the
  owner explicitly wants a richer scene-native intake shell.

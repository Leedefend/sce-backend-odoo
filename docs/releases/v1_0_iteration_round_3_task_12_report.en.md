# v1.0 Iteration Round 3 · Task 12 Closure Report

## 1. Task 12 Objective

Complete the next closure item for product-expression iteration:

- further sink list semantics into scene configuration,
- keep frontend expression convergence,
- keep verification chain runnable.

## 2. Completed

1. Risk workspace scene semantic sink
   - File: `addons/smart_construction_scene/data/sc_scene_layout.xml`
   - Added for `risk.center`:
     - `page.page_mode=workspace`
     - `list_profile` (column order + localized labels)
     - `default_sort`

2. Continued list expression enhancement
   - Added portfolio-style summary strip for `projects.list`.
   - Kept unified summary cards and column priorities for `task.center` / `risk.center` / `cost.project_boq`.

3. Semantic mapping hardening
   - many2one arrays now prefer display name.
   - Chinese keyword state mapping improves risk/warning/completed tones.

## 3. Boundary Statement

- No change to scene governance, ACL baseline, deploy/rollback main logic.
- No refactor of contract envelope.
- Changes remain in expression layer and scene payload semantics.

## 4. Note

`task.center` and `cost.project_boq` currently rely mostly on runtime action contract. Scene-aware list presets are already applied on frontend; deeper scene-version sinking can be added when those scenes are explicitly modeled in data files.

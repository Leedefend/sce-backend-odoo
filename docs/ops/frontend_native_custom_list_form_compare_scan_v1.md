# Frontend Native vs Custom List/Form Compare Scan v1

## Scope

This scan stays bounded to existing automated evidence and current high-frequency
page artifacts. It does not modify frontend or backend code.

Compared evidence sets:

- native/custom direct compare:
  - `artifacts/playwright/iter-2026-04-09-1427/compare_final_truth.json`
  - `native_tree_542_final.png`
  - `custom_tree_542_final.png`
  - `native_form_543_action_final.png`
  - `custom_form_543_action_final.png`
- current high-frequency custom pages:
  - `artifacts/playwright/high_frequency_pages_v2/20260418T184258Z/summary.json`
  - `project-list.png`
  - `project-detail.png`
  - `task-list.png`
  - `task-detail.png`
- current walkthrough interpretation:
  - `docs/frontend/ui_high_frequency_pages_v2_walkthrough.md`
  - `docs/frontend/ui_high_frequency_pages_v2.md`

## Layer Target

- Layer Target: `Frontend audit evidence scan`
- Module: `native versus custom list/form comparison`
- Reason: determine whether the intended native-list/native-form convergence has
  actually landed in user-visible form, rather than only in code organization.

## Automated Evidence Summary

### A. Historical native vs custom direct compare

The direct compare artifacts from `iter-2026-04-09-1427` show that the custom
views were not close visual replicas of native Odoo list/form views.

Observed from `compare_final_truth.json` and screenshots:

- `tree_542`
  - native:
    - classic Odoo top bar + dense left menu + flat list table
    - list shell is thin and table-first
  - custom:
    - branded shell, large left rail, header card, summary/filter shells
    - list is embedded inside a product-style application shell rather than
      presented as a native-first work area
- `form_543_action`
  - native:
    - standard Odoo form header with `创建 / 保存 / 放弃变更`
    - dense field grid, little chrome, low ornament
  - custom:
    - large dashboard-like shell, extra summary/filter regions, card containers
    - no native-equivalent action/header density

Conclusion from this evidence:

- at that time, the custom list/form direction had already diverged materially
  from native Odoo visual grammar
- the divergence was not a small token/theme delta; it was a different shell
  model

### B. Current high-frequency custom pages

Current high-frequency screenshots from `20260418T184258Z` confirm that the
newer project/task pages are cleaner and more internally unified, but they still
do not read as native Odoo list/form views.

Observed from current screenshots:

- `project-list.png`
  - stronger table density than older custom pages
  - but still rendered inside a branded left rail + top summary/filter shell
  - header chips, rounded cards, spacing rhythm, and soft gradient background
    remain product-shell oriented rather than native-tree oriented
- `project-detail.png`
  - form area is visibly more structured and closer to a shared detail shell
  - but still uses large hero header, KPI cards, tab chips, rounded container
    hierarchy, and command-bar treatment not present in native Odoo form views

Automated walkthrough result from `summary.json`:

- `项目列表 -> 项目详情 -> 返回`: `PASS`
- `任务列表 -> 任务详情 -> 返回`: `PASS_WITH_RISK`

This means:

- route/mainline continuity improved
- but the evidence does not indicate native visual parity
- part of the remaining instability is still startup/route latency around task
  detail, not just shell styling

## What Actually Landed

The intended work has landed mainly at these layers:

1. shared page-shell consolidation
   - project/task list pages converge onto `ListPage`
   - project/task detail pages converge onto `ContractFormPage`
2. internal design-language convergence
   - list/detail wrappers now share one token language more consistently
   - legacy wrappers were pulled closer to the same visual family
3. route/contract mainline improvements
   - project list/detail walkthrough is stable
   - task detail eventually mounts, though still with startup risk

## What Did Not Land

The following expectation has not landed:

- “custom list/form should feel close to native Odoo list/form”

Why not:

- the active shell model is still app-shell first, not native-view first
- custom left rail, large summary bands, rounded card stacks, and command/KPI
  chrome remain dominant
- list/form content is still wrapped by a product console language rather than
  exposed with native Odoo density and restraint

## Judgment

Judgment: `PARTIAL_PASS_WITH_PRODUCT_GAP`

Interpretation:

- if the goal was “统一自定义 list/form 体系并清理不一致”，then the work has
  materially landed
- if the goal was “让当前自定义视图明显更接近原生 list/form 体验”，then the
  work has not landed strongly enough in user-visible form

## Most Likely Reason User Feels “No Change”

The user-visible dominant layers did not change enough:

- left navigation shell still dominates first impression
- list/form are still framed by non-native hero/card/filter chrome
- density, spacing, and action placement remain unlike native Odoo

So even though internal convergence happened, the perceptual delta against
native remains small from the user’s point of view.

## Recommended Next Step

Do not continue with generic “style polish” first.

Open a dedicated bounded screen task:

- compare `native tree/form skeleton` vs `ListPage/ContractFormPage skeleton`
- classify differences into:
  - must align to native structure
  - acceptable custom shell retention
  - should be removed because it blocks native perception

Priority should be:

1. list/detail top shell density and header chrome
2. action placement and primary/secondary command rhythm
3. container depth and card rounding
4. left rail / app shell interference with native work-area perception

## Scan Result

- status: `PASS_WITH_RISK`
- risk:
  - current evidence proves convergence of custom system, not native parity
  - task-detail route still carries startup latency risk, so current form
    comparison evidence is stronger for project detail than for task detail

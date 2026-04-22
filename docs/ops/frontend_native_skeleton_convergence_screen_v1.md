# Frontend Native Skeleton Convergence Screen v1

## Scope

This screen translates the previous native-vs-custom evidence scan into a
bounded execution screen for the next frontend convergence batch.

Target carriers only:

- `frontend/apps/web/src/pages/ListPage.vue`
- `frontend/apps/web/src/pages/ContractFormPage.vue`

Reference evidence:

- native/custom compare:
  - `artifacts/playwright/iter-2026-04-09-1427/compare_final_truth.json`
  - `native_tree_542_final.png`
  - `custom_tree_542_final.png`
  - `native_form_543_action_final.png`
  - `custom_form_543_action_final.png`
- current high-frequency custom pages:
  - `artifacts/playwright/high_frequency_pages_v2/20260418T184258Z/project-list.png`
  - `artifacts/playwright/high_frequency_pages_v2/20260418T184258Z/project-detail.png`
  - `artifacts/playwright/high_frequency_pages_v2/20260418T184258Z/task-list.png`
  - `artifacts/playwright/high_frequency_pages_v2/20260418T184258Z/task-detail.png`

## Decision

Current state is not “native parity”.

Current state is:

- shared custom shell convergence: yes
- route/contract mainline stability: mostly yes
- user-visible native list/form perception: no

Therefore the next batch should not be called generic UI polish.

It should be treated as:

- `native skeleton convergence`

## Layer Target

- Layer Target: `Frontend page-shell screen`
- Module: `ListPage / ContractFormPage native skeleton convergence`
- Kernel or Scenario: `scenario`
- Reason: reduce the user-visible gap between current custom list/form shells
  and native Odoo work-area perception without reopening backend contract work.

## What Must Align To Native

These are the layers that most strongly block native perception and therefore
must move closer to native structure.

### ListPage

1. Top shell density
   - reduce oversized hero/header treatment
   - avoid large empty summary bands before the table
   - bring first visual focus back to toolbar + table

2. Toolbar rhythm
   - primary/secondary action count should feel native-thin
   - search/filter/sort should read as one compact control strip
   - avoid excessive chip rows before the table

3. Container depth
   - reduce nested rounded cards around toolbar, batch bar, and table
   - table should feel like the main work surface, not one card inside many

4. Table-first perception
   - restore dense work-area reading
   - keep decorative spacing below the threshold where the page reads like a
     dashboard instead of a list view

### ContractFormPage

1. Header chrome
   - reduce dashboard-style hero feeling
   - bring title + status + action line closer to a native form header rhythm

2. Action placement
   - `返回 + 保存` must stay visually obvious and primary
   - KPI/summary cards must not visually outrank core form actions

3. Form work-area density
   - reduce oversized shell spacing above the first editable field group
   - form content must feel like the main surface rather than a card below a
     product dashboard

4. Section container hierarchy
   - reduce card stacking where it hides native form continuity
   - keep tabs/sections readable, but avoid excessive visual segmentation

## What May Remain Custom

These custom traits are acceptable if they do not dominate first impression.

1. Brand shell
   - left rail and product shell may remain
   - but they must not overpower list/form work-area perception

2. Token language
   - color, border radius, and typography system may stay custom
   - only if structure and density move closer to native usage patterns

3. Summary/meta aids
   - compact summary strips or semantic aids may remain
   - only when they are subordinate to the table/form body

## What Should Be Removed Or Significantly Weakened

1. Large dashboard-like hero blocks on ordinary list/form pages
2. Multiple stacked container layers before the main work area
3. Over-wide spacing that lowers list/form information density
4. Decorative chrome that outranks the actual editable/list content

## Execution Priority

The next implementation batch should follow this order:

1. `ListPage` top shell and toolbar density
2. `ListPage` container depth around table/batch/filter areas
3. `ContractFormPage` header/action density
4. `ContractFormPage` section/container depth above first field groups

## Not In Scope

1. backend contract changes
2. route/bootstrap performance changes
3. task-detail startup latency
4. non-list/form pages such as dashboard/workbench/home
5. global token redesign

## Acceptance For Next Batch

The next implementation batch should be accepted only if new screenshots show:

1. list pages visually read table-first within one screen
2. form pages visually read action-and-fields-first within one screen
3. header chrome no longer dominates over list/form content
4. container depth is visibly reduced relative to the current screenshots

## Result

- screen status: `PASS`
- next task type: `implementation`
- next task suggestion:
  - `FE-LIST-FORM-NATIVE-SKELETON-CONVERGENCE-IMPLEMENT`

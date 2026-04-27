# Business Fact Systematic Button Label Audit Batch - 2026-04-27

## Scope

- Layer Target: `Domain/UI business fact page surface`
- Module: `smart_construction_core`, `smart_construction_scene`
- Reason: button labels can be rendered from multiple sources, so checking only `<button string>` is insufficient.

## Audit Method

The database view audit scanned all `smart_construction*` form/tree/kanban views and checked:

- `<button string="...">`
- descendant nodes under buttons with `@string`, including `statinfo`
- field metadata labels for fields rendered inside buttons
- visible text nodes inside buttons
- buttons without visible labels and without icons

## Findings Before Fix

Core module audit found 4 visible English label sources and 0 missing-label buttons:

- `project.material.plan`: purchase order statistic button used field metadata `Purchase Order Count`
- `project.material.plan`: purchase line statistic button used field metadata `Purchase Line Count`
- `project.project`: task statistic button still depended on field metadata `Open Task Count`
- `project.project`: status statistic area still depended on field metadata `Last Update Status`

Full `smart_construction*` audit additionally found 2 English wizard buttons:

- `smart_construction_scene.view_sc_scene_governance_wizard_form`: `Execute`
- `smart_construction_scene.view_sc_scene_governance_wizard_form`: `Cancel`

## Changes

- Added Chinese field metadata labels for material plan statistic counters:
  - `purchase_order_count`: `采购单`
  - `purchase_line_count`: `采购明细`
- Added Chinese setup labels for inherited project statistic fields:
  - `open_task_count`: `任务`
  - `last_update_status`: `项目状态`
- Localized scene governance wizard footer buttons:
  - `Execute` -> `执行`
  - `Cancel` -> `取消`

## Verification

- `python3 -m py_compile addons/smart_construction_core/models/core/material_plan.py addons/smart_construction_core/models/core/project_core.py`
- `git diff --check`
- `make mod.upgrade MODULE=smart_construction_core`
- `make mod.upgrade MODULE=smart_construction_scene`
- Full `smart_construction*` button audit:
  - `SC_ALL_BUTTON_VISIBLE_ENGLISH_COUNT=0`
  - `SC_ALL_BUTTON_MISSING_LABEL_COUNT=0`
- `make restart`
- `E2E_LOGIN=wutao E2E_PASSWORD=123456 make verify.menu.navigation_snapshot.container`
  - `PASS checked=139 scenes=16 trace=6cb9f7518046`

## Result

PASS. Button label normalization is now checked across direct button labels, statinfo labels, button field metadata, text nodes, and missing-label buttons for all `smart_construction*` views.

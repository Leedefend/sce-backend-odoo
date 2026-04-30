# Frontend Native List Alignment Batch 20260430

## Scope

- Layer Target: Backend Tree/Search Contract + Frontend Generic List Renderer
- Module: `addons/smart_core`, `frontend/apps/web`
- User: `wutao`
- Database: `sc_prod_sim`
- Typical page: project list, action `506`

## Checklist

| ID | Gap | Status | Evidence |
| --- | --- | --- | --- |
| L1 | `views.tree.columns_schema` was produced by parser but stripped before `ui.contract`, forcing frontend to infer column widget/label. | Fixed | `ui.contract action_id=506` returns `views.tree.columns_schema` count `8`. |
| L2 | Project favorite column was rendered by frontend name fallback and hardcoded favorite copy. | Fixed | Contract returns `is_favorite` first with `widget=boolean_favorite`; browser renders star buttons before project name. |
| L3 | Project list column order did not carry favorite before project name as a contract decision. | Fixed | `views.tree.columns=["is_favorite","name","user_id","partner_id","stage_id","lifecycle_state","date_start","date"]`. |
| L4 | Row decorations from native tree are present in parser output but not yet consumed visually by the list renderer. | Not applicable for action 506 | `project.project` action `506` current native tree has no `decoration-*`; `views.tree.row_classes=[]`. |
| L5 | Search/group/list toolbar copy still contained frontend-local wording. | Fixed first pass | Backend returns `search.ui_labels`; `ActionSurfaceToolbar` consumes labels for search placeholder, menu title/empty states, custom filter controls, saved filters, group, sort, create. |
| L6 | Row open behavior was frontend-default navigation and row action label stayed generic `Open`. | Fixed | `views.tree.row_actions[0]` now has `label=打开`, `trigger=row_click`, `display_mode=row_click`; frontend row click checks this contract before navigation. |
| L7 | List body still carried frontend-local labels for loading/error, pagination, selection, grouped rows, and column picker/save state. | Fixed | Backend `search.ui_labels` now includes list-body labels; `ListPage` consumes `uiLabels` via `ActionView` and only keeps fallbacks for compatibility. |
| L8 | Status badge rendering was inferred by frontend field-name matching (`state/status/stage`). | Fixed | Backend `columns_schema` marks `cell_role=status`; `ListPage` renders status badges only from column contract/list profile. |
| L9 | Status cell display text/tone still came from frontend generic value mapping, producing `in_progress -> 进行中` instead of native selection label `在建`. | Fixed | Backend `columns_schema.selection` and `tone_by_value` drive display text/tone; `ListPage` no longer uses `semanticValueByField`. |
| L10 | Grouped list controls used frontend-local sample limits/sort semantics, and route sync dropped `group_by`, causing grouped pages to loop in loading. | Fixed | Backend `list_profile.grouping` defines sample limits and sort semantics; route sync preserves `group_by`; api.data group fingerprint ignores volatile route cursor fields. |
| L11 | Route preset restore still normalized grouped-list sample/sort with frontend-local defaults. | Fixed | Route preset runtime consumes `list_profile.grouping` for sample limits, default sample size, sort directions, and default direction. |
| L12 | Grouped-list runtime interactions and URL sync still used local default omission semantics for sample size/sort. | Fixed | Sample-limit transition, sort transition, and list route sync now consume `list_profile.grouping` defaults and allowed values. |
| L13 | Search custom filter/group/favorite entry labels still had frontend-local defaults as the primary source. | Fixed | Backend `search.ui_labels` now includes `custom_filter`, `custom_group`, and `favorite_save`; frontend consumes these labels through `customSearchCapabilities.uiLabels`. |
| L14 | Scoped project metrics derived status/amount from frontend field-name scans and Chinese completion keywords. | Fixed | Backend `semantic_page.list_semantics` supplies `status_field` and `metric_fields`; frontend metrics consume status selection/tone and metric fields from contract only. |
| L15 | Active/assignee/scope batch semantics were still vulnerable to frontend field-map checks such as `active`/`user_id`. | Fixed | Backend `list_profile.batch_policy` supplies `active_field`, `assignee_field`, assignee lookup, delete mode, and allowed actions; frontend consumes that policy only. |
| L16 | Batch archive/activate execution still needed to prove it used governed active semantics and returned user-visible feedback. | Fixed | Real browser executed `批量归档` and `批量激活`; `api.data.batch` returned success/failure counts and page feedback stayed visible. |
| L17 | Selection action bar mixed business action buttons and generic permission facts into row selection actions. | Fixed | Selection bar is driven only by `batch_policy.available_actions`; `permissions.effective.rights` remains an audit/governance input, not a frontend action source. |
| L18 | Same-model multi-action entries were not governed consistently: action `589` defaulted to kanban but also exposed tree/list, so list selection under that action only had `清空`. | Fixed, then retired by business fact cleanup | `_is_model_tree_contract` covered same-model tree/list surfaces; the duplicate action `589` was later removed from business facts, leaving canonical action `506`. |
| L19 | Favorite column and favorite writeback still had residual frontend field-name assumptions. | Fixed | Frontend no longer injects `is_favorite` from `fields`; backend `columns_schema[is_favorite].mutation` defines the generic write operation; browser verified favorite toggle round-trip and batch bar remains governed. |
| L20 | Backend contract still exposed native/system copy such as `在仪表板上显示项目` and `显示名称` to business users. | Fixed | Contract governance normalizes `is_favorite` to `我的收藏` and `display_name` to `名称`; list and relation dialog browser checks confirm the technical copy is absent. |

## Verification

- `python3 -m py_compile addons/smart_core/utils/contract_governance.py addons/smart_core/app_config_engine/models/app_view_config.py addons/smart_core/app_config_engine/models/contract_mixin.py 'addons/smart_core/app_config_engine/services/view_Parser/parsers Tree Form.py'` -> PASS
- `pnpm --dir frontend/apps/web run typecheck` -> PASS
- `make restart` with prod-sim env -> PASS; Odoo healthy on `18069`
- `ui.contract action_id=506` -> PASS; `columns_schema[is_favorite].widget=boolean_favorite`
- `ui.contract action_id=506` -> PASS; `search.ui_labels` includes `view_switch/search_placeholder/filters/saved_filters/group_by/sort/create/select_field/select_value/add/cancel/save`
- `ui.contract action_id=506` -> PASS; `row_actions[0]={name:open_form,label:打开,trigger:row_click,display_mode:row_click,payload.view_mode:form}`
- Real browser `http://127.0.0.1:5174/a/506?menu_id=0&db=sc_prod_sim` -> PASS:
  - headers after L20: `我的收藏`, `项目名称`, `项目经理`, `业主单位`, `当前阶段`, `项目执行阶段`, `开始日期`, `结束日期`
  - row count: `80`
  - favorite buttons: `80`
  - favorite button title/aria after L20: `我的收藏`
  - hardcoded `已收藏`: absent
  - console/page errors: `0`
  - screenshot: `artifacts/playwright/screenshots/project_list_alignment_l1.png`
- Real browser toolbar labels -> PASS:
  - toolbar labels: `视图`, `排序`
  - search placeholder: `搜索关键字`
  - search dropdown titles: `筛选`, `分组方式`, `收藏夹`
  - saved filter empty state: `暂无收藏`
  - custom filter panel contains `选择字段`, `添加`, `取消`
  - create button: `新建`
  - console/page errors: `0`
  - screenshot: `artifacts/playwright/screenshots/project_list_toolbar_labels_l5.png`
- Real browser row action -> PASS:
  - before: `http://127.0.0.1:5174/a/506?menu_id=0&db=sc_prod_sim`
  - after first row click: `http://127.0.0.1:5174/r/project.project/64?menu_id=0&action_id=506`
  - form statusbar count: `7`
  - console/page errors: `0`
  - screenshot: `artifacts/playwright/screenshots/project_list_row_action_l6.png`
- L7 static checks -> PASS:
  - `python3 -m py_compile addons/smart_core/utils/contract_governance.py`
  - `pnpm --dir frontend/apps/web run typecheck`
  - `git diff --check`
- L7 contract probe -> PASS:
  - `load_view project.project tree` as `wutao/123456/sc_prod_sim`
  - missing `search.ui_labels` keys: `[]`
  - sample keys include `loading_list`, `pagination_prev`, `pagination_next`, `pagination_jump`, `pagination_page`, `record_count`, `selected_count`, `grouped_result`, `column_picker`, `column_reset`, `column_save_error`
- Real browser list-body labels -> PASS:
  - `http://127.0.0.1:5174/a/506?menu_id=0&db=sc_prod_sim`
  - column picker button: `列`
  - pagination page text: `第 1 / n 页`
  - pagination summary: `共 n 条`
  - pagination actions: `上一页`, `下一页`, `跳转`
  - hardcoded `已收藏`: absent
  - console/page errors: `0`
  - screenshot: `artifacts/playwright/screenshots/project_list_internal_labels_l7.png`
- Note:
  - `verify.portal.view_contract_shape.container MVP_VIEW_TYPE=tree` failed with `layout assertion failed`; this generic shape smoke expects layout-style form coverage and is not the L7 label gate. L7 used a targeted `load_view(tree)` contract probe and real browser check instead.
- L8 contract probe -> PASS:
  - `views.tree.columns_schema[lifecycle_state].cell_role=status`
  - `views.tree.columns_schema[is_favorite].cell_role=favorite`
  - `list_profile.status_field=lifecycle_state`
  - `search.ui_labels.group_sort_desc=按数量降序`
  - `search.ui_labels.group_sort_asc=按数量升序`
- Real browser status cell role -> PASS:
  - `http://127.0.0.1:5174/a/506?menu_id=0&db=sc_prod_sim`
  - status badge count: `80`
  - first status text: `进行中`
  - console/page errors: `0`
  - screenshot: `artifacts/playwright/screenshots/project_list_status_cell_role_l8.png`
- L9 contract probe -> PASS:
  - `views.tree.columns_schema[lifecycle_state].selection[in_progress].label=在建`
  - `views.tree.columns_schema[lifecycle_state].tone_by_value.in_progress=info`
- Real browser display semantics -> PASS:
  - `http://127.0.0.1:5174/a/506?menu_id=0&db=sc_prod_sim`
  - status badge count: `80`
  - first status text: `在建`
  - first status class: `status-badge tone-info`
  - console/page errors: `0`
  - screenshot: `artifacts/playwright/screenshots/project_list_display_semantics_l9.png`
- L10 contract/API probe -> PASS:
  - `list_profile.grouping.sample_limits=[3,5,8]`
  - `list_profile.grouping.sort.key=count`
  - `list_profile.grouping.sort.default_direction=desc`
  - `api.data grouped_rows=2` for `group_by=lifecycle_state`
- Real browser grouped list -> PASS:
  - `http://127.0.0.1:5174/a/506?menu_id=0&db=sc_prod_sim&group_by=lifecycle_state`
  - final URL preserves `group_by=lifecycle_state`
  - grouped blocks: `2`
  - sample limit options: `每组 3 条`, `每组 5 条`, `每组 8 条`
  - sort toggle: `按数量降序 -> 按数量升序`
  - api.data group fingerprint unique count: `1`
  - console/page errors: `0`
  - screenshot: `artifacts/playwright/screenshots/project_list_grouping_contract_l10.png`
- Frontend restart for prod-sim validation -> PASS:
  - command: `FRONTEND_PROFILE=prod-sim make frontend.restart`
  - frontend URL: `http://127.0.0.1:5174/`
  - proxy target: `http://localhost:18069`
  - default frontend DB: `sc_prod_sim`
  - note: using default `frontend.restart` starts `daily/sc_demo` and is not valid for prod-sim browser acceptance.
- L11 static checks -> PASS:
  - `pnpm --dir frontend/apps/web run typecheck`
  - `python3 -m py_compile addons/smart_core/handlers/api_data.py addons/smart_core/utils/contract_governance.py`
  - `git diff --check`
- Real browser grouped list after frontend prod-sim restart -> PASS:
  - `http://127.0.0.1:5174/a/506?menu_id=0&db=sc_prod_sim&group_by=lifecycle_state`
  - sample limit options: `每组 3 条`, `每组 5 条`, `每组 8 条`
  - sort toggle: `按数量降序 -> 按数量升序`
  - final URL preserves `group_by=lifecycle_state` and syncs `group_sort=asc`
  - `group_fp` stable: `31ceecc639e63a6b29fa1c155d43ace2a0aab37c`
  - console/page errors: `0`
  - screenshot: `artifacts/playwright/screenshots/project_list_grouping_contract_l11.png`
- L12 static checks -> PASS:
  - `pnpm --dir frontend/apps/web run typecheck`
  - `git diff --check`
- Real browser grouped route interaction after frontend prod-sim restart -> PASS:
  - `FRONTEND_PROFILE=prod-sim make frontend.restart`
  - `http://127.0.0.1:5174/a/506?menu_id=0&db=sc_prod_sim&group_by=lifecycle_state`
  - sample limit options from contract: `每组 3 条`, `每组 5 条`, `每组 8 条`
  - selecting sample `5` syncs `group_sample_limit=5`
  - selecting contract default sample `3` removes `group_sample_limit`
  - sorting ascending syncs `group_sort=asc`
  - returning to contract default sort `desc` removes `group_sort`
  - console/page errors: `0`
  - screenshot: `artifacts/playwright/screenshots/project_list_group_route_contract_l12.png`
- L13 static checks -> PASS:
  - `python3 -m py_compile addons/smart_core/utils/contract_governance.py`
  - `pnpm --dir frontend/apps/web run typecheck`
  - `git diff --check`
- Real browser search custom labels -> PASS:
  - backend restarted with prod-sim env so `search.ui_labels` changes are loaded
  - `http://127.0.0.1:5174/a/506?menu_id=0&db=sc_prod_sim`
  - opened search menu via aria label `展开搜索菜单`
  - contract response contains `custom_filter`, `custom_group`, `favorite_save`
  - rendered labels: `添加自定义筛选`, `添加自定义分组`, `加入收藏`
  - console/page errors: `0`
  - screenshot: `artifacts/playwright/screenshots/project_list_search_custom_labels_l13.png`
- L14 static checks -> PASS:
  - `python3 -m py_compile addons/smart_core/utils/contract_governance.py`
  - `pnpm --dir frontend/apps/web run typecheck`
  - `git diff --check`
  - source scan confirms metric runtime no longer references `semanticStatus`, `stage_id/state/status/kanban_state/health_state`, amount field-name candidates, or Chinese completion keywords.
- Real browser scoped metric contract -> PASS:
  - backend restarted with prod-sim env so `semantic_page.list_semantics.metric_fields` changes are loaded
  - `http://127.0.0.1:5174/a/506?menu_id=0&db=sc_prod_sim`
  - `semantic_page.list_semantics.status_field=lifecycle_state`
  - `semantic_page.list_semantics.metric_fields=[contract_income_total,contract_amount,dashboard_invoice_amount,budget_total]`
  - page loaded with project rows and status labels
  - console/page errors: `0`
  - screenshot: `artifacts/playwright/screenshots/project_list_metric_contract_l14.png`
- L15 static checks -> PASS:
  - `python3 -m py_compile addons/smart_core/utils/contract_governance.py`
  - `pnpm --dir frontend/apps/web run typecheck`
  - `git diff --check`
  - source scan confirms list runtime no longer uses `fieldMapRaw`, `'active' in fieldMap`, `'user_id' in fieldMap`, or hardcoded `['active', '=', ...]` for the project list active filter/scope path.
- Real browser batch policy contract -> PASS:
  - backend restarted with prod-sim env and frontend restarted with `FRONTEND_PROFILE=prod-sim`
  - `http://127.0.0.1:5174/a/506?menu_id=0&db=sc_prod_sim`
  - `list_profile.batch_policy.active_field=active`
  - `list_profile.batch_policy.assignee_field=user_id`
  - `list_profile.batch_policy.assignee_options.model=res.users`
  - `list_profile.batch_policy.available_actions=[archive,activate]`
  - `list_profile.batch_policy.delete_mode=none`
  - page loaded with project rows
  - console/page errors: `0`
  - screenshot: `artifacts/playwright/screenshots/project_list_batch_policy_l15.png`
- L16 static checks -> PASS:
  - `python3 -m py_compile addons/smart_core/utils/contract_governance.py`
  - `pnpm --dir frontend/apps/web run typecheck`
  - `git diff --check`
  - source scan confirms batch idempotency extra no longer hardcodes `{active: ...}` and uses `batch_policy.active_field`.
- Real browser batch action execution -> PASS:
  - backend restarted with prod-sim env and frontend restarted with `FRONTEND_PROFILE=prod-sim`
  - user: `wutao`
  - `http://127.0.0.1:5174/a/506?menu_id=0&db=sc_prod_sim&active_filter=active`
  - selected one project row and clicked contract-driven `批量归档`
  - `api.data.batch action=archive requested_ids=[514] succeeded=1 failed=0`
  - result feedback `批量归档完成...` visible after list reload
  - searched the same project in `active_filter=archived`, selected it, and clicked contract-driven `批量激活`
  - `api.data.batch action=activate requested_ids=[514] succeeded=1 failed=0`
  - result feedback `批量激活完成...` visible even when the filtered archived result becomes empty
  - cleanup probe for previous diagnostic records found no remaining archived rows for the recorded names
  - console/page errors: `0`
  - screenshot: `artifacts/playwright/screenshots/project_list_batch_action_l16.png`
- L16 residual:
  - `admin` sees the global batch action because `permissions.effective.rights.write=true`, but a selected project row can still fail with record-level `PERMISSION_DENIED`.
  - This is now user-visible through `api.data.batch` success/failure counts; future work should add record-level executability semantics if Odoo native parity requires disabling per-row or per-selection actions before execution.
- L17 selection action bar correction -> PASS:
  - row selection bar no longer mixes `contractActionButtons` business actions such as `执行结构` into batch actions.
  - selection bar is now driven only by `list_profile.batch_policy.available_actions`.
  - real browser `wutao/123456` selected one active project row.
  - rendered selection bar text: `已选 1 条 / 批量归档 / 批量激活 / 清空`
  - `执行结构` absent.
  - console/page errors: `0`
  - screenshot: `artifacts/playwright/screenshots/project_list_selection_actions_l17.png`
- L17 boundary correction follow-up -> PASS:
  - Removed frontend-side combination of `permissions.effective.rights.write` with `batch_policy`; frontend now renders batch actions directly from `batch_policy`.
  - Backend mirrors governed `batch_policy` to both `list_profile.batch_policy` and `surface_policies.batch_policy` so action-route and scene-route consumers receive the same governed result.
  - Real browser `wutao/123456` checked both entries:
    - `/a/506?menu_id=0&db=sc_prod_sim&active_filter=active`
    - `/s/projects.list?db=sc_prod_sim&active_filter=active`
  - Both entries render selection bar text: `已选 1 条 / 批量归档 / 批量激活 / 清空`.
  - Both entries expose `surface_policies.batch_policy.available_actions=[archive,activate]`.
  - Boundary: `permissions.effective.rights` remains a generic permission fact; `batch_policy` is the governed page-action contract. Frontend must not recompute `batch_policy` from permissions.
- L18 same-model multi-action governance -> PASS:
  - Backend restarted with prod-sim env; frontend restarted with `FRONTEND_PROFILE=prod-sim`.
  - Default action probe `http://127.0.0.1:5174/a/589?menu_id=353&action_id=589&db=sc_prod_sim`:
    - `head.view_type=kanban`
    - `views=[kanban,tree,form]`
    - `list_profile.columns=[is_favorite,name,user_id,partner_id,stage_id,lifecycle_state,date_start,date]`
    - `list_profile.batch_policy.available_actions=[archive,activate]`
    - `surface_policies.batch_policy.available_actions=[archive,activate]`
- Real browser list-mode probe `http://127.0.0.1:5174/a/589?menu_id=353&action_id=589&db=sc_prod_sim&view_mode=list`:
    - selected one row as `wutao/123456`
    - selection bar text: `已选 1 条 / 批量归档 / 批量激活 / 清空`
    - `执行结构` absent from `.batch-bar`
    - console/page errors: `0`
    - screenshot: `artifacts/playwright/screenshots/project_list_action589_l18.png`
    - structured result: `artifacts/playwright/screenshots/project_list_action589_l18.json`
- L19 static checks -> PASS:
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile addons/smart_core/utils/contract_governance.py`
  - `pnpm --dir frontend/apps/web run typecheck`
  - source scan confirms `nativeFavoriteColumns`, frontend `fields.is_favorite` injection, `targetModel !== 'project.project'`, `vals: { is_favorite: ... }`, and `row.is_favorite` writeback are absent from the list runtime path.
- L19 contract probe -> PASS:
  - backend restarted with prod-sim env; frontend restarted with `FRONTEND_PROFILE=prod-sim`.
  - `ui.contract action_id=506` returns `views.tree.columns_schema[is_favorite].mutation={type: field_toggle, operation: record_write, field: is_favorite, value_type: boolean}`.
- Real browser favorite/list action contract -> PASS:
  - user: `wutao`
  - `http://127.0.0.1:5174/a/506?menu_id=353&action_id=506&db=sc_prod_sim&active_filter=active`
  - row count: `80`
  - favorite buttons: `80`
  - favorite toggle round-trip: `favorite-toggle -> favorite-toggle active -> favorite-toggle`
  - rendered headers after L20: `我的收藏`, `项目名称`, `项目经理`, `业主单位`, `当前阶段`, `项目执行阶段`, `开始日期`, `结束日期`
  - selected-row bar: `已选 1 条 / 批量归档 / 批量激活 / 清空`
  - `执行结构` absent from `.batch-bar`
  - console/page errors: `0`
  - screenshot: `artifacts/playwright/screenshots/project_list_contract_favorite_l19.png`
- L20 static checks -> PASS:
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile addons/smart_core/utils/contract_governance.py addons/smart_core/tests/test_contract_governance_project_form.py`
  - `pnpm --dir frontend/apps/web run typecheck`
  - local governance probe confirms `fields.is_favorite.string=我的收藏`, `fields.display_name.string=名称`, `columns_schema[is_favorite].label=我的收藏`, `columns_schema[display_name].label=名称`.
  - `python3 -m unittest ...test_list_business_labels_override_native_technical_copy` is blocked in this repo shell by `addons.smart_core.tests.__init__` importing Odoo (`ModuleNotFoundError: No module named 'odoo'`); the equivalent isolated governance probe passed.
- Real browser business label contract -> PASS:
  - backend restarted with prod-sim env; frontend restarted with `FRONTEND_PROFILE=prod-sim`.
  - user: `wutao`
  - list URL: `http://127.0.0.1:5174/a/506?menu_id=353&action_id=506&db=sc_prod_sim&active_filter=active`
  - list headers: `我的收藏`, `项目名称`, `项目经理`, `业主单位`, `当前阶段`, `项目执行阶段`, `开始日期`, `结束日期`
  - `ui.contract columns_schema[is_favorite].label=我的收藏`
  - page body contains no `在仪表板上显示项目` and no `显示名称`
  - project detail relation search-more dialog headers: `名称`, `完整名称`, `工作职位`, `电话`, `手机`, `电子邮件`
  - relation dialog contains no `显示名称`
  - console/page errors: `0`
  - screenshot: `artifacts/playwright/screenshots/project_list_business_labels_l20.png`

## L21 Relation Inline Create Save Boundary

- Contract boundary -> PASS:
  - `relation_entry.inline_create` is backend-owned and exposes `enabled`, `create_on_no_match`, `match`, `name_field`, `value_source`, and `reason_code`.
  - Inline create label is now `保存时创建“%s”`, so the UI does not imply creation happens on input/blur.
  - Frontend stores unmatched many2one text as pending input and only resolves it during the main form save path.
- Static checks -> PASS:
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile addons/smart_core/app_config_engine/services/assemblers/page_assembler.py addons/smart_core/utils/contract_governance.py`
  - `pnpm --dir frontend/apps/web run typecheck`
- Runtime checks -> PASS:
  - backend restarted with prod-sim env; frontend restarted with `FRONTEND_PROFILE=prod-sim`.
  - user: `wutao`
  - project detail: `project.project/750`
  - typed unmatched customer `保存时创建客户 1777524530565`
  - before save: `beforeInputCreates=0`, `afterInputCreates=0`, save button enabled, inline hint `保存时创建“保存时创建客户 1777524530565”`.
  - on save: exactly one `api.data op=create model=res.partner` was emitted in phase `save`, followed by project `partner_id=8057`.
  - cleanup: project `partner_id` restored to `false`; partner `8057` removed through `make odoo.shell.exec` with `env.cr.commit`; follow-up search `remaining_save_time_partners=0`.
  - screenshot: `artifacts/playwright/screenshots/project_relation_save_time_create_l22.png`
- Negative-path check -> PASS:
  - project detail `project.project/771` has invalid historical one2many contract lines.
  - save was blocked by main form validation before relation create; no `res.partner create` was emitted.
  - conclusion: pending relation create follows successful main form save flow and does not pollute data when the main save is rejected.

## L22 Relation Quick Input Match Correction

- Behavior correction -> PASS:
  - Quick input no longer requires full label equality before auto-fill.
  - Matching priority is now: exact label match first; otherwise auto-fill only when the search result set has exactly one record.
  - When the search result set has multiple records, frontend does not pick the first row, does not show the save-time-create hint, and does not create a new relation record on save.
- Static checks -> PASS:
  - `pnpm --dir frontend/apps/web run typecheck`
  - `git diff --check -- frontend/apps/web/src/pages/ContractFormPage.vue`
- Real browser unique-match check -> PASS:
  - user: `wutao`
  - project detail: `project.project/750`
  - temporary partner: `快速输入唯一客户 1777525200`
  - typed keyword: `快速输入唯一客户`
  - input auto-filled full label `快速输入唯一客户 1777525200`
  - create calls during input: `0`
  - cleanup: temporary partner `8058` removed through `make odoo.shell.exec` with `env.cr.commit`.
- Real browser multi-match check -> PASS:
  - typed keyword: `四川`
  - input remained `四川`
  - inline create hint count: `0`
  - save opened relation search dialog with `120` rows.
  - validation message: `客户存在多个匹配记录，请选择具体记录`
  - create calls after save: `0`
  - console errors: `0`

## Contract Boundary

Frontend list rendering must consume `views.tree.columns_schema`, `views.tree.row_actions`, `list_profile`/`semantic_page.list_semantics`, and `search.ui_labels`; it must not decide business semantics from field names, values, local toolbar/list-body copy, local custom-search entry copy, local route restore defaults, local URL default-omission rules, local grouped-list policy, local status/metric heuristics, local `active/user_id` capability checks, or generic permission facts. Favorite rendering is now a backend contract semantic: `widget=boolean_favorite`; favorite writeback is now a backend contract semantic: `columns_schema[].mutation`; business-facing labels are backend contract semantics and must be normalized before reaching the frontend (`is_favorite=我的收藏`, `display_name=名称`). Status badge rendering is now a backend contract semantic: `cell_role=status`; status display text/tone now comes from `selection` and `tone_by_value`; grouped list controls, interactions, route restore, and URL sync now come from `list_profile.grouping`; scoped metrics now use `status_field`, `metric_fields`, and backend tone semantics; batch active/assignee/scope/action semantics now use `list_profile.batch_policy`. `permissions.effective.rights` remains a backend-delivered permission fact for audit/diagnostics and backend governance inputs; frontend must not combine it with `batch_policy` to create or remove page actions.

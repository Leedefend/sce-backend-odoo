# List Search Group Usability Audit 20260501

## Scope

- Layer Target: unified list search/group usability audit
- Module: `frontend/apps/web/src/pages/ListPage.vue`, `scripts/verify`
- Specimen: `project.project` action `506`, menu `353`, user `wutao`, db `sc_prod_sim`
- Rule: frontend consumes backend search/group contract; it must not invent filter/group semantics.

## Finding

The first real browser audit exposed a grouped-list usability defect:

- Search dropdown sections were available from backend contract.
- Search typing and search clear were usable.
- Selecting a group updated the URL with `group_by=manager_id`.
- After grouped rows loaded, the page still rendered the flat list table below grouped results.

This made the page show grouped and ungrouped results at the same time, unlike native grouped list behavior.

Failure artifact:

- `artifacts/list-search-group-usability/20260501T020944/summary.json`

## Fix

- `ListPage.vue` now treats grouped rows as a mutually exclusive view state.
- When `enableGroupedRows=true` and grouped rows exist:
  - render grouped results;
  - do not render the flat table;
  - do not render flat list pagination controls.

No backend contract or business semantics were changed.

## Verification

- `node --check scripts/verify/list_search_group_usability_audit.js`: PASS
- `pnpm --dir frontend/apps/web run typecheck`: PASS
- Real browser audit:
  - `artifacts/list-search-group-usability/20260501T030648/summary.json`
  - `LSG-P01`: search dropdown exposes filter/group/favorite sections
  - `LSG-P02`: typing search reloads list and syncs route state
  - `LSG-P03`: clear search removes route search and restores non-empty list
  - `LSG-P04`: group selection shows grouped result and syncs `group_by`
  - `LSG-P05`: grouped view does not render duplicate flat table
  - `LSG-P06`: clear group removes grouped route state and restores flat table
  - `LSG-P07`: custom filter panel opens and cancels without route mutation
  - `LSG-P08`: custom filter apply creates a visible facet and reloads without error
  - `LSG-P09`: grouped list survives browser reload and browser back remains recoverable
  - `LSG-P10`: custom group selector applies grouped view and can be cleared
  - `LSG-P11`: grouped result supports per-group pagination with route state
  - `LSG-P12`: saving current search creates a usable visible favorite filter
  - console errors: `0`
- `git diff --check`: PASS
- Frontend restart:
  - `FRONTEND_PROFILE=prod-sim make frontend.restart`: PASS, URL `http://127.0.0.1:5174/`

## Decision Notes

- Search/filter/group state changes currently sync route state through replace-style navigation.
- Therefore browser Back is not guaranteed to step through every search/group state inside the same action page.
- This batch only requires grouped-route reload recovery and non-error Back recovery. If product wants browser Back to return to the previous list state, that is a separate route-history policy batch.

## Follow-Up Matrix

Next audit batches should cover:

- applying the same search/group audit to M2/M3/M4/M5 representative list actions;
- route history policy if product requires browser Back to step through each list state;
- saved filter delete/rename behavior when that capability is contracted;

## Batch-C Closure

Use-level blockers found and closed:

- `group_page` keys can contain encoded separators; route parsing now preserves both encoded and decoded keys so grouped page offsets are not dropped during reload.
- grouped per-group pagination now re-applies the backend page payload after route sync, with key-first and label-fallback matching, so a user is not bounced back to page 1 after clicking next.
- saving a favorite search now refreshes `ui.contract` before the list reload returns, so the saved favorite is visible when the user reopens the search menu.

Data hygiene:

- Real browser validation created temporary `ir.filters` names under `LSG-AUDIT-*`.
- All temporary favorites were removed from `sc_prod_sim` through `make odoo.shell.exec` with explicit `env.cr.commit()`.

## Batch-D Closure

Search trigger usability was tightened:

- typing in the toolbar search box only updates the draft input;
- pressing Enter or clicking the contracted `search_submit` button is required before route state and list data reload;
- composition input no longer submits on `compositionend`, so Chinese keyword entry is not interrupted by intermediate reloads;
- clearing search remains an explicit action.

Verification:

- `artifacts/list-search-group-usability/20260501T033600/summary.json`
- `LSG-P02`: PASS, draft input does not add `search` to the URL; explicit submit adds `search=德阳` and reloads
- `LSG-P01` through `LSG-P12`: PASS
- console errors: `0`
- Temporary `LSG-AUDIT-*` favorites removed from `sc_prod_sim`; remaining count `0`.

## Batch-E Closure

All unified list tables now render a page-local row number as the first visible column:

- backend `search.ui_labels.row_number` supplies the header text `序号`;
- flat list rows render `1..n` for the current visible page;
- grouped list rows render one continuous sequence across visible group sample rows;
- the selector checkbox column, favorite column, and business columns remain after the row number column;
- no business field order is rewritten and no sequence is persisted to ORM data.

Verification:

- `artifacts/list-search-group-usability/20260501T035525/summary.json`
- `LSG-P00`: PASS, flat list first header is `序号` and first visible row number is `1`
- `LSG-P04`: PASS, grouped list first header is `序号` and visible grouped row numbers are continuous
- `LSG-P01` through `LSG-P12`: PASS
- console errors: `0`
- Route clear race found while validating grouped facets was fixed by awaiting route replacement before list reload.
- Temporary `LSG-AUDIT-*` favorites removed from `sc_prod_sim`; remaining count `0`.

## Batch-F Closure

Unified list tables now support page-level list operation affordances:

- business column headers are clickable and submit backend `order` route state;
- the active sort column shows a direction indicator while the row-number column remains fixed and non-sortable;
- visible business columns can be drag-reordered, with the order stored in `sc.user.view.preference` as `column_order`;
- column visibility and column order share the same list preference scope, so refresh/navigation can restore the user layout;
- a list footer renders current-page row count and sums every visible numeric column whose backend column contract declares `integer`, `float`, or `monetary`;
- the frontend does not infer business semantics for summaries: numeric aggregation is generic and based on backend column type only.

Verification:

- `artifacts/list-search-group-usability/20260501T041421/summary.json`
- `LSG-P13`: PASS, clicking a column header toggles `order=<field> asc` then `order=<field> desc` and reloads without error
- `LSG-P14`: PASS, dragging columns changes the visible business-column order and keeps the first `序号` column fixed
- `LSG-P15`: PASS, list footer shows `页面统计` and current-page row count; numeric summary cards render when visible numeric columns exist
- `LSG-P00` through `LSG-P12`: PASS
- console errors: `0`

Data hygiene:

- Temporary `LSG-AUDIT-*` favorites removed from `sc_prod_sim`; remaining count `0`.
- The validation-created `sc.user.view.preference` row for `wutao` / `list_columns:list:action:506` was removed after the drag-order test; remaining count `0`.

## Batch-G Closure

Two user-level list operability gaps were closed:

- selecting/copying text inside list body cells no longer opens the record row;
- body cells explicitly allow text selection while existing row-click navigation still works when there is no active text selection;
- list column widths can be adjusted by dragging the resize handle on business column headers;
- column widths are saved in the existing `list_columns` user preference scope as `column_widths`, alongside `visible_columns`, `hidden_columns`, and `column_order`;
- the resize handle uses the contracted label `column_resize=调整列宽`.

Verification:

- `artifacts/list-search-group-usability/20260501T062019/summary.json`
- `LSG-P16`: PASS, selecting text in a list cell keeps the current list URL and does not trigger row navigation
- `LSG-P17`: PASS, dragging a column resize handle changes the visible column width
- `LSG-P00` through `LSG-P15`: PASS
- console errors: `0`

Data hygiene:

- Temporary `LSG-AUDIT-*` favorites removed from `sc_prod_sim`; remaining count `0`.
- The validation-created `sc.user.view.preference` row for `wutao` / `list_columns:list:action:506` was removed after the resize test; remaining count `0`.

## Batch-H Closure

Unified list table usability was extended for scrolling, fixed row numbers, plain text search, page size control, and aligned totals:

- table headers are sticky while the user scrolls the page;
- the `序号` column remains sticky at the left edge and row-number values are centered;
- a plain list search input was added for direct keyword entry while the existing search menu, filters, groups, and favorites remain unchanged;
- pagination accepts a user-entered page size and reloads from the first page;
- `api.data` now supports `need_aggregates` and returns backend-computed numeric field sums for the active list domain;
- list totals moved into table `tfoot` rows so current-page totals and backend grand totals align under their data columns.

Verification:

- `artifacts/list-search-group-usability/20260501T065437/summary.json`
- `LSG-P15`: PASS, table footer renders aligned `当前页合计` and `总计` rows
- `LSG-P18`: PASS, table body scrolls inside `section.table`; after `tableScrollTop=420`, header remains at the table top with `headerDeltaFromTableTop=0`, fixed-left row-number column, centered row-number data
- `LSG-P19`: PASS, plain search input submits keyword search without removing existing search menu/group controls
- `LSG-P20`: PASS, user-entered page size reloads the list and limits visible rows; footer shows current-page row count and backend total count under the first business column
- `LSG-P00` through `LSG-P17`: PASS
- console errors: `0`

Data hygiene:

- Temporary `LSG-AUDIT-*` favorites removed from `sc_prod_sim`; remaining count `0`.
- The validation-created `sc.user.view.preference` row for `wutao` / `list_columns:list:action:506` was removed after column-order/width tests; remaining count `0`.

## Batch-I Correction

The second real-user review found two gaps in Batch-H:

- the prior table header implementation locked the wrong scroll context by making `section.table` the scrolling container; real users scroll the page content, so the table header still failed to stay visible in that path;
- `buildActionViewListRequest` set `need_aggregates=true`, but `frontend/apps/web/src/api/data.ts` did not pass that field through the API payload, so backend numeric totals were never requested by the list page.

Corrections:

- `section.table` is back in the page/content scroll flow, and only `thead th` is sticky;
- `tfoot` is no longer sticky, so page scroll behavior is not confused with footer locking;
- `ApiDataListRequest` and the frontend API payload now include `need_aggregates`;
- `api.data` numeric aggregation now sums stored numeric fields independently, so one non-aggregatable numeric field cannot blank all other totals.

Verification:

- focused browser probe on `/a/506?menu_id=353`: content scroller moved from `0` to `420`, `tableTopAfter=-201`, `afterTop=32`, `headerPosition=sticky`, row-number column `left=0px` and centered;
- focused browser probe on `/a/586?menu_id=336`: request includes `need_aggregates=true`; backend returns `settlement_amount_payable.sum=400` and `amount.sum=6239218333.96`; footer shows current-page `400 / -8,745,417.08` and grand total `400 / 6,239,218,333.96`;
- full list audit: `artifacts/list-search-group-usability/20260501T071748/summary.json`;
- `LSG-P15`: PASS, footer rows align current-page and grand-total summaries under data columns;
- `LSG-P18`: PASS, page/content scroll keeps table header sticky while the table body scrolls away;
- `LSG-P19`: PASS, plain keyword input remains independent from existing search menu/group controls;
- `LSG-P20`: PASS, page size input reloads the page and footer count remains aligned;
- `LSG-P00` through `LSG-P17`: PASS;
- console errors: `0`.

Data hygiene:

- Temporary `LSG-AUDIT-*` favorites removed from `sc_prod_sim`; remaining count `0`.
- The validation-created `sc.user.view.preference` row for `wutao` / `list_columns:list:action:506` was removed; remaining count `0`.

## Batch-J Correction

The follow-up real-user review found two remaining gaps:

- only the row-number column/cells were visibly fixed in the user's scroll path; the expected behavior is that the whole table header row, including the `序号` header, remains locked while rows scroll;
- the contract summary page showed `最终合同价` as a numeric business value, but the table footer did not show current-page and grand-total figures.

Corrections:

- the list table now sets sticky behavior on the whole `thead` row group as well as header cells, so the `序号` header row is locked as one header band;
- frontend list column option resolution now falls back from tree `columns_schema` to backend `fields[name]` metadata for `type`, `widget`, `selection`, and label. This keeps the frontend contract-driven while avoiding lost numeric semantics when a tree schema is incomplete.

Verification:

- contract summary page `/a/536?menu_id=353`: `最终合同价` footer shows current-page `23,974,168.62` and grand total `5,545,250,245.26`;
- contract summary page desktop/content scroll: after scrolling `900px`, `theadTop=32`, `firstHeaderTop=32`, `theadPosition=sticky`;
- contract summary page narrow/window scroll: after `window.scrollY=900`, `theadTop=0`, `headerTop=0`, `.content overflow=visible`;
- project list full audit: `artifacts/list-search-group-usability/20260501T073257/summary.json`;
- `LSG-P18`: PASS, now asserts `headerRowPosition=sticky` and `headerRowTop=0px` in addition to sticky header cells;
- `LSG-P00` through `LSG-P20`: PASS;
- console errors: `0`.

Data hygiene:

- Temporary `LSG-AUDIT-*` favorites removed from `sc_prod_sim`; remaining count `0`.
- The validation-created `sc.user.view.preference` row for `wutao` / `list_columns:list:action:506` was removed; remaining count `0`.

# ActionView Assembler Design v1

## Goal

- Layer Target: `Page Assembly Layer`
- Module: `frontend/apps/web/src/app/assemblers/action/*`, `frontend/apps/web/src/views/ActionView*.vue`
- Reason: move display assembly control from page component to assembler and provide a single `vm` output.

## Delivered in This Wave

- Added:
  - `app/assemblers/action/actionPageVm.ts`
  - `app/assemblers/action/actionPageAdapters.ts`
  - `app/assemblers/action/actionPageSections.ts`
  - `app/assemblers/action/useActionPageModel.ts`
  - `views/ActionViewShell.vue`
- Integrated into: `views/ActionView.vue`
- First action-runtime extraction done: `app/assemblers/action/useActionViewActionRuntime.ts` now owns `runContractAction/applyActionRefreshPolicy` logic (can be moved to runtime layer in next wave).
- Batch runtime extraction done: `app/assemblers/action/useActionViewBatchRuntime.ts` now owns batch action/assign/export/failure handlers; legacy batch handlers are removed from page.
- Selection runtime extraction done: `app/assemblers/action/useActionViewSelectionRuntime.ts` now owns clear/toggle/ifMatch/idempotency glue.
- Trigger runtime extraction done: `app/assemblers/action/useActionViewTriggerRuntime.ts` now owns search/sort/filter trigger plans.
- Grouped rows/route runtime extraction done: `app/assemblers/action/useActionViewGroupedRowsRuntime.ts` now owns grouped page-change/hydrate/route-normalize glue.
- Route preset/sync runtime extraction done: `app/assemblers/action/useActionViewRoutePresetRuntime.ts` now owns route-preset apply/clear/patch/sync glue.
- Filter/group runtime extraction done: `app/assemblers/action/useActionViewFilterGroupRuntime.ts` now owns contract/saved/groupBy apply/clear glue.
- Header runtime extraction done: `app/assemblers/action/useActionViewHeaderRuntime.ts` now owns reload/focus/header action glue.
- Navigation runtime extraction done: `app/assemblers/action/useActionViewNavigationRuntime.ts` now owns workspace/carry/workbench query and row-click glue.
- Request-context runtime extraction done: `app/assemblers/action/useActionViewRequestContextRuntime.ts` now owns filter/context/domain merge wrappers.
- Scoped-metrics runtime extraction done: `app/assemblers/action/useActionViewScopedMetricsRuntime.ts` now owns scoped total/project metrics query loops.
- Contract-shape runtime extraction done: `app/assemblers/action/useActionViewContractShapeRuntime.ts` now owns columns/kanban/advanced/model extraction helpers.
- Action meta/url/window runtime extraction done: `app/assemblers/action/useActionViewActionMetaRuntime.ts` now owns action-type/url/navigation redirect helpers (`getActionType/isClientAction/isUrlAction/resolveNavigationUrl/redirectUrlAction/isWindowAction`).
- Scene identity runtime extraction done: `app/assemblers/action/useActionViewSceneIdentityRuntime.ts` now owns `resolveSceneCode/resolveNodeSceneKey/findMenuNode` helper glue.
- Batch artifact glue runtime extraction done: `app/assemblers/action/useActionViewBatchArtifactGlueRuntime.ts` now owns `downloadCsvBase64/applyBatchFailureArtifacts/handleBatchDetailAction` helper glue.
- Assignee options runtime extraction done: `app/assemblers/action/useActionViewAssigneeRuntime.ts` now owns `loadAssigneeOptions` fetch/permission-warning flow.
- View-mode runtime extraction done: `app/assemblers/action/useActionViewModeRuntime.ts` now owns `viewModeLabel/switchViewMode` helper glue.
- Project-metric/sort runtime extraction done: `app/assemblers/action/useActionViewProjectMetricRuntime.ts` now owns `resolveProjectStateCell/resolveProjectAmount/isCompletedState/resolveDefaultSort` helper glue.
- Contract-action-button mapping runtime extraction done: `app/assemblers/action/useActionViewContractActionButtonRuntime.ts` now owns `toContractActionButton` helper glue.
- Contract-action-grouping runtime extraction done: `app/assemblers/action/useActionViewActionGroupingRuntime.ts` now owns grouping strategy helpers (`resolveContractActionGroups/resolveContractPrimaryActions/resolveContractOverflowActions/resolveContractOverflowActionGroups`).
- Display-computed runtime extraction done: `app/assemblers/action/useActionViewDisplayComputedRuntime.ts` now owns `sortOptions/subtitle/statusLabel/pageStatus/recordCount` computed glue.
- Filter-computed runtime extraction done: `app/assemblers/action/useActionViewFilterComputedRuntime.ts` now owns filter/groupBy computed glue (`contractFilterChips/filterPrimaryBudget/contractSavedFilterChips/contractGroupByChips/activeGroupByLabel`).
- Load-lifecycle runtime extraction done: `app/assemblers/action/useActionViewLoadLifecycleRuntime.ts` now owns `load()` reset/missing-action/catch branches; page keeps the main load orchestration flow only.
- Load-preflight runtime extraction done: `app/assemblers/action/useActionViewLoadPreflightRuntime.ts` now owns `load()` preflight branches (contract/meta/view-mode/route-selection/capability/missing-model/form-redirect); page now consumes structured preflight results only.
- Load-preflight-apply runtime extraction done: `app/assemblers/action/useActionViewLoadPreflightApplyRuntime.ts` now owns preflight continue/blocked state-apply branches; page no longer inlines preflight state writes.
- Load-request runtime extraction done: `app/assemblers/action/useActionViewLoadRequestRuntime.ts` now owns load request building and pre-request branches (fields/domain/context/payload).
- Load-request-guard runtime extraction done: `app/assemblers/action/useActionViewLoadRequestGuardRuntime.ts` now owns request-blocked state-apply branches.
- Load-request-phase runtime extraction done: `app/assemblers/action/useActionViewLoadRequestPhaseRuntime.ts` now owns request execution + blocked-branch orchestration; page consumes phased request result only.
- Load-success-phase runtime extraction done: `app/assemblers/action/useActionViewLoadSuccessPhaseRuntime.ts` now owns success-phase payload assembly handoff; page injects `dynamicInput` while static success dependencies are centralized.
- Load-request-input builder extraction done: `app/assemblers/action/useActionViewLoadRequestInputRuntime.ts` now owns request payload input assembly handoff; page calls `buildLoadRequestInput(...)`.
- Load-success-dynamic-input builder extraction done: `app/assemblers/action/useActionViewLoadSuccessDynamicInputRuntime.ts` now owns success dynamic-input assembly handoff; page calls `buildLoadSuccessDynamicInput(...)`.
- Load-catch-phase runtime extraction done: `app/assemblers/action/useActionViewLoadCatchPhaseRuntime.ts` now owns catch-phase payload assembly handoff; page calls `executeLoadCatchPhase({ input })`.
- Load-preflight-input builder extraction done: `app/assemblers/action/useActionViewLoadPreflightInputRuntime.ts` now owns preflight payload input assembly handoff; page calls `buildLoadPreflightInput(...)`.
- Load-preflight-apply-bound extraction done: `app/assemblers/action/useActionViewLoadPreflightApplyBoundRuntime.ts` now owns preflight blocked/continue bound-apply handoff; page calls `applyLoadPreflightBlocked/Continue(...)`.
- Load-preflight-phase extraction done: `app/assemblers/action/useActionViewLoadPreflightPhaseRuntime.ts` now owns preflight branch orchestration (redirect/handled/blocked/continue); page calls `executeLoadPreflightPhase({ input })`.
- Load-request-blocked-apply extraction done: `app/assemblers/action/useActionViewLoadRequestBlockedApplyRuntime.ts` now owns blocked-apply adapter handoff; page calls `applyLoadRequestBlocked(...)`.
- Load-request-dynamic-input builder extraction done: `app/assemblers/action/useActionViewLoadRequestDynamicInputRuntime.ts` now owns request dynamic payload assembly handoff; page calls `buildLoadRequestDynamicInput(...)`.
- Load-success-phase-input builder extraction done: `app/assemblers/action/useActionViewLoadSuccessPhaseInputRuntime.ts` now owns success-phase dynamic payload assembly handoff; page calls `buildLoadSuccessPhaseInput(...)`.
- Load-main-phase extraction done: `app/assemblers/action/useActionViewLoadMainPhaseRuntime.ts` now owns preflight/request/success orchestration handoff; page calls `executeLoadMainPhase(...)`.
- Load-main-phase closure: `useActionViewLoadMainPhaseRuntime.ts` now also owns catch-branch handoff; page no longer keeps `load()`-level `try/catch` wrapper.
- Load-main-phase-input extraction done: `app/assemblers/action/useActionViewLoadMainPhaseInputRuntime.ts` now owns main-phase payload assembly handoff; page calls `executeLoadMainPhase(buildLoadMainPhaseInput({ startedAt }))`.
- Load-bound execution extraction done: `app/assemblers/action/useActionViewLoadBoundRuntime.ts` now owns begin/main phase dispatch handoff; page `load()` calls `executeLoad()`.
- Load-main-bound execution extraction done: `app/assemblers/action/useActionViewLoadMainBoundRuntime.ts` now owns main-phase bound dispatch handoff; load-bound runtime now depends on `executeLoadMainBound()` instead of direct builder+main-phase coupling.
- Section visibility/style runtime extraction done: `app/assemblers/action/useActionViewSectionRuntime.ts` now owns section visibility/style checks; page template now consumes `isSectionVisible/getSectionStyle` instead of composing `pageSectionEnabled + pageSectionTagIs + pageSectionStyle` inline.
- Template busy/disabled runtime extraction done: `app/assemblers/action/useActionViewTemplateStateRuntime.ts` now owns busy/disabled checks; page template no longer repeats inline `status === 'loading' || batchBusy` and `!btn.enabled` checks and now consumes `isUiBusy/isBusyDisabled/isViewModeDisabled/isContractActionDisabled`.
- Template expand/collapse interaction runtime extraction done: `app/assemblers/action/useActionViewTemplateInteractionRuntime.ts` now owns `showMore*` toggle interactions; page template no longer inlines `showMore* = !showMore*` and now consumes dedicated toggle handlers.
- Text fallback access runtime extraction done: `app/assemblers/action/useActionViewTextRuntime.ts` now owns text fallback access; page template/page script no longer call `pageText(...)` directly and now consume `t(...)`.
- Template UI state runtime extraction done: `app/assemblers/action/useActionViewTemplateUiStateRuntime.ts` now owns `showMoreContractActions/showMoreContractFilters/showMoreSavedFilters` state creation; page no longer directly declares those `ref(false)` states.
- Filter/view UI state runtime extraction done: `app/assemblers/action/useActionViewFilterUiStateRuntime.ts` now owns `activeContractFilterKey/activeSavedFilterKey/contractLimit/preferredViewMode` state creation; page no longer directly declares those refs.
- Page display state runtime extraction done: `app/assemblers/action/useActionViewPageDisplayStateRuntime.ts` now owns `pageTitle/emptyReasonText/showHud/errorMessage` derivation; page no longer inlines those display-state computeds.
- HUD entries assembly runtime extraction done: `app/assemblers/action/useActionViewHudEntriesRuntime.ts` now owns large HUD entries assembly; page no longer inlines a large `hudEntries` array computed and now consumes `buildHudEntries()`.
- HUD entries input assembly runtime extraction done: `app/assemblers/action/useActionViewHudEntriesInputRuntime.ts` now owns HUD input payload assembly; page no longer tightly couples a large inline `staticInput` object directly into HUD entries runtime.
- Surface-intent parsing runtime extraction done: `app/assemblers/action/useActionViewSurfaceIntentRuntime.ts` now owns `contractSurfaceIntent/surfaceIntent` composition; page no longer inlines those semantic composition computeds.
- Advanced-view display parsing runtime extraction done: `app/assemblers/action/useActionViewAdvancedDisplayRuntime.ts` now owns `advancedViewTitle/advancedViewHint` composition; page no longer inlines those advanced display computeds.
- Content-display derivation runtime extraction done: `app/assemblers/action/useActionViewContentDisplayRuntime.ts` now owns `ledgerOverviewItems/listSummaryItems/kanbanTitleField` derivations; page no longer inlines those content display computeds.
- Surface-display derivation runtime extraction done: `app/assemblers/action/useActionViewSurfaceDisplayRuntime.ts` now owns `sortLabel/surfaceKind` derivations; page no longer inlines those surface display computeds.
- Load-begin-input/phase extraction done: `app/assemblers/action/useActionViewLoadBeginInputRuntime.ts` and `app/assemblers/action/useActionViewLoadBeginPhaseRuntime.ts` now own begin/reset payload assembly handoff; page calls `executeLoadBeginPhase({ input })`.
- Load-success runtime extraction done: `app/assemblers/action/useActionViewLoadSuccessRuntime.ts` now owns load success apply/finalize branches (group paging/route sync/project scope/grouped rows/finalize/trace).

## Input

`useActionPageModel` currently consumes:

1. Contract outputs (strict/surface/filter/action/projection)
2. Runtime state (page state/view mode/group summary/hud)
3. Page context (text and route-preset metadata)

## Output

Single `ActionPageVM` output:

- `vm.page`
- `vm.header`
- `vm.filters`
- `vm.focus`
- `vm.strictAlert`
- `vm.groupSummary`
- `vm.actions`
- `vm.content`
- `vm.empty`
- `vm.hud`

## Boundary

Assembler does:

- page display-shape assembly
- section visibility aggregation
- contract/runtime to UI VM adapters

Assembler does not:

- call APIs
- execute mutation/batch flows
- perform route navigation

## Deferred to Next Wave

- full `load()` ownership transfer
- group/window/page-size runtime ownership transfer
- deeper template condition removal via section VM

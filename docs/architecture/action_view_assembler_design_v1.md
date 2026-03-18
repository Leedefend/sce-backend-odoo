# ActionView Assembler 设计方案 v1

## 1. 目标

- Layer Target: `Page Assembly Layer`
- Module: `frontend/apps/web/src/app/assemblers/action/*`、`frontend/apps/web/src/views/ActionView*.vue`
- Reason: 将 ActionView 的展示装配控制权从页面组件迁移至 assembler，建立统一 `vm` 出口。

## 2. 本轮落点

- 新增：
  - `frontend/apps/web/src/app/assemblers/action/actionPageVm.ts`
  - `frontend/apps/web/src/app/assemblers/action/actionPageAdapters.ts`
  - `frontend/apps/web/src/app/assemblers/action/actionPageSections.ts`
  - `frontend/apps/web/src/app/assemblers/action/useActionPageModel.ts`
  - `frontend/apps/web/src/views/ActionViewShell.vue`
- 接入：`frontend/apps/web/src/views/ActionView.vue`

## 3. 输入

`useActionPageModel` 当前接收三类输入：

1. Contract outputs
   - strict bundle (`missing/defaults`)
   - surface intent
   - filter/action/projection 结构化输出
2. Runtime state
   - page 状态、viewMode、record/status、groupSummary、hud
3. Page context
   - page contract text、route preset 标签、scene/page 元信息

## 4. 输出

统一输出 `ActionPageVM`：

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

页面模板优先消费 `vm.*`。

## 5. 边界

### 5.1 Assembler 负责

- 页面展示形状装配
- section 可见性聚合
- contract/runtime 输出到 UI VM 的结构转换

### 5.2 Assembler 不负责

- API 调用
- mutation 执行
- batch 执行
- route push/replace 执行

### 5.3 当前仍暂留页面的逻辑

- `load()` 主流程
- `runContractAction()`

已迁出：

- `runContractAction/applyActionRefreshPolicy` -> `useActionViewActionRuntime`
- `handleBatchAction/handleBatchAssign/handleBatchExport/handleDownloadFailedCsv/handleLoadMoreFailures` -> `useActionViewBatchRuntime`
- selection glue（clear/toggle/ifMatch/idempotency）-> `useActionViewSelectionRuntime`

下一轮 runtime ownership 迁移重点收口到 `load()/group window/page-size` 主链。

## 6. 当前阶段判断

本轮已实现：

- ActionView 出现统一 `vm` 出口。
- 模板关键展示块（focus/strict/filter/action/content/empty/hud）开始转向 `vm` 消费。
- 路由入口切到 `ActionViewShell`（壳组件入口建立）。
- action 执行链首批外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewActionRuntime.ts`，将 `runContractAction/applyActionRefreshPolicy` 从页面抽离为可复用 composable（后续可再下沉到 runtime 层）。
- batch 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewBatchRuntime.ts`，页面改为事件绑定调用，legacy 批处理函数已清理。
- selection 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewSelectionRuntime.ts`，页面不再内联选择状态与幂等键构造逻辑。
- trigger 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewTriggerRuntime.ts`，页面不再内联 `search/sort/filter` 触发计划逻辑。
- grouped rows / grouped route 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewGroupedRowsRuntime.ts`，页面不再内联 `handleGroupedRowsPageChange/hydrateGroupedRowsByOffset/normalizeGroupedRouteState`。
- route preset / route sync 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewRoutePresetRuntime.ts`，页面不再内联 `applyRoutePreset/clearRoutePreset/applyRoutePatchAndReload/syncRouteListState/syncRouteStateAndReload/restartLoadWithRouteSync`。
- contract filter / saved filter / groupBy 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewFilterGroupRuntime.ts`，页面不再内联 `applyContractFilter/applySavedFilter/clearContractFilter/clearSavedFilter/applyGroupBy/clearGroupBy`。
- header 事件执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewHeaderRuntime.ts`，页面不再内联 `reload/openFocusAction/executeHeaderAction`。
- navigation 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewNavigationRuntime.ts`，页面不再内联 `resolveWorkspaceContextQuery/resolveCarryQuery/resolveWorkbenchQuery/handleRowClick`。
- request context 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewRequestContextRuntime.ts`，页面不再内联 filter/context/domain 合成与 `mergeContext/mergeActiveFilterDomain` 包装函数。
- scoped metrics 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewScopedMetricsRuntime.ts`，页面不再内联 `fetchScopedTotal/fetchProjectScopeMetrics` 查询循环。
- contract shape 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewContractShapeRuntime.ts`，页面不再内联 columns/kanban/advanced/model 解析函数。
- action meta/url/window 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewActionMetaRuntime.ts`，页面不再内联 `getActionType/isClientAction/isUrlAction/resolveNavigationUrl/redirectUrlAction/isWindowAction`。
- scene identity 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewSceneIdentityRuntime.ts`，页面不再内联 `resolveSceneCode/resolveNodeSceneKey/findMenuNode`。
- batch artifact glue 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewBatchArtifactGlueRuntime.ts`，页面不再内联 `downloadCsvBase64/applyBatchFailureArtifacts/handleBatchDetailAction`。
- assignee options 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewAssigneeRuntime.ts`，页面不再内联 `loadAssigneeOptions` 查询与权限告警分支。
- view mode 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewModeRuntime.ts`，页面不再内联 `viewModeLabel/switchViewMode`。
- project metric/sort 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewProjectMetricRuntime.ts`，页面不再内联 `resolveProjectStateCell/resolveProjectAmount/isCompletedState/resolveDefaultSort`。
- contract action button 映射执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewContractActionButtonRuntime.ts`，页面不再内联 `toContractActionButton`。
- contract action grouping 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewActionGroupingRuntime.ts`，页面不再内联 `contractActionGroups/contractPrimaryActions/contractOverflowActions/contractOverflowActionGroups` 分组决策。
- display computed 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewDisplayComputedRuntime.ts`，页面不再内联 `sortOptions/subtitle/statusLabel/pageStatus/recordCount`。
- filter computed 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewFilterComputedRuntime.ts`，页面不再内联 `contractFilterChips/filterPrimaryBudget/contractSavedFilterChips/contractGroupByChips/activeGroupByLabel`。
- load lifecycle 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadLifecycleRuntime.ts`，页面 `load()` 的 reset/missing-action/catch 分支已迁到 runtime，页面仅保留主干编排。
- load preflight 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadPreflightRuntime.ts`，页面 `load()` 的 preflight 分支（contract/meta/view-mode/route-selection/capability/missing-model/form-redirect）已迁到 runtime，页面仅消费结构化 preflight 结果。
- load preflight apply 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadPreflightApplyRuntime.ts`，页面不再内联 preflight continue/blocked 状态写回（contract/status/filter/group/model/sort/limit）。
- load request 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadRequestRuntime.ts`，页面 `load()` 的 request 构建与数据请求前分支（fields/domain/context/payload）已迁到 runtime。
- load request guard 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadRequestGuardRuntime.ts`，页面不再内联 request blocked 分支状态写回。
- load request phase 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadRequestPhaseRuntime.ts`，页面不再内联 request 执行 + blocked 分支编排，改为消费阶段化结果。
- load success phase 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadSuccessPhaseRuntime.ts`，页面不再内联 success 参数大对象装配，改为 `dynamicInput + staticInput` 分层注入。
- load request input 构建外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadRequestInputRuntime.ts`，页面不再内联 request 参数大对象装配，改为 `buildLoadRequestInput(...)`。
- load success dynamic input 构建外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadSuccessDynamicInputRuntime.ts`，页面不再内联 success dynamic 参数装配，改为 `buildLoadSuccessDynamicInput(...)`。
- load catch phase 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadCatchPhaseRuntime.ts`，页面不再内联 catch 参数大对象装配，改为 `executeLoadCatchPhase({ input })`。
- load preflight input 构建外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadPreflightInputRuntime.ts`，页面不再内联 preflight 参数大对象装配，改为 `buildLoadPreflightInput(...)`。
- load preflight apply bound 外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadPreflightApplyBoundRuntime.ts`，页面不再内联 preflight blocked/continue 的参数大对象装配，改为 `applyLoadPreflightBlocked/Continue(...)`。
- load preflight phase 外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadPreflightPhaseRuntime.ts`，页面不再内联 preflight 分支判断（redirect/handled/blocked/continue），改为 `executeLoadPreflightPhase({ input })`。
- load request blocked apply 外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadRequestBlockedApplyRuntime.ts`，页面不再内联 blocked 处理适配，改为 `applyLoadRequestBlocked(...)`。
- load request dynamic input 构建外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadRequestDynamicInputRuntime.ts`，页面不再内联 request 动态参数对象，改为 `buildLoadRequestDynamicInput(...)`。
- load success phase input 构建外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadSuccessPhaseInputRuntime.ts`，页面不再内联 success phase 动态参数对象，改为 `buildLoadSuccessPhaseInput(...)`。
- load main phase 外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadMainPhaseRuntime.ts`，页面不再内联 preflight/request/success 串联编排，改为 `executeLoadMainPhase(...)`。
- load main phase 进一步收口：`useActionViewLoadMainPhaseRuntime.ts` 现已并入 catch 分支处理，页面不再保留 `load()` 的 `try/catch` 包装。
- load main phase input 外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadMainPhaseInputRuntime.ts`，页面不再内联 `executeLoadMainPhase({ ...大对象... })`，改为 `executeLoadMainPhase(buildLoadMainPhaseInput({ startedAt }))`。
- load bound 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadBoundRuntime.ts`，页面 `load()` 不再内联 begin/main phase 调度，改为 `executeLoad()`。
- load main bound 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadMainBoundRuntime.ts`，`load bound` 不再直接依赖 `buildLoadMainPhaseInput + executeLoadMainPhase`，改为依赖 `executeLoadMainBound()`。
- section 可见性/样式运行时外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewSectionRuntime.ts`，页面模板不再直接组合 `pageSectionEnabled + pageSectionTagIs + pageSectionStyle`，改为统一 `isSectionVisible/getSectionStyle`。
- template busy/disabled 运行时外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewTemplateStateRuntime.ts`，页面模板不再重复内联 `status === 'loading' || batchBusy` 与 `!btn.enabled` 判定，改为统一 `isUiBusy/isBusyDisabled/isViewModeDisabled/isContractActionDisabled`。
- template 展开/收起交互运行时外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewTemplateInteractionRuntime.ts`，页面模板不再内联 `showMore* = !showMore*`，改为统一 `toggleMoreContractFilters/toggleMoreSavedFilters/toggleMoreGroupBy/toggleMoreContractActions`。
- text fallback 访问运行时外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewTextRuntime.ts`，页面模板与页面脚本不再直接调用 `pageText(...)`，改为统一 `t(...)`。
- template UI state 运行时外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewTemplateUiStateRuntime.ts`，页面不再直接 `ref(false)` 持有 `showMoreContractActions/showMoreContractFilters/showMoreSavedFilters`，改为统一由 runtime 提供。
- filter/view UI state 运行时外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewFilterUiStateRuntime.ts`，页面不再直接声明 `activeContractFilterKey/activeSavedFilterKey/contractLimit/preferredViewMode`，改为统一由 runtime 提供。
- page display state 运行时外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewPageDisplayStateRuntime.ts`，页面不再直接内联 `pageTitle/emptyReasonText/showHud/errorMessage` 计算，改为统一由 runtime 提供。
- HUD entries 拼装运行时外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewHudEntriesRuntime.ts`，页面不再直接内联 `hudEntries` 大型数组拼装，改为统一由 runtime `buildHudEntries()` 提供。
- HUD entries input 组装运行时外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewHudEntriesInputRuntime.ts`，页面不再直接将 `hudEntries` `staticInput` 大对象内联耦合到 entries runtime，改为先由 input runtime 统一产出 `buildHudEntriesInput()`。
- surface intent 解析运行时外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewSurfaceIntentRuntime.ts`，页面不再直接内联 `contractSurfaceIntent/surfaceIntent` 组合解析，改为统一由 runtime 提供。
- advanced view 展示解析运行时外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewAdvancedDisplayRuntime.ts`，页面不再直接内联 `advancedViewTitle/advancedViewHint` 计算，改为统一由 runtime 提供。
- content display 派生运行时外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewContentDisplayRuntime.ts`，页面不再直接内联 `ledgerOverviewItems/listSummaryItems/kanbanTitleField` 派生计算，改为统一由 runtime 提供。
- surface display 派生运行时外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewSurfaceDisplayRuntime.ts`，页面不再直接内联 `sortLabel/surfaceKind` 派生计算，改为统一由 runtime 提供。
- load begin input/phase 外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadBeginInputRuntime.ts` 与 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadBeginPhaseRuntime.ts`，页面不再内联 `beginActionViewLoad({...大对象...})`，改为 `executeLoadBeginPhase({ input })`。
- load success 执行链外移：新增 `frontend/apps/web/src/app/assemblers/action/useActionViewLoadSuccessRuntime.ts`，页面 `load()` 的成功分支 apply/finalize（group paging/route sync/project scope/grouped rows/finalize/trace）已迁到 runtime。

本轮未实现（明确延后）：

- runtime 主流程彻底迁出页面。
- ActionView 页面文件体量显著缩减。

## 7. 下一轮计划

1. 拆分 `load()` 为 list/group/request runtime 组合调用。
2. 拆分 action/batch 执行链为独立 runtime composables。
3. 进一步收缩模板判断逻辑到 `actionPageSections`。
4. 将同模式推广到 `HomeView`。

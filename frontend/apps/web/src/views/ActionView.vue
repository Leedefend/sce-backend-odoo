<template>
  <section class="page">
    <!-- Page intent: 在列表场景中先判断状态，再给出下一步可执行动作。 -->
    <section v-if="displayHeaderActions.length" class="page-actions">
      <button
        v-for="action in displayHeaderActions"
        :key="`header-${action.key}`"
        class="contract-chip ghost"
        :disabled="action.enabled === false"
        :title="action.hint || ''"
        @click="executeHeaderAction(action.key)"
      >
        {{ action.label || action.key }}
      </button>
    </section>
    <section
      v-if="isSectionVisible('view_switch', { defaultEnabled: true, tag: 'section', vmVisible: vm.page.availableViewModes.length > 1 })"
      class="view-switch"
      :style="getSectionStyle('view_switch')"
    >
      <p class="contract-label">{{ t('label.view_switch', '视图切换') }}</p>
      <div class="contract-chips">
        <button
          v-for="mode in vm.page.availableViewModes"
          :key="`view-mode-${mode}`"
          class="contract-chip"
          :class="{ active: vm.page.viewMode === mode }"
          :disabled="isViewModeDisabled({ mode, currentViewMode: vm.page.viewMode })"
          @click="switchViewMode(mode)"
        >
          {{ viewModeLabel(mode) }}
        </button>
      </div>
    </section>
    <section v-if="showViewSwitchDebug" class="contract-block">
      <p class="contract-label">view switch debug</p>
      <pre class="debug-json">{{ JSON.stringify(viewSwitchDebugState, null, 2) }}</pre>
    </section>
    <section v-if="!preferNativeListSurface && isSectionVisible('route_preset', { defaultEnabled: pageSectionEnabled('route_preset', true), tag: 'section', vmVisible: Boolean(vm.filters.routePreset) })" class="route-preset" :style="getSectionStyle('route_preset')">
      <p>
        {{ t('route_preset_applied_prefix', '已应用推荐筛选：') }}{{ vm.filters.routePreset?.label }}
        <span v-if="routePresetBannerSourceText">（{{ t('route_preset_source_prefix', '来源：') }}{{ routePresetBannerSourceText }}）</span>
      </p>
      <button class="clear-btn" @click="clearRoutePreset">{{ t('route_preset_clear', '清除推荐') }}</button>
    </section>
    <section v-if="!preferNativeListSurface && isSectionVisible('focus_strip', { defaultEnabled: pageSectionEnabled('focus_strip', true), tag: 'section', vmVisible: vm.sections.focus })" class="focus-strip" :style="getSectionStyle('focus_strip')">
      <div>
        <p class="focus-intent">{{ vm.focus.title }}</p>
        <p class="focus-summary">{{ vm.focus.summary }}</p>
      </div>
      <div class="focus-actions">
        <button v-for="item in vm.focus.actions" :key="`focus-${item.label}`" class="contract-chip ghost" @click="openFocusAction(item)">
          {{ item.label }}
        </button>
      </div>
    </section>
    <section v-if="!preferNativeListSurface && vm.sections.strictAlert && vm.strictAlert" class="contract-missing-alert">
      <p class="contract-missing-title">{{ vm.strictAlert.title }}</p>
      <p class="contract-missing-summary">{{ vm.strictAlert.summary }}</p>
      <p v-if="vm.strictAlert.defaultsSummary" class="contract-missing-defaults">{{ vm.strictAlert.defaultsSummary }}</p>
    </section>
    <section v-if="showNativeFallbackPanel" class="contract-native-fallback">
      <StatusPanel title="当前页面建议使用原生页面" :message="nativeFallbackMessage" variant="info" />
      <button class="contract-chip" @click="openNativeFallback">打开原生页面</button>
    </section>
    <section v-if="vm.content.kind !== 'list' && !preferNativeListSurface && isSectionVisible('quick_filters', { defaultEnabled: pageSectionEnabled('quick_filters', true), tag: 'section', vmVisible: vm.sections.quickFilters && vm.filters.quickFilters.visible })" class="contract-block" :style="getSectionStyle('quick_filters')">
      <p class="contract-label">{{ t('label.quick_filters', '快速筛选') }}</p>
      <div class="contract-chips">
        <button
          v-for="chip in vm.filters.quickFilters.primary"
          :key="`contract-filter-${chip.key}`"
          class="contract-chip"
          :class="{ active: activeContractFilterKey === chip.key }"
          :disabled="isBusyDisabled()"
          @click="applyContractFilter(chip.key)"
        >
          {{ chip.label }}
        </button>
        <button
          v-if="activeContractFilterKey"
          class="contract-chip ghost"
          :disabled="isBusyDisabled()"
          @click="clearContractFilter"
        >
          {{ t('chip_action_clear', '清除') }}
        </button>
        <button
          v-if="vm.filters.quickFilters.overflow.length"
          class="contract-chip ghost"
          :disabled="isBusyDisabled()"
          @click="toggleMoreContractFilters"
        >
          {{
            showMoreContractFilters
              ? t('chip_more_filters_collapse', '收起更多筛选')
              : `${t('chip_more_filters_expand', '更多筛选')} (${vm.filters.quickFilters.overflow.length})`
          }}
        </button>
      </div>
      <div v-if="showMoreContractFilters && vm.filters.quickFilters.overflow.length" class="contract-chips">
        <button
          v-for="chip in vm.filters.quickFilters.overflow"
          :key="`contract-filter-overflow-${chip.key}`"
          class="contract-chip"
          :class="{ active: activeContractFilterKey === chip.key }"
          :disabled="isBusyDisabled()"
          @click="applyContractFilter(chip.key)"
        >
          {{ chip.label }}
        </button>
      </div>
    </section>
    <section v-if="vm.content.kind !== 'list' && !preferNativeListSurface && isSectionVisible('saved_filters', { defaultEnabled: pageSectionEnabled('saved_filters', true), tag: 'section', vmVisible: vm.sections.savedFilters && vm.filters.savedFilters.visible })" class="contract-block" :style="getSectionStyle('saved_filters')">
      <p class="contract-label">{{ t('label.saved_filters', '已保存筛选') }}</p>
      <div class="contract-chips">
        <button
          v-for="chip in vm.filters.savedFilters.primary"
          :key="`saved-filter-${chip.key}`"
          class="contract-chip"
          :class="{ active: activeSavedFilterKey === chip.key }"
          :disabled="isBusyDisabled()"
          @click="applySavedFilter(chip.key)"
        >
          {{ chip.label }}
        </button>
        <button
          v-if="activeSavedFilterKey"
          class="contract-chip ghost"
          :disabled="isBusyDisabled()"
          @click="clearSavedFilter"
        >
          {{ t('chip_action_clear', '清除') }}
        </button>
        <button
          v-if="vm.filters.savedFilters.overflow.length"
          class="contract-chip ghost"
          :disabled="isBusyDisabled()"
          @click="toggleMoreSavedFilters"
        >
          {{
            showMoreSavedFilters
              ? t('chip_more_filters_collapse', '收起更多筛选')
              : `${t('chip_more_filters_expand', '更多筛选')} (${vm.filters.savedFilters.overflow.length})`
          }}
        </button>
      </div>
      <div v-if="showMoreSavedFilters && vm.filters.savedFilters.overflow.length" class="contract-chips">
        <button
          v-for="chip in vm.filters.savedFilters.overflow"
          :key="`saved-filter-overflow-${chip.key}`"
          class="contract-chip"
          :class="{ active: activeSavedFilterKey === chip.key }"
          :disabled="isBusyDisabled()"
          @click="applySavedFilter(chip.key)"
        >
          {{ chip.label }}
        </button>
      </div>
    </section>
    <section v-if="vm.content.kind !== 'list' && !preferNativeListSurface && isSectionVisible('group_view', { defaultEnabled: pageSectionEnabled('group_view', true), tag: 'section', vmVisible: vm.sections.groupBy && vm.filters.groupBy.visible })" class="contract-block" :style="getSectionStyle('group_view')">
      <p class="contract-label">{{ t('label.group_view', '分组查看') }}</p>
      <div class="contract-chips">
        <button
          v-for="chip in vm.filters.groupBy.primary"
          :key="`group-by-${chip.field}`"
          class="contract-chip"
          :class="{ active: activeGroupByField === chip.key }"
          :disabled="isBusyDisabled()"
          @click="applyGroupBy(chip.key)"
        >
          {{ chip.label }}
        </button>
        <button
          v-if="activeGroupByField"
          class="contract-chip ghost"
          :disabled="isBusyDisabled()"
          @click="clearGroupBy"
        >
          {{ t('chip_action_clear', '清除') }}
        </button>
        <button
          v-if="vm.filters.groupBy.overflow.length"
          class="contract-chip ghost"
          :disabled="isBusyDisabled()"
          @click="toggleMoreGroupBy"
        >
          {{
            showMoreGroupBy
              ? t('chip_more_group_collapse', '收起更多分组')
              : `${t('chip_more_group_expand', '更多分组')} (${vm.filters.groupBy.overflow.length})`
          }}
        </button>
      </div>
      <div v-if="showMoreGroupBy && vm.filters.groupBy.overflow.length" class="contract-chips">
        <button
          v-for="chip in vm.filters.groupBy.overflow"
          :key="`group-by-overflow-${chip.field}`"
          class="contract-chip"
          :class="{ active: activeGroupByField === chip.key }"
          :disabled="isBusyDisabled()"
          @click="applyGroupBy(chip.key)"
        >
          {{ chip.label }}
        </button>
      </div>
    </section>
    <GroupSummaryBar
      v-if="!preferNativeListSurface && isSectionVisible('group_summary', { defaultEnabled: pageSectionEnabled('group_summary', true), tag: 'section', vmVisible: vm.sections.groupSummary && Boolean(vm.groupSummary?.visible) })"
      :style="getSectionStyle('group_summary')"
      :items="vm.groupSummary?.items || []"
      :group-by-label="activeGroupByLabel"
      :active-key="activeGroupSummaryKey"
      :window-offset="groupWindowOffset"
      :window-count="groupWindowCount"
      :window-total="groupWindowTotal ?? undefined"
      :window-start="groupWindowStart ?? undefined"
      :window-end="groupWindowEnd ?? undefined"
      :can-prev-window="groupWindowPrevOffset !== null"
      :can-next-window="groupWindowNextOffset !== null"
      :on-pick="handleGroupSummaryPick"
      :on-clear="clearGroupSummaryDrilldown"
      :on-prev-window="handleGroupWindowPrev"
      :on-next-window="handleGroupWindowNext"
    />
    <section v-if="!preferNativeListSurface && isSectionVisible('quick_actions', { defaultEnabled: pageSectionEnabled('quick_actions', true), tag: 'section', vmVisible: vm.sections.quickActions && Boolean(vm.actions.primary.length || vm.actions.overflowGroups.length) })" class="contract-block" :style="getSectionStyle('quick_actions')">
      <p class="contract-label">{{ t('label.quick_actions', '快捷操作') }}</p>
      <div class="contract-chips">
        <button
          v-for="btn in vm.actions.primary"
          :key="`contract-action-${btn.key}`"
          class="contract-chip"
          :disabled="isContractActionDisabled({ enabled: btn.enabled })"
          :title="btn.hint"
          @click="runContractAction(btn)"
        >
          {{ btn.label }}
        </button>
        <button
          v-if="vm.actions.overflowGroups.length"
          class="contract-chip ghost"
          :disabled="isBusyDisabled()"
          @click="toggleMoreContractActions"
        >
          {{
            showMoreContractActions
              ? t('chip_more_actions_collapse', '收起更多操作')
              : `${t('chip_more_actions_expand', '更多操作')} (${vm.actions.overflowGroups.length})`
          }}
        </button>
      </div>
      <div v-if="showMoreContractActions && vm.actions.overflowGroups.length" class="contract-groups">
        <section
          v-for="group in vm.actions.overflowGroups"
          :key="`contract-group-${group.key}`"
          class="contract-group"
        >
          <p class="contract-group-label">{{ group.label }}</p>
          <div class="contract-chips">
            <button
              v-for="btn in group.actions"
              :key="`contract-group-action-${group.key}-${btn.key}`"
              class="contract-chip"
              :disabled="isContractActionDisabled({ enabled: btn.enabled })"
              :title="btn.hint"
              @click="runContractAction(btn)"
            >
              {{ btn.label }}
            </button>
          </div>
        </section>
      </div>
    </section>
    <section v-if="vm.content.kind === 'kanban' && hasLedgerOverviewStrip && (vm.content.kanban?.overviewItems || []).length" class="ledger-overview-strip">
      <article v-for="item in vm.content.kanban?.overviewItems || []" :key="item.key" class="ledger-overview-card" :class="`tone-${item.tone}`">
        <p class="ledger-overview-label">{{ item.label }}</p>
        <p class="ledger-overview-value">{{ item.value }}</p>
      </article>
    </section>
    <KanbanPage
      v-if="vm.content.kind === 'kanban'"
      :title="vm.page.title"
      :status="vm.page.status"
      :loading="isUiBusy"
      :error-message="vm.page.errorMessage"
      :trace-id="vm.page.traceId"
      :error="error"
      :records="records"
      :fields="kanbanFields"
      :primary-fields="kanbanPrimaryFields"
      :secondary-fields="kanbanSecondaryFields"
      :status-fields="kanbanStatusFields"
      :metric-fields="kanbanMetricFields"
      :quick-action-count="kanbanQuickActionCount"
      :active-group-by-field="activeGroupByField"
      :field-labels="contractColumnLabels"
      :title-field="kanbanTitleField"
      :subtitle="vm.page.subtitle"
      :status-label="vm.page.statusLabel"
      :scene-key="vm.page.sceneKey"
      :semantic-zones="semanticZones"
      :page-mode="vm.page.pageMode"
      :on-reload="reload"
      :on-card-click="handleRowClick"
    />
    <ListPage
      v-else-if="vm.content.kind === 'list'"
      :title="vm.page.title"
      :model="model"
      :status="vm.page.status"
      :loading="isUiBusy"
      :error-message="vm.page.errorMessage"
      :trace-id="vm.page.traceId"
      :error="error"
      :columns="columns"
      :records="records"
      :column-labels="contractColumnLabels"
      :sort-label="sortDisplayLabel"
      :sort-options="sortOptions"
      :sort-value="sortValue"
      :sort-source-label="sortSourceLabel"
      :search-placeholder="listSearchPlaceholder"
      :filter-value="filterValue"
      :has-active-field="hasActiveField"
      :search-term="searchTerm"
      :quick-filters="[...vm.filters.quickFilters.primary, ...vm.filters.quickFilters.overflow]"
      :saved-filters="listSavedFilterOptions"
      :group-by-options="listGroupByToolbarOptions"
      :search-panel-options="listSearchPanelOptions"
      :searchable-field-options="listSearchableFieldOptions"
      :searchable-field-total-count="listSearchableFieldTotalCount"
      :searchable-field-count-label="listSearchableFieldCountLabel"
      :saved-filter-count-label="listSavedFilterCountLabel"
      :group-by-count-label="listGroupByCountLabel"
      :search-panel-count-label="listSearchPanelCountLabel"
      :route-preset-label="listRoutePresetDisplayLabel"
      :route-preset-source="vm.filters.routePreset?.source || ''"
      :search-mode-label="listSearchModeLabel"
      :optimization-composition="listOptimizationComposition"
      :active-contract-filter-key="activeContractFilterKey || ''"
      :active-saved-filter-key="activeSavedFilterKey || ''"
      :active-group-by-field="activeGroupByField || ''"
      :subtitle="vm.page.subtitle"
      :status-label="vm.page.statusLabel"
      :primary-action-label="listPrimaryActionLabel"
      :on-primary-action="listPrimaryAction"
      :scene-key="vm.page.sceneKey"
      :semantic-zones="semanticZones"
      :page-mode="vm.page.pageMode"
      :record-count="recordCount"
      :page-offset="listOffset"
      :page-limit="contractLimit"
      :page-total="listTotalCount"
      :on-page-change="handlePageChange"
      :summary-items="vm.content.list?.summaryItems || []"
      :selected-ids="selectedIds"
      :batch-message="batchMessage"
      :batch-details="batchDetails"
      :failed-csv-available="Boolean(failedCsvContentB64)"
      :has-more-failures="batchHasMoreFailures"
      :show-assign="hasAssigneeField"
      :show-delete="canBatchDelete"
      :show-archive="!useDeleteOnlyBatchMode"
      :show-activate="!useDeleteOnlyBatchMode"
      :assignee-options="assigneeOptions"
      :selected-assignee-id="selectedAssigneeId"
      :list-profile="listProfile"
      :grouped-rows="groupedRows"
      :on-open-group="handleOpenGroupedRows"
      :group-sample-limit="groupSampleLimit"
      :on-group-sample-limit-change="handleGroupSampleLimitChange"
      :group-sort="groupSort"
      :on-group-sort-change="handleGroupSortChange"
      :collapsed-group-keys="collapsedGroupKeys"
      :on-group-collapsed-change="handleGroupCollapsedChange"
      :on-group-page-change="handleGroupedRowsPageChange"
      :on-reload="reload"
      :on-search="handleSearch"
      :on-sort="handleSort"
      :on-filter="handleFilter"
      :on-apply-contract-filter="applyContractFilter"
      :on-clear-contract-filter="clearContractFilter"
      :on-apply-saved-filter="applySavedFilter"
      :on-clear-saved-filter="clearSavedFilter"
      :on-apply-group-by="applyGroupBy"
      :on-clear-group-by="clearGroupBy"
      :on-clear-route-preset="clearRoutePreset"
      :on-toggle-selection="handleToggleSelection"
      :on-toggle-selection-all="handleToggleSelectionAll"
      :on-batch-action="handleBatchAction"
      :on-batch-assign="handleBatchAssign"
      :on-batch-export="handleBatchExport"
      :on-assignee-change="handleAssigneeChange"
      :on-download-failed-csv="handleDownloadFailedCsv"
      :on-load-more-failures="handleLoadMoreFailures"
      :on-batch-detail-action="handleBatchDetailAction"
      :on-clear-selection="clearSelection"
      :on-row-click="handleRowClick"
    />
    <section v-else-if="isSectionVisible('advanced_view', { defaultEnabled: pageSectionEnabled('advanced_view', true), tag: 'section' })" class="advanced-view" :style="getSectionStyle('advanced_view')">
      <header class="advanced-view-head">
        <h3>{{ vm.content.advanced?.title }}</h3>
        <p>{{ vm.content.advanced?.hint }}</p>
      </header>
      <div v-if="showHud" class="advanced-contract">
        <p class="contract-label">{{ t('label.contract_summary', '契约摘要') }}</p>
        <p>view_type={{ contractViewType || '-' }} · mode={{ vm.page.viewMode || '-' }} · records={{ records.length }}</p>
      </div>
      <div v-if="vm.content.advanced?.rows.length" class="advanced-list">
        <article v-for="row in vm.content.advanced?.rows || []" :key="row.key" class="advanced-item">
          <p class="advanced-item-title">{{ row.title }}</p>
          <p class="advanced-item-meta">{{ row.meta }}</p>
        </article>
      </div>
      <section v-else class="empty-next">
        <p class="empty-next-title">{{ vm.empty?.title || vm.focus.title }}</p>
        <p class="empty-next-hint">{{ vm.content.advanced?.hint }}</p>
      </section>
    </section>
    <section v-if="isSectionVisible('empty_next', { defaultEnabled: pageSectionEnabled('empty_next', true), tag: 'section', vmVisible: Boolean(vm.empty) })" class="empty-next" :style="getSectionStyle('empty_next')">
      <p class="empty-next-title">{{ vm.empty.title }}</p>
      <p class="empty-next-hint">{{ vm.empty.hint }}</p>
      <p class="empty-next-reason">{{ vm.empty.reason }}</p>
      <div class="focus-actions">
        <button class="contract-chip primary" @click="openFocusAction(vm.empty.primaryAction)">{{ vm.empty.primaryAction.label }}</button>
        <button
          v-if="vm.empty.secondaryAction"
          class="contract-chip ghost"
          @click="openFocusAction(vm.empty.secondaryAction)"
        >
          {{ vm.empty.secondaryAction.label }}
        </button>
      </div>
    </section>

    <DevContextPanel
      :visible="isSectionVisible('dev_context', { defaultEnabled: pageSectionEnabled('dev_context', true), tag: 'div', vmVisible: vm.sections.hud && Boolean(vm.hud?.visible) })"
      :style="getSectionStyle('dev_context')"
      :title="hudPanelTitle"
      :entries="vm.hud?.entries || []"
      :message="hudPanelMessage"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, inject, onMounted, ref, watch, watchEffect } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { batchUpdateRecords, exportRecordsCsv, listRecordsRaw, unlinkRecord } from '../api/data';
import { executeButton } from '../api/executeButton';
import { trackUsageEvent } from '../api/usage';
import { resolveAction } from '../app/resolvers/actionResolver';
import { loadActionContract } from '../api/contract';
import { config } from '../config';
import { useSessionStore } from '../stores/session';
import ListPage from '../pages/ListPage.vue';
import KanbanPage from '../pages/KanbanPage.vue';
import DevContextPanel from '../components/DevContextPanel.vue';
import GroupSummaryBar from '../components/GroupSummaryBar.vue';
import StatusPanel from '../components/StatusPanel.vue';
import { deriveListStatus } from '../app/view_state';
import { isHudEnabled } from '../config/debug';
import { ErrorCodes } from '../app/error_codes';
import { evaluateCapabilityPolicy } from '../app/capabilityPolicy';
import { resolveSuggestedAction, useStatus } from '../composables/useStatus';
import type { StatusError } from '../composables/useStatus';
import { describeSuggestedAction, runSuggestedAction } from '../composables/useSuggestedAction';
import {
  parseContractContextRaw,
  resolveContractAccessPolicy,
  resolveContractRights,
  resolveContractReadRight,
  resolveContractViewMode,
} from '../app/contractActionRuntime';
import { detectObjectMethodFromActionKey, normalizeActionKind, toPositiveInt } from '../app/contractRuntime';
import type { Scene, SceneListProfile } from '../app/resolvers/sceneRegistry';
import { findSceneReadyEntryByTarget, resolveListSceneReady } from '../app/resolvers/sceneReadyResolver';
import { normalizeSceneActionProtocol, type MutationContract, type ProjectionRefreshPolicy } from '../app/sceneActionProtocol';
import { executeProjectionRefresh } from '../app/projectionRefreshRuntime';
import { executeSceneMutation } from '../app/sceneMutationRuntime';
import { buildNativeFallbackUrl, resolveContractListSemantics, resolveContractViewRenderPolicy } from '../app/contractTakeover';
import { pickContractNavQuery } from '../app/navigationContext';
import { useActionViewActionRuntime } from '../app/action_runtime/useActionViewActionRuntime';
import { useActionViewBatchRuntime } from '../app/action_runtime/useActionViewBatchRuntime';
import { useActionViewSelectionRuntime } from '../app/action_runtime/useActionViewSelectionRuntime';
import { useActionViewTriggerRuntime } from '../app/action_runtime/useActionViewTriggerRuntime';
import { useActionViewGroupedRowsRuntime } from '../app/action_runtime/useActionViewGroupedRowsRuntime';
import { useActionViewRoutePresetRuntime } from '../app/action_runtime/useActionViewRoutePresetRuntime';
import { useActionViewFilterGroupRuntime } from '../app/action_runtime/useActionViewFilterGroupRuntime';
import { useActionViewHeaderRuntime } from '../app/action_runtime/useActionViewHeaderRuntime';
import { useActionViewNavigationRuntime } from '../app/action_runtime/useActionViewNavigationRuntime';
import { useActionViewRequestContextRuntime } from '../app/action_runtime/useActionViewRequestContextRuntime';
import { useActionViewScopedMetricsRuntime } from '../app/action_runtime/useActionViewScopedMetricsRuntime';
import { useActionViewContractShapeRuntime } from '../app/action_runtime/useActionViewContractShapeRuntime';
import { useActionViewActionMetaRuntime } from '../app/action_runtime/useActionViewActionMetaRuntime';
import { useActionViewSceneIdentityRuntime } from '../app/action_runtime/useActionViewSceneIdentityRuntime';
import { useActionViewBatchArtifactGlueRuntime } from '../app/action_runtime/useActionViewBatchArtifactGlueRuntime';
import { useActionViewAssigneeRuntime } from '../app/action_runtime/useActionViewAssigneeRuntime';
import { useActionViewModeRuntime } from '../app/action_runtime/useActionViewModeRuntime';
import { useActionViewProjectMetricRuntime } from '../app/action_runtime/useActionViewProjectMetricRuntime';
import { useActionViewContractActionButtonRuntime } from '../app/action_runtime/useActionViewContractActionButtonRuntime';
import { useActionViewActionGroupingRuntime } from '../app/action_runtime/useActionViewActionGroupingRuntime';
import { useActionViewDisplayComputedRuntime } from '../app/action_runtime/useActionViewDisplayComputedRuntime';
import { useActionViewFilterComputedRuntime } from '../app/action_runtime/useActionViewFilterComputedRuntime';
import { useActionViewLoadLifecycleRuntime } from '../app/action_runtime/useActionViewLoadLifecycleRuntime';
import { useActionViewLoadBeginInputRuntime } from '../app/action_runtime/useActionViewLoadBeginInputRuntime';
import { useActionViewLoadBeginPhaseRuntime } from '../app/action_runtime/useActionViewLoadBeginPhaseRuntime';
import { useActionViewLoadPreflightRuntime } from '../app/action_runtime/useActionViewLoadPreflightRuntime';
import { useActionViewLoadPreflightApplyRuntime } from '../app/action_runtime/useActionViewLoadPreflightApplyRuntime';
import { useActionViewLoadPreflightApplyBoundRuntime } from '../app/action_runtime/useActionViewLoadPreflightApplyBoundRuntime';
import { useActionViewLoadPreflightInputRuntime } from '../app/action_runtime/useActionViewLoadPreflightInputRuntime';
import { useActionViewLoadPreflightPhaseRuntime } from '../app/action_runtime/useActionViewLoadPreflightPhaseRuntime';
import { useActionViewLoadRequestRuntime } from '../app/action_runtime/useActionViewLoadRequestRuntime';
import { useActionViewLoadRequestGuardRuntime } from '../app/action_runtime/useActionViewLoadRequestGuardRuntime';
import { useActionViewLoadRequestBlockedApplyRuntime } from '../app/action_runtime/useActionViewLoadRequestBlockedApplyRuntime';
import { useActionViewLoadRequestDynamicInputRuntime } from '../app/action_runtime/useActionViewLoadRequestDynamicInputRuntime';
import { useActionViewLoadRequestInputRuntime } from '../app/action_runtime/useActionViewLoadRequestInputRuntime';
import { useActionViewLoadMainPhaseRuntime } from '../app/action_runtime/useActionViewLoadMainPhaseRuntime';
import { useActionViewLoadMainPhaseInputRuntime } from '../app/action_runtime/useActionViewLoadMainPhaseInputRuntime';
import { useActionViewLoadMainBoundRuntime } from '../app/action_runtime/useActionViewLoadMainBoundRuntime';
import { useActionViewLoadBoundRuntime } from '../app/action_runtime/useActionViewLoadBoundRuntime';
import { useActionViewSectionRuntime } from '../app/action_runtime/useActionViewSectionRuntime';
import { useActionViewTemplateStateRuntime } from '../app/action_runtime/useActionViewTemplateStateRuntime';
import { useActionViewTemplateInteractionRuntime } from '../app/action_runtime/useActionViewTemplateInteractionRuntime';
import { useActionViewTextRuntime } from '../app/action_runtime/useActionViewTextRuntime';
import { useActionViewTemplateUiStateRuntime } from '../app/action_runtime/useActionViewTemplateUiStateRuntime';
import { useActionViewFilterUiStateRuntime } from '../app/action_runtime/useActionViewFilterUiStateRuntime';
import { useActionViewPageDisplayStateRuntime } from '../app/action_runtime/useActionViewPageDisplayStateRuntime';
import { useActionViewSurfaceIntentRuntime } from '../app/action_runtime/useActionViewSurfaceIntentRuntime';
import { useActionViewAdvancedDisplayRuntime } from '../app/action_runtime/useActionViewAdvancedDisplayRuntime';
import { useActionViewContentDisplayRuntime } from '../app/action_runtime/useActionViewContentDisplayRuntime';
import { useActionViewSurfaceDisplayRuntime } from '../app/action_runtime/useActionViewSurfaceDisplayRuntime';
import { useActionViewLoadRequestPhaseRuntime } from '../app/action_runtime/useActionViewLoadRequestPhaseRuntime';
import { useActionViewLoadCatchPhaseRuntime } from '../app/action_runtime/useActionViewLoadCatchPhaseRuntime';
import { useActionViewLoadSuccessDynamicInputRuntime } from '../app/action_runtime/useActionViewLoadSuccessDynamicInputRuntime';
import { useActionViewLoadSuccessPhaseInputRuntime } from '../app/action_runtime/useActionViewLoadSuccessPhaseInputRuntime';
import { useActionViewLoadSuccessRuntime } from '../app/action_runtime/useActionViewLoadSuccessRuntime';
import { useActionViewLoadSuccessPhaseRuntime } from '../app/action_runtime/useActionViewLoadSuccessPhaseRuntime';
import { useActionViewLoadFacadeRuntime } from '../app/action_runtime/useActionViewLoadFacadeRuntime';
import { useActionViewLoadDispatchRuntime } from '../app/action_runtime/useActionViewLoadDispatchRuntime';
import { useActionViewActionEffectsRuntime } from '../app/action_runtime/useActionViewActionEffectsRuntime';
import { useActionViewBatchEffectsRuntime } from '../app/action_runtime/useActionViewBatchEffectsRuntime';
import { useActionViewActionPresentationRuntime } from '../app/action_runtime/useActionViewActionPresentationRuntime';
import {
  normalizeGroupPageOffset,
  parseGroupPageOffsets,
} from '../app/runtime/actionViewGroupWindowRuntime';
import {
  mergeSceneDomain,
  readTotalFromListResult,
  resolveRequestedFields,
  uniqueFields,
} from '../app/runtime/actionViewRequestRuntime';
import { resolvePreferredActionViewMode, resolveRouteSelectionState } from '../app/runtime/actionViewContractLoadRuntime';
import {
  resolveActionViewResolvedModel,
} from '../app/runtime/actionViewLoadGuardRuntime';
import {
  resolveLoadPreflightContractFlags,
  resolveLoadPreflightContractLimit,
  resolveLoadPreflightFieldFlags,
  resolveLoadPreflightSortValue,
} from '../app/runtime/actionViewLoadPreflightRuntime';
import {
  resolveLoadCapabilityRedirectPayload,
  resolveLoadContractReadRedirectPayload,
  resolveLoadFormActionResId,
  resolveLoadMissingModelRedirectDecision,
  resolveLoadMissingResolvedModelErrorState,
} from '../app/runtime/actionViewLoadBranchRuntime';
import {
  resolveLoadGroupRouteSyncPatch,
  resolveLoadGroupRouteSyncPlan,
} from '../app/runtime/actionViewLoadRouteRequestRuntime';
import { resolveActionViewGroupPagingState } from '../app/runtime/actionViewGroupPagingRuntime';
import {
  resolveLoadCatchState,
  resolveLoadMissingActionIdErrorState,
  resolveLoadMissingContractViewTypeErrorState,
  resolveLoadMissingTreeColumnsErrorState,
} from '../app/runtime/actionViewLoadErrorRuntime';
import {
  resolveLoadCatchLatencyState,
  resolveLoadCatchListTotalState,
  resolveLoadCatchProjectScopeState,
  resolveLoadCatchStatusApplyInput,
  resolveLoadCatchTraceApplyState,
} from '../app/runtime/actionViewLoadCatchApplyRuntime';
import {
  resolveLoadSuccessGroupedRowsState,
  resolveLoadSuccessGroupSummaryState,
  resolveLoadSuccessProjectScopeApplyState,
  resolveLoadSuccessRecordsState,
  resolveLoadSuccessWindowApplyState,
} from '../app/runtime/actionViewLoadSuccessApplyRuntime';
import {
  resolveLoadFinalizeColumnsState,
  resolveLoadFinalizeSelectedIdsState,
  resolveLoadFinalizeStatusState,
  resolveLoadFinalizeSummaryKeyState,
  resolveLoadFinalizeTraceTimingState,
} from '../app/runtime/actionViewLoadFinalizeRuntime';
import {
  resolveReloadTriggerPlan,
} from '../app/runtime/actionViewLoadTriggerRuntime';
import {
  buildContractActionRouteTarget,
  buildContractActionButtonRequest,
  resolveContractActionCounters,
  resolveContractActionExecIds,
  resolveContractActionDoneMessage,
  resolveContractActionMissingModelMessage,
  resolveContractActionMissingOpenTargetMessage,
  resolveContractActionOpenNavigation,
  resolveContractActionResponseActionId,
  resolveContractActionRequiresRecordContextMessage,
  resolveContractActionRunIds,
  resolveContractActionSelectionBlockMessage,
  shouldNavigateContractAction,
} from '../app/runtime/actionViewContractActionRuntime';
import {
  buildBatchErrorLine,
  resolveBatchActionGuardMessage,
  resolveBatchActionErrorLabel,
  buildBatchUpdateRequest,
  resolveBatchActionFailureMessage,
  resolveBatchActionResultMessage,
  resolveBatchAssignGuardMessage,
} from '../app/runtime/actionViewBatchRuntime';
import {
  resolveBatchActionDeleteMode,
  resolveBatchActionGuardDecision,
  resolveBatchActionTargetModel,
  resolveBatchDeleteExecutionSeed,
  resolveBatchStandardExecutionSeed,
} from '../app/runtime/actionViewBatchActionFlowRuntime';
import {
  resolveBatchAssignAssigneeLabel,
  resolveBatchAssignExecutionSeed,
  resolveBatchAssignFailureMessage,
  resolveBatchAssignGuardDecision,
  resolveBatchAssignTargetModel,
} from '../app/runtime/actionViewBatchAssignFlowRuntime';
import {
  resolveBatchActionErrorFallback,
  resolveBatchAssignErrorFallback,
  resolveBatchExportErrorFallback,
} from '../app/runtime/actionViewBatchErrorDetailFlowRuntime';
import {
  resolveBatchActionLastRequestState,
} from '../app/runtime/actionViewBatchRequestSeedRuntime';
import {
  resolveAssigneeLoadFailureState,
  resolveAssigneeLoadSuccessState,
  resolveAssigneeOptionsLoadGuard,
  resolveAssigneeOptions,
  resolveExportDoneMessage,
  resolveExportFailedMessage,
  resolveAssigneePermissionWarningMessage,
  resolveAssigneePermissionWarning,
  resolveExportGuardMessage,
  resolveExportNoContentMessage,
} from '../app/runtime/actionViewAssigneeExportRuntime';
import {
  resolveBatchExportDomainState,
  resolveBatchExportGuardDecision,
  resolveBatchExportNoContent,
  resolveBatchExportRequestPayload,
  resolveBatchExportTargetModel,
} from '../app/runtime/actionViewBatchExportFlowRuntime';
import {
  resolveBatchFailureCsvApplyState,
  resolveBatchFailureDetailMergeState,
  resolveBatchFailureLinesState,
  resolveBatchFailurePagingApplyState,
  resolveBatchFailurePreviewState,
} from '../app/runtime/actionViewBatchFailureApplyFlowRuntime';
import {
  resolveBatchErrorHintResolver,
  resolveBatchFailureActionMetaResolver,
  resolveBatchFailureHintResolver,
  resolveBatchRetryTagTexts,
} from '../app/runtime/actionViewBatchHintResolverRuntime';
import {
  resolveBatchExportCatchState,
  resolveBatchExportResetState,
  resolveBatchFailureCatchState,
  resolveBatchOperationResetState,
  resolveLoadMoreFailuresCatchState,
} from '../app/runtime/actionViewBatchArtifactStateFlowRuntime';
import {
  resolveLoadMoreFailuresApplyPlan,
  resolveLoadMoreFailuresErrorFallback,
  resolveLoadMoreFailuresGuardPlan,
  resolveLoadMoreFailuresRequestPayload,
} from '../app/runtime/actionViewLoadMoreFailuresFlowRuntime';
import { applyActionViewLoadResetState } from '../app/runtime/actionViewLoadResetRuntime';
import {
  resolveContractFlagApplyState,
  resolveGroupPagingIdentityApplyState,
  resolveProjectScopeApplyState,
  resolveRouteSelectionApplyState,
  resolveWindowMetricsApplyState,
} from '../app/runtime/actionViewLoadStateApplyRuntime';
import {
  resolveCapabilityMissingRedirectTarget,
  resolveLoadMissingActionApplyState,
  resolveLoadMissingResolvedModelApplyState,
  resolveLoadMissingViewTypeApplyState,
  resolveMissingModelRedirectTarget,
} from '../app/runtime/actionViewLoadRedirectErrorRuntime';
import {
  resolveLoadKanbanFieldApplyState,
  resolveLoadMissingColumnsApplyState,
  resolveLoadRequestedFieldsApplyState,
} from '../app/runtime/actionViewLoadViewFieldStateRuntime';
import {
  resolveLoadContextStateApply,
  resolveLoadDomainStateApply,
  resolveLoadRequestPayloadState,
} from '../app/runtime/actionViewLoadDomainContextRequestRuntime';
import {
  resolveLoadFinalizeApplyState,
  resolveLoadGroupedRowsApplyState,
  resolveLoadGroupSummaryApplyState,
  resolveLoadListTotalApplyState,
  resolveLoadTraceApplyState,
} from '../app/runtime/actionViewLoadSuccessStateApplyRuntime';
import {
  resolveLoadRouteResetApplyState,
  resolveLoadRouteSyncApplyState,
} from '../app/runtime/actionViewLoadRouteApplyRuntime';
import {
  resolveFocusActionPushState,
  resolvePortalSelfRedirectState,
  resolveReplaceCurrentRouteState,
  resolveUrlUnsupportedRedirectState,
} from '../app/runtime/actionViewNavigationApplyRuntime';
import {
  buildActionViewClearedPresetQuery,
  buildActionViewPatchedRouteQuery,
  normalizeActionViewRouteQuery,
  resolveActionViewRouteSnapshot,
  buildActionViewSyncedRouteQuery,
  buildModelFormRouteTarget,
  buildPathRouteTarget,
  buildWorkbenchRouteTarget,
} from '../app/runtime/actionViewRouteRuntime';
import {
  hasRoutePresetGroupPageStateChanged,
  resolveRoutePresetActiveFilterValue,
  resolveRoutePresetAppliedLabel,
  resolveRoutePresetGroupPageState,
  resolveRoutePresetGroupSummaryResetState,
  resolveRoutePresetGroupVisualState,
  resolveRoutePresetGroupWindowState,
  resolveRoutePresetSavedFilterValue,
  resolveRoutePresetSearchTerm,
  resolveRoutePresetTrackingState,
} from '../app/runtime/actionViewRoutePresetRuntime';
import {
  buildActionViewRouteSyncStatePayload,
  resolveRouteSyncExtra,
  resolveRouteSyncShouldAwaitLoad,
} from '../app/runtime/actionViewRouteSyncStateRuntime';
import {
  createActionViewGroupRuntimeCapsule,
} from '../app/runtime/actionViewGroupRuntimeState';
import {
  createActionViewSelectionRuntimeCapsule,
} from '../app/runtime/actionViewSelectionRuntimeState';
import {
  createActionViewBatchRuntimeCapsule,
} from '../app/runtime/actionViewBatchRuntimeState';
import { useActionViewGroupRuntime } from '../app/runtime/useActionViewGroupRuntime';
import {
  extractActionResId,
  resolveActionViewType,
} from '../app/runtime/actionViewMetaRuntime';
import { usePageContract } from '../app/pageContract';
import { executePageContractAction } from '../app/pageContractActionRuntime';
import { resolvePageMode } from '../app/pageMode';
import { useActionViewStrictContractBundle } from '../app/contracts/actionViewStrictContract';
import {
  normalizeActionViewMode,
  resolveActionViewAvailableModes,
  resolveActionViewModeLabel,
  resolveActionViewSurfaceIntent,
  type SurfaceIntentContract,
} from '../app/contracts/actionViewSurfaceContract';
import {
  mapProjectionMetricItems,
  resolveActionViewSurfaceKind,
} from '../app/contracts/actionViewProjectionContract';
import {
  hasActionViewNoiseMarker,
  isActionViewNumericToken,
} from '../app/contracts/actionViewContractSanitizer';
import {
  resolveActionViewAdvancedHint,
  resolveActionViewAdvancedTitle,
} from '../app/contracts/actionViewAdvancedContract';
import { useActionPageModel } from '../app/assemblers/action/useActionPageModel';

const route = useRoute();
const router = useRouter();
const session = useSessionStore();
const {
  resolveSceneCode,
  resolveNodeSceneKey,
  findMenuNode,
} = useActionViewSceneIdentityRuntime();
const pageContract = usePageContract('action');
const pageText = pageContract.text;
const pageSectionEnabled = pageContract.sectionEnabled;
const pageSectionStyle = pageContract.sectionStyle;
const pageSectionTagIs = pageContract.sectionTagIs;

const { bindLoad, requestLoad } = useActionViewLoadDispatchRuntime();

let clearSelectionInvoker: () => void = () => {};
function clearSelection(): void {
  clearSelectionInvoker();
}

const { t } = useActionViewTextRuntime({ pageText });
const pageActionIntent = pageContract.actionIntent;
const pageActionTarget = pageContract.actionTarget;
const pageGlobalActions = pageContract.globalActions;
const {
  isSectionVisible,
  getSectionStyle,
} = useActionViewSectionRuntime({
  pageSectionEnabled,
  pageSectionTagIs,
  pageSectionStyle,
});
const routeQueryMap = computed<Record<string, unknown>>(() => normalizeActionViewRouteQuery(route.query));

const status = ref<'idle' | 'loading' | 'ok' | 'empty' | 'error'>('idle');
const isListInteractionLocked = computed(() => status.value === 'loading');
const traceId = ref('');
const lastTraceId = ref('');
const records = ref<Array<Record<string, unknown>>>([]);
const listTotalCount = ref<number | null>(null);
const listOffset = ref(0);
const projectScopeTotals = ref<{ all: number; active: number; archived: number } | null>(null);
const projectScopeMetrics = ref<{ warning: number; done: number; amount: number } | null>(null);
const searchTerm = ref('');
const sortValue = ref('');
const filterValue = ref<'all' | 'active' | 'archived'>('all');
const columns = ref<string[]>([]);
const kanbanFields = ref<string[]>([]);
const kanbanPrimaryFields = ref<string[]>([]);
const kanbanSecondaryFields = ref<string[]>([]);
const kanbanStatusFields = ref<string[]>([]);
const kanbanMetricFields = ref<string[]>([]);
const kanbanQuickActionCount = ref(0);
const kanbanTitleFieldHint = ref('');
const hasActiveField = ref(false);
const hasAssigneeField = ref(false);
const assigneeOptions = ref<Array<{ id: number; name: string }>>([]);
const selectionRuntimeCapsule = createActionViewSelectionRuntimeCapsule();
const {
  selectedAssigneeId,
  selectedIds,
} = selectionRuntimeCapsule.state;
const batchRuntimeCapsule = createActionViewBatchRuntimeCapsule();
const {
  batchMessage,
  batchDetails,
  failedCsvFileName,
  failedCsvContentB64,
  batchFailedOffset,
  batchFailedLimit,
  batchHasMoreFailures,
  lastBatchRequest,
  batchBusy,
} = batchRuntimeCapsule.state;
const groupRuntimeCapsule = createActionViewGroupRuntimeCapsule();
const { state: groupRuntimeState } = groupRuntimeCapsule;
const {
  groupSummaryItems,
  groupedRows,
  groupSampleLimit,
  groupSort,
  collapsedGroupKeys,
  groupPageOffsets,
  activeGroupSummaryKey,
  activeGroupSummaryDomain,
  groupWindowOffset,
  groupWindowCount,
  groupWindowTotal,
  groupWindowStart,
  groupWindowEnd,
  groupWindowId,
  groupQueryFingerprint,
  groupWindowDigest,
  groupWindowIdentityKey,
  groupWindowPrevOffset,
  groupWindowNextOffset,
  showMoreGroupBy,
} = groupRuntimeState;
const headerActions = computed(() => pageGlobalActions.value);
const displayHeaderActions = computed(() => {
  if (preferNativeListSurface.value) {
    return [
      {
        key: 'open_workbench',
        label: '返回工作台',
        enabled: true,
        hint: '',
      },
    ];
  }
  const disabledMap = new Map(
    headerActions.value.map((item) => [item.key, { disabled: Boolean(item.disabled), reason: item.disabledReason || '' }]),
  );
  return vm.value.header.actions.map((item) => {
    const mapped = disabledMap.get(item.key);
    if (!mapped) return item;
    if (!mapped.disabled) return item;
    return {
      ...item,
      enabled: false,
      hint: mapped.reason || item.hint,
    };
  });
});
const preferNativeListSurface = computed(() => vm.value.content.kind === 'list');
const hudPanelTitle = computed(() => {
  const explicit = String(vm.value.hud?.title || '').trim();
  if (explicit) return explicit;
  return vm.value.content.kind === 'list' ? '列表上下文' : '记录上下文';
});
const hudPanelMessage = computed(() => {
  if (!vm.value.sections.hud || !vm.value.hud?.visible) return '';
  if (vm.value.content.kind === 'list') {
    return '展示当前列表请求与排序等调试上下文';
  }
  return '展示当前记录请求、写入模式与耗时等上下文';
});
const advancedFields = ref<string[]>([]);
const {
  isUiBusy,
  isViewModeDisabled,
  isBusyDisabled,
  isContractActionDisabled,
} = useActionViewTemplateStateRuntime({
  status,
  batchBusy,
});
const lastIntent = ref('');
const lastWriteMode = ref('');
const lastLatencyMs = ref<number | null>(null);
const appliedPresetLabel = ref('');
const routeContextSource = ref('');
const lastTrackedPreset = ref('');
const statusApi = useStatus?.();
const error = statusApi?.error ?? ref<StatusError | null>(null);
const clearError = statusApi?.clearError ?? (() => {});
const setError = statusApi?.setError ?? (() => {});
type ContractColumnSchema = { name?: string };
type ContractViewBlock = {
  columns?: string[];
  columnsSchema?: ContractColumnSchema[];
  columns_schema?: ContractColumnSchema[];
  fields?: string[];
  kanban_profile?: {
    title_field?: string;
    primary_fields?: string[];
    secondary_fields?: string[];
    status_fields?: string[];
    max_meta?: number;
  };
  model?: string;
  order?: string;
};
type ActionContractLoose = Awaited<ReturnType<typeof loadActionContract>> & {
  head?: {
    model?: string;
    view_type?: string;
    context?: unknown;
    res_id?: number | string;
  };
  views?: {
    tree?: ContractViewBlock;
    list?: ContractViewBlock;
    kanban?: ContractViewBlock;
    form?: ContractViewBlock;
  };
  ui_contract?: {
    views?: {
      tree?: ContractViewBlock;
      list?: ContractViewBlock;
      kanban?: ContractViewBlock;
    };
    columns?: string[];
    columnsSchema?: ContractColumnSchema[];
  };
  fields?: Record<string, unknown>;
  buttons?: Array<Record<string, unknown>>;
  action_groups?: ContractActionGroupRaw[];
  toolbar?: {
    header?: Array<Record<string, unknown>>;
    sidebar?: Array<Record<string, unknown>>;
    footer?: Array<Record<string, unknown>>;
  };
  surface_policies?: {
    filters_primary_max?: number;
    actions_primary_max?: number;
    filters_max?: number;
    actions_max?: number;
    kind?: string;
    delete_mode?: string;
    intent_profile?: SurfaceIntentContract;
    empty_reason?: string;
  };
  model?: string;
  data?: {
    type?: string;
    url?: string;
    target?: string;
  };
  warnings?: Array<string | Record<string, unknown>>;
  degraded?: boolean;
  permissions?: {
    effective?: {
      rights?: {
        read?: boolean;
        write?: boolean;
        create?: boolean;
        unlink?: boolean;
      };
    };
  };
};
type ContractActionSelection = 'none' | 'single' | 'multi';
type ContractActionButton = {
  key: string;
  label: string;
  kind: string;
  actionId: number | null;
  methodName: string;
  model: string;
  target: string;
  url: string;
  selection: ContractActionSelection;
  context: Record<string, unknown>;
  domainRaw: string;
  enabled: boolean;
  hint: string;
  mutation?: MutationContract;
  refreshPolicy?: ProjectionRefreshPolicy;
};
type ContractActionGroupRaw = {
  key?: string;
  label?: string;
  actions?: Array<Record<string, unknown>>;
  overflow_actions?: Array<Record<string, unknown>>;
  overflow_count?: number;
};
const actionId = computed(() => {
  const fromParam = Number(route.params.actionId || 0);
  if (Number.isFinite(fromParam) && fromParam > 0) return fromParam;
  const fromQuery = Number(route.query.action_id || 0);
  return Number.isFinite(fromQuery) && fromQuery > 0 ? fromQuery : 0;
});
const actionMeta = computed(() => session.currentAction);
const routeSceneLabel = computed(() => String(route.query.scene_label || '').trim());
const menuId = computed(() => Number(route.query.menu_id ?? 0));
const keepSceneRoute = computed(() => String(route.name || '').toLowerCase() === 'scene');
const sceneKey = computed(() => {
  const metaKey = route.meta?.sceneKey as string | undefined;
  if (metaKey) return metaKey;
  const queryKey = (route.query.scene_key || route.query.scene) as string | undefined;
  if (queryKey) return String(queryKey);
  const node = findMenuNode(session.menuTree, menuId.value);
  return node ? resolveNodeSceneKey(node) : '';
});
const scene = computed<Scene | null>(() => {
  if (!sceneKey.value) return null;
  return session.scenes.find((item: Scene) => item.key === sceneKey.value || resolveSceneCode(item) === sceneKey.value) || null;
});
const pageMode = computed(() => resolvePageMode(sceneKey.value, String(scene.value?.layout?.kind || '')));
const hasLedgerOverviewStrip = computed(() => pageMode.value === 'ledger');

const sceneReadyEntry = computed<Record<string, unknown> | null>(() => {
  return findSceneReadyEntryByTarget(session.sceneReadyContractV1, {
    sceneKey: sceneKey.value,
    actionId: actionId.value,
    menuId: menuId.value,
    route: String(route.path || ''),
  });
});
const sceneReadyListSurface = computed(() => {
  const fallback = resolveListSceneReady(sceneReadyEntry.value);
  return resolveSceneFirstListSurface(sceneContractV1.value, fallback);
});
const listOptimizationRefreshAttempted = ref(false);
function applyDefaultMarkerLabel<T extends { key?: string; label?: string; isDefault?: boolean }>(rows: T[]): Array<T & { label: string }> {
  return rows.map((row) => {
    const baseLabel = String(row.label || '').trim();
    return {
      ...row,
      label: row.isDefault && baseLabel ? `${baseLabel} · 默认` : baseLabel,
    };
  });
}
function dedupeToolbarChipsByKey<T extends { key?: string }>(rows: T[]): T[] {
  const seen = new Set<string>();
  return rows.filter((row) => {
    const key = String(row?.key || '').trim();
    if (!key) return false;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}
function normalizeMetadataModeLabel(mode: string): string {
  const raw = String(mode || '').trim().toLowerCase();
  if (!raw) return '';
  if (raw === 'faceted' || raw === 'facet' || raw === 'searchpanel' || raw === 'panel') return '分面搜索';
  if (raw === 'search' || raw === 'keyword' || raw === 'fulltext') return '关键字搜索';
  if (raw === 'advanced') return '高级搜索';
  return raw.replace(/[_-]+/g, ' ');
}
const nativeDefaultSortLabel = computed(() => {
  const sceneReadyDefault = String(sceneReadyListSurface.value.defaultSort || '').trim();
  if (sceneReadyDefault) return sceneReadyDefault;
  return String(scene.value?.default_sort || '').trim();
});
const listSearchPlaceholder = computed(() => {
  const labels = listSearchableFieldMetadata.value
    .map((item) => String(item.label || '').trim())
    .filter(Boolean)
    .slice(0, 3);
  if (!labels.length) return '搜索关键字';
  if (listSearchableFieldMetadata.value.length <= labels.length) return `搜索 ${labels.join(' / ')}`;
  return `搜索 ${labels.join(' / ')} 等 ${listSearchableFieldMetadata.value.length} 项`;
});
const listSearchableFieldMetadata = computed(() => {
  const searchPanelKeys = new Set(
    listSearchPanelOptions.value
      .map((item) => String(item.key || '').trim())
      .filter(Boolean),
  );
  const rawFields = Array.isArray(sceneReadyListSurface.value.searchableFields) ? sceneReadyListSurface.value.searchableFields : [];
  return rawFields
    .map((field) => String(field || '').trim())
    .filter(Boolean)
    .map((field) => ({ key: field, label: String(contractColumnLabels.value[field] || field).trim() || field }))
    .filter((item) => !searchPanelKeys.has(item.key))
    .filter((item, index, rows) => rows.findIndex((row) => row.key === item.key) === index);
});
const listSearchableFieldOptions = computed(() =>
  listSearchableFieldMetadata.value.slice(0, 6),
);
const listSearchableFieldPreviewCount = computed(() => listSearchableFieldOptions.value.length);
const listSearchableFieldTotalCount = computed(() => listSearchableFieldMetadata.value.length);
const listSearchableFieldCountLabel = computed(() => {
  const preview = listSearchableFieldPreviewCount.value;
  const total = listSearchableFieldTotalCount.value;
  if (!total) return '0';
  if (!preview || preview >= total) return String(total);
  return `预览 ${preview} / 共 ${total}`;
});
const listSearchPanelOptions = computed(() => {
  const rows = Array.isArray(sceneReadyListSurface.value.searchPanel) ? sceneReadyListSurface.value.searchPanel : [];
  return rows
    .map((row) => {
      const raw = (row && typeof row === 'object') ? row as Record<string, unknown> : {};
      const key = String(raw.name || raw.field || '').trim();
      const fallbackLabel = String(contractColumnLabels.value[key] || key).trim() || key;
      const baseLabel = String(raw.string || raw.label || fallbackLabel).trim();
      const select = String(raw.select || '').trim().toLowerCase();
      const selectLabel = select === 'multi' ? '多选' : select ? '单选' : '';
      const label = selectLabel ? `${baseLabel} · ${selectLabel}` : baseLabel;
      if (!key || !label) return null;
      return { key, label };
    })
    .filter(Boolean)
    .filter((item, index, list) => list.findIndex((row) => row && item && row.key === item.key) === index) as Array<{ key: string; label: string }>;
});
const listSearchPanelCountLabel = computed(() => {
  const total = listSearchPanelOptions.value.length;
  if (!total) return '0';
  const multiCount = listSearchPanelOptions.value.filter((item) => item.label.includes('· 多选')).length;
  if (!multiCount) return String(total);
  const singleCount = total - multiCount;
  return `共 ${total}（单选 ${singleCount} / 多选 ${multiCount}）`;
});
const listSearchModeLabel = computed(() => {
  const mode = String(sceneReadyListSurface.value.mode || '').trim().toLowerCase();
  return normalizeMetadataModeLabel(mode);
});
const listSavedFilterOptions = computed(() =>
  applyDefaultMarkerLabel(
    dedupeToolbarChipsByKey([
      ...savedFilterPrimaryChips.value,
      ...savedFilterOverflowChips.value,
    ]),
  ),
);
const listSavedFilterCountLabel = computed(() => {
  const total = listSavedFilterOptions.value.length;
  if (!total) return '0';
  const defaultCount = listSavedFilterOptions.value.filter((chip) => Boolean((chip as { isDefault?: boolean }).isDefault)).length;
  return defaultCount > 0 ? `${total}，默认 ${defaultCount}` : String(total);
});
const listGroupByOptions = computed(() =>
  applyDefaultMarkerLabel(
    dedupeToolbarChipsByKey([
      ...groupByPrimaryChips.value,
      ...groupByOverflowChips.value,
    ]),
  ),
);
const listGroupByToolbarOptions = computed(() => {
  if (!vm.value.filters.groupBy.visible) return [];
  return listGroupByOptions.value;
});
const listGroupByCountLabel = computed(() => {
  const total = listGroupByToolbarOptions.value.length;
  if (!total) return '0';
  const defaultCount = listGroupByToolbarOptions.value.filter((chip) => Boolean((chip as { isDefault?: boolean }).isDefault)).length;
  return defaultCount > 0 ? `${total}，默认 ${defaultCount}` : String(total);
});
const listRoutePresetDisplayLabel = computed(() => {
  const rawLabel = String(appliedPresetLabel.value || '').trim();
  if (!rawLabel) return '';
  const presetFilterKey = String(route.query.preset_filter || '').trim();
  if (presetFilterKey) {
    const matchedQuick = contractFilterChips.value.find((chip) => String((chip as { key?: string }).key || '') === presetFilterKey) as { label?: string } | undefined;
    if (matchedQuick?.label) return `快速筛选：${matchedQuick.label}`;
  }
  const savedFilterKey = String(route.query.saved_filter || '').trim();
  if (savedFilterKey) {
    const matchedSaved = listSavedFilterOptions.value.find((chip) => chip.key === savedFilterKey);
    if (matchedSaved?.label) return `已保存筛选：${matchedSaved.label}`;
  }
  const groupByFieldKey = String(route.query.group_by || '').trim();
  if (groupByFieldKey) {
    const matchedGroup = listGroupByOptions.value.find((chip) => chip.key === groupByFieldKey);
    if (matchedGroup?.label) return `分组：${matchedGroup.label}`;
  }
  if (/^[a-z0-9_:-]+$/i.test(rawLabel) && rawLabel.includes('_')) {
    return '推荐预设';
  }
  return rawLabel;
});
const routePresetBannerSourceText = computed(() => {
  const raw = String(routeContextSource.value || '').trim().toLowerCase();
  if (!raw) return '';
  if (raw === 'scene' || raw === 'route' || raw === 'query' || raw === 'url') return '路由上下文';
  if (raw === 'menu') return '菜单';
  if (raw === 'recommended' || raw === 'preset') return '系统推荐';
  return raw.replace(/[_-]+/g, ' ');
});
const listOptimizationComposition = computed(() => {
  const raw = (sceneReadyEntry.value && typeof sceneReadyEntry.value === 'object')
    ? ((sceneReadyEntry.value as Record<string, unknown>).optimization_composition as Record<string, unknown> | undefined)
    : undefined;
  if (!raw || typeof raw !== 'object') return null;
  const toolbarSectionsRaw = Array.isArray(raw.toolbar_sections) ? raw.toolbar_sections : [];
  return {
    toolbarSections: toolbarSectionsRaw
      .map((row) => {
        const payload = (row && typeof row === 'object') ? row as Record<string, unknown> : {};
        const key = String(payload.key || '').trim();
        if (!key) return null;
        return {
          key,
          kind: String(payload.kind || key).trim() || key,
          priority: Number(payload.priority || 0),
          visible: payload.visible !== false,
          collapsible: Boolean(payload.collapsible),
          defaultOpen: payload.default_open !== false,
        };
      })
      .filter(Boolean),
    activeConditions: (raw.active_conditions && typeof raw.active_conditions === 'object')
      ? {
          visible: (raw.active_conditions as Record<string, unknown>).visible !== false,
          include: Array.isArray((raw.active_conditions as Record<string, unknown>).include)
            ? ((raw.active_conditions as Record<string, unknown>).include as unknown[]).map((item) => String(item || '').trim()).filter(Boolean)
            : [],
          mergeRules: ((raw.active_conditions as Record<string, unknown>).merge_rules && typeof (raw.active_conditions as Record<string, unknown>).merge_rules === 'object')
            ? (raw.active_conditions as Record<string, unknown>).merge_rules as Record<string, unknown>
            : {},
        }
      : null,
    highFrequencyFilters: Array.isArray(raw.high_frequency_filters)
      ? raw.high_frequency_filters
          .map((row) => {
            const payload = (row && typeof row === 'object') ? row as Record<string, unknown> : {};
            const key = String(payload.key || payload.name || '').trim();
            return key ? { key } : null;
          })
          .filter(Boolean)
      : [],
    advancedFilters: (raw.advanced_filters && typeof raw.advanced_filters === 'object')
      ? {
          visible: (raw.advanced_filters as Record<string, unknown>).visible !== false,
          collapsible: (raw.advanced_filters as Record<string, unknown>).collapsible !== false,
          defaultOpen: Boolean((raw.advanced_filters as Record<string, unknown>).default_open),
          source: ((raw.advanced_filters as Record<string, unknown>).source && typeof (raw.advanced_filters as Record<string, unknown>).source === 'object')
            ? (raw.advanced_filters as Record<string, unknown>).source as Record<string, unknown>
            : {},
        }
      : null,
  };
});
const shouldRefreshListOptimizationComposition = computed(() => {
  if (listOptimizationRefreshAttempted.value) return false;
  if (!sceneKey.value) return false;
  if (!sceneReadyEntry.value) return false;
  const hasListTruth =
    sceneReadyListSurface.value.columns.length > 0
    || sceneReadyListSurface.value.filters.length > 0
    || sceneReadyListSurface.value.groupBy.length > 0
    || sceneReadyListSurface.value.searchPanel.length > 0
    || sceneReadyListSurface.value.searchableFields.length > 0;
  if (!hasListTruth) return false;
  return !listOptimizationComposition.value;
});

async function refreshListOptimizationCompositionOnce() {
  if (!shouldRefreshListOptimizationComposition.value) return;
  listOptimizationRefreshAttempted.value = true;
  try {
    await session.loadAppInit();
  } catch (error) {
    console.warn('[ActionView] failed to refresh scene-ready optimization composition', error);
  }
}
const {
  strictContractMode,
  strictSurfaceContract,
  strictProjectionContract,
  strictContractMissingSummary,
  strictContractDefaultsSummary,
  strictAdvancedViewContract,
  strictViewModeLabelMap,
} = useActionViewStrictContractBundle({
  sceneKey,
  sceneReadyEntry,
  pageText,
});

const injectedTitle = inject('pageTitle', computed(() => ''));
const contractViewType = ref('');
const contractReadAllowed = ref(true);
const contractWarningCount = ref(0);
const contractDegraded = ref(false);
const actionContract = ref<ActionContractLoose | null>(null);
const semanticZones = computed<Array<Record<string, unknown>>>(() => {
  const contract = actionContract.value as Record<string, unknown> | null;
  if (!contract || typeof contract !== 'object') return [];
  const semanticPage = contract.semantic_page;
  if (!semanticPage || typeof semanticPage !== 'object' || Array.isArray(semanticPage)) return [];
  const zones = (semanticPage as Record<string, unknown>).zones;
  if (!Array.isArray(zones)) return [];
  return zones
    .filter((item) => item && typeof item === 'object' && !Array.isArray(item))
    .map((item) => item as Record<string, unknown>);
});
const resolvedModelRef = ref('');
const model = computed(() => {
  const actionModel = String(actionMeta.value?.model || '').trim();
  if (actionModel) return actionModel;
  const resolvedModel = String(resolvedModelRef.value || '').trim();
  if (resolvedModel) return resolvedModel;
  const contractModel = String(actionContract.value?.head?.model || actionContract.value?.model || '').trim();
  return contractModel;
});
const contractRights = computed(() => resolveContractRights(actionContract.value));
const enterpriseBootstrapCreateLabel = computed(() => {
  if (vm.value.content.kind !== 'list') return '';
  if (model.value === 'res.company') return '新建公司';
  if (model.value === 'hr.department') return '新建部门';
  if (model.value === 'res.users') return '新建用户';
  return '';
});
const canBatchDelete = computed(() => {
  if (String(model.value || '').trim() === 'project.project') return false;
  return contractRights.value.unlink === true && viewMode.value === 'tree';
});
const batchDeleteOnlyModels = new Set(['project.task', 'res.company', 'hr.department', 'res.users']);
const useDeleteOnlyBatchMode = computed(() => {
  return viewMode.value === 'tree' && batchDeleteOnlyModels.has(String(model.value || '').trim());
});
const activeGroupByField = ref('');
const {
  activeContractFilterKey,
  activeSavedFilterKey,
  contractLimit,
  preferredViewMode,
} = useActionViewFilterUiStateRuntime();
const {
  showMoreContractActions,
  showMoreContractFilters,
  showMoreSavedFilters,
} = useActionViewTemplateUiStateRuntime();
const {
  toggleMoreContractFilters,
  toggleMoreSavedFilters,
  toggleMoreGroupBy,
  toggleMoreContractActions,
} = useActionViewTemplateInteractionRuntime({
  showMoreContractFilters,
  showMoreSavedFilters,
  showMoreGroupBy,
  showMoreContractActions,
});
const availableViewModes = computed(() =>
  resolveActionViewAvailableModes({
    contractViewTypeRaw: contractViewType.value,
    metaViewModesRaw: (actionMeta.value as { view_modes?: unknown } | null)?.view_modes,
    metaViewsRaw: (actionMeta.value as { views?: unknown } | null)?.views,
    contract: (actionContract.value as Record<string, unknown> | null),
  }),
);
const viewMode = computed(() => {
  const modes = availableViewModes.value;
  const mode = normalizeActionViewMode(preferredViewMode.value) || modes[0] || '';
  if (mode === 'kanban') return 'kanban';
  if (mode === 'form') return 'form';
  if (mode === 'list' || mode === 'tree') return 'tree';
  if (mode === 'pivot' || mode === 'graph' || mode === 'calendar' || mode === 'gantt' || mode === 'activity' || mode === 'dashboard') {
    return mode;
  }
  return '';
});

function resolveFormTargetId(): string {
  const fromQuery = String(route.query.id || route.query.res_id || route.query.active_id || '').trim();
  if (/^\d+$/.test(fromQuery)) return fromQuery;
  return 'new';
}

watch(
  [viewMode, model],
  ([mode, modelName]) => {
    if (mode !== 'form') return;
    const normalizedModel = String(modelName || '').trim();
    if (!normalizedModel) return;
    if (route.name === 'model-form' && String(route.params.model || '').trim() === normalizedModel) return;
    const carryQuery = pickContractNavQuery(route.query as Record<string, unknown>, {
      action_id: actionId.value || undefined,
      menu_id: menuId.value || undefined,
    });
    void router.push({
      name: 'model-form',
      params: { model: normalizedModel, id: resolveFormTargetId() },
      query: carryQuery,
    }).catch(() => {});
  },
  { immediate: true },
);

const {
  viewModeLabel,
  switchViewMode,
} = useActionViewModeRuntime({
  strictContractMode,
  strictViewModeLabelMap,
  pageText,
  preferredViewMode,
  viewMode,
  normalizeActionViewMode,
  resolveActionViewModeLabel,
  beforeSwitchViewMode: async (mode: string) => {
    const currentMode = normalizeActionViewMode(route.query.view_mode);
    if (!mode || currentMode === mode) return;
    await router.replace({
      query: {
        ...(route.query as Record<string, unknown>),
        view_mode: mode,
      },
    } as never).catch(() => {});
  },
  load: requestLoad,
});
const sceneContractV1 = computed<Record<string, unknown>>(() => {
  const raw = pageContract.contract.value?.scene_contract_v1;
  if (!raw || typeof raw !== 'object') return {};
  if (String((raw as Record<string, unknown>).contract_version || '') !== 'v1') return {};
  return raw as Record<string, unknown>;
});
function actionViewRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : {};
}

function sceneListColumns(semantics: Record<string, unknown>) {
  const columnsRaw = Array.isArray(semantics.columns) ? semantics.columns : [];
  const columnLabels: Record<string, string> = {};
  const columns = columnsRaw
    .map((item) => {
      if (typeof item === 'string') return item.trim();
      if (!item || typeof item !== 'object' || Array.isArray(item)) return '';
      const row = item as Record<string, unknown>;
      const name = String(row.name || row.field || row.key || '').trim();
      const label = String(row.label || row.string || '').trim();
      if (name && label) columnLabels[name] = label;
      return name;
    })
    .filter(Boolean);
  return { columns, columnLabels };
}

function sceneDefaultSort(raw: unknown): string {
  if (typeof raw === 'string') return raw.trim();
  const row = actionViewRecord(raw);
  return String(row.raw || row.value || '').trim();
}

function resolveSceneFirstListSurface(contract: Record<string, unknown>, fallback: ReturnType<typeof resolveListSceneReady>) {
  const semanticPage = actionViewRecord(contract.semantic_page);
  const semantics = actionViewRecord(semanticPage.list_semantics);
  const searchSurface = actionViewRecord(contract.search_surface);
  const { columns } = sceneListColumns(semantics);
  const defaultSort = sceneDefaultSort(searchSurface.default_sort);
  const mode = String(searchSurface.mode || '').trim();
  const filters = Array.isArray(searchSurface.filters) ? searchSurface.filters : [];
  const groupBy = Array.isArray(searchSurface.group_by) ? searchSurface.group_by : [];
  const searchPanel = Array.isArray(searchSurface.searchpanel) ? searchSurface.searchpanel : [];
  const searchableFields = Array.isArray(searchSurface.fields)
    ? searchSurface.fields
    : Array.isArray(searchSurface.searchable_fields)
      ? searchSurface.searchable_fields
      : [];
  const hasSceneSurface = Boolean(
    columns.length
    || defaultSort
    || mode
    || filters.length
    || groupBy.length
    || searchPanel.length
    || searchableFields.length,
  );
  if (!hasSceneSurface) return fallback;
  return {
    ...fallback,
    columns: columns.length ? columns : fallback.columns,
    defaultSort: defaultSort || fallback.defaultSort,
    mode: mode || fallback.mode,
    filters: filters.length ? filters : fallback.filters,
    groupBy: groupBy.length ? groupBy : fallback.groupBy,
    searchPanel: searchPanel.length ? searchPanel : fallback.searchPanel,
    searchableFields: searchableFields.length ? searchableFields : fallback.searchableFields,
  };
}

function normalizeSceneListProfile(contract: Record<string, unknown>): SceneListProfile | null {
  const semantics = resolveContractListSemantics(contract);
  const { columns, columnLabels } = sceneListColumns(semantics);
  const hiddenColumns = Array.isArray(semantics.hidden_columns)
    ? semantics.hidden_columns.map((item) => String(item || '').trim()).filter(Boolean)
    : [];
  const rowPrimary = String(semantics.row_primary || '').trim();
  const rowSecondary = String(semantics.row_secondary || '').trim();
  if (!columns.length && !hiddenColumns.length && !rowPrimary && !rowSecondary) return null;
  return {
    columns,
    hidden_columns: hiddenColumns,
    column_labels: columnLabels,
    row_primary: rowPrimary,
    row_secondary: rowSecondary,
  };
}
const listProfile = computed<SceneListProfile | null>(() => {
  return normalizeSceneListProfile(sceneContractV1.value)
    || (scene.value?.list_profile as SceneListProfile)
    || null;
});
const {
  contractColumnLabels,
  extractColumnsFromContract,
  convergeColumnsForSurface,
  extractKanbanFields,
  extractKanbanProfile,
  extractAdvancedViewFields,
  advancedRowTitle,
  advancedRowMeta,
  buildGroupKey,
  resolveModelFromContract,
  resolveModeRecommendedRuntime,
} = useActionViewContractShapeRuntime({
  pageText,
  actionContract,
  advancedFields,
  activeGroupByField,
});
const {
  sortLabel,
  sortDisplayLabel,
  sortSourceLabel,
  surfaceKind,
} = useActionViewSurfaceDisplayRuntime({
  sortValue,
  nativeDefaultSort: nativeDefaultSortLabel,
  contractColumnLabels,
  sceneContractV1,
  strictContractMode,
  strictSurfaceContract,
  actionContract,
  resolveActionViewSurfaceKind,
});
const {
  sortOptions,
  subtitle,
  statusLabel,
  pageStatus,
  recordCount,
} = useActionViewDisplayComputedRuntime({
  surfaceKind,
  records,
  sortDisplayLabel,
  sortSourceLabel,
  status,
  listTotalCount,
  pageText,
});

const {
  resolveProjectStateCell,
  resolveProjectAmount,
  isCompletedState,
  resolveDefaultSort,
} = useActionViewProjectMetricRuntime();

const {
  ledgerOverviewItems,
  listSummaryItems,
  kanbanTitleField,
} = useActionViewContentDisplayRuntime({
  strictProjectionContract,
  mapProjectionMetricItems,
  kanbanTitleFieldHint,
  kanbanFields,
});
const {
  advancedViewTitle,
  advancedViewHint,
} = useActionViewAdvancedDisplayRuntime({
  strictContractMode,
  strictAdvancedViewContract,
  viewMode,
  pageText,
  resolveActionViewAdvancedTitle,
  resolveActionViewAdvancedHint,
});
const {
  surfaceIntent,
} = useActionViewSurfaceIntentRuntime({
  actionContract,
  sceneContractV1,
  strictContractMode,
  strictSurfaceContract,
  sceneKey,
  pageText,
  resolveActionViewSurfaceIntent,
});
const actionMetaName = computed(() => String(actionMeta.value?.name || '').trim());
const baseErrorMessage = computed(() => (error.value?.code ? `code=${error.value.code} · ${error.value.message}` : error.value?.message || ''));
const {
  pageTitle,
  emptyReasonText,
  showHud,
  errorMessage,
} = useActionViewPageDisplayStateRuntime({
  routeSceneLabel,
  actionContract,
  sceneContractV1,
  injectedTitle,
  actionMetaName,
  t,
  searchTerm,
  activeContractFilterKey,
  errorMessage: baseErrorMessage,
  route,
  isHudEnabled,
});

function resolveContractActionCountForHud() {
  const sceneActions = sceneReadyListSurface.value.actions;
  if (sceneActions.length) return sceneActions.length;

  const contract = actionContract.value;
  if (!contract) return 0;

  const buttons = Array.isArray(contract.buttons) ? contract.buttons : [];
  if (buttons.length) return buttons.length;

  const toolbar = typeof contract.toolbar === 'object' && contract.toolbar
    ? (contract.toolbar as Record<string, unknown>)
    : {};
  const header = Array.isArray(toolbar.header) ? toolbar.header.length : 0;
  const sidebar = Array.isArray(toolbar.sidebar) ? toolbar.sidebar.length : 0;
  const footer = Array.isArray(toolbar.footer) ? toolbar.footer.length : 0;
  return header + sidebar + footer;
}
const {
  contractFilterChips,
  contractPrimaryFilterChips,
  contractOverflowFilterChips,
  contractSavedFilterChips,
  savedFilterPrimaryChips,
  savedFilterOverflowChips,
  contractGroupByChips,
  groupByPrimaryChips,
  groupByOverflowChips,
  activeGroupByLabel,
} = useActionViewFilterComputedRuntime({
  sceneReadyListSurface,
  actionContract,
  activeGroupByField,
  parseContractContextRaw,
  isActionViewNumericToken,
  hasActionViewNoiseMarker,
});
const {
  toContractActionButton,
} = useActionViewContractActionButtonRuntime({
  selectedIds,
  resolvedModelRef,
  modelRef: model,
  userGroupsXmlids: () => session.user?.groups_xmlids || [],
  pageText,
  isActionViewNumericToken,
  hasActionViewNoiseMarker,
  normalizeSceneActionProtocol,
  parseContractContextRaw,
  normalizeActionKind,
  toPositiveInt,
  detectObjectMethodFromActionKey,
});
const {
  resolveContractActionPresentation,
} = useActionViewActionGroupingRuntime();
const {
  contractPrimaryActions,
  contractOverflowActionGroups,
} = useActionViewActionPresentationRuntime({
  actionContract,
  sceneContractV1,
  sceneReadyListSurface,
  strictContractMode,
  toContractActionButton: (row, dedup) => toContractActionButton(row, dedup) as ContractActionButton | null,
  resolveContractActionPresentation,
  pageText,
});

const actionableViewModes = computed(() => {
  const modes = availableViewModes.value;
  const hasKanban = modes.includes('kanban');
  const normalizedModes = hasKanban && !modes.includes('tree')
    ? ['tree', ...modes]
    : modes;
  const filtered = normalizedModes.filter((mode) => {
    if (mode === 'kanban') return true;
    if (mode === 'form') return true;
    if (mode === 'tree' && hasKanban) return true;
    return resolveModeRecommendedRuntime(actionContract.value, mode) !== 'native';
  });
  return filtered.length ? filtered : normalizedModes;
});
const showViewSwitchDebug = computed(() => isHudEnabled(route) && String(route.query.debug_view_switch || '').trim() === '1');
const viewSwitchDebugState = computed(() => ({
  routePath: route.fullPath,
  actionId: Number(route.params.actionId || 0),
  contractViewType: contractViewType.value,
  actionMetaViewModes: (actionMeta.value as { view_modes?: unknown } | null)?.view_modes ?? null,
  actionMetaViews: (actionMeta.value as { views?: unknown } | null)?.views ?? null,
  availableViewModes: availableViewModes.value,
  actionableViewModes: actionableViewModes.value,
  vmAvailableViewModes: vm.value.page.availableViewModes,
  currentViewMode: viewMode.value,
  preferNativeListSurface: preferNativeListSurface.value,
  nativeRecommendedRuntime: nativeFallbackPolicy.value.recommendedRuntime,
}));
const nativeFallbackPolicy = computed(() => resolveContractViewRenderPolicy(actionContract.value, viewMode.value || contractViewType.value));
const nativeFallbackUrl = computed(() => {
  const action = nativeFallbackPolicy.value.fallbackAction;
  return Object.keys(action || {}).length ? buildNativeFallbackUrl(action) : '';
});
const showNativeFallbackPanel = computed(() => nativeFallbackPolicy.value.recommendedRuntime === 'native' && Boolean(nativeFallbackUrl.value));
const nativeFallbackMessage = computed(() => {
  const reason = nativeFallbackPolicy.value.notes[0] || '当前页面命中了原生兜底条件。';
  return `${reason} 请使用原生页面完成本次操作。`;
});

const { vm } = useActionPageModel({
  page: {
    title: pageTitle,
    status: pageStatus,
    statusLabel,
    subtitle,
    traceId,
    errorMessage,
    sceneKey,
    pageMode,
    viewMode,
    availableViewModes: actionableViewModes,
  },
  headerActions,
  routePreset: {
    label: appliedPresetLabel,
    source: routeContextSource,
  },
  filters: {
    quickPrimary: contractPrimaryFilterChips,
    quickOverflow: contractOverflowFilterChips,
    savedPrimary: savedFilterPrimaryChips,
    savedOverflow: savedFilterOverflowChips,
    groupByPrimary: groupByPrimaryChips,
    groupByOverflow: groupByOverflowChips,
  },
  focus: {
    surfaceIntent,
  },
  strict: {
    missingSummary: strictContractMissingSummary,
    defaultsSummary: strictContractDefaultsSummary,
    title: computed(() => t('strict_contract_missing_title', '契约缺口提示')),
  },
  groupSummary: {
    items: groupSummaryItems,
  },
  actions: {
    primary: contractPrimaryActions,
    overflowGroups: contractOverflowActionGroups,
  },
  content: {
    listSummaryItems,
    kanbanOverviewItems: ledgerOverviewItems,
    advancedTitle: advancedViewTitle,
    advancedHint: advancedViewHint,
    advancedRecords: records,
    resolveAdvancedRowTitle: (row) => advancedRowTitle(row),
    resolveAdvancedRowMeta: (row) => advancedRowMeta(row),
  },
  empty: {
    reasonText: emptyReasonText,
  },
  hud: {
    visible: showHud,
    title: '',
    state: {
      actionId,
      menuId,
      sceneKey,
      model,
      viewMode,
      contractViewType,
      activeContractFilterKey,
      activeSavedFilterKey,
      activeGroupByField,
      groupWindowOffset,
      groupWindowId,
      groupQueryFingerprint,
      groupWindowDigest,
      groupWindowIdentityKey,
      routeGroupFp: computed(() => String(route.query.group_fp || '').trim()),
      routeGroupWid: computed(() => String(route.query.group_wid || '').trim()),
      routeGroupWdg: computed(() => String(route.query.group_wdg || '').trim()),
      routeGroupWik: computed(() => String(route.query.group_wik || '').trim()),
      contractActionCount: computed(() => resolveContractActionCountForHud()),
      contractLimit,
      contractReadAllowed,
      contractWarningCount,
      contractDegraded,
      sortLabel,
      lastIntent,
      lastWriteMode,
      traceId,
      lastTraceId,
      lastLatencyMs,
      routeFullPath: computed(() => route.fullPath),
    },
  },
});

const canCreateListRecord = computed(() => {
  const bootstrapCreate = Boolean(enterpriseBootstrapCreateLabel.value);
  return vm.value.content.kind === 'list'
    && nativeFallbackPolicy.value.recommendedRuntime !== 'native'
    && Boolean(model.value)
    && (contractRights.value.create === true || bootstrapCreate);
});
const listPrimaryActionLabel = computed(() => {
  if (!canCreateListRecord.value) return '';
  if (enterpriseBootstrapCreateLabel.value) return enterpriseBootstrapCreateLabel.value;
  return '新建记录';
});
function openListCreateForm() {
  if (isListInteractionLocked.value) return;
  if (!canCreateListRecord.value || !model.value) return;
  router.push({
    name: 'model-form',
    params: { model: model.value, id: 'new' },
    query: pickContractNavQuery(route.query as Record<string, unknown>, {
      action_id: actionId.value || undefined,
    }),
  });
}
const listPrimaryAction = computed(() => (canCreateListRecord.value ? openListCreateForm : null));

function handlePageChange(nextOffset: number) {
  if (isListInteractionLocked.value) return;
  const normalized = Math.max(0, Math.trunc(Number(nextOffset || 0)));
  if (normalized === listOffset.value) return;
  listOffset.value = normalized;
  clearSelection();
  void requestLoad();
}

watchEffect(() => {
  if (typeof window === 'undefined') return;
  (window as Window & { __scActionDebug?: Record<string, unknown> }).__scActionDebug = {
    actionId: actionId.value,
    contractViewType: contractViewType.value,
    availableViewModes: availableViewModes.value,
    preferredViewMode: preferredViewMode.value,
    viewMode: viewMode.value,
    model: model.value,
    resolvedModel: resolvedModelRef.value,
    pageMode: pageMode.value,
    contentKind: vm.value.content.kind,
    canCreateListRecord: canCreateListRecord.value,
    listPrimaryActionLabel: listPrimaryActionLabel.value,
    nativeFallbackRecommendedRuntime: nativeFallbackPolicy.value.recommendedRuntime,
    contractCreateRight: contractRights.value.create,
    contractHeadViewType: actionContract.value?.head?.view_type,
    contractNestedHeadViewType: (actionContract.value as Record<string, unknown> | null)?.ui_contract
      && typeof (actionContract.value as Record<string, unknown>).ui_contract === 'object'
      ? ((actionContract.value as Record<string, unknown>).ui_contract as Record<string, unknown>)?.head && typeof ((actionContract.value as Record<string, unknown>).ui_contract as Record<string, unknown>).head === 'object'
        ? (((((actionContract.value as Record<string, unknown>).ui_contract as Record<string, unknown>).head as Record<string, unknown>).view_type) || '')
        : ''
      : '',
  };
});

const {
  resolveWorkspaceContextQuery,
  resolveCarryQuery,
  resolveWorkbenchQuery,
  handleRowClick,
} = useActionViewNavigationRuntime({
  routeQueryMap,
  showHud,
  menuId,
  actionId,
  resolvedModelRef,
  modelRef: model,
  routerPush: (target) => router.push(target),
});

const {
  applyRoutePreset,
  clearRoutePreset,
  applyRoutePatchAndReload,
  syncRouteListState,
  syncRouteStateAndReload,
  restartLoadWithRouteSync,
} = useActionViewRoutePresetRuntime({
  routeQueryMap,
  pageText,
  showHud,
  menuId,
  actionId,
  searchTerm,
  sortValue,
  filterValue,
  activeSavedFilterKey,
  activeGroupByField,
  groupWindowOffset,
  groupQueryFingerprint,
  groupWindowId,
  groupWindowDigest,
  groupWindowIdentityKey,
  activeGroupSummaryKey,
  activeGroupSummaryDomain,
  groupSampleLimit,
  groupSort,
  collapsedGroupKeys,
  groupPageOffsets,
  appliedPresetLabel,
  routeContextSource,
  lastTrackedPreset,
  resolveWorkspaceContextQuery,
  replaceCurrentRouteQuery: (query) => {
    const routeState = resolveReplaceCurrentRouteState({ routePath: route.path, query });
    router.replace(routeState.target as Parameters<typeof router.replace>[0]).catch(() => {});
  },
  trackUsageEvent,
  load: requestLoad,
  resolveActionViewRouteSnapshot,
  resolveRoutePresetSearchTerm,
  resolveRoutePresetAppliedLabel,
  resolveRoutePresetActiveFilterValue,
  resolveRoutePresetSavedFilterValue,
  resolveRoutePresetGroupWindowState,
  resolveRoutePresetGroupSummaryResetState,
  resolveRoutePresetGroupVisualState,
  parseGroupPageOffsets,
  hasRoutePresetGroupPageStateChanged,
  resolveRoutePresetGroupPageState,
  resolveRoutePresetTrackingState,
  buildActionViewClearedPresetQuery,
  buildActionViewPatchedRouteQuery,
  buildActionViewRouteSyncStatePayload,
  buildActionViewSyncedRouteQuery,
  resolveRouteSyncExtra,
  resolveRouteSyncShouldAwaitLoad,
});

const {
  handleGroupSummaryPick,
  handleOpenGroupedRows,
  clearGroupSummaryDrilldown,
  handleGroupWindowPrev,
  handleGroupWindowNext,
  handleGroupSampleLimitChange,
  handleGroupSortChange,
  handleGroupCollapsedChange,
} = useActionViewGroupRuntime({
  activeGroupSummaryKey,
  activeGroupSummaryDomain,
  searchTerm,
  groupWindowOffset,
  groupWindowPrevOffset,
  groupWindowNextOffset,
  groupSampleLimit,
  groupSort,
  collapsedGroupKeys,
  groupPageOffsets,
  syncRouteStateAndReload,
  syncRouteListState,
  applyRoutePatchAndReload,
  applyGroupSharedState: (state) => {
    groupRuntimeCapsule.applySharedState(state);
  },
});

const {
  applyContractFilter,
  applySavedFilter,
  clearContractFilter,
  clearSavedFilter,
  applyGroupBy,
  clearGroupBy,
} = useActionViewFilterGroupRuntime({
  activeContractFilterKey,
  showMoreContractFilters,
  activeSavedFilterKey,
  showMoreSavedFilters,
  activeGroupByField,
  clearSelection,
  applyRoutePatchAndReload,
  applyGroupSharedState: (state) => {
    groupRuntimeCapsule.applySharedState(state);
  },
});

const {
  resolveEffectiveFilterDomain,
  resolveEffectiveFilterDomainRaw,
  resolveEffectiveRequestContext,
  resolveEffectiveRequestContextRaw,
  mergeContext,
  mergeActiveFilterDomain,
} = useActionViewRequestContextRuntime({
  routeContextRaw: () => String(route.query.context_raw || '').trim(),
  menuId,
  hasActiveField,
  filterValue,
  contractFilterChips,
  activeContractFilterKey,
  contractSavedFilterChips,
  activeSavedFilterKey,
  activeGroupSummaryDomain,
  contractGroupByChips,
  activeGroupByField,
});

const {
  handleGroupedRowsPageChange,
  hydrateGroupedRowsByOffset,
  normalizeGroupedRouteState,
} = useActionViewGroupedRowsRuntime({
  activeGroupByField,
  groupWindowOffset,
  collapsedGroupKeys,
  groupPageOffsets,
  groupedRows,
  groupSummaryItems,
  activeGroupSummaryKey,
  activeGroupSummaryDomain,
  groupSampleLimit,
  columns,
  listProfile,
  sortLabel,
  routeQueryMap,
  resolvedModelRef,
  modelRef: model,
  actionMetaContext: () => actionMeta.value?.context,
  resolveEffectiveRequestContext,
  resolveEffectiveRequestContextRaw,
  mergeContext,
  syncRouteListState,
  listRecordsRaw,
});

const {
  reload,
  openFocusAction,
  executeHeaderAction,
} = useActionViewHeaderRuntime({
  batchMessage,
  pageText,
  syncRouteListState,
  load: requestLoad,
  resolveReloadTriggerPlan,
  resolveFocusActionPushState,
  resolveWorkspaceContextQuery,
  routerPush: (target) => router.push(target),
  executePageContractAction,
  router,
  pageActionIntent,
  pageActionTarget,
  isHeaderActionDisabled: (actionKey) => {
    const matched = displayHeaderActions.value.find((item) => item.key === actionKey);
    return matched?.enabled === false;
  },
  onHeaderActionBlocked: (actionKey) => {
    const matched = displayHeaderActions.value.find((item) => item.key === actionKey);
    batchMessage.value = matched?.hint || pageText('error_fallback', '操作暂不可用');
  },
});

function openNativeFallback() {
  if (!nativeFallbackUrl.value) return;
  window.location.assign(nativeFallbackUrl.value);
}

function resolveActionViewSuggestedHint(...args: Parameters<typeof resolveSuggestedAction>) {
  return resolveSuggestedAction(...args);
}

function runActionViewSuggestedAction(...args: Parameters<typeof runSuggestedAction>) {
  runSuggestedAction(...args);
}

const {
  fetchScopedTotal,
  fetchProjectScopeMetrics,
} = useActionViewScopedMetricsRuntime({
  listRecordsRaw,
  resolveProjectStateCell,
  isCompletedState,
  resolveProjectAmount,
});

const {
  downloadCsvBase64: downloadCsvBase64Runtime,
  applyBatchFailureArtifacts,
  handleBatchDetailAction,
} = useActionViewBatchArtifactGlueRuntime({
  batchDetails,
  batchFailedOffset,
  batchFailedLimit,
  batchHasMoreFailures,
  failedCsvFileName,
  failedCsvContentB64,
  pageText,
  resolveSuggestedAction: resolveActionViewSuggestedHint,
  describeSuggestedAction,
  runSuggestedAction: runActionViewSuggestedAction,
  reload,
  resolveBatchFailurePreviewState,
  resolveBatchRetryTagTexts,
  resolveBatchFailureLinesState,
  resolveBatchFailureHintResolver,
  resolveBatchFailureActionMetaResolver,
  resolveBatchFailureDetailMergeState,
  resolveBatchFailurePagingApplyState,
  resolveBatchFailureCsvApplyState,
});

const {
  getActionType,
  isClientAction,
  isUrlAction,
  resolveNavigationUrl,
  redirectUrlAction,
  isWindowAction,
} = useActionViewActionMetaRuntime({
  actionUnsupportedCode: ErrorCodes.ACT_UNSUPPORTED_TYPE,
  configApiBaseUrl: config.apiBaseUrl,
  menuId,
  actionId,
  buildWorkbenchRouteTarget,
  resolveWorkbenchQuery,
  buildPathRouteTarget,
  resolveCarryQuery,
  resolveUrlUnsupportedRedirectState,
  resolvePortalSelfRedirectState,
  routerReplace: async (target) => router.replace(target as never),
  openWindow: (url, target) => {
    window.open(url, target, 'noopener,noreferrer');
  },
  assignLocation: (url) => {
    window.location.assign(url);
  },
});

const {
  applyActionRefreshPolicy,
  runOpenAction,
  navigateByResponse,
} = useActionViewActionEffectsRuntime({
  load: requestLoad,
  sessionLoadAppInit: () => session.loadAppInit(),
  recordIntentTrace: (payload) => session.recordIntentTrace(payload),
  resolveOpenNavigation: (input) => resolveContractActionOpenNavigation({ actionId: input.actionId, url: input.url }),
  buildRouteTarget: (nextActionId) => buildContractActionRouteTarget({
    nextActionId,
    carryQuery: resolveCarryQuery(),
    menuId: menuId.value,
    keepSceneRoute: keepSceneRoute.value,
    routePath: route.path,
  }),
  routerPush: async (target) => router.push(target as never),
  resolveNavigationUrl,
  openWindow: (url, target) => {
    window.open(url, target, 'noopener,noreferrer');
  },
  pageText,
  resolveMissingOpenTargetMessage: (text) => resolveContractActionMissingOpenTargetMessage(text),
  executeProjectionRefresh: async (payload) => {
    await executeProjectionRefresh(payload as {
      policy: ProjectionRefreshPolicy;
      refreshScene: () => Promise<void>;
      refreshWorkbench: () => Promise<void>;
      refreshRoleSurface: () => Promise<void>;
      recordTrace: (input: { intent: string; writeMode: string; latencyMs?: number }) => void;
    });
  },
  resolveResponseActionId: resolveContractActionResponseActionId,
  shouldNavigate: shouldNavigateContractAction,
});

const { runContractAction } = useActionViewActionRuntime({
  selectedIds,
  batchBusy,
  batchMessage,
  pageText,
  load: requestLoad,
  resolveActionContextRecordId: () => {
    const fromRoute = toPositiveInt(route.query.res_id);
    if (fromRoute) return fromRoute;
    const fromContract = toPositiveInt(actionContract.value?.head?.res_id);
    if (fromContract) return fromContract;
    return null;
  },
  resolveExecIds: resolveContractActionExecIds,
  resolveRunIds: resolveContractActionRunIds,
  resolveCounters: resolveContractActionCounters,
  resolveDoneMessage: resolveContractActionDoneMessage,
  resolveRequiresRecordContextMessage: resolveContractActionRequiresRecordContextMessage,
  resolveSelectionBlockMessage: resolveContractActionSelectionBlockMessage,
  resolveMissingModelMessage: resolveContractActionMissingModelMessage,
  applyActionRefreshPolicy,
  runOpenAction,
  executeSceneMutation,
  executeButton,
  buildButtonRequest: buildContractActionButtonRequest,
  navigateByResponse,
});

const { loadAssigneeOptions } = useActionViewAssigneeRuntime({
  hasAssigneeField,
  assigneeOptions,
  selectedAssigneeId,
  batchMessage,
  pageText,
  resolveAssigneeOptionsLoadGuard,
  resolveAssigneeLoadSuccessState,
  resolveAssigneeLoadFailureState,
  resolveAssigneeOptions,
  resolveAssigneePermissionWarning,
  resolveAssigneePermissionWarningMessage,
});

const {
  beginActionViewLoad,
  handleActionViewLoadCatch,
} = useActionViewLoadLifecycleRuntime();

const {
  buildLoadBeginInput,
} = useActionViewLoadBeginInputRuntime({
  staticInput: () => ({
    applyActionViewLoadResetState,
    resetInput: {
      showMoreContractActions,
      showMoreSavedFilters,
      showMoreGroupBy,
      status,
      traceId,
      lastIntent,
      lastWriteMode,
      lastLatencyMs,
      contractViewType,
      actionContract,
      resolvedModelRef,
      contractLimit,
      records,
      groupedRows,
      groupSummaryItems,
      groupWindowCount,
      groupWindowTotal,
      groupWindowStart,
      groupWindowEnd,
      groupWindowId,
      groupQueryFingerprint,
      groupWindowDigest,
      groupWindowIdentityKey,
      groupWindowPrevOffset,
      groupWindowNextOffset,
      columns,
      kanbanFields,
      kanbanPrimaryFields,
      kanbanSecondaryFields,
      kanbanStatusFields,
      kanbanTitleFieldHint,
      advancedFields,
    },
    clearError,
    actionId,
    resolveLoadMissingActionIdErrorState,
    resolveLoadMissingActionApplyState,
    currentErrorMessage: () => error.value?.message || '',
    setError,
    deriveListStatus,
    status,
  }),
});

const {
  executeLoadBeginPhase,
} = useActionViewLoadBeginPhaseRuntime({
  beginActionViewLoad: beginActionViewLoad as (input: Record<string, unknown>) => { startedAt: number; shouldReturn: boolean },
  buildLoadBeginInput,
});

const {
  executeLoadDataRequest,
} = useActionViewLoadRequestRuntime();

const {
  applyLoadSuccess,
} = useActionViewLoadSuccessRuntime();

const {
  executeLoadSuccessPhase,
} = useActionViewLoadSuccessPhaseRuntime({
  applyLoadSuccess: applyLoadSuccess as (input: Record<string, unknown>) => Promise<void>,
  staticInput: {
    resolveEffectiveFilterDomainRaw,
    pageText,
    fetchScopedTotal,
    fetchProjectScopeMetrics,
    restartLoadWithRouteSync,
    syncRouteListState,
    normalizeGroupedRouteState,
    hydrateGroupedRowsByOffset,
    deriveListStatus,
    readTotalFromListResult,
    buildGroupKey,
    normalizeGroupPageOffset,
    resolveActionViewGroupPagingState,
    resolveGroupPagingIdentityApplyState,
    resolveActionViewRouteSnapshot,
    resolveLoadGroupRouteSyncPlan,
    resolveLoadRouteResetApplyState,
    resolveLoadGroupRouteSyncPatch,
    resolveLoadRouteSyncApplyState,
    resolveLoadListTotalApplyState,
    resolveLoadSuccessProjectScopeApplyState,
    resolveProjectScopeApplyState,
    resolveLoadSuccessRecordsState,
    resolveLoadGroupSummaryApplyState,
    resolveLoadSuccessGroupSummaryState,
    resolveLoadSuccessWindowApplyState,
    resolveWindowMetricsApplyState,
    resolveLoadGroupedRowsApplyState,
    resolveLoadSuccessGroupedRowsState,
    resolveLoadFinalizeApplyState,
    resolveLoadFinalizeSummaryKeyState,
    resolveLoadFinalizeSelectedIdsState,
    resolveLoadFinalizeColumnsState,
    resolveLoadFinalizeStatusState,
    resolveLoadTraceApplyState,
    resolveLoadFinalizeTraceTimingState,
    groupWindowOffsetRef: groupWindowOffset,
    groupWindowIdRef: groupWindowId,
    groupQueryFingerprintRef: groupQueryFingerprint,
    groupWindowDigestRef: groupWindowDigest,
    groupWindowIdentityKeyRef: groupWindowIdentityKey,
    groupPageOffsetsRef: groupPageOffsets,
    collapsedGroupKeysRef: collapsedGroupKeys,
    listTotalCountRef: listTotalCount,
    projectScopeTotalsRef: projectScopeTotals,
    projectScopeMetricsRef: projectScopeMetrics,
    recordsRef: records,
    groupSummaryItemsRef: groupSummaryItems,
    groupWindowCountRef: groupWindowCount,
    groupWindowStartRef: groupWindowStart,
    groupWindowEndRef: groupWindowEnd,
    groupWindowTotalRef: groupWindowTotal,
    groupWindowNextOffsetRef: groupWindowNextOffset,
    groupWindowPrevOffsetRef: groupWindowPrevOffset,
    groupedRowsRef: groupedRows,
    activeGroupSummaryKeyRef: activeGroupSummaryKey,
    selectedIdsRef: selectedIds,
    columnsRef: columns,
    statusRef: status,
    traceIdRef: traceId,
    lastTraceIdRef: lastTraceId,
    lastLatencyMsRef: lastLatencyMs,
  },
});

const {
  executeLoadCatchPhase,
} = useActionViewLoadCatchPhaseRuntime({
  handleActionViewLoadCatch,
  staticInput: {
    setError,
    errorMessage: () => error.value?.message || '',
    errorTraceId: () => error.value?.traceId || '',
    resolveLoadCatchState,
    resolveLoadCatchListTotalState,
    resolveLoadCatchProjectScopeState,
    resolveLoadCatchTraceApplyState,
    resolveLoadCatchStatusApplyInput,
    resolveLoadCatchLatencyState,
    deriveListStatus,
    listTotalCount,
    projectScopeTotals,
    projectScopeMetrics,
    traceId,
    lastTraceId,
    status,
    lastLatencyMs,
  },
});

const {
  executeLoadPreflight,
} = useActionViewLoadPreflightRuntime();

const {
  applyLoadPreflightContinueState,
  applyLoadPreflightBlockedState,
} = useActionViewLoadPreflightApplyRuntime();

const {
  buildLoadPreflightInput,
} = useActionViewLoadPreflightInputRuntime({
  staticInput: () => ({
    sessionMenuTree: session.menuTree,
    routeViewModeRaw: route.query.view_mode,
    routeFilterRaw: route.query.preset_filter,
    routeSavedFilterRaw: route.query.saved_filter,
    routeGroupByRaw: route.query.group_by,
    sceneReadyDefaultSortRaw: sceneReadyListSurface.value.defaultSort,
    sceneDefaultSortRaw: scene.value?.default_sort,
    sessionCapabilities: session.capabilities,
    currentSortRaw: sortValue.value,
    activeContractFilterKey: activeContractFilterKey.value,
    activeSavedFilterKey: activeSavedFilterKey.value,
    activeGroupByField: activeGroupByField.value,
    contractSavedFilterChips: contractSavedFilterChips.value,
    contractGroupByChips: contractGroupByChips.value,
    currentPreferredViewModeRaw: preferredViewMode.value,
    buildWorkbenchRouteTarget,
    resolveWorkbenchQuery,
    buildModelFormRouteTarget,
    resolveCarryQuery,
    extractActionResId,
    resolveAction,
    setActionMeta: (meta: Record<string, unknown>) => {
      session.setActionMeta(meta);
    },
    resolveContractViewMode,
    resolveActionViewType,
    resolvePreferredActionViewMode,
    resolveRouteSelectionState,
    resolveRouteSelectionApplyState,
    resolveContractAccessPolicy,
    resolveContractReadRight,
    resolveLoadPreflightContractFlags,
    resolveContractFlagApplyState,
    resolveLoadContractReadRedirectPayload,
    resolveCapabilityMissingRedirectTarget,
    isUrlAction,
    redirectUrlAction,
    resolveDefaultSort,
    resolveLoadPreflightSortValue,
    resolveLoadPreflightContractLimit,
    evaluateCapabilityPolicy,
    resolveLoadCapabilityRedirectPayload,
    resolveModelFromContract,
    resolveActionViewResolvedModel,
    isClientAction,
    isWindowAction,
    getActionType,
    resolveLoadMissingModelRedirectDecision,
    resolveMissingModelRedirectTarget,
    resolveLoadFormActionResId,
    resolveLoadMissingContractViewTypeErrorState,
    resolveLoadMissingViewTypeApplyState,
    resolveLoadMissingResolvedModelErrorState,
    resolveLoadMissingResolvedModelApplyState,
    capabilityMissingCode: ErrorCodes.CAPABILITY_MISSING,
  }),
});

const {
  applyLoadPreflightContinue,
  applyLoadPreflightBlocked,
} = useActionViewLoadPreflightApplyBoundRuntime({
  applyLoadPreflightContinueState,
  applyLoadPreflightBlockedState,
  contractViewTypeRef: contractViewType,
  actionContractRef: actionContract,
  preferredViewModeRef: preferredViewMode,
  activeContractFilterKeyRef: activeContractFilterKey,
  activeSavedFilterKeyRef: activeSavedFilterKey,
  activeGroupByFieldRef: activeGroupByField,
  contractReadAllowedRef: contractReadAllowed,
  contractWarningCountRef: contractWarningCount,
  contractDegradedRef: contractDegraded,
  contractLimitRef: contractLimit,
  sortValueRef: sortValue,
  resolvedModelRef,
  setActionMeta: (payload) => {
    session.setActionMeta(payload);
  },
  setError,
  deriveListStatus,
  statusRef: status,
});

const {
  executeLoadPreflightPhase,
} = useActionViewLoadPreflightPhaseRuntime({
  executeLoadPreflight: executeLoadPreflight as (input: Record<string, unknown>) => Promise<Record<string, unknown>>,
  buildLoadPreflightInput,
  applyLoadPreflightBlocked,
  applyLoadPreflightContinue,
  handleRedirect: async (target) => {
    await router.replace(target as never);
  },
});

const {
  applyLoadRequestBlockedState,
} = useActionViewLoadRequestGuardRuntime();

const {
  applyLoadRequestBlocked,
} = useActionViewLoadRequestBlockedApplyRuntime({
  applyLoadRequestBlockedState,
  setError,
  deriveListStatus,
  statusRef: status,
});

const {
  buildLoadRequestDynamicInput,
} = useActionViewLoadRequestDynamicInputRuntime();

const {
  executeLoadRequestPhase,
} = useActionViewLoadRequestPhaseRuntime();

const {
  executeLoadMainPhase,
} = useActionViewLoadMainPhaseRuntime();

const {
  buildLoadMainPhaseInput,
} = useActionViewLoadMainPhaseInputRuntime({
  staticInput: () => ({
    actionId: actionId.value,
    actionMeta: actionMeta.value as Record<string, unknown> | null,
    routeQueryMap: routeQueryMap.value,
    viewMode: viewMode.value,
    searchTerm: searchTerm.value,
    sortLabel: sortLabel.value,
    activeGroupByField: activeGroupByField.value,
    listOffset: listOffset.value,
    groupWindowOffset: groupWindowOffset.value,
    groupSampleLimit: groupSampleLimit.value,
    contractLimit: contractLimit.value,
    groupPageOffsets: groupPageOffsets.value,
    sceneFiltersRaw: scene.value?.filters,
    executeLoadPreflightPhase,
    executeLoadRequestPhase,
    executeLoadDataRequest,
    buildLoadRequestInput,
    buildLoadRequestDynamicInput,
    applyLoadRequestBlocked,
    executeLoadSuccessPhase,
    executeLoadCatchPhase,
    buildLoadSuccessDynamicInput,
    buildLoadSuccessPhaseInput,
  }),
});

const {
  buildLoadRequestInput,
} = useActionViewLoadRequestInputRuntime({
  staticInput: () => ({
    sceneReadyColumns: sceneReadyListSurface.value.columns,
    listProfile: listProfile.value,
    actionId: actionId.value,
    resolveEffectiveFilterDomainRaw,
    resolveEffectiveFilterDomain,
    resolveEffectiveRequestContext,
    resolveEffectiveRequestContextRaw,
    mergeSceneDomain,
    mergeActiveFilterDomain,
    mergeContext,
    extractColumnsFromContract,
    convergeColumnsForSurface,
    extractKanbanFields,
    extractKanbanProfile,
    extractAdvancedViewFields,
    resolveRequestedFields,
    uniqueFields,
    resolveLoadKanbanFieldApplyState,
    resolveLoadPreflightFieldFlags,
    loadAssigneeOptions,
    resolveLoadRequestedFieldsApplyState,
    resolveLoadMissingTreeColumnsErrorState,
    resolveLoadMissingColumnsApplyState,
    resolveLoadDomainStateApply,
    resolveLoadContextStateApply,
    resolveLoadRequestPayloadState,
    listRecordsRaw,
    currentErrorMessage: () => error.value?.message || '',
    warn: (message: string, payload: Record<string, unknown>) => {
      console.warn(message, payload);
    },
    advancedFieldsRef: advancedFields,
    kanbanFieldsRef: kanbanFields,
    kanbanTitleFieldHintRef: kanbanTitleFieldHint,
    kanbanPrimaryFieldsRef: kanbanPrimaryFields,
    kanbanSecondaryFieldsRef: kanbanSecondaryFields,
    kanbanStatusFieldsRef: kanbanStatusFields,
    kanbanMetricFieldsRef: kanbanMetricFields,
    kanbanQuickActionCountRef: kanbanQuickActionCount,
    hasActiveFieldRef: hasActiveField,
    hasAssigneeFieldRef: hasAssigneeField,
  }),
});

const {
  buildLoadSuccessDynamicInput,
} = useActionViewLoadSuccessDynamicInputRuntime({
  staticInput: () => ({
    routeQueryMap: routeQueryMap.value,
    routeGroupValueRaw: route.query.group_value,
    activeGroupByField: activeGroupByField.value,
    groupSampleLimit: groupSampleLimit.value,
    searchTerm: searchTerm.value,
    sortLabel: sortLabel.value,
    pageMode: pageMode.value,
    hasActiveField: hasActiveField.value,
  }),
});

const {
  buildLoadSuccessPhaseInput,
} = useActionViewLoadSuccessPhaseInputRuntime();

const {
  executeLoadMainBound,
} = useActionViewLoadMainBoundRuntime({
  buildLoadMainPhaseInput: (input) => buildLoadMainPhaseInput(input),
  executeLoadMainPhase: (input) => executeLoadMainPhase(input as Parameters<typeof executeLoadMainPhase>[0]),
});

const {
  executeLoad,
} = useActionViewLoadBoundRuntime({
  executeLoadBeginPhase,
  executeLoadMainBound,
});

const {
  loadPage,
} = useActionViewLoadFacadeRuntime({
  executeLoad,
});
bindLoad(loadPage);

const {
  handleSearch,
  handleSort,
  handleFilter,
} = useActionViewTriggerRuntime({
  searchTerm,
  sortValue,
  filterValue,
  listOffset,
  groupWindowOffset,
  syncRouteListState,
  load: requestLoad,
  clearSelection,
});

const {
  clearSelection: selectionRuntimeClearSelection,
  handleAssigneeChange,
  handleToggleSelection,
  handleToggleSelectionAll,
  buildIfMatchMap,
  buildIdempotencyKey,
} = useActionViewSelectionRuntime({
  selectedIds,
  selectedAssigneeId,
  records,
  resolveTargetModel: () => resolvedModelRef.value || model.value || '',
});
clearSelectionInvoker = selectionRuntimeClearSelection;

const {
  reportBatchError,
  buildBatchRequestContext,
  applyBatchSuccessReload,
  downloadCsv,
} = useActionViewBatchEffectsRuntime({
  setError,
  load: requestLoad,
  clearSelection,
  resolveRequestContext: resolveEffectiveRequestContext,
  mergeContext,
  actionMetaContext: () => actionMeta.value?.context,
  downloadCsvBase64: downloadCsvBase64Runtime,
});

const {
  handleBatchAction,
  handleBatchAssign,
  handleBatchExport,
  handleDownloadFailedCsv,
  handleLoadMoreFailures,
} = useActionViewBatchRuntime({
  selectedIds,
  selectedAssigneeId,
  batchBusy,
  batchMessage,
  batchDetails,
  failedCsvFileName,
  failedCsvContentB64,
  batchFailedOffset,
  batchFailedLimit,
  batchHasMoreFailures,
  lastBatchRequest,
  pageText,
  reportBatchError,
  buildBatchRequestContext,
  applyBatchSuccessReload,
  downloadCsv,
  resolveTargetModel: () => resolveBatchAssignTargetModel({
    resolvedModelRaw: resolvedModelRef.value,
    routeModelRaw: model.value,
  }),
  buildIfMatchMap,
  buildIdempotencyKey,
  batchUpdateRecords,
  unlinkRecords: (payload) => unlinkRecord({
    model: String(payload.model || ''),
    ids: Array.isArray(payload.ids) ? payload.ids : [],
    context: payload.context ?? {},
    idempotencyKey: String(payload.idempotencyKey || ''),
  }),
  exportRecordsCsv,
  buildBatchUpdateRequest,
  buildBatchErrorLine,
  applyBatchFailureArtifacts,
  resolveBatchOperationResetState,
  resolveBatchActionTargetModel,
  resolveBatchActionDeleteMode,
  resolveBatchActionGuardDecision,
  resolveBatchActionGuardMessage,
  resolveBatchDeleteExecutionSeed,
  resolveBatchActionResultMessage,
  resolveBatchStandardExecutionSeed,
  resolveBatchActionLastRequestState,
  resolveBatchActionSuccessMessage: resolveBatchActionResultMessage,
  resolveBatchFailureCatchState,
  resolveBatchActionFailureFallback: (input) => resolveBatchActionErrorFallback({
    targetModel: String(input.targetModel || ''),
    action: (input.action as 'archive' | 'activate' | 'delete') || 'archive',
    resolveActionLabel: (action) => resolveBatchActionErrorLabel({ action, text: pageText }),
  }),
  resolveBatchAssignGuardDecision,
  resolveBatchAssignGuardMessage,
  resolveBatchAssignSeedState: (input) => ({
    ...resolveBatchAssignExecutionSeed({
      selectedIds: input.selectedIds,
      assigneeId: input.selectedAssigneeId,
      buildIfMatchMap: input.buildIfMatchMap,
      buildIdempotencyKey: input.buildIdempotencyKey,
    }),
    assigneeId: input.selectedAssigneeId,
  }),
  resolveBatchAssignResultMessage: (input) => resolveBatchActionFailureMessage({
    action: 'assign',
    assigneeName: resolveBatchAssignAssigneeLabel({
      assigneeId: Number(selectedAssigneeId.value || 0),
      assigneeOptions: assigneeOptions.value,
    }),
    idempotentReplay: Boolean(input.idempotentReplay),
    succeeded: Number(input.succeeded || 0),
    failed: Number(input.failed || 0),
    text: pageText,
  }),
  resolveBatchAssignSuccessMessage: (input) => resolveBatchActionFailureMessage({
    action: 'assign',
    assigneeName: resolveBatchAssignAssigneeLabel({
      assigneeId: Number(selectedAssigneeId.value || 0),
      assigneeOptions: assigneeOptions.value,
    }),
    idempotentReplay: Boolean(input.idempotentReplay),
    succeeded: Number(input.succeeded || 0),
    failed: Number(input.failed || 0),
    text: pageText,
  }),
  resolveBatchAssignFailureMessage,
  resolveBatchAssignErrorFallback,
  resolveBatchErrorHintResolver,
  resolveSuggestedAction: resolveActionViewSuggestedHint,
  resolveBatchExportResetState,
  resolveBatchExportTargetModel,
  resolveBatchExportGuardDecision,
  resolveExportGuardMessage,
  resolveBatchExportDomainState,
  actionMetaDomain: () => actionMeta.value?.domain,
  sceneFilters: () => scene.value?.filters,
  resolveEffectiveFilterDomain,
  mergeSceneDomain,
  mergeActiveFilterDomain,
  columns: () => columns.value,
  sortLabel: () => sortLabel.value,
  resolveBatchExportRequestPayload,
  resolveBatchExportNoContent,
  resolveExportNoContentMessage,
  resolveExportDoneMessage,
  resolveExportFailedMessage,
  resolveBatchExportCatchState,
  resolveBatchExportErrorFallback,
  resolveLoadMoreFailuresGuardPlan,
  resolveLoadMoreFailuresRequestPayload,
  resolveLoadMoreFailuresApplyPlan,
  resolveLoadMoreFailuresCatchState,
  resolveLoadMoreFailuresErrorFallback,
  hasActiveField: () => hasActiveField.value,
  contractDeleteMode: () => actionContract.value?.surface_policies?.delete_mode,
  resolvedModelRaw: () => resolvedModelRef.value,
  routeModelRaw: () => model.value,
});

onMounted(async () => {
  applyRoutePreset();
  await requestLoad();
});

watch(
  () => route.fullPath,
  () => {
    if (applyRoutePreset()) {
      void requestLoad();
    }
  },
);

watch(
  shouldRefreshListOptimizationComposition,
  (shouldRefresh) => {
    if (shouldRefresh) {
      void refreshListOptimizationCompositionOnce();
    }
  },
  { immediate: true },
);
</script>

<style scoped>
.page {
  display: grid;
  gap: 16px;
}

.page-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.view-switch {
  display: grid;
  gap: 8px;
}

.route-preset {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid #bfdbfe;
  border-radius: 10px;
  background: #eff6ff;
}

.route-preset p {
  margin: 0;
  color: #1e3a8a;
  font-size: 13px;
}

.clear-btn {
  border: 1px solid #93c5fd;
  border-radius: 8px;
  background: #fff;
  color: #1d4ed8;
  padding: 4px 8px;
  cursor: pointer;
}

.contract-block {
  display: grid;
  gap: 8px;
}

.focus-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid #dbeafe;
  border-radius: 10px;
  background: #f8fbff;
  padding: 10px 12px;
}

.focus-intent {
  margin: 0;
  color: #0f172a;
  font-size: 14px;
  font-weight: 700;
}

.focus-summary {
  margin: 4px 0 0;
  color: #475569;
  font-size: 12px;
}

.focus-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.contract-missing-alert {
  border: 1px solid #f8d7da;
  border-radius: 10px;
  background: #fff5f5;
  padding: 10px 12px;
}

.contract-missing-title {
  margin: 0;
  color: #b42318;
  font-size: 13px;
  font-weight: 700;
}

.contract-missing-summary,
.contract-missing-defaults {
  margin: 4px 0 0;
  color: #7a271a;
  font-size: 12px;
}

.contract-native-fallback {
  display: grid;
  gap: 12px;
}

.empty-next {
  border: 1px dashed #cbd5e1;
  border-radius: 10px;
  background: #f8fafc;
  padding: 12px;
  display: grid;
  gap: 8px;
}

.empty-next p {
  margin: 0;
  color: #334155;
  font-size: 13px;
}

.empty-next-title {
  color: #0f172a !important;
  font-weight: 700;
}

.empty-next-hint {
  color: #334155 !important;
}

.empty-next-reason {
  color: #64748b !important;
  font-size: 12px !important;
}

.contract-label {
  margin: 0;
  font-size: 13px;
  color: #334155;
}

.contract-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.contract-groups {
  display: grid;
  gap: 8px;
}

.contract-group {
  display: grid;
  gap: 6px;
}

.contract-group-label {
  margin: 0;
  font-size: 12px;
  color: #64748b;
}

.contract-chip {
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  background: #fff;
  color: #0f172a;
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
}

.contract-chip.active {
  border-color: #2563eb;
  color: #1d4ed8;
  background: #eff6ff;
}

.contract-chip.primary {
  border-color: #2563eb;
  background: #2563eb;
  color: #fff;
}

.contract-chip.ghost {
  border-style: dashed;
}

.advanced-view {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
  padding: 12px;
  display: grid;
  gap: 10px;
}

.advanced-view-head h3 {
  margin: 0;
  font-size: 15px;
  color: #0f172a;
}

.advanced-view-head p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #64748b;
}

.advanced-contract {
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  padding: 8px 10px;
  background: #f8fafc;
  display: grid;
  gap: 4px;
}

.advanced-contract p {
  margin: 0;
  font-size: 12px;
  color: #334155;
}

.advanced-list {
  display: grid;
  gap: 8px;
}

.advanced-item {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 8px 10px;
  display: grid;
  gap: 4px;
}

.advanced-item-title {
  margin: 0;
  font-size: 13px;
  color: #0f172a;
  font-weight: 600;
}

.advanced-item-meta {
  margin: 0;
  font-size: 12px;
  color: #64748b;
}

.ledger-overview-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
}

.ledger-overview-card {
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  padding: 10px;
  background: #fff;
}

.ledger-overview-label {
  margin: 0;
  font-size: 12px;
  color: #64748b;
}

.ledger-overview-value {
  margin: 6px 0 0;
  font-size: 20px;
  font-weight: 700;
}

.ledger-overview-card.tone-danger { background: #fef2f2; border-color: #fecaca; color: #b91c1c; }
.ledger-overview-card.tone-success { background: #ecfdf5; border-color: #a7f3d0; color: #047857; }
.ledger-overview-card.tone-info { background: #eff6ff; border-color: #bfdbfe; color: #1d4ed8; }
.ledger-overview-card.tone-neutral { background: #f9fafb; border-color: #d1d5db; color: #374151; }

@media (max-width: 760px) {
  .focus-strip {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>

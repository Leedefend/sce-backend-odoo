<template>
  <section class="page">
    <!-- Page intent: 在列表场景中先判断状态，再给出下一步可执行动作。 -->
    <StatusPanel
      v-if="renderErrorMessage"
      title="页面渲染失败"
      :message="renderErrorMessage"
      variant="error"
      :on-retry="reload"
    />
    <section v-else-if="vm.header.actions.length" class="page-actions">
      <button v-for="action in vm.header.actions" :key="`header-${action.key}`" class="contract-chip ghost" @click="executeHeaderAction(action.key)">
        {{ action.label || action.key }}
      </button>
    </section>
    <section v-if="isSectionVisible('route_preset', { defaultEnabled: pageSectionEnabled('route_preset', false), tag: 'section', vmVisible: Boolean(vm.filters.routePreset) })" class="route-preset" :style="getSectionStyle('route_preset')">
      <p>
        {{ t('route_preset_applied_prefix', '已应用推荐筛选：') }}{{ vm.filters.routePreset?.label }}
        <span v-if="vm.filters.routePreset?.source">（{{ t('route_preset_source_prefix', '来源：') }}{{ vm.filters.routePreset?.source }}）</span>
      </p>
      <button class="clear-btn" @click="clearRoutePreset">{{ t('route_preset_clear', '清除推荐') }}</button>
    </section>
    <section v-if="isSectionVisible('focus_strip', { defaultEnabled: pageSectionEnabled('focus_strip', false), tag: 'section', vmVisible: vm.sections.focus })" class="focus-strip" :style="getSectionStyle('focus_strip')">
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
    <section v-if="vm.sections.strictAlert && vm.strictAlert" class="contract-missing-alert">
      <p class="contract-missing-title">{{ vm.strictAlert.title }}</p>
      <p class="contract-missing-summary">{{ vm.strictAlert.summary }}</p>
      <p v-if="vm.strictAlert.defaultsSummary" class="contract-missing-defaults">{{ vm.strictAlert.defaultsSummary }}</p>
    </section>
    <section v-if="showStandaloneQuickFilters" class="contract-block" :style="getSectionStyle('quick_filters')">
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
    <section v-if="showStandaloneSavedFilters" class="contract-block" :style="getSectionStyle('saved_filters')">
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
    <section v-if="showStandaloneGroupView" class="contract-block" :style="getSectionStyle('group_view')">
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
      v-if="isSectionVisible('group_summary', { defaultEnabled: pageSectionEnabled('group_summary', false), tag: 'section', vmVisible: vm.sections.groupSummary && Boolean(vm.groupSummary?.visible) })"
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
    <section v-if="isSectionVisible('quick_actions', { defaultEnabled: pageSectionEnabled('quick_actions', false), tag: 'section', vmVisible: vm.sections.quickActions && Boolean(vm.actions.primary.length || vm.actions.overflowGroups.length) })" class="contract-block" :style="getSectionStyle('quick_actions')">
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
      :error="pageError"
      :records="records"
      :fields="kanbanFields"
      :primary-fields="kanbanPrimaryFields"
      :secondary-fields="kanbanSecondaryFields"
      :status-fields="kanbanStatusFields"
      :field-labels="contractColumnLabels"
      :title-field="kanbanTitleField"
      :subtitle="vm.page.subtitle"
      :status-label="vm.page.statusLabel"
      :scene-key="vm.page.sceneKey"
      :page-mode="vm.page.pageMode"
      :list-total-count="listTotalCount"
      :list-offset="listOffset"
      :list-limit="contractLimit"
      :on-reload="reload"
      :on-card-click="handleRowClick"
      :on-page-change="handleListPageChange"
    >
      <template v-if="showTopActionToolbar" #toolbar>
        <ActionSurfaceToolbar
          :loading="isUiBusy"
          :show-view-switch="showViewSwitch"
          :view-label="t('label.view_switch', '视图')"
          :view-modes="vm.page.availableViewModes"
          :current-view-mode="vm.page.viewMode"
          :view-mode-labels="toolbarViewModeLabels"
          :search-value="toolbarSearchDraft"
          :search-placeholder="t('placeholder.search_keyword', '搜索关键字')"
          :clear-label="t('chip_action_clear', '清除')"
          :show-filter="showToolbarFilter"
          :filter-label="t('label.quick_filters', '筛选')"
          :filter-primary="vm.filters.quickFilters.primary"
          :filter-overflow="vm.filters.quickFilters.overflow"
          :active-filter-key="activeContractFilterKey"
          :show-saved-filter="showToolbarSavedFilter"
          saved-filter-label="收藏夹"
          :saved-filter-primary="vm.filters.savedFilters.primary"
          :saved-filter-overflow="vm.filters.savedFilters.overflow"
          :active-saved-filter-key="activeSavedFilterKey"
          :sort-label="t('label.sort', '排序')"
          :sort-options="displaySortOptions"
          :sort-value="sortValue"
          :show-group="showToolbarGroup"
          group-label="分组方式"
          :group-primary="vm.filters.groupBy.primary"
          :group-overflow="vm.filters.groupBy.overflow"
          :custom-filter-enabled="customSearchCapabilities.filterEnabled"
          :custom-filter-label="customSearchCapabilities.filterLabel"
          :custom-filter-fields="customFilterFields"
          :custom-group-enabled="customSearchCapabilities.groupEnabled"
          :custom-group-label="customSearchCapabilities.groupLabel"
          :custom-group-fields="customGroupByChips"
          :favorite-save-enabled="customSearchCapabilities.favoriteSaveEnabled"
          :favorite-save-label="customSearchCapabilities.favoriteLabel"
          :active-custom-filter-label="activeCustomFilterLabel"
          :active-group-key="toolbarActiveGroupKey"
          :can-create-record="canCreateRecord"
          :create-label="t('action_create_record', '新建')"
          @switch-view="switchViewMode"
          @search-composition-start="onToolbarSearchCompositionStart"
          @search-composition-end="onToolbarSearchCompositionEnd"
          @search-input="onToolbarSearchInput"
          @search-submit="submitToolbarSearch"
          @clear-search="clearToolbarSearch"
          @filter="applyContractFilter"
          @clear-filter="clearContractFilter"
          @saved-filter="applySavedFilter"
          @clear-saved-filter="clearSavedFilter"
          @sort="handleSort"
          @group="applyGroupBy"
          @clear-group="clearGroupBy"
          @custom-filter="applyCustomFilter"
          @clear-custom-filter="clearCustomFilter"
          @save-favorite="handleSaveFavorite"
          @create="openCreateRecord"
        />
      </template>
    </KanbanPage>
    <ListPage
      v-else-if="vm.content.kind === 'list'"
      :title="vm.page.title"
      :model="model"
      :status="vm.page.status"
      :loading="isUiBusy"
      :error-message="vm.page.errorMessage"
      :trace-id="vm.page.traceId"
      :error="pageError"
      :columns="columns"
      :records="records"
      :list-total-count="listTotalCount"
      :list-offset="listOffset"
      :list-limit="contractLimit"
      :column-labels="contractColumnLabels"
      :sort-label="sortLabel"
      :sort-options="displaySortOptions"
      :sort-value="sortValue"
      :filter-value="filterValue"
      :status-label="vm.page.statusLabel"
      :search-term="searchTerm"
      :subtitle="vm.page.subtitle"
      :scene-key="vm.page.sceneKey"
      :enable-summary-strip="pageSectionEnabled('summary_strip', false)"
      :enable-grouped-rows="pageSectionEnabled('grouped_table', false)"
      :summary-items="vm.content.list?.summaryItems || []"
      :selected-ids="selectedIds"
      :selection-actions="selectionActions"
      :batch-message="batchMessage"
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
      :on-toggle-selection="handleToggleSelection"
      :on-toggle-selection-all="handleToggleSelectionAll"
      :on-run-selection-action="handleSelectionAction"
      :on-clear-selection="clearSelection"
      :on-row-click="handleRowClick"
      :on-page-change="handleListPageChange"
    >
      <template v-if="showTopActionToolbar" #toolbar>
        <ActionSurfaceToolbar
          :loading="isUiBusy"
          :show-view-switch="showViewSwitch"
          :view-label="t('label.view_switch', '视图')"
          :view-modes="vm.page.availableViewModes"
          :current-view-mode="vm.page.viewMode"
          :view-mode-labels="toolbarViewModeLabels"
          :search-value="toolbarSearchDraft"
          :search-placeholder="t('placeholder.search_keyword', '搜索关键字')"
          :clear-label="t('chip_action_clear', '清除')"
          :show-filter="showToolbarFilter"
          :filter-label="t('label.quick_filters', '筛选')"
          :filter-primary="vm.filters.quickFilters.primary"
          :filter-overflow="vm.filters.quickFilters.overflow"
          :active-filter-key="activeContractFilterKey"
          :show-saved-filter="showToolbarSavedFilter"
          saved-filter-label="收藏夹"
          :saved-filter-primary="vm.filters.savedFilters.primary"
          :saved-filter-overflow="vm.filters.savedFilters.overflow"
          :active-saved-filter-key="activeSavedFilterKey"
          :sort-label="t('label.sort', '排序')"
          :sort-options="displaySortOptions"
          :sort-value="sortValue"
          :show-group="showToolbarGroup"
          group-label="分组方式"
          :group-primary="vm.filters.groupBy.primary"
          :group-overflow="vm.filters.groupBy.overflow"
          :custom-filter-enabled="customSearchCapabilities.filterEnabled"
          :custom-filter-label="customSearchCapabilities.filterLabel"
          :custom-filter-fields="customFilterFields"
          :custom-group-enabled="customSearchCapabilities.groupEnabled"
          :custom-group-label="customSearchCapabilities.groupLabel"
          :custom-group-fields="customGroupByChips"
          :favorite-save-enabled="customSearchCapabilities.favoriteSaveEnabled"
          :favorite-save-label="customSearchCapabilities.favoriteLabel"
          :active-custom-filter-label="activeCustomFilterLabel"
          :active-group-key="toolbarActiveGroupKey"
          :can-create-record="canCreateRecord"
          :create-label="t('action_create_record', '新建')"
          @switch-view="switchViewMode"
          @search-composition-start="onToolbarSearchCompositionStart"
          @search-composition-end="onToolbarSearchCompositionEnd"
          @search-input="onToolbarSearchInput"
          @search-submit="submitToolbarSearch"
          @clear-search="clearToolbarSearch"
          @filter="applyContractFilter"
          @clear-filter="clearContractFilter"
          @saved-filter="applySavedFilter"
          @clear-saved-filter="clearSavedFilter"
          @sort="handleSort"
          @group="applyGroupBy"
          @clear-group="clearGroupBy"
          @custom-filter="applyCustomFilter"
          @clear-custom-filter="clearCustomFilter"
          @save-favorite="handleSaveFavorite"
          @create="openCreateRecord"
        />
      </template>
    </ListPage>
    <section v-else-if="isSectionVisible('advanced_view', { defaultEnabled: pageSectionEnabled('advanced_view', true), tag: 'section' })" class="advanced-view" :style="getSectionStyle('advanced_view')">
      <header class="advanced-view-head">
        <h3>{{ vm.content.advanced?.title }}</h3>
        <p>{{ vm.content.advanced?.hint }}</p>
      </header>
      <div class="advanced-contract">
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
      :title="vm.hud?.title || 'View Context'"
      :entries="vm.hud?.entries || []"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, inject, onErrorCaptured, onMounted, ref, watch, type Ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { listRecordsRaw, saveSearchFavorite } from '../api/data';
import { executeButton } from '../api/executeButton';
import { trackUsageEvent } from '../api/usage';
import { resolveAction } from '../app/resolvers/actionResolver';
import { loadActionContract } from '../api/contract';
import { config } from '../config';
import { useSessionStore } from '../stores/session';
import ListPage from '../pages/ListPage.vue';
import KanbanPage from '../pages/KanbanPage.vue';
import StatusPanel from '../components/StatusPanel.vue';
import DevContextPanel from '../components/DevContextPanel.vue';
import GroupSummaryBar from '../components/GroupSummaryBar.vue';
import ActionSurfaceToolbar from '../components/action/ActionSurfaceToolbar.vue';
import { deriveListStatus } from '../app/view_state';
import { isHudEnabled } from '../config/debug';
import { ErrorCodes } from '../app/error_codes';
import { evaluateCapabilityPolicy } from '../app/capabilityPolicy';
import { resolveSuggestedAction, useStatus } from '../composables/useStatus';
import { describeSuggestedAction, runSuggestedAction } from '../composables/useSuggestedAction';
import {
  parseContractContextRaw,
  resolveContractAccessPolicy,
  resolveContractReadRight,
  resolveContractViewMode,
} from '../app/contractActionRuntime';
import { detectObjectMethodFromActionKey, normalizeActionKind, toPositiveInt } from '../app/contractRuntime';
import type { Scene, SceneListProfile } from '../app/resolvers/sceneRegistry';
import { findSceneReadyEntry } from '../app/resolvers/sceneReadyResolver';
import { normalizeSceneActionProtocol, type MutationContract, type ProjectionRefreshPolicy } from '../app/sceneActionProtocol';
import { executeProjectionRefresh } from '../app/projectionRefreshRuntime';
import { executeSceneMutation } from '../app/sceneMutationRuntime';
import { useActionViewActionRuntime } from '../app/action_runtime/useActionViewActionRuntime';
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
import { useActionViewHudEntriesRuntime } from '../app/action_runtime/useActionViewHudEntriesRuntime';
import { useActionViewHudEntriesInputRuntime } from '../app/action_runtime/useActionViewHudEntriesInputRuntime';
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
  resolveExportDoneMessage,
} from '../app/runtime/actionViewAssigneeExportRuntime';
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

let loadPageInvoker: () => Promise<void> = async () => {};
function requestLoadPage(): Promise<void> {
  return loadPageInvoker();
}

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
const renderErrorMessage = ref('');
const traceId = ref('');
const lastTraceId = ref('');
const records = ref<Array<Record<string, unknown>>>([]);
const listTotalCount = ref<number | null>(null);
const listOffset = ref(0);
const projectScopeTotals = ref<{ all: number; active: number; archived: number } | null>(null);
const projectScopeMetrics = ref<{ warning: number; done: number; amount: number } | null>(null);
const searchTerm = ref('');
const toolbarSearchDraft = ref('');
const toolbarSearchComposing = ref(false);
const activeCustomFilter = ref<{ label: string; domain: unknown[] } | null>(null);
const activeCustomFilterDomain = computed(() => activeCustomFilter.value?.domain || []);
const activeCustomFilterLabel = computed(() => activeCustomFilter.value?.label || '');
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
const selectedAssigneeId = ref<number | null>(null);
const selectedIds = ref<number[]>([]);
const batchMessage = ref('');
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
const advancedFields = ref<string[]>([]);
const batchBusy = ref(false);
const {
  isUiBusy,
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
type StatusErrorLike = { code?: unknown; message?: string };
const error = statusApi?.error ?? ref<StatusErrorLike | null>(null);
const pageError = error as unknown as ReturnType<typeof useStatus>['error'];
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
    metric_fields?: string[];
    quick_action_count?: number;
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
  level: string;
  actionId: number | null;
  methodName: string;
  model: string;
  target: string;
  url: string;
  selection: ContractActionSelection;
  visibleProfiles: string[];
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
const sceneContextEnabled = computed(() => keepSceneRoute.value);
const sceneKey = computed(() => {
  if (!sceneContextEnabled.value) return '';
  const metaKey = route.meta?.sceneKey as string | undefined;
  if (metaKey) return metaKey;
  const queryKey = (route.query.scene_key || route.query.scene) as string | undefined;
  return queryKey ? String(queryKey) : '';
});
const scene = computed<Scene | null>(() => {
  if (!sceneKey.value) return null;
  return session.scenes.find((item: Scene) => item.key === sceneKey.value || resolveSceneCode(item) === sceneKey.value) || null;
});
const pageMode = computed(() => resolvePageMode(sceneKey.value, String(scene.value?.layout?.kind || '')));
const hasLedgerOverviewStrip = computed(() => pageMode.value === 'ledger');

const listProfile = computed<SceneListProfile | null>(() => {
  return extractListProfile(actionContract.value);
});
const sceneReadyEntry = computed<Record<string, unknown> | null>(() => {
  if (!sceneContextEnabled.value || !sceneKey.value) return null;
  return findSceneReadyEntry(session.sceneReadyContractV1, sceneKey.value);
});
const {
  strictContractMode,
  strictSurfaceContract,
  strictProjectionContract,
  strictContractMissingSummary,
  strictContractDefaultsSummary,
  strictAdvancedViewContract,
  strictViewModeLabelMap,
} = useActionViewStrictContractBundle({
  sceneKey: computed(() => (sceneContextEnabled.value ? sceneKey.value : '')),
  sceneReadyEntry,
  pageText,
});

const model = computed(() => actionMeta.value?.model ?? '');
const injectedTitle = inject('pageTitle', computed(() => ''));
const contractViewType = ref('');
const contractReadAllowed = ref(true);
const contractWarningCount = ref(0);
const contractDegraded = ref(false);
const actionContract = ref<ActionContractLoose | null>(null);
const resolvedModelRef = ref('');
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

function resolveCreateRight(contract: ActionContractLoose | null): boolean {
  const effective = contract?.permissions?.effective?.rights?.create;
  if (typeof effective === 'boolean') return effective;
  return false;
}

const canCreateRecord = computed(() => {
  const targetModel = (resolvedModelRef.value || model.value || '').trim();
  if (!targetModel || !actionId.value) return false;
  if (status.value === 'loading') return false;
  return resolveCreateRight(actionContract.value);
});
const isKanbanContent = computed(() => vm.value.content.kind === 'kanban');
const canRenderActionSurfaceToolbar = computed(() => isKanbanContent.value || vm.value.content.kind === 'list');
const showViewSwitch = computed(() =>
  isSectionVisible('view_switch', {
    defaultEnabled: true,
    tag: 'section',
    vmVisible: canRenderActionSurfaceToolbar.value && vm.value.page.availableViewModes.length > 0,
  }),
);
const toolbarViewModeLabels = computed(() =>
  vm.value.page.availableViewModes.reduce<Record<string, string>>((acc, mode) => {
    acc[mode] = viewModeLabel(mode);
    return acc;
  }, {}),
);
const showToolbarSearch = computed(() => canRenderActionSurfaceToolbar.value);
const quickFiltersVisible = computed(() =>
  isSectionVisible('quick_filters', {
    defaultEnabled: pageSectionEnabled('quick_filters', true),
    tag: 'section',
    vmVisible: vm.value.sections.quickFilters && vm.value.filters.quickFilters.visible,
  }),
);
const savedFiltersVisible = computed(() =>
  isSectionVisible('saved_filters', {
    defaultEnabled: pageSectionEnabled('saved_filters', true),
    tag: 'section',
    vmVisible: vm.value.sections.savedFilters && vm.value.filters.savedFilters.visible,
  }),
);
const groupViewVisible = computed(() =>
  isSectionVisible('group_view', {
    defaultEnabled: pageSectionEnabled('group_view', true),
    tag: 'section',
    vmVisible: vm.value.sections.groupBy && vm.value.filters.groupBy.visible,
  }),
);
const showToolbarFilter = computed(() => canRenderActionSurfaceToolbar.value && quickFiltersVisible.value);
const showToolbarSavedFilter = computed(() => canRenderActionSurfaceToolbar.value && savedFiltersVisible.value);
const showToolbarGroup = computed(() => canRenderActionSurfaceToolbar.value && groupViewVisible.value);
const showStandaloneQuickFilters = computed(() => quickFiltersVisible.value && !showToolbarFilter.value);
const showStandaloneSavedFilters = computed(() => savedFiltersVisible.value && !showToolbarSavedFilter.value);
const showStandaloneGroupView = computed(() => groupViewVisible.value && !showToolbarGroup.value);
const toolbarActiveGroupKey = computed(() =>
  activeGroupByField.value || String(route.query.group_by || '').trim(),
);
const showTopActionToolbar = computed(() =>
  showViewSwitch.value
  || showToolbarSearch.value
  || showToolbarFilter.value
  || showToolbarSavedFilter.value
  || showToolbarGroup.value
  || canCreateRecord.value,
);

async function openCreateRecord() {
  const targetModel = (resolvedModelRef.value || model.value || '').trim();
  if (!targetModel || !canCreateRecord.value) return;
  await router.push(buildModelFormRouteTarget({
    model: targetModel,
    id: 'new',
    query: resolveCarryQuery(),
  }) as never);
}
const availableViewModes = computed(() =>
  resolveActionViewAvailableModes({
    contractViewTypeRaw: contractViewType.value,
    metaViewModesRaw: (actionMeta.value as { view_modes?: unknown } | null)?.view_modes,
    contract: (actionContract.value as Record<string, unknown> | null),
  }),
);
const viewMode = computed(() => {
  const modes = availableViewModes.value;
  const mode = normalizeActionViewMode(preferredViewMode.value) || modes[0] || '';
  if (mode === 'kanban') return 'kanban';
  if (mode === 'list' || mode === 'tree') return 'tree';
  if (mode === 'pivot' || mode === 'graph' || mode === 'calendar' || mode === 'gantt' || mode === 'activity' || mode === 'dashboard') {
    return mode;
  }
  return '';
});

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
  load: requestLoadPage,
});
const {
  contractColumnLabels,
  extractListProfile,
  extractColumnsFromContract,
  extractListOrderFromContract,
  buildListSortOptions,
  convergeColumnsForSurface,
  extractKanbanFields,
  extractKanbanProfile,
  extractAdvancedViewFields,
  advancedRowTitle,
  advancedRowMeta,
  buildGroupKey,
  resolveModelFromContract,
} = useActionViewContractShapeRuntime({
  pageText,
  actionContract,
  advancedFields,
  activeGroupByField,
});
const {
  sortLabel,
} = useActionViewSurfaceDisplayRuntime({
  sortValue,
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
  actionContract,
  records,
  sortLabel,
  status,
  listTotalCount,
  pageText,
  buildListSortOptions,
});
const displaySortOptions = computed(() => {
  const seen = new Set<string>();
  return sortOptions.value.filter((option) => {
    const label = String(option.label || '').trim();
    const key = label || String(option.value || '').trim();
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
});

const {
  resolveProjectStateCell,
  resolveProjectAmount,
  isCompletedState,
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
  strictContractMode,
  strictSurfaceContract,
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

const { buildHudEntriesInput } = useActionViewHudEntriesInputRuntime({
  staticInput: () => ({
    actionId: actionId.value,
    menuId: menuId.value,
    sceneKey: sceneKey.value,
    model: model.value,
    viewMode: viewMode.value,
    contractViewType: contractViewType.value,
    activeContractFilterKey: activeContractFilterKey.value,
    activeSavedFilterKey: activeSavedFilterKey.value,
    activeGroupByField: activeGroupByField.value,
    listOffset: listOffset.value,
    groupWindowOffset: groupWindowOffset.value,
    groupWindowId: groupWindowId.value,
    groupQueryFingerprint: groupQueryFingerprint.value,
    groupWindowDigest: groupWindowDigest.value,
    groupWindowIdentityKey: groupWindowIdentityKey.value,
    routeGroupFp: String(route.query.group_fp || '').trim(),
    routeGroupWid: String(route.query.group_wid || '').trim(),
    routeGroupWdg: String(route.query.group_wdg || '').trim(),
    routeGroupWik: String(route.query.group_wik || '').trim(),
    contractActionCount: resolveContractActionCountForHud(),
    contractLimit: contractLimit.value,
    contractReadAllowed: contractReadAllowed.value,
    contractWarningCount: contractWarningCount.value,
    contractDegraded: contractDegraded.value,
    sortLabel: sortLabel.value,
    lastIntent: lastIntent.value,
    lastWriteMode: lastWriteMode.value,
    traceId: traceId.value,
    lastTraceId: lastTraceId.value,
    lastLatencyMs: lastLatencyMs.value,
    routeFullPath: route.fullPath,
  }),
});
const { buildHudEntries } = useActionViewHudEntriesRuntime({
  buildHudEntriesInput,
});
const hudEntries = computed(() => buildHudEntries());
const {
  contractFilterChips,
  contractPrimaryFilterChips,
  contractOverflowFilterChips,
  contractSavedFilterChips,
  savedFilterPrimaryChips,
  savedFilterOverflowChips,
  contractGroupByChips,
  customFilterFields,
  customGroupByChips,
  routeGroupByChips,
  customSearchCapabilities,
  groupByPrimaryChips,
  groupByOverflowChips,
  activeGroupByLabel,
} = useActionViewFilterComputedRuntime({
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
  contractActionButtons,
  contractPrimaryActions,
  contractOverflowActionGroups,
} = useActionViewActionPresentationRuntime({
  actionContract,
  strictContractMode,
  toContractActionButton: (row, dedup) => toContractActionButton(row, dedup) as ContractActionButton | null,
  resolveContractActionPresentation,
  pageText,
});

const selectionActions = computed(() =>
  contractActionButtons.value
    .filter((action) => {
      if (action.selection !== 'single' && action.selection !== 'multi') return false;
      const visibleProfiles = Array.isArray(action.visibleProfiles) ? action.visibleProfiles : [];
      if (!visibleProfiles.length) return true;
      return visibleProfiles.includes('readonly') || visibleProfiles.includes('list');
    })
    .map((action) => ({
      key: action.key,
      label: action.label,
      enabled: action.enabled,
      hint: action.hint,
    })),
);

function handleSelectionAction(key: string) {
  const target = contractActionButtons.value.find((action) => action.key === key);
  if (!target) return;
  void runContractAction(target as ContractActionButton);
}

const advancedRows = computed(() => {
  return records.value.slice(0, 20).map((row, idx) => {
    const rowId = String((row as Record<string, unknown>).id || idx).trim() || String(idx);
    return {
      key: `adv-${idx}-${rowId}`,
      title: advancedRowTitle(row),
      meta: advancedRowMeta(row),
    };
  });
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
    availableViewModes,
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
    advancedRows,
  },
  empty: {
    reasonText: emptyReasonText,
  },
  hud: {
    visible: showHud,
    entries: hudEntries,
  },
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
  routerPush: (target) => router.push(target as never),
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
    router.replace(routeState.target as never).catch(() => {});
  },
  trackUsageEvent,
  load: requestLoadPage,
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

function applyCustomFilter(payload: { label: string; domain: unknown[] }) {
  activeCustomFilter.value = {
    label: String(payload.label || '自定义筛选'),
    domain: Array.isArray(payload.domain) ? payload.domain : [],
  };
  clearSelection();
  void requestLoadPage();
}

function clearCustomFilter() {
  activeCustomFilter.value = null;
  clearSelection();
  void requestLoadPage();
}

async function handleSaveFavorite(payload: { name: string }) {
  const targetModel = String(resolvedModelRef.value || model.value || '').trim();
  const name = String(payload.name || '').trim();
  if (!targetModel || !name) return;
  await saveSearchFavorite({
    model: targetModel,
    name,
    domain: resolveEffectiveFilterDomain(),
    context: resolveEffectiveRequestContext(),
    order: sortValue.value,
  });
  await requestLoadPage();
}

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
  activeCustomFilterDomain,
  activeGroupSummaryDomain,
  contractGroupByChips: routeGroupByChips,
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
  actionMetaContext: () => {
    const context = actionMeta.value?.context;
    return context && typeof context === 'object' ? context as Record<string, unknown> : {};
  },
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
  load: requestLoadPage,
  resolveReloadTriggerPlan,
  resolveFocusActionPushState,
  resolveWorkspaceContextQuery,
  routerPush: (target) => router.push(target as never),
  executePageContractAction,
  router,
  pageActionIntent,
  pageActionTarget,
});

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

const { runContractAction } = useActionViewActionRuntime({
  selectedIds,
  batchBusy,
  batchMessage,
  pageText,
  load: requestLoadPage,
  sessionLoadAppInit: () => session.loadAppInit(),
  recordIntentTrace: (payload) => session.recordIntentTrace(payload),
  resolveActionContextRecordId: () => {
    const fromRoute = toPositiveInt(route.query.res_id);
    if (fromRoute) return fromRoute;
    const fromContract = toPositiveInt(actionContract.value?.head?.res_id);
    if (fromContract) return fromContract;
    return null;
  },
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
  resolveMissingOpenTargetMessage: (text) => resolveContractActionMissingOpenTargetMessage(text),
  resolveExecIds: resolveContractActionExecIds,
  resolveRunIds: resolveContractActionRunIds,
  resolveCounters: resolveContractActionCounters,
  resolveDoneMessage: resolveContractActionDoneMessage,
  resolveRequiresRecordContextMessage: resolveContractActionRequiresRecordContextMessage,
  resolveSelectionBlockMessage: resolveContractActionSelectionBlockMessage,
  resolveMissingModelMessage: resolveContractActionMissingModelMessage,
  executeProjectionRefresh: async (payload) => {
    await executeProjectionRefresh(payload as unknown as {
      policy: ProjectionRefreshPolicy;
      refreshScene: () => Promise<void>;
      refreshWorkbench: () => Promise<void>;
      refreshRoleSurface: () => Promise<void>;
      recordTrace: (input: { intent: string; writeMode: string; latencyMs?: number }) => void;
    });
  },
  executeSceneMutation: executeSceneMutation as (options: any) => Promise<unknown>,
  executeButton: executeButton as (payload: any) => Promise<unknown>,
  buildButtonRequest: buildContractActionButtonRequest,
  resolveResponseActionId: resolveContractActionResponseActionId,
  shouldNavigate: shouldNavigateContractAction,
});

const loadAssigneeOptions = async () => {};

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
    errorTraceId: () => (error.value as { traceId?: string } | null)?.traceId || '',
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
    sceneReadyDefaultSortRaw: '',
    sceneDefaultSortRaw: '',
    sessionCapabilities: session.capabilities,
    currentSortRaw: sortValue.value,
    activeContractFilterKey: activeContractFilterKey.value,
    activeSavedFilterKey: activeSavedFilterKey.value,
    activeGroupByField: activeGroupByField.value,
    contractSavedFilterChips: contractSavedFilterChips.value,
    contractGroupByChips: routeGroupByChips.value,
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
    extractListOrderFromContract,
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
  deriveListStatus: deriveListStatus as (input: string) => 'loading' | 'ok' | 'empty' | 'error',
  statusRef: status as unknown as Ref<'loading' | 'ok' | 'empty' | 'error'>,
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
    sceneReadyColumns: [],
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
loadPageInvoker = loadPage;

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
  load: requestLoadPage,
  clearSelection,
});

function onToolbarSearchInput(event: Event): void {
  const value = String((event.target as HTMLInputElement | null)?.value || '');
  toolbarSearchDraft.value = value;
  if (toolbarSearchComposing.value || (event as InputEvent).isComposing) return;
  handleSearch(value);
}

function onToolbarSearchCompositionStart(): void {
  toolbarSearchComposing.value = true;
}

function onToolbarSearchCompositionEnd(event: CompositionEvent): void {
  toolbarSearchComposing.value = false;
  const value = String((event.target as HTMLInputElement | null)?.value || '');
  toolbarSearchDraft.value = value;
  handleSearch(value);
}

function submitToolbarSearch(): void {
  if (toolbarSearchComposing.value) return;
  handleSearch(toolbarSearchDraft.value || '');
}

function clearToolbarSearch(): void {
  toolbarSearchComposing.value = false;
  toolbarSearchDraft.value = '';
  handleSearch('');
}

watch(
  searchTerm,
  (value) => {
    if (toolbarSearchComposing.value) return;
    toolbarSearchDraft.value = value || '';
  },
  { immediate: true },
);

function handleListPageChange(offset: number): void {
  listOffset.value = Math.max(0, Math.trunc(Number(offset || 0)));
  clearSelection();
  void requestLoadPage();
}

const {
  clearSelection: selectionRuntimeClearSelection,
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

onMounted(async () => {
  renderErrorMessage.value = '';
  applyRoutePreset();
  await requestLoadPage();
});

onErrorCaptured((err) => {
  const message = err instanceof Error ? err.message : String(err || 'unknown render error');
  renderErrorMessage.value = `ActionView render error: ${message}`;
  console.error('[ActionView] render failed', err);
  return false;
});

watch(
  () => route.fullPath,
  () => {
    renderErrorMessage.value = '';
    listOffset.value = 0;
    clearSelection();
    applyRoutePreset();
    void requestLoadPage();
  },
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
  white-space: nowrap;
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
  padding: 5px 11px;
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

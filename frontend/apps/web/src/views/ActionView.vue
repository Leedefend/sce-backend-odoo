/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-explicit-any */
<template>
  <section class="page sc-page sc-product-workspace-stack" data-product-page-mode="list">
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
    <SceneBlocksRenderer
      v-if="showSceneBlocksDebug && sceneReadyListSurface.sceneBlocks.length"
      :blocks="sceneReadyListSurface.sceneBlocks"
      @action="handleSceneBlockAction"
    />
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
    <section v-if="batchMessage" class="contract-block batch-feedback">
      <p>{{ batchMessage }}</p>
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
      :field-labels="kanbanFieldLabels"
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
          :view-label="toolbarUiLabel('view_switch', '视图')"
          :view-modes="vm.page.availableViewModes"
          :current-view-mode="vm.page.viewMode"
          :view-mode-labels="toolbarViewModeLabels"
          :search-value="toolbarSearchDraft"
          :search-placeholder="toolbarUiLabel('search_placeholder', '搜索关键字')"
          :clear-label="t('chip_action_clear', '清除')"
          :show-filter="showToolbarFilter"
          :filter-label="toolbarUiLabel('filters', '筛选')"
          :filter-primary="vm.filters.quickFilters.primary"
          :filter-overflow="vm.filters.quickFilters.overflow"
          :active-filter-key="activeContractFilterKey"
          :show-saved-filter="showToolbarSavedFilter"
          :saved-filter-label="toolbarUiLabel('saved_filters', '收藏夹')"
          :saved-filter-primary="vm.filters.savedFilters.primary"
          :saved-filter-overflow="vm.filters.savedFilters.overflow"
          :active-saved-filter-key="activeSavedFilterKey"
          :sort-label="toolbarUiLabel('sort', '排序')"
          :sort-options="displaySortOptions"
          :sort-value="sortValue"
          :show-group="showToolbarGroup"
          :group-label="toolbarUiLabel('group_by', '分组方式')"
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
          :active-group-label="activeGroupByDisplayLabel || activeGroupByLabel"
          :active-group-key="toolbarActiveGroupKey"
          :can-create-record="canCreateRecord"
          :create-label="toolbarUiLabel('create', '新建')"
          :ui-labels="toolbarUiLabels"
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
          @custom-group="applyCustomGroupBy"
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
      :list-aggregates="listAggregates"
      :column-labels="contractColumnLabels"
      :column-options="listColumnOptions"
      :column-visibility="listColumnVisibility"
      :column-order="listColumnOrder"
      :column-widths="listColumnWidths"
      :column-save-status="listColumnSaveStatus"
      :sort-label="sortLabel"
      :sort-options="displaySortOptions"
      :sort-value="sortValue"
      :filter-value="filterValue"
      :status-label="vm.page.statusLabel"
      :search-term="searchTerm"
      :subtitle="vm.page.subtitle"
      :scene-key="vm.page.sceneKey"
      :enable-summary-strip="pageSectionEnabled('summary_strip', false)"
      :enable-grouped-rows="listGroupedRowsEnabled"
      :summary-items="vm.content.list?.summaryItems || []"
      :selected-ids="selectedIds"
      :selection-actions="selectionActions"
      :batch-message="batchMessage"
      :list-profile="listProfile"
      :ui-labels="toolbarUiLabels"
      :show-plain-search="!showTopActionToolbar"
      :grouped-rows="currentPageGroupedRows"
      :group-window-offset="groupWindowOffset"
      :group-window-count="groupWindowCount"
      :group-window-total="groupWindowTotal ?? undefined"
      :group-window-start="groupWindowStart ?? undefined"
      :group-window-end="groupWindowEnd ?? undefined"
      :can-group-window-prev="groupWindowPrevOffset !== null"
      :can-group-window-next="groupWindowNextOffset !== null"
      :on-group-window-prev="handleGroupWindowPrev"
      :on-group-window-next="handleGroupWindowNext"
      :can-create-record="canCreateRecord"
      :create-label="toolbarUiLabel('create', '新建')"
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
      :on-toggle-record-favorite="handleToggleRecordFavorite"
      :on-row-click="handleRowClick"
      :on-page-change="handleListPageChange"
      :on-page-limit-change="handleListPageLimitChange"
      :on-create="openCreateRecord"
      @column-visibility-change="handleListColumnVisibilityChange"
      @column-order-change="handleListColumnOrderChange"
      @column-widths-change="handleListColumnWidthsChange"
    >
      <template v-if="showTopActionToolbar" #toolbar>
        <ActionSurfaceToolbar
          :loading="isUiBusy"
          :show-view-switch="showViewSwitch"
          :view-label="toolbarUiLabel('view_switch', '视图')"
          :view-modes="vm.page.availableViewModes"
          :current-view-mode="vm.page.viewMode"
          :view-mode-labels="toolbarViewModeLabels"
          :search-value="toolbarSearchDraft"
          :search-placeholder="toolbarUiLabel('search_placeholder', '搜索关键字')"
          :clear-label="t('chip_action_clear', '清除')"
          :show-filter="showToolbarFilter"
          :filter-label="toolbarUiLabel('filters', '筛选')"
          :filter-primary="vm.filters.quickFilters.primary"
          :filter-overflow="vm.filters.quickFilters.overflow"
          :active-filter-key="activeContractFilterKey"
          :show-saved-filter="showToolbarSavedFilter"
          :saved-filter-label="toolbarUiLabel('saved_filters', '收藏夹')"
          :saved-filter-primary="vm.filters.savedFilters.primary"
          :saved-filter-overflow="vm.filters.savedFilters.overflow"
          :active-saved-filter-key="activeSavedFilterKey"
          :sort-label="toolbarUiLabel('sort', '排序')"
          :sort-options="displaySortOptions"
          :sort-value="sortValue"
          :show-group="showToolbarGroup"
          :group-label="toolbarUiLabel('group_by', '分组方式')"
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
          :active-group-label="activeGroupByDisplayLabel || activeGroupByLabel"
          :active-group-key="toolbarActiveGroupKey"
          :can-create-record="canCreateRecord"
          :create-label="toolbarUiLabel('create', '新建')"
          :ui-labels="toolbarUiLabels"
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
          @custom-group="applyCustomGroupBy"
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
        <p class="contract-label">{{ t('label.contract_summary', '配置摘要') }}</p>
        <p>{{ t('label.view_type', '视图类型') }}：{{ contractViewType || '-' }} · {{ t('label.view_mode', '页面模式') }}：{{ vm.page.viewMode || '-' }} · {{ t('label.record_count', '记录数') }}：{{ records.length }}</p>
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
    <section v-if="showGlobalEmptyNext" class="empty-next" :style="getSectionStyle('empty_next')">
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
      :title="vm.hud?.title || pageText('dev_context_title', '页面上下文')"
      :entries="vm.hud?.entries || []"
    />
    <div
      v-if="businessCategoryCreatePickerVisible"
      class="business-category-picker-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="business-category-picker-title"
      @click.self="closeBusinessCategoryCreatePicker"
    >
      <section class="business-category-picker">
        <header class="business-category-picker-head">
          <div>
            <h3 id="business-category-picker-title">选择办理类型</h3>
            <p>{{ actionMetaName || vm.page.title || '新建业务' }}</p>
          </div>
          <button class="business-category-picker-close" type="button" aria-label="关闭" @click="closeBusinessCategoryCreatePicker">×</button>
        </header>
        <div class="business-category-picker-list">
          <button
            v-for="option in businessCategoryCreateOptions"
            :key="option.code"
            class="business-category-picker-option"
            type="button"
            @click="openCreateRecordWithBusinessCategory(option.code)"
          >
            <span>{{ option.label }}</span>
          </button>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, inject, onActivated, onBeforeUnmount, onDeactivated, onErrorCaptured, onMounted, ref, watch, type Ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import type { ActionContract } from '@sc/schema';
import { ApiError } from '../api/client';
import { getUserViewPreference, setUserViewPreference } from '../api/preferences';
import { executeButton } from '../api/executeButton';
import { trackUsageEvent } from '../api/usage';
import { resolveAction } from '../app/resolvers/actionResolver';
import { resolveMenuAction } from '../app/resolvers/menuResolver';
import { loadActionContract } from '../api/contract';
import { config } from '../config';
import { intentRequest } from '../api/intents';
import { useSessionStore } from '../stores/session';
import ListPage from '../pages/ListPage.vue';
import KanbanPage from '../pages/KanbanPage.vue';
import StatusPanel from '../components/StatusPanel.vue';
import DevContextPanel from '../components/DevContextPanel.vue';
import GroupSummaryBar from '../components/GroupSummaryBar.vue';
import SceneBlocksRenderer from '../components/scene/SceneBlocksRenderer.vue';
import ActionSurfaceToolbar from '../components/action/ActionSurfaceToolbar.vue';
import { deriveListStatus } from '../app/view_state';
import { isHudEnabled, isSceneBlocksDebugEnabled } from '../config/debug';
import { ErrorCodes } from '../app/error_codes';
import { evaluateCapabilityPolicy } from '../app/capabilityPolicy';
import { useStatus } from '../composables/useStatus';
import {
  parseContractContextRaw,
  resolveContractAccessPolicy,
  resolveContractReadRight,
  resolveContractViewMode,
} from '../app/contractActionRuntime';
import { detectObjectMethodFromActionKey, normalizeActionKind, toPositiveInt } from '../app/contractRuntime';
import { findActionMeta, findMenuNode } from '../app/menu';
import { getSceneByKey, type Scene, type SceneListProfile } from '../app/resolvers/sceneRegistry';
import { findSceneReadyEntry, resolveCollectionSceneReady } from '../app/resolvers/sceneReadyResolver';
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
  batchUpdateActionViewRecords,
  listActionViewRecordsRaw,
  saveActionViewSearchFavorite,
  unlinkActionViewRecord,
  writeActionViewRecord,
} from '../app/runtime/actionViewDataRuntime';
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
  resolveContractActionResponseNavigation,
  resolveContractActionRequiresRecordContextMessage,
  resolveContractActionRunIds,
  resolveContractActionSelectionBlockMessage,
  shouldNavigateContractAction,
} from '../app/runtime/actionViewContractActionRuntime';
import {
  buildBatchUpdateRequest,
  resolveBatchActionFailureMessage,
  resolveBatchActionGuardMessage,
  resolveBatchActionResultMessage,
} from '../app/runtime/actionViewBatchRuntime';
import {
  resolveBatchActionGuardDecision,
  resolveBatchDeleteExecutionSeed,
  resolveBatchStandardExecutionSeed,
} from '../app/runtime/actionViewBatchActionFlowRuntime';
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
import { buildCanonicalSceneRouteTarget, buildEntryTargetRouteTarget } from '../app/routeQuery';
import { buildBusinessEntryNavQuery, buildBusinessEntryRequestContext } from '../app/navigationContext';
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
  collectUnifiedPageContractV2ButtonStatus,
  resolveUnifiedPageContractV2GlobalStatus,
  resolveUnifiedPageContractV2SurfacePolicies,
  type UnifiedPageContractV2ButtonStatus,
} from '../app/contracts/unifiedPageContractV2';
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
const PROJECT_CONTEXT_CHANGED_EVENT = 'sc:project-context-changed';
const {
  resolveSceneCode,
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

function currentActionActivityRouteKey(): string {
  const currentActionId = String(route.params.actionId || route.query.action_id || '').trim();
  const currentMenuId = String(route.query.menu_id || '').trim() || '0';
  return currentActionId ? `action:${currentActionId}:menu:${currentMenuId}` : '';
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
const isComponentActive = ref(true);
const instanceActivityRouteKey = ref('');
const retainedRouteFullPath = ref('');
const renderErrorMessage = ref('');
const traceId = ref('');
const lastTraceId = ref('');
const records = ref<Array<Record<string, unknown>>>([]);
const listTotalCount = ref<number | null>(null);
const listOffset = ref(0);
const listLimitOverride = ref(0);
const listAggregates = ref<Record<string, Record<string, unknown>>>({});
const projectScopeTotals = ref<{ all: number; active: number; archived: number } | null>(null);
const projectScopeMetrics = ref<{ warning: number; done: number; amount: number } | null>(null);
const searchTerm = ref('');
const toolbarSearchDraft = ref('');
const toolbarSearchComposing = ref(false);
const activeCustomFilter = ref<{ label: string; domain: unknown[] } | null>(null);
const activeCustomFilterDomain = computed(() => activeCustomFilter.value?.domain || []);
const activeCustomFilterLabel = computed(() => activeCustomFilter.value?.label || '');
const activeGroupByDisplayLabel = ref('');
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
type ActionViewRuntimeContract = ActionContract & {
  head?: {
    model?: string;
    view_type?: string;
    context?: unknown;
    res_id?: number | string;
    permissions?: {
      read?: boolean;
      write?: boolean;
      create?: boolean;
      unlink?: boolean;
    };
  };
  views?: {
    tree?: ContractViewBlock;
    list?: ContractViewBlock;
    kanban?: ContractViewBlock;
    form?: ContractViewBlock;
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
    batch_policy?: SceneListProfile['batch_policy'];
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
  __unified_page_contract_v2?: Record<string, unknown>;
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
type BusinessCategoryCreateOption = {
  code: string;
  label: string;
  categoryId?: number;
  defaultValues: Record<string, unknown>;
};

function stableActionContractId(value: unknown, fallback: string) {
  const raw = String(value || fallback || '').trim();
  const normalized = raw
    .split('')
    .map((char) => {
      if (/^[A-Za-z0-9_.:-]$/.test(char)) return char;
      if (char === ' ' || char === '/') return '.';
      return '';
    })
    .join('')
    .replace(/^\.+|\.+$/g, '');
  const safe = normalized || fallback || 'action';
  return /^[A-Za-z]/.test(safe) ? safe : `id.${safe}`;
}

function resolveActionViewV2ButtonStatus(
  key: string,
  statusById: Record<string, UnifiedPageContractV2ButtonStatus>,
): UnifiedPageContractV2ButtonStatus | null {
  const stableKey = stableActionContractId(key, 'action');
  const candidates = [`btn.${stableKey}`, key, stableKey].filter(Boolean);
  for (const candidate of candidates) {
    if (statusById[candidate]) return statusById[candidate];
  }
  return null;
}

function applyActionViewV2ButtonStatus<T extends ContractActionButton>(
  action: T | null,
  statusById: Record<string, UnifiedPageContractV2ButtonStatus>,
): T | null {
  if (!action) return null;
  const status = resolveActionViewV2ButtonStatus(action.key, statusById);
  if (status?.visible === false) return null;
  if (status?.disabled === true) {
    action.enabled = false;
    action.hint = status.reasonCode || action.hint || 'disabled_by_status_contract';
  }
  return action;
}
const actionId = computed(() => {
  const fromParam = Number(route.params.actionId || 0);
  if (Number.isFinite(fromParam) && fromParam > 0) return fromParam;
  const fromQuery = Number(route.query.action_id || 0);
  return Number.isFinite(fromQuery) && fromQuery > 0 ? fromQuery : 0;
});
const actionMeta = computed(() => session.currentAction);
function resolveActionProjectScopeContext(): Record<string, unknown> {
  const policy = String(
    (actionMeta.value as Record<string, unknown> | null)?.project_scope_policy
      || (actionMeta.value as Record<string, unknown> | null)?.projectScopePolicy
      || '',
  ).trim();
  return policy ? { project_scope_policy: policy } : {};
}
const businessCategoryCreatePickerVisible = ref(false);
const routeSceneLabel = computed(() => String(route.query.scene_label || '').trim());
const menuId = computed(() => Number(route.query.menu_id ?? 0));
const keepSceneRoute = computed(() => String(route.name || '').toLowerCase() === 'scene');
const sceneKey = computed(() => {
  const metaKey = route.meta?.sceneKey as string | undefined;
  if (metaKey) return metaKey;
  const queryKey = (route.query.scene_key || route.query.scene) as string | undefined;
  if (queryKey) return String(queryKey);
  const actionSceneKey =
    findActionMeta(session.menuTree, actionId.value)?.scene_key
    || findActionMeta(session.menuTree, actionId.value)?.sceneKey
    || session.currentAction?.scene_key
    || session.currentAction?.sceneKey;
  return actionSceneKey ? String(actionSceneKey) : '';
});
const sceneContextEnabled = computed(() => keepSceneRoute.value || Boolean(sceneKey.value));
const scene = computed<Scene | null>(() => {
  if (!sceneKey.value) return null;
  return session.scenes.find((item: Scene) => item.key === sceneKey.value || resolveSceneCode(item) === sceneKey.value) || null;
});
const pageMode = computed(() => resolvePageMode(sceneKey.value, String(scene.value?.layout?.kind || '')));
const hasLedgerOverviewStrip = computed(() => String(scene.value?.layout?.kind || '').trim().toLowerCase() === 'ledger');

const listProfile = computed<SceneListProfile | null>(() => {
  return extractListProfile(actionContract.value);
});
type ActionBatchPolicy = NonNullable<SceneListProfile['batch_policy']>;

const batchPolicy = computed<ActionBatchPolicy>(() => {
  const profilePolicy = listProfile.value?.batch_policy;
  if (profilePolicy && Array.isArray(profilePolicy.available_actions) && profilePolicy.available_actions.length > 0) {
    return profilePolicy;
  }
  const surfacePolicies = resolveUnifiedPageContractV2SurfacePolicies(actionContract.value);
  return (surfacePolicies.batch_policy as ActionBatchPolicy | undefined) || profilePolicy || {};
});
const activeField = computed(() => String(batchPolicy.value.active_field || '').trim());
const allowedBatchActions = computed(() =>
  Array.isArray(batchPolicy.value.available_actions)
    ? batchPolicy.value.available_actions.map((item) => String(item || '').trim()).filter(Boolean)
    : [],
);
const listColumnOptions = computed(() => resolveListColumnOptions(actionContract.value, listProfile.value));
const listColumnVisibility = ref<Record<string, boolean>>({});
const listColumnOrder = ref<string[]>([]);
const listColumnWidths = ref<Record<string, number>>({});
const listColumnSaveStatus = ref<'idle' | 'saving' | 'saved' | 'error'>('idle');
const listColumnPreferenceScope = computed(() => {
  const aid = Number(actionId.value || 0);
  const targetModel = String(resolvedModelRef.value || model.value || '').trim();
  return {
    action_id: aid || undefined,
    model: targetModel,
    view_type: 'list',
    preference_key: 'list_columns',
  };
});
const sceneReadyEntry = computed<Record<string, unknown> | null>(() => {
  if (!sceneContextEnabled.value || !sceneKey.value) return null;
  return findSceneReadyEntry(session.sceneReadyContractV1, sceneKey.value);
});
const sceneReadyCollectionMode = computed<'list' | 'kanban'>(() => {
  const raw = String(route.query.view_mode || '').trim().toLowerCase();
  return raw === 'kanban' ? 'kanban' : 'list';
});
const sceneReadyListSurface = computed(() => resolveCollectionSceneReady(sceneReadyEntry.value, sceneReadyCollectionMode.value));
const sceneReadyHydrateRequested = ref(false);
function handleSceneBlockAction(payload: { action?: { target?: Record<string, unknown> } }) {
  const target = payload?.action?.target && typeof payload.action.target === 'object'
    ? payload.action.target
    : {};
  const targetKind = String(target.kind || '').trim();
  if (targetKind === 'quick_filter') {
    const filterKey = String(target.filter_key || '').trim();
    if (filterKey) {
      applyContractFilter(filterKey);
      return;
    }
  }
  if (targetKind === 'view_mode') {
    const mode = String(target.view_mode || '').trim();
    if (mode) {
      switchViewMode(mode);
      return;
    }
  }
  const route = String(target.route || '').trim();
  if (route) {
    void router.push(route);
    return;
  }
  const sceneKey = String(target.scene_key || '').trim();
  if (sceneKey) {
    void router.push({ name: 'scene', params: { sceneKey } });
  }
}
watch(
  () => [sceneKey.value, sceneReadyListSurface.value.sceneBlocks.length],
  async ([sceneKeyValue, blockCount]) => {
    if (!sceneKeyValue || Number(blockCount || 0) > 0 || sceneReadyHydrateRequested.value) return;
    sceneReadyHydrateRequested.value = true;
    try {
      const result = await intentRequest<Record<string, unknown>>({
        intent: 'system.init',
        params: {
          scene: 'web',
          with_preload: false,
          scene_ready_mode: 'full',
          with: ['workspace_home'],
          ...(config.startupRootXmlid ? { root_xmlid: config.startupRootXmlid } : {}),
          scene_key: sceneKeyValue,
        },
        meta: { startup_chain_bypass: true },
      });
      const contract = result.scene_ready_contract_v1;
      if (contract && typeof contract === 'object' && Array.isArray((contract as Record<string, unknown>).scenes)) {
        session.sceneReadyContractV1 = contract as never;
      }
    } catch (err) {
      void err;
    }
  },
  { immediate: true },
);
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
const currentMenuTitle = computed(() => {
  const node = findMenuNode(session.menuTree, Number(menuId.value || 0));
  const nodeActionId = Number(node?.meta?.action_id || 0);
  if (nodeActionId && nodeActionId !== actionId.value) return '';
  return String(node?.label || node?.name || node?.title || '').trim();
});
const contractViewType = ref('');
const contractReadAllowed = ref(true);
const contractWarningCount = ref(0);
const contractDegraded = ref(false);
const actionContract = ref<ActionViewRuntimeContract | null>(null);
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

function resolveCreateRight(contract: ActionViewRuntimeContract | null): boolean {
  const globalStatus = resolveUnifiedPageContractV2GlobalStatus(contract?.__unified_page_contract_v2);
  if (String(globalStatus?.pageAuth || '').trim().toLowerCase() === 'read') return false;
  const head = contract?.head?.permissions?.create;
  if (typeof head === 'boolean') return head;
  const effective = contract?.permissions?.effective?.rights?.create;
  if (typeof effective === 'boolean') return effective;
  return true;
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
const listGroupedRowsEnabled = computed(() =>
  Boolean(activeGroupByField.value && groupViewVisible.value),
);
function normalizeGroupCell(field: string, value: unknown) {
  const option = listColumnOptions.value.find((column) => column.name === field);
  if (Array.isArray(value)) {
    const rawValue = value.length ? value[0] : null;
    const label = value.length > 1 && value[1] !== null && value[1] !== undefined
      ? String(value[1])
      : String(rawValue ?? pageText('group_label_unset', '未设置'));
    return { value: rawValue, label };
  }
  if (value === null || value === undefined || value === '') {
    return { value: null, label: pageText('group_label_unset', '未设置') };
  }
  if (typeof value === 'boolean') {
    return { value, label: pageText(value ? 'boolean_true' : 'boolean_false', value ? '是' : '否') };
  }
  const key = String(value ?? '').trim();
  const selectionLabel = Array.isArray(option?.selection)
    ? option.selection.find((item) => item.value === key)?.label
    : '';
  return { value, label: selectionLabel || key || pageText('group_label_unset', '未设置') };
}
const currentPageGroupedRows = computed(() => {
  const field = String(activeGroupByField.value || '').trim();
  if (!field || !groupViewVisible.value) return [];
  if (groupedRows.value.length) return groupedRows.value;
  const groups = new Map<string, {
    key: string;
    label: string;
    count: number;
    sampleRows: Array<Record<string, unknown>>;
    domain: unknown[];
    pageOffset: number;
    pageLimit: number;
    pageCurrent: number;
    pageTotal: number;
    pageRangeStart: number;
    pageRangeEnd: number;
    pageHasPrev: boolean;
    pageHasNext: boolean;
  }>();
  records.value.forEach((row) => {
    const normalized = normalizeGroupCell(field, row[field]);
    const key = buildGroupKey(field, normalized.value, normalized.label);
    const existing = groups.get(key);
    if (existing) {
      existing.sampleRows.push(row);
      existing.count = existing.sampleRows.length;
      existing.pageLimit = existing.count || 1;
      existing.pageRangeEnd = existing.count;
      return;
    }
    groups.set(key, {
      key,
      label: normalized.label,
      count: 1,
      sampleRows: [row],
      domain: [[field, '=', normalized.value]],
      pageOffset: 0,
      pageLimit: 1,
      pageCurrent: 1,
      pageTotal: 1,
      pageRangeStart: 1,
      pageRangeEnd: 1,
      pageHasPrev: false,
      pageHasNext: false,
    });
  });
  return Array.from(groups.values()).map((group) => ({
    ...group,
    count: group.sampleRows.length,
    pageLimit: group.sampleRows.length || 1,
    pageRangeStart: group.sampleRows.length ? 1 : 0,
    pageRangeEnd: group.sampleRows.length,
  }));
});
const showStandaloneQuickFilters = computed(() => quickFiltersVisible.value && !showToolbarFilter.value);
const showStandaloneSavedFilters = computed(() => savedFiltersVisible.value && !showToolbarSavedFilter.value);
const showStandaloneGroupView = computed(() => groupViewVisible.value && !showToolbarGroup.value);
const toolbarActiveGroupKey = computed(() =>
  activeGroupByField.value || (activeGroupByDisplayLabel.value ? '__active_custom_group__' : String(route.query.group_by || '').trim()),
);
const showTopActionToolbar = computed(() =>
  showViewSwitch.value
  || showToolbarSearch.value
  || showToolbarFilter.value
  || showToolbarSavedFilter.value
  || showToolbarGroup.value
  || canCreateRecord.value,
);
const showGlobalEmptyNext = computed(() =>
  isSectionVisible('empty_next', {
    defaultEnabled: pageSectionEnabled('empty_next', true),
    tag: 'section',
    vmVisible: Boolean(vm.value.empty) && vm.value.content.kind !== 'list',
  }),
);

const businessCategoryCreateOptions = computed<BusinessCategoryCreateOption[]>(() => {
  const meta = actionMeta.value as Record<string, unknown> | null;
  const rawOptions = Array.isArray(meta?.business_category_options) ? meta.business_category_options : [];
  const seen = new Set<string>();
  return rawOptions
    .map((raw) => {
      const row = raw && typeof raw === 'object' && !Array.isArray(raw) ? raw as Record<string, unknown> : {};
      const code = String(row.code || '').trim();
      const label = String(row.label || '').trim();
      const defaultValuesRaw = row.default_values || row.defaultValues;
      const defaultValues = defaultValuesRaw && typeof defaultValuesRaw === 'object' && !Array.isArray(defaultValuesRaw)
        ? defaultValuesRaw as Record<string, unknown>
        : {};
      const categoryIdRaw = Number(row.category_id || row.categoryId || 0);
      const categoryId = Number.isFinite(categoryIdRaw) && categoryIdRaw > 0 ? categoryIdRaw : undefined;
      if (!code || seen.has(code)) return null;
      seen.add(code);
      const option: BusinessCategoryCreateOption = { code, label, defaultValues };
      if (categoryId) option.categoryId = categoryId;
      return option;
    })
    .filter((row): row is BusinessCategoryCreateOption => Boolean(row));
});

function closeBusinessCategoryCreatePicker() {
  businessCategoryCreatePickerVisible.value = false;
}

function createRouteQueryForBusinessCategory(categoryCode = '') {
  const code = String(categoryCode || '').trim();
  const option = code ? businessCategoryCreateOptions.value.find((row) => row.code === code) : undefined;
  const defaults: Record<string, string> = {};
  if (option?.categoryId) {
    defaults.default_business_category_id = String(option.categoryId);
  }
  Object.entries(option?.defaultValues || {}).forEach(([key, value]) => {
    const normalizedKey = String(key || '').trim();
    if (!normalizedKey || value === undefined || value === null) return;
    if (Array.isArray(value) || typeof value === 'object') return;
    defaults[`default_${normalizedKey}`] = String(value);
  });
  const label = String(option?.label || actionMeta.value?.name || currentMenuTitle.value || '办理类型').trim();
  return resolveCarryQuery(code ? {
    current_business_category_code: code,
    default_business_category_code: code,
    current_business_category_label: label,
    default_business_category_label: label,
    ctx_source: 'business_category_create_picker',
    ...defaults,
  } : undefined);
}

async function openCreateRecordWithBusinessCategory(categoryCode = '') {
  const targetModel = (resolvedModelRef.value || model.value || '').trim();
  if (!targetModel || !canCreateRecord.value) return;
  closeBusinessCategoryCreatePicker();
  await router.push({
    path: `/f/${encodeURIComponent(targetModel)}/new`,
    query: createRouteQueryForBusinessCategory(categoryCode),
  } as never);
}

async function openCreateRecord() {
  const targetModel = (resolvedModelRef.value || model.value || '').trim();
  if (!targetModel || !canCreateRecord.value) return;
  const existingCategoryCode = String(route.query.default_business_category_code || route.query.current_business_category_code || '').trim();
  if (!existingCategoryCode && businessCategoryCreateOptions.value.length > 1) {
    businessCategoryCreatePickerVisible.value = true;
    return;
  }
  await openCreateRecordWithBusinessCategory(existingCategoryCode || businessCategoryCreateOptions.value[0]?.code || '');
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
  const routeActionId = Number(route.query.action_id || 0);
  const fallbackMode = resolvedModelRef.value || routeActionId > 0 ? 'tree' : '';
  const mode = normalizeActionViewMode(preferredViewMode.value) || modes[0] || fallbackMode;
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
  resolveListColumnOptions,
  extractColumnsFromContract,
  extractListOrderFromContract,
  buildListSortOptions,
  convergeColumnsForSurface,
  extractKanbanFields,
  extractKanbanProfile,
  extractAdvancedViewFields,
  extractViewFieldLabels,
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
const kanbanFieldLabels = computed<Record<string, string>>(() => ({
  ...contractColumnLabels.value,
  ...extractViewFieldLabels(actionContract.value, 'kanban'),
  ...(listProfile.value?.column_labels || {}),
}));
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
  subtitle,
  statusLabel,
  pageStatus,
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
  return [];
});

const {
  metricFields: resolveProjectMetricFields,
  resolveProjectStateCell,
  resolveProjectAmount,
  isCompletedState,
} = useActionViewProjectMetricRuntime({
  listProfile,
  listColumnOptions,
});

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
  menuTitle: currentMenuTitle,
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
const showSceneBlocksDebug = computed(() => isSceneBlocksDebugEnabled(route));

watch(
  pageTitle,
  (title) => {
    if (!isComponentActive.value) return;
    session.updateActiveActivityTitle(title);
  },
  { immediate: true },
);

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
const toolbarUiLabels = computed<Record<string, string>>(() => {
  const rows = customSearchCapabilities.value.uiLabels || {};
  return Object.entries(rows).reduce<Record<string, string>>((acc, [key, value]) => {
    const normalizedKey = String(key || '').trim();
    const label = String(value || '').trim();
    if (normalizedKey && label) acc[normalizedKey] = label;
    return acc;
  }, {});
});

function toolbarUiLabel(key: string, fallback: string) {
  return toolbarUiLabels.value[key] || fallback;
}
const {
  toContractActionButton,
} = useActionViewContractActionButtonRuntime({
  selectedIds,
  resolvedModelRef,
  modelRef: model,
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
  toContractActionButton: (row, dedup) => applyActionViewV2ButtonStatus(
    toContractActionButton(row, dedup) as ContractActionButton | null,
    collectUnifiedPageContractV2ButtonStatus(actionContract.value),
  ),
  resolveContractActionPresentation,
  pageText,
});

const selectionActions = computed(() => {
  return allowedBatchActions.value
    .filter((action): action is 'archive' | 'activate' | 'delete' => action === 'archive' || action === 'activate' || action === 'delete')
    .map((action) => ({
      key: `batch:${action}`,
      label: action === 'delete'
        ? toolbarUiLabel('batch_label_delete', '批量删除')
        : toolbarUiLabel(action === 'activate' ? 'batch_label_activate' : 'batch_label_archive', action === 'activate' ? '批量激活' : '批量归档'),
      enabled: action === 'delete' ? String(batchPolicy.value.delete_mode || 'none') === 'unlink' : Boolean(activeField.value),
      hint: '',
    }));
});

function handleSelectionAction(key: string) {
  if (key.startsWith('batch:')) {
    const action = key.slice('batch:'.length);
    if (action === 'archive' || action === 'activate' || action === 'delete') {
      void runBatchPolicyAction(action);
    }
    return;
  }
  const target = contractActionButtons.value.find((action) => action.key === key);
  if (!target || !target.enabled) return;
  void runContractAction(target as ContractActionButton);
}

function resolveBatchDeleteFailureMessage(err: unknown) {
  if (err instanceof ApiError) {
    const message = String(err.message || '').trim();
    if (message) return message;
  }
  return resolveBatchActionFailureMessage({ action: 'delete', text: toolbarUiLabel });
}

async function runBatchPolicyAction(action: 'archive' | 'activate' | 'delete') {
  const targetModel = String(resolvedModelRef.value || model.value || '').trim();
  const selected = [...selectedIds.value];
  if (!allowedBatchActions.value.includes(action)) {
    batchMessage.value = toolbarUiLabel('batch_msg_action_not_allowed', '当前场景不支持该批量操作');
    return;
  }
  const guard = resolveBatchActionGuardDecision({
    targetModel,
    selectedCount: selected.length,
    action,
    hasActiveField: Boolean(activeField.value),
    deleteMode: String(batchPolicy.value.delete_mode || 'none'),
  });
  if (!guard.ok) {
    batchMessage.value = resolveBatchActionGuardMessage({
      reason: guard.reason as 'missing_target_model' | 'missing_selection' | 'active_field_required' | 'delete_mode_unavailable',
      text: toolbarUiLabel,
    });
    return;
  }
  if (action === 'delete') {
    if (!confirm(toolbarUiLabel('batch_confirm_delete', `确认删除选中的 ${selected.length} 条记录？`))) {
      return;
    }
    const seed = resolveBatchDeleteExecutionSeed({
      selectedIds: selected,
      buildIfMatchMap,
      buildIdempotencyKey,
    });
    batchBusy.value = true;
    try {
      await unlinkActionViewRecord({
        model: targetModel,
        ids: selected,
        context: resolveEffectiveRequestContext(),
        idempotencyKey: seed.dryRunIdempotencyKey,
        dryRun: true,
      });
      const result = await unlinkActionViewRecord({
        model: targetModel,
        ids: selected,
        context: resolveEffectiveRequestContext(),
        idempotencyKey: seed.idempotencyKey,
      });
      const resultMessage = resolveBatchActionResultMessage({
        action,
        idempotentReplay: result.idempotent_replay === true,
        succeeded: Array.isArray(result.ids) ? result.ids.length : selected.length,
        failed: 0,
        text: toolbarUiLabel,
      });
      clearSelection();
      await requestLoadPage();
      batchMessage.value = resultMessage;
    } catch (err) {
      batchMessage.value = action === 'delete'
        ? resolveBatchDeleteFailureMessage(err)
        : resolveBatchActionFailureMessage({ action, text: toolbarUiLabel });
    } finally {
      batchBusy.value = false;
    }
    return;
  }
  const activeValue = action === 'activate'
    ? batchPolicy.value.activate_value === true
    : batchPolicy.value.archive_value === true;
  const seed = resolveBatchStandardExecutionSeed({
    action,
    selectedIds: selected,
    activeField: activeField.value,
    activeValue,
    buildIfMatchMap,
    buildIdempotencyKey,
  });
  batchBusy.value = true;
  try {
    const result = await batchUpdateActionViewRecords(buildBatchUpdateRequest({
      model: targetModel,
      ids: selected,
      action,
      ifMatchMap: seed.ifMatchMap,
      idempotencyKey: seed.idempotencyKey,
      context: resolveEffectiveRequestContext(),
    }) as Parameters<typeof batchUpdateActionViewRecords>[0]);
    const resultMessage = resolveBatchActionResultMessage({
      action,
      idempotentReplay: result.idempotent_replay === true,
      succeeded: Number(result.succeeded || 0),
      failed: Number(result.failed || 0),
      text: toolbarUiLabel,
    });
    clearSelection();
    await requestLoadPage();
    batchMessage.value = resultMessage;
  } catch {
    batchMessage.value = resolveBatchActionFailureMessage({ action, text: toolbarUiLabel });
  } finally {
    batchBusy.value = false;
  }
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
    title: computed(() => t('strict_contract_missing_title', '配置状态提示')),
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
  actionContract,
  resolvedModelRef,
  modelRef: model,
  routerPush: (target) => router.push(target as never),
});

function resolveMenuCarryQuery(meta?: Record<string, unknown> | null, extra?: Record<string, unknown>) {
  return resolveCarryQuery({
    ...buildBusinessEntryNavQuery(meta || {}),
    ...(extra || {}),
  });
}

const suppressNextRouteReload = ref(false);
const routePresetRuntime = useActionViewRoutePresetRuntime({
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
  listProfile,
  collapsedGroupKeys,
  groupPageOffsets,
  appliedPresetLabel,
  routeContextSource,
  lastTrackedPreset,
  resolveWorkspaceContextQuery,
  replaceCurrentRouteQuery: (query) => {
    const routeState = resolveReplaceCurrentRouteState({ routePath: route.path, query });
    return router.replace(routeState.target as never).catch(() => {});
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
  applyRoutePreset,
  clearRoutePreset,
} = routePresetRuntime;

function applyRoutePatchAndReload(patch: Record<string, unknown>): void {
  suppressNextRouteReload.value = true;
  routePresetRuntime.applyRoutePatchAndReload(patch);
}

function normalizeActivityRuntimeRouteQuery(source: Record<string, unknown>): Record<string, unknown> {
  const allowedKeys = new Set([
    'search',
    'q',
    'active_filter',
    'saved_filter',
    'group_by',
    'group_value',
    'group_sample_limit',
    'group_sort',
    'group_collapsed',
    'group_page',
    'group_offset',
    'group_fp',
    'group_wid',
    'group_wdg',
    'group_wik',
  ]);
  const next: Record<string, unknown> = {};
  Object.entries(source).forEach(([key, value]) => {
    if (!allowedKeys.has(key)) return;
    if (Array.isArray(value)) {
      const values = value.map((item) => String(item || '').trim()).filter(Boolean);
      if (values.length) next[key] = values;
      return;
    }
    const text = String(value || '').trim();
    if (text) next[key] = text;
  });
  if (next.active_filter && !['all', 'active', 'archived'].includes(String(next.active_filter))) {
    delete next.active_filter;
  }
  if (next.group_sort && !['asc', 'desc'].includes(String(next.group_sort).toLowerCase())) {
    delete next.group_sort;
  }
  return next;
}

function updateActivityRuntimeQueryFromRoute(): void {
  if (route.name !== 'action') return;
  session.updateActiveActivityRuntimeQuery(normalizeActivityRuntimeRouteQuery(route.query));
}

function syncRouteListState(extra?: Record<string, unknown>): void {
  suppressNextRouteReload.value = true;
  routePresetRuntime.syncRouteListState(extra);
  const routeState = normalizeActivityRuntimeRouteQuery({
    ...normalizeActivityRuntimeRouteQuery(route.query),
    search: searchTerm.value,
    active_filter: filterValue.value !== 'all' ? filterValue.value : undefined,
    saved_filter: activeSavedFilterKey.value,
    group_by: activeGroupByField.value,
    group_sample_limit: groupSampleLimit.value,
    group_sort: groupSort.value,
    ...extra,
  });
  session.updateActiveActivityRuntimeQuery(routeState);
}

function syncRouteStateAndReload(extra?: Record<string, unknown>): void {
  suppressNextRouteReload.value = true;
  routePresetRuntime.syncRouteStateAndReload(extra);
}

function restartLoadWithRouteSync(extra?: Record<string, unknown>): Promise<void> | void {
  suppressNextRouteReload.value = true;
  return routePresetRuntime.restartLoadWithRouteSync(extra) as Promise<void> | void;
}

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
  activeGroupByField,
  searchTerm,
  listOffset,
  listLimitOverride,
  contractLimit,
  groupWindowOffset,
  groupWindowPrevOffset,
  groupWindowNextOffset,
  groupSampleLimit,
  groupSort,
  listProfile,
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
  applyGroupBy: applyGroupByRuntime,
  clearGroupBy: clearGroupByRuntime,
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

function applyGroupBy(field: string) {
  const normalized = String(field || '').trim();
  const found = routeGroupByChips.value.find((chip) => String((chip as Record<string, unknown>).field || '') === normalized) as Record<string, unknown> | undefined;
  activeGroupByDisplayLabel.value = String(found?.label || normalized);
  applyGroupByRuntime(field);
}

function applyCustomGroupBy(payload: { key: string; label: string }) {
  const key = String(payload.key || '').trim();
  if (!key) return;
  activeGroupByDisplayLabel.value = String(payload.label || key);
  applyGroupByRuntime(key);
}

function clearGroupBy() {
  activeGroupByDisplayLabel.value = '';
  clearGroupByRuntime();
}

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

async function handleSaveFavorite(payload: { name: string; isDefault?: boolean; isShared?: boolean }) {
  const targetModel = String(resolvedModelRef.value || model.value || '').trim();
  const name = String(payload.name || '').trim();
  if (!targetModel || !name) return;
  await saveActionViewSearchFavorite({
    model: targetModel,
    name,
    domain: resolveEffectiveFilterDomain(),
    context: resolveEffectiveRequestContext(),
    order: sortValue.value,
    action_id: actionId.value,
    is_default: payload.isDefault === true,
    is_shared: payload.isShared === true,
  });
  actionContract.value = await loadActionContract(actionId.value) as ActionViewRuntimeContract;
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
  routeDomainRaw: () => String(route.query.domain_raw || '').trim(),
  routeContextRaw: () => String(route.query.context_raw || '').trim(),
  routeContext: () => ({
    ...buildBusinessEntryRequestContext(route.query as Record<string, unknown>),
    ...resolveActionProjectScopeContext(),
  }),
  menuId,
  activeField,
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
  sortValue,
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
  listRecordsRaw: listActionViewRecordsRaw,
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
  listRecordsRaw: listActionViewRecordsRaw,
  resolveProjectStateCell,
  isCompletedState,
  resolveProjectAmount,
  resolveProjectMetricFields,
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
  buildRouteTarget: (navigation) => buildContractActionRouteTarget({
    nextActionId: typeof navigation === 'number' ? navigation : navigation.nextActionId,
    entryTarget: typeof navigation === 'number' ? null : navigation.entryTarget,
    carryQuery: resolveCarryQuery(),
    responseQuery: typeof navigation === 'number' ? null : navigation.query,
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
  executeSceneMutation,
  executeButton,
  buildButtonRequest: buildContractActionButtonRequest,
  resolveResponseNavigation: resolveContractActionResponseNavigation,
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
    listAggregatesRef: listAggregates,
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
    routeGroupClearedRaw: route.query.group_by_cleared,
    routeGroupValueRaw: route.query.group_value,
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
    resolveAction: (menuTree, nextActionId, currentAction) => resolveAction(
      menuTree,
      nextActionId,
      { ...(currentAction || {}), menu_id: menuId.value || currentAction?.menu_id },
      {
        menuId: menuId.value || currentAction?.menu_id,
        viewType: String(route.query.view_mode || '').trim() || undefined,
      },
    ),
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
    resolveLoadDynamicState: () => ({
      viewMode: viewMode.value,
      searchTerm: searchTerm.value,
      sortLabel: sortLabel.value,
      activeGroupByField: activeGroupByField.value,
      listOffset: listOffset.value,
      groupWindowOffset: groupWindowOffset.value,
      groupSampleLimit: groupSampleLimit.value,
      contractLimit: listLimitOverride.value > 0 ? listLimitOverride.value : contractLimit.value,
      groupPageOffsets: groupPageOffsets.value,
    }),
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
    listRecordsRaw: listActionViewRecordsRaw,
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
    activeField: activeField.value,
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
}

function onToolbarSearchCompositionStart(): void {
  toolbarSearchComposing.value = true;
}

function onToolbarSearchCompositionEnd(event: CompositionEvent): void {
  toolbarSearchComposing.value = false;
  const value = String((event.target as HTMLInputElement | null)?.value || '');
  toolbarSearchDraft.value = value;
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

function handleListPageLimitChange(limit: number): void {
  const normalized = Math.min(Math.max(Math.trunc(Number(limit || 0)), 1), 200);
  if (!Number.isFinite(normalized) || normalized <= 0) return;
  listLimitOverride.value = normalized;
  contractLimit.value = normalized;
  listOffset.value = 0;
  clearSelection();
  void requestLoadPage();
}

let listColumnPreferenceLoadSeq = 0;
let listColumnSaveSeq = 0;
let listColumnSaveStatusTimer: number | null = null;

function setListColumnSaveStatus(status: 'idle' | 'saving' | 'saved' | 'error') {
  listColumnSaveStatus.value = status;
  if (listColumnSaveStatusTimer) {
    window.clearTimeout(listColumnSaveStatusTimer);
    listColumnSaveStatusTimer = null;
  }
  if (status === 'saved') {
    listColumnSaveStatusTimer = window.setTimeout(() => {
      if (listColumnSaveStatus.value === 'saved') {
        listColumnSaveStatus.value = 'idle';
      }
      listColumnSaveStatusTimer = null;
    }, 2500);
  }
}

async function loadListColumnPreference(): Promise<void> {
  const seq = ++listColumnPreferenceLoadSeq;
  const scope = listColumnPreferenceScope.value;
  if (!scope.action_id && !scope.model) {
    listColumnVisibility.value = {};
    listColumnOrder.value = [];
    listColumnWidths.value = {};
    return;
  }
  try {
    const result = await getUserViewPreference(scope);
    if (seq !== listColumnPreferenceLoadSeq) return;
    const preference = result.preference || {};
    const visible = Array.isArray(preference.visible_columns) ? preference.visible_columns.map((item) => String(item || '').trim()).filter(Boolean) : [];
    const hidden = Array.isArray(preference.hidden_columns) ? preference.hidden_columns.map((item) => String(item || '').trim()).filter(Boolean) : [];
    const columnOrder = Array.isArray(preference.column_order) ? preference.column_order.map((item) => String(item || '').trim()).filter(Boolean) : [];
    const columnWidthsRaw = preference.column_widths && typeof preference.column_widths === 'object' ? preference.column_widths as Record<string, unknown> : {};
    const columnWidths = Object.entries(columnWidthsRaw).reduce<Record<string, number>>((acc, [name, width]) => {
      const normalizedName = String(name || '').trim();
      const normalizedWidth = normalizeListColumnWidth(width);
      if (normalizedName && normalizedWidth) acc[normalizedName] = normalizedWidth;
      return acc;
    }, {});
    const preferencePolicy = listProfile.value?.preference_policy || {};
    const allowVisibility = preferencePolicy.allow_visibility !== false;
    const allowOrder = preferencePolicy.allow_order !== false;
    const allowWidth = preferencePolicy.allow_width !== false;
    const lockedColumns = new Set(
      (Array.isArray(preferencePolicy.locked_columns) ? preferencePolicy.locked_columns : [])
        .map((item) => String(item || '').trim())
        .filter(Boolean),
    );
    const next: Record<string, boolean> = {};
    if (allowVisibility) {
      visible.forEach((name) => { next[name] = true; });
      hidden.forEach((name) => {
        if (!lockedColumns.has(name)) {
          next[name] = false;
        }
      });
    }
    listColumnVisibility.value = next;
    listColumnOrder.value = allowOrder ? columnOrder : [];
    listColumnWidths.value = allowWidth ? columnWidths : {};
  } catch (err) {
    if (seq === listColumnPreferenceLoadSeq) {
      listColumnVisibility.value = {};
      listColumnOrder.value = [];
      listColumnWidths.value = {};
    }
    console.warn('[list-columns] failed to load preference', err);
  }
}

function normalizeListColumnWidth(value: unknown) {
  const parsed = Number(value || 0);
  if (!Number.isFinite(parsed) || parsed <= 0) return 0;
  return Math.min(Math.max(Math.trunc(parsed), 80), 640);
}

function buildListColumnPreference(visibility: Record<string, boolean>, columnOrder: string[], columnWidths: Record<string, number>) {
  const preferencePolicy = listProfile.value?.preference_policy || {};
  const allowVisibility = preferencePolicy.allow_visibility !== false;
  const allowOrder = preferencePolicy.allow_order !== false;
  const allowWidth = preferencePolicy.allow_width !== false;
  const columnNames = listColumnOptions.value.map((column) => column.name);
  const columnNameSet = new Set(columnNames);
  const visibleColumns = allowVisibility ? columnNames.filter((name) => visibility[name] === true) : [];
  const hiddenColumns = allowVisibility ? columnNames.filter((name) => visibility[name] === false) : [];
  const orderedColumns = (allowOrder ? columnOrder : [])
    .map((name) => String(name || '').trim())
    .filter((name, index, rows) => Boolean(name) && columnNameSet.has(name) && rows.indexOf(name) === index);
  const normalizedWidths = (allowWidth ? Object.entries(columnWidths || {}) : []).reduce<Record<string, number>>((acc, [name, width]) => {
    const normalizedName = String(name || '').trim();
    const normalizedWidth = normalizeListColumnWidth(width);
    if (normalizedName && columnNameSet.has(normalizedName) && normalizedWidth) acc[normalizedName] = normalizedWidth;
    return acc;
  }, {});
  return {
    visible_columns: visibleColumns,
    hidden_columns: hiddenColumns,
    column_order: orderedColumns,
    column_widths: normalizedWidths,
  };
}

async function handleListColumnVisibilityChange(payload: { visibility: Record<string, boolean> }): Promise<void> {
  const saveSeq = ++listColumnSaveSeq;
  const next = payload.visibility || {};
  listColumnVisibility.value = { ...next };
  setListColumnSaveStatus('saving');
  try {
    await setUserViewPreference(listColumnPreferenceScope.value, buildListColumnPreference(next, listColumnOrder.value, listColumnWidths.value));
    if (saveSeq === listColumnSaveSeq) {
      setListColumnSaveStatus('saved');
    }
  } catch (err) {
    if (saveSeq === listColumnSaveSeq) {
      setListColumnSaveStatus('error');
    }
    console.warn('[list-columns] failed to save preference', err);
  }
}

async function handleListColumnOrderChange(payload: { columnOrder: string[] }): Promise<void> {
  const saveSeq = ++listColumnSaveSeq;
  const next = Array.isArray(payload.columnOrder) ? payload.columnOrder.map((item) => String(item || '').trim()).filter(Boolean) : [];
  listColumnOrder.value = next;
  setListColumnSaveStatus('saving');
  try {
    await setUserViewPreference(listColumnPreferenceScope.value, buildListColumnPreference(listColumnVisibility.value, next, listColumnWidths.value));
    if (saveSeq === listColumnSaveSeq) {
      setListColumnSaveStatus('saved');
    }
  } catch (err) {
    if (saveSeq === listColumnSaveSeq) {
      setListColumnSaveStatus('error');
    }
    console.warn('[list-columns] failed to save column order preference', err);
  }
}

async function handleListColumnWidthsChange(payload: { columnWidths: Record<string, number> }): Promise<void> {
  const saveSeq = ++listColumnSaveSeq;
  const next = Object.entries(payload.columnWidths || {}).reduce<Record<string, number>>((acc, [name, width]) => {
    const normalizedName = String(name || '').trim();
    const normalizedWidth = normalizeListColumnWidth(width);
    if (normalizedName && normalizedWidth) acc[normalizedName] = normalizedWidth;
    return acc;
  }, {});
  listColumnWidths.value = next;
  setListColumnSaveStatus('saving');
  try {
    await setUserViewPreference(
      listColumnPreferenceScope.value,
      buildListColumnPreference(listColumnVisibility.value, listColumnOrder.value, next),
    );
    if (saveSeq === listColumnSaveSeq) {
      setListColumnSaveStatus('saved');
    }
  } catch (err) {
    if (saveSeq === listColumnSaveSeq) {
      setListColumnSaveStatus('error');
    }
    console.warn('[list-columns] failed to save column width preference', err);
  }
}

async function handleToggleRecordFavorite(row: Record<string, unknown>, field: string, nextValue: boolean): Promise<void> {
  const targetModel = String(resolvedModelRef.value || model.value || '').trim();
  const recordId = Number(row.id || 0);
  const option = listColumnOptions.value.find((column) => column.name === field);
  const mutation = option?.mutation || {};
  const mutationOperation = String(mutation.operation || '').trim();
  const mutationField = String(mutation.field || field || '').trim();
  if (!targetModel || !recordId || mutationOperation !== 'record_write' || mutationField !== field) return;
  const previousValue = row[field];
  row[field] = nextValue;
  try {
    await writeActionViewRecord({
      model: targetModel,
      ids: [recordId],
      vals: { [mutationField]: nextValue },
      context: {},
    });
  } catch (err) {
    row[field] = previousValue;
    console.warn('[list-field-mutation] failed to save field state', err);
  }
}

watch(
  () => [
    listColumnPreferenceScope.value.action_id || 0,
    listColumnPreferenceScope.value.model || '',
    listColumnOptions.value.map((column) => column.name).join(','),
  ].join('|'),
  () => {
    void loadListColumnPreference();
  },
  { immediate: true },
);

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

function findMenuNodeByLabel(nodes: Array<Record<string, unknown>>, label: string): Record<string, unknown> | null {
  const expected = String(label || '').trim();
  if (!expected || !Array.isArray(nodes)) return null;
  for (const node of nodes) {
    if (!node || typeof node !== 'object') continue;
    const current = String(node.label || node.title || node.name || '').trim();
    if (current === expected) return node;
    const found = findMenuNodeByLabel((node.children as Array<Record<string, unknown>>) || [], expected);
    if (found) return found;
  }
  return null;
}

async function redirectMenuOnlyRouteIfNeeded(): Promise<boolean> {
  const currentMenuId = Number(menuId.value || 0);
  if (Number(actionId.value || 0) > 0 || currentMenuId <= 0) {
    return false;
  }
  let result = resolveMenuAction(session.menuTree, currentMenuId);
  if (result.kind === 'broken' && result.reason === 'menu not found') {
    const fallbackNode = findMenuNodeByLabel(
      session.menuTree as unknown as Array<Record<string, unknown>>,
      String(route.query.label || ''),
    );
    const fallbackMenuId = Number(fallbackNode?.menu_id || fallbackNode?.id || 0);
    if (fallbackMenuId > 0) {
      result = resolveMenuAction(session.menuTree, fallbackMenuId);
    }
  }
  if (result.kind === 'leaf') {
    const entryTarget = result.meta?.entry_target && typeof result.meta.entry_target === 'object'
      ? result.meta.entry_target as Record<string, unknown>
      : null;
    const targetActionId = Number(result.meta.action_id || 0);
    if (targetActionId <= 0) return false;
    session.setActionMeta(result.meta);
    if (entryTarget) {
      await router.replace(buildEntryTargetRouteTarget(entryTarget, {
        query: resolveMenuCarryQuery(result.meta),
        menuId: currentMenuId,
        actionId: targetActionId,
        keepSceneRoute: keepSceneRoute.value,
        routePath: route.path,
      }) as never);
      return true;
    }
    await router.replace({
      name: 'action',
      params: { actionId: targetActionId },
      query: resolveMenuCarryQuery(result.meta, { menu_id: currentMenuId, action_id: targetActionId }),
    });
    return true;
  }
  if (result.kind === 'redirect') {
    if (result.target.entry_target) {
      await router.replace(buildEntryTargetRouteTarget(result.target.entry_target, {
        query: resolveMenuCarryQuery(result.target.meta),
        menuId: result.target.menu_id || currentMenuId,
        actionId: result.target.action_id,
        keepSceneRoute: keepSceneRoute.value,
        routePath: route.path,
      }) as never);
      return true;
    }
    if (result.target.scene_key) {
      const sceneKey = String(result.target.scene_key || '').trim();
      await router.replace(buildCanonicalSceneRouteTarget(sceneKey, {
        scene: getSceneByKey(sceneKey),
        query: resolveMenuCarryQuery(result.target.meta),
        menuId: result.target.menu_id || currentMenuId,
        actionId: result.target.action_id,
      }));
      return true;
    }
    const targetActionId = Number(result.target.action_id || 0);
    if (targetActionId > 0) {
      if (result.target.meta) {
        session.setActionMeta(result.target.meta);
      }
      await router.replace({
        name: 'action',
        params: { actionId: targetActionId },
        query: resolveMenuCarryQuery(result.target.meta, {
          menu_id: result.target.menu_id || currentMenuId,
          action_id: targetActionId,
        }),
      });
      return true;
    }
  }
  return false;
}

onMounted(async () => {
  instanceActivityRouteKey.value = currentActionActivityRouteKey();
  renderErrorMessage.value = '';
  applyRoutePreset();
  if (await redirectMenuOnlyRouteIfNeeded()) {
    return;
  }
  await requestLoadPage();
  retainedRouteFullPath.value = route.fullPath;
  if (typeof window !== 'undefined') {
    window.addEventListener(PROJECT_CONTEXT_CHANGED_EVENT, handleProjectContextChanged);
  }
});

onActivated(() => {
  isComponentActive.value = true;
});

onDeactivated(() => {
  isComponentActive.value = false;
});

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener(PROJECT_CONTEXT_CHANGED_EVENT, handleProjectContextChanged);
  }
  if (listColumnSaveStatusTimer) {
    window.clearTimeout(listColumnSaveStatusTimer);
    listColumnSaveStatusTimer = null;
  }
});

onErrorCaptured((err) => {
  const message = err instanceof Error ? err.message : String(err || pageText('error_unknown_render', '未知渲染异常'));
  renderErrorMessage.value = `${pageText('error_action_render_failed', '列表页面渲染失败：')}${message}`;
  console.error('[ActionView] render failed', err);
  return false;
});

watch(
  () => route.fullPath,
  async () => {
    const currentKey = currentActionActivityRouteKey();
    if (instanceActivityRouteKey.value && currentKey !== instanceActivityRouteKey.value) return;
    if (!isComponentActive.value) return;
    if (suppressNextRouteReload.value) {
      suppressNextRouteReload.value = false;
      applyRoutePreset();
      updateActivityRuntimeQueryFromRoute();
      retainedRouteFullPath.value = route.fullPath;
      return;
    }
    if (retainedRouteFullPath.value === route.fullPath && status.value !== 'idle' && status.value !== 'loading') {
      applyRoutePreset();
      updateActivityRuntimeQueryFromRoute();
      return;
    }
    renderErrorMessage.value = '';
    listOffset.value = 0;
    clearSelection();
    applyRoutePreset();
    updateActivityRuntimeQueryFromRoute();
    if (await redirectMenuOnlyRouteIfNeeded()) {
      return;
    }
    void Promise.resolve(requestLoadPage()).then(() => {
      retainedRouteFullPath.value = route.fullPath;
    });
  },
);

watch(
  () => route.query,
  () => {
    const currentKey = currentActionActivityRouteKey();
    if (instanceActivityRouteKey.value && currentKey !== instanceActivityRouteKey.value) return;
    if (!isComponentActive.value) return;
    updateActivityRuntimeQueryFromRoute();
  },
  { deep: true, immediate: true },
);

watch(
  () => Number(session.projectContext?.selected?.id || 0),
  () => {
    if (!isComponentActive.value) return;
    refreshForProjectContextChange();
  },
);

function handleProjectContextChanged(): void {
  refreshForProjectContextChange();
}

function refreshForProjectContextChange(): void {
  renderErrorMessage.value = '';
  listOffset.value = 0;
  clearSelection();
  void requestLoadPage();
}
</script>

<style scoped>
.page {
  display: grid;
  gap: var(--sc-product-workspace-stack-gap);
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
  border: 1px solid var(--sc-app-info-border);
  border-radius: var(--sc-component-panel-radius);
  background: var(--sc-app-info-bg);
}

.route-preset p {
  margin: 0;
  color: var(--sc-app-info-text);
  font-size: 13px;
}

.clear-btn {
  border: 1px solid var(--sc-app-info-border);
  border-radius: var(--sc-component-button-radius);
  background: var(--sc-app-panel);
  color: var(--sc-app-info-text);
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
  border: 1px solid var(--sc-app-info-border);
  border-radius: var(--sc-component-panel-radius);
  background: var(--sc-app-info-bg);
  padding: 10px 12px;
}

.focus-intent {
  margin: 0;
  color: var(--sc-app-text-primary);
  font-size: 14px;
  font-weight: 700;
}

.focus-summary {
  margin: 4px 0 0;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.focus-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.contract-missing-alert {
  border: 1px solid var(--sc-app-danger-border);
  border-radius: var(--sc-component-panel-radius);
  background: var(--sc-app-danger-bg);
  padding: 10px 12px;
}

.contract-missing-title {
  margin: 0;
  color: var(--sc-app-danger-text);
  font-size: 13px;
  font-weight: 700;
}

.contract-missing-summary,
.contract-missing-defaults {
  margin: 4px 0 0;
  color: var(--sc-app-danger-text);
  font-size: 12px;
}

.empty-next {
  border: 1px dashed var(--sc-app-border-strong);
  border-radius: var(--sc-component-panel-radius);
  background: var(--sc-app-muted-bg);
  padding: 12px;
  display: grid;
  gap: 8px;
}

.empty-next p {
  margin: 0;
  color: var(--sc-app-text-secondary);
  font-size: 13px;
}

.empty-next-title {
  color: var(--sc-app-text-primary) !important;
  font-weight: 700;
}

.empty-next-hint {
  color: var(--sc-app-text-secondary) !important;
}

.empty-next-reason {
  color: var(--sc-semantic-text-muted) !important;
  font-size: 12px !important;
}

.contract-label {
  margin: 0;
  font-size: 13px;
  color: var(--sc-app-text-secondary);
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
  color: var(--sc-semantic-text-muted);
}

.contract-chip {
  border: 1px solid var(--sc-app-border-strong);
  border-radius: 999px;
  background: var(--sc-app-panel);
  color: var(--sc-app-text-primary);
  padding: 5px 11px;
  font-size: 12px;
  cursor: pointer;
}

.contract-chip.active {
  border-color: var(--sc-semantic-surface-interactive);
  color: var(--sc-app-info-text);
  background: var(--sc-app-info-bg);
}

.contract-chip.primary {
  border-color: var(--sc-semantic-surface-interactive);
  background: var(--sc-semantic-surface-interactive);
  color: var(--sc-semantic-text-on-interactive);
}

.contract-chip.ghost {
  border-style: dashed;
}

.advanced-view {
  border: 1px solid var(--sc-app-border);
  border-radius: var(--sc-component-panel-radius);
  background: var(--sc-app-panel);
  padding: 12px;
  display: grid;
  gap: 10px;
}

.advanced-view-head h3 {
  margin: 0;
  font-size: 15px;
  color: var(--sc-app-text-primary);
}

.advanced-view-head p {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--sc-semantic-text-muted);
}

.advanced-contract {
  border: 1px dashed var(--sc-app-border-strong);
  border-radius: var(--sc-component-panel-radius);
  padding: 8px 10px;
  background: var(--sc-app-muted-bg);
  display: grid;
  gap: 4px;
}

.advanced-contract p {
  margin: 0;
  font-size: 12px;
  color: var(--sc-app-text-secondary);
}

.advanced-list {
  display: grid;
  gap: 8px;
}

.advanced-item {
  border: 1px solid var(--sc-app-border);
  border-radius: var(--sc-component-panel-radius);
  padding: 8px 10px;
  display: grid;
  gap: 4px;
}

.advanced-item-title {
  margin: 0;
  font-size: 13px;
  color: var(--sc-app-text-primary);
  font-weight: 600;
}

.advanced-item-meta {
  margin: 0;
  font-size: 12px;
  color: var(--sc-semantic-text-muted);
}

.ledger-overview-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
}

.ledger-overview-card {
  border-radius: var(--sc-component-panel-radius);
  border: 1px solid var(--sc-app-border);
  padding: 10px;
  background: var(--sc-app-panel);
}

.ledger-overview-label {
  margin: 0;
  font-size: 12px;
  color: var(--sc-semantic-text-muted);
}

.ledger-overview-value {
  margin: 6px 0 0;
  font-size: 20px;
  font-weight: 700;
}

.ledger-overview-card.tone-danger { background: var(--sc-app-danger-bg); border-color: var(--sc-app-danger-border); color: var(--sc-app-danger-text); }
.ledger-overview-card.tone-success { background: var(--sc-app-success-bg); border-color: var(--sc-app-success-border); color: var(--sc-app-success-text); }
.ledger-overview-card.tone-info { background: var(--sc-app-info-bg); border-color: var(--sc-app-info-border); color: var(--sc-app-info-text); }
.ledger-overview-card.tone-neutral { background: var(--sc-app-muted-bg); border-color: var(--sc-app-border); color: var(--sc-app-text-secondary); }

.business-category-picker-backdrop {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.38);
}

.business-category-picker {
  width: min(560px, 100%);
  max-height: min(720px, calc(100vh - 48px));
  overflow: auto;
  border: 1px solid var(--sc-app-border);
  border-radius: var(--sc-component-panel-radius);
  background: var(--sc-app-panel);
  box-shadow: var(--sc-semantic-shadow-modal);
}

.business-category-picker-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 18px 12px;
  border-bottom: 1px solid var(--sc-app-border);
}

.business-category-picker-head h3,
.business-category-picker-head p {
  margin: 0;
}

.business-category-picker-head h3 {
  color: var(--sc-app-text-primary);
  font-size: 16px;
  line-height: 1.35;
}

.business-category-picker-head p {
  margin-top: 4px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.business-category-picker-close {
  width: 32px;
  height: 32px;
  border: 1px solid var(--sc-app-border-strong);
  border-radius: 999px;
  background: var(--sc-app-panel);
  color: var(--sc-app-text-secondary);
  cursor: pointer;
}

.business-category-picker-list {
  display: grid;
  gap: 8px;
  padding: 14px;
}

.business-category-picker-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 44px;
  border: 1px solid var(--sc-app-border);
  border-radius: var(--sc-component-control-radius);
  background: var(--sc-app-muted-bg);
  color: var(--sc-app-text-primary);
  padding: 10px 12px;
  text-align: left;
  cursor: pointer;
}

.business-category-picker-option:hover {
  border-color: var(--sc-semantic-surface-interactive);
  background: var(--sc-app-info-bg);
}

.business-category-picker-option span {
  font-size: 14px;
  font-weight: 700;
}

.business-category-picker-option small {
  color: var(--sc-semantic-text-muted);
  font-size: 11px;
  white-space: nowrap;
}

@media (max-width: 760px) {
  .focus-strip {
    flex-direction: column;
    align-items: flex-start;
  }

  .business-category-picker-backdrop {
    align-items: flex-end;
    padding: 12px;
  }

  .business-category-picker-option {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>

<template>
  <section class="page">
    <!-- Page intent: 在列表场景中先判断状态，再给出下一步可执行动作。 -->
    <section v-if="headerActions.length" class="page-actions">
      <button v-for="action in headerActions" :key="`header-${action.key}`" class="contract-chip ghost" @click="executeHeaderAction(action.key)">
        {{ action.label || action.key }}
      </button>
    </section>
    <section
      v-if="availableViewModes.length > 1 && pageSectionEnabled('view_switch', true) && pageSectionTagIs('view_switch', 'section')"
      class="view-switch"
      :style="pageSectionStyle('view_switch')"
    >
      <p class="contract-label">{{ pageText('label.view_switch', '视图切换') }}</p>
      <div class="contract-chips">
        <button
          v-for="mode in availableViewModes"
          :key="`view-mode-${mode}`"
          class="contract-chip"
          :class="{ active: viewMode === mode }"
          :disabled="status === 'loading' || batchBusy || viewMode === mode"
          @click="switchViewMode(mode)"
        >
          {{ viewModeLabel(mode) }}
        </button>
      </div>
    </section>
    <section v-if="pageSectionEnabled('route_preset', true) && pageSectionTagIs('route_preset', 'section') && appliedPresetLabel" class="route-preset" :style="pageSectionStyle('route_preset')">
      <p>
        {{ pageText('route_preset_applied_prefix', '已应用推荐筛选：') }}{{ appliedPresetLabel }}
        <span v-if="routeContextSource">（{{ pageText('route_preset_source_prefix', '来源：') }}{{ routeContextSource }}）</span>
      </p>
      <button class="clear-btn" @click="clearRoutePreset">{{ pageText('route_preset_clear', '清除推荐') }}</button>
    </section>
    <section v-if="pageSectionEnabled('focus_strip', true) && pageSectionTagIs('focus_strip', 'section')" class="focus-strip" :style="pageSectionStyle('focus_strip')">
      <div>
        <p class="focus-intent">{{ surfaceIntent.title }}</p>
        <p class="focus-summary">{{ surfaceIntent.summary }}</p>
      </div>
      <div class="focus-actions">
        <button v-for="item in surfaceIntent.actions" :key="`focus-${item.label}`" class="contract-chip ghost" @click="openFocusAction(item)">
          {{ item.label }}
        </button>
      </div>
    </section>
    <section v-if="pageSectionEnabled('quick_filters', true) && pageSectionTagIs('quick_filters', 'section') && (contractPrimaryFilterChips.length || contractOverflowFilterChips.length)" class="contract-block" :style="pageSectionStyle('quick_filters')">
      <p class="contract-label">{{ pageText('label.quick_filters', '快速筛选') }}</p>
      <div class="contract-chips">
        <button
          v-for="chip in contractPrimaryFilterChips"
          :key="`contract-filter-${chip.key}`"
          class="contract-chip"
          :class="{ active: activeContractFilterKey === chip.key }"
          :disabled="status === 'loading' || batchBusy"
          @click="applyContractFilter(chip.key)"
        >
          {{ chip.label }}
        </button>
        <button
          v-if="activeContractFilterKey"
          class="contract-chip ghost"
          :disabled="status === 'loading' || batchBusy"
          @click="clearContractFilter"
        >
          {{ pageText('chip_action_clear', '清除') }}
        </button>
        <button
          v-if="contractOverflowFilterChips.length"
          class="contract-chip ghost"
          :disabled="status === 'loading' || batchBusy"
          @click="showMoreContractFilters = !showMoreContractFilters"
        >
          {{
            showMoreContractFilters
              ? pageText('chip_more_filters_collapse', '收起更多筛选')
              : `${pageText('chip_more_filters_expand', '更多筛选')} (${contractOverflowFilterChips.length})`
          }}
        </button>
      </div>
      <div v-if="showMoreContractFilters && contractOverflowFilterChips.length" class="contract-chips">
        <button
          v-for="chip in contractOverflowFilterChips"
          :key="`contract-filter-overflow-${chip.key}`"
          class="contract-chip"
          :class="{ active: activeContractFilterKey === chip.key }"
          :disabled="status === 'loading' || batchBusy"
          @click="applyContractFilter(chip.key)"
        >
          {{ chip.label }}
        </button>
      </div>
    </section>
    <section v-if="pageSectionEnabled('saved_filters', true) && pageSectionTagIs('saved_filters', 'section') && (savedFilterPrimaryChips.length || savedFilterOverflowChips.length)" class="contract-block" :style="pageSectionStyle('saved_filters')">
      <p class="contract-label">{{ pageText('label.saved_filters', '已保存筛选') }}</p>
      <div class="contract-chips">
        <button
          v-for="chip in savedFilterPrimaryChips"
          :key="`saved-filter-${chip.key}`"
          class="contract-chip"
          :class="{ active: activeSavedFilterKey === chip.key }"
          :disabled="status === 'loading' || batchBusy"
          @click="applySavedFilter(chip.key)"
        >
          {{ chip.label }}
        </button>
        <button
          v-if="activeSavedFilterKey"
          class="contract-chip ghost"
          :disabled="status === 'loading' || batchBusy"
          @click="clearSavedFilter"
        >
          {{ pageText('chip_action_clear', '清除') }}
        </button>
        <button
          v-if="savedFilterOverflowChips.length"
          class="contract-chip ghost"
          :disabled="status === 'loading' || batchBusy"
          @click="showMoreSavedFilters = !showMoreSavedFilters"
        >
          {{
            showMoreSavedFilters
              ? pageText('chip_more_filters_collapse', '收起更多筛选')
              : `${pageText('chip_more_filters_expand', '更多筛选')} (${savedFilterOverflowChips.length})`
          }}
        </button>
      </div>
      <div v-if="showMoreSavedFilters && savedFilterOverflowChips.length" class="contract-chips">
        <button
          v-for="chip in savedFilterOverflowChips"
          :key="`saved-filter-overflow-${chip.key}`"
          class="contract-chip"
          :class="{ active: activeSavedFilterKey === chip.key }"
          :disabled="status === 'loading' || batchBusy"
          @click="applySavedFilter(chip.key)"
        >
          {{ chip.label }}
        </button>
      </div>
    </section>
    <section v-if="pageSectionEnabled('group_view', true) && pageSectionTagIs('group_view', 'section') && (groupByPrimaryChips.length || groupByOverflowChips.length)" class="contract-block" :style="pageSectionStyle('group_view')">
      <p class="contract-label">{{ pageText('label.group_view', '分组查看') }}</p>
      <div class="contract-chips">
        <button
          v-for="chip in groupByPrimaryChips"
          :key="`group-by-${chip.field}`"
          class="contract-chip"
          :class="{ active: activeGroupByField === chip.field }"
          :disabled="status === 'loading' || batchBusy"
          @click="applyGroupBy(chip.field)"
        >
          {{ chip.label }}
        </button>
        <button
          v-if="activeGroupByField"
          class="contract-chip ghost"
          :disabled="status === 'loading' || batchBusy"
          @click="clearGroupBy"
        >
          {{ pageText('chip_action_clear', '清除') }}
        </button>
        <button
          v-if="groupByOverflowChips.length"
          class="contract-chip ghost"
          :disabled="status === 'loading' || batchBusy"
          @click="showMoreGroupBy = !showMoreGroupBy"
        >
          {{
            showMoreGroupBy
              ? pageText('chip_more_group_collapse', '收起更多分组')
              : `${pageText('chip_more_group_expand', '更多分组')} (${groupByOverflowChips.length})`
          }}
        </button>
      </div>
      <div v-if="showMoreGroupBy && groupByOverflowChips.length" class="contract-chips">
        <button
          v-for="chip in groupByOverflowChips"
          :key="`group-by-overflow-${chip.field}`"
          class="contract-chip"
          :class="{ active: activeGroupByField === chip.field }"
          :disabled="status === 'loading' || batchBusy"
          @click="applyGroupBy(chip.field)"
        >
          {{ chip.label }}
        </button>
      </div>
    </section>
    <GroupSummaryBar
      v-if="pageSectionEnabled('group_summary', true) && pageSectionTagIs('group_summary', 'section') && groupSummaryItems.length"
      :style="pageSectionStyle('group_summary')"
      :items="groupSummaryItems"
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
    <section v-if="pageSectionEnabled('quick_actions', true) && pageSectionTagIs('quick_actions', 'section') && (contractPrimaryActions.length || contractOverflowActions.length)" class="contract-block" :style="pageSectionStyle('quick_actions')">
      <p class="contract-label">{{ pageText('label.quick_actions', '快捷操作') }}</p>
      <div class="contract-chips">
        <button
          v-for="btn in contractPrimaryActions"
          :key="`contract-action-${btn.key}`"
          class="contract-chip"
          :disabled="!btn.enabled || status === 'loading' || batchBusy"
          :title="btn.hint"
          @click="runContractAction(btn)"
        >
          {{ btn.label }}
        </button>
        <button
          v-if="contractOverflowActions.length"
          class="contract-chip ghost"
          :disabled="status === 'loading' || batchBusy"
          @click="showMoreContractActions = !showMoreContractActions"
        >
          {{
            showMoreContractActions
              ? pageText('chip_more_actions_collapse', '收起更多操作')
              : `${pageText('chip_more_actions_expand', '更多操作')} (${contractOverflowActions.length})`
          }}
        </button>
      </div>
      <div v-if="showMoreContractActions && contractOverflowActionGroups.length" class="contract-groups">
        <section
          v-for="group in contractOverflowActionGroups"
          :key="`contract-group-${group.key}`"
          class="contract-group"
        >
          <p class="contract-group-label">{{ group.label }}</p>
          <div class="contract-chips">
            <button
              v-for="btn in group.actions"
              :key="`contract-group-action-${group.key}-${btn.key}`"
              class="contract-chip"
              :disabled="!btn.enabled || status === 'loading' || batchBusy"
              :title="btn.hint"
              @click="runContractAction(btn)"
            >
              {{ btn.label }}
            </button>
          </div>
        </section>
      </div>
    </section>
    <section v-if="viewMode === 'kanban' && hasLedgerOverviewStrip && ledgerOverviewItems.length" class="ledger-overview-strip">
      <article v-for="item in ledgerOverviewItems" :key="item.key" class="ledger-overview-card" :class="`tone-${item.tone}`">
        <p class="ledger-overview-label">{{ item.label }}</p>
        <p class="ledger-overview-value">{{ item.value }}</p>
      </article>
    </section>
    <KanbanPage
      v-if="viewMode === 'kanban'"
      :title="pageTitle"
      :status="pageStatus"
      :loading="status === 'loading' || batchBusy"
      :error-message="errorMessage"
      :trace-id="traceId"
      :error="error"
      :records="records"
      :fields="kanbanFields"
      :primary-fields="kanbanPrimaryFields"
      :secondary-fields="kanbanSecondaryFields"
      :status-fields="kanbanStatusFields"
      :field-labels="contractColumnLabels"
      :title-field="kanbanTitleField"
      :subtitle="subtitle"
      :status-label="statusLabel"
      :scene-key="sceneKey"
      :page-mode="pageMode"
      :on-reload="reload"
      :on-card-click="handleRowClick"
    />
    <ListPage
      v-else-if="viewMode === 'tree'"
      :title="pageTitle"
      :model="model"
      :status="pageStatus"
      :loading="status === 'loading' || batchBusy"
      :error-message="errorMessage"
      :trace-id="traceId"
      :error="error"
      :columns="columns"
      :records="records"
      :column-labels="contractColumnLabels"
      :sort-label="sortLabel"
      :sort-options="sortOptions"
      :sort-value="sortValue"
      :filter-value="filterValue"
      :search-term="searchTerm"
      :subtitle="subtitle"
      :status-label="statusLabel"
      :scene-key="sceneKey"
      :page-mode="pageMode"
      :record-count="recordCount"
      :summary-items="listSummaryItems"
      :selected-ids="selectedIds"
      :batch-message="batchMessage"
      :batch-details="batchDetails"
      :failed-csv-available="Boolean(failedCsvContentB64)"
      :has-more-failures="batchHasMoreFailures"
      :show-assign="hasAssigneeField"
      :show-delete="canBatchDelete"
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
    <section v-else-if="pageSectionEnabled('advanced_view', true) && pageSectionTagIs('advanced_view', 'section')" class="advanced-view" :style="pageSectionStyle('advanced_view')">
      <header class="advanced-view-head">
        <h3>{{ advancedViewTitle }}</h3>
        <p>{{ advancedViewHint }}</p>
      </header>
      <div class="advanced-contract">
        <p class="contract-label">{{ pageText('label.contract_summary', '契约摘要') }}</p>
        <p>view_type={{ contractViewType || '-' }} · mode={{ viewMode || '-' }} · records={{ records.length }}</p>
      </div>
      <div v-if="records.length" class="advanced-list">
        <article v-for="(row, idx) in records.slice(0, 20)" :key="`adv-${idx}-${String(row.id || idx)}`" class="advanced-item">
          <p class="advanced-item-title">{{ advancedRowTitle(row) }}</p>
          <p class="advanced-item-meta">{{ advancedRowMeta(row) }}</p>
        </article>
      </div>
      <section v-else class="empty-next">
        <p class="empty-next-title">{{ surfaceIntent.emptyTitle }}</p>
        <p class="empty-next-hint">{{ advancedViewHint }}</p>
      </section>
    </section>
    <section v-if="pageSectionEnabled('empty_next', true) && pageSectionTagIs('empty_next', 'section') && pageStatus === 'empty'" class="empty-next" :style="pageSectionStyle('empty_next')">
      <p class="empty-next-title">{{ surfaceIntent.emptyTitle }}</p>
      <p class="empty-next-hint">{{ surfaceIntent.emptyHint }}</p>
      <p class="empty-next-reason">{{ emptyReasonText }}</p>
      <div class="focus-actions">
        <button class="contract-chip primary" @click="openFocusAction(surfaceIntent.primaryAction)">{{ surfaceIntent.primaryAction.label }}</button>
        <button
          v-if="surfaceIntent.secondaryAction"
          class="contract-chip ghost"
          @click="openFocusAction(surfaceIntent.secondaryAction)"
        >
          {{ surfaceIntent.secondaryAction.label }}
        </button>
      </div>
    </section>

    <DevContextPanel
      :visible="showHud && pageSectionEnabled('dev_context', true) && pageSectionTagIs('dev_context', 'div')"
      :style="pageSectionStyle('dev_context')"
      title="View Context"
      :entries="hudEntries"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, inject, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { batchUpdateRecords, exportRecordsCsv, listRecords, listRecordsRaw } from '../api/data';
import { ApiError } from '../api/client';
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
import { collectErrorContextIssue, issueScopeLabel } from '../app/errorContext';
import type { Scene, SceneListProfile } from '../app/resolvers/sceneRegistry';
import { findSceneReadyEntry, resolveListSceneReady } from '../app/resolvers/sceneReadyResolver';
import { normalizeSceneActionProtocol, type MutationContract, type ProjectionRefreshPolicy } from '../app/sceneActionProtocol';
import { executeProjectionRefresh } from '../app/projectionRefreshRuntime';
import { executeSceneMutation } from '../app/sceneMutationRuntime';
import { readWorkspaceContext, stripWorkspaceContext } from '../app/workspaceContext';
import { pickContractNavQuery } from '../app/navigationContext';
import { usePageContract } from '../app/pageContract';
import { executePageContractAction } from '../app/pageContractActionRuntime';
import { resolvePageMode } from '../app/pageMode';
import { formatAmountCN, semanticStatus } from '../utils/semantic';
import type { NavNode } from '@sc/schema';

type NavNodeWithScene = NavNode & {
  scene_key?: string;
  sceneKey?: string;
};

function resolveSceneCode(scene: Scene): string {
  const raw = scene as Scene & { code?: string };
  return typeof raw.code === 'string' ? raw.code : '';
}

function resolveNodeSceneKey(node: NavNode): string {
  const raw = node as NavNodeWithScene;
  return raw.scene_key || raw.sceneKey || node.meta?.scene_key || '';
}

const route = useRoute();
const router = useRouter();
const session = useSessionStore();
const pageContract = usePageContract('action');
const pageText = pageContract.text;
const pageSectionEnabled = pageContract.sectionEnabled;
const pageSectionStyle = pageContract.sectionStyle;
const pageSectionTagIs = pageContract.sectionTagIs;
const pageActionIntent = pageContract.actionIntent;
const pageActionTarget = pageContract.actionTarget;
const pageGlobalActions = pageContract.globalActions;

const status = ref<'idle' | 'loading' | 'ok' | 'empty' | 'error'>('idle');
const traceId = ref('');
const lastTraceId = ref('');
const records = ref<Array<Record<string, unknown>>>([]);
const listTotalCount = ref<number | null>(null);
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
const kanbanTitleFieldHint = ref('');
const hasActiveField = ref(false);
const hasAssigneeField = ref(false);
const assigneeOptions = ref<Array<{ id: number; name: string }>>([]);
const selectedAssigneeId = ref<number | null>(null);
const selectedIds = ref<number[]>([]);
const batchMessage = ref('');
type BatchDetailLine = { text: string; actionRaw?: string; actionLabel?: string };
const batchDetails = ref<BatchDetailLine[]>([]);
const failedCsvFileName = ref('');
const failedCsvContentB64 = ref('');
const batchFailedOffset = ref(0);
const batchFailedLimit = ref(12);
const batchHasMoreFailures = ref(false);
const groupSummaryItems = ref<GroupSummaryItem[]>([]);
type GroupedRow = {
  key: string;
  label: string;
  count: number;
  sampleRows: Array<Record<string, unknown>>;
  domain?: unknown[];
  pageOffset: number;
  pageLimit: number;
  pageCurrent?: number;
  pageTotal?: number;
  pageRangeStart?: number;
  pageRangeEnd?: number;
  pageWindow?: { start?: number; end?: number };
  pageHasPrev?: boolean;
  pageHasNext?: boolean;
  pageSyncedFromServer?: boolean;
  loading?: boolean;
};
const groupedRows = ref<GroupedRow[]>([]);
const groupSampleLimit = ref(3);
const groupSort = ref<'asc' | 'desc'>('desc');
const collapsedGroupKeys = ref<string[]>([]);
const groupPageOffsets = ref<Record<string, number>>({});
const activeGroupSummaryKey = ref('');
const activeGroupSummaryDomain = ref<unknown[]>([]);
const groupWindowOffset = ref(0);
const groupWindowCount = ref(0);
const groupWindowTotal = ref<number | null>(null);
const groupWindowStart = ref<number | null>(null);
const groupWindowEnd = ref<number | null>(null);
const groupWindowId = ref('');
const groupQueryFingerprint = ref('');
const groupWindowDigest = ref('');
const groupWindowIdentityKey = ref('');
const groupWindowPrevOffset = ref<number | null>(null);
const groupWindowNextOffset = ref<number | null>(null);
const headerActions = computed(() => pageGlobalActions.value);
const advancedFields = ref<string[]>([]);
const lastBatchRequest = ref<{
  model: string;
  ids: number[];
  action: 'archive' | 'activate' | 'assign';
  assigneeId?: number;
  ifMatchMap: Record<number, string>;
  idempotencyKey: string;
  context: Record<string, unknown>;
} | null>(null);
const batchBusy = ref(false);
const lastIntent = ref('');
const lastWriteMode = ref('');
const lastLatencyMs = ref<number | null>(null);
const appliedPresetLabel = ref('');
const routeContextSource = ref('');
const lastTrackedPreset = ref('');
const { error, clearError, setError } = useStatus();
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
type ActionMetaLoose = {
  order?: string;
  url?: string;
};
type ContractFilterChip = {
  key: string;
  label: string;
  domain: unknown[];
  domainRaw: string;
  context: Record<string, unknown>;
  contextRaw: string;
};
type ContractSavedFilterChip = {
  key: string;
  label: string;
  domain: unknown[];
  domainRaw: string;
  context: Record<string, unknown>;
  contextRaw: string;
  isDefault: boolean;
};
type ContractGroupByChip = {
  field: string;
  label: string;
  isDefault: boolean;
  context: Record<string, unknown>;
  contextRaw: string;
};
type GroupSummaryItem = {
  key: string;
  label: string;
  count: number;
  domain: unknown[];
  value?: unknown;
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
type FocusNavAction = {
  label: string;
  to: string;
  query?: Record<string, string>;
};
type SurfaceIntent = {
  title: string;
  summary: string;
  actions: FocusNavAction[];
  emptyTitle: string;
  emptyHint: string;
  primaryAction: FocusNavAction;
  secondaryAction?: FocusNavAction;
};
type SurfaceIntentContract = {
  title?: string;
  summary?: string;
  actions?: FocusNavAction[];
  empty_title?: string;
  empty_hint?: string;
  primary_action?: FocusNavAction;
  secondary_action?: FocusNavAction;
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

const listProfile = computed<SceneListProfile | null>(() => {
  return (scene.value?.list_profile as SceneListProfile) || null;
});
const sceneReadyEntry = computed<Record<string, unknown> | null>(() => {
  if (!sceneKey.value) return null;
  return findSceneReadyEntry(session.sceneReadyContractV1, sceneKey.value);
});
const sceneReadyListSurface = computed(() => resolveListSceneReady(sceneReadyEntry.value));

const model = computed(() => actionMeta.value?.model ?? '');
const injectedTitle = inject('pageTitle', computed(() => ''));
const contractViewType = ref('');
const contractReadAllowed = ref(true);
const contractWarningCount = ref(0);
const contractDegraded = ref(false);
const actionContract = ref<ActionContractLoose | null>(null);
const resolvedModelRef = ref('');
const canBatchDelete = computed(() => {
  const unlinkRight = actionContract.value?.permissions?.effective?.rights?.unlink;
  return unlinkRight === true && viewMode.value === 'list';
});
const activeContractFilterKey = ref('');
const activeSavedFilterKey = ref('');
const activeGroupByField = ref('');
const contractLimit = ref(40);
const showMoreContractActions = ref(false);
const showMoreContractFilters = ref(false);
const showMoreSavedFilters = ref(false);
const showMoreGroupBy = ref(false);
const preferredViewMode = ref('');

function replaceCurrentRouteQuery(query: Record<string, unknown>) {
  router.replace({ path: route.path, query }).catch(() => {});
}

function normalizeViewMode(raw: unknown): string {
  const mode = String(raw || '').trim().toLowerCase();
  if (!mode) return '';
  if (mode === 'list') return 'tree';
  return mode;
}

function parseViewModes(raw: unknown): string[] {
  if (Array.isArray(raw)) {
    const out: string[] = [];
    const seen = new Set<string>();
    raw
      .map((item) => normalizeViewMode(item))
      .forEach((mode) => {
        if (!mode || seen.has(mode)) return;
        seen.add(mode);
        out.push(mode);
      });
    return out;
  }
  const out: string[] = [];
  const seen = new Set<string>();
  String(raw || '')
    .split(',')
    .map((item) => normalizeViewMode(item))
    .forEach((mode) => {
      if (!mode || seen.has(mode)) return;
      seen.add(mode);
      out.push(mode);
    });
  return out;
}

function collectContractViewModes(contract: ActionContractLoose | null): string[] {
  if (!contract) return [];
  const out: string[] = [];
  const seen = new Set<string>();
  const addMode = (raw: unknown) => {
    const mode = normalizeViewMode(raw);
    if (!mode || seen.has(mode)) return;
    seen.add(mode);
    out.push(mode);
  };
  const addModes = (raw: unknown) => {
    parseViewModes(raw).forEach((mode) => addMode(mode));
  };

  addModes(contract.head?.view_type);
  addModes(contract.view_type);
  addModes(contract.ui_contract?.head?.view_type);
  addModes(contract.ui_contract?.view_type);

  const views = contract.views || {};
  const nestedViews = contract.ui_contract?.views || {};
  if (views.tree || views.list || nestedViews.tree || nestedViews.list) addMode('tree');
  if (views.kanban || nestedViews.kanban) addMode('kanban');
  if (views.pivot || nestedViews.pivot) addMode('pivot');
  if (views.graph || nestedViews.graph) addMode('graph');
  if (views.calendar || nestedViews.calendar) addMode('calendar');
  if (views.gantt || nestedViews.gantt) addMode('gantt');
  if (views.activity || nestedViews.activity) addMode('activity');
  if (views.dashboard || nestedViews.dashboard) addMode('dashboard');
  return out;
}

function resolveAvailableViewModes(meta: NavNode['meta'] | null | undefined, contract: ActionContractLoose | null, contractViewTypeRaw: unknown) {
  const out: string[] = [];
  const seen = new Set<string>();
  const addMode = (raw: unknown) => {
    const mode = normalizeViewMode(raw);
    if (!mode || mode === 'form' || seen.has(mode)) return;
    seen.add(mode);
    out.push(mode);
  };
  const addModes = (raw: unknown) => {
    parseViewModes(raw).forEach((mode) => addMode(mode));
  };
  addModes(contractViewTypeRaw);
  addModes((meta as { view_modes?: unknown } | null)?.view_modes);
  collectContractViewModes(contract).forEach((mode) => addMode(mode));
  return out;
}

const availableViewModes = computed(() =>
  resolveAvailableViewModes(actionMeta.value, actionContract.value, contractViewType.value),
);
const viewMode = computed(() => {
  const modes = availableViewModes.value;
  const mode = normalizeViewMode(preferredViewMode.value) || modes[0] || '';
  if (mode === 'kanban') return 'kanban';
  if (mode === 'list' || mode === 'tree') return 'tree';
  if (mode === 'pivot' || mode === 'graph' || mode === 'calendar' || mode === 'gantt' || mode === 'activity' || mode === 'dashboard') {
    return mode;
  }
  return '';
});

function viewModeLabel(mode: string) {
  if (mode === 'tree') return pageText('view_mode_tree', '列表');
  if (mode === 'kanban') return pageText('view_mode_kanban', '看板');
  if (mode === 'pivot') return pageText('view_mode_pivot', '透视');
  if (mode === 'graph') return pageText('view_mode_graph', '图表');
  if (mode === 'calendar') return pageText('view_mode_calendar', '日历');
  if (mode === 'gantt') return pageText('view_mode_gantt', '甘特');
  if (mode === 'activity') return pageText('view_mode_activity', '活动');
  if (mode === 'dashboard') return pageText('view_mode_dashboard', '仪表板');
  return mode;
}

function switchViewMode(mode: string) {
  const normalized = normalizeViewMode(mode);
  if (!normalized || normalized === viewMode.value) return;
  preferredViewMode.value = normalized;
  void load();
}
const sortLabel = computed(() => sortValue.value || 'id asc');
const effectiveSurfaceModel = computed(() => (resolvedModelRef.value || model.value || '').toLowerCase());
const surfaceKey = computed(() => `${sceneKey.value} ${effectiveSurfaceModel.value} ${pageTitle.value}`.toLowerCase());
const sceneContractV1 = computed<Record<string, unknown>>(() => {
  const raw = pageContract.contract.value?.scene_contract_v1;
  if (!raw || typeof raw !== 'object') return {};
  if (String((raw as Record<string, unknown>).contract_version || '') !== 'v1') return {};
  return raw as Record<string, unknown>;
});
function keywordList(key: string, fallbackCsv: string) {
  return String(pageText(key, fallbackCsv) || '')
    .split(',')
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
}
function includesAnyKeyword(text: string, keywords: string[]) {
  const raw = String(text || '').toLowerCase();
  if (!raw) return false;
  return keywords.some((item) => raw.includes(String(item || '').toLowerCase()));
}
const surfaceKind = computed<'risk' | 'contract' | 'cost' | 'project' | 'generic'>(() => {
  const contractKind = String(actionContract.value?.surface_policies?.kind || '').trim().toLowerCase();
  if (contractKind === 'risk' || contractKind === 'contract' || contractKind === 'cost' || contractKind === 'project') {
    return contractKind;
  }
  const extensionKind = String((sceneContractV1.value.extensions as Record<string, unknown> | undefined)?.surface_kind || '').trim().toLowerCase();
  if (extensionKind === 'risk' || extensionKind === 'contract' || extensionKind === 'cost' || extensionKind === 'project') {
    return extensionKind;
  }
  const key = surfaceKey.value;
  if (includesAnyKeyword(key, keywordList('surface_kind_keywords_risk', 'risk,风险'))) return 'risk';
  if (includesAnyKeyword(key, keywordList('surface_kind_keywords_contract', 'contract,合同'))) return 'contract';
  if (includesAnyKeyword(key, keywordList('surface_kind_keywords_cost', 'cost,成本'))) return 'cost';
  if (includesAnyKeyword(key, keywordList('surface_kind_keywords_project', 'project,项目'))) return 'project';
  return 'generic';
});
const sortOptions = computed(() => {
  if (surfaceKind.value === 'risk' || surfaceKind.value === 'cost') {
    return [
      { label: pageText('sort_option_priority_deadline', '优先级↓ / 截止日↑'), value: 'priority desc,deadline asc,write_date desc' },
      { label: pageText('sort_option_deadline_updated', '截止日↑ / 更新时间↓'), value: 'deadline asc,write_date desc' },
      { label: pageText('sort_option_updated_id', '更新时间↓ / ID↓'), value: 'write_date desc,id desc' },
    ];
  }
  return [
    { label: pageText('sort_option_updated_name_asc', '更新时间↓ / 名称↑'), value: 'write_date desc,name asc' },
    { label: pageText('sort_option_updated_asc_name_asc', '更新时间↑ / 名称↑'), value: 'write_date asc,name asc' },
    { label: pageText('sort_option_name_updated', '名称↑ / 更新时间↓'), value: 'name asc,write_date desc' },
    { label: pageText('sort_option_name_desc_updated', '名称↓ / 更新时间↓'), value: 'name desc,write_date desc' },
  ];
});
const subtitle = computed(
  () =>
    `${records.value.length}${pageText('subtitle_records_suffix', ' 条记录')} · ${pageText('subtitle_sort_prefix', '排序：')}${sortLabel.value}`,
);

function resolveProjectStateCell(row: Record<string, unknown>) {
  return semanticStatus(row.stage_id || row.state || row.status || row.kanban_state || row.health_state);
}

function resolveProjectAmount(row: Record<string, unknown>) {
  const candidates = [
    row.contract_amount,
    row.contract_income_total,
    row.dashboard_invoice_amount,
    row.amount_total,
    row.total_amount,
    row.planned_revenue,
    row.budget_total,
  ];
  for (const candidate of candidates) {
    const amount = Number(candidate);
    if (Number.isFinite(amount) && amount > 0) return amount;
  }
  return 0;
}

function isCompletedState(stateText: string, tone: string) {
  if (tone === 'success') return true;
  const text = String(stateText || '');
  return ['完成', '完工', '归档', '关闭', '交付'].some((keyword) => text.includes(keyword));
}

const ledgerOverviewItems = computed(() => {
  if (!hasLedgerOverviewStrip.value) return [] as Array<{ key: string; label: string; value: string; tone: string }>;
  const rows = records.value || [];
  let running = 0;
  let warning = 0;
  let done = 0;
  let contractAmount = 0;
  rows.forEach((row) => {
    const stage = resolveProjectStateCell(row);
    const text = String(stage.text || '');
    if (!isCompletedState(text, stage.tone)) running += 1;
    if (stage.tone === 'danger' || stage.tone === 'warning') warning += 1;
    if (isCompletedState(text, stage.tone)) done += 1;
    contractAmount += resolveProjectAmount(row);
  });
  const hasAmount = contractAmount > 0;
  return [
    { key: 'running', label: '在建项目数', value: String(running), tone: running > 0 ? 'info' : 'neutral' },
    { key: 'warning', label: '预警项目数', value: String(warning), tone: warning > 0 ? 'danger' : 'success' },
    { key: 'done', label: '已完工项目数', value: String(done), tone: 'success' },
    {
      key: 'metric',
      label: hasAmount ? '合同额汇总' : '项目群规模',
      value: hasAmount ? formatAmountCN(contractAmount) : `${rows.length} 个项目`,
      tone: 'neutral',
    },
  ];
});

const listSemanticKind = computed(() => {
  const fieldSet = new Set(columns.value.map((field) => String(field || '').toLowerCase()));
  if (fieldSet.has('quantity') && (fieldSet.has('price') || fieldSet.has('amount_total'))) return 'boq';
  if (fieldSet.has('date_deadline') && (fieldSet.has('kanban_state') || fieldSet.has('user_ids'))) return 'task';
  if (fieldSet.has('date_request') && fieldSet.has('amount') && fieldSet.has('state')) return 'risk';
  if (fieldSet.has('stage_id') && (fieldSet.has('contract_amount') || fieldSet.has('user_id'))) return 'project';
  if (pageMode.value === 'ledger') return 'project';
  return 'generic';
});

const listSummaryItems = computed(() => {
  const rows = records.value || [];
  if (listSemanticKind.value === 'task') {
    let done = 0;
    let pending = 0;
    let blocked = 0;
    rows.forEach((row) => {
      const state = semanticStatus(row.kanban_state || row.state || row.status);
      if (state.tone === 'success') done += 1;
      else if (state.tone === 'danger') blocked += 1;
      else pending += 1;
    });
    return [
      { key: 'task_total', label: '任务总数', value: String(rows.length), tone: 'info' },
      { key: 'task_pending', label: '待处理', value: String(pending), tone: pending > 0 ? 'warning' : 'success' },
      { key: 'task_blocked', label: '受阻/风险', value: String(blocked), tone: blocked > 0 ? 'danger' : 'success' },
      { key: 'task_done', label: '已完成', value: String(done), tone: 'success' },
    ];
  }
  if (listSemanticKind.value === 'risk') {
    let high = 0;
    let warning = 0;
    rows.forEach((row) => {
      const state = semanticStatus(row.state || row.status || row.level);
      if (state.tone === 'danger') high += 1;
      else if (state.tone === 'warning') warning += 1;
    });
    return [
      { key: 'risk_total', label: '风险记录数', value: String(rows.length), tone: 'info' },
      { key: 'risk_high', label: '高风险', value: String(high), tone: high > 0 ? 'danger' : 'success' },
      { key: 'risk_warning', label: '预警', value: String(warning), tone: warning > 0 ? 'warning' : 'neutral' },
    ];
  }
  if (listSemanticKind.value === 'boq') {
    let quantity = 0;
    rows.forEach((row) => {
      quantity += Number(row.quantity || 0) || 0;
    });
    return [
      { key: 'boq_total', label: '清单行数', value: String(rows.length), tone: 'info' },
      { key: 'boq_qty', label: '总工程量', value: `${Math.round(quantity * 100) / 100}`, tone: 'neutral' },
    ];
  }
  if (listSemanticKind.value === 'project') {
    const totals = projectScopeTotals.value;
    const scopeMetrics = projectScopeMetrics.value;
    let warning = 0;
    let done = 0;
    let amount = 0;
    rows.forEach((row) => {
      const state = resolveProjectStateCell(row);
      if (state.tone === 'danger' || state.tone === 'warning') warning += 1;
      if (isCompletedState(String(state.text || ''), state.tone)) done += 1;
      amount += resolveProjectAmount(row);
    });
    if (scopeMetrics) {
      warning = scopeMetrics.warning;
      done = scopeMetrics.done;
      amount = scopeMetrics.amount;
    }
    const hasAmount = amount > 0;
    return [
      { key: 'project_total', label: '项目总数', value: String(totals?.all ?? rows.length), tone: 'info' },
      { key: 'project_active', label: '在办项目', value: String(totals?.active ?? rows.length), tone: 'neutral' },
      { key: 'project_archived', label: '已归档', value: String(totals?.archived ?? 0), tone: (totals?.archived ?? 0) > 0 ? 'warning' : 'success' },
      { key: 'project_warning', label: '预警项目', value: String(warning), tone: warning > 0 ? 'danger' : 'success' },
      { key: 'project_done', label: '已完工', value: String(done), tone: 'success' },
      {
        key: 'project_amount',
        label: hasAmount ? '合同额汇总' : '项目群规模',
        value: hasAmount ? formatAmountCN(amount) : `${rows.length} 个项目`,
        tone: 'neutral',
      },
    ];
  }
  return [];
});
const kanbanTitleField = computed(() => {
  if (kanbanTitleFieldHint.value && kanbanFields.value.includes(kanbanTitleFieldHint.value)) {
    return kanbanTitleFieldHint.value;
  }
  const candidates = ['display_name', 'name'];
  const found = candidates.find((field) => kanbanFields.value.includes(field));
  return found || kanbanFields.value[0] || 'id';
});
const statusLabel = computed(() => {
  if (status.value === 'loading') return pageText('status_loading', '加载中');
  if (status.value === 'error') return pageText('status_error', '加载失败');
  if (status.value === 'empty') return pageText('status_empty', '暂无数据');
  return pageText('status_ready', '已就绪');
});
const pageStatus = computed<'loading' | 'ok' | 'empty' | 'error'>(() =>
  status.value === 'idle' ? 'loading' : status.value,
);
const recordCount = computed(() => {
  if (listTotalCount.value !== null && Number.isFinite(listTotalCount.value)) {
    return Math.max(0, Math.trunc(listTotalCount.value));
  }
  return records.value.length;
});
const advancedViewTitle = computed(() => {
  const labels: Record<string, string> = {
    pivot: pageText('advanced_title_pivot', '数据透视视图'),
    graph: pageText('advanced_title_graph', '图表视图'),
    calendar: pageText('advanced_title_calendar', '日历视图'),
    gantt: pageText('advanced_title_gantt', '甘特视图'),
    activity: pageText('advanced_title_activity', '活动视图'),
    dashboard: pageText('advanced_title_dashboard', '仪表板视图'),
  };
  return labels[viewMode.value] || pageText('advanced_title_default', '高级视图');
});
const advancedViewHint = computed(() => {
  const hints: Record<string, string> = {
    pivot: pageText('advanced_hint_pivot', '当前为可读降级视图，可查看核心统计记录并继续下钻到列表/表单。'),
    graph: pageText('advanced_hint_graph', '当前为可读降级视图，可查看核心指标记录并继续下钻到列表/表单。'),
    calendar: pageText('advanced_hint_calendar', '当前为可读降级视图，可查看时间相关记录并继续下钻到列表/表单。'),
    gantt: pageText('advanced_hint_gantt', '当前为可读降级视图，可查看进度相关记录并继续下钻到列表/表单。'),
    activity: pageText('advanced_hint_activity', '当前为可读降级视图，可查看活动记录并继续下钻到列表/表单。'),
    dashboard: pageText('advanced_hint_dashboard', '当前为可读降级视图，可查看关键记录并继续下钻到列表/表单。'),
  };
  return hints[viewMode.value] || pageText('advanced_hint_default', '当前视图使用可读降级渲染。');
});
const pageTitle = computed(() => {
  if (routeSceneLabel.value) return routeSceneLabel.value;
  const contractTitle = String(actionContract.value?.head?.title || '').trim();
  if (contractTitle) return contractTitle;
  return injectedTitle?.value || actionMeta.value?.name || pageText('page_title_fallback', '工作台');
});
const contractSurfaceIntent = computed<SurfaceIntentContract>(() => {
  const fromSurfacePolicies = actionContract.value?.surface_policies?.intent_profile;
  if (fromSurfacePolicies && typeof fromSurfacePolicies === 'object') {
    return fromSurfacePolicies;
  }
  const extensions = sceneContractV1.value.extensions;
  const fromExtensions = extensions && typeof extensions === 'object'
    ? (extensions as Record<string, unknown>).surface_intent
    : null;
  return fromExtensions && typeof fromExtensions === 'object'
    ? fromExtensions as SurfaceIntentContract
    : {};
});
const surfaceIntent = computed<SurfaceIntent>(() => {
  const override = contractSurfaceIntent.value;
  if (override && Object.keys(override).length) {
    const fallbackPrimary: FocusNavAction = {
      label: pageText('primary_action_default', '去我的工作'),
      to: '/my-work',
    };
    const primaryAction = override.primary_action && typeof override.primary_action === 'object'
      ? override.primary_action
      : fallbackPrimary;
    return {
      title: String(override.title || pageText('intent_title_default', '业务列表：先看状态，再执行动作')),
      summary: String(override.summary || pageText('intent_summary_default', '通过快速筛选与快捷操作，优先处理最关键事项。')),
      actions: Array.isArray(override.actions) ? override.actions : [],
      emptyTitle: String(override.empty_title || pageText('empty_title_default', '')),
      emptyHint: String(override.empty_hint || pageText('empty_hint_default', '')),
      primaryAction,
      secondaryAction: override.secondary_action,
    };
  }
  const key = surfaceKey.value;
  if (includesAnyKeyword(key, keywordList('surface_kind_keywords_risk', 'risk,风险'))) {
    return {
      title: pageText('intent_title_risk', '风险驾驶舱：先处理严重与逾期风险'),
      summary: pageText('intent_summary_risk', '优先完成分派、关闭或发起审批，避免风险停留在“仅可见”状态。'),
      actions: [
        { label: pageText('intent_action_risk_todo', '待我处理风险'), to: '/my-work', query: { section: 'todo', source: 'project.risk', search: '风险' } },
        { label: pageText('intent_action_risk_scene', '打开风险场景'), to: '/s/projects.dashboard' },
      ],
      emptyTitle: pageText('empty_title_risk', '当前暂无风险记录'),
      emptyHint: pageText('empty_hint_risk', '建议转到“我的工作”处理风险待办，或进入风险驾驶舱继续巡检。'),
      primaryAction: { label: pageText('primary_action_risk', '处理风险待办'), to: '/my-work', query: { section: 'todo', source: 'project.risk', search: '风险' } },
      secondaryAction: { label: pageText('secondary_action_risk', '进入风险驾驶舱'), to: '/s/projects.dashboard' },
    };
  }
  if (includesAnyKeyword(key, keywordList('surface_kind_keywords_contract', 'contract,合同'))) {
    return {
      title: pageText('intent_title_contract', '合同执行：优先识别付款与变更风险'),
      summary: pageText('intent_summary_contract', '先看执行率与付款状态，再进入异常合同处理。'),
      actions: [
        { label: pageText('intent_action_contract_todo', '处理合同待办'), to: '/my-work', query: { section: 'todo', search: '合同' } },
        { label: pageText('intent_action_contract_dashboard', '查看风险驾驶舱'), to: '/s/projects.dashboard' },
      ],
      emptyTitle: pageText('empty_title_contract', '当前暂无合同记录'),
      emptyHint: pageText('empty_hint_contract', '可前往“我的工作”查看合同待办，或进入风险驾驶舱追踪履约风险。'),
      primaryAction: { label: pageText('primary_action_contract', '处理合同待办'), to: '/my-work', query: { section: 'todo', search: '合同' } },
      secondaryAction: { label: pageText('secondary_action_contract', '查看风险驾驶舱'), to: '/s/projects.dashboard' },
    };
  }
  if (includesAnyKeyword(key, keywordList('surface_kind_keywords_cost', 'cost,成本'))) {
    return {
      title: pageText('intent_title_cost', '成本执行：先回答是否超支'),
      summary: pageText('intent_summary_cost', '优先关注超支金额与超支项，再下钻到具体偏差来源。'),
      actions: [
        { label: pageText('intent_action_cost_todo', '处理成本待办'), to: '/my-work', query: { section: 'todo', search: '成本' } },
        { label: pageText('intent_action_cost_dashboard', '查看风险驾驶舱'), to: '/s/projects.dashboard' },
      ],
      emptyTitle: pageText('empty_title_cost', '当前暂无成本记录'),
      emptyHint: pageText('empty_hint_cost', '可前往“我的工作”处理成本待办，或进入风险驾驶舱继续巡检。'),
      primaryAction: { label: pageText('primary_action_cost', '处理超支待办'), to: '/my-work', query: { section: 'todo', search: '成本' } },
      secondaryAction: { label: pageText('secondary_action_cost', '查看风险驾驶舱'), to: '/s/projects.dashboard' },
    };
  }
  if (includesAnyKeyword(key, keywordList('surface_kind_keywords_project', 'project,项目'))) {
    return {
      title: pageText('intent_title_project', '项目视角：先判断是否可控'),
      summary: pageText('intent_summary_project', '优先查看风险、审批与经营指标，再决定下一步动作。'),
      actions: [
        { label: pageText('intent_action_project_todo', '查看项目待办'), to: '/my-work', query: { section: 'todo', search: '项目' } },
        { label: pageText('intent_action_project_dashboard', '进入风险驾驶舱'), to: '/s/projects.dashboard' },
      ],
      emptyTitle: pageText('empty_title_project', '当前暂无项目记录'),
      emptyHint: pageText('empty_hint_project', '建议进入“我的工作”处理项目待办，或去风险驾驶舱查看全局状态。'),
      primaryAction: { label: pageText('primary_action_project', '查看项目待办'), to: '/my-work', query: { section: 'todo', search: '项目' } },
      secondaryAction: { label: pageText('secondary_action_project', '进入风险驾驶舱'), to: '/s/projects.dashboard' },
    };
  }
  return {
    title: pageText('intent_title_default', '业务列表：先看状态，再执行动作'),
    summary: pageText('intent_summary_default', '通过快速筛选与快捷操作，优先处理最关键事项。'),
    actions: [
      { label: pageText('intent_action_default_home', '工作台'), to: '/' },
      { label: pageText('intent_action_default_my_work', '我的工作'), to: '/my-work' },
    ],
    emptyTitle: pageText('empty_title_default', ''),
    emptyHint: pageText('empty_hint_default', ''),
    primaryAction: { label: pageText('primary_action_default', '去我的工作'), to: '/my-work' },
    secondaryAction: { label: pageText('secondary_action_default', '去风险驾驶舱'), to: '/s/projects.dashboard' },
  };
});
const emptyReasonText = computed(() => {
  if (searchTerm.value.trim() || activeContractFilterKey.value) {
    return pageText('empty_reason_filter', '可能由当前筛选条件导致无数据，建议先清除筛选后重试。');
  }
  const fromSurfacePolicy = String(actionContract.value?.surface_policies?.empty_reason || '').trim();
  if (fromSurfacePolicy) return fromSurfacePolicy;
  const fromExtensions = String((sceneContractV1.value.extensions as Record<string, unknown> | undefined)?.empty_reason || '').trim();
  if (fromExtensions) return fromExtensions;
  return pageText('empty_reason_default', '');
});
const showHud = computed(() => isHudEnabled(route));
const errorMessage = computed(() => (error.value?.code ? `code=${error.value.code} · ${error.value.message}` : error.value?.message || ''));
const hudEntries = computed(() => [
  { label: 'action_id', value: actionId.value || '-' },
  { label: 'menu_id', value: menuId.value || '-' },
  { label: 'scene_key', value: sceneKey.value || '-' },
  { label: 'model', value: model.value || '-' },
  { label: 'view_mode', value: viewMode.value || '-' },
  { label: 'contract_view_type', value: contractViewType.value || '-' },
  { label: 'contract_filter', value: activeContractFilterKey.value || '-' },
  { label: 'saved_filter', value: activeSavedFilterKey.value || '-' },
  { label: 'group_by', value: activeGroupByField.value || '-' },
  { label: 'group_offset', value: groupWindowOffset.value || 0 },
  { label: 'group_window_id', value: groupWindowId.value || '-' },
  { label: 'group_query_fp', value: groupQueryFingerprint.value || '-' },
  { label: 'group_window_digest', value: groupWindowDigest.value || '-' },
  { label: 'group_window_identity_key', value: groupWindowIdentityKey.value || '-' },
  { label: 'route_group_fp', value: String(route.query.group_fp || '').trim() || '-' },
  { label: 'route_group_wid', value: String(route.query.group_wid || '').trim() || '-' },
  { label: 'route_group_wdg', value: String(route.query.group_wdg || '').trim() || '-' },
  { label: 'route_group_wik', value: String(route.query.group_wik || '').trim() || '-' },
  { label: 'contract_actions', value: contractActionButtons.value.length },
  { label: 'contract_limit', value: contractLimit.value },
  { label: 'contract_read', value: contractReadAllowed.value },
  { label: 'contract_warnings', value: contractWarningCount.value },
  { label: 'contract_degraded', value: contractDegraded.value },
  { label: 'order', value: sortLabel.value || '-' },
  { label: 'last_intent', value: lastIntent.value || '-' },
  { label: 'write_mode', value: lastWriteMode.value || '-' },
  { label: 'trace_id', value: traceId.value || lastTraceId.value || '-' },
  { label: 'latency_ms', value: lastLatencyMs.value ?? '-' },
  { label: 'route', value: route.fullPath },
]);
const userSurfaceNoiseMarkers = ['demo', 'showcase', 'smoke', 'internal', 'ir_cron', 'project_update_all_action'];
function hasNoiseMarker(...values: unknown[]): boolean {
  const merged = values
    .map((value) => String(value || '').trim().toLowerCase())
    .filter(Boolean)
    .join(' ');
  if (!merged) return false;
  return userSurfaceNoiseMarkers.some((token) => merged.includes(token));
}
function isNumericToken(value: unknown): boolean {
  const text = String(value || '').trim();
  return text.length > 0 && /^\d+$/.test(text);
}
const contractFilterChips = computed<ContractFilterChip[]>(() => {
  const rows = sceneReadyListSurface.value.filters?.length
    ? sceneReadyListSurface.value.filters
    : actionContract.value?.search?.filters;
  if (!Array.isArray(rows)) return [];
  return rows
    .map((row) => {
      const key = String(row?.key || '').trim();
      const label = String(row?.label || row?.key || '').trim();
      if (!key || !label) return null;
      if (isNumericToken(key) || isNumericToken(label)) return null;
      if (hasNoiseMarker(key, label, row?.domain_raw, row?.context_raw)) return null;
      const domain = Array.isArray(row?.domain) ? row.domain : [];
      const domainRaw = String(row?.domain_raw || '').trim();
      const contextRaw = String(row?.context_raw || '').trim();
      const context = parseContractContextRaw(row?.context_raw);
      return { key, label, domain, domainRaw, context, contextRaw };
    })
    .filter((item): item is ContractFilterChip => Boolean(item))
    .slice(0, 8);
});
const filterPrimaryBudget = computed(() => {
  const raw = Number(actionContract.value?.surface_policies?.filters_primary_max ?? 5);
  if (!Number.isFinite(raw) || raw < 0) return 5;
  return Math.floor(raw);
});
const contractPrimaryFilterChips = computed<ContractFilterChip[]>(() =>
  contractFilterChips.value.slice(0, filterPrimaryBudget.value),
);
const contractOverflowFilterChips = computed<ContractFilterChip[]>(() =>
  contractFilterChips.value.slice(filterPrimaryBudget.value),
);
const contractSavedFilterChips = computed<ContractSavedFilterChip[]>(() => {
  const rows = actionContract.value?.search?.saved_filters;
  if (!Array.isArray(rows)) return [];
  return rows
    .map((row, idx) => {
      const raw = row as Record<string, unknown>;
      const key = String(raw.key || raw.name || raw.xmlid || raw.xml_id || `saved_${idx + 1}`).trim();
      const label = String(raw.label || raw.name || key).trim();
      if (!key || !label) return null;
      if (isNumericToken(key) || isNumericToken(label)) return null;
      if (hasNoiseMarker(key, label, raw.domain_raw, raw.context_raw)) return null;
      const domain = Array.isArray(raw.domain) ? raw.domain : [];
      const domainRaw = String(raw.domain_raw || '').trim();
      const contextRaw = String(raw.context_raw || '').trim();
      const context = parseContractContextRaw(raw.context_raw);
      const isDefault = raw.default === true || raw.is_default === true;
      return { key, label, domain, domainRaw, context, contextRaw, isDefault };
    })
    .filter((item): item is ContractSavedFilterChip => Boolean(item))
    .slice(0, 12);
});
const savedFilterPrimaryChips = computed<ContractSavedFilterChip[]>(() =>
  contractSavedFilterChips.value.slice(0, filterPrimaryBudget.value),
);
const savedFilterOverflowChips = computed<ContractSavedFilterChip[]>(() =>
  contractSavedFilterChips.value.slice(filterPrimaryBudget.value),
);
const contractGroupByChips = computed<ContractGroupByChip[]>(() => {
  const rows = sceneReadyListSurface.value.groupBy?.length
    ? sceneReadyListSurface.value.groupBy
    : actionContract.value?.search?.group_by;
  if (!Array.isArray(rows)) return [];
  return rows
    .map((row) => {
      const raw = row as Record<string, unknown>;
      const field = String(raw.field || '').trim();
      const label = String(raw.label || field).trim();
      if (!field || !label) return null;
      if (isNumericToken(field) || isNumericToken(label)) return null;
      const contextRaw = String(raw.context_raw || '').trim();
      const context = parseContractContextRaw(contextRaw);
      const isDefault = raw.default === true || raw.is_default === true;
      return { field, label, context, contextRaw, isDefault };
    })
    .filter((item): item is ContractGroupByChip => Boolean(item))
    .slice(0, 12);
});
const groupByPrimaryChips = computed<ContractGroupByChip[]>(() =>
  contractGroupByChips.value.slice(0, filterPrimaryBudget.value),
);
const groupByOverflowChips = computed<ContractGroupByChip[]>(() =>
  contractGroupByChips.value.slice(filterPrimaryBudget.value),
);
const activeGroupByLabel = computed(() => {
  const field = activeGroupByField.value;
  if (!field) return '';
  const found = contractGroupByChips.value.find((chip) => chip.field === field);
  return found?.label || field;
});
function toContractActionButton(
  row: Record<string, unknown>,
  dedup: Set<string>,
): ContractActionButton | null {
  const key = String(row.key || '').trim();
  if (!key || dedup.has(key)) return null;
  const rawLabel = String(row.label || key).trim();
  if (!rawLabel || isNumericToken(key) || isNumericToken(rawLabel)) return null;
  if (hasNoiseMarker(key, rawLabel, row.name, row.xml_id)) return null;
  dedup.add(key);

  const protocol = normalizeSceneActionProtocol(row);
  const targetPayload = parseContractContextRaw(row.target);
  const legacyPayload = parseContractContextRaw(row.payload);
  const payload = Object.keys(targetPayload).length ? targetPayload : legacyPayload;

  const explicitKind = normalizeActionKind(row.kind);
  const hasOpenTarget = Boolean(
    toPositiveInt(payload.action_id)
    || toPositiveInt(payload.ref)
    || String(payload.url || payload.route || '').trim(),
  );
  const kind = protocol?.mutation
    ? 'mutation'
    : hasOpenTarget
      ? 'open'
      : explicitKind;
  const actionId = toPositiveInt(payload.action_id) ?? toPositiveInt(payload.ref);
  const methodName = detectObjectMethodFromActionKey(key, String(payload.method || '').trim());
  const selectionRaw = String(row.selection || 'none').toLowerCase();
  const selection: ContractActionSelection =
    selectionRaw === 'single' || selectionRaw === 'multi' ? selectionRaw : 'none';
  const groups = Array.isArray(row.groups_xmlids) ? (row.groups_xmlids as string[]) : [];
  const userGroups = session.user?.groups_xmlids || [];
  const allowedByGroup = !groups.length || groups.some((group) => userGroups.includes(group));
  const selectedCount = selectedIds.value.length;
  const enabledBySelection =
    selection === 'none' ? true : selection === 'single' ? selectedCount === 1 : selectedCount > 0;
  const enabled = allowedByGroup && enabledBySelection;
  const hint = allowedByGroup
    ? enabledBySelection
      ? ''
      : selection === 'single'
        ? pageText('hint_select_single_record', '请选择 1 条记录')
        : pageText('hint_select_record_first', '请先选择记录')
    : pageText('hint_permission_denied', '权限不足');
  return {
    key,
    label: rawLabel,
    kind,
    actionId,
    methodName,
    model: String(row.target_model || row.model || protocol?.mutation?.model || resolvedModelRef.value || model.value || '').trim(),
    target: String(payload.target || '').trim(),
    url: String(payload.url || payload.route || '').trim(),
    selection,
    context: parseContractContextRaw(payload.context_raw),
    domainRaw: String(payload.domain_raw || '').trim(),
    enabled,
    hint,
    mutation: protocol?.mutation,
    refreshPolicy: protocol?.refresh_policy,
  };
}
const contractActionButtons = computed<ContractActionButton[]>(() => {
  const contract = actionContract.value;
  const merged: Array<Record<string, unknown>> = [];
  const sceneActions = sceneReadyListSurface.value.actions;
  if (sceneActions.length) {
    merged.push(...sceneActions);
  } else {
    if (!contract) return [];
    const contractButtons = Array.isArray(contract.buttons) ? (contract.buttons as Array<Record<string, unknown>>) : [];
    if (contractButtons.length) {
      merged.push(...contractButtons);
    } else {
      if (Array.isArray(contract.toolbar?.header)) merged.push(...(contract.toolbar?.header as Array<Record<string, unknown>>));
      if (Array.isArray(contract.toolbar?.sidebar)) merged.push(...(contract.toolbar?.sidebar as Array<Record<string, unknown>>));
      if (Array.isArray(contract.toolbar?.footer)) merged.push(...(contract.toolbar?.footer as Array<Record<string, unknown>>));
    }
  }
  const dedup = new Set<string>();
  return merged
    .map((row) => toContractActionButton(row, dedup))
    .filter((item): item is ContractActionButton => Boolean(item))
    .slice(0, 8);
});
const actionPrimaryBudget = computed(() => {
  const raw = Number(actionContract.value?.surface_policies?.actions_primary_max ?? 4);
  if (!Number.isFinite(raw) || raw < 0) return 4;
  return Math.floor(raw);
});
const contractActionGroups = computed<Array<{ key: string; label: string; actions: ContractActionButton[] }>>(() => {
  const contract = actionContract.value;
  const all = contractActionButtons.value;
  if (!all.length) return [];
  const map = new Map(all.map((item) => [item.key, item]));
  const groupsRaw = Array.isArray(contract?.action_groups) ? (contract?.action_groups as ContractActionGroupRaw[]) : [];
  const grouped: Array<{ key: string; label: string; actions: ContractActionButton[] }> = [];
  const used = new Set<string>();
  for (const row of groupsRaw) {
    const groupKey = String(row?.key || '').trim();
    if (!groupKey) continue;
    const rows = Array.isArray(row?.actions) ? row.actions : [];
    const actions: ContractActionButton[] = [];
    for (const item of rows) {
      const key = String(item?.key || '').trim();
      if (!key || used.has(key)) continue;
      const resolved = map.get(key);
      if (!resolved) continue;
      used.add(key);
      actions.push(resolved);
    }
    if (actions.length) {
      grouped.push({ key: groupKey, label: String(row?.label || groupKey), actions });
    }
  }
  if (!grouped.length) {
    const basicKeywords = keywordList('group_keywords_basic', '创建,保存,submit,create,save');
    const workflowKeywords = keywordList('group_keywords_workflow', '阶段,审批,workflow,transition');
    const drilldownKeywords = keywordList('group_keywords_drilldown', '查看,列表,看板,open,view');
    const basic = all.filter((item) => includesAnyKeyword(item.label, basicKeywords));
    const workflow = all.filter((item) => includesAnyKeyword(item.label, workflowKeywords));
    const drilldown = all.filter((item) => includesAnyKeyword(item.label, drilldownKeywords));
    const other = all.filter((item) => !basic.includes(item) && !workflow.includes(item) && !drilldown.includes(item));
    if (basic.length) grouped.push({ key: 'basic', label: pageText('group_label_basic', '基础操作'), actions: basic });
    if (workflow.length) grouped.push({ key: 'workflow', label: pageText('group_label_workflow', '流程推进'), actions: workflow });
    if (drilldown.length) grouped.push({ key: 'drilldown', label: pageText('group_label_drilldown', '业务查看'), actions: drilldown });
    if (other.length) grouped.push({ key: 'other', label: pageText('group_label_other', '更多操作'), actions: other });
  }
  return grouped;
});
const contractPrimaryActions = computed<ContractActionButton[]>(() => {
  const groups = contractActionGroups.value;
  if (!groups.length) return contractActionButtons.value.slice(0, actionPrimaryBudget.value);
  const primaryGroupOrder = ['basic', 'workflow', 'drilldown'];
  const merged: ContractActionButton[] = [];
  for (const key of primaryGroupOrder) {
    const group = groups.find((item) => item.key === key);
    if (!group) continue;
    for (const action of group.actions) {
      if (merged.some((item) => item.key === action.key)) continue;
      merged.push(action);
      if (merged.length >= actionPrimaryBudget.value) return merged;
    }
  }
  return merged.slice(0, actionPrimaryBudget.value);
});
const contractOverflowActions = computed<ContractActionButton[]>(() => {
  const primaryKeys = new Set(contractPrimaryActions.value.map((item) => item.key));
  return contractActionButtons.value.filter((item) => !primaryKeys.has(item.key));
});
const contractOverflowActionGroups = computed<Array<{ key: string; label: string; actions: ContractActionButton[] }>>(() => {
  const primaryKeys = new Set(contractPrimaryActions.value.map((item) => item.key));
  const groups = contractActionGroups.value;
  const out: Array<{ key: string; label: string; actions: ContractActionButton[] }> = [];
  for (const group of groups) {
    const actions = group.actions.filter((item) => !primaryKeys.has(item.key));
    if (!actions.length) continue;
    out.push({ key: group.key, label: group.label, actions });
  }
  return out;
});
const contractColumnLabels = computed<Record<string, string>>(() => {
  const rows = actionContract.value?.fields || {};
  return Object.entries(rows).reduce<Record<string, string>>((acc, [name, descriptor]) => {
    const label = String(descriptor?.string || '').trim();
    if (label) acc[name] = label;
    return acc;
  }, {});
});

function resolveWorkspaceContextQuery() {
  return readWorkspaceContext(route.query as Record<string, unknown>);
}

function resolveCarryQuery(extra?: Record<string, unknown>) {
  return {
    ...pickContractNavQuery(route.query as Record<string, unknown>, extra),
    ...resolveWorkspaceContextQuery(),
  };
}

function resolveWorkbenchQuery(
  reason: string,
  payload?: { public?: Record<string, unknown>; diag?: Record<string, unknown> },
) {
  return {
    reason,
    ...resolveWorkspaceContextQuery(),
    ...(payload?.public || {}),
    ...(showHud.value
      ? {
          menu_id: menuId.value || undefined,
          action_id: actionId.value || undefined,
          ...(payload?.diag || {}),
        }
      : {}),
  };
}

function resolveActionViewType(meta: unknown, contract: unknown) {
  const typedContract = contract as ActionContractLoose;
  const nestedContract = (typedContract.ui_contract_raw || typedContract.ui_contract || {}) as ActionContractLoose;
  const fromHead = String(typedContract.head?.view_type || nestedContract.head?.view_type || '').trim();
  if (fromHead) return fromHead;
  const fromContract = String(typedContract.view_type || nestedContract.view_type || '').trim();
  if (fromContract) return fromContract;
  const metaViewModes = (meta as { view_modes?: unknown } | null)?.view_modes;
  if (Array.isArray(metaViewModes) && metaViewModes.length) {
    const normalized = metaViewModes
      .map((item) => String(item || '').trim())
      .filter(Boolean)
      .join(',');
    if (normalized) return normalized;
  }
  return '';
}

function parseNumericId(raw: unknown): number | null {
  if (typeof raw === 'number' && Number.isFinite(raw) && raw > 0) return raw;
  if (typeof raw === 'string' && raw.trim()) {
    const parsed = Number(raw.trim());
    if (Number.isFinite(parsed) && parsed > 0) return parsed;
  }
  return null;
}

function extractActionResId(contract: unknown, routeQuery: Record<string, unknown>): number | null {
  const typed = contract as ActionContractLoose;
  const routeResId = parseNumericId(routeQuery.res_id);
  if (routeResId) return routeResId;
  const headResId = parseNumericId(typed.head?.res_id);
  if (headResId) return headResId;
  const headContext = typed.head?.context;
  if (headContext && typeof headContext === 'object' && !Array.isArray(headContext)) {
    const ctx = headContext as Record<string, unknown>;
    const activeId = parseNumericId(ctx.active_id);
    if (activeId) return activeId;
    const defaultResId = parseNumericId(ctx.default_res_id);
    if (defaultResId) return defaultResId;
  }
  return null;
}

function applyRoutePreset() {
  const preset = String(route.query.preset || '').trim();
  const presetFilter = String(route.query.preset_filter || '').trim();
  const savedFilter = String(route.query.saved_filter || '').trim();
  const groupBy = String(route.query.group_by || '').trim();
  const groupValue = String(route.query.group_value || '').trim();
  const groupSampleLimitRaw = Number(route.query.group_sample_limit || 0);
  const groupSortRaw = String(route.query.group_sort || '').trim().toLowerCase();
  const groupCollapsedRaw = String(route.query.group_collapsed || '').trim();
  const groupPageRaw = String(route.query.group_page || '').trim();
  const groupOffsetRaw = Number(route.query.group_offset || 0);
  const groupFingerprintRaw = String(route.query.group_fp || '').trim();
  const groupWindowIdRaw = String(route.query.group_wid || '').trim();
  const groupWindowDigestRaw = String(route.query.group_wdg || '').trim();
  const groupWindowIdentityKeyRaw = String(route.query.group_wik || '').trim();
  const routeSearch = String(route.query.search || '').trim();
  const routeOrder = String(route.query.order || route.query.sort || '').trim();
  const routeActiveFilter = String(route.query.active_filter || '').trim();
  const ctxSource = String(route.query.ctx_source || '').trim();
  routeContextSource.value = ctxSource;
  let changed = false;
  const setIfDiff = <T>(target: { value: T }, next: T) => {
    if (target.value === next) return;
    target.value = next;
    changed = true;
  };

  appliedPresetLabel.value = '';
  if (routeSearch) {
    setIfDiff(searchTerm, routeSearch);
  } else {
    setIfDiff(searchTerm, '');
  }
  if (routeOrder) {
    setIfDiff(sortValue, routeOrder);
  }
  if (routeActiveFilter === 'all' || routeActiveFilter === 'active' || routeActiveFilter === 'archived') {
    setIfDiff(filterValue, routeActiveFilter);
  }
  if (!preset && presetFilter) {
    appliedPresetLabel.value = `${pageText('preset_label_contract_filter_prefix', '契约筛选: ')}${presetFilter}`;
    setIfDiff(searchTerm, routeSearch || presetFilter);
  }
  if (savedFilter) {
    appliedPresetLabel.value = appliedPresetLabel.value || `${pageText('preset_label_saved_filter_prefix', '保存筛选: ')}${savedFilter}`;
    setIfDiff(activeSavedFilterKey, savedFilter);
  } else {
    setIfDiff(activeSavedFilterKey, '');
  }
  if (groupBy) {
    setIfDiff(activeGroupByField, groupBy);
  } else {
    setIfDiff(activeGroupByField, '');
    setIfDiff(groupWindowOffset, 0);
  }
  if (groupBy) {
    const normalizedGroupOffset = Number.isFinite(groupOffsetRaw) && groupOffsetRaw > 0 ? Math.trunc(groupOffsetRaw) : 0;
    setIfDiff(groupWindowOffset, normalizedGroupOffset);
    setIfDiff(groupQueryFingerprint, groupFingerprintRaw);
    setIfDiff(groupWindowId, groupWindowIdRaw);
    setIfDiff(groupWindowDigest, groupWindowDigestRaw);
    setIfDiff(groupWindowIdentityKey, groupWindowIdentityKeyRaw);
  } else {
    setIfDiff(groupQueryFingerprint, '');
    setIfDiff(groupWindowId, '');
    setIfDiff(groupWindowDigest, '');
    setIfDiff(groupWindowIdentityKey, '');
  }
  if (groupValue && !routeSearch) {
    setIfDiff(searchTerm, groupValue);
  } else if (!groupValue) {
    activeGroupSummaryKey.value = '';
    activeGroupSummaryDomain.value = [];
  }
  if (Number.isFinite(groupSampleLimitRaw) && [3, 5, 8].includes(groupSampleLimitRaw)) {
    setIfDiff(groupSampleLimit, groupSampleLimitRaw);
  } else {
    setIfDiff(groupSampleLimit, 3);
  }
  if (groupSortRaw === 'asc' || groupSortRaw === 'desc') {
    setIfDiff(groupSort, groupSortRaw as 'asc' | 'desc');
  } else {
    setIfDiff(groupSort, 'desc');
  }
  const collapsedList = groupCollapsedRaw
    ? groupCollapsedRaw.split(',').map((item) => item.trim()).filter(Boolean)
    : [];
  setIfDiff(collapsedGroupKeys, collapsedList);
  const parsedGroupPages = parseGroupPageOffsets(groupPageRaw);
  const currentGroupPages = groupPageOffsets.value;
  const sameGroupPageState =
    Object.keys(parsedGroupPages).length === Object.keys(currentGroupPages).length
    && Object.entries(parsedGroupPages).every(([key, value]) => currentGroupPages[key] === value);
  if (!sameGroupPageState) {
    groupPageOffsets.value = parsedGroupPages;
    changed = true;
  }
  if (preset && preset !== lastTrackedPreset.value) {
    lastTrackedPreset.value = preset;
    void trackUsageEvent('workspace.preset.apply', { preset, view: 'action' }).catch(() => {});
  }
  if (!preset && !presetFilter && !savedFilter && !groupBy) {
    lastTrackedPreset.value = '';
  }
  return changed;
}

function clearRoutePreset() {
  appliedPresetLabel.value = '';
  routeContextSource.value = '';
  const nextQuery = stripWorkspaceContext(route.query as Record<string, unknown>);
  void trackUsageEvent('workspace.preset.clear', { view: 'action' }).catch(() => {});
  replaceCurrentRouteQuery(nextQuery);
}

function syncRouteListState(extra?: Record<string, unknown>) {
  const collapsed = collapsedGroupKeys.value.filter(Boolean).join(',');
  const groupPage = serializeGroupPageOffsets(groupPageOffsets.value);
  const query = pickContractNavQuery(route.query as Record<string, unknown>, {
    search: searchTerm.value.trim() || undefined,
    order: sortValue.value.trim() || undefined,
    active_filter: filterValue.value !== 'all' ? filterValue.value : undefined,
    group_sample_limit: groupSampleLimit.value !== 3 ? groupSampleLimit.value : undefined,
    group_sort: groupSort.value !== 'desc' ? groupSort.value : undefined,
    group_collapsed: collapsed || undefined,
    group_page: groupPage || undefined,
    group_offset: activeGroupByField.value && groupWindowOffset.value > 0 ? groupWindowOffset.value : undefined,
    group_fp: activeGroupByField.value && groupQueryFingerprint.value ? groupQueryFingerprint.value : undefined,
    group_wid: activeGroupByField.value && groupWindowId.value ? groupWindowId.value : undefined,
    group_wdg: activeGroupByField.value && groupWindowDigest.value ? groupWindowDigest.value : undefined,
    group_wik: activeGroupByField.value && groupWindowIdentityKey.value ? groupWindowIdentityKey.value : undefined,
    ...extra,
  });
  replaceCurrentRouteQuery(query);
}

function parseGroupPageOffsets(raw: string) {
  const out: Record<string, number> = {};
  if (!raw) return out;
  raw.split(';').forEach((pair) => {
    const [rawKey, rawOffset] = pair.split(':');
    const key = decodeURIComponent(String(rawKey || '').trim());
    const offset = Number(rawOffset || 0);
    if (!key) return;
    if (!Number.isFinite(offset) || offset < 0) return;
    out[key] = Math.trunc(offset);
  });
  return out;
}

function serializeGroupPageOffsets(state: Record<string, number>) {
  return Object.entries(state || {})
    .filter(([key, offset]) => key && Number.isFinite(offset) && offset >= 0)
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([key, offset]) => `${encodeURIComponent(key)}:${Math.trunc(offset)}`)
    .join(';');
}

function applyContractFilter(key: string) {
  if (!key) return;
  activeContractFilterKey.value = key;
  showMoreContractFilters.value = false;
  clearSelection();
  const query = pickContractNavQuery(route.query as Record<string, unknown>, { preset_filter: key });
  replaceCurrentRouteQuery(query);
  void load();
}

function applySavedFilter(key: string) {
  if (!key) return;
  activeSavedFilterKey.value = key;
  showMoreSavedFilters.value = false;
  clearSelection();
  const query = pickContractNavQuery(route.query as Record<string, unknown>, { saved_filter: key });
  replaceCurrentRouteQuery(query);
  void load();
}

function clearContractFilter() {
  activeContractFilterKey.value = '';
  showMoreContractFilters.value = false;
  clearSelection();
  const query = pickContractNavQuery(route.query as Record<string, unknown>, { preset_filter: undefined });
  replaceCurrentRouteQuery(query);
  void load();
}

function clearSavedFilter() {
  activeSavedFilterKey.value = '';
  showMoreSavedFilters.value = false;
  clearSelection();
  const query = pickContractNavQuery(route.query as Record<string, unknown>, { saved_filter: undefined });
  replaceCurrentRouteQuery(query);
  void load();
}

function applyGroupBy(field: string) {
  if (!field) return;
  activeGroupByField.value = field;
  activeGroupSummaryKey.value = '';
  activeGroupSummaryDomain.value = [];
  groupWindowOffset.value = 0;
  groupWindowPrevOffset.value = null;
  groupWindowNextOffset.value = null;
  groupWindowCount.value = 0;
  groupWindowTotal.value = null;
  groupWindowStart.value = null;
  groupWindowEnd.value = null;
  groupWindowId.value = '';
  groupQueryFingerprint.value = '';
  groupWindowDigest.value = '';
  groupWindowIdentityKey.value = '';
  groupPageOffsets.value = {};
  showMoreGroupBy.value = false;
  clearSelection();
  const query = pickContractNavQuery(route.query as Record<string, unknown>, {
    group_by: field,
    group_value: undefined,
    group_page: undefined,
    group_offset: undefined,
    group_fp: undefined,
    group_wid: undefined,
    group_wdg: undefined,
    group_wik: undefined,
  });
  replaceCurrentRouteQuery(query);
  void load();
}

function clearGroupBy() {
  activeGroupByField.value = '';
  activeGroupSummaryKey.value = '';
  activeGroupSummaryDomain.value = [];
  groupWindowOffset.value = 0;
  groupWindowPrevOffset.value = null;
  groupWindowNextOffset.value = null;
  groupWindowCount.value = 0;
  groupWindowTotal.value = null;
  groupWindowStart.value = null;
  groupWindowEnd.value = null;
  groupWindowId.value = '';
  groupQueryFingerprint.value = '';
  groupWindowDigest.value = '';
  groupWindowIdentityKey.value = '';
  groupPageOffsets.value = {};
  showMoreGroupBy.value = false;
  clearSelection();
  const query = pickContractNavQuery(route.query as Record<string, unknown>, {
    group_by: undefined,
    group_value: undefined,
    group_page: undefined,
    group_offset: undefined,
    group_fp: undefined,
    group_wid: undefined,
    group_wdg: undefined,
    group_wik: undefined,
  });
  replaceCurrentRouteQuery(query);
  void load();
}

function handleGroupSummaryPick(item: GroupSummaryItem) {
  if (!item) return;
  activeGroupSummaryKey.value = item.key;
  activeGroupSummaryDomain.value = Array.isArray(item.domain) ? item.domain : [];
  groupWindowOffset.value = 0;
  searchTerm.value = item.label || '';
  syncRouteListState({
    search: searchTerm.value.trim() || undefined,
    group_value: item.label || undefined,
    group_offset: undefined,
    group_fp: undefined,
    group_wid: undefined,
    group_wdg: undefined,
    group_wik: undefined,
  });
  void load();
}

function handleOpenGroupedRows(group: { key: string; label: string; count: number; domain?: unknown[] }) {
  activeGroupSummaryKey.value = group.key;
  activeGroupSummaryDomain.value = Array.isArray(group.domain) ? group.domain : [];
  groupWindowOffset.value = 0;
  searchTerm.value = '';
  syncRouteListState({
    search: undefined,
    group_value: group.label || undefined,
    group_offset: undefined,
    group_fp: undefined,
    group_wid: undefined,
    group_wdg: undefined,
    group_wik: undefined,
  });
  void load();
}

function clearGroupSummaryDrilldown() {
  activeGroupSummaryKey.value = '';
  activeGroupSummaryDomain.value = [];
  groupWindowOffset.value = 0;
  const q = pickContractNavQuery(route.query as Record<string, unknown>, {
    group_value: undefined,
    group_offset: undefined,
    group_fp: undefined,
    group_wid: undefined,
    group_wdg: undefined,
    group_wik: undefined,
  });
  replaceCurrentRouteQuery(q);
  void load();
}

function handleGroupWindowPrev() {
  if (groupWindowPrevOffset.value === null) return;
  groupWindowOffset.value = Math.max(0, Math.trunc(groupWindowPrevOffset.value));
  groupWindowId.value = '';
  groupWindowDigest.value = '';
  groupWindowIdentityKey.value = '';
  collapsedGroupKeys.value = [];
  groupPageOffsets.value = {};
  syncRouteListState({ group_offset: groupWindowOffset.value || undefined, group_collapsed: undefined, group_page: undefined, group_wid: undefined, group_wdg: undefined, group_wik: undefined });
  void load();
}

function handleGroupWindowNext() {
  if (groupWindowNextOffset.value === null) return;
  groupWindowOffset.value = Math.max(0, Math.trunc(groupWindowNextOffset.value));
  groupWindowId.value = '';
  groupWindowDigest.value = '';
  groupWindowIdentityKey.value = '';
  collapsedGroupKeys.value = [];
  groupPageOffsets.value = {};
  syncRouteListState({ group_offset: groupWindowOffset.value || undefined, group_collapsed: undefined, group_page: undefined, group_wid: undefined, group_wdg: undefined, group_wik: undefined });
  void load();
}

function handleGroupSampleLimitChange(limit: number) {
  const normalized = Number(limit || 0);
  if (!Number.isFinite(normalized) || ![3, 5, 8].includes(normalized)) return;
  groupSampleLimit.value = normalized;
  groupWindowOffset.value = 0;
  groupPageOffsets.value = {};
  syncRouteListState({ group_sample_limit: normalized, group_offset: undefined, group_fp: undefined, group_wid: undefined, group_wdg: undefined, group_wik: undefined });
  void load();
}

function handleGroupSortChange(next: 'asc' | 'desc') {
  groupSort.value = next === 'asc' ? 'asc' : 'desc';
  syncRouteListState({ group_sort: groupSort.value !== 'desc' ? groupSort.value : undefined });
}

function handleGroupCollapsedChange(keys: string[]) {
  collapsedGroupKeys.value = Array.isArray(keys) ? keys.filter(Boolean) : [];
  syncRouteListState({
    group_collapsed: collapsedGroupKeys.value.length ? collapsedGroupKeys.value.join(',') : undefined,
  });
}

function resolveGroupedPageFields() {
  const requested = resolveRequestedFields(columns.value, listProfile.value);
  const base = requested.length ? requested : columns.value;
  const dedup = Array.from(new Set((base.length ? base : ['id', 'name']).map((item) => String(item || '').trim()).filter(Boolean)));
  if (!dedup.includes('id')) dedup.unshift('id');
  return dedup;
}

function normalizeGroupPageOffset(offset: number, pageLimit: number, totalCount: number) {
  const limit = Number.isFinite(pageLimit) && pageLimit > 0 ? Math.trunc(pageLimit) : 1;
  const maxOffset = Math.max(0, Math.trunc(totalCount) - limit);
  const clamped = Number.isFinite(offset) ? Math.min(Math.max(Math.trunc(offset), 0), maxOffset) : 0;
  return Math.floor(clamped / limit) * limit;
}

async function handleGroupedRowsPageChange(group: {
  key: string;
  label: string;
  count: number;
  domain?: unknown[];
  offset: number;
  limit: number;
}) {
  if (!group?.key) return;
  const found = groupedRows.value.find((item) => item.key === group.key);
  if (!found) return;
  const pageLimitRaw = Number(group.limit || found.pageLimit || groupSampleLimit.value || 3);
  const pageLimit = Number.isFinite(pageLimitRaw) && pageLimitRaw > 0 ? Math.min(Math.trunc(pageLimitRaw), 50) : 3;
  const nextOffset = normalizeGroupPageOffset(Number(group.offset || 0), pageLimit, Number(found.count || 0));
  if (nextOffset === found.pageOffset && found.sampleRows.length > 0) return;
  const targetModel = resolvedModelRef.value || model.value;
  if (!targetModel) return;
  groupedRows.value = groupedRows.value.map((item) => (item.key === group.key ? { ...item, loading: true } : item));
  try {
    const result = await listRecordsRaw({
      model: targetModel,
      fields: resolveGroupedPageFields(),
      domain: Array.isArray(group.domain) ? group.domain : [],
      context: mergeContext(actionMeta.value?.context, resolveEffectiveRequestContext()),
      context_raw: resolveEffectiveRequestContextRaw(),
      limit: pageLimit,
      offset: nextOffset,
      order: sortLabel.value,
    });
    const rows = Array.isArray(result.data?.records) ? (result.data.records as Array<Record<string, unknown>>) : [];
    const nextCurrent = Math.floor(nextOffset / pageLimit) + 1;
    const nextTotal = Math.max(1, Math.ceil(Number(found.count || 0) / pageLimit));
    const nextRangeStart = Number(found.count || 0) > 0 ? nextOffset + 1 : 0;
    const nextRangeEnd = Number(found.count || 0) > 0 ? Math.min(Number(found.count || 0), nextOffset + pageLimit) : 0;
    groupedRows.value = groupedRows.value.map((item) =>
      item.key === group.key
        ? {
          ...item,
          sampleRows: rows,
          pageOffset: nextOffset,
          pageLimit,
          pageCurrent: nextCurrent,
          pageTotal: nextTotal,
          pageRangeStart: nextRangeStart,
          pageRangeEnd: nextRangeEnd,
          pageWindow: { start: nextRangeStart, end: nextRangeEnd },
          pageHasPrev: nextOffset > 0,
          pageHasNext: nextOffset + pageLimit < Number(found.count || 0),
          pageSyncedFromServer: true,
          loading: false,
        }
        : item,
    );
    groupPageOffsets.value = { ...groupPageOffsets.value, [group.key]: nextOffset };
    syncRouteListState({ group_page: serializeGroupPageOffsets(groupPageOffsets.value) || undefined });
  } catch {
    groupedRows.value = groupedRows.value.map((item) => (item.key === group.key ? { ...item, loading: false } : item));
  }
}

async function hydrateGroupedRowsByOffset() {
  const targetModel = resolvedModelRef.value || model.value;
  if (!targetModel) return;
  // When backend already returns offset-aligned sample_rows for each group, skip redundant hydration fetches.
  const candidates = groupedRows.value.filter(
    (item) => Number(item.pageOffset || 0) > 0 && !item.pageSyncedFromServer,
  );
  if (!candidates.length) return;
  const keys = new Set(candidates.map((item) => item.key));
  groupedRows.value = groupedRows.value.map((item) => (keys.has(item.key) ? { ...item, loading: true } : item));
  const fields = resolveGroupedPageFields();
  const updates = await Promise.all(
    candidates.map(async (item) => {
      try {
        const limit = Math.max(1, Number(item.pageLimit || groupSampleLimit.value || 3));
        const offset = normalizeGroupPageOffset(Number(item.pageOffset || 0), limit, Number(item.count || 0));
        const result = await listRecordsRaw({
          model: targetModel,
          fields,
          domain: Array.isArray(item.domain) ? item.domain : [],
          context: mergeContext(actionMeta.value?.context, resolveEffectiveRequestContext()),
          context_raw: resolveEffectiveRequestContextRaw(),
          limit,
          offset,
          order: sortLabel.value,
        });
        return {
          key: item.key,
          rows: Array.isArray(result.data?.records) ? (result.data.records as Array<Record<string, unknown>>) : [],
          ok: true,
        };
      } catch {
        return { key: item.key, rows: [] as Array<Record<string, unknown>>, ok: false };
      }
    }),
  );
  const updateMap = new Map(updates.map((row) => [row.key, row]));
  groupedRows.value = groupedRows.value.map((item) => {
    const found = updateMap.get(item.key);
    if (!found) return item;
    if (!found.ok) return { ...item, loading: false };
    return { ...item, sampleRows: found.rows, loading: false };
  });
}

function normalizeGroupedRouteState() {
  if (!activeGroupByField.value) {
    if (groupWindowOffset.value !== 0) {
      groupWindowOffset.value = 0;
      syncRouteListState({ group_offset: undefined });
    }
    if (collapsedGroupKeys.value.length) {
      collapsedGroupKeys.value = [];
      syncRouteListState({ group_collapsed: undefined, group_page: undefined, group_offset: undefined });
    }
    if (Object.keys(groupPageOffsets.value).length) {
      groupPageOffsets.value = {};
      syncRouteListState({ group_page: undefined, group_offset: undefined });
    }
    return;
  }
  const validGroupKeys = new Set(groupedRows.value.map((item) => item.key).filter(Boolean));
  const normalizedCollapsed = collapsedGroupKeys.value.filter((key) => validGroupKeys.has(key));
  const collapsedChanged =
    normalizedCollapsed.length !== collapsedGroupKeys.value.length
    || normalizedCollapsed.some((key, idx) => key !== collapsedGroupKeys.value[idx]);
  const routeGroupValue = String(route.query.group_value || '').trim();
  const groupValueExists = !routeGroupValue
    || groupedRows.value.some((item) => item.label === routeGroupValue)
    || groupSummaryItems.value.some((item) => item.label === routeGroupValue);
  if (!groupValueExists) {
    activeGroupSummaryKey.value = '';
    activeGroupSummaryDomain.value = [];
  }
  const normalizedGroupPages = Object.entries(groupPageOffsets.value).reduce<Record<string, number>>((acc, [key, offset]) => {
    if (!validGroupKeys.has(key)) return acc;
    const grouped = groupedRows.value.find((item) => item.key === key);
    if (!grouped) return acc;
    const pageLimit = Math.max(1, Number(grouped.pageLimit || groupSampleLimit.value || 3));
    const normalizedOffset = normalizeGroupPageOffset(Number(offset || 0), pageLimit, Number(grouped.count || 0));
    if (normalizedOffset > 0) acc[key] = normalizedOffset;
    return acc;
  }, {});
  const groupPageChanged =
    Object.keys(normalizedGroupPages).length !== Object.keys(groupPageOffsets.value).length
    || Object.entries(normalizedGroupPages).some(([key, value]) => groupPageOffsets.value[key] !== value);
  collapsedGroupKeys.value = normalizedCollapsed;
  groupPageOffsets.value = normalizedGroupPages;
  const nextState: Record<string, unknown> = {
    group_collapsed: normalizedCollapsed.length ? normalizedCollapsed.join(',') : undefined,
    group_page: serializeGroupPageOffsets(normalizedGroupPages) || undefined,
    group_offset: groupWindowOffset.value > 0 ? groupWindowOffset.value : undefined,
  };
  if (!groupValueExists) nextState.group_value = undefined;
  const routeGroupOffset = Number(route.query.group_offset || 0);
  const currentOffset = Number.isFinite(routeGroupOffset) && routeGroupOffset > 0 ? Math.trunc(routeGroupOffset) : 0;
  const groupOffsetChanged = currentOffset !== groupWindowOffset.value;
  if (collapsedChanged || !groupValueExists || groupPageChanged || groupOffsetChanged) syncRouteListState(nextState);
}

function openFocusAction(action: FocusNavAction | string) {
  const path = typeof action === 'string' ? action : action.to;
  const query = typeof action === 'string' ? undefined : action.query;
  router.push({ path, query: query ? { ...resolveWorkspaceContextQuery(), ...query } : undefined }).catch(() => {});
}

async function executeHeaderAction(actionKey: string) {
  const handled = await executePageContractAction({
    actionKey,
    router,
    actionIntent: pageActionIntent,
    actionTarget: pageActionTarget,
    query: resolveWorkspaceContextQuery(),
    onRefresh: reload,
    onFallback: async (key) => {
      if (key === 'open_my_work') {
        openFocusAction('/my-work');
        return true;
      }
      if (key === 'open_risk_dashboard') {
        openFocusAction('/s/projects.dashboard');
        return true;
      }
      if (key === 'refresh_page' || key === 'refresh') {
        reload();
        return true;
      }
      return false;
    },
  });
  if (!handled) {
    batchMessage.value = pageText('error_fallback', '操作暂不可用');
  }
}

function resolveDefaultSort(contract: ActionContractLoose) {
  const fieldNames = new Set(Object.keys(contract.fields || {}));
  const supports = (name: string) => fieldNames.has(name);
  const segments: string[] = [];
  if (surfaceKind.value === 'risk') {
    if (supports('priority')) segments.push('priority desc');
    if (supports('deadline')) segments.push('deadline asc');
    if (supports('user_id')) segments.push('user_id asc');
  } else if (surfaceKind.value === 'cost') {
    if (supports('priority')) segments.push('priority desc');
    if (supports('deadline')) segments.push('deadline asc');
  }
  if (supports('write_date')) segments.push('write_date desc');
  segments.push('id desc');
  return segments.join(',');
}

function resolveContractFilterDomain() {
  const key = activeContractFilterKey.value;
  if (!key) return [];
  const found = contractFilterChips.value.find((chip) => chip.key === key);
  return found?.domain || [];
}

function resolveContractFilterDomainRaw() {
  const key = activeContractFilterKey.value;
  if (!key) return '';
  const found = contractFilterChips.value.find((chip) => chip.key === key);
  return found?.domainRaw || '';
}

function resolveContractFilterContext() {
  const key = activeContractFilterKey.value;
  if (!key) return {};
  const found = contractFilterChips.value.find((chip) => chip.key === key);
  return found?.context || {};
}

function resolveContractFilterContextRaw() {
  const key = activeContractFilterKey.value;
  if (!key) return '';
  const found = contractFilterChips.value.find((chip) => chip.key === key);
  return found?.contextRaw || '';
}

function resolveSavedFilterDomain() {
  const key = activeSavedFilterKey.value;
  if (!key) return [];
  const found = contractSavedFilterChips.value.find((chip) => chip.key === key);
  return found?.domain || [];
}

function resolveSavedFilterDomainRaw() {
  const key = activeSavedFilterKey.value;
  if (!key) return '';
  const found = contractSavedFilterChips.value.find((chip) => chip.key === key);
  return found?.domainRaw || '';
}

function resolveSavedFilterContext() {
  const key = activeSavedFilterKey.value;
  if (!key) return {};
  const found = contractSavedFilterChips.value.find((chip) => chip.key === key);
  return found?.context || {};
}

function resolveSavedFilterContextRaw() {
  const key = activeSavedFilterKey.value;
  if (!key) return '';
  const found = contractSavedFilterChips.value.find((chip) => chip.key === key);
  return found?.contextRaw || '';
}

function resolveEffectiveFilterDomain() {
  return mergeSceneDomain(
    mergeSceneDomain(resolveContractFilterDomain(), resolveSavedFilterDomain()),
    Array.isArray(activeGroupSummaryDomain.value) ? activeGroupSummaryDomain.value : [],
  );
}

function resolveEffectiveFilterDomainRaw() {
  const raw = [resolveContractFilterDomainRaw(), resolveSavedFilterDomainRaw()].filter(Boolean);
  return raw.join(' && ');
}

function resolveEffectiveFilterContext() {
  return { ...resolveContractFilterContext(), ...resolveSavedFilterContext() };
}

function resolveEffectiveFilterContextRaw() {
  const raw = [resolveContractFilterContextRaw(), resolveSavedFilterContextRaw()].filter(Boolean);
  return raw.join(' && ');
}

function resolveGroupByContext() {
  const field = activeGroupByField.value;
  if (!field) return {};
  const found = contractGroupByChips.value.find((chip) => chip.field === field);
  return { ...(found?.context || {}), group_by: field };
}

function resolveGroupByContextRaw() {
  const field = activeGroupByField.value;
  if (!field) return '';
  const found = contractGroupByChips.value.find((chip) => chip.field === field);
  const raw = [found?.contextRaw || '', `{'group_by': '${field}'}`].filter(Boolean);
  return raw.join(' && ');
}

function resolveEffectiveRequestContext() {
  return { ...resolveEffectiveFilterContext(), ...resolveGroupByContext() };
}

function resolveEffectiveRequestContextRaw() {
  const raw = [resolveEffectiveFilterContextRaw(), resolveGroupByContextRaw()].filter(Boolean);
  return raw.join(' && ');
}

function mergeContext(base: Record<string, unknown> | string | undefined, extra?: Record<string, unknown>) {
  const routeContextRaw = String(route.query.context_raw || '').trim();
  const routeContext = parseContractContextRaw(routeContextRaw);
  const mergedExtra = extra || {};
  if (!base || typeof base === 'string') {
    return menuId.value ? { menu_id: menuId.value, ...routeContext, ...mergedExtra } : { ...routeContext, ...mergedExtra };
  }
  if (!menuId.value) {
    return { ...base, ...routeContext, ...mergedExtra };
  }
  return { ...base, menu_id: menuId.value, ...routeContext, ...mergedExtra };
}

function normalizeDomain(domain: unknown) {
  if (Array.isArray(domain)) {
    return domain;
  }
  return [];
}

function mergeSceneDomain(base: unknown, sceneFilters: unknown) {
  const baseDomain = normalizeDomain(base);
  const sceneDomain = normalizeDomain(sceneFilters);
  if (!sceneDomain.length) {
    return baseDomain;
  }
  if (!baseDomain.length) {
    return sceneDomain;
  }
  return [...sceneDomain, ...baseDomain];
}

function mergeActiveFilter(base: unknown) {
  const domain = normalizeDomain(base);
  if (!hasActiveField.value || filterValue.value === 'all') {
    return domain;
  }
  const activeClause = ['active', '=', filterValue.value === 'active'];
  if (!domain.length) {
    return [activeClause];
  }
  return [...domain, activeClause];
}

function readTotalFromListResult(payload: unknown): number | null {
  if (!payload || typeof payload !== 'object') return null;
  const raw = Number((payload as Record<string, unknown>).total);
  if (!Number.isFinite(raw) || raw < 0) return null;
  return Math.trunc(raw);
}

async function fetchScopedTotal(params: {
  model: string;
  domain: unknown[];
  domainRaw: string;
  context: Record<string, unknown>;
  contextRaw: string;
  searchTerm: string;
  order: string;
}) {
  const result = await listRecordsRaw({
    model: params.model,
    fields: ['id'],
    domain: params.domain,
    domain_raw: params.domainRaw,
    need_total: true,
    context: params.context,
    context_raw: params.contextRaw,
    limit: 1,
    offset: 0,
    search_term: params.searchTerm || undefined,
    order: params.order,
  });
  return readTotalFromListResult(result.data);
}

async function fetchProjectScopeMetrics(params: {
  model: string;
  domain: unknown[];
  domainRaw: string;
  context: Record<string, unknown>;
  contextRaw: string;
  searchTerm: string;
  order: string;
}) {
  const fields = [
    'id',
    'stage_id',
    'state',
    'status',
    'contract_income_total',
    'contract_amount',
    'amount_total',
    'total_amount',
    'budget_total',
  ];
  const pageLimit = 200;
  const maxPages = 25;
  let page = 0;
  let offset = 0;
  let warning = 0;
  let done = 0;
  let amount = 0;
  while (page < maxPages) {
    const result = await listRecordsRaw({
      model: params.model,
      fields,
      domain: params.domain,
      domain_raw: params.domainRaw,
      context: params.context,
      context_raw: params.contextRaw,
      limit: pageLimit,
      offset,
      search_term: params.searchTerm || undefined,
      order: params.order,
    });
    const payload = result.data && typeof result.data === 'object'
      ? (result.data as Record<string, unknown>)
      : {};
    const pageRows = Array.isArray(payload.records)
      ? (payload.records as Array<Record<string, unknown>>)
      : [];
    if (!pageRows.length) break;
    pageRows.forEach((row) => {
      const state = resolveProjectStateCell(row);
      if (state.tone === 'danger' || state.tone === 'warning') warning += 1;
      if (isCompletedState(String(state.text || ''), state.tone)) done += 1;
      amount += resolveProjectAmount(row);
    });
    const nextOffset = Number(payload.next_offset || 0);
    if (!Number.isFinite(nextOffset) || nextOffset <= offset) {
      offset += pageRows.length;
    } else {
      offset = Math.trunc(nextOffset);
    }
    if (pageRows.length < pageLimit) break;
    page += 1;
  }
  return { warning, done, amount };
}

function uniqueFields(fields: string[]) {
  const seen = new Set<string>();
  return fields.filter((field) => {
    if (!field) return false;
    if (seen.has(field)) return false;
    seen.add(field);
    return true;
  });
}

function resolveRequestedFields(contractFields: string[], profile: SceneListProfile | null) {
  const profileColumns = profile?.columns ?? [];
  const secondary = profile?.row_secondary ? [profile.row_secondary] : [];
  return uniqueFields([...profileColumns, ...secondary, ...contractFields]);
}

function findMenuNode(nodes: NavNode[], menuId?: number): NavNode | null {
  if (!menuId) {
    return null;
  }
  const walk = (items: NavNode[]): NavNode | null => {
    for (const node of items) {
      if (node.menu_id === menuId || node.id === menuId) {
        return node;
      }
      if (node.children?.length) {
        const found = walk(node.children);
        if (found) return found;
      }
    }
    return null;
  };
  return walk(nodes) || null;
}

function downloadCsvBase64(filename: string, mimeType: string, contentB64: string) {
  if (!contentB64) return;
  const binary = atob(contentB64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  const blob = new Blob([bytes], { type: mimeType || 'text/csv' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename || 'export.csv';
  link.click();
  URL.revokeObjectURL(url);
}

function applyBatchFailureArtifacts(result: {
  failed_preview?: Array<{ id: number; reason_code: string; message: string; retryable?: boolean; suggested_action?: string }>;
  failed_page_offset?: number;
  failed_page_limit?: number;
  failed_has_more?: boolean;
  failed_truncated?: number;
  failed_csv_file_name?: string;
  failed_csv_content_b64?: string;
}, options?: { append?: boolean }) {
  const preview = Array.isArray(result.failed_preview) ? result.failed_preview : [];
  const lines: BatchDetailLine[] = preview.map((item) => {
    const hint = resolveSuggestedAction(item.suggested_action, item.reason_code, item.retryable);
    const retryTag = item.retryable === true
      ? pageText('retry_tag_retryable', '可重试')
      : item.retryable === false
        ? pageText('retry_tag_non_retryable', '不可重试')
        : '';
    const text = [`#${item.id} ${item.reason_code}: ${item.message}`, retryTag, hint].filter(Boolean).join(' | ');
    const action = describeSuggestedAction(item.suggested_action, {
      hasRetryHandler: true,
      hasActionHandler: false,
    });
    return {
      text,
      actionRaw: action.canRun ? action.parsed.raw : '',
      actionLabel: action.label,
    };
  });
  if (options?.append) {
    batchDetails.value = [...batchDetails.value, ...lines];
  } else {
    batchDetails.value = lines;
  }
  batchFailedOffset.value = Number(result.failed_page_offset || 0) + preview.length;
  batchFailedLimit.value = Number(result.failed_page_limit || 12) || 12;
  batchHasMoreFailures.value = Boolean(result.failed_has_more);
  if ('failed_csv_file_name' in result && result.failed_csv_file_name) {
    failedCsvFileName.value = String(result.failed_csv_file_name || '');
  }
  if ('failed_csv_content_b64' in result && result.failed_csv_content_b64) {
    failedCsvContentB64.value = String(result.failed_csv_content_b64 || '');
  }
}

function handleBatchDetailAction(actionRaw: string) {
  runSuggestedAction(actionRaw, { onRetry: reload });
}

function extractColumnsFromContract(contract: Awaited<ReturnType<typeof loadActionContract>>, sceneColumns: string[] = []) {
  if (Array.isArray(sceneColumns) && sceneColumns.length) {
    return sceneColumns;
  }
  const typed = contract as ActionContractLoose;
  const directViews = typed.views || typed.ui_contract?.views;
  if (directViews) {
    const treeBlock = directViews.tree || directViews.list;
    const treeColumns = treeBlock?.columns;
    if (Array.isArray(treeColumns) && treeColumns.length) {
      return treeColumns;
    }
    const treeSchema = treeBlock?.columnsSchema || treeBlock?.columns_schema;
    if (Array.isArray(treeSchema) && treeSchema.length) {
      return treeSchema.map((col) => col.name).filter(Boolean) as string[];
    }
  }

  const columns = typed.ui_contract?.columns;
  if (Array.isArray(columns) && columns.length) {
    return columns;
  }
  const schema = typed.ui_contract?.columnsSchema;
  if (Array.isArray(schema) && schema.length) {
    return schema.map((col) => col.name).filter(Boolean) as string[];
  }
  return [];
}

function convergeColumnsForSurface(rawColumns: string[], fields: Record<string, unknown>) {
  const normalized = rawColumns.filter(Boolean);
  if (!normalized.length || surfaceKind.value === 'generic') return normalized;

  const rows = normalized.map((name) => {
    const descriptor = (fields?.[name] || {}) as { string?: string };
    const merged = `${name} ${String(descriptor.string || '')}`.toLowerCase();
    return { name, merged };
  });
  const pick = (keywords: string[]) =>
    rows.filter((row) => keywords.some((kw) => row.merged.includes(kw))).map((row) => row.name);

  const buckets: string[][] = [];
  if (surfaceKind.value === 'risk') {
    buckets.push(
      pick(keywordList('columns_risk_bucket_identity', 'title,name,风险,事项')),
      pick(keywordList('columns_risk_bucket_priority', 'priority,severity,优先级,严重')),
      pick(keywordList('columns_risk_bucket_deadline', 'deadline,date_deadline,截止,逾期')),
      pick(keywordList('columns_risk_bucket_owner', 'user_id,owner,assignee,负责人,分派')),
      pick(keywordList('columns_risk_bucket_state', 'state,stage,status,状态')),
      pick(keywordList('columns_risk_bucket_reason', 'reason,原因')),
    );
  } else if (surfaceKind.value === 'contract') {
    buckets.push(
      pick(keywordList('columns_contract_bucket_amount', 'amount_total,contract_amount,金额,合同额')),
      pick(keywordList('columns_contract_bucket_execution', 'execute,execution,progress,执行率')),
      pick(keywordList('columns_contract_bucket_payment', 'paid,payment,付款,支付')),
      pick(keywordList('columns_contract_bucket_risk', 'risk,风险,alert')),
      pick(keywordList('columns_contract_bucket_change', 'change,变更,write_date,最近')),
      pick(keywordList('columns_contract_bucket_identity', 'title,name,合同')),
    );
  } else if (surfaceKind.value === 'cost') {
    buckets.push(
      pick(keywordList('columns_cost_bucket_execution', 'cost,执行率,rate')),
      pick(keywordList('columns_cost_bucket_overrun', 'over,overrun,超支,偏差')),
      pick(keywordList('columns_cost_bucket_count', 'count,项数')),
      pick(keywordList('columns_cost_bucket_deadline', 'deadline,截止')),
      pick(keywordList('columns_cost_bucket_priority', 'priority,优先级')),
      pick(keywordList('columns_cost_bucket_identity', 'title,name,项目')),
    );
  } else if (surfaceKind.value === 'project') {
    buckets.push(
      pick(keywordList('columns_project_bucket_identity', 'title,name,项目')),
      pick(keywordList('columns_project_bucket_state', 'state,stage,status,状态,阶段')),
      pick(keywordList('columns_project_bucket_risk', 'risk,风险')),
      pick(keywordList('columns_project_bucket_payment', 'payment,付款')),
      pick(keywordList('columns_project_bucket_output', 'output,产值')),
      pick(keywordList('columns_project_bucket_cost', 'cost,成本')),
    );
  }

  const selected: string[] = [];
  for (const bucket of buckets) {
    for (const name of bucket) {
      if (!selected.includes(name)) selected.push(name);
    }
  }
  for (const name of normalized) {
    if (selected.length >= 6) break;
    if (!selected.includes(name)) selected.push(name);
  }
  return selected.length ? selected : normalized;
}

function extractKanbanFields(contract: Awaited<ReturnType<typeof loadActionContract>>) {
  const typed = contract as ActionContractLoose;
  const directViews = typed.views || typed.ui_contract?.views;
  if (directViews) {
    const kanbanBlock = directViews.kanban;
    if (Array.isArray(kanbanBlock?.fields) && kanbanBlock.fields.length) {
      return kanbanBlock.fields;
    }
  }
  return [];
}

function extractKanbanProfile(contract: Awaited<ReturnType<typeof loadActionContract>>) {
  const typed = contract as ActionContractLoose;
  const directViews = typed.views || typed.ui_contract?.views;
  const block = directViews?.kanban;
  const profile = (block?.kanban_profile || {}) as Record<string, unknown>;
  const normalize = (rows: unknown) =>
    Array.isArray(rows) ? rows.map((item) => String(item || '').trim()).filter(Boolean) : [];
  return {
    titleField: String(profile.title_field || '').trim(),
    primaryFields: normalize(profile.primary_fields),
    secondaryFields: normalize(profile.secondary_fields),
    statusFields: normalize(profile.status_fields),
  };
}

function extractAdvancedViewFields(contract: Awaited<ReturnType<typeof loadActionContract>>, mode: string) {
  const typed = contract as ActionContractLoose;
  const directViews = typed.views as Record<string, unknown> | undefined;
  const normalizedViews = typed.ui_contract?.views as Record<string, unknown> | undefined;
  const viewBlock = (directViews?.[mode] || normalizedViews?.[mode]) as Record<string, unknown> | undefined;
  const fallbackNames = ['name', 'display_name', 'id'];
  if (mode === 'pivot') {
    const measures = Array.isArray(viewBlock?.measures) ? viewBlock.measures : [];
    const dims = Array.isArray(viewBlock?.dimensions) ? viewBlock.dimensions : [];
    const fields = [...dims, ...measures, ...fallbackNames]
      .map((item) => String(item || '').trim())
      .filter(Boolean);
    return uniqueFields(fields);
  }
  if (mode === 'graph') {
    const measure = String(viewBlock?.measure || '').trim();
    const dim = String(viewBlock?.dimension || '').trim();
    return uniqueFields([dim, measure, ...fallbackNames].filter(Boolean));
  }
  if (mode === 'calendar' || mode === 'gantt') {
    const dateStart = String(viewBlock?.date_start || '').trim();
    const dateStop = String(viewBlock?.date_stop || '').trim();
    const fields = [dateStart, dateStop, ...fallbackNames];
    return uniqueFields(fields.map((item) => String(item || '').trim()).filter(Boolean));
  }
  if (mode === 'activity') {
    const activityField = String(viewBlock?.field || '').trim();
    return uniqueFields([activityField, ...fallbackNames].filter(Boolean));
  }
  if (mode === 'dashboard') {
    const kpis = Array.isArray(viewBlock?.kpis) ? viewBlock.kpis : [];
    const cards = Array.isArray(viewBlock?.cards) ? viewBlock.cards : [];
    const guessed = [...kpis, ...cards]
      .map((item) => String((item as Record<string, unknown>)?.field || '').trim())
      .filter(Boolean);
    return uniqueFields([...guessed, ...fallbackNames]);
  }
  return fallbackNames;
}

function advancedRowTitle(row: Record<string, unknown>) {
  return String(row.display_name || row.name || row.id || pageText('advanced_row_title_fallback', '记录')).trim();
}

function advancedFieldLabel(field: string) {
  return String(contractColumnLabels.value[field] || field).trim();
}

function advancedRowMeta(row: Record<string, unknown>) {
  const preferredKeys = advancedFields.value.length
    ? advancedFields.value
    : Object.keys(row);
  const entries = preferredKeys
    .filter((key) => key !== 'id' && key !== 'name' && key !== 'display_name' && key in row)
    .slice(0, 3)
    .map((key) => `${advancedFieldLabel(key)}: ${String(row[key] ?? '-')}`);
  if (!entries.length) return pageText('advanced_row_meta_empty', '无附加字段');
  return entries.join(' · ');
}

function buildGroupKey(field: unknown, value: unknown, fallback: unknown) {
  const fieldPart = String(field || activeGroupByField.value || 'group').trim() || 'group';
  const valuePart = typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean'
    ? String(value)
    : JSON.stringify(value ?? fallback);
  return `${fieldPart}:${valuePart}`;
}

function resolveModelFromContract(contract: Awaited<ReturnType<typeof loadActionContract>>) {
  const typed = contract as ActionContractLoose;
  const nested = (typed.ui_contract_raw || typed.ui_contract || {}) as ActionContractLoose;
  const direct = typed.model;
  if (typeof direct === 'string' && direct.trim()) {
    return direct.trim();
  }
  const nestedDirect = nested.model;
  if (typeof nestedDirect === 'string' && nestedDirect.trim()) {
    return nestedDirect.trim();
  }
  const headModel = typed.head?.model;
  if (typeof headModel === 'string' && headModel.trim()) {
    return headModel.trim();
  }
  const nestedHeadModel = nested.head?.model;
  if (typeof nestedHeadModel === 'string' && nestedHeadModel.trim()) {
    return nestedHeadModel.trim();
  }
  const viewModel = typed.views?.tree?.model || typed.views?.form?.model || typed.views?.kanban?.model;
  if (typeof viewModel === 'string' && viewModel.trim()) {
    return viewModel.trim();
  }
  const nestedViewModel = nested.views?.tree?.model || nested.views?.form?.model || nested.views?.kanban?.model;
  if (typeof nestedViewModel === 'string' && nestedViewModel.trim()) {
    return nestedViewModel.trim();
  }
  return '';
}

function getActionType(meta: unknown) {
  const raw = (meta as { type?: string; action_type?: string }) || {};
  return String(raw.type || raw.action_type || '').toLowerCase();
}

function isClientAction(meta: unknown) {
  const raw = meta as { tag?: string; type?: string; action_type?: string };
  const tag = String(raw?.tag || '').toLowerCase();
  const actionType = getActionType(meta);
  return actionType.includes('client') || tag.length > 0;
}

function isUrlAction(meta: unknown, contract: unknown) {
  const actionType = getActionType(meta);
  if (actionType.includes('act_url') || actionType.includes('url')) {
    return true;
  }
  const typed = contract as ActionContractLoose;
  const contractType = String(typed.data?.type || '').toLowerCase();
  return contractType === 'url_redirect';
}

function normalizeUrlTarget(target: unknown) {
  const raw = String(target || '').toLowerCase();
  if (raw === 'self' || raw === 'current' || raw === 'main') {
    return 'self';
  }
  return 'new';
}

function isShellRoute(url: string) {
  return (
    url === '/' ||
    url.startsWith('/s/') ||
    url.startsWith('/m/') ||
    url.startsWith('/a/') ||
    url.startsWith('/r/') ||
    url.startsWith('/login') ||
    url.startsWith('/admin/')
  );
}

function resolveNavigationUrl(url: string) {
  const raw = String(url || '').trim();
  if (!raw) {
    return '';
  }
  if (/^https?:\/\//i.test(raw)) {
    return raw;
  }
  if (!raw.startsWith('/')) {
    return raw;
  }
  try {
    return new URL(raw, config.apiBaseUrl).toString();
  } catch {
    return raw;
  }
}

function isPortalPath(url: string) {
  return url.startsWith('/portal/');
}

function resolveActionUrl(meta: unknown, contract: unknown) {
  const metaTyped = (meta as { url?: string }) || {};
  const metaUrl = String(metaTyped.url || '').trim();
  if (metaUrl) {
    return metaUrl;
  }
  const typed = contract as ActionContractLoose;
  const contractUrl = String(typed.data?.url || '').trim();
  if (contractUrl) {
    return contractUrl;
  }
  return '';
}

async function redirectUrlAction(meta: unknown, contract: unknown) {
  const url = resolveActionUrl(meta, contract);
  if (!url) {
    const actionType = getActionType(meta);
    const typed = contract as ActionContractLoose;
    const contractType = String(typed.data?.type || '').toLowerCase();
    await router.replace({
      name: 'workbench',
      query: resolveWorkbenchQuery(ErrorCodes.ACT_UNSUPPORTED_TYPE, {
        diag: {
          diag: 'act_url_empty',
          diag_action_type: actionType || undefined,
          diag_contract_type: contractType || undefined,
        },
      }),
    });
    return true;
  }
  const metaTyped = (meta as { target?: string }) || {};
  const typed = contract as ActionContractLoose;
  const target = normalizeUrlTarget(metaTyped.target || typed.data?.target);
  if (target === 'self' && isPortalPath(url)) {
    await router.replace({
      path: '/',
      query: resolveCarryQuery({
        menu_id: menuId.value || undefined,
        action_id: actionId.value || undefined,
      }),
    });
    return true;
  }
  if (target === 'self' && url.startsWith('/')) {
    if (isShellRoute(url)) {
      await router.replace(url);
    } else {
      window.location.assign(resolveNavigationUrl(url));
    }
    return true;
  }
  const navUrl = resolveNavigationUrl(url);
  window.open(navUrl, target === 'self' ? '_self' : '_blank', 'noopener,noreferrer');
  return true;
}

function isWindowAction(meta: unknown) {
  const actionType = getActionType(meta);
  return actionType.includes('act_window') || actionType.includes('window') || actionType === '';
}

function resolveSelectedIdsForAction(selection: ContractActionSelection) {
  if (selection === 'none') return [];
  if (selection === 'single') {
    return selectedIds.value.length === 1 ? [selectedIds.value[0]] : [];
  }
  return selectedIds.value.length ? [...selectedIds.value] : [];
}

function resolveActionContextRecordId() {
  const fromRoute = parseNumericId(route.query.res_id);
  if (fromRoute) return fromRoute;
  const fromContract = parseNumericId(actionContract.value?.head?.res_id);
  if (fromContract) return fromContract;
  return null;
}

function mutationRequiresRecordContext(action: ContractActionButton) {
  const required = Array.isArray(action.mutation?.payload_schema?.required)
    ? action.mutation?.payload_schema?.required
    : [];
  const requiredKeys = required.map((item) => String(item || '').trim().toLowerCase());
  return requiredKeys.includes('record_id')
    || requiredKeys.includes('id')
    || requiredKeys.includes('risk_action_id');
}

function buildMutationContext(action: ContractActionButton, recordId: number) {
  const context = { ...(action.context || {}) } as Record<string, unknown>;
  const modelName = String(action.mutation?.model || action.model || '').trim().toLowerCase();
  if (modelName === 'project.risk.action' && !context.risk_action_id) {
    context.risk_action_id = recordId;
  }
  if ((modelName === 'finance.payment.request' || modelName === 'payment.request') && !context.id) {
    context.id = recordId;
  }
  return context;
}

async function applyActionRefreshPolicy(policy?: ProjectionRefreshPolicy) {
  if (!policy || !Array.isArray(policy.on_success) || !policy.on_success.length) {
    await load();
    return;
  }
  await executeProjectionRefresh({
    policy,
    refreshScene: async () => {
      await load();
    },
    refreshWorkbench: async () => {
      await session.loadAppInit();
    },
    refreshRoleSurface: async () => {
      await session.loadAppInit();
    },
    recordTrace: ({ intent, writeMode, latencyMs }) => {
      session.recordIntentTrace({ intent, writeMode, latencyMs });
    },
  });
}

async function runContractAction(action: ContractActionButton) {
  if (!action.enabled) return;
  if (action.kind === 'open') {
    if (action.actionId) {
      const nextQuery = {
        ...resolveCarryQuery(),
        menu_id: menuId.value || undefined,
        action_id: action.actionId,
      };
      if (keepSceneRoute.value) {
        await router.push({ path: route.path, query: nextQuery });
      } else {
        await router.push({
          name: 'action',
          params: { actionId: action.actionId },
          query: nextQuery,
        });
      }
      return;
    }
    if (action.url) {
      const navUrl = resolveNavigationUrl(action.url);
      window.open(navUrl, action.target === 'self' ? '_self' : '_blank', 'noopener,noreferrer');
      return;
    }
    batchMessage.value = pageText('batch_msg_contract_action_missing_action_id', '契约动作缺少 action_id，无法打开目标页面');
    return;
  }

  if (action.mutation) {
    const ids = resolveSelectedIdsForAction(action.selection);
    const contextRecordId = resolveActionContextRecordId();
    const execIds = ids.length ? ids : contextRecordId ? [contextRecordId] : [];
    if (!execIds.length && mutationRequiresRecordContext(action)) {
      batchMessage.value = pageText('batch_msg_action_requires_record_context', '当前动作需要记录上下文，暂不支持无记录执行');
      return;
    }

    batchBusy.value = true;
    try {
      let successCount = 0;
      let failureCount = 0;
      const runIds = execIds.length ? execIds : [0];
      for (const id of runIds) {
        try {
          await executeSceneMutation({
            mutation: action.mutation,
            actionKey: action.key,
            recordId: id > 0 ? id : null,
            model: action.model,
            context: buildMutationContext(action, id),
          });
          successCount += 1;
        } catch {
          failureCount += 1;
        }
      }
      batchMessage.value = `${pageText('batch_msg_contract_action_done_prefix', '契约动作执行完成：成功 ')}${successCount}${pageText('batch_msg_contract_action_done_middle', '，失败 ')}${failureCount}`;
      if (successCount > 0) {
        await applyActionRefreshPolicy(action.refreshPolicy);
      }
    } finally {
      batchBusy.value = false;
    }
    return;
  }

  const ids = resolveSelectedIdsForAction(action.selection);
  if (action.selection !== 'none' && !ids.length) {
    batchMessage.value =
      action.selection === 'single'
        ? pageText('batch_msg_select_single_before_run', '请选择 1 条记录后再执行')
        : pageText('batch_msg_select_records_before_run', '请先选择记录后再执行');
    return;
  }
  if (!action.model) {
    batchMessage.value = pageText('batch_msg_contract_action_missing_model', '契约动作缺少 model，无法执行');
    return;
  }
  const contextRecordId = resolveActionContextRecordId();
  const execIds = ids.length ? ids : contextRecordId ? [contextRecordId] : [];
  if (!execIds.length) {
    batchMessage.value = pageText('batch_msg_action_requires_record_context', '当前动作需要记录上下文，暂不支持无记录执行');
    return;
  }

  batchBusy.value = true;
  try {
    let successCount = 0;
    let failureCount = 0;
    for (const id of execIds) {
      try {
        const response = await executeButton({
          model: action.model,
          res_id: id,
          button: { name: action.methodName || action.key, type: action.kind || 'object' },
          context: action.context,
        });
        if (response?.result?.action_id) {
          const nextQuery = {
            ...resolveCarryQuery(),
            menu_id: menuId.value || undefined,
            action_id: response.result.action_id,
          };
          if (keepSceneRoute.value) {
            await router.push({ path: route.path, query: nextQuery });
          } else {
            await router.push({
              name: 'action',
              params: { actionId: response.result.action_id },
              query: nextQuery,
            });
          }
          return;
        }
        successCount += 1;
      } catch {
        failureCount += 1;
      }
    }
    batchMessage.value = `${pageText('batch_msg_contract_action_done_prefix', '契约动作执行完成：成功 ')}${successCount}${pageText('batch_msg_contract_action_done_middle', '，失败 ')}${failureCount}`;
    if (successCount > 0) {
      await load();
    }
  } finally {
    batchBusy.value = false;
  }
}

async function loadAssigneeOptions() {
  if (!hasAssigneeField.value) {
    assigneeOptions.value = [];
    selectedAssigneeId.value = null;
    return;
  }
  try {
    const result = await listRecords({
      model: 'res.users',
      fields: ['id', 'name'],
      domain: [['active', '=', true]],
      order: 'name asc',
      limit: 80,
      silentErrors: true,
    });
    const rows = Array.isArray(result.records) ? result.records : [];
    assigneeOptions.value = rows
      .map((row) => {
        const id = typeof row.id === 'number' ? row.id : Number(row.id);
        const name = String(row.name || '');
        if (!id || Number.isNaN(id) || !name) return null;
        return { id, name };
      })
      .filter((row): row is { id: number; name: string } => !!row);
    if (selectedAssigneeId.value && !assigneeOptions.value.find((opt) => opt.id === selectedAssigneeId.value)) {
      selectedAssigneeId.value = null;
    }
  } catch (error) {
    assigneeOptions.value = [];
    selectedAssigneeId.value = null;
    if (error instanceof ApiError && String(error.reasonCode || '').toUpperCase() === 'PERMISSION_DENIED') {
      const model = String(error.details?.model || 'res.users').trim();
      const op = String(error.details?.op || 'list').trim().toLowerCase();
      batchMessage.value = `${pageText('batch_msg_assignee_options_limited_prefix', '负责人候选加载受限（')}${model}/${op}${pageText('batch_msg_assignee_options_limited_suffix', '）')}`;
    }
  }
}

async function load() {
  showMoreContractActions.value = false;
  showMoreSavedFilters.value = false;
  showMoreGroupBy.value = false;
  status.value = 'loading';
  clearError();
  traceId.value = '';
  lastIntent.value = 'api.data.list';
  lastWriteMode.value = 'read';
  lastLatencyMs.value = null;
  contractViewType.value = '';
  actionContract.value = null;
  resolvedModelRef.value = '';
  contractLimit.value = 40;
  records.value = [];
  groupedRows.value = [];
  groupSummaryItems.value = [];
  groupWindowCount.value = 0;
  groupWindowTotal.value = null;
  groupWindowStart.value = null;
  groupWindowEnd.value = null;
  groupWindowId.value = '';
  groupQueryFingerprint.value = '';
  groupWindowDigest.value = '';
  groupWindowIdentityKey.value = '';
  groupWindowPrevOffset.value = null;
  groupWindowNextOffset.value = null;
  columns.value = [];
  kanbanFields.value = [];
  kanbanPrimaryFields.value = [];
  kanbanSecondaryFields.value = [];
  kanbanStatusFields.value = [];
  kanbanTitleFieldHint.value = '';
  advancedFields.value = [];
  const startedAt = Date.now();

  if (!actionId.value) {
    setError(new Error('Action id missing'), 'Action id missing');
    status.value = deriveListStatus({ error: error.value?.message || '', recordsLength: 0 });
    return;
  }

  try {
    const { contract, meta } = await resolveAction(session.menuTree, actionId.value, actionMeta.value);
    if (meta) {
      session.setActionMeta(meta);
    }
    contractViewType.value = resolveContractViewMode(contract as ActionContractLoose, resolveActionViewType(meta, contract));
    if (!contractViewType.value) {
      setError(new Error('missing contract view_type'), 'missing contract view_type');
      status.value = deriveListStatus({ error: error.value?.message || '', recordsLength: 0 });
      return;
    }
    const typedContract = contract as ActionContractLoose;
    actionContract.value = typedContract;
    {
      const candidates = resolveAvailableViewModes(meta || null, typedContract, contractViewType.value);
      const routeMode = normalizeViewMode(route.query.view_mode);
      if (routeMode && candidates.includes(routeMode)) {
        preferredViewMode.value = routeMode;
      } else if (!preferredViewMode.value || !candidates.includes(normalizeViewMode(preferredViewMode.value))) {
        preferredViewMode.value = candidates[0] || '';
      }
    }
    const routeFilter = String(route.query.preset_filter || '').trim();
    const routeSavedFilter = String(route.query.saved_filter || '').trim();
    const routeGroupBy = String(route.query.group_by || '').trim();
    if (!activeContractFilterKey.value && routeFilter) {
      activeContractFilterKey.value = routeFilter;
    }
    if (activeContractFilterKey.value) {
      const hasFilter = Array.isArray(typedContract.search?.filters)
        && typedContract.search.filters.some((row) => String(row?.key || '') === activeContractFilterKey.value);
      if (!hasFilter) {
        activeContractFilterKey.value = '';
      }
    }
    if (!activeSavedFilterKey.value && routeSavedFilter) {
      activeSavedFilterKey.value = routeSavedFilter;
    }
    if (activeSavedFilterKey.value) {
      const hasSavedFilter = contractSavedFilterChips.value.some((row) => row.key === activeSavedFilterKey.value);
      if (!hasSavedFilter) {
        activeSavedFilterKey.value = '';
      }
    } else {
      const defaultSaved = contractSavedFilterChips.value.find((row) => row.isDefault);
      if (defaultSaved) activeSavedFilterKey.value = defaultSaved.key;
    }
    if (!activeGroupByField.value && routeGroupBy) {
      activeGroupByField.value = routeGroupBy;
    }
    if (activeGroupByField.value) {
      const hasGroupBy = contractGroupByChips.value.some((item) => item.field === activeGroupByField.value);
      if (!hasGroupBy) activeGroupByField.value = '';
    } else {
      const defaultGroupBy = contractGroupByChips.value.find((item) => item.isDefault);
      if (defaultGroupBy) activeGroupByField.value = defaultGroupBy.field;
    }
    const accessPolicy = resolveContractAccessPolicy(typedContract);
    contractReadAllowed.value = resolveContractReadRight(typedContract);
    contractWarningCount.value = Array.isArray(typedContract.warnings) ? typedContract.warnings.length : 0;
    contractDegraded.value = Boolean(typedContract.degraded);
    if (!contractReadAllowed.value) {
      await router.replace({
        name: 'workbench',
        query: resolveWorkbenchQuery(ErrorCodes.CAPABILITY_MISSING, {
          diag: {
            diag: 'contract_read_forbidden',
            diag_reason_code: accessPolicy.reasonCode || undefined,
            diag_access_mode: accessPolicy.mode,
          },
        }),
      });
      return;
    }
    if (isUrlAction(meta, contract)) {
      await redirectUrlAction(meta, contract);
      return;
    }
    if (!sortValue.value) {
      const searchDefaults = typedContract.search?.defaults;
      const searchOrder = searchDefaults?.order;
      const viewOrder = typedContract.views?.tree?.order || typedContract.ui_contract?.views?.tree?.order;
      const metaOrder = (meta as ActionMetaLoose | undefined)?.order;
      const order = sceneReadyListSurface.value.defaultSort || scene.value?.default_sort || searchOrder || viewOrder || metaOrder;
      if (surfaceKind.value !== 'generic') {
        sortValue.value = resolveDefaultSort(typedContract);
      } else if (typeof order === 'string' && order.trim()) {
        sortValue.value = order;
      } else {
        sortValue.value = 'id asc';
      }
    }
    {
      const searchDefaults = typedContract.search?.defaults;
      const limitRaw = Number(searchDefaults?.limit || 40);
      contractLimit.value = Number.isFinite(limitRaw) && limitRaw > 0 ? Math.min(Math.trunc(limitRaw), 200) : 40;
    }
    const policy = evaluateCapabilityPolicy({ source: meta, available: session.capabilities });
    if (policy.state !== 'enabled') {
      await router.replace({
        name: 'workbench',
        query: resolveWorkbenchQuery(ErrorCodes.CAPABILITY_MISSING, {
          public: { missing: policy.missing.join(',') || undefined },
        }),
      });
      return;
    }
    const contractModel = resolveModelFromContract(contract);
    const resolvedModel = meta?.model ?? model.value ?? contractModel;
    resolvedModelRef.value = resolvedModel || '';
    if (meta && !meta.model && resolvedModel) {
      session.setActionMeta({ ...meta, model: resolvedModel });
    }
    if (!resolvedModel) {
      if (isClientAction(meta)) {
        await router.replace({
          name: 'workbench',
          query: resolveWorkbenchQuery(ErrorCodes.ACT_NO_MODEL),
        });
        return;
      }
      if (!isWindowAction(meta)) {
        const actionType = getActionType(meta);
        const contractType = String(typedContract.data?.type || '').toLowerCase();
        const contractUrl = String(typedContract.data?.url || '');
        const metaUrl = String((meta as ActionMetaLoose | undefined)?.url || '');
        await router.replace({
          name: 'workbench',
          query: resolveWorkbenchQuery(ErrorCodes.ACT_UNSUPPORTED_TYPE, {
            diag: {
              diag: 'non_window_action',
              diag_action_type: actionType || undefined,
              diag_contract_type: contractType || undefined,
              diag_contract_url: contractUrl || undefined,
              diag_meta_url: metaUrl || undefined,
            },
          }),
        });
        return;
      }
      setError(new Error('Action has no model'), 'Action has no model');
      status.value = deriveListStatus({ error: error.value?.message || '', recordsLength: 0 });
      return;
    }
    if (contractViewType.value === 'form') {
      const actionResId = extractActionResId(contract, route.query as Record<string, unknown>);
      await router.replace({
        name: 'model-form',
        params: { model: resolvedModel, id: actionResId ? String(actionResId) : 'new' },
        query: resolveCarryQuery(),
      });
      return;
    }
    const contractColumns = convergeColumnsForSurface(
      extractColumnsFromContract(contract, sceneReadyListSurface.value.columns),
      typedContract.fields || {},
    );
    const kanbanContractFields = extractKanbanFields(contract);
    const kanbanProfile = extractKanbanProfile(contract);
    const advancedContractFields = extractAdvancedViewFields(contract, viewMode.value);
    const fallbackKanbanFields = resolveRequestedFields(contractColumns, listProfile.value);
    const effectiveKanbanFields = kanbanContractFields.length
      ? kanbanContractFields
      : uniqueFields([...fallbackKanbanFields, 'id', 'name']);
    advancedFields.value = advancedContractFields;
    kanbanFields.value = effectiveKanbanFields;
    kanbanTitleFieldHint.value = kanbanProfile.titleField;
    kanbanPrimaryFields.value = uniqueFields(
      [...kanbanProfile.primaryFields].filter((name) => effectiveKanbanFields.includes(name)),
    );
    kanbanSecondaryFields.value = uniqueFields(
      [...kanbanProfile.secondaryFields].filter((name) => effectiveKanbanFields.includes(name)),
    );
    kanbanStatusFields.value = uniqueFields(
      [...kanbanProfile.statusFields].filter((name) => effectiveKanbanFields.includes(name)),
    );
    const fieldMap = typedContract.fields || {};
    hasActiveField.value = Boolean(fieldMap && typeof fieldMap === 'object' && 'active' in fieldMap);
    hasAssigneeField.value = Boolean(fieldMap && typeof fieldMap === 'object' && 'user_id' in fieldMap);
    await loadAssigneeOptions();
    if (viewMode.value === 'kanban' && !kanbanContractFields.length) {
      console.warn('[contract] missing kanban fields; fallback to list/profile fields', {
        actionId: actionId.value,
        model: resolvedModel,
        fallbackFieldCount: effectiveKanbanFields.length,
      });
    }
    const requestedFields =
      viewMode.value === 'kanban'
        ? effectiveKanbanFields
        : viewMode.value === 'tree'
          ? resolveRequestedFields(contractColumns, listProfile.value)
          : advancedContractFields;
    if (viewMode.value === 'tree' && !contractColumns.length) {
      setError(new Error('missing contract columns for list/tree view'), 'missing contract columns for list/tree view');
      status.value = deriveListStatus({ error: error.value?.message || '', recordsLength: 0 });
      return;
    }
    const baseDomain = mergeSceneDomain(
      mergeSceneDomain(meta?.domain, scene.value?.filters),
      resolveEffectiveFilterDomain(),
    );
    const activeDomain = mergeActiveFilter(baseDomain);
    const requestContext = mergeContext(meta?.context, resolveEffectiveRequestContext());
    const requestContextRaw = resolveEffectiveRequestContextRaw();
    const result = await listRecordsRaw({
      model: resolvedModel,
      fields: requestedFields.length ? requestedFields : ['id', 'name'],
      domain: activeDomain,
      domain_raw: resolveEffectiveFilterDomainRaw(),
      need_total: true,
      group_by: activeGroupByField.value || undefined,
      group_offset: activeGroupByField.value ? Math.max(0, Math.trunc(groupWindowOffset.value || 0)) : 0,
      need_group_total: Boolean(activeGroupByField.value),
      group_sample_limit: groupSampleLimit.value,
      group_limit: Math.min(50, Math.max(12, Number(contractLimit.value || 0))),
      group_page_size: groupSampleLimit.value,
      group_page_offsets: groupPageOffsets.value,
      context: requestContext,
      context_raw: requestContextRaw,
      limit: contractLimit.value,
      offset: 0,
      search_term: searchTerm.value.trim() || undefined,
      order: sortLabel.value,
    });
    const groupPaging =
      result.data && typeof (result.data as Record<string, unknown>).group_paging === 'object'
        ? ((result.data as Record<string, unknown>).group_paging as Record<string, unknown>)
        : null;
    const effectiveGroupOffset =
      groupPaging && Number.isFinite(Number(groupPaging.group_offset))
        ? Math.max(0, Math.trunc(Number(groupPaging.group_offset)))
        : Math.max(0, Math.trunc(groupWindowOffset.value || 0));
    const windowIdentity = groupPaging && typeof groupPaging.window_identity === 'object' && groupPaging.window_identity !== null
      ? (groupPaging.window_identity as Record<string, unknown>)
      : null;
    groupWindowOffset.value = effectiveGroupOffset;
    groupWindowId.value =
      windowIdentity && typeof windowIdentity.window_id === 'string'
        ? String(windowIdentity.window_id)
        : (groupPaging && typeof groupPaging.window_id === 'string' ? String(groupPaging.window_id) : '');
    const responseGroupFingerprint =
      windowIdentity && typeof windowIdentity.query_fingerprint === 'string'
        ? String(windowIdentity.query_fingerprint)
        : (groupPaging && typeof groupPaging.query_fingerprint === 'string' ? String(groupPaging.query_fingerprint) : '');
    groupQueryFingerprint.value = responseGroupFingerprint;
    groupWindowDigest.value =
      windowIdentity && typeof windowIdentity.window_digest === 'string'
        ? String(windowIdentity.window_digest)
        : (groupPaging && typeof groupPaging.window_digest === 'string' ? String(groupPaging.window_digest) : '');
    groupWindowIdentityKey.value =
      windowIdentity && typeof windowIdentity.key === 'string'
        ? String(windowIdentity.key)
        : (groupPaging && typeof groupPaging.window_key === 'string' ? String(groupPaging.window_key) : '');
    const routeGroupFingerprint = String(route.query.group_fp || '').trim();
    const routeGroupWindowId = String(route.query.group_wid || '').trim();
    const routeGroupWindowDigest = String(route.query.group_wdg || '').trim();
    const routeGroupWindowIdentityKey = String(route.query.group_wik || '').trim();
    if (
      activeGroupByField.value
      && routeGroupFingerprint
      && responseGroupFingerprint
      && routeGroupFingerprint !== responseGroupFingerprint
      && effectiveGroupOffset > 0
    ) {
      // Route window state is stale for current grouped query; reset to first window.
      groupWindowOffset.value = 0;
      groupPageOffsets.value = {};
      collapsedGroupKeys.value = [];
      syncRouteListState({
        group_offset: undefined,
        group_page: undefined,
        group_collapsed: undefined,
        group_fp: responseGroupFingerprint,
        group_wid: undefined,
        group_wdg: undefined,
        group_wik: undefined,
      });
      return void load();
    }
    if (
      activeGroupByField.value
      && routeGroupWindowId
      && groupWindowId.value
      && routeGroupWindowId !== groupWindowId.value
      && effectiveGroupOffset > 0
    ) {
      groupWindowOffset.value = 0;
      groupPageOffsets.value = {};
      collapsedGroupKeys.value = [];
      syncRouteListState({
        group_offset: undefined,
        group_page: undefined,
        group_collapsed: undefined,
        group_wid: groupWindowId.value,
        group_wdg: undefined,
        group_wik: undefined,
      });
      return void load();
    }
    if (
      activeGroupByField.value
      && routeGroupWindowDigest
      && groupWindowDigest.value
      && routeGroupWindowDigest !== groupWindowDigest.value
      && effectiveGroupOffset > 0
    ) {
      groupWindowOffset.value = 0;
      groupPageOffsets.value = {};
      collapsedGroupKeys.value = [];
      syncRouteListState({
        group_offset: undefined,
        group_page: undefined,
        group_collapsed: undefined,
        group_wdg: groupWindowDigest.value,
      });
      return void load();
    }
    if (
      activeGroupByField.value
      && routeGroupWindowIdentityKey
      && groupWindowIdentityKey.value
      && routeGroupWindowIdentityKey !== groupWindowIdentityKey.value
      && effectiveGroupOffset > 0
    ) {
      groupWindowOffset.value = 0;
      groupPageOffsets.value = {};
      collapsedGroupKeys.value = [];
      syncRouteListState({
        group_offset: undefined,
        group_page: undefined,
        group_collapsed: undefined,
        group_wik: groupWindowIdentityKey.value,
      });
      return void load();
    }
    if (
      activeGroupByField.value
      && responseGroupFingerprint
      && routeGroupFingerprint !== responseGroupFingerprint
      && effectiveGroupOffset <= 0
    ) {
      syncRouteListState({
        group_fp: responseGroupFingerprint,
        group_wid: groupWindowId.value || undefined,
        group_wdg: groupWindowDigest.value || undefined,
        group_wik: groupWindowIdentityKey.value || undefined,
      });
    } else if (activeGroupByField.value && !responseGroupFingerprint && routeGroupFingerprint) {
      syncRouteListState({ group_fp: undefined });
    }
    if (activeGroupByField.value && routeGroupWindowId !== (groupWindowId.value || '')) {
      syncRouteListState({ group_wid: groupWindowId.value || undefined });
    } else if (activeGroupByField.value && !groupWindowId.value && routeGroupWindowId) {
      syncRouteListState({ group_wid: undefined });
    }
    if (activeGroupByField.value && routeGroupWindowDigest !== (groupWindowDigest.value || '')) {
      syncRouteListState({ group_wdg: groupWindowDigest.value || undefined });
    } else if (activeGroupByField.value && !groupWindowDigest.value && routeGroupWindowDigest) {
      syncRouteListState({ group_wdg: undefined });
    }
    if (activeGroupByField.value && routeGroupWindowIdentityKey !== (groupWindowIdentityKey.value || '')) {
      syncRouteListState({ group_wik: groupWindowIdentityKey.value || undefined });
    } else if (activeGroupByField.value && !groupWindowIdentityKey.value && routeGroupWindowIdentityKey) {
      syncRouteListState({ group_wik: undefined });
    }
    const resultData = result.data && typeof result.data === 'object'
      ? (result.data as Record<string, unknown>)
      : {};
    listTotalCount.value = readTotalFromListResult(resultData);
    if (pageMode.value === 'list' && hasActiveField.value) {
      try {
        const domainRaw = resolveEffectiveFilterDomainRaw();
        const term = searchTerm.value.trim();
        const [allTotal, activeTotal, archivedTotal, scopeMetrics] = await Promise.all([
          fetchScopedTotal({
            model: resolvedModel,
            domain: baseDomain,
            domainRaw,
            context: requestContext,
            contextRaw: requestContextRaw,
            searchTerm: term,
            order: sortLabel.value,
          }),
          fetchScopedTotal({
            model: resolvedModel,
            domain: [...baseDomain, ['active', '=', true]],
            domainRaw,
            context: requestContext,
            contextRaw: requestContextRaw,
            searchTerm: term,
            order: sortLabel.value,
          }),
          fetchScopedTotal({
            model: resolvedModel,
            domain: [...baseDomain, ['active', '=', false]],
            domainRaw,
            context: requestContext,
            contextRaw: requestContextRaw,
            searchTerm: term,
            order: sortLabel.value,
          }),
          fetchProjectScopeMetrics({
            model: resolvedModel,
            domain: baseDomain,
            domainRaw,
            context: requestContext,
            contextRaw: requestContextRaw,
            searchTerm: term,
            order: sortLabel.value,
          }),
        ]);
        if (allTotal !== null && activeTotal !== null && archivedTotal !== null) {
          projectScopeTotals.value = {
            all: allTotal,
            active: activeTotal,
            archived: archivedTotal,
          };
        } else {
          projectScopeTotals.value = null;
        }
        projectScopeMetrics.value = scopeMetrics;
      } catch {
        projectScopeTotals.value = null;
        projectScopeMetrics.value = null;
      }
    } else {
      projectScopeTotals.value = null;
      projectScopeMetrics.value = null;
    }
    records.value = Array.isArray(resultData.records) ? (resultData.records as Array<Record<string, unknown>>) : [];
    const groupSummaryRows = Array.isArray(resultData.group_summary)
      ? (resultData.group_summary as Array<Record<string, unknown>>)
      : [];
    groupSummaryItems.value = groupSummaryRows
      .map((row) => {
        const item = row as Record<string, unknown>;
        const label = String(item.label ?? item.value ?? pageText('group_label_unset', '未设置')).trim()
          || pageText('group_label_unset', '未设置');
        const backendGroupKey = String(item.group_key || '').trim();
        return {
          key: backendGroupKey || buildGroupKey(item.field, item.value, label),
          label,
          count: Number(item.count || 0),
          domain: Array.isArray(item.domain) ? item.domain : [],
          value: item.value,
        };
      })
      .filter((item) => item.count >= 0)
      .slice(0, 12);
    groupWindowCount.value =
      groupPaging && Number.isFinite(Number(groupPaging.group_count))
        ? Math.max(0, Math.trunc(Number(groupPaging.group_count)))
        : groupSummaryItems.value.length;
    groupWindowStart.value =
      groupPaging && Number.isFinite(Number(groupPaging.window_start))
        ? Math.max(0, Math.trunc(Number(groupPaging.window_start)))
        : groupWindowCount.value > 0
          ? effectiveGroupOffset + 1
          : 0;
    groupWindowEnd.value =
      groupPaging && Number.isFinite(Number(groupPaging.window_end))
        ? Math.max(0, Math.trunc(Number(groupPaging.window_end)))
        : groupWindowCount.value > 0
          ? effectiveGroupOffset + groupWindowCount.value
          : 0;
    groupWindowTotal.value =
      groupPaging && Number.isFinite(Number(groupPaging.group_total))
        ? Math.max(0, Math.trunc(Number(groupPaging.group_total)))
        : null;
    groupWindowNextOffset.value =
      groupPaging && Number.isFinite(Number(groupPaging.next_group_offset))
        ? Math.max(0, Math.trunc(Number(groupPaging.next_group_offset)))
        : (groupPaging && Boolean(groupPaging.has_more))
          ? effectiveGroupOffset + Math.max(1, groupSummaryItems.value.length || groupWindowCount.value || 0)
          : null;
    groupWindowPrevOffset.value =
      groupPaging && Number.isFinite(Number(groupPaging.prev_group_offset))
        ? Math.max(0, Math.trunc(Number(groupPaging.prev_group_offset)))
        : effectiveGroupOffset > 0
          ? Math.max(0, effectiveGroupOffset - Math.max(1, groupSummaryItems.value.length || groupWindowCount.value || 1))
          : null;
    const groupedRowsRaw = Array.isArray(resultData.grouped_rows)
      ? (resultData.grouped_rows as Array<Record<string, unknown>>)
      : [];
    groupedRows.value = groupedRowsRaw
      .map((row) => {
        const item = row as Record<string, unknown>;
        const fallbackPageSize = Number(
          resultData.group_paging && typeof resultData.group_paging === 'object'
            ? ((resultData.group_paging as Record<string, unknown>).page_size)
            : 0,
        ) || groupSampleLimit.value || 3;
        const label = String(item.label ?? item.value ?? pageText('group_label_unset', '未设置')).trim()
          || pageText('group_label_unset', '未设置');
        const fallbackKey = buildGroupKey(item.field, item.value, label);
        return {
          key: String(item.group_key || fallbackKey),
          label,
          count: Number(item.count || 0),
          domain: Array.isArray(item.domain) ? item.domain : [],
          sampleRows: Array.isArray(item.sample_rows) ? (item.sample_rows as Array<Record<string, unknown>>) : [],
          pageOffset: normalizeGroupPageOffset(
            Number((item.page_applied_offset ?? item.page_offset ?? groupPageOffsets.value[String(item.group_key || fallbackKey)]) || 0),
            Number((item.page_size ?? item.page_limit) || fallbackPageSize),
            Number(item.count || 0),
          ),
          pageLimit: Math.max(1, Number((item.page_size ?? item.page_limit) || fallbackPageSize)),
          pageCurrent: Number(item.page_current || 0) > 0 ? Number(item.page_current || 0) : undefined,
          pageTotal: Number(item.page_total || 0) > 0 ? Number(item.page_total || 0) : undefined,
          pageRangeStart: Number(item.page_range_start || 0) >= 0 ? Number(item.page_range_start || 0) : undefined,
          pageRangeEnd: Number(item.page_range_end || 0) >= 0 ? Number(item.page_range_end || 0) : undefined,
          pageWindow: typeof item.page_window === 'object' && item.page_window !== null
            ? {
              start: Number((item.page_window as Record<string, unknown>).start || 0) >= 0
                ? Number((item.page_window as Record<string, unknown>).start || 0)
                : undefined,
              end: Number((item.page_window as Record<string, unknown>).end || 0) >= 0
                ? Number((item.page_window as Record<string, unknown>).end || 0)
                : undefined,
            }
            : undefined,
          pageHasPrev: typeof item.page_has_prev === 'boolean' ? Boolean(item.page_has_prev) : undefined,
          pageHasNext: typeof item.page_has_next === 'boolean' ? Boolean(item.page_has_next) : undefined,
          pageSyncedFromServer: Object.prototype.hasOwnProperty.call(item, 'page_offset')
            || Object.prototype.hasOwnProperty.call(item, 'page_applied_offset')
            || Object.prototype.hasOwnProperty.call(item, 'page_clamped')
            || Object.prototype.hasOwnProperty.call(item, 'page_limit')
            || Object.prototype.hasOwnProperty.call(item, 'page_size'),
          loading: false,
        };
      })
      .filter((item) => item.sampleRows.length > 0)
      .slice(0, 12);
    normalizeGroupedRouteState();
    void hydrateGroupedRowsByOffset();
    if (!activeGroupSummaryKey.value) {
      const routeGroupValue = String(route.query.group_value || '').trim();
      if (routeGroupValue) {
        const matched = groupSummaryItems.value.find((item) => item.label === routeGroupValue);
        if (matched) activeGroupSummaryKey.value = matched.key;
      }
    }
    const currentIds = new Set(
      records.value
        .map((row) => {
          const id = row.id;
          if (typeof id === 'number') return id;
          if (typeof id === 'string' && id.trim()) {
            const parsed = Number(id);
            return Number.isNaN(parsed) ? null : parsed;
          }
          return null;
        })
        .filter((id): id is number => typeof id === 'number'),
    );
    selectedIds.value = selectedIds.value.filter((id) => currentIds.has(id));
    columns.value = contractColumns;
    status.value = deriveListStatus({ error: '', recordsLength: records.value.length });
    if (result.meta?.trace_id) {
      traceId.value = String(result.meta.trace_id);
      lastTraceId.value = String(result.meta.trace_id);
    } else if (result.traceId) {
      traceId.value = String(result.traceId);
      lastTraceId.value = String(result.traceId);
    }
    lastLatencyMs.value = Date.now() - startedAt;
  } catch (err) {
    setError(err, 'failed to load list');
    listTotalCount.value = null;
    projectScopeTotals.value = null;
    projectScopeMetrics.value = null;
    traceId.value = error.value?.traceId || '';
    lastTraceId.value = error.value?.traceId || '';
    status.value = deriveListStatus({ error: error.value?.message || '', recordsLength: 0 });
    lastLatencyMs.value = Date.now() - startedAt;
  }
}

function handleRowClick(row: Record<string, unknown>) {
  const id = row.id;
  const targetModel = resolvedModelRef.value || model.value;
  if (!targetModel) {
    return;
  }
  if (typeof id === 'number') {
    router.push({
      path: `/r/${targetModel}/${id}`,
      query: { menu_id: menuId.value || undefined, action_id: actionId.value || undefined, ...resolveCarryQuery() },
    });
  } else if (typeof id === 'string' && id) {
    router.push({
      path: `/r/${targetModel}/${id}`,
      query: { menu_id: menuId.value || undefined, action_id: actionId.value || undefined, ...resolveCarryQuery() },
    });
  }
}

function reload() {
  load();
}

function handleSearch(value: string) {
  searchTerm.value = value;
  groupWindowOffset.value = 0;
  syncRouteListState();
  load();
}

function handleSort(value: string) {
  sortValue.value = value;
  groupWindowOffset.value = 0;
  syncRouteListState();
  load();
}

function handleFilter(value: 'all' | 'active' | 'archived') {
  filterValue.value = value;
  groupWindowOffset.value = 0;
  clearSelection();
  syncRouteListState();
  load();
}

function clearSelection() {
  selectedIds.value = [];
}

function handleAssigneeChange(assigneeId: number | null) {
  selectedAssigneeId.value = assigneeId;
}

function handleToggleSelection(id: number, selected: boolean) {
  const set = new Set(selectedIds.value);
  if (selected) {
    set.add(id);
  } else {
    set.delete(id);
  }
  selectedIds.value = Array.from(set);
}

function handleToggleSelectionAll(ids: number[], selected: boolean) {
  if (!ids.length) return;
  const set = new Set(selectedIds.value);
  ids.forEach((id) => {
    if (selected) {
      set.add(id);
    } else {
      set.delete(id);
    }
  });
  selectedIds.value = Array.from(set);
}

function buildIfMatchMap(ids: number[]) {
  const wanted = new Set(ids);
  const map: Record<number, string> = {};
  records.value.forEach((row) => {
    const rawId = row.id;
    const id =
      typeof rawId === 'number'
        ? rawId
        : typeof rawId === 'string' && rawId.trim()
          ? Number(rawId)
          : NaN;
    if (!Number.isFinite(id) || !wanted.has(id)) return;
    const writeDate = String((row.write_date as string | undefined) || '').trim();
    if (writeDate) {
      map[id] = writeDate;
    }
  });
  return map;
}

function buildIdempotencyKey(action: string, ids: number[], extra: Record<string, unknown> = {}) {
  const targetModel = resolvedModelRef.value || model.value || '';
  const payload = {
    model: targetModel,
    action,
    ids: [...ids].sort((a, b) => a - b),
    extra,
  };
  return `batch:${JSON.stringify(payload)}`;
}

function buildBatchErrorLine(err: unknown, fallback: { model: string; op: string; label: string }) {
  const issueCounter = new Map<string, { model: string; op: string; reasonCode: string; count: number }>();
  const issue = collectErrorContextIssue(issueCounter, err, { model: fallback.model, op: fallback.op });
  const scope = issueScopeLabel(issue);
  const reasonText = issue.reasonCode ? `${pageText('batch_error_reason_prefix', '原因=')}${issue.reasonCode}` : '';
  if (!(err instanceof ApiError)) {
    return [fallback.label, scope ? `${pageText('batch_error_scope_prefix', '范围=')}${scope}` : '', reasonText].filter(Boolean).join(' | ');
  }
  const hint = resolveSuggestedAction(err.suggestedAction, err.reasonCode, err.retryable);
  return [fallback.label, scope ? `${pageText('batch_error_scope_prefix', '范围=')}${scope}` : '', reasonText, hint].filter(Boolean).join(' | ');
}

async function handleBatchAction(action: 'archive' | 'activate' | 'delete') {
  batchMessage.value = '';
  batchDetails.value = [];
  failedCsvFileName.value = '';
  failedCsvContentB64.value = '';
  batchFailedOffset.value = 0;
  batchHasMoreFailures.value = false;
  lastBatchRequest.value = null;
  const targetModel = resolvedModelRef.value || model.value;
  if (!targetModel || !selectedIds.value.length) return;
  if (action !== 'delete' && !hasActiveField.value) {
    batchMessage.value = pageText('batch_msg_model_no_active_field', '当前模型不支持 active 字段，无法批量归档/激活');
    return;
  }
  batchBusy.value = true;
  try {
    if (action === 'delete') {
      const deleteMode = String(actionContract.value?.surface_policies?.delete_mode || 'archive').trim().toLowerCase();
      if (deleteMode !== 'archive') {
        batchMessage.value = pageText('batch_msg_delete_mode_unavailable', '当前场景暂不支持物理删除，请使用归档操作。');
        return;
      }
      const idempotencyKey = buildIdempotencyKey(action, selectedIds.value, { delete_mode: 'archive' });
      const requestContext = mergeContext(actionMeta.value?.context, resolveEffectiveRequestContext());
      const result = await batchUpdateRecords({
        model: targetModel,
        ids: selectedIds.value,
        action: 'archive',
        ifMatchMap: buildIfMatchMap(selectedIds.value),
        idempotencyKey,
        failedPreviewLimit: 12,
        failedOffset: 0,
        failedLimit: 12,
        exportFailedCsv: true,
        context: requestContext,
      });
      if (result.idempotent_replay) {
        batchMessage.value = pageText('batch_msg_idempotent_replay', '批量操作已幂等处理（重复请求被忽略）');
      } else {
        batchMessage.value = `${pageText('batch_msg_delete_archive_done_prefix', '批量删除请求已按归档处理：成功 ')}${result.succeeded}${pageText('batch_msg_done_middle', '，失败 ')}${result.failed}`;
      }
      applyBatchFailureArtifacts(result);
      clearSelection();
      await load();
      return;
    }
    const ifMatchMap = buildIfMatchMap(selectedIds.value);
    const idempotencyKey = buildIdempotencyKey(action, selectedIds.value, { active: action === 'activate' });
    const requestContext = mergeContext(actionMeta.value?.context, resolveEffectiveRequestContext());
    const result = await batchUpdateRecords({
      model: targetModel,
      ids: selectedIds.value,
      action,
      ifMatchMap,
      idempotencyKey,
      failedPreviewLimit: 12,
      failedOffset: 0,
      failedLimit: 12,
      exportFailedCsv: true,
      context: requestContext,
    });
    lastBatchRequest.value = {
      model: targetModel,
      ids: [...selectedIds.value],
      action,
      ifMatchMap,
      idempotencyKey,
      context: requestContext,
    };
    if (result.idempotent_replay) {
      batchMessage.value = pageText('batch_msg_idempotent_replay', '批量操作已幂等处理（重复请求被忽略）');
    } else {
      batchMessage.value =
        action === 'activate'
          ? `${pageText('batch_msg_activate_done_prefix', '批量激活完成：成功 ')}${result.succeeded}${pageText('batch_msg_done_middle', '，失败 ')}${result.failed}`
          : `${pageText('batch_msg_archive_done_prefix', '批量归档完成：成功 ')}${result.succeeded}${pageText('batch_msg_done_middle', '，失败 ')}${result.failed}`;
    }
    applyBatchFailureArtifacts(result);
    clearSelection();
    await load();
  } catch (err) {
    setError(err, 'batch operation failed');
    batchMessage.value = action === 'activate'
      ? pageText('batch_msg_activate_failed', '批量激活失败')
      : action === 'archive'
        ? pageText('batch_msg_archive_failed', '批量归档失败')
        : pageText('batch_msg_delete_failed', '批量删除失败');
    batchDetails.value = [{
      text: buildBatchErrorLine(err, {
        model: targetModel,
        op: action,
        label: action === 'activate'
          ? pageText('batch_label_activate', '批量激活')
          : action === 'archive'
            ? pageText('batch_label_archive', '批量归档')
            : pageText('batch_label_delete', '批量删除'),
      }),
    }];
    failedCsvFileName.value = '';
    failedCsvContentB64.value = '';
    batchFailedOffset.value = 0;
    batchHasMoreFailures.value = false;
    lastBatchRequest.value = null;
  } finally {
    batchBusy.value = false;
  }
}

async function handleBatchAssign(assigneeId: number) {
  batchMessage.value = '';
  batchDetails.value = [];
  failedCsvFileName.value = '';
  failedCsvContentB64.value = '';
  batchFailedOffset.value = 0;
  batchHasMoreFailures.value = false;
  lastBatchRequest.value = null;
  const targetModel = resolvedModelRef.value || model.value;
  if (!targetModel || !selectedIds.value.length) return;
  if (!hasAssigneeField.value) {
    batchMessage.value = pageText('batch_msg_model_no_assignee_field', '当前模型不支持负责人字段，无法批量指派');
    return;
  }
  if (!assigneeId) {
    batchMessage.value = pageText('batch_msg_select_assignee_first', '请先选择负责人');
    return;
  }
  batchBusy.value = true;
  try {
    const ifMatchMap = buildIfMatchMap(selectedIds.value);
    const idempotencyKey = buildIdempotencyKey('assign', selectedIds.value, { assignee_id: assigneeId });
    const requestContext = mergeContext(actionMeta.value?.context, resolveEffectiveRequestContext());
    const result = await batchUpdateRecords({
      model: targetModel,
      ids: selectedIds.value,
      action: 'assign',
      assigneeId,
      ifMatchMap,
      idempotencyKey,
      failedPreviewLimit: 12,
      failedOffset: 0,
      failedLimit: 12,
      exportFailedCsv: true,
      context: requestContext,
    });
    lastBatchRequest.value = {
      model: targetModel,
      ids: [...selectedIds.value],
      action: 'assign',
      assigneeId,
      ifMatchMap,
      idempotencyKey,
      context: requestContext,
    };
    const assignee = assigneeOptions.value.find((opt) => opt.id === assigneeId)?.name || `#${assigneeId}`;
    if (result.idempotent_replay) {
      batchMessage.value = `${pageText('batch_msg_assign_idempotent_prefix', '批量指派给 ')}${assignee}${pageText('batch_msg_assign_idempotent_suffix', ' 已幂等处理（重复请求被忽略）')}`;
    } else {
      batchMessage.value = `${pageText('batch_msg_assign_done_prefix', '批量指派给 ')}${assignee}${pageText('batch_msg_assign_done_middle', '：成功 ')}${result.succeeded}${pageText('batch_msg_done_middle', '，失败 ')}${result.failed}`;
    }
    applyBatchFailureArtifacts(result);
    clearSelection();
    await load();
  } catch (err) {
    setError(err, 'batch assign failed');
    batchMessage.value = pageText('batch_msg_assign_failed', '批量指派失败');
    batchDetails.value = [{
      text: buildBatchErrorLine(err, {
        model: targetModel,
        op: 'assign',
        label: pageText('batch_label_assign', '批量指派'),
      }),
    }];
    failedCsvFileName.value = '';
    failedCsvContentB64.value = '';
    batchFailedOffset.value = 0;
    batchHasMoreFailures.value = false;
    lastBatchRequest.value = null;
  } finally {
    batchBusy.value = false;
  }
}

function handleBatchExport(scope: 'selected' | 'all') {
  void exportByBackend(scope);
}

async function exportByBackend(scope: 'selected' | 'all') {
  batchMessage.value = '';
  batchDetails.value = [];
  failedCsvFileName.value = '';
  failedCsvContentB64.value = '';
  const targetModel = resolvedModelRef.value || model.value;
  if (!targetModel) return;
  if (scope === 'selected' && !selectedIds.value.length) {
    batchMessage.value = pageText('batch_msg_no_selected_records_export', '没有可导出的选中记录');
    return;
  }
  batchBusy.value = true;
  try {
    const ids = scope === 'selected' ? selectedIds.value : [];
    const domain =
      scope === 'all'
        ? mergeActiveFilter(
            mergeSceneDomain(mergeSceneDomain(actionMeta.value?.domain, scene.value?.filters), resolveEffectiveFilterDomain()),
          )
        : [];
    const fields = columns.value.length ? ['id', ...columns.value.filter((col) => col !== 'id')] : ['id', 'name'];
    const result = await exportRecordsCsv({
      model: targetModel,
      fields,
      ids,
      domain,
      order: sortLabel.value,
      limit: scope === 'all' ? 10000 : 5000,
      context: mergeContext(actionMeta.value?.context, resolveEffectiveRequestContext()),
    });
    if (!result.content_b64) {
      batchMessage.value = pageText('batch_msg_no_records_export', '没有可导出的记录');
      return;
    }
    downloadCsvBase64(result.file_name, result.mime_type, result.content_b64);
    batchMessage.value = `${pageText('batch_msg_export_done_prefix', '已导出 ')}${result.count}${pageText('batch_msg_export_done_suffix', ' 条记录')}`;
  } catch (err) {
    setError(err, 'batch export failed');
    batchMessage.value = pageText('batch_msg_export_failed', '批量导出失败');
    batchDetails.value = [{
      text: buildBatchErrorLine(err, {
        model: targetModel,
        op: 'export_csv',
        label: pageText('batch_label_export', '批量导出'),
      }),
    }];
  } finally {
    batchBusy.value = false;
  }
}

function handleDownloadFailedCsv() {
  if (!failedCsvContentB64.value) return;
  downloadCsvBase64(failedCsvFileName.value || 'batch_failed.csv', 'text/csv', failedCsvContentB64.value);
}

async function handleLoadMoreFailures() {
  if (!lastBatchRequest.value || !batchHasMoreFailures.value) return;
  const req = lastBatchRequest.value;
  batchBusy.value = true;
  try {
    const result = await batchUpdateRecords({
      model: req.model,
      ids: req.ids,
      action: req.action,
      assigneeId: req.assigneeId,
      ifMatchMap: req.ifMatchMap,
      idempotencyKey: req.idempotencyKey,
      failedPreviewLimit: batchFailedLimit.value,
      failedOffset: batchFailedOffset.value,
      failedLimit: batchFailedLimit.value,
      exportFailedCsv: false,
      context: req.context,
    });
    applyBatchFailureArtifacts(result, { append: true });
  } catch (err) {
    setError(err, 'load more failures failed');
    batchDetails.value = [{
      text: buildBatchErrorLine(err, {
        model: req.model,
        op: req.action,
        label: pageText('batch_label_load_more_failed', '加载更多失败'),
      }),
    }];
  } finally {
    batchBusy.value = false;
  }
}

onMounted(async () => {
  applyRoutePreset();
  await load();
});

watch(
  () => route.fullPath,
  () => {
    if (applyRoutePreset()) {
      void load();
    }
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

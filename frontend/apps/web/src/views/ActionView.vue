<template>
  <section class="page">
    <!-- Page intent: 在列表场景中先判断状态，再给出下一步可执行动作。 -->
    <section v-if="appliedPresetLabel" class="route-preset">
      <p>已应用推荐筛选：{{ appliedPresetLabel }}<span v-if="routeContextSource">（来源：{{ routeContextSource }}）</span></p>
      <button class="clear-btn" @click="clearRoutePreset">清除推荐</button>
    </section>
    <section class="focus-strip">
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
    <section v-if="contractPrimaryFilterChips.length || contractOverflowFilterChips.length" class="contract-block">
      <p class="contract-label">快速筛选</p>
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
          清除
        </button>
        <button
          v-if="contractOverflowFilterChips.length"
          class="contract-chip ghost"
          :disabled="status === 'loading' || batchBusy"
          @click="showMoreContractFilters = !showMoreContractFilters"
        >
          {{ showMoreContractFilters ? '收起更多筛选' : `更多筛选 (${contractOverflowFilterChips.length})` }}
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
    <section v-if="savedFilterPrimaryChips.length || savedFilterOverflowChips.length" class="contract-block">
      <p class="contract-label">已保存筛选</p>
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
          清除
        </button>
        <button
          v-if="savedFilterOverflowChips.length"
          class="contract-chip ghost"
          :disabled="status === 'loading' || batchBusy"
          @click="showMoreSavedFilters = !showMoreSavedFilters"
        >
          {{ showMoreSavedFilters ? '收起更多筛选' : `更多筛选 (${savedFilterOverflowChips.length})` }}
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
    <section v-if="groupByPrimaryChips.length || groupByOverflowChips.length" class="contract-block">
      <p class="contract-label">分组查看</p>
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
          清除
        </button>
        <button
          v-if="groupByOverflowChips.length"
          class="contract-chip ghost"
          :disabled="status === 'loading' || batchBusy"
          @click="showMoreGroupBy = !showMoreGroupBy"
        >
          {{ showMoreGroupBy ? '收起更多分组' : `更多分组 (${groupByOverflowChips.length})` }}
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
      v-if="groupSummaryItems.length"
      :items="groupSummaryItems"
      :group-by-label="activeGroupByLabel"
      :active-key="activeGroupSummaryKey"
      :on-pick="handleGroupSummaryPick"
      :on-clear="clearGroupSummaryDrilldown"
    />
    <section v-if="contractPrimaryActions.length || contractOverflowActions.length" class="contract-block">
      <p class="contract-label">快捷操作</p>
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
          {{ showMoreContractActions ? '收起更多操作' : `更多操作 (${contractOverflowActions.length})` }}
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
      :field-labels="contractColumnLabels"
      :title-field="kanbanTitleField"
      :subtitle="subtitle"
      :status-label="statusLabel"
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
      :selected-ids="selectedIds"
      :batch-message="batchMessage"
      :batch-details="batchDetails"
      :failed-csv-available="Boolean(failedCsvContentB64)"
      :has-more-failures="batchHasMoreFailures"
      :show-assign="hasAssigneeField"
      :assignee-options="assigneeOptions"
      :selected-assignee-id="selectedAssigneeId"
      :list-profile="listProfile"
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
    <section v-else class="advanced-view">
      <header class="advanced-view-head">
        <h3>{{ advancedViewTitle }}</h3>
        <p>{{ advancedViewHint }}</p>
      </header>
      <div class="advanced-contract">
        <p class="contract-label">契约摘要</p>
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
    <section v-if="pageStatus === 'empty'" class="empty-next">
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
      :visible="showHud"
      title="View Context"
      :entries="hudEntries"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, inject, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { batchUpdateRecords, exportRecordsCsv, listRecords, listRecordsRaw } from '../api/data';
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
import { parseContractContextRaw, resolveContractReadRight, resolveContractViewMode } from '../app/contractActionRuntime';
import { detectObjectMethodFromActionKey, normalizeActionKind, toPositiveInt } from '../app/contractRuntime';
import type { Scene, SceneListProfile } from '../app/resolvers/sceneRegistry';
import { readWorkspaceContext, stripWorkspaceContext } from '../app/workspaceContext';
import { pickContractNavQuery } from '../app/navigationContext';
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

const status = ref<'idle' | 'loading' | 'ok' | 'empty' | 'error'>('idle');
const traceId = ref('');
const lastTraceId = ref('');
const records = ref<Array<Record<string, unknown>>>([]);
const searchTerm = ref('');
const sortValue = ref('');
const filterValue = ref<'all' | 'active' | 'archived'>('all');
const columns = ref<string[]>([]);
const kanbanFields = ref<string[]>([]);
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
const activeGroupSummaryKey = ref('');
const activeGroupSummaryDomain = ref<unknown[]>([]);
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

const actionId = computed(() => Number(route.params.actionId));
const actionMeta = computed(() => session.currentAction);

const model = computed(() => actionMeta.value?.model ?? '');
const injectedTitle = inject('pageTitle', computed(() => ''));
const menuId = computed(() => Number(route.query.menu_id ?? 0));
const contractViewType = ref('');
const contractReadAllowed = ref(true);
const contractWarningCount = ref(0);
const contractDegraded = ref(false);
const actionContract = ref<ActionContractLoose | null>(null);
const resolvedModelRef = ref('');
const activeContractFilterKey = ref('');
const activeSavedFilterKey = ref('');
const activeGroupByField = ref('');
const contractLimit = ref(40);
const showMoreContractActions = ref(false);
const showMoreContractFilters = ref(false);
const showMoreSavedFilters = ref(false);
const showMoreGroupBy = ref(false);
const viewMode = computed(() => {
  const mode = String(contractViewType.value || '')
    .split(',')
    .map((item) => item.trim().toLowerCase())
    .find(Boolean) || '';
  if (mode === 'kanban') return 'kanban';
  if (mode === 'list' || mode === 'tree') return 'tree';
  if (mode === 'pivot' || mode === 'graph' || mode === 'calendar' || mode === 'gantt' || mode === 'activity' || mode === 'dashboard') {
    return mode;
  }
  return '';
});
const sortLabel = computed(() => sortValue.value || 'id asc');
const surfaceKey = computed(() => `${sceneKey.value} ${model.value} ${pageTitle.value}`.toLowerCase());
const surfaceKind = computed<'risk' | 'contract' | 'cost' | 'project' | 'generic'>(() => {
  const key = surfaceKey.value;
  if (key.includes('risk') || key.includes('风险')) return 'risk';
  if (key.includes('contract') || key.includes('合同')) return 'contract';
  if (key.includes('cost') || key.includes('成本')) return 'cost';
  if (key.includes('project') || key.includes('项目')) return 'project';
  return 'generic';
});
const sortOptions = computed(() => {
  if (surfaceKind.value === 'risk' || surfaceKind.value === 'cost') {
    return [
      { label: '优先级↓ / 截止日↑', value: 'priority desc,deadline asc,write_date desc' },
      { label: '截止日↑ / 更新时间↓', value: 'deadline asc,write_date desc' },
      { label: '更新时间↓ / ID↓', value: 'write_date desc,id desc' },
    ];
  }
  return [
    { label: '更新时间↓ / 名称↑', value: 'write_date desc,name asc' },
    { label: '更新时间↑ / 名称↑', value: 'write_date asc,name asc' },
    { label: '名称↑ / 更新时间↓', value: 'name asc,write_date desc' },
    { label: '名称↓ / 更新时间↓', value: 'name desc,write_date desc' },
  ];
});
const subtitle = computed(() => `${records.value.length} 条记录 · 排序：${sortLabel.value}`);
const kanbanTitleField = computed(() => {
  const candidates = ['display_name', 'name'];
  const found = candidates.find((field) => kanbanFields.value.includes(field));
  return found || kanbanFields.value[0] || 'id';
});
const statusLabel = computed(() => {
  if (status.value === 'loading') return '加载中';
  if (status.value === 'error') return '加载失败';
  if (status.value === 'empty') return '暂无数据';
  return '已就绪';
});
const pageStatus = computed<'loading' | 'ok' | 'empty' | 'error'>(() =>
  status.value === 'idle' ? 'loading' : status.value,
);
const advancedViewTitle = computed(() => {
  const labels: Record<string, string> = {
    pivot: '数据透视视图',
    graph: '图表视图',
    calendar: '日历视图',
    gantt: '甘特视图',
    activity: '活动视图',
    dashboard: '仪表板视图',
  };
  return labels[viewMode.value] || '高级视图';
});
const advancedViewHint = computed(() => {
  const hints: Record<string, string> = {
    pivot: '当前为可读降级视图，可查看核心统计记录并继续下钻到列表/表单。',
    graph: '当前为可读降级视图，可查看核心指标记录并继续下钻到列表/表单。',
    calendar: '当前为可读降级视图，可查看时间相关记录并继续下钻到列表/表单。',
    gantt: '当前为可读降级视图，可查看进度相关记录并继续下钻到列表/表单。',
    activity: '当前为可读降级视图，可查看活动记录并继续下钻到列表/表单。',
    dashboard: '当前为可读降级视图，可查看关键记录并继续下钻到列表/表单。',
  };
  return hints[viewMode.value] || '当前视图使用可读降级渲染。';
});
const pageTitle = computed(() => {
  const contractTitle = String(actionContract.value?.head?.title || '').trim();
  if (contractTitle) return contractTitle;
  return injectedTitle?.value || actionMeta.value?.name || '工作台';
});
const surfaceIntent = computed<SurfaceIntent>(() => {
  const key = surfaceKey.value;
  if (key.includes('risk') || key.includes('风险')) {
    return {
      title: '风险驾驶舱：先处理严重与逾期风险',
      summary: '优先完成分派、关闭或发起审批，避免风险停留在“仅可见”状态。',
      actions: [
        { label: '待我处理风险', to: '/my-work', query: { section: 'todo', source: 'project.risk', search: '风险' } },
        { label: '打开风险场景', to: '/s/projects.dashboard' },
      ],
      emptyTitle: '当前暂无风险记录',
      emptyHint: '建议转到“我的工作”处理风险待办，或进入风险驾驶舱继续巡检。',
      primaryAction: { label: '处理风险待办', to: '/my-work', query: { section: 'todo', source: 'project.risk', search: '风险' } },
      secondaryAction: { label: '进入风险驾驶舱', to: '/s/projects.dashboard' },
    };
  }
  if (key.includes('contract') || key.includes('合同')) {
    return {
      title: '合同执行：优先识别付款与变更风险',
      summary: '先看执行率与付款状态，再进入异常合同处理。',
      actions: [
        { label: '处理合同待办', to: '/my-work', query: { section: 'todo', search: '合同' } },
        { label: '查看风险驾驶舱', to: '/s/projects.dashboard' },
      ],
      emptyTitle: '当前暂无合同记录',
      emptyHint: '可前往“我的工作”查看合同待办，或进入风险驾驶舱追踪履约风险。',
      primaryAction: { label: '处理合同待办', to: '/my-work', query: { section: 'todo', search: '合同' } },
      secondaryAction: { label: '查看风险驾驶舱', to: '/s/projects.dashboard' },
    };
  }
  if (key.includes('cost') || key.includes('成本')) {
    return {
      title: '成本执行：先回答是否超支',
      summary: '优先关注超支金额与超支项，再下钻到具体偏差来源。',
      actions: [
        { label: '处理成本待办', to: '/my-work', query: { section: 'todo', search: '成本' } },
        { label: '查看风险驾驶舱', to: '/s/projects.dashboard' },
      ],
      emptyTitle: '当前暂无成本记录',
      emptyHint: '可前往“我的工作”处理成本待办，或进入风险驾驶舱继续巡检。',
      primaryAction: { label: '处理超支待办', to: '/my-work', query: { section: 'todo', search: '成本' } },
      secondaryAction: { label: '查看风险驾驶舱', to: '/s/projects.dashboard' },
    };
  }
  if (key.includes('project') || key.includes('项目')) {
    return {
      title: '项目视角：先判断是否可控',
      summary: '优先查看风险、审批与经营指标，再决定下一步动作。',
      actions: [
        { label: '查看项目待办', to: '/my-work', query: { section: 'todo', search: '项目' } },
        { label: '进入风险驾驶舱', to: '/s/projects.dashboard' },
      ],
      emptyTitle: '当前暂无项目记录',
      emptyHint: '建议进入“我的工作”处理项目待办，或去风险驾驶舱查看全局状态。',
      primaryAction: { label: '查看项目待办', to: '/my-work', query: { section: 'todo', search: '项目' } },
      secondaryAction: { label: '进入风险驾驶舱', to: '/s/projects.dashboard' },
    };
  }
  return {
    title: '业务列表：先看状态，再执行动作',
    summary: '通过快速筛选与快捷操作，优先处理最关键事项。',
    actions: [
      { label: '工作台', to: '/' },
      { label: '我的工作', to: '/my-work' },
    ],
    emptyTitle: '当前视图暂无数据',
    emptyHint: '建议切换到我的工作或风险驾驶舱继续处理。',
    primaryAction: { label: '去我的工作', to: '/my-work' },
    secondaryAction: { label: '去风险驾驶舱', to: '/s/projects.dashboard' },
  };
});
const emptyReasonText = computed(() => {
  if (searchTerm.value.trim() || activeContractFilterKey.value) {
    return '可能由当前筛选条件导致无数据，建议先清除筛选后重试。';
  }
  return '可能因为暂无业务数据、当前角色权限受限，或数据尚未生成。';
});
const showHud = computed(() => isHudEnabled(route));
const errorMessage = computed(() => (error.value?.code ? `code=${error.value.code} · ${error.value.message}` : error.value?.message || ''));
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
const listProfile = computed<SceneListProfile | null>(() => (scene.value?.list_profile as SceneListProfile) || null);
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
  const rows = actionContract.value?.search?.filters;
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
  const rows = actionContract.value?.search?.group_by;
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
  const payload = parseContractContextRaw(row.payload);
  const kind = normalizeActionKind(row.kind);
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
        ? '请选择 1 条记录'
        : '请先选择记录'
    : '权限不足';
  return {
    key,
    label: rawLabel,
    kind,
    actionId,
    methodName,
    model: String(row.target_model || row.model || resolvedModelRef.value || model.value || '').trim(),
    target: String(payload.target || '').trim(),
    url: String(payload.url || '').trim(),
    selection,
    context: parseContractContextRaw(payload.context_raw),
    domainRaw: String(payload.domain_raw || '').trim(),
    enabled,
    hint,
  };
}
const contractActionButtons = computed<ContractActionButton[]>(() => {
  const contract = actionContract.value;
  if (!contract) return [];
  const merged: Array<Record<string, unknown>> = [];
  const contractButtons = Array.isArray(contract.buttons) ? (contract.buttons as Array<Record<string, unknown>>) : [];
  if (contractButtons.length) {
    merged.push(...contractButtons);
  } else {
    if (Array.isArray(contract.toolbar?.header)) merged.push(...(contract.toolbar?.header as Array<Record<string, unknown>>));
    if (Array.isArray(contract.toolbar?.sidebar)) merged.push(...(contract.toolbar?.sidebar as Array<Record<string, unknown>>));
    if (Array.isArray(contract.toolbar?.footer)) merged.push(...(contract.toolbar?.footer as Array<Record<string, unknown>>));
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
    const basic = all.filter((item) => /创建|保存|submit|create|save/i.test(item.label));
    const workflow = all.filter((item) => /阶段|审批|workflow|transition/i.test(item.label));
    const drilldown = all.filter((item) => /查看|列表|看板|open|view/i.test(item.label));
    const other = all.filter((item) => !basic.includes(item) && !workflow.includes(item) && !drilldown.includes(item));
    if (basic.length) grouped.push({ key: 'basic', label: '基础操作', actions: basic });
    if (workflow.length) grouped.push({ key: 'workflow', label: '流程推进', actions: workflow });
    if (drilldown.length) grouped.push({ key: 'drilldown', label: '业务查看', actions: drilldown });
    if (other.length) grouped.push({ key: 'other', label: '更多操作', actions: other });
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

function resolveActionViewType(_meta: unknown, contract: unknown) {
  const typedContract = contract as ActionContractLoose;
  const fromHead = String(typedContract.head?.view_type || '').trim();
  if (fromHead) return fromHead;
  const fromContract = String(typedContract.view_type || '').trim();
  if (fromContract) return fromContract;
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
    appliedPresetLabel.value = `契约筛选: ${presetFilter}`;
    setIfDiff(searchTerm, routeSearch || presetFilter);
  }
  if (savedFilter) {
    appliedPresetLabel.value = appliedPresetLabel.value || `保存筛选: ${savedFilter}`;
    setIfDiff(activeSavedFilterKey, savedFilter);
  } else {
    setIfDiff(activeSavedFilterKey, '');
  }
  if (groupBy) {
    setIfDiff(activeGroupByField, groupBy);
  } else {
    setIfDiff(activeGroupByField, '');
  }
  if (groupValue && !routeSearch) {
    setIfDiff(searchTerm, groupValue);
  } else if (!groupValue) {
    activeGroupSummaryKey.value = '';
    activeGroupSummaryDomain.value = [];
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
  router.replace({ name: 'action', params: route.params, query: nextQuery }).catch(() => {});
}

function syncRouteListState(extra?: Record<string, unknown>) {
  const query = pickContractNavQuery(route.query as Record<string, unknown>, {
    search: searchTerm.value.trim() || undefined,
    order: sortValue.value.trim() || undefined,
    active_filter: filterValue.value !== 'all' ? filterValue.value : undefined,
    ...extra,
  });
  router.replace({ name: 'action', params: route.params, query }).catch(() => {});
}

function applyContractFilter(key: string) {
  if (!key) return;
  activeContractFilterKey.value = key;
  showMoreContractFilters.value = false;
  clearSelection();
  const query = pickContractNavQuery(route.query as Record<string, unknown>, { preset_filter: key });
  router.replace({ name: 'action', params: route.params, query }).catch(() => {});
  void load();
}

function applySavedFilter(key: string) {
  if (!key) return;
  activeSavedFilterKey.value = key;
  showMoreSavedFilters.value = false;
  clearSelection();
  const query = pickContractNavQuery(route.query as Record<string, unknown>, { saved_filter: key });
  router.replace({ name: 'action', params: route.params, query }).catch(() => {});
  void load();
}

function clearContractFilter() {
  activeContractFilterKey.value = '';
  showMoreContractFilters.value = false;
  clearSelection();
  const query = pickContractNavQuery(route.query as Record<string, unknown>, { preset_filter: undefined });
  router.replace({ name: 'action', params: route.params, query }).catch(() => {});
  void load();
}

function clearSavedFilter() {
  activeSavedFilterKey.value = '';
  showMoreSavedFilters.value = false;
  clearSelection();
  const query = pickContractNavQuery(route.query as Record<string, unknown>, { saved_filter: undefined });
  router.replace({ name: 'action', params: route.params, query }).catch(() => {});
  void load();
}

function applyGroupBy(field: string) {
  if (!field) return;
  activeGroupByField.value = field;
  activeGroupSummaryKey.value = '';
  activeGroupSummaryDomain.value = [];
  showMoreGroupBy.value = false;
  clearSelection();
  const query = pickContractNavQuery(route.query as Record<string, unknown>, { group_by: field, group_value: undefined });
  router.replace({ name: 'action', params: route.params, query }).catch(() => {});
  void load();
}

function clearGroupBy() {
  activeGroupByField.value = '';
  activeGroupSummaryKey.value = '';
  activeGroupSummaryDomain.value = [];
  showMoreGroupBy.value = false;
  clearSelection();
  const query = pickContractNavQuery(route.query as Record<string, unknown>, { group_by: undefined, group_value: undefined });
  router.replace({ name: 'action', params: route.params, query }).catch(() => {});
  void load();
}

function handleGroupSummaryPick(item: GroupSummaryItem) {
  if (!item) return;
  activeGroupSummaryKey.value = item.key;
  activeGroupSummaryDomain.value = Array.isArray(item.domain) ? item.domain : [];
  searchTerm.value = item.label || '';
  syncRouteListState({ search: searchTerm.value.trim() || undefined, group_value: item.label || undefined });
  void load();
}

function clearGroupSummaryDrilldown() {
  activeGroupSummaryKey.value = '';
  activeGroupSummaryDomain.value = [];
  const q = pickContractNavQuery(route.query as Record<string, unknown>, { group_value: undefined });
  router.replace({ name: 'action', params: route.params, query: q }).catch(() => {});
  void load();
}

function openFocusAction(action: FocusNavAction | string) {
  const path = typeof action === 'string' ? action : action.to;
  const query = typeof action === 'string' ? undefined : action.query;
  router.push({ path, query: query ? { ...resolveWorkspaceContextQuery(), ...query } : undefined }).catch(() => {});
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
    const retryTag = item.retryable === true ? '可重试' : item.retryable === false ? '不可重试' : '';
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

function extractColumnsFromContract(contract: Awaited<ReturnType<typeof loadActionContract>>) {
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
      pick(['title', 'name', '风险', '事项']),
      pick(['priority', 'severity', '优先级', '严重']),
      pick(['deadline', 'date_deadline', '截止', '逾期']),
      pick(['user_id', 'owner', 'assignee', '负责人', '分派']),
      pick(['state', 'stage', 'status', '状态']),
      pick(['reason', '原因']),
    );
  } else if (surfaceKind.value === 'contract') {
    buckets.push(
      pick(['amount_total', 'contract_amount', '金额', '合同额']),
      pick(['execute', 'execution', 'progress', '执行率']),
      pick(['paid', 'payment', '付款', '支付']),
      pick(['risk', '风险', 'alert']),
      pick(['change', '变更', 'write_date', '最近']),
      pick(['title', 'name', '合同']),
    );
  } else if (surfaceKind.value === 'cost') {
    buckets.push(
      pick(['cost', '执行率', 'rate']),
      pick(['over', 'overrun', '超支', '偏差']),
      pick(['count', '项数']),
      pick(['deadline', '截止']),
      pick(['priority', '优先级']),
      pick(['title', 'name', '项目']),
    );
  } else if (surfaceKind.value === 'project') {
    buckets.push(
      pick(['title', 'name', '项目']),
      pick(['state', 'stage', 'status', '状态', '阶段']),
      pick(['risk', '风险']),
      pick(['payment', '付款']),
      pick(['output', '产值']),
      pick(['cost', '成本']),
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
  return String(row.display_name || row.name || row.id || '记录').trim();
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
  if (!entries.length) return '无附加字段';
  return entries.join(' · ');
}

function resolveModelFromContract(contract: Awaited<ReturnType<typeof loadActionContract>>) {
  const typed = contract as ActionContractLoose;
  const direct = typed.model;
  if (typeof direct === 'string' && direct.trim()) {
    return direct.trim();
  }
  const headModel = typed.head?.model;
  if (typeof headModel === 'string' && headModel.trim()) {
    return headModel.trim();
  }
  const viewModel = typed.views?.tree?.model || typed.views?.form?.model || typed.views?.kanban?.model;
  if (typeof viewModel === 'string' && viewModel.trim()) {
    return viewModel.trim();
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
      query: {
        menu_id: menuId.value || undefined,
        action_id: actionId.value || undefined,
        reason: ErrorCodes.ACT_UNSUPPORTED_TYPE,
        diag: 'act_url_empty',
        diag_action_type: actionType || undefined,
        diag_contract_type: contractType || undefined,
      },
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

async function runContractAction(action: ContractActionButton) {
  if (!action.enabled) return;
  if (action.kind === 'open') {
    if (action.actionId) {
      await router.push({
        name: 'action',
        params: { actionId: action.actionId },
        query: {
          menu_id: menuId.value || undefined,
          action_id: action.actionId,
          ...resolveCarryQuery(),
        },
      });
      return;
    }
    if (action.url) {
      const navUrl = resolveNavigationUrl(action.url);
      window.open(navUrl, action.target === 'self' ? '_self' : '_blank', 'noopener,noreferrer');
      return;
    }
    batchMessage.value = '契约动作缺少 action_id，无法打开目标页面';
    return;
  }

  const ids = resolveSelectedIdsForAction(action.selection);
  if (action.selection !== 'none' && !ids.length) {
    batchMessage.value = action.selection === 'single' ? '请选择 1 条记录后再执行' : '请先选择记录后再执行';
    return;
  }
  if (!action.model) {
    batchMessage.value = '契约动作缺少 model，无法执行';
    return;
  }
  const contextRecordId = resolveActionContextRecordId();
  const execIds = ids.length ? ids : contextRecordId ? [contextRecordId] : [];
  if (!execIds.length) {
    batchMessage.value = '当前动作需要记录上下文，暂不支持无记录执行';
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
          await router.push({
            name: 'action',
            params: { actionId: response.result.action_id },
            query: {
              menu_id: menuId.value || undefined,
              action_id: response.result.action_id,
              ...resolveCarryQuery(),
            },
          });
          return;
        }
        successCount += 1;
      } catch {
        failureCount += 1;
      }
    }
    batchMessage.value = `契约动作执行完成：成功 ${successCount}，失败 ${failureCount}`;
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
  } catch {
    assigneeOptions.value = [];
    selectedAssigneeId.value = null;
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
  groupSummaryItems.value = [];
  columns.value = [];
  kanbanFields.value = [];
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
    contractReadAllowed.value = resolveContractReadRight(typedContract);
    contractWarningCount.value = Array.isArray(typedContract.warnings) ? typedContract.warnings.length : 0;
    contractDegraded.value = Boolean(typedContract.degraded);
    if (!contractReadAllowed.value) {
      await router.replace({
        name: 'workbench',
        query: {
          menu_id: menuId.value || undefined,
          action_id: actionId.value || undefined,
          reason: ErrorCodes.CAPABILITY_MISSING,
          diag: 'contract_read_forbidden',
        },
      });
      return;
    }
    if (isUrlAction(meta, contract)) {
      await redirectUrlAction(meta, contract);
      return;
    }
    if (!sortValue.value) {
      const typedContract = contract as ActionContractLoose;
      const searchDefaults = typedContract.search?.defaults;
      const searchOrder = searchDefaults?.order;
      const viewOrder = typedContract.views?.tree?.order || typedContract.ui_contract?.views?.tree?.order;
      const metaOrder = (meta as ActionMetaLoose | undefined)?.order;
      const order = scene.value?.default_sort || searchOrder || viewOrder || metaOrder;
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
        query: {
          menu_id: menuId.value || undefined,
          action_id: actionId.value || undefined,
          reason: ErrorCodes.CAPABILITY_MISSING,
          missing: policy.missing.join(','),
        },
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
          query: {
            menu_id: menuId.value || undefined,
            action_id: actionId.value || undefined,
            reason: ErrorCodes.ACT_NO_MODEL,
          },
        });
        return;
      }
      if (!isWindowAction(meta)) {
        const actionType = getActionType(meta);
        const typedContract = contract as ActionContractLoose;
        const contractType = String(typedContract.data?.type || '').toLowerCase();
        const contractUrl = String(typedContract.data?.url || '');
        const metaUrl = String((meta as ActionMetaLoose | undefined)?.url || '');
        await router.replace({
          name: 'workbench',
          query: {
            menu_id: menuId.value || undefined,
            action_id: actionId.value || undefined,
            reason: ErrorCodes.ACT_UNSUPPORTED_TYPE,
            diag: 'non_window_action',
            diag_action_type: actionType || undefined,
            diag_contract_type: contractType || undefined,
            diag_contract_url: contractUrl || undefined,
            diag_meta_url: metaUrl || undefined,
          },
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
    const contractColumns = convergeColumnsForSurface(extractColumnsFromContract(contract), typedContract.fields || {});
    const kanbanContractFields = extractKanbanFields(contract);
    const advancedContractFields = extractAdvancedViewFields(contract, viewMode.value);
    advancedFields.value = advancedContractFields;
    kanbanFields.value = kanbanContractFields;
    const fieldMap = typedContract.fields || {};
    hasActiveField.value = Boolean(fieldMap && typeof fieldMap === 'object' && 'active' in fieldMap);
    hasAssigneeField.value = Boolean(fieldMap && typeof fieldMap === 'object' && 'user_id' in fieldMap);
    await loadAssigneeOptions();
    const requestedFields =
      viewMode.value === 'kanban'
        ? kanbanContractFields
        : viewMode.value === 'tree'
          ? resolveRequestedFields(contractColumns, listProfile.value)
          : advancedContractFields;
    if (viewMode.value === 'kanban' && !kanbanContractFields.length) {
      setError(new Error('missing contract fields for kanban view'), 'missing contract fields for kanban view');
      status.value = deriveListStatus({ error: error.value?.message || '', recordsLength: 0 });
      return;
    }
    if (viewMode.value === 'tree' && !contractColumns.length) {
      setError(new Error('missing contract columns for list/tree view'), 'missing contract columns for list/tree view');
      status.value = deriveListStatus({ error: error.value?.message || '', recordsLength: 0 });
      return;
    }
    const result = await listRecordsRaw({
      model: resolvedModel,
      fields: requestedFields.length ? requestedFields : ['id', 'name'],
      domain: mergeActiveFilter(mergeSceneDomain(mergeSceneDomain(meta?.domain, scene.value?.filters), resolveEffectiveFilterDomain())),
      domain_raw: resolveEffectiveFilterDomainRaw(),
      group_by: activeGroupByField.value || undefined,
      context: mergeContext(meta?.context, resolveEffectiveRequestContext()),
      context_raw: resolveEffectiveRequestContextRaw(),
      limit: contractLimit.value,
      offset: 0,
      search_term: searchTerm.value.trim() || undefined,
      order: sortLabel.value,
    });
    records.value = result.data?.records ?? [];
    groupSummaryItems.value = (Array.isArray(result.data?.group_summary) ? result.data?.group_summary : [])
      .map((row, idx) => {
        const item = row as Record<string, unknown>;
        const label = String(item.label ?? item.value ?? '未设置').trim() || '未设置';
        return {
          key: `${String(item.field || activeGroupByField.value || 'group')}:${String(item.value ?? label)}:${idx}`,
          label,
          count: Number(item.count || 0),
          domain: Array.isArray(item.domain) ? item.domain : [],
          value: item.value,
        };
      })
      .filter((item) => item.count >= 0)
      .slice(0, 12);
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
  syncRouteListState();
  load();
}

function handleSort(value: string) {
  sortValue.value = value;
  syncRouteListState();
  load();
}

function handleFilter(value: 'all' | 'active' | 'archived') {
  filterValue.value = value;
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

async function handleBatchAction(action: 'archive' | 'activate') {
  batchMessage.value = '';
  batchDetails.value = [];
  failedCsvFileName.value = '';
  failedCsvContentB64.value = '';
  batchFailedOffset.value = 0;
  batchHasMoreFailures.value = false;
  lastBatchRequest.value = null;
  const targetModel = resolvedModelRef.value || model.value;
  if (!targetModel || !selectedIds.value.length) return;
  if (!hasActiveField.value) {
    batchMessage.value = '当前模型不支持 active 字段，无法批量归档/激活';
    return;
  }
  batchBusy.value = true;
  try {
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
      batchMessage.value = '批量操作已幂等处理（重复请求被忽略）';
    } else {
    batchMessage.value =
      action === 'activate'
        ? `批量激活完成：成功 ${result.succeeded}，失败 ${result.failed}`
        : `批量归档完成：成功 ${result.succeeded}，失败 ${result.failed}`;
    }
    applyBatchFailureArtifacts(result);
    clearSelection();
    await load();
  } catch (err) {
    setError(err, 'batch operation failed');
    batchMessage.value = action === 'activate' ? '批量激活失败' : '批量归档失败';
    batchDetails.value = [];
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
    batchMessage.value = '当前模型不支持负责人字段，无法批量指派';
    return;
  }
  if (!assigneeId) {
    batchMessage.value = '请先选择负责人';
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
      batchMessage.value = `批量指派给 ${assignee} 已幂等处理（重复请求被忽略）`;
    } else {
      batchMessage.value = `批量指派给 ${assignee}：成功 ${result.succeeded}，失败 ${result.failed}`;
    }
    applyBatchFailureArtifacts(result);
    clearSelection();
    await load();
  } catch (err) {
    setError(err, 'batch assign failed');
    batchMessage.value = '批量指派失败';
    batchDetails.value = [];
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
    batchMessage.value = '没有可导出的选中记录';
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
      batchMessage.value = '没有可导出的记录';
      return;
    }
    downloadCsvBase64(result.file_name, result.mime_type, result.content_b64);
    batchMessage.value = `已导出 ${result.count} 条记录`;
  } catch (err) {
    setError(err, 'batch export failed');
    batchMessage.value = '批量导出失败';
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
  batchBusy.value = true;
  try {
    const req = lastBatchRequest.value;
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

@media (max-width: 760px) {
  .focus-strip {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>

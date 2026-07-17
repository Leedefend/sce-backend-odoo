<template>
<section v-if="coverageScan" class="scan-panel">
  <div class="scan-toolbar">
    <label class="page-search">
      <span>页面搜索</span>
      <input :value="pageSearch" type="search" placeholder="输入页面名称" @input="$emit('update:pageSearch', ($event.target as HTMLInputElement).value)" />
    </label>
    <div class="page-type-tabs" role="group" aria-label="页面类型筛选">
      <ScButton
        v-for="option in pageTypeOptions"
        :key="option.key"
        type="button"
        :class="{ active: pageTypeFilter === option.key }"
        @click="$emit('update:pageTypeFilter', option.key)"
      >
        {{ option.label }}
      </ScButton>
    </div>
    <label class="config-status-filter">
      <span>配置状态</span>
      <ScSelect :model-value="configStatusFilter" @update:model-value="$emit('update:configStatusFilter', $event as ConfigStatusFilter)">
        <option v-for="option in configStatusOptions" :key="option.key" :value="option.key">{{ option.label }}</option>
      </ScSelect>
    </label>
    <label v-if="advancedPanelOpen" class="scan-toggle">
      <input :checked="showOnlyIssues" type="checkbox" @change="$emit('update:showOnlyIssues', ($event.target as HTMLInputElement).checked)" />
      <span>只看需处理</span>
    </label>
    <ScButton v-if="advancedPanelOpen" variant="ghost" @click="$emit('copyCoverageSummary')">
      复制配置摘要
    </ScButton>
    <ScButton
      v-if="advancedPanelOpen"
      variant="secondary"
      :disabled="scanLoading || listSearchSaving || !coverageBatchBootstrapRows.length"
      @click="$emit('bootstrapCoverageMissing')"
    >
      {{ listSearchSaving ? '生成中...' : '批量补齐配置' }}
    </ScButton>
  </div>
  <div class="scan-summary">
    <span>业务页面 {{ coverageScan.summary.action_count }}</span>
    <span>当前显示 {{ visibleCoverageRows.length }}</span>
    <span v-if="advancedPanelOpen">{{ coverageScopeLabel }}</span>
    <span v-if="advancedPanelOpen && coverageScan.summary.user_preference_count">已有个人设置 {{ coverageScan.summary.user_preference_count }}</span>
    <span v-if="advancedPanelOpen">配置状态 {{ overallStatusLabel(coverageScan.summary.overall_status) }}</span>
    <span v-if="advancedPanelOpen">需处理 {{ coverageIssueRows.length }}</span>
    <span v-for="item in advancedPanelOpen ? remediationSummaryItems : []" :key="item.code">
      {{ item.label }} {{ item.count }}
    </span>
  </div>
  <div class="config-workspace sc-product-workspace sc-product-main-surface sc-lowcode-workspace" data-lowcode-workbench-ia="three-column">
    <aside class="page-picker-panel" aria-label="业务页面列表">
      <div class="page-picker-head">
        <div>
          <span>业务页面目录</span>
          <strong>{{ visibleCoverageRows.length }} 个匹配页面</strong>
        </div>
        <em>{{ selectedCoverageRow?.name || selectedPageLabel || '未选择' }}</em>
      </div>
      <div v-if="visibleCoverageRows.length" class="scan-list">
        <div
          v-for="(row, rowIndex) in visibleCoverageRows"
          :key="coverageRowKey(row)"
          class="scan-row"
          :class="{ 'scan-row--selected': coverageRowMatchesScope(row), 'scan-row--clickable': !coverageRowMatchesScope(row) }"
          role="group"
          :aria-label="`${row.name || row.model}页面`"
          tabindex="0"
          :aria-current="coverageRowMatchesScope(row) ? 'page' : undefined"
          @click="$emit('focusScanRow', row)"
          @keydown.enter.prevent="$emit('focusScanRow', row)"
          @keydown.space.prevent="$emit('focusScanRow', row)"
          @keydown.up.prevent="movePageSelection(rowIndex, -1, $event)"
          @keydown.down.prevent="movePageSelection(rowIndex, 1, $event)"
        >
          <div class="scan-row-main">
            <strong :title="row.name || row.model">{{ row.name || row.model }}</strong>
            <span v-if="advancedPanelOpen">{{ row.model }}</span>
          </div>
          <div class="scan-row-meta">
            <span>{{ pageViewModeText(row) }}</span>
            <span>{{ rowCoverageProgressText(row) }}</span>
            <span v-if="rowActionHintText(row)">{{ rowActionHintText(row) }}</span>
            <span>{{ pageDesignStatus(row) }}</span>
            <span v-if="advancedPanelOpen && row.user_preference_count">已有个人设置 {{ row.user_preference_count }}</span>
            <span v-if="advancedPanelOpen">{{ runtimeEvidenceText(row) }}</span>
            <span v-if="advancedPanelOpen && runtimeReasonText(row)">原因 {{ runtimeReasonText(row) }}</span>
          </div>
          <div v-if="advancedPanelOpen" class="scan-row-admin-actions">
            <span>{{ severityLabel(row.severity) }}</span>
            <span v-if="row.missing_view_types.length">待配置 {{ row.missing_view_types.map(viewTypeLabel).join('、') }}</span>
            <span v-if="row.runtime_missing_view_types.length">办理页未生效 {{ row.runtime_missing_view_types.map(viewTypeLabel).join('、') }}</span>
          </div>
          <div class="scan-row-actions">
            <ScButton
              v-for="action in advancedPanelOpen ? visibleRowRemediationActions(row) : []"
              :key="`row-remediation-${coverageRowKey(row)}-${action.code}`"
              variant="ghost"
              :disabled="listSearchSaving || versionsLoading"
              @click.stop="$emit('runRemediationAction', row, action)"
            >
              {{ action.label }}
            </ScButton>
            <ScStatusBadge v-if="coverageRowMatchesScope(row)" class="scan-row-current" label="当前配置" semantic="info" />
            <ScButton v-else variant="ghost" @click.stop="$emit('focusScanRow', row)">选择</ScButton>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">当前没有匹配的业务页面，可调整搜索条件或取消“只看需处理”。</div>
    </aside>

    <section v-if="(!loading || surface) && (currentModel || visibleConfigSections.length)" class="page-config-panel" aria-label="已选页面配置">
      <div class="selected-page-overview">
        <div>
          <span>正在配置</span>
          <strong>{{ selectedCoverageRow?.name || selectedPageLabel || currentModel || '当前页面' }}</strong>
        </div>
        <div class="selected-page-overview-side">
          <div class="selected-page-overview-meta">
            <span>{{ selectedCoverageRow ? pageViewModeText(selectedCoverageRow) : '页面配置' }}</span>
            <span v-if="selectedCoverageRow">{{ rowCoverageProgressText(selectedCoverageRow) }}</span>
            <span v-if="selectedCoverageRow">{{ pageDesignStatus(selectedCoverageRow) }}</span>
          </div>
          <ScButton
            variant="secondary"
            :disabled="!runtimeRouteTarget.path"
            @click="$emit('openCurrentEffectivePage')"
          >
            打开当前生效页面
          </ScButton>
        </div>
      </div>
      <div class="config-type-tabs" role="tablist" aria-label="配置类型">
        <ScButton
          v-for="section in visibleConfigSections"
          :key="`tab-${section.key}`"
          :variant="activeSectionKey === section.key ? 'primary' : 'ghost'"
          role="tab"
          :aria-selected="activeSectionKey === section.key"
          @click="$emit('update:activeSectionKey', section.key)"
        >
          {{ sectionDisplayLabel(section.key, section.label) }}
        </ScButton>
      </div>
      <div v-if="activeSection" class="section-grid section-grid--active" data-lowcode-config-task-grid="v1">
        <article :key="activeSection.key" class="config-card" data-lowcode-config-task-card="v1">
          <div class="config-card-head">
            <div>
              <span>{{ sectionTaskKindLabel(activeSection.key) }}</span>
              <h2>{{ sectionDisplayLabel(activeSection.key, activeSection.label) }}</h2>
            </div>
            <ScStatusBadge
              :label="sectionStatusLabel(activeSection.key, activeSection.contract_count)"
              :semantic="activeSection.contract_count ? 'success' : 'warning'"
            />
          </div>
          <div class="config-task-impact">
            <span>{{ sectionPrimaryCopy(activeSection.key) }}</span>
            <em>{{ sectionImpactText(activeSection.key) }}</em>
          </div>
          <div class="config-card-meta" data-lowcode-config-task-meta="v1">
            <span>{{ advancedPanelOpen ? boundaryLabel(activeSection.boundary) : sectionHelpLabel(activeSection.key) }}</span>
            <span>{{ sectionTaskCoverageText(activeSection.key, activeSection.contract_count) }}</span>
          </div>
          <div class="config-card-actions">
            <ScButton
              v-if="activeSection.key === 'form' || activeSection.key === 'list_search' || activeSection.key === 'analysis'"
              variant="ghost"
              :disabled="!currentModel || versionsLoading"
              @click="$emit('loadVersions', activeSection.key)"
            >
              {{ versionsLoading ? '读取中...' : '版本记录' }}
            </ScButton>
            <ScButton
              v-if="activeSection.key === 'list_search'"
              variant="primary"
              :disabled="!currentModel || listSearchBusy"
              @click="$emit('loadListSearchConfig')"
            >
              {{ listSearchBusy ? '读取中...' : sectionPrimaryActionLabel(activeSection.key) }}
            </ScButton>
            <ScButton
              v-else-if="activeSection.key === 'form'"
              variant="primary"
              :disabled="!canOpenDesigner"
              @click="$emit('openFormConfig')"
            >
              {{ sectionPrimaryActionLabel(activeSection.key) }}
            </ScButton>
            <ScButton
              v-else-if="activeSection.key === 'menu'"
              variant="primary"
              @click="$emit('openMenuConfig')"
            >
              {{ sectionPrimaryActionLabel(activeSection.key) }}
            </ScButton>
            <ScButton
              v-if="activeSection.key === 'menu'"
              variant="ghost"
              @click="$emit('openCreateMenuConfig')"
            >
              新增菜单
            </ScButton>
            <ScButton
              v-else-if="activeSection.key === 'analysis'"
              variant="primary"
              :disabled="!currentModel || listSearchBusy"
              @click="$emit('loadAnalysisConfig')"
            >
              {{ listSearchBusy ? '读取中...' : sectionPrimaryActionLabel(activeSection.key) }}
            </ScButton>
            <ScButton
              v-else-if="activeSection.key === 'approval'"
              variant="primary"
              :disabled="!currentModel || approvalLoading"
              @click="$emit('loadApprovalConfig')"
            >
              {{ approvalLoading ? '读取中...' : sectionPrimaryActionLabel(activeSection.key) }}
            </ScButton>
            <ScButton
              v-if="activeSection.key === 'approval' && activeSection.route?.path"
              variant="ghost"
              @click="$emit('openApprovalConfig', activeSection)"
            >
              打开完整规则
            </ScButton>
          </div>
        </article>
      </div>
    </section>
    <aside v-if="surface" class="workbench-status-rail" aria-label="交付状态" data-lowcode-delivery-readiness="low_code_delivery_readiness.v1">
      <div class="delivery-readiness-head">
        <div>
          <span>交付状态</span>
          <strong>{{ deliveryReadinessStatusText }}</strong>
        </div>
        <em>{{ visibleDeliveryReadinessProgressText }}</em>
      </div>
      <div class="delivery-readiness-grid delivery-readiness-grid--rail">
        <ScButton
          v-for="item in visibleDeliveryReadinessItems"
          :key="`rail-${item.id}`"
          type="button"
          class="delivery-readiness-item"
          :class="{ 'delivery-readiness-item--pending': item.status !== 'ready' }"
          @click="$emit('runDeliveryReadinessAction', item)"
        >
          <span>{{ item.label }}</span>
          <strong>{{ deliveryReadinessItemStatusText(item) }}</strong>
          <em>{{ deliveryReadinessItemMetaText(item) }}</em>
        </ScButton>
      </div>
      <div v-if="!visibleDeliveryReadinessItems.length" class="workbench-status-empty">状态读取中</div>
      <div v-if="advancedPanelOpen && snapshotSummary" class="workbench-status-snapshot">
        <span>配置快照</span>
        <strong>{{ snapshotSummary.contract_count }}</strong>
        <em>已发布 {{ snapshotSummary.status_counts?.published || 0 }}</em>
      </div>
    </aside>
  </div>
</section>
</template>

<script setup lang="ts">
import { computed, nextTick } from 'vue';
import type {
  BusinessConfigCoverageScanItem,
  BusinessConfigCoverageScanPayload,
  BusinessConfigRemediationAction,
  BusinessConfigSnapshotSummaryPayload,
  BusinessConfigSurfacePayload,
} from '../../api/businessConfig';
import ScButton from '../../components/design-system/ScButton.vue';
import ScStatusBadge from '../../components/design-system/ScStatusBadge.vue';
import ScSelect from '../../components/design-system/ScSelect.vue';

type SurfaceSection = BusinessConfigSurfacePayload['sections'][number];
type DeliveryItem = NonNullable<BusinessConfigSurfacePayload['delivery_readiness']>['items'][number];
type PageTypeFilter = 'all' | 'form' | 'list' | 'analysis';
type ConfigStatusFilter = 'all' | 'unconfigured' | 'partial' | 'configured';
type PageTypeOption = { key: PageTypeFilter; label: string };

const props = defineProps<{
  coverageScan: BusinessConfigCoverageScanPayload;
  pageSearch: string;
  pageTypeFilter: PageTypeFilter;
  pageTypeOptions: PageTypeOption[];
  configStatusFilter: ConfigStatusFilter;
  configStatusOptions: Array<{ key: ConfigStatusFilter; label: string }>;
  activeSectionKey: string;
  showOnlyIssues: boolean;
  advancedPanelOpen: boolean;
  scanLoading: boolean;
  listSearchSaving: boolean;
  versionsLoading: boolean;
  loading: boolean;
  surface: BusinessConfigSurfacePayload | null;
  currentModel: string;
  selectedPageLabel: string;
  selectedCoverageRow: BusinessConfigCoverageScanItem | undefined;
  visibleCoverageRows: BusinessConfigCoverageScanItem[];
  visibleConfigSections: SurfaceSection[];
  coverageScopeLabel: string;
  coverageIssueRows: BusinessConfigCoverageScanItem[];
  coverageBatchBootstrapRows: BusinessConfigCoverageScanItem[];
  remediationSummaryItems: Array<{ code: string; count: number; label: string }>;
  runtimeRouteTarget: { path: string; query: Record<string, string> };
  canOpenDesigner: boolean;
  listSearchBusy: boolean;
  approvalLoading: boolean;
  deliveryReadinessStatusText: string;
  visibleDeliveryReadinessProgressText: string;
  visibleDeliveryReadinessItems: DeliveryItem[];
  snapshotSummary: BusinessConfigSnapshotSummaryPayload | null;
  coverageRowKey: (row: Pick<BusinessConfigCoverageScanItem, 'model' | 'action_id' | 'view_id'>) => string;
  coverageRowMatchesScope: (row: Pick<BusinessConfigCoverageScanItem, 'model' | 'action_id' | 'view_id'>) => boolean;
  pageViewModeText: (row: BusinessConfigCoverageScanItem) => string;
  rowCoverageProgressText: (row: BusinessConfigCoverageScanItem) => string;
  rowActionHintText: (row: BusinessConfigCoverageScanItem) => string;
  pageDesignStatus: (row: BusinessConfigCoverageScanItem) => string;
  runtimeEvidenceText: (row: BusinessConfigCoverageScanItem) => string;
  runtimeReasonText: (row: BusinessConfigCoverageScanItem) => string;
  visibleRowRemediationActions: (row: BusinessConfigCoverageScanItem) => BusinessConfigRemediationAction[];
  viewTypeLabel: (viewType: string) => string;
  severityLabel: (severity: string) => string;
  overallStatusLabel: (status: string) => string;
  boundaryLabel: (boundary: unknown) => string;
  sectionTaskKindLabel: (sectionKey: string) => string;
  sectionDisplayLabel: (sectionKey: string, fallback: string) => string;
  sectionStatusLabel: (sectionKey: string, contractCount: number) => string;
  sectionPrimaryCopy: (sectionKey: string) => string;
  sectionImpactText: (sectionKey: string) => string;
  sectionHelpLabel: (sectionKey: string) => string;
  sectionTaskCoverageText: (sectionKey: string, contractCount: number) => string;
  sectionPrimaryActionLabel: (sectionKey: string) => string;
  deliveryReadinessItemStatusText: (item: DeliveryItem) => string;
  deliveryReadinessItemMetaText: (item: DeliveryItem) => string;
}>();

const activeSection = computed(() => (
  props.visibleConfigSections.find((section) => section.key === props.activeSectionKey)
  || props.visibleConfigSections[0]
  || null
));

const emit = defineEmits<{
  'update:pageSearch': [value: string];
  'update:pageTypeFilter': [value: PageTypeFilter];
  'update:configStatusFilter': [value: ConfigStatusFilter];
  'update:activeSectionKey': [value: string];
  'update:showOnlyIssues': [value: boolean];
  copyCoverageSummary: [];
  bootstrapCoverageMissing: [];
  focusScanRow: [row: BusinessConfigCoverageScanItem];
  runRemediationAction: [row: BusinessConfigCoverageScanItem, action: BusinessConfigRemediationAction];
  openCurrentEffectivePage: [];
  loadVersions: [sectionKey: string];
  loadListSearchConfig: [];
  openFormConfig: [];
  openMenuConfig: [];
  openCreateMenuConfig: [];
  loadAnalysisConfig: [];
  loadApprovalConfig: [];
  openApprovalConfig: [section: SurfaceSection];
  runDeliveryReadinessAction: [item: DeliveryItem];
}>();

async function movePageSelection(index: number, offset: -1 | 1, event: KeyboardEvent) {
  const targetIndex = Math.max(0, Math.min(props.visibleCoverageRows.length - 1, index + offset));
  const row = props.visibleCoverageRows[targetIndex];
  if (!row) return;
  emit('focusScanRow', row);
  await nextTick();
  const list = (event.currentTarget as HTMLElement | null)?.closest('.scan-list');
  list?.querySelectorAll<HTMLElement>('.scan-row')[targetIndex]?.focus();
}
</script>

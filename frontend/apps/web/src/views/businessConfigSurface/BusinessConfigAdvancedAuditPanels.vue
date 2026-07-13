<template>
  <section v-if="coverageScan" class="scan-panel scan-panel--admin">
    <div class="scan-toolbar">
      <strong>配置检查明细</strong>
      <span v-if="snapshotSummaryText">{{ snapshotSummaryText }}</span>
    </div>
    <div class="scan-list">
      <div v-for="row in visibleCoverageRows" :key="`admin-${coverageRowKey(row)}`" class="scan-row">
        <strong>{{ row.name || row.model }}</strong>
        <span>{{ severityLabel(row.severity) }}</span>
        <span>{{ row.model }}</span>
        <span>{{ row.view_mode || '-' }}</span>
        <span>菜单 {{ row.menu_count }}</span>
        <span v-if="row.user_preference_count">个人设置 {{ row.user_preference_count }} · {{ boundaryLabel(row.user_preference_boundary) }}</span>
        <span v-if="row.missing_view_types.length">待配置 {{ row.missing_view_types.map(viewTypeLabel).join('、') }}</span>
        <span v-else>配置完整</span>
        <span v-if="row.runtime_missing_view_types.length">办理页未生效 {{ row.runtime_missing_view_types.map(viewTypeLabel).join('、') }}</span>
        <span v-else>运行时完整</span>
        <span>{{ runtimeEvidenceText(row) }}</span>
        <span v-if="runtimeReasonText(row)">原因 {{ runtimeReasonText(row) }}</span>
        <button
          v-for="action in row.remediation_actions"
          :key="`admin-${coverageRowKey(row)}-${action.code}`"
          type="button"
          class="link-button"
          @click="$emit('runRemediationAction', row, action)"
        >
          {{ action.label }}
        </button>
        <button
          type="button"
          class="link-button"
          :disabled="!row.runtime_route?.path"
          @click="$emit('openRuntimeRoute', row)"
        >
          预览页面
        </button>
        <button type="button" class="link-button" @click="$emit('focusScanRow', row)">选择此页面</button>
      </div>
    </div>
  </section>
  <section class="scan-panel snapshot-compare-panel">
    <div class="scan-toolbar">
      <strong>跨环境快照对比</strong>
      <span v-if="snapshotCompareResult">{{ snapshotCompareSummary }}</span>
      <button type="button" class="ghost small" :disabled="snapshotExportLoading" @click="$emit('downloadSnapshot')">
        {{ snapshotExportLoading ? '导出中...' : '下载当前快照' }}
      </button>
      <button type="button" class="ghost small" :disabled="snapshotCompareLoading || !snapshotCompareText.trim()" @click="$emit('compareSnapshot')">
        {{ snapshotCompareLoading ? '对比中...' : '对比快照' }}
      </button>
      <button type="button" class="ghost small" :disabled="!snapshotCompareResult" @click="$emit('downloadSnapshotRemediationPlan')">
        下载整改清单
      </button>
    </div>
    <textarea
      :value="snapshotCompareText"
      class="snapshot-input"
      rows="5"
      placeholder="粘贴从目标环境导出的配置快照内容"
      @input="$emit('update:snapshotCompareText', ($event.target as HTMLTextAreaElement).value)"
    ></textarea>
    <div v-if="snapshotCompareResult" class="snapshot-remediation-summary">
      <span>{{ snapshotRemediationSummary }}</span>
    </div>
    <div v-if="snapshotCompareResult" class="snapshot-diff-list">
      <div v-for="item in snapshotCompareChangedRows" :key="item.key" class="snapshot-diff-row">
        <strong>{{ item.name || item.model }}</strong>
        <span>{{ viewTypeLabel(item.view_type) }}</span>
        <span>版本 {{ item.previous_version_no }} -> {{ item.current_version_no }}</span>
        <span>{{ item.previous_status || '-' }} -> {{ item.current_status || '-' }}</span>
      </div>
      <div v-for="item in snapshotCompareAddedRows" :key="`added-${item.model}-${item.view_type}-${item.action_id}-${item.name}`" class="snapshot-diff-row">
        <strong>{{ item.name || item.model }}</strong>
        <span>新增</span>
        <span>{{ viewTypeLabel(item.view_type) }}</span>
        <span>版本 {{ item.version_no }}</span>
      </div>
      <div v-for="item in snapshotCompareRemovedRows" :key="`removed-${item.model}-${item.view_type}-${item.action_id}-${item.name}`" class="snapshot-diff-row">
        <strong>{{ item.name || item.model }}</strong>
        <span>移除</span>
        <span>{{ viewTypeLabel(item.view_type) }}</span>
        <span>版本 {{ item.version_no }}</span>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type {
  BusinessConfigCoverageScanItem,
  BusinessConfigRemediationAction,
  BusinessConfigSnapshotComparePayload,
} from '../../api/businessConfig';

defineProps<{
  coverageScan: unknown;
  visibleCoverageRows: BusinessConfigCoverageScanItem[];
  snapshotSummaryText: string;
  snapshotCompareText: string;
  snapshotCompareLoading: boolean;
  snapshotExportLoading: boolean;
  snapshotCompareResult: BusinessConfigSnapshotComparePayload | null;
  snapshotCompareSummary: string;
  snapshotRemediationSummary: string;
  snapshotCompareChangedRows: BusinessConfigSnapshotComparePayload['changed'];
  snapshotCompareAddedRows: BusinessConfigSnapshotComparePayload['added'];
  snapshotCompareRemovedRows: BusinessConfigSnapshotComparePayload['removed'];
  coverageRowKey: (row: Pick<BusinessConfigCoverageScanItem, 'model' | 'action_id' | 'view_id'>) => string;
  severityLabel: (severity: string) => string;
  boundaryLabel: (boundary: unknown) => string;
  viewTypeLabel: (viewType: string) => string;
  runtimeEvidenceText: (row: BusinessConfigCoverageScanItem) => string;
  runtimeReasonText: (row: BusinessConfigCoverageScanItem) => string;
}>();

defineEmits<{
  runRemediationAction: [row: BusinessConfigCoverageScanItem, action: BusinessConfigRemediationAction];
  openRuntimeRoute: [row: BusinessConfigCoverageScanItem];
  focusScanRow: [row: BusinessConfigCoverageScanItem];
  downloadSnapshot: [];
  compareSnapshot: [];
  downloadSnapshotRemediationPlan: [];
  'update:snapshotCompareText': [value: string];
}>();
</script>

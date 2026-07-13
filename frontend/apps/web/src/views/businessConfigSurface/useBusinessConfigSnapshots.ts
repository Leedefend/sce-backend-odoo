import { computed, ref, type Ref } from 'vue';
import {
  compareBusinessConfigSnapshot,
  exportBusinessConfigSnapshot,
  type BusinessConfigSnapshotComparePayload,
  type BusinessConfigSnapshotSummaryPayload,
  type BusinessConfigSurfacePayload,
} from '../../api/businessConfig';
import { viewTypeLabel } from './formatters';
import { buildSnapshotRemediationPlan, normalizeSnapshotFileToken } from './snapshotRemediation';

type UseBusinessConfigSnapshotsOptions = {
  surface: Ref<BusinessConfigSurfacePayload | null>;
  error: Ref<string>;
  setMessage: (text: string, detail?: string) => void;
  clearMessage: () => void;
};

export function useBusinessConfigSnapshots(options: UseBusinessConfigSnapshotsOptions) {
  const snapshotCompareText = ref('');
  const snapshotCompareLoading = ref(false);
  const snapshotExportLoading = ref(false);
  const snapshotCompareResult = ref<BusinessConfigSnapshotComparePayload | null>(null);

  const snapshotSummary = computed<BusinessConfigSnapshotSummaryPayload | null>(() => (
    options.surface.value?.snapshot_summary || null
  ));
  const snapshotSummaryText = computed(() => {
    const summary = snapshotSummary.value;
    if (!summary) return '';
    const published = summary.status_counts?.published || 0;
    const viewTypes = Object.entries(summary.view_type_counts || {})
      .map(([key, count]) => `${viewTypeLabel(key)} ${count}`)
      .join('、');
    return `配置快照 ${summary.contract_count}，已发布 ${published}，按业务操作 ${summary.action_scope_count}${viewTypes ? `，${viewTypes}` : ''}`;
  });
  const snapshotCompareSummary = computed(() => {
    const result = snapshotCompareResult.value;
    if (!result) return '';
    return [
      `当前 ${result.current_contract_count}`,
      `基线 ${result.baseline_contract_count}`,
      `变化 ${result.changed_count}`,
      `新增 ${result.added_count}`,
      `移除 ${result.removed_count}`,
    ].join('，');
  });
  const snapshotCompareChangedRows = computed(() => (snapshotCompareResult.value?.changed || []).slice(0, 8));
  const snapshotCompareAddedRows = computed(() => (snapshotCompareResult.value?.added || []).slice(0, 6));
  const snapshotCompareRemovedRows = computed(() => (snapshotCompareResult.value?.removed || []).slice(0, 6));
  const snapshotRemediationSummary = computed(() => {
    const result = snapshotCompareResult.value;
    if (!result) return '';
    const total = result.changed_count + result.added_count + result.removed_count;
    if (!total) return '两个环境配置一致，无需生成整改项。';
    return `可生成 ${total} 条整改项：新增 ${result.added_count}，移除 ${result.removed_count}，变化 ${result.changed_count}。`;
  });

  async function downloadSnapshot() {
    snapshotExportLoading.value = true;
    options.error.value = '';
    options.clearMessage();
    try {
      const snapshot = await exportBusinessConfigSnapshot();
      const database = String(snapshot.database || 'business-config').replace(/[^a-zA-Z0-9_-]+/g, '-');
      const blob = new Blob([`${JSON.stringify(snapshot, null, 2)}\n`], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `business-config-contract-snapshot-${database}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      options.setMessage('已生成当前快照');
    } catch (err) {
      options.error.value = err instanceof Error ? err.message : '当前快照导出失败';
    } finally {
      snapshotExportLoading.value = false;
    }
  }

  function downloadJsonFile(payload: unknown, filename: string) {
    const blob = new Blob([`${JSON.stringify(payload, null, 2)}\n`], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }

  function downloadSnapshotRemediationPlan() {
    const result = snapshotCompareResult.value;
    if (!result) return;
    const plan = buildSnapshotRemediationPlan(result);
    const current = normalizeSnapshotFileToken(result.current_database);
    const baseline = normalizeSnapshotFileToken(result.baseline_database);
    downloadJsonFile(plan, `business-config-remediation-${baseline}-to-${current}.json`);
    options.setMessage('已生成整改清单', snapshotRemediationSummary.value);
  }

  async function compareSnapshot() {
    const text = snapshotCompareText.value.trim();
    if (!text) return;
    snapshotCompareLoading.value = true;
    options.error.value = '';
    options.clearMessage();
    try {
      const snapshot = JSON.parse(text) as Record<string, unknown>;
      snapshotCompareResult.value = await compareBusinessConfigSnapshot({ snapshot });
      const result = snapshotCompareResult.value;
      options.setMessage(
        '已完成快照对比',
        `变化 ${result.changed_count}，新增 ${result.added_count}，移除 ${result.removed_count}`,
      );
    } catch (err) {
      snapshotCompareResult.value = null;
      options.error.value = err instanceof Error ? err.message : '配置快照解析或对比失败';
    } finally {
      snapshotCompareLoading.value = false;
    }
  }

  return {
    snapshotCompareText,
    snapshotCompareLoading,
    snapshotExportLoading,
    snapshotCompareResult,
    snapshotSummary,
    snapshotSummaryText,
    snapshotCompareSummary,
    snapshotCompareChangedRows,
    snapshotCompareAddedRows,
    snapshotCompareRemovedRows,
    snapshotRemediationSummary,
    downloadSnapshot,
    downloadSnapshotRemediationPlan,
    compareSnapshot,
  };
}

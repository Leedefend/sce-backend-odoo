import type { ComputedRef, Ref } from 'vue';
import type {
  BusinessConfigCoverageScanItem,
  BusinessConfigSurfacePayload,
} from '../../api/businessConfig';
import { boundaryLabel } from './formatters';

type DeliveryItem = NonNullable<BusinessConfigSurfacePayload['delivery_readiness']>['items'][number];

type UseBusinessConfigWorkbenchMetaOptions = {
  selectedCoverageRow: ComputedRef<BusinessConfigCoverageScanItem | undefined>;
  selectedPageLabel: Ref<string>;
  advancedPanelOpen: Ref<boolean>;
  scanSystemRootCoverage: () => void;
  openMenuConfig: () => void;
  loadApprovalConfig: () => void;
  loadListSearchConfig: () => void;
  openFormConfig: () => void;
};

export function useBusinessConfigWorkbenchMeta(options: UseBusinessConfigWorkbenchMetaOptions) {
  function sectionImpactText(sectionKey: string) {
    const page = options.selectedCoverageRow.value?.name || options.selectedPageLabel.value || '当前页面';
    if (sectionKey === 'form') return `影响 ${page} 的表单填写体验`;
    if (sectionKey === 'list_search') return `影响 ${page} 的列表和检索默认值`;
    if (sectionKey === 'analysis') return `影响 ${page} 的统计分析视图`;
    if (sectionKey === 'menu') return `影响 ${page} 的导航可见性`;
    if (sectionKey === 'approval') return `影响 ${page} 的提交和审核判断`;
    return `影响 ${page}`;
  }

  function selectedPageViewTypes() {
    const row = options.selectedCoverageRow.value;
    const fromTarget = (row?.target_view_types || []).map((item) => String(item || '').trim()).filter(Boolean);
    const fromMode = String(row?.view_mode || '')
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
    return new Set([...fromTarget, ...fromMode]);
  }

  function sectionExpectedContractCount(sectionKey: string) {
    const viewTypes = selectedPageViewTypes();
    if (sectionKey === 'list_search') {
      const expected = [
        viewTypes.has('tree') || viewTypes.has('list') ? 'tree' : '',
        viewTypes.has('search') ? 'search' : '',
      ].filter(Boolean).length;
      return expected || 2;
    }
    if (sectionKey === 'analysis') {
      const expected = ['pivot', 'graph', 'calendar', 'dashboard'].filter((viewType) => viewTypes.has(viewType)).length;
      return expected || 1;
    }
    return 1;
  }

  function sectionStatusLabel(sectionKey: string, contractCount: number) {
    const count = Number(contractCount || 0);
    if (sectionKey === 'menu') return count > 0 ? '已配置' : '未调整';
    const expected = sectionExpectedContractCount(sectionKey);
    if (count <= 0) return '未配置';
    if (count < expected) return '部分配置';
    return '已配置';
  }

  function sectionConfigProgressText(sectionKey: string, contractCount: number) {
    if (sectionKey === 'menu') return '';
    const expected = sectionExpectedContractCount(sectionKey);
    const count = Math.max(0, Math.min(Number(contractCount || 0), expected));
    return `${count}/${expected}`;
  }

  function sectionTaskCoverageText(sectionKey: string, contractCount: number) {
    if (sectionKey === 'menu') {
      return Number(contractCount || 0) > 0 ? '已有菜单显示规则' : '使用默认菜单显示';
    }
    const progress = sectionConfigProgressText(sectionKey, contractCount);
    return progress ? `覆盖 ${progress}` : '覆盖 0/1';
  }

  function deliveryReadinessItemMetaText(item: DeliveryItem) {
    const countText = item.contract_count ? `${item.contract_count} 项` : '未建立';
    return options.advancedPanelOpen.value && item.boundary ? `${countText} · ${boundaryLabel(item.boundary)}` : countText;
  }

  function runDeliveryReadinessAction(item: DeliveryItem) {
    if (item.action === 'coverage_scan') {
      options.scanSystemRootCoverage();
      return;
    }
    if (item.action === 'snapshot_compare') {
      options.advancedPanelOpen.value = true;
      return;
    }
    if (item.section_key === 'menu') {
      options.openMenuConfig();
      return;
    }
    if (item.section_key === 'approval') {
      options.loadApprovalConfig();
      return;
    }
    if (item.section_key === 'list_search') {
      options.loadListSearchConfig();
      return;
    }
    if (item.section_key === 'form') {
      options.openFormConfig();
    }
  }

  return {
    sectionImpactText,
    sectionStatusLabel,
    sectionTaskCoverageText,
    deliveryReadinessItemMetaText,
    runDeliveryReadinessAction,
  };
}

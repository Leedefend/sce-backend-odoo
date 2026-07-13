import { computed, ref, type Ref } from 'vue';
import type {
  BusinessConfigCoverageScanItem,
  BusinessConfigCoverageScanPayload,
} from '../../api/businessConfig';
import {
  overallStatusLabel,
  pageViewModeText,
  remediationActionLabel,
  rowBootstrapMissingViewTypes,
  rowHasAnalysisConfig,
  rowHasListSearchConfig,
  runtimeRouteText,
} from './formatters';

type PageTypeFilter = 'all' | 'form' | 'list' | 'analysis';

type UseBusinessConfigCoverageOptions = {
  coverageScan: Ref<BusinessConfigCoverageScanPayload | null>;
  advancedPanelOpen: Ref<boolean>;
  setMessage: (text: string, detail?: string) => void;
};

export function useBusinessConfigCoverage(options: UseBusinessConfigCoverageOptions) {
  const showOnlyIssues = ref(false);
  const pageSearch = ref('');
  const pageTypeFilter = ref<PageTypeFilter>('all');
  const pageTypeOptions = [
    { key: 'all' as const, label: '全部页面' },
    { key: 'form' as const, label: '表单页面' },
    { key: 'list' as const, label: '列表页面' },
    { key: 'analysis' as const, label: '分析页面' },
  ];

  const coverageIssueRows = computed(() => (
    options.coverageScan.value?.items || []
  ).filter(isCoverageIssue));
  const coverageBatchBootstrapRows = computed(() => (
    options.coverageScan.value?.items || []
  ).filter((row) => (
    rowBootstrapMissingViewTypes(row, ['form', 'tree', 'search', 'pivot', 'graph']).length > 0
  )));
  const coverageScopeLabel = computed(() => {
    const scan = options.coverageScan.value;
    if (!scan) return '未扫描';
    if (scan.include_all_root_menu_actions) {
      return scan.root_menu_xmlid ? '扫描范围：系统根菜单' : '扫描范围：全部菜单';
    }
    if (scan.include_unreachable_actions) return '扫描范围：含无菜单动作';
    return '扫描范围：当前用户可见';
  });
  const pageSearchText = computed(() => pageSearch.value.trim().toLowerCase());
  const visibleCoverageRows = computed(() => {
    const rows = showOnlyIssues.value ? coverageIssueRows.value : options.coverageScan.value?.items || [];
    const keyword = pageSearchText.value;
    const filtered = rows
      .filter((row) => {
        if (pageTypeFilter.value === 'form') return row.target_view_types.includes('form');
        if (pageTypeFilter.value === 'list') return rowHasListSearchConfig(row);
        if (pageTypeFilter.value === 'analysis') return rowHasAnalysisConfig(row);
        return true;
      })
      .filter((row) => {
        if (!keyword) return true;
        const searchable = options.advancedPanelOpen.value
          ? [row.name, row.model, row.view_mode, pageViewModeText(row)]
          : [row.name, pageViewModeText(row)];
        return searchable.some((text) => String(text || '').toLowerCase().includes(keyword));
      });
    return filtered.slice(0, 60);
  });
  const remediationSummaryItems = computed(() => {
    const counts = options.coverageScan.value?.summary.remediation_action_counts || {};
    return Object.entries(counts)
      .map(([code, count]) => ({ code, count, label: remediationActionLabel(code) }))
      .filter((item) => item.count > 0)
      .sort((left, right) => left.label.localeCompare(right.label, 'zh-Hans-CN'));
  });

  function isCoverageIssue(row: BusinessConfigCoverageScanItem) {
    return !row.is_complete || !row.is_runtime_complete || !row.has_menu;
  }

  function buildCoverageSummaryText() {
    const scan = options.coverageScan.value;
    if (!scan) return '';
    const summary = scan.summary;
    const actions = remediationSummaryItems.value
      .map((item) => `${item.label}${item.count}`)
      .join('，') || '无';
    const routeRows = (coverageIssueRows.value.length ? coverageIssueRows.value : scan.items || [])
      .map((row) => ({
        row,
        route: runtimeRouteText(row),
      }))
      .filter((item) => item.route)
      .slice(0, 10);
    const routeEvidence = routeRows.length
      ? routeRows.map((item) => `${item.row.name || item.row.model}：${item.route}`).join('\n')
      : '无';
    return [
      `低代码配置覆盖验收：${overallStatusLabel(summary.overall_status)}`,
      `${coverageScopeLabel.value}；范围：${scan.model || '全部业务对象'}，业务操作 ${summary.action_count}`,
      `严重级别：阻断 ${summary.severity_counts.error || 0}，警告 ${summary.severity_counts.warning || 0}，提示 ${summary.severity_counts.notice || 0}`,
      `未配置：配置 ${summary.missing_count}，办理页 ${summary.runtime_missing_count}，分析页 ${summary.runtime_missing_analysis_count || 0}，无菜单 ${summary.no_menu_count}，个人设置 ${summary.user_preference_count}`,
      `原因：未发布 ${summary.not_published_gap_count}，作用域未命中 ${summary.not_runtime_applicable_gap_count}`,
      `整改：${actions}`,
      `运行页面证据：\n${routeEvidence}`,
    ].join('\n');
  }

  async function copyCoverageSummary() {
    const text = buildCoverageSummaryText();
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      options.setMessage('已复制验收摘要');
    } catch {
      options.setMessage('复制摘要失败', '浏览器未允许写入剪贴板，请稍后重试');
    }
  }

  return {
    showOnlyIssues,
    pageSearch,
    pageTypeFilter,
    pageTypeOptions,
    coverageIssueRows,
    coverageBatchBootstrapRows,
    coverageScopeLabel,
    visibleCoverageRows,
    remediationSummaryItems,
    copyCoverageSummary,
  };
}

import { computed, ref, type ComputedRef, type Ref } from 'vue';
import {
  loadBusinessConfigContractVersions,
  rollbackBusinessConfigContract,
  type BusinessConfigContractVersionsPayload,
  type BusinessConfigSurfacePayload,
} from '../../api/businessConfig';
import {
  countDiff,
  formatDiffNames,
  viewTypeLabel,
} from './formatters';

type RollbackConfirm = {
  open: (options: {
    title: string;
    message: string;
    confirmLabel: string;
    cancelLabel: string;
    tone: 'danger';
  }) => Promise<boolean>;
};

type VersionSectionKey = 'form' | 'list_search' | 'analysis' | '';
type VersionContract = BusinessConfigContractVersionsPayload['contracts'][number];
type VersionSummary = VersionContract['summary'];

type UseBusinessConfigVersionsOptions = {
  currentModel: ComputedRef<string>;
  scopeAction: ComputedRef<number | undefined>;
  scopeView: ComputedRef<number | undefined>;
  scopeRole: ComputedRef<string | undefined>;
  selectedPageLabel: Ref<string>;
  surface: Ref<BusinessConfigSurfacePayload | null>;
  advancedPanelOpen: Ref<boolean>;
  listSearchSaving: Ref<boolean>;
  coverageScan: Ref<unknown>;
  error: Ref<string>;
  setMessage: (text: string, detail?: string) => void;
  clearMessage: () => void;
  loadSurface: () => Promise<void>;
  rescanCoverageAfterBootstrap: () => Promise<void>;
  rollbackConfirm: RollbackConfirm;
};

export function useBusinessConfigVersions(options: UseBusinessConfigVersionsOptions) {
  const versionsLoading = ref(false);
  const versionsPanelOpen = ref(false);
  const versionTitle = ref('配置版本');
  const activeVersionSection = ref<VersionSectionKey>('');
  const versionContracts = ref<BusinessConfigContractVersionsPayload['contracts']>([]);

  const versionPanelDescription = computed(() => (
    options.advancedPanelOpen.value
      ? '按当前业务对象、业务操作、页面类型、角色范围读取正式业务配置版本。'
      : '查看这个页面的配置保存记录，可在需要时回滚到历史版本。'
  ));
  const versionPanelGuide = computed(() => {
    if (activeVersionSection.value === 'form') {
      return {
        title: '表单版本怎么用',
        body: '当前生效版决定办理页面的字段、分组和布局。恢复历史版本后会立即发布为新的当前配置。',
      };
    }
    if (activeVersionSection.value === 'list_search') {
      return {
        title: '列表与搜索版本怎么用',
        body: '这里管理页面默认列表列、搜索条件和默认分组，不覆盖用户自己的列宽、排序等个人设置。',
      };
    }
    if (activeVersionSection.value === 'analysis') {
      return {
        title: '分析版本怎么用',
        body: '这里管理透视、图表等分析视图的默认指标和维度。恢复历史版本后刷新业务页面即可生效。',
      };
    }
    return {
      title: '配置版本怎么用',
      body: '先确认当前生效版，再选择需要恢复的历史版本。恢复操作会发布为新的当前配置。',
    };
  });
  const versionEmptyText = computed(() => (
    options.advancedPanelOpen.value ? '当前作用域暂无版本记录。' : '当前页面暂无版本记录。'
  ));

  function versionParams(viewType?: string) {
    return {
      model: options.currentModel.value,
      view_type: viewType,
      action_id: options.scopeAction.value,
      view_id: options.scopeView.value,
      role_key: options.scopeRole.value,
    };
  }

  async function loadVersions(sectionKey: string) {
    if (!options.currentModel.value) return;
    activeVersionSection.value = sectionKey === 'form' || sectionKey === 'list_search' || sectionKey === 'analysis'
      ? sectionKey
      : '';
    versionsLoading.value = true;
    options.error.value = '';
    options.clearMessage();
    try {
      if (sectionKey === 'form') {
        const result = await loadBusinessConfigContractVersions(versionParams('form'));
        versionTitle.value = '表单配置版本';
        versionContracts.value = result.contracts || [];
      } else if (sectionKey === 'list_search') {
        const [treeResult, searchResult] = await Promise.all([
          loadBusinessConfigContractVersions(versionParams('tree')),
          loadBusinessConfigContractVersions(versionParams('search')),
        ]);
        versionTitle.value = '列表/搜索配置版本';
        versionContracts.value = [...(treeResult.contracts || []), ...(searchResult.contracts || [])];
      } else {
        const results = await Promise.all(
          ['pivot', 'graph', 'calendar', 'dashboard'].map((viewType) => (
            loadBusinessConfigContractVersions(versionParams(viewType))
          )),
        );
        versionTitle.value = '分析视图配置版本';
        versionContracts.value = results.flatMap((result) => result.contracts || []);
      }
      versionsPanelOpen.value = true;
    } catch (err) {
      options.error.value = err instanceof Error ? err.message : '配置版本读取失败';
    } finally {
      versionsLoading.value = false;
    }
  }

  function versionContractDisplayName(contract: VersionContract) {
    if (options.advancedPanelOpen.value) return contract.name || contract.model || '业务配置';
    const page = options.selectedPageLabel.value || options.surface.value?.model || contract.model || '当前页面';
    const view = viewTypeLabel(contract.view_type);
    return view ? `${page} · ${view}` : page;
  }

  function versionContractImpactText(contract: VersionContract) {
    const view = viewTypeLabel(contract.view_type);
    if (contract.view_type === 'form') return '影响办理页字段、分组、显示隐藏和布局。';
    if (contract.view_type === 'tree' || contract.view_type === 'list') return '影响办理页默认列表列。';
    if (contract.view_type === 'search') return '影响办理页搜索条件和默认分组。';
    if (['pivot', 'graph', 'calendar', 'dashboard'].includes(contract.view_type)) return `影响${view}视图的默认展示。`;
    return `影响${view}配置的默认运行效果。`;
  }

  function versionRollbackButtonLabel(contract: VersionContract) {
    return contract.versions.length < 2 ? '暂无可回滚版本' : '恢复上一版本配置';
  }

  function versionContractDecisionText(contract: VersionContract) {
    const historyCount = Math.max(0, contract.versions.length - 1);
    const currentSummary = versionSummaryText(contract.summary);
    if (!historyCount) return `当前只有一个版本：${currentSummary}。`;
    return `当前生效：${currentSummary}。可恢复 ${historyCount} 个历史版本，恢复后会发布为新的当前配置。`;
  }

  function versionSummaryNames(summary: VersionSummary) {
    return {
      form: (summary.form_field_labels && summary.form_field_labels.length ? summary.form_field_labels : summary.form_fields) || [],
      list: summary.list_columns || [],
      filter: summary.search_filters || [],
      group: summary.search_group_by || [],
      viewTypes: summary.view_types || [],
      analysis: summary.analysis_items || [],
    };
  }

  function versionDeltaText(current: VersionSummary, target: VersionSummary, isCurrent: boolean) {
    if (isCurrent) return '当前版本';
    const currentNames = versionSummaryNames(current);
    const targetNames = versionSummaryNames(target);
    const parts = [
      { label: '字段', diff: countDiff(currentNames.form, targetNames.form) },
      { label: '列', diff: countDiff(currentNames.list, targetNames.list) },
      { label: '筛选', diff: countDiff(currentNames.filter, targetNames.filter) },
      { label: '分组', diff: countDiff(currentNames.group, targetNames.group) },
      { label: '分析项', diff: countDiff(currentNames.analysis, targetNames.analysis) },
      { label: '视图', diff: countDiff(currentNames.viewTypes, targetNames.viewTypes) },
    ]
      .map((item) => {
        const changes = [
          item.diff.added.length ? `多 ${item.diff.added.length}：${formatDiffNames(item.diff.added)}` : '',
          item.diff.removed.length ? `少 ${item.diff.removed.length}：${formatDiffNames(item.diff.removed)}` : '',
        ].filter(Boolean).join('、');
        return changes ? `${item.label}${changes}` : '';
      })
      .filter(Boolean);
    return parts.length ? `与当前相比：${parts.join('；')}` : '与当前一致';
  }

  function versionSummaryText(summary: VersionSummary) {
    const counts = [
      summary.form_field_count ? `字段 ${summary.form_field_count}` : '',
      summary.list_column_count ? `列 ${summary.list_column_count}` : '',
      summary.search_filter_count ? `筛选 ${summary.search_filter_count}` : '',
      summary.search_group_by_count ? `分组 ${summary.search_group_by_count}` : '',
      summary.analysis_item_count ? `分析项 ${summary.analysis_item_count}` : '',
    ].filter(Boolean);
    if (counts.length) return counts.join(' / ');
    const viewTypes = (summary.view_types || []).map(viewTypeLabel).filter(Boolean);
    return viewTypes.length ? `视图 ${viewTypes.join('、')}` : '暂无配置项';
  }

  async function rollbackContractFromWorkbench(contract: VersionContract, versionNo?: number) {
    if (!contract?.name || (versionNo ? versionNo === contract.version_no : contract.versions.length < 2)) return;
    const targetText = versionNo ? `v${versionNo}` : '上一版';
    const confirmed = await options.rollbackConfirm.open({
      title: '确认恢复配置版本',
      message: [
        `确认恢复${versionContractDisplayName(contract)}的${targetText}？`,
        versionContractImpactText(contract),
        '恢复后会立即发布为新的当前配置，刷新业务页面后生效。',
      ].join('\n'),
      confirmLabel: '恢复',
      cancelLabel: '取消',
      tone: 'danger',
    });
    if (!confirmed) return;
    options.listSearchSaving.value = true;
    options.error.value = '';
    options.clearMessage();
    try {
      const result = await rollbackBusinessConfigContract({
        name: contract.name,
        model: contract.model,
        view_type: contract.view_type,
        action_id: contract.action_id || undefined,
        view_id: contract.view_id || undefined,
        role_key: contract.role_key || undefined,
        version_no: versionNo,
      });
      await options.loadSurface();
      await loadVersions(sectionKeyForViewType(contract.view_type));
      if (options.coverageScan.value) {
        await options.rescanCoverageAfterBootstrap();
      }
      options.setMessage('配置已回滚并发布', `已回滚到 v${result.rolled_back_to_version}，刷新页面后按该版本生效`);
    } catch (err) {
      options.error.value = err instanceof Error ? err.message : '业务配置回滚失败';
    } finally {
      options.listSearchSaving.value = false;
    }
  }

  function sectionKeyForViewType(viewType: string) {
    if (viewType === 'form') return 'form';
    if (viewType === 'tree' || viewType === 'list' || viewType === 'search') return 'list_search';
    if (['pivot', 'graph', 'calendar', 'dashboard'].includes(viewType)) return 'analysis';
    return 'list_search';
  }

  return {
    versionsLoading,
    versionsPanelOpen,
    versionTitle,
    activeVersionSection,
    versionContracts,
    versionPanelDescription,
    versionPanelGuide,
    versionEmptyText,
    loadVersions,
    rollbackContractFromWorkbench,
    versionContractDisplayName,
    versionContractImpactText,
    versionRollbackButtonLabel,
    versionContractDecisionText,
    versionDeltaText,
    versionSummaryText,
  };
}

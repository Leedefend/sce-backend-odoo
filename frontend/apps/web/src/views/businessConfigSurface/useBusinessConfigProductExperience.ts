import { computed, onBeforeUnmount, onMounted, watch, type ComputedRef, type Ref } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
import type {
  BusinessConfigAnalysisAuditPayload,
  BusinessConfigListSearchAuditPayload,
  BusinessConfigSnapshotSummaryPayload,
} from '../../api/businessConfig';
import type { useSessionStore } from '../../stores/session';
import { normalizeNamesText } from './formatters';

type SessionStore = ReturnType<typeof useSessionStore>;
type VersionRow = { version_no?: number };

export function useBusinessConfigProductExperience(options: {
  session: SessionStore;
  versionContracts: Ref<VersionRow[]>;
  listSearchAudit: Ref<BusinessConfigListSearchAuditPayload | null>;
  analysisAudit: Ref<BusinessConfigAnalysisAuditPayload | null>;
  snapshotSummary: ComputedRef<BusinessConfigSnapshotSummaryPayload | null>;
  hasListSearchDraftChanges: ComputedRef<boolean>;
  hasAnalysisDraftChanges: ComputedRef<boolean>;
  hasApprovalDraftChanges: ComputedRef<boolean>;
  listColumnsText: Ref<string>;
  searchFiltersText: Ref<string>;
  searchGroupByText: Ref<string>;
  listSearchBase: Ref<{ list: string; filter: string; group: string }>;
  listSearchPanelOpen: Ref<boolean>;
  analysisPanelOpen: Ref<boolean>;
  approvalPanelOpen: Ref<boolean>;
  versionsPanelOpen: Ref<boolean>;
  resetListSearchDraft: () => void;
  resetAnalysisDraft: () => void;
  resetApprovalDraft: () => void;
  loadSurface: () => Promise<void>;
  scanSystemRootCoverage: () => Promise<void>;
  setMessage: (text: string, detail?: string) => void;
  openImpactDialog: (options: { summary: string; immediate?: boolean; rollbackText?: string }) => Promise<boolean>;
}) {
  const workbenchCompanyLabel = computed(() => String(
    options.session.projectContext?.company_name
    || options.session.projectContext?.selected?.company_name
    || '',
  ).trim());
  const workbenchRoleLabel = computed(() => String(options.session.roleSurface?.role_label || '').trim());
  const hasWorkbenchDraftChanges = computed(() => (
    options.hasListSearchDraftChanges.value
    || options.hasAnalysisDraftChanges.value
    || options.hasApprovalDraftChanges.value
  ));
  const currentEffectiveVersionLabel = computed(() => {
    const versionNumbers = [
      ...options.versionContracts.value.map((item) => Number(item.version_no || 0)),
      ...(options.listSearchAudit.value?.business_config_list_contracts || []).map((item) => Number(item.version_no || 0)),
      ...(options.listSearchAudit.value?.business_config_search_contracts || []).map((item) => Number(item.version_no || 0)),
      ...(options.analysisAudit.value?.business_config_analysis_contracts || []).map((item) => Number(item.version_no || 0)),
    ].filter((item) => Number.isFinite(item) && item > 0);
    if (versionNumbers.length) return `版本 ${Math.max(...versionNumbers)}`;
    const publishedCount = Number(options.snapshotSummary.value?.status_counts?.published || 0);
    return publishedCount ? `已发布 ${publishedCount} 项配置` : '尚未配置';
  });

  function inspectListSearchDraft() {
    if (!options.hasListSearchDraftChanges.value) {
      options.setMessage('当前没有未保存修改', '打开当前生效页面不会保存、发布或创建版本。');
      return;
    }
    const changedAreas = [
      normalizeNamesText(options.listColumnsText.value) !== options.listSearchBase.value.list ? '列表列' : '',
      normalizeNamesText(options.searchFiltersText.value) !== options.listSearchBase.value.filter ? '搜索条件' : '',
      normalizeNamesText(options.searchGroupByText.value) !== options.listSearchBase.value.group ? '默认分组' : '',
    ].filter(Boolean);
    options.setMessage(
      '当前修改检查完成',
      `${changedAreas.join('、') || '列表与搜索'}存在未保存修改。当前版本不支持未发布效果预览；本次检查未保存、未发布，也未创建版本。`,
    );
  }

  function inspectAnalysisDraft() {
    if (!options.hasAnalysisDraftChanges.value) {
      options.setMessage('当前没有未保存修改', '打开当前生效页面不会保存、发布或创建版本。');
      return;
    }
    options.setMessage(
      '当前修改检查完成',
      '分析视图存在未保存修改。当前版本不支持未发布效果预览；本次检查未保存、未发布，也未创建版本。',
    );
  }

  function handleBeforeUnload(event: BeforeUnloadEvent) {
    if (!hasWorkbenchDraftChanges.value) return;
    event.preventDefault();
    event.returnValue = '';
  }
  onBeforeRouteLeave(async () => {
    if (!hasWorkbenchDraftChanges.value) return true;
    return options.openImpactDialog({
      summary: '离开工作台将放弃当前未保存修改',
      immediate: false,
      rollbackText: '未保存修改尚未形成版本，离开后无法恢复。',
    });
  });
  watch(
    () => `${options.session.projectContext?.company_id || ''}:${options.session.roleSurface?.role_code || ''}`,
    async (nextScope, previousScope) => {
      if (!previousScope || nextScope === previousScope) return;
      options.resetListSearchDraft();
      options.resetAnalysisDraft();
      options.resetApprovalDraft();
      options.listSearchPanelOpen.value = false;
      options.analysisPanelOpen.value = false;
      options.approvalPanelOpen.value = false;
      options.versionsPanelOpen.value = false;
      await options.loadSurface();
      await options.scanSystemRootCoverage();
    },
  );
  onMounted(() => window.addEventListener('beforeunload', handleBeforeUnload));
  onBeforeUnmount(() => window.removeEventListener('beforeunload', handleBeforeUnload));

  return {
    workbenchCompanyLabel,
    workbenchRoleLabel,
    hasWorkbenchDraftChanges,
    currentEffectiveVersionLabel,
    inspectListSearchDraft,
    inspectAnalysisDraft,
  };
}

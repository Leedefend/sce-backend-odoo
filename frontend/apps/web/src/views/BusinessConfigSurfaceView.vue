<template src="./businessConfigSurface/template.html"></template>
<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-unused-vars */
import { computed, nextTick, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import BusinessConfigAdvancedAuditPanels from './businessConfigSurface/BusinessConfigAdvancedAuditPanels.vue';
import BusinessConfigApprovalPanel from './businessConfigSurface/BusinessConfigApprovalPanel.vue';
import BusinessConfigContextBar from './businessConfigSurface/BusinessConfigContextBar.vue';
import BusinessConfigChangeSetPanel from './businessConfigSurface/BusinessConfigChangeSetPanel.vue';
import BusinessConfigCoverageWorkspace from './businessConfigSurface/BusinessConfigCoverageWorkspace.vue';
import BusinessConfigEditorPanels from './businessConfigSurface/BusinessConfigEditorPanels.vue';
import BusinessConfigImpactDialog from './businessConfigSurface/BusinessConfigImpactDialog.vue';
import BusinessConfigStartPanel from './businessConfigSurface/BusinessConfigStartPanel.vue';
import BusinessConfigVersionPanel from './businessConfigSurface/BusinessConfigVersionPanel.vue';
import ScButton from '../components/design-system/ScButton.vue';
import {
  auditBusinessAnalysisConfig,
  auditBusinessListSearchConfig,
  bootstrapBusinessAnalysisConfig,
  bootstrapBusinessFormConfig,
  bootstrapBusinessListSearchConfig,
  bootstrapCoverageMissingConfig,
  loadBusinessConfigSurface,
  scanBusinessConfigCoverage,
  type BusinessConfigAnalysisAuditPayload,
  type BusinessConfigCoverageScanItem,
  type BusinessConfigCoverageScanPayload,
  type BusinessConfigListSearchAuditPayload,
  type BusinessConfigRemediationAction,
  type BusinessConfigSurfacePayload,
} from '../api/businessConfig';
import {
  BUSINESS_CONFIG_INTENTS,
  BUSINESS_CONFIG_ROUTE_FLAGS,
  isBusinessConfigRuntimeModel,
} from '../app/businessConfigBoundaries';
import { usePageContract } from '../app/pageContract';
import { executePageContractAction } from '../app/pageContractActionRuntime';
import { useSessionStore } from '../stores/session';
import {
  analysisItemLabel,
  boundaryLabel,
  deliveryReadinessItemStatusText,
  namesToText,
  normalizeNamesText,
  overallStatusLabel,
  pageDesignStatus,
  pageViewModeText,
  parseNames,
  rowActionHintText,
  rowBootstrapMissingViewTypes,
  rowCoverageProgressText,
  rowHasAnalysisConfig,
  rowHasFormConfig,
  rowHasListSearchConfig,
  runtimeEvidenceText,
  runtimeReasonText,
  sectionDisplayLabel,
  sectionHelpLabel,
  sectionPrimaryActionLabel,
  sectionPrimaryCopy,
  sectionTaskKindLabel,
  severityLabel,
  versionStatusLabel, viewTypeLabel,
  visibleRowRemediationActions,
} from './businessConfigSurface/formatters';
import { useBusinessConfigApprovalEditor } from './businessConfigSurface/useBusinessConfigApprovalEditor';
import { useBusinessConfigCoverage } from './businessConfigSurface/useBusinessConfigCoverage';
import { useBusinessConfigFieldEditors } from './businessConfigSurface/useBusinessConfigFieldEditors';
import { useBusinessConfigSnapshots } from './businessConfigSurface/useBusinessConfigSnapshots';
import { useBusinessConfigVersions } from './businessConfigSurface/useBusinessConfigVersions';
import { useBusinessConfigWorkbenchMeta } from './businessConfigSurface/useBusinessConfigWorkbenchMeta';
import { useBusinessConfigProductExperience } from './businessConfigSurface/useBusinessConfigProductExperience';
import { useBusinessConfigNavigation } from './businessConfigSurface/useBusinessConfigNavigation';
import { useBusinessConfigImpactDialog } from './businessConfigSurface/useBusinessConfigImpactDialog';
import { useBusinessConfigDraftSession } from './businessConfigSurface/useBusinessConfigDraftSession';
import { useBusinessConfigScopeLifecycle } from './businessConfigSurface/useBusinessConfigScopeLifecycle';
import { useBusinessConfigPublishLifecycle } from './businessConfigSurface/useBusinessConfigPublishLifecycle';
import { useBusinessConfigRemediationLifecycle } from './businessConfigSurface/useBusinessConfigRemediationLifecycle';
import { analysisContractPayload, contractTargetKey, listContractPayload, searchContractPayload } from './businessConfigSurface/changeSetPayloads';
import { clearConsumedOpenIntent, replaceWorkbenchQuerySilently, withSurfaceLoadTimeout } from './businessConfigSurface/workbenchUtils';
import { focusActiveEditorPanel, focusSelectedConfigPanelOnMobile } from './businessConfigSurface/workbenchFocus';
const SURFACE_LOAD_TIMEOUT_MS = 20000;
const CORE_DELIVERY_READINESS_SECTIONS = new Set(['form', 'list_search', 'menu', 'approval']);
const route = useRoute();
const router = useRouter();
const session = useSessionStore();
const pageContract = usePageContract('business_config');
const pageSectionEnabled = pageContract.sectionEnabled;
const pageSectionStyle = pageContract.sectionStyle;
const pageSectionTagIs = pageContract.sectionTagIs;
const pageActionIntent = pageContract.actionIntent;
const pageActionTarget = pageContract.actionTarget;
const pageGlobalActions = pageContract.globalActions;
const pageSectionsReady = computed(() => (
  pageSectionEnabled('root', true)
  && pageSectionEnabled('header', true)
  && pageSectionEnabled('coverage', true)
  && pageSectionEnabled('designer', true)
));
const pageSectionContractValid = computed(() => (
  pageSectionTagIs('root', 'section')
  && pageSectionTagIs('header', 'header')
  && pageSectionTagIs('coverage', 'section')
  && pageSectionTagIs('designer', 'section')
));
const pageSectionsFingerprint = computed(() => JSON.stringify([
  pageSectionContractValid.value,
  pageSectionStyle('header'),
  pageSectionStyle('coverage'),
  pageSectionStyle('designer'),
]));
async function executeGlobalPageAction(actionKey: string) {
  await executePageContractAction({
    actionKey,
    router,
    actionIntent: pageActionIntent,
    actionTarget: pageActionTarget,
    query: route.query,
    onRefresh: loadSurface,
  });
}
const loading = ref(false);
const scanLoading = ref(false);
const listSearchBusy = ref(false);
const listSearchSaving = ref(false);
const error = ref('');
const message = ref({ text: '', detail: '' });
const { impactDialog, openImpactDialog, resolveImpactDialog, rollbackConfirm } = useBusinessConfigImpactDialog();
const surface = ref<BusinessConfigSurfacePayload | null>(null);
const coverageScan = ref<BusinessConfigCoverageScanPayload | null>(null);
const listSearchAudit = ref<BusinessConfigListSearchAuditPayload | null>(null);
const analysisAudit = ref<BusinessConfigAnalysisAuditPayload | null>(null);
const listSearchPanelOpen = ref(false);
const analysisPanelOpen = ref(false);
const selectedRuntimeRoute = ref<BusinessConfigCoverageScanItem['runtime_route'] | null>(null);
const advancedPanelOpen = ref(false);
const surfaceLoadSeq = ref(0);
const scopeModel = ref(String(route.query.model || '').trim());
const scopeActionId = ref(numericQuery('action_id') || 0);
const scopeViewId = ref(numericQuery('view_id') || 0);
const scopeRoleKey = ref(String(route.query.role_key || '').trim());
const selectedPageLabel = ref(String(route.query.page_label || '').trim());
const rootMenuXmlid = computed(() => String(route.query.root_menu_xmlid || '').trim());
const shouldOpenPageList = computed(() => String(route.query[BUSINESS_CONFIG_ROUTE_FLAGS.openPages] || '').trim() === '1');
const shouldOpenListSearch = computed(() => String(route.query.open_list_search || '').trim() === '1');
const shouldOpenAnalysis = computed(() => String(route.query.open_analysis || '').trim() === '1');
const shouldOpenFormConfig = computed(() => String(route.query.open_form_config || '').trim() === '1');

const sections = computed(() => surface.value?.sections || []);
const visibleSections = computed(() => sections.value.filter((section) => {
  if (advancedPanelOpen.value) return true;
  return section.key === 'form'
    || section.key === 'list_search'
    || section.key === 'analysis'
    || section.key === 'menu'
    || section.key === 'approval';
}));
const selectedCoverageRow = computed(() => (coverageScan.value?.items || []).find(coverageRowMatchesScope));
const selectedPageHasFormConfig = computed(() => {
  const row = selectedCoverageRow.value;
  return row ? rowHasFormConfig(row) : true;
});
const selectedPageHasListSearchConfig = computed(() => {
  const row = selectedCoverageRow.value;
  return row ? rowHasListSearchConfig(row) : true;
});
const selectedPageHasAnalysisConfig = computed(() => {
  const row = selectedCoverageRow.value;
  return row ? rowHasAnalysisConfig(row) : false;
});
const visibleConfigSections = computed(() => {
  const result = visibleSections.value.filter((section) => {
    if (section.key === 'form' && currentModelIsRuntimeConfig.value) return false;
    if (section.key === 'form') return selectedPageHasFormConfig.value;
    if (section.key === 'list_search') return selectedPageHasListSearchConfig.value;
    return true;
  });
  if (
    !advancedPanelOpen.value
    && selectedPageHasAnalysisConfig.value
    && !result.some((section) => section.key === 'analysis')
  ) {
    result.push({
      key: 'analysis',
      label: '分析视图配置',
      contract_count: 0,
      intent: BUSINESS_CONFIG_INTENTS.analysisAudit,
      boundary: 'business_contract',
    });
  }
  return result;
});
const currentModel = computed(() => String(scopeModel.value || surface.value?.model || '').trim());
const scopeAction = computed(() => { const parsed = Number(scopeActionId.value || 0); return Number.isFinite(parsed) && parsed > 0 ? Math.trunc(parsed) : undefined; });
const scopeView = computed(() => { const parsed = Number(scopeViewId.value || 0); return Number.isFinite(parsed) && parsed > 0 ? Math.trunc(parsed) : undefined; });
const scopeRole = computed(() => String(scopeRoleKey.value || '').trim() || undefined);
const currentModelIsRuntimeConfig = computed(() => isBusinessConfigRuntimeModel(currentModel.value));
const approvalSection = computed(() => visibleConfigSections.value.find((section) => section.key === 'approval') || null);
const {
  changeSet,
  loading: changeSetLoading,
  publishing: changeSetPublishing,
  previewing: changeSetPreviewing,
  stageItem: stageUnifiedDraftItem,
  validateDraft: validateUnifiedDraft,
  previewDraft,
  publishDraft,
  rollbackPublished,
  discardDraft,
  ensureChangeSet,
  hasUnifiedDraft,
  resetScope: resetUnifiedDraftScope,
} = useBusinessConfigDraftSession(() => scopeRole.value || '');
function resetEditorPanels() {
  listSearchPanelOpen.value = false; listSearchAudit.value = null;
  analysisPanelOpen.value = false; analysisAudit.value = null;
  versionsPanelOpen.value = false; versionContracts.value = [];
}
function runtimeReturnQuery(baseQuery: Record<string, string>, options: Record<string, unknown>) { return buildRuntimeReturnQuery(baseQuery, options); }
const {
  coverageRowKey, coverageRowMatchesScope, coverageRowActionId, coverageRowViewId,
  clearMessage, setMessage, loadSurface, scanCoverage, scanSystemRootCoverage, scanCurrentModel,
  rescanCoverageAfterBootstrap, applyScopeAndLoad, focusScanRow, hydrateSelectedCoverageRowFromScan, openRuntimeRoute,
} = useBusinessConfigScopeLifecycle({ scopeAction, currentModel, scopeView, message, surfaceLoadSeq, loading, error, withSurfaceLoadTimeout, loadBusinessConfigSurface, SURFACE_LOAD_TIMEOUT_MS, scopeRole, session, router, route, surface, scanLoading, coverageScan, scanBusinessConfigCoverage, rootMenuXmlid, selectedPageLabel, scopeModel, scopeActionId, scopeViewId, selectedRuntimeRoute, replaceWorkbenchQuerySilently, focusSelectedConfigPanelOnMobile, resetEditorPanels, runtimeReturnQuery });
const {
  approvalLoading,
  approvalAudit,
  approvalPanelOpen,
  approvalForm,
  approvalSteps,
  approvalStepDragIndex,
  approvalStepDropIndex,
  approvalModeOptions,
  approvalScopeOptions,
  approvalPolicyLabel,
  approvalRuntimeText,
  approvalEffectGuideText,
  approvalImpactSummaryText,
  hasApprovalDraftChanges,
  activeApprovalStepCount,
  approvalValidationMessage,
  canSaveApprovalDraft,
  resetApprovalDraft,
  updateApprovalFormField,
  onApprovalRequiredChange,
  enableApprovalWithDefaultStep,
  loadApprovalConfig,
  saveApprovalConfig,
  addApprovalStep,
  removeApprovalStep,
  moveApprovalStep,
  startApprovalStepDrag,
  dropApprovalStep,
  clearApprovalStepDrag,
} = useBusinessConfigApprovalEditor({
  currentModel,
  selectedPageLabel,
  error,
  setMessage,
  clearMessage,
  loadSurface,
  focusActiveEditorPanel,
  onOpenPanel: () => {
    listSearchPanelOpen.value = false;
    analysisPanelOpen.value = false;
  },
});
const canOpenDesigner = computed(() => Boolean(currentModel.value && scopeAction.value && !currentModelIsRuntimeConfig.value));
const startScopeSummary = computed(() => {
  if (selectedPageLabel.value) return '当前页面配置，只影响这个业务页面';
  if (currentModel.value) return '已选择业务页面，可配置表单、列表、菜单和审批';
  return '先从业务页面目录选择配置对象';
});
const {
  showOnlyIssues,
  pageSearch,
  pageTypeFilter,
  pageTypeOptions,
  configStatusFilter,
  configStatusOptions,
  coverageIssueRows,
  coverageBatchBootstrapRows,
  coverageScopeLabel,
  visibleCoverageRows,
  remediationSummaryItems,
  copyCoverageSummary,
} = useBusinessConfigCoverage({
  coverageScan,
  advancedPanelOpen,
  setMessage,
});
const activeConfigSectionKey = ref(String(route.query.workbench_section || 'form'));
pageSearch.value = String(route.query.workbench_search || '').trim();
const initialPageType = String(route.query.workbench_page_type || '').trim();
if (pageTypeOptions.some((option) => option.key === initialPageType)) {
  pageTypeFilter.value = initialPageType as typeof pageTypeFilter.value;
}
const initialConfigStatus = String(route.query.workbench_config_status || '').trim();
if (configStatusOptions.some((option) => option.key === initialConfigStatus)) configStatusFilter.value = initialConfigStatus as typeof configStatusFilter.value;
const {
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
} = useBusinessConfigSnapshots({
  surface,
  error,
  setMessage,
  clearMessage,
});
const deliveryReadiness = computed(() => surface.value?.delivery_readiness || null);
const deliveryReadinessItems = computed(() => deliveryReadiness.value?.items || []);
const visibleDeliveryReadinessItems = computed(() => {
  const items = deliveryReadinessItems.value;
  if (advancedPanelOpen.value) return items;
  return items.filter((item) => CORE_DELIVERY_READINESS_SECTIONS.has(String(item.section_key || '')));
});
const deliveryReadinessStatusText = computed(() => {
  const items = visibleDeliveryReadinessItems.value;
  if (!deliveryReadiness.value || !items.length) return '读取中';
  return items.every((item) => item.status === 'ready') ? '可交付' : '待处理';
});
const visibleDeliveryReadinessProgressText = computed(() => {
  const items = visibleDeliveryReadinessItems.value;
  if (!deliveryReadiness.value || !items.length) return snapshotSummary.value ? `配置 ${snapshotSummary.value.contract_count}` : '';
  const readyCount = items.filter((item) => item.status === 'ready').length;
  return `${readyCount}/${items.length} 项就绪`;
});
const listSearchPanelDescription = computed(() => (
  advancedPanelOpen.value
    ? '这些配置写入正式业务配置，不写入个人列偏好。'
    : '保存为这个页面的默认列表、搜索和分组设置，不覆盖个人列宽和排序偏好。'
));
const {
  listColumnsText,
  searchFiltersText,
  searchGroupByText,
  pivotMeasuresText,
  pivotDimensionsText,
  graphMeasuresText,
  graphDimensionsText,
  graphType,
  listSearchBase,
  analysisBase,
  listColumnDraft,
  searchFilterDraft,
  searchGroupDraft,
  activeListSearchEditor,
  activeAnalysisEditor,
  listFieldOptionSearch,
  filterFieldOptionSearch,
  groupFieldOptionSearch,
  analysisFieldOptionSearch,
  requestedListSearchTab,
  requestedAnalysisTab,
  listSearchEditorTabs,
  analysisEditorTabs,
  availableListFieldOptions,
  availableFilterFieldOptions,
  availableGroupFieldOptions,
  availableAnalysisFieldOptions,
  hasListSearchDraftChanges,
  hasAnalysisDraftChanges,
  listSearchEditorCount,
  updateListSearchFieldSearch,
  updateListSearchDraft,
  setActiveListSearchEditor,
  setActiveAnalysisEditor,
  resetListSearchDraft,
  fieldOptionAvailableCount,
  analysisEditorState,
  analysisEditorLabel,
  setAnalysisDraft,
  analysisEditorCount, analysisFieldOptionCandidates,
  fieldDisplayLabel,
  fieldOptionHelpText,
  fieldOptionLabel,
  fieldHelpText,
  addListSearchName,
  addVisibleListSearchOptions,
  removeListSearchName,
  moveListSearchName,
  clearChipDrag,
  startListSearchChipDrag,
  hoverListSearchChipDrop,
  dropListSearchChip,
  isListSearchChipDragging,
  isListSearchChipDropTarget,
  addAnalysisName,
  addVisibleAnalysisOptions,
  removeAnalysisName,
  moveAnalysisName,
  startAnalysisChipDrag,
  hoverAnalysisChipDrop,
  dropAnalysisChip,
  isAnalysisChipDragging,
  isAnalysisChipDropTarget,
  resetAnalysisDraft,
} = useBusinessConfigFieldEditors({
  route,
  router,
  listSearchAudit,
  analysisAudit,
  listSearchPanelOpen,
  analysisPanelOpen,
  advancedPanelOpen,
  setMessage,
  clearMessage,
});
const runtimeRouteTarget = computed(() => {
  const runtimeRoute = selectedRuntimeRoute.value || {};
  const runtimePath = String(runtimeRoute.path || '').trim();
  if (runtimePath && !runtimePath.startsWith('/admin/business-config')) {
    return { path: runtimePath, query: runtimeRoute.query || {} };
  }
  if (scopeAction.value) {
    const query: Record<string, string> = {};
    const menuId = String(route.query.menu_id || '').trim();
    if (menuId) query.menu_id = menuId;
    return { path: `/a/${scopeAction.value}`, query };
  }
  return { path: '', query: {} };
});
const runtimeRouteHref = computed(() => (
  runtimeRouteTarget.value.path
    ? router.resolve({ path: runtimeRouteTarget.value.path, query: runtimeRouteTarget.value.query }).href
    : ''
));
function numericQuery(name: string) {
  const parsed = Number(route.query[name] || 0);
  return Number.isFinite(parsed) && parsed > 0 ? Math.trunc(parsed) : undefined;
}

const {
  buildRuntimeReturnQuery,
  openCurrentEffectivePage,
  openMenuConfig,
  openCreateMenuConfig,
  openApprovalConfig,
  openFormConfig,
} = useBusinessConfigNavigation({
  route,
  router,
  session,
  runtimeRouteTarget,
  currentModel,
  selectedPageLabel,
  scopeAction,
  scopeView,
  scopeRole,
  pageSearch,
  pageTypeFilter,
  configStatusFilter,
  activeConfigSectionKey,
  listSearchPanelOpen,
  analysisPanelOpen,
  activeListSearchEditor,
  activeAnalysisEditor,
  canOpenDesigner,
  ensureChangeSetToken: async () => (await ensureChangeSet()).token,
});

const {
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
} = useBusinessConfigVersions({
  currentModel,
  scopeAction,
  scopeView,
  scopeRole,
  selectedPageLabel,
  surface,
  advancedPanelOpen,
  listSearchSaving,
  coverageScan,
  error,
  setMessage,
  clearMessage,
  loadSurface,
  rescanCoverageAfterBootstrap,
  rollbackConfirm,
});
const {
  workbenchCompanyLabel,
  workbenchRoleLabel,
  hasWorkbenchDraftChanges,
  currentEffectiveVersionLabel,
  inspectListSearchDraft,
  inspectAnalysisDraft,
} = useBusinessConfigProductExperience({
  session,
  versionContracts,
  listSearchAudit,
  analysisAudit,
  snapshotSummary,
  hasListSearchDraftChanges,
  hasAnalysisDraftChanges,
  hasApprovalDraftChanges,
  hasUnifiedDraft,
  activeChangeSetToken: computed(() => String(changeSet.value?.token || '')),
  listColumnsText,
  searchFiltersText,
  searchGroupByText,
  listSearchBase,
  listSearchPanelOpen,
  analysisPanelOpen,
  approvalPanelOpen,
  versionsPanelOpen,
  resetListSearchDraft,
  resetAnalysisDraft,
  resetApprovalDraft,
  resetUnifiedDraftScope,
  loadSurface,
  scanSystemRootCoverage,
  setMessage,
  openImpactDialog,
});
const { loadListSearchConfig, loadAnalysisConfig, saveListSearchConfig, saveAnalysisConfig, previewUnifiedDraft, publishUnifiedDraft, rollbackUnifiedDraft, discardUnifiedDraft } = useBusinessConfigPublishLifecycle({ currentModel, listSearchBusy, error, clearMessage, auditBusinessListSearchConfig, scopeAction, scopeView, scopeRole, listSearchAudit, namesToText, normalizeNamesText, listColumnsText, searchFiltersText, searchGroupByText, listSearchBase, activeListSearchEditor, requestedListSearchTab, analysisPanelOpen, approvalPanelOpen, listSearchPanelOpen, focusActiveEditorPanel, setMessage, auditBusinessAnalysisConfig, analysisAudit, pivotMeasuresText, pivotDimensionsText, graphMeasuresText, graphDimensionsText, graphType, analysisBase, activeAnalysisEditor, requestedAnalysisTab, listSearchSaving, hasListSearchDraftChanges, parseNames, stageUnifiedDraftItem, contractTargetKey, listContractPayload, searchContractPayload, hasAnalysisDraftChanges, analysisContractPayload, previewDraft, openImpactDialog, changeSet, publishDraft, loadSurface, rollbackPublished, discardDraft });
const {
  sectionImpactText,
  sectionStatusLabel,
  sectionTaskCoverageText,
  deliveryReadinessItemMetaText,
  runDeliveryReadinessAction,
} = useBusinessConfigWorkbenchMeta({
  selectedCoverageRow,
  selectedPageLabel,
  advancedPanelOpen,
  scanSystemRootCoverage,
  openMenuConfig,
  loadApprovalConfig,
  loadListSearchConfig,
  openFormConfig,
});
const { runRemediationAction, openVersionsForRuntimeGaps, bootstrapMissingContracts, bootstrapCoverageMissing, confirmAndSaveApprovalConfig } = useBusinessConfigRemediationLifecycle({ focusScanRow, loadAnalysisConfig, loadVersions, setMessage, openMenuConfig, loadListSearchConfig, rowBootstrapMissingViewTypes, listSearchSaving, error, clearMessage, bootstrapBusinessFormConfig, coverageRowActionId, coverageRowViewId, scopeRole, bootstrapBusinessListSearchConfig, bootstrapBusinessAnalysisConfig, loadSurface, scanCurrentModel, openFormConfig, coverageBatchBootstrapRows, openImpactDialog, bootstrapCoverageMissingConfig, currentModel, scopeView, rootMenuXmlid, coverageScan, rescanCoverageAfterBootstrap, approvalImpactSummaryText, saveApprovalConfig });

onMounted(() => {
  void (async () => {
    const openPageListOnMount = shouldOpenPageList.value;
    const openFormConfigOnMount = shouldOpenFormConfig.value;
    const openListSearchOnMount = shouldOpenListSearch.value;
    const openAnalysisOnMount = shouldOpenAnalysis.value;
    await loadSurface();
    if (!surface.value || route.path !== '/admin/business-config') return;
    await ensureChangeSet();
    if (openPageListOnMount || !coverageScan.value) {
      await scanSystemRootCoverage();
    }
    if (openFormConfigOnMount && currentModel.value && scopeAction.value) {
      await clearConsumedOpenIntent(['open_form_config']);
      const matched = (coverageScan.value?.items || []).find(coverageRowMatchesScope);
      if (matched) {
        await focusScanRow(matched);
      } else {
        await loadSurface();
      }
    }
    if (openListSearchOnMount && currentModel.value) {
      await clearConsumedOpenIntent(['open_list_search']);
      await loadListSearchConfig();
    }
    if (openAnalysisOnMount && currentModel.value) {
      await clearConsumedOpenIntent(['open_analysis']);
      await loadAnalysisConfig();
    }
    const returnScroll = Number(route.query.workbench_scroll || 0);
    if (Number.isFinite(returnScroll) && returnScroll > 0) {
      await nextTick();
      window.scrollTo({ top: returnScroll, behavior: 'auto' });
    }
  })();
});
</script>

<style src="./businessConfigSurface/style.css"></style>

<template>
  <section
    v-if="pageSectionsReady"
    class="business-config-page sc-page"
    :class="{ 'business-config-page--editor-open': listSearchPanelOpen || approvalPanelOpen || analysisPanelOpen }"
    :style="pageSectionStyle('root')"
    :data-contract-sections="pageSectionsFingerprint"
    data-product-page-mode="admin"
  >
    <header class="business-config-header sc-product-page-header">
      <div>
        <p class="eyebrow">低代码页面设计器</p>
        <h1>{{ designerTitle }}</h1>
      </div>
      <div class="header-actions">
        <button
          v-for="action in pageGlobalActions"
          :key="action.key"
          type="button"
          class="ghost"
          :disabled="action.disabled"
          @click="executeGlobalPageAction(action.key)"
        >
          {{ action.label }}
        </button>
        <button type="button" class="ghost" :disabled="scanLoading" @click="scanSystemRootCoverage">
          {{ scanLoading ? '读取中...' : '选择业务页面' }}
        </button>
        <button type="button" class="ghost" :disabled="loading" @click="advancedPanelOpen = !advancedPanelOpen">
          高级设置
        </button>
      </div>
    </header>

    <div v-if="error" class="status error">{{ error }}</div>
    <div v-else-if="message.text" class="status ok">
      <span>{{ message.text }}</span>
      <small v-if="advancedPanelOpen && message.detail">{{ message.detail }}</small>
    </div>

    <BusinessConfigStartPanel
      v-if="!coverageScan"
      :selected-page-label="selectedPageLabel"
      :current-model="currentModel"
      :start-scope-summary="startScopeSummary"
      :scan-loading="scanLoading"
      :preview-route-path="previewRouteTarget.path"
      :sections="visibleConfigSections"
      :advanced-panel-open="advancedPanelOpen"
      :versions-loading="versionsLoading"
      :list-search-busy="listSearchBusy"
      :approval-loading="approvalLoading"
      :can-open-designer="canOpenDesigner"
      :show-status="Boolean(surface)"
      :delivery-readiness-status-text="deliveryReadinessStatusText"
      :visible-delivery-readiness-progress-text="visibleDeliveryReadinessProgressText"
      :visible-delivery-readiness-items="visibleDeliveryReadinessItems"
      :section-task-kind-label="sectionTaskKindLabel"
      :section-display-label="sectionDisplayLabel"
      :section-status-label="sectionStatusLabel"
      :section-primary-copy="sectionPrimaryCopy"
      :section-impact-text="sectionImpactText"
      :boundary-label="boundaryLabel"
      :section-help-label="sectionHelpLabel"
      :section-task-coverage-text="sectionTaskCoverageText"
      :section-primary-action-label="sectionPrimaryActionLabel"
      :delivery-readiness-item-status-text="deliveryReadinessItemStatusText"
      :delivery-readiness-item-meta-text="deliveryReadinessItemMetaText"
      @scan-system-root-coverage="scanSystemRootCoverage"
      @preview-selected-runtime-route="previewSelectedRuntimeRoute"
      @load-versions="loadVersions"
      @load-list-search-config="loadListSearchConfig"
      @open-form-config="openFormConfig"
      @open-menu-config="openMenuConfig"
      @open-create-menu-config="openCreateMenuConfig"
      @load-analysis-config="loadAnalysisConfig"
      @load-approval-config="loadApprovalConfig"
      @run-delivery-readiness-action="runDeliveryReadinessAction"
    />

    <section v-if="advancedPanelOpen" class="scope-panel">
      <label>
        <span>业务对象</span>
        <input v-model="scopeModel" type="text" placeholder="输入业务对象编码或名称" />
      </label>
      <label>
        <span>页面编号</span>
        <input v-model.number="scopeActionId" type="number" min="0" />
      </label>
      <label>
        <span>视图编号</span>
        <input v-model.number="scopeViewId" type="number" min="0" />
      </label>
      <label>
        <span>角色编码</span>
        <input v-model="scopeRoleKey" type="text" placeholder="可选：按角色范围读取" />
      </label>
      <button type="button" class="ghost small" :disabled="loading" @click="applyScopeAndLoad">读取配置对象</button>
    </section>

    <section v-if="loading" class="loading-state">正在读取配置能力...</section>
    <BusinessConfigCoverageWorkspace
      v-if="coverageScan"
      v-model:page-search="pageSearch"
      v-model:page-type-filter="pageTypeFilter"
      v-model:show-only-issues="showOnlyIssues"
      :coverage-scan="coverageScan"
      :page-type-options="pageTypeOptions"
      :advanced-panel-open="advancedPanelOpen"
      :scan-loading="scanLoading"
      :list-search-saving="listSearchSaving"
      :versions-loading="versionsLoading"
      :loading="loading"
      :surface="surface"
      :current-model="currentModel"
      :selected-page-label="selectedPageLabel"
      :selected-coverage-row="selectedCoverageRow"
      :visible-coverage-rows="visibleCoverageRows"
      :visible-config-sections="visibleConfigSections"
      :coverage-scope-label="coverageScopeLabel"
      :coverage-issue-rows="coverageIssueRows"
      :coverage-batch-bootstrap-rows="coverageBatchBootstrapRows"
      :remediation-summary-items="remediationSummaryItems"
      :preview-route-target="previewRouteTarget"
      :can-open-designer="canOpenDesigner"
      :list-search-busy="listSearchBusy"
      :approval-loading="approvalLoading"
      :delivery-readiness-status-text="deliveryReadinessStatusText"
      :visible-delivery-readiness-progress-text="visibleDeliveryReadinessProgressText"
      :visible-delivery-readiness-items="visibleDeliveryReadinessItems"
      :snapshot-summary="snapshotSummary"
      :coverage-row-key="coverageRowKey"
      :coverage-row-matches-scope="coverageRowMatchesScope"
      :page-view-mode-text="pageViewModeText"
      :row-coverage-progress-text="rowCoverageProgressText"
      :row-action-hint-text="rowActionHintText"
      :page-design-status="pageDesignStatus"
      :runtime-evidence-text="runtimeEvidenceText"
      :runtime-reason-text="runtimeReasonText"
      :visible-row-remediation-actions="visibleRowRemediationActions"
      :view-type-label="viewTypeLabel"
      :severity-label="severityLabel"
      :overall-status-label="overallStatusLabel"
      :boundary-label="boundaryLabel"
      :section-task-kind-label="sectionTaskKindLabel"
      :section-display-label="sectionDisplayLabel"
      :section-status-label="sectionStatusLabel"
      :section-primary-copy="sectionPrimaryCopy"
      :section-impact-text="sectionImpactText"
      :section-help-label="sectionHelpLabel"
      :section-task-coverage-text="sectionTaskCoverageText"
      :section-primary-action-label="sectionPrimaryActionLabel"
      :delivery-readiness-item-status-text="deliveryReadinessItemStatusText"
      :delivery-readiness-item-meta-text="deliveryReadinessItemMetaText"
      @copy-coverage-summary="copyCoverageSummary"
      @bootstrap-coverage-missing="bootstrapCoverageMissing"
      @focus-scan-row="focusScanRow"
      @run-remediation-action="runRemediationAction"
      @preview-selected-runtime-route="previewSelectedRuntimeRoute"
      @load-versions="loadVersions"
      @load-list-search-config="loadListSearchConfig"
      @open-form-config="openFormConfig"
      @open-menu-config="openMenuConfig"
      @open-create-menu-config="openCreateMenuConfig"
      @load-analysis-config="loadAnalysisConfig"
      @load-approval-config="loadApprovalConfig"
      @open-approval-config="openApprovalConfig"
      @run-delivery-readiness-action="runDeliveryReadinessAction"
    />

    <BusinessConfigAdvancedAuditPanels
      v-if="advancedPanelOpen"
      v-model:snapshot-compare-text="snapshotCompareText"
      :coverage-scan="coverageScan"
      :visible-coverage-rows="visibleCoverageRows"
      :snapshot-summary-text="snapshotSummaryText"
      :snapshot-compare-loading="snapshotCompareLoading"
      :snapshot-export-loading="snapshotExportLoading"
      :snapshot-compare-result="snapshotCompareResult"
      :snapshot-compare-summary="snapshotCompareSummary"
      :snapshot-remediation-summary="snapshotRemediationSummary"
      :snapshot-compare-changed-rows="snapshotCompareChangedRows"
      :snapshot-compare-added-rows="snapshotCompareAddedRows"
      :snapshot-compare-removed-rows="snapshotCompareRemovedRows"
      :coverage-row-key="coverageRowKey"
      :severity-label="severityLabel"
      :boundary-label="boundaryLabel"
      :view-type-label="viewTypeLabel"
      :runtime-evidence-text="runtimeEvidenceText"
      :runtime-reason-text="runtimeReasonText"
      @run-remediation-action="runRemediationAction"
      @open-runtime-route="openRuntimeRoute"
      @focus-scan-row="focusScanRow"
      @download-snapshot="downloadSnapshot"
      @compare-snapshot="compareSnapshot"
      @download-snapshot-remediation-plan="downloadSnapshotRemediationPlan"
    />

    <BusinessConfigApprovalPanel
      v-if="approvalPanelOpen"
      :policy-label="approvalPolicyLabel"
      :effect-guide-text="approvalEffectGuideText"
      :runtime-text="approvalRuntimeText"
      :impact-summary-text="approvalImpactSummaryText"
      :boundary-text="boundaryLabel(approvalAudit?.boundary || 'industry_policy_runtime')"
      :form="approvalForm"
      :steps="approvalSteps"
      :mode-options="approvalModeOptions"
      :scope-options="approvalScopeOptions"
      :active-step-count="activeApprovalStepCount"
      :has-draft-changes="hasApprovalDraftChanges"
      :can-save-draft="canSaveApprovalDraft"
      :can-open-full-rule="Boolean(approvalSection?.route?.path)"
      :validation-message="approvalValidationMessage"
      :loading="approvalLoading"
      :advanced-panel-open="advancedPanelOpen"
      :drag-index="approvalStepDragIndex"
      :drop-index="approvalStepDropIndex"
      @close="approvalPanelOpen = false"
      @update-form-field="updateApprovalFormField"
      @approval-required-change="onApprovalRequiredChange"
      @add-step="addApprovalStep"
      @enable-with-default-step="enableApprovalWithDefaultStep"
      @remove-step="removeApprovalStep"
      @move-step="moveApprovalStep"
      @start-step-drag="startApprovalStepDrag"
      @set-step-drop-index="approvalStepDropIndex = $event"
      @drop-step="dropApprovalStep"
      @clear-step-drag="clearApprovalStepDrag"
      @save="saveApprovalConfig"
      @reset="resetApprovalDraft"
      @open-full-rule="approvalSection && openApprovalConfig(approvalSection)"
    />

    <BusinessConfigVersionPanel
      v-if="versionsPanelOpen"
      :title="versionTitle"
      :description="versionPanelDescription"
      :guide="versionPanelGuide"
      :empty-text="versionEmptyText"
      :contracts="versionContracts"
      :loading="versionsLoading"
      :saving="listSearchSaving"
      :view-type-label="viewTypeLabel"
      :contract-display-name="versionContractDisplayName"
      :contract-impact-text="versionContractImpactText"
      :rollback-button-label="versionRollbackButtonLabel"
      :contract-decision-text="versionContractDecisionText"
      :analysis-item-label="analysisItemLabel"
      :version-status-label="versionStatusLabel"
      :version-summary-text="versionSummaryText"
      :version-delta-text="versionDeltaText"
      @close="versionsPanelOpen = false"
      @rollback="rollbackContractFromWorkbench"
    />

    <BusinessConfigEditorPanels
      :analysis-panel-open="analysisPanelOpen"
      :list-search-panel-open="listSearchPanelOpen"
      :list-search-saving="listSearchSaving"
      :preview-route-target="previewRouteTarget"
      :has-analysis-draft-changes="hasAnalysisDraftChanges"
      :has-list-search-draft-changes="hasListSearchDraftChanges"
      :analysis-editor-tabs="analysisEditorTabs"
      :list-search-editor-tabs="listSearchEditorTabs"
      :active-analysis-editor="activeAnalysisEditor"
      :active-list-search-editor="activeListSearchEditor"
      :graph-type="graphType"
      :analysis-field-option-search="analysisFieldOptionSearch"
      :list-field-option-search="listFieldOptionSearch"
      :filter-field-option-search="filterFieldOptionSearch"
      :group-field-option-search="groupFieldOptionSearch"
      :list-column-draft="listColumnDraft"
      :search-filter-draft="searchFilterDraft"
      :search-group-draft="searchGroupDraft"
      :advanced-panel-open="advancedPanelOpen"
      :available-analysis-field-options="availableAnalysisFieldOptions"
      :available-list-field-options="availableListFieldOptions"
      :available-filter-field-options="availableFilterFieldOptions"
      :available-group-field-options="availableGroupFieldOptions"
      :list-columns-text="listColumnsText"
      :search-filters-text="searchFiltersText"
      :search-group-by-text="searchGroupByText"
      :list-search-panel-description="listSearchPanelDescription"
      :list-search-audit="listSearchAudit"
      :analysis-audit="analysisAudit"
      :parse-names="parseNames"
      :analysis-editor-state="analysisEditorState"
      :analysis-editor-label="analysisEditorLabel"
      :analysis-editor-count="analysisEditorCount"
      :analysis-field-option-candidates="analysisFieldOptionCandidates"
      :list-search-editor-count="listSearchEditorCount"
      :field-option-available-count="fieldOptionAvailableCount"
      :field-display-label="fieldDisplayLabel"
      :field-help-text="fieldHelpText"
      :field-option-help-text="fieldOptionHelpText"
      :field-option-label="fieldOptionLabel"
      :is-analysis-chip-dragging="isAnalysisChipDragging"
      :is-analysis-chip-drop-target="isAnalysisChipDropTarget"
      :is-list-search-chip-dragging="isListSearchChipDragging"
      :is-list-search-chip-drop-target="isListSearchChipDropTarget"
      :boundary-label="boundaryLabel"
      :view-type-label="viewTypeLabel"
      @preview-analysis-config="previewAnalysisConfig"
      @save-analysis-config="saveAnalysisConfig"
      @reset-analysis-draft="resetAnalysisDraft"
      @set-active-analysis-editor="setActiveAnalysisEditor"
      @update-analysis-search="analysisFieldOptionSearch = $event"
      @set-analysis-draft="setAnalysisDraft"
      @update-graph-type="graphType = $event"
      @add-analysis-name="addAnalysisName"
      @add-visible-analysis-options="addVisibleAnalysisOptions"
      @remove-analysis-name="removeAnalysisName"
      @move-analysis-name="moveAnalysisName"
      @start-analysis-chip-drag="startAnalysisChipDrag"
      @hover-analysis-chip-drop="hoverAnalysisChipDrop"
      @drop-analysis-chip="dropAnalysisChip"
      @clear-chip-drag="clearChipDrag"
      @close-list-search="listSearchPanelOpen = false"
      @preview-list-search-config="previewListSearchConfig"
      @save-list-search-config="saveListSearchConfig"
      @reset-list-search-draft="resetListSearchDraft"
      @set-active-list-search-editor="setActiveListSearchEditor"
      @update-list-search-search="updateListSearchFieldSearch"
      @update-list-search-draft="updateListSearchDraft"
      @add-list-search-name="addListSearchName"
      @add-visible-list-search-options="addVisibleListSearchOptions"
      @remove-list-search-name="removeListSearchName"
      @move-list-search-name="moveListSearchName"
      @start-list-search-chip-drag="startListSearchChipDrag"
      @hover-list-search-chip-drop="hoverListSearchChipDrop"
      @drop-list-search-chip="dropListSearchChip"
    />

  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import BusinessConfigAdvancedAuditPanels from './businessConfigSurface/BusinessConfigAdvancedAuditPanels.vue';
import BusinessConfigApprovalPanel from './businessConfigSurface/BusinessConfigApprovalPanel.vue';
import BusinessConfigCoverageWorkspace from './businessConfigSurface/BusinessConfigCoverageWorkspace.vue';
import BusinessConfigEditorPanels from './businessConfigSurface/BusinessConfigEditorPanels.vue';
import BusinessConfigStartPanel from './businessConfigSurface/BusinessConfigStartPanel.vue';
import BusinessConfigVersionPanel from './businessConfigSurface/BusinessConfigVersionPanel.vue';
import {
  auditBusinessAnalysisConfig,
  auditBusinessListSearchConfig,
  bootstrapBusinessAnalysisConfig,
  bootstrapBusinessFormConfig,
  bootstrapBusinessListSearchConfig,
  bootstrapCoverageMissingConfig,
  loadBusinessConfigSurface,
  saveBusinessAnalysisConfig,
  saveBusinessListSearchConfig,
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
  BUSINESS_CONFIG_MODES,
  BUSINESS_CONFIG_MODELS,
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
import { findMenuConfigNavigationEntry } from './businessConfigSurface/navigation';
import { useBusinessConfigApprovalEditor } from './businessConfigSurface/useBusinessConfigApprovalEditor';
import { useBusinessConfigCoverage } from './businessConfigSurface/useBusinessConfigCoverage';
import { useBusinessConfigFieldEditors } from './businessConfigSurface/useBusinessConfigFieldEditors';
import { useBusinessConfigSnapshots } from './businessConfigSurface/useBusinessConfigSnapshots';
import { useBusinessConfigVersions } from './businessConfigSurface/useBusinessConfigVersions';
import { useBusinessConfigWorkbenchMeta } from './businessConfigSurface/useBusinessConfigWorkbenchMeta';
import { clearConsumedOpenIntent, replaceWorkbenchQuerySilently, withSurfaceLoadTimeout } from './businessConfigSurface/workbenchUtils';

const SURFACE_LOAD_TIMEOUT_MS = 20000;
const ACTIVE_EDITOR_SCROLL_OPTIONS = { block: 'start', behavior: 'auto' } as const;
const ACTIVE_EDITOR_VIEWPORT_TOP = 96;
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

async function focusActiveEditorPanel() {
  await nextTick();
  const panel = document.querySelector<HTMLElement>('.config-editor-panel');
  if (!panel) return;
  await new Promise<void>((resolve) => window.requestAnimationFrame(() => resolve()));
  const scrollContainer = panel.closest<HTMLElement>('.content');
  const rect = panel.getBoundingClientRect();
  if (scrollContainer) {
    const containerRect = scrollContainer.getBoundingClientRect();
    scrollContainer.scrollBy({
      top: rect.top - containerRect.top - ACTIVE_EDITOR_VIEWPORT_TOP,
      behavior: 'auto',
    });
    return;
  }
  window.scrollBy({ top: rect.top - ACTIVE_EDITOR_VIEWPORT_TOP, behavior: 'auto' });
}

async function focusSelectedConfigPanelOnMobile() {
  await nextTick();
  if (!window.matchMedia('(max-width: 900px)').matches) return;
  const panel = document.querySelector<HTMLElement>('.page-config-panel');
  panel?.scrollIntoView(ACTIVE_EDITOR_SCROLL_OPTIONS);
}
const pageSectionsReady = computed(() => (
  pageSectionEnabled('root', true)
  && pageSectionEnabled('header', true)
  && pageSectionEnabled('coverage', true)
  && pageSectionEnabled('designer', true)
  && pageSectionTagIs('root', 'section')
  && pageSectionTagIs('header', 'header')
  && pageSectionTagIs('coverage', 'section')
  && pageSectionTagIs('designer', 'section')
));
const pageSectionsFingerprint = computed(() => JSON.stringify([
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
const rollbackConfirm = {
  async open(options: { message: string }) {
    return window.confirm(options.message);
  },
};
const surface = ref<BusinessConfigSurfacePayload | null>(null);
const coverageScan = ref<BusinessConfigCoverageScanPayload | null>(null);
const listSearchAudit = ref<BusinessConfigListSearchAuditPayload | null>(null);
const analysisAudit = ref<BusinessConfigAnalysisAuditPayload | null>(null);
const listSearchPanelOpen = ref(false);
const analysisPanelOpen = ref(false);
const selectedRuntimeRoute = ref<BusinessConfigCoverageScanItem['runtime_route'] | null>(null);
const advancedPanelOpen = ref(false);
let surfaceLoadSeq = 0;
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
const designerTitle = computed(() => {
  const model = currentModel.value || scopeModel.value.trim();
  const pageLabel = selectedPageLabel.value.trim();
  if (pageLabel) return `正在配置：${pageLabel}`;
  return model ? `正在配置：${model}` : '选择一个业务页面开始配置';
});

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
const currentModelIsRuntimeConfig = computed(() => isBusinessConfigRuntimeModel(currentModel.value));
const approvalSection = computed(() => visibleConfigSections.value.find((section) => section.key === 'approval') || null);
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
const previewRouteTarget = computed(() => {
  const runtimeRoute = selectedRuntimeRoute.value || {};
  const runtimePath = String(runtimeRoute.path || '').trim();
  if (runtimePath) return { path: runtimePath, query: runtimeRoute.query || {} };
  if (scopeAction.value) {
    const query: Record<string, string> = {};
    const menuId = String(route.query.menu_id || '').trim();
    if (menuId) query.menu_id = menuId;
    return { path: `/a/${scopeAction.value}`, query };
  }
  return { path: '', query: {} };
});
function numericQuery(name: string) {
  const parsed = Number(route.query[name] || 0);
  return Number.isFinite(parsed) && parsed > 0 ? Math.trunc(parsed) : undefined;
}

const scopeAction = computed(() => {
  const parsed = Number(scopeActionId.value || 0);
  return Number.isFinite(parsed) && parsed > 0 ? Math.trunc(parsed) : undefined;
});

const scopeView = computed(() => {
  const parsed = Number(scopeViewId.value || 0);
  return Number.isFinite(parsed) && parsed > 0 ? Math.trunc(parsed) : undefined;
});

const scopeRole = computed(() => String(scopeRoleKey.value || '').trim() || undefined);

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

function coverageRowKey(row: Pick<BusinessConfigCoverageScanItem, 'model' | 'action_id' | 'view_id'>) {
  return [
    String(row.model || '').trim(),
    Number(row.action_id || 0),
    Number(row.view_id || 0),
  ].join(':');
}

function coverageRowMatchesScope(row: Pick<BusinessConfigCoverageScanItem, 'model' | 'action_id' | 'view_id'>) {
  const actionId = Number(scopeAction.value || 0);
  if (!actionId || Number(row.action_id || 0) !== actionId) return false;
  const rowModel = String(row.model || '').trim();
  const model = String(currentModel.value || '').trim();
  if (model && rowModel && rowModel !== model) return false;
  return Number(row.view_id || 0) === Number(scopeView.value || 0);
}

function coverageRowActionId(row: Pick<BusinessConfigCoverageScanItem, 'action_id'>) {
  return Number(row.action_id || 0) || undefined;
}

function coverageRowViewId(row: Pick<BusinessConfigCoverageScanItem, 'view_id'>) {
  return Number(row.view_id || 0) || undefined;
}

function clearMessage() {
  message.value = { text: '', detail: '' };
}

function setMessage(text: string, detail = '') {
  message.value = { text, detail };
}

async function loadSurface() {
  const seq = ++surfaceLoadSeq;
  loading.value = true;
  error.value = '';
  clearMessage();
  try {
    const nextSurface = await withSurfaceLoadTimeout(
      loadBusinessConfigSurface({
        model: currentModel.value || undefined,
        action_id: scopeAction.value,
        view_id: scopeView.value,
        role_key: scopeRole.value,
      }),
      SURFACE_LOAD_TIMEOUT_MS,
    );
    if (seq !== surfaceLoadSeq) return;
    surface.value = nextSurface;
  } catch (err) {
    if (seq !== surfaceLoadSeq) return;
    error.value = err instanceof Error ? err.message : '业务配置工作台加载失败';
  } finally {
    if (seq === surfaceLoadSeq) {
      loading.value = false;
    }
  }
}

async function scanCoverage() {
  scanLoading.value = true;
  error.value = '';
  clearMessage();
  try {
    coverageScan.value = await scanBusinessConfigCoverage({
      model: currentModel.value || undefined,
      view_id: scopeView.value,
      role_key: scopeRole.value,
      root_menu_xmlid: rootMenuXmlid.value || undefined,
      include_all_root_menu_actions: false,
      limit: 1000,
    });
    hydrateSelectedCoverageRowFromScan();
  } catch (err) {
    error.value = err instanceof Error ? err.message : '业务配置覆盖检查失败';
  } finally {
    scanLoading.value = false;
  }
}

async function scanSystemRootCoverage() {
  scanLoading.value = true;
  error.value = '';
  clearMessage();
  try {
    coverageScan.value = await scanBusinessConfigCoverage({
      model: currentModel.value || undefined,
      view_id: scopeView.value,
      role_key: scopeRole.value,
      root_menu_xmlid: rootMenuXmlid.value || undefined,
      include_all_root_menu_actions: true,
      limit: 1000,
    });
    hydrateSelectedCoverageRowFromScan();
  } catch (err) {
    error.value = err instanceof Error ? err.message : '系统根菜单覆盖检查失败';
  } finally {
    scanLoading.value = false;
  }
}

async function scanCurrentModel() {
  if (!currentModel.value) return;
  scanLoading.value = true;
  error.value = '';
  clearMessage();
  try {
    coverageScan.value = await scanBusinessConfigCoverage({
      model: currentModel.value,
      view_id: scopeView.value,
      role_key: scopeRole.value,
      root_menu_xmlid: rootMenuXmlid.value || undefined,
      include_all_root_menu_actions: Boolean(coverageScan.value?.include_all_root_menu_actions),
      limit: 1000,
    });
    hydrateSelectedCoverageRowFromScan();
  } catch (err) {
    error.value = err instanceof Error ? err.message : '当前业务对象覆盖检查失败';
  } finally {
    scanLoading.value = false;
  }
}

async function rescanCoverageAfterBootstrap() {
  if (coverageScan.value?.include_all_root_menu_actions) {
    await scanSystemRootCoverage();
    return;
  }
  if (coverageScan.value?.model) {
    await scanCurrentModel();
    return;
  }
  await scanCoverage();
}

async function applyScopeAndLoad() {
  listSearchPanelOpen.value = false;
  listSearchAudit.value = null;
  analysisPanelOpen.value = false;
  analysisAudit.value = null;
  versionsPanelOpen.value = false;
  versionContracts.value = [];
  coverageScan.value = null;
  selectedPageLabel.value = '';
  await router.replace({
    path: route.path,
    query: {
      ...route.query,
      model: currentModel.value || undefined,
      action_id: scopeAction.value ? String(scopeAction.value) : undefined,
      view_id: scopeView.value ? String(scopeView.value) : undefined,
      role_key: scopeRole.value || undefined,
      page_label: undefined,
    },
  });
  await loadSurface();
}

async function focusScanRow(row: BusinessConfigCoverageScanItem) {
  scopeModel.value = row.model;
  scopeActionId.value = row.action_id;
  scopeViewId.value = Number(row.view_id || 0);
  selectedPageLabel.value = row.name || row.model;
  selectedRuntimeRoute.value = row.runtime_route || null;
  listSearchPanelOpen.value = false;
  listSearchAudit.value = null;
  analysisPanelOpen.value = false;
  analysisAudit.value = null;
  versionsPanelOpen.value = false;
  versionContracts.value = [];
  replaceWorkbenchQuerySilently({
    model: row.model || undefined,
    action_id: row.action_id ? String(row.action_id) : undefined,
    view_id: row.view_id ? String(row.view_id) : undefined,
    role_key: scopeRole.value || undefined,
    page_label: row.name || undefined,
    open_list_search: undefined,
  });
  await loadSurface();
  await focusSelectedConfigPanelOnMobile();
}

function hydrateSelectedCoverageRowFromScan() {
  const matched = (coverageScan.value?.items || []).find(coverageRowMatchesScope);
  if (!matched) return;
  scopeModel.value = matched.model || scopeModel.value;
  scopeActionId.value = matched.action_id || scopeActionId.value;
  scopeViewId.value = Number(matched.view_id || scopeViewId.value || 0);
  selectedPageLabel.value = matched.name || selectedPageLabel.value || matched.model;
  selectedRuntimeRoute.value = matched.runtime_route || selectedRuntimeRoute.value;
}

async function openRuntimeRoute(row: BusinessConfigCoverageScanItem) {
  const runtimeRoute = row.runtime_route || {};
  const path = String(runtimeRoute.path || '').trim();
  if (!path) return;
  await router.push({
    path,
    query: buildPreviewRuntimeQuery(runtimeRoute.query || {}, {
      model: row.model,
      actionId: row.action_id,
      viewId: row.view_id,
      pageLabel: row.name || row.model,
    }),
  });
}

function buildPreviewRuntimeQuery(
  baseQuery: Record<string, string> = {},
  options: { model?: string; actionId?: number; viewId?: number; pageLabel?: string; preserveEditorContext?: boolean } = {},
) {
  const preserveEditorContext = Boolean(options.preserveEditorContext);
  return {
    ...baseQuery,
    root_menu_xmlid: route.query.root_menu_xmlid || undefined,
    page_label: options.pageLabel || selectedPageLabel.value || undefined,
    [BUSINESS_CONFIG_ROUTE_FLAGS.returnToBusinessConfig]: '1',
    [BUSINESS_CONFIG_ROUTE_FLAGS.openPages]: '1',
    model: options.model || currentModel.value || undefined,
    action_id: options.actionId ? String(options.actionId) : (scopeAction.value ? String(scopeAction.value) : undefined),
    view_id: options.viewId ? String(options.viewId) : (scopeView.value ? String(scopeView.value) : undefined),
    list_search_tab: preserveEditorContext && listSearchPanelOpen.value && activeListSearchEditor.value !== 'list' ? activeListSearchEditor.value : undefined,
    open_list_search: preserveEditorContext && listSearchPanelOpen.value ? '1' : undefined,
    analysis_tab: preserveEditorContext && analysisPanelOpen.value && activeAnalysisEditor.value !== 'pivotMeasure' ? activeAnalysisEditor.value : undefined,
    open_analysis: preserveEditorContext && analysisPanelOpen.value ? '1' : undefined,
  };
}

async function previewSelectedRuntimeRoute() {
  const target = previewRouteTarget.value;
  const path = String(target.path || '').trim();
  if (!path) return;
  await router.push({
    path,
    query: buildPreviewRuntimeQuery(target.query || {}, { preserveEditorContext: true }),
  });
}

async function runRemediationAction(row: BusinessConfigCoverageScanItem, action: BusinessConfigRemediationAction) {
  await focusScanRow(row);
  if (action.code === 'configure_contract') {
    if (
      row.runtime_missing_view_types.some((viewType) => ['calendar', 'dashboard'].includes(viewType))
      && !row.runtime_missing_view_types.some((viewType) => ['form', 'tree', 'search', 'pivot', 'graph'].includes(viewType))
    ) {
      await loadAnalysisConfig();
      return;
    }
    await bootstrapMissingContracts(row);
    return;
  }
  if (action.code === 'fix_scope') {
    await openVersionsForRuntimeGaps(row);
    setMessage('请检查配置作用域', '当前配置已存在但未命中这个业务页面，请确认页面、视图或角色范围。');
    return;
  }
  if (action.code === 'publish_contract') {
    await openVersionsForRuntimeGaps(row);
    return;
  }
  if (action.code === 'configure_menu') {
    openMenuConfig();
    return;
  }
  if (action.code === 'review_user_preference_boundary') {
    await loadListSearchConfig();
  }
}

async function openVersionsForRuntimeGaps(row: BusinessConfigCoverageScanItem) {
  if (row.runtime_missing_view_types.some((viewType) => viewType === 'tree' || viewType === 'search')) {
    await loadVersions('list_search');
  } else if (row.runtime_missing_view_types.some((viewType) => ['pivot', 'graph', 'calendar', 'dashboard'].includes(viewType))) {
    await loadVersions('analysis');
  } else {
    await loadVersions('form');
  }
}

async function bootstrapMissingContracts(row: BusinessConfigCoverageScanItem) {
  if (!row.model) return;
  const missingContractTypes = rowBootstrapMissingViewTypes(row, ['form', 'tree', 'search', 'pivot', 'graph']);
  if (!missingContractTypes.length) {
    await openVersionsForRuntimeGaps(row);
    setMessage('没有可自动生成的配置项', '当前项目需要检查发布状态或配置作用域。');
    return;
  }
  listSearchSaving.value = true;
  error.value = '';
  clearMessage();
  let savedCount = 0;
  let formFieldCount = 0;
  try {
    if (missingContractTypes.includes('form')) {
      const formResult = await bootstrapBusinessFormConfig({
        model: row.model,
        action_id: coverageRowActionId(row),
        view_id: coverageRowViewId(row),
        role_key: scopeRole.value,
        publish: true,
      });
      savedCount += 1;
      formFieldCount = formResult.field_count || 0;
    }
    const listSearchTypes = missingContractTypes
      .filter((viewType) => viewType === 'tree' || viewType === 'search');
    if (listSearchTypes.length) {
      const listResult = await bootstrapBusinessListSearchConfig({
        model: row.model,
        action_id: coverageRowActionId(row),
        view_id: coverageRowViewId(row),
        role_key: scopeRole.value,
        view_types: listSearchTypes,
        publish: true,
      });
      savedCount += listResult.saved_count || 0;
    }
    const analysisTypes = missingContractTypes
      .filter((viewType) => viewType === 'pivot' || viewType === 'graph');
    if (analysisTypes.length) {
      const analysisResult = await bootstrapBusinessAnalysisConfig({
        model: row.model,
        action_id: coverageRowActionId(row),
        view_id: coverageRowViewId(row),
        role_key: scopeRole.value,
        view_types: analysisTypes,
        publish: true,
      });
      savedCount += analysisResult.saved_count || 0;
    }
    await loadSurface();
    await scanCurrentModel();
    setMessage(
      '已补齐配置',
      formFieldCount ? `已发布 ${savedCount} 个业务配置，表单字段 ${formFieldCount}` : `已发布 ${savedCount} 个业务配置`,
    );
  } catch (err) {
    error.value = err instanceof Error ? err.message : '业务配置补齐失败，已打开手工配置';
    if (missingContractTypes.includes('form')) {
      openFormConfig();
    } else {
      await loadListSearchConfig();
    }
  } finally {
    listSearchSaving.value = false;
  }
}

async function bootstrapCoverageMissing() {
  if (!coverageBatchBootstrapRows.value.length) return;
  listSearchSaving.value = true;
  error.value = '';
  clearMessage();
  try {
    const result = await bootstrapCoverageMissingConfig({
      model: currentModel.value || undefined,
      view_id: scopeView.value,
      role_key: scopeRole.value,
      root_menu_xmlid: rootMenuXmlid.value || undefined,
      include_all_root_menu_actions: Boolean(coverageScan.value?.include_all_root_menu_actions),
      limit: 1000,
      batch_limit: 300,
    });
    await rescanCoverageAfterBootstrap();
    const failedNames = (result.results || [])
      .filter((item) => !item.ok)
      .map((item) => item.name || item.model || String(item.action_id || ''))
      .filter(Boolean)
      .slice(0, 5)
      .join('、');
    setMessage(
      result.failed_count ? '已批量补齐配置，部分页面需手工处理' : '已批量补齐配置',
      result.failed_count
        ? `已发布 ${result.saved_count} 个业务配置，${result.failed_count} 个页面需手工处理${failedNames ? `：${failedNames}` : ''}`
        : `已发布 ${result.saved_count} 个业务配置`,
    );
  } catch (err) {
    error.value = err instanceof Error ? err.message : '批量补齐业务配置失败';
  } finally {
    listSearchSaving.value = false;
  }
}

async function loadListSearchConfig() {
  if (!currentModel.value) return;
  listSearchBusy.value = true;
  error.value = '';
  clearMessage();
  try {
    const result = await auditBusinessListSearchConfig({
      model: currentModel.value,
      action_id: scopeAction.value,
      view_id: scopeView.value,
      role_key: scopeRole.value,
    });
    listSearchAudit.value = result;
    const configuredListColumns = result.business_config_list_columns || [];
    const configuredSearchFilters = result.business_config_search_filters || [];
    const configuredSearchGroupBy = result.business_config_search_group_by || [];
    const suggestedListColumns = configuredListColumns.length ? [] : result.suggested_list_columns || [];
    const suggestedSearchFilters = (configuredSearchFilters.length || configuredSearchGroupBy.length) ? [] : result.suggested_search_filters || [];
    const suggestedSearchGroupBy = (configuredSearchFilters.length || configuredSearchGroupBy.length) ? [] : result.suggested_search_group_by || [];
    listColumnsText.value = namesToText(configuredListColumns.length ? configuredListColumns : suggestedListColumns);
    searchFiltersText.value = namesToText(configuredSearchFilters.length ? configuredSearchFilters : suggestedSearchFilters);
    searchGroupByText.value = namesToText(configuredSearchGroupBy.length ? configuredSearchGroupBy : suggestedSearchGroupBy);
    listSearchBase.value = {
      list: normalizeNamesText(namesToText(configuredListColumns)),
      filter: normalizeNamesText(namesToText(configuredSearchFilters)),
      group: normalizeNamesText(namesToText(configuredSearchGroupBy)),
    };
    activeListSearchEditor.value = requestedListSearchTab.value;
    analysisPanelOpen.value = false;
    approvalPanelOpen.value = false;
    listSearchPanelOpen.value = true;
    await focusActiveEditorPanel();
    if (!configuredListColumns.length && suggestedListColumns.length) {
      setMessage('已按当前页面生成列表草稿', '调整后点击保存列表与搜索，才会发布为正式业务配置');
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '列表与搜索设置读取失败';
  } finally {
    listSearchBusy.value = false;
  }
}

async function loadAnalysisConfig() {
  if (!currentModel.value) return;
  listSearchBusy.value = true;
  error.value = '';
  clearMessage();
  try {
    const result = await auditBusinessAnalysisConfig({
      model: currentModel.value,
      action_id: scopeAction.value,
      view_id: scopeView.value,
      role_key: scopeRole.value,
    });
    analysisAudit.value = result;
    const configuredPivotMeasures = result.pivot_measures || [];
    const configuredPivotDimensions = result.pivot_dimensions || [];
    const configuredGraphMeasures = result.graph_measures || [];
    const configuredGraphDimensions = result.graph_dimensions || [];
    const suggestedPivotMeasures = (configuredPivotMeasures.length || configuredPivotDimensions.length) ? [] : result.suggested_pivot_measures || [];
    const suggestedPivotDimensions = (configuredPivotMeasures.length || configuredPivotDimensions.length) ? [] : result.suggested_pivot_dimensions || [];
    const suggestedGraphMeasures = (configuredGraphMeasures.length || configuredGraphDimensions.length) ? [] : result.suggested_graph_measures || [];
    const suggestedGraphDimensions = (configuredGraphMeasures.length || configuredGraphDimensions.length) ? [] : result.suggested_graph_dimensions || [];
    const configuredGraphType = (configuredGraphMeasures.length || configuredGraphDimensions.length) ? result.graph_type || 'bar' : '';
    pivotMeasuresText.value = namesToText(configuredPivotMeasures.length ? configuredPivotMeasures : suggestedPivotMeasures);
    pivotDimensionsText.value = namesToText(configuredPivotDimensions.length ? configuredPivotDimensions : suggestedPivotDimensions);
    graphMeasuresText.value = namesToText(configuredGraphMeasures.length ? configuredGraphMeasures : suggestedGraphMeasures);
    graphDimensionsText.value = namesToText(configuredGraphDimensions.length ? configuredGraphDimensions : suggestedGraphDimensions);
    graphType.value = configuredGraphType || result.suggested_graph_type || result.graph_type || 'bar';
    analysisBase.value = {
      pivotMeasures: normalizeNamesText(namesToText(configuredPivotMeasures)),
      pivotDimensions: normalizeNamesText(namesToText(configuredPivotDimensions)),
      graphMeasures: normalizeNamesText(namesToText(configuredGraphMeasures)),
      graphDimensions: normalizeNamesText(namesToText(configuredGraphDimensions)),
      graphType: configuredGraphType || 'bar',
    };
    listSearchPanelOpen.value = false;
    approvalPanelOpen.value = false;
    analysisPanelOpen.value = true;
    activeAnalysisEditor.value = requestedAnalysisTab.value;
    await focusActiveEditorPanel();
    if (
      (!configuredPivotMeasures.length && !configuredPivotDimensions.length && (suggestedPivotMeasures.length || suggestedPivotDimensions.length))
      || (!configuredGraphMeasures.length && !configuredGraphDimensions.length && (suggestedGraphMeasures.length || suggestedGraphDimensions.length))
    ) {
      setMessage('已按当前页面生成分析草稿', '调整后点击保存分析视图，才会发布为正式业务配置');
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '分析视图设置读取失败';
  } finally {
    listSearchBusy.value = false;
  }
}

async function saveListSearchConfig() {
  if (!currentModel.value || !hasListSearchDraftChanges.value) return false;
  listSearchSaving.value = true;
  error.value = '';
  clearMessage();
  try {
    const result = await saveBusinessListSearchConfig({
      model: currentModel.value,
      action_id: scopeAction.value,
      view_id: scopeView.value,
      role_key: scopeRole.value,
      list_columns: parseNames(listColumnsText.value),
      search_filters: parseNames(searchFiltersText.value),
      search_group_by: parseNames(searchGroupByText.value),
      publish: true,
    });
    await loadSurface();
    await loadListSearchConfig();
    if (coverageScan.value) {
      await rescanCoverageAfterBootstrap();
    }
    if (versionsPanelOpen.value && activeVersionSection.value === 'list_search') {
      await loadVersions('list_search');
    }
    setMessage('列表与搜索配置已保存并发布', `已保存 ${result.saved_count} 个业务配置，刷新页面后按新配置生效`);
    return true;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '列表与搜索设置保存失败';
    return false;
  } finally {
    listSearchSaving.value = false;
  }
}

async function saveAnalysisConfig() {
  if (!currentModel.value || !hasAnalysisDraftChanges.value) return false;
  listSearchSaving.value = true;
  error.value = '';
  clearMessage();
  try {
    const result = await saveBusinessAnalysisConfig({
      model: currentModel.value,
      action_id: scopeAction.value,
      view_id: scopeView.value,
      role_key: scopeRole.value,
      pivot_measures: parseNames(pivotMeasuresText.value),
      pivot_dimensions: parseNames(pivotDimensionsText.value),
      graph_measures: parseNames(graphMeasuresText.value),
      graph_dimensions: parseNames(graphDimensionsText.value),
      graph_type: graphType.value || 'bar',
      publish: true,
    });
    await loadSurface();
    await loadAnalysisConfig();
    if (coverageScan.value) {
      await rescanCoverageAfterBootstrap();
    }
    if (versionsPanelOpen.value && activeVersionSection.value === 'analysis') {
      await loadVersions('analysis');
    }
    setMessage('分析视图配置已保存并发布', `已保存 ${result.saved_count} 个业务配置，刷新页面后按新配置生效`);
    return true;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '分析视图设置保存失败';
    return false;
  } finally {
    listSearchSaving.value = false;
  }
}

async function previewListSearchConfig() {
  if (hasListSearchDraftChanges.value) {
    const saved = await saveListSearchConfig();
    if (!saved) return;
  }
  await previewSelectedRuntimeRoute();
}

async function previewAnalysisConfig() {
  if (hasAnalysisDraftChanges.value) {
    const saved = await saveAnalysisConfig();
    if (!saved) return;
  }
  await previewSelectedRuntimeRoute();
}

function menuConfigWorkbenchReturnQuery() {
  const menuEntry = findMenuConfigNavigationEntry(session.menuTree || [], BUSINESS_CONFIG_MODELS.menuConfigPolicy);
  return {
    menu_id: menuEntry?.menuId ? String(menuEntry.menuId) : undefined,
    action_id: menuEntry?.actionId ? String(menuEntry.actionId) : undefined,
    root_menu_xmlid: route.query.root_menu_xmlid || undefined,
    [BUSINESS_CONFIG_ROUTE_FLAGS.returnToBusinessConfig]: '1',
    [BUSINESS_CONFIG_ROUTE_FLAGS.openPages]: route.query[BUSINESS_CONFIG_ROUTE_FLAGS.openPages] || '1',
    [BUSINESS_CONFIG_ROUTE_FLAGS.returnModel]: currentModel.value || undefined,
    [BUSINESS_CONFIG_ROUTE_FLAGS.returnActionId]: scopeAction.value ? String(scopeAction.value) : undefined,
    [BUSINESS_CONFIG_ROUTE_FLAGS.returnMenuId]: route.query.menu_id || undefined,
    [BUSINESS_CONFIG_ROUTE_FLAGS.returnPageLabel]: selectedPageLabel.value || undefined,
    [BUSINESS_CONFIG_ROUTE_FLAGS.returnViewId]: scopeView.value ? String(scopeView.value) : undefined,
    [BUSINESS_CONFIG_ROUTE_FLAGS.returnRoleKey]: scopeRole.value || undefined,
  };
}

function openMenuConfig() {
  router.push({
    path: '/admin/menu-config',
    query: menuConfigWorkbenchReturnQuery(),
  });
}

function openCreateMenuConfig() {
  router.push({
    path: '/admin/menu-config',
    query: {
      ...menuConfigWorkbenchReturnQuery(),
      create_menu: '1',
    },
  });
}

function openApprovalConfig(section: BusinessConfigSurfacePayload['sections'][number]) {
  const path = String(section.route?.path || '').trim();
  if (!path) return;
  router.push({
    path,
    query: {
      ...(section.route?.query || {}),
      [BUSINESS_CONFIG_ROUTE_FLAGS.returnToBusinessConfig]: '1',
      root_menu_xmlid: route.query.root_menu_xmlid || undefined,
      page_label: selectedPageLabel.value || undefined,
    },
  });
}

function openFormConfig() {
  if (!canOpenDesigner.value) return;
  router.push({
    path: `/f/${encodeURIComponent(currentModel.value)}/new`,
    query: {
      action_id: scopeAction.value ? String(scopeAction.value) : undefined,
      menu_id: route.query.menu_id || undefined,
      root_menu_xmlid: route.query.root_menu_xmlid || undefined,
      view_id: scopeView.value ? String(scopeView.value) : undefined,
      role_key: scopeRole.value || undefined,
      page_label: selectedPageLabel.value || undefined,
      config_mode: BUSINESS_CONFIG_MODES.lowCode,
      [BUSINESS_CONFIG_ROUTE_FLAGS.returnToBusinessConfig]: '1',
    },
  });
}

onMounted(() => {
  void (async () => {
    const openPageListOnMount = shouldOpenPageList.value;
    const openFormConfigOnMount = shouldOpenFormConfig.value;
    const openListSearchOnMount = shouldOpenListSearch.value;
    const openAnalysisOnMount = shouldOpenAnalysis.value;
    await loadSurface();
    if (openPageListOnMount) {
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
  })();
});
</script>

<style scoped src="./businessConfigSurface/style.css"></style>

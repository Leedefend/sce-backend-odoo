/* eslint-disable @typescript-eslint/no-unused-vars, no-extra-boolean-cast, vue/attributes-order */
<template>
  <LayoutShell
    :flow="isProjectIntakeCreateMode"
    :class="['sc-page', { 'contract-form-native-shell': useNativeFormTree }]"
    data-product-page-mode="form"
    :data-v2-shadow-store="String(v2ShadowStoreReady)"
    :data-v2-shadow-widgets="String(v2ShadowWidgetCount)"
    :data-v2-shadow-actions="String(v2ShadowActionCount)"
    :data-v2-shadow-button-statuses="String(v2ShadowButtonStatusCount)"
    :data-v2-shadow-field-codes="String(v2ShadowFieldCodeCount)"
    :data-v2-shadow-field-overlap="String(v2ShadowLegacyFieldOverlapCount)"
    :data-v2-shadow-field-missing="v2ShadowLegacyFieldMissingPreview"
    :data-v2-shadow-layout-source="v2ShadowLayoutSourceKind"
    :data-v2-shadow-global-source="v2ShadowGlobalSourceKind"
    :data-v2-shadow-source-context="v2ShadowSourceContextKind"
    :data-v2-shadow-status-fields="String(v2ShadowStatusFieldCount)"
    :data-v2-shadow-value-fields="String(v2ShadowValueFieldCount)"
    :data-v2-shadow-main-data-fields="String(v2ShadowMainDataFieldCount)"
    :data-v2-shadow-readonly-values="String(v2ShadowReadonlyValueCount)"
    :data-v2-shadow-value-source="v2ShadowValueSourceKind"
    :data-v2-shadow-error="v2ContractDecodeError || '-'"
  >
    <PageHeaderTemplate
      :title="pageDisplayTitle"
      :subtitle="pageDisplaySubtitle || undefined"
      :hide-title="suppressPageHeaderTitle"
    >
      <template #meta>
        <p v-if="showHud" class="meta">model={{ model }} · id={{ recordIdDisplay }} · action={{ actionId || '-' }}</p>
        <p v-if="showHud && contractMetaLine" class="meta">{{ contractMetaLine }}</p>
      </template>
      <template #status>
        <template v-if="isProjectIntakeCreateMode">
          <p class="header-status-item">当前进度：{{ intakeRequiredSummary }}</p>
          <p class="header-status-item" :class="{ 'header-status-item--danger': intakeMissingSummary !== '无' }">缺少：{{ intakeMissingSummary }}</p>
        </template>
        <section v-else-if="nativeStatusbar.visible" class="native-statusbar native-statusbar--header" aria-label="项目状态">
          <button
            v-for="item in nativeStatusbar.states"
            :key="String(item.value)"
            type="button"
            class="native-statusbar-step"
            :class="{
              'native-statusbar-step--active': nativeStatusbar.current === String(item.value),
              'native-statusbar-step--done': nativeStatusbar.reachedValues.includes(String(item.value)),
            }"
            :disabled="busy || nativeStatusbar.readonly"
            @click="setStatusbarValue(String(item.value))"
          >
            {{ item.label }}
          </button>
        </section>
      </template>
      <template #actions>
        <span class="contract-header-action-label">办理操作</span>
        <button
          v-if="showReturnToBusinessConfigAction"
          class="sc-btn sc-btn-ghost sc-btn-sm"
          :disabled="busy"
          @click="returnToBusinessConfigDesigner"
        >
          返回工作台
        </button>
        <button
          v-if="showDraftSaveAction"
          class="sc-btn sc-btn-ghost sc-btn-sm"
          :disabled="draftSaveDisabled"
          @click="() => saveRecord()"
        >
          {{ draftSaveButtonLabel }}
        </button>
        <button
          v-if="showPrimaryBusinessFormAction"
          class="sc-btn sc-btn-primary sc-btn-sm"
          :disabled="primaryFormActionDisabled"
          @click="runPrimaryFormAction"
        >
          {{ submitButtonLabel }}
        </button>
        <button
          v-for="action in headerBusinessActionsVisible"
          :key="`hdr-${action.key}`"
          :class="headerActionButtonClass(action)"
          :disabled="busy || !action.enabled"
          :title="action.hint"
          @click="runAction(action)"
        >
          {{ action.label }}
        </button>
        <span v-if="headerConfigActionsVisible.length" class="contract-header-action-separator" aria-hidden="true" />
        <button
          v-for="action in headerConfigActionsVisible"
          :key="`hdr-config-${action.key}`"
          class="sc-btn sc-btn-ghost sc-btn-sm contract-header-config-action"
          :disabled="busy || !action.enabled"
          :title="action.hint"
          @click="runAction(action)"
        >
          {{ action.label }}
        </button>
        <button v-if="showDiscardAction" class="sc-btn sc-btn-ghost sc-btn-sm" :disabled="busy" @click="discardChanges">{{ formUiLabel('discard') }}</button>
        <button v-if="showDebugActionsVisible && !isProjectIntakeCreateMode" class="sc-btn sc-btn-ghost sc-btn-sm" :disabled="busy || !contract" @click="copyContractJson">复制配置</button>
        <button v-if="showDebugActionsVisible && !isProjectIntakeCreateMode" class="sc-btn sc-btn-ghost sc-btn-sm" :disabled="busy || !contract" @click="exportContractJson">导出配置</button>
        <button v-if="showDebugActionsVisible && !isProjectIntakeCreateMode" class="sc-btn sc-btn-ghost sc-btn-sm" :disabled="busy" @click="reload">{{ formUiLabel('reload') }}</button>
      </template>
    </PageHeaderTemplate>

    <StatusPanel v-if="renderErrorMessage" title="页面打开失败" :message="renderErrorMessage" variant="error" :on-retry="reload" />
    <StatusPanel v-else-if="status === 'loading'" title="正在加载页面..." variant="info" />
    <StatusPanel v-else-if="status === 'error'" title="页面加载失败" :message="errorMessage" variant="error" :on-retry="reload" />

    <section v-else :class="['card', 'sc-panel', 'sc-product-main-surface', { 'card--flow': isProjectIntakeCreateMode }]">
      <ContractFormActionBlocks
        :active-filter-key="activeFilterKey"
        :body-actions="bodyActions"
        :busy="busy"
        :is-project-intake-create-mode="isProjectIntakeCreateMode"
        :search-filters="searchFilters"
        :show-hud="showHud"
        :show-search-filters="showSearchFilters"
        :strict-contract-defaults-summary="strictContractDefaultsSummary"
        :strict-contract-missing-summary="strictContractMissingSummary"
        :use-native-form-tree="useNativeFormTree"
        :warnings="warnings"
        :workflow-evidence-gate-rows="workflowEvidenceGateRows"
        :workflow-transitions="workflowTransitions"
        @open-filter="openFilter"
        @run-action="runAction"
      />

      <section class="form-grid" :class="{ 'form-grid--designer-workspace': showCurrentFormFieldConfigScope }">
        <StatusPanel
          v-if="sceneValidationPanel"
          title="表单校验失败"
          :message="sceneValidationPanel.message"
          :error-code="sceneValidationPanel.code"
          :reason-code="sceneValidationPanel.code"
          :hint="sceneValidationPanel.hint"
          :suggested-action="sceneValidationPanel.suggestedAction"
          variant="error"
        />
        <p v-if="nonSceneValidationErrors.length" class="validation-error">
          {{ nonSceneValidationErrors.join('；') }}
        </p>
        <p v-if="onchangeWarnings.length" class="validation-warn">
          {{ onchangeWarnings.map((item) => item.message || item.title || '').filter(Boolean).join('；') }}
        </p>
        <p v-if="submissionFeedback" class="submission-feedback" :class="`submission-feedback--${submissionFeedback.kind}`">
          {{ submissionFeedback.message }}
        </p>
        <SceneBlocksRenderer
          v-if="showSceneBlocksDebug && sceneReadyFormSurface.sceneBlocks.length"
          :blocks="sceneReadyFormSurface.sceneBlocks"
          @action="handleSceneBlockAction"
        />
        <CurrentFormFieldSettingsPanel
          v-if="showCurrentFormFieldConfigScope"
          v-model:field-search-text="formDesignerFieldSearchText"
          v-model:order-placement="selectedFormSettingsOrderPlacement"
          v-model:order-target-key="selectedFormSettingsOrderTargetKey"
          v-model:selected-field-group-title-edit="selectedFormSettingsFieldGroupTitleEdit"
          :active-tab="formSettingsActiveTab"
          :audit-busy="formConfigAuditBusy"
          :audit-result="formConfigAuditResult"
          :audit-summary="formConfigAuditSummary"
          :busy="busy"
          :field-count="currentFormDesignFieldCount"
          :filtered-field-rows="formDesignerFilteredFieldRows"
          :format-operation-summary="formatFormConfigOperationSummary"
          :format-operation-time="formatFormConfigOperationTime"
          :group-navigator-items="formDesignerGroupNavigatorItems"
          :group-options="currentFormGroupOptions"
          :has-draft-changes="hasCurrentFormFieldDraftChanges"
          :layout-columns="formLayoutColumnsDraft"
          :operation-log="formConfigOperationLog"
          :operation-status-label="formConfigOperationStatusLabel"
          :operator-name="formConfigOperatorName"
          :order-target-options="selectedFormSettingsOrderTargetOptions"
          :scope="formFieldConfigScope"
          :selected-field-group-title="selectedFormSettingsFieldGroupTitle"
          :selected-field-key="selectedFormSettingsFieldKey"
          :selected-field-row="selectedFormSettingsFieldRow"
          :selected-field-size="selectedFormSettingsFieldSize"
          :selected-group-columns="selectedFormSettingsGroupColumns"
          :selected-group-visible="selectedFormSettingsGroupVisible"
          :suggested-hidden-count="suggestedHiddenFieldRows.length"
          @audit="auditCurrentFormConfiguration"
          @clear-operation-log="clearFormConfigOperationLog"
          @hide-suggested-internal-fields="hideSuggestedInternalFields"
          @layout-columns-change="onFormLayoutColumnsChange"
          @move-selected-field="moveSelectedFormSettingsFieldToOrderTarget"
          @open-custom-field-create="openCentralCustomFieldCreate"
          @preview="previewCurrentFormConfiguration"
          @reset="resetContractFieldOrder"
          @return-to-workbench="returnToBusinessConfigDesigner"
          @save="saveContractFieldOrder"
          @select-field="selectFormDesignerField"
          @select-group="selectFormDesignerGroup"
          @selected-field-group-move-change="onSelectedFormSettingsFieldGroupMoveChange"
          @selected-field-label-change="onSelectedFormSettingsFieldLabelChange"
          @selected-field-size-change="onSelectedFormSettingsFieldSizeChange"
          @selected-field-visibility-change="onSelectedFormSettingsFieldVisibilityChange"
          @selected-group-columns-change="onSelectedFormSettingsGroupColumnsChange"
          @selected-group-title-change="onSelectedFormSettingsGroupTitleChange"
          @selected-group-visibility-change="onSelectedFormSettingsGroupVisibilityChange"
        />
        <ContractFormNativeCanvas
          :button-label-resolver="resolveNativeButtonLabel"
          :collaboration-panel-listeners="nativeCollaborationPanelListeners"
          :collaboration-panel-props="nativeCollaborationPanelProps"
          :designer-mode="showCurrentFormFieldConfigScope"
          :field-actions="isContractFieldOrderEditable ? formSettingsFieldActions : contractFieldActions"
          :field-config-editable="isContractFieldOrderEditable"
          :field-order-count="fieldOrderDraft.length"
          :field-order-dragging-key="draggingFieldKey"
          :field-order-drop-placement="dropTargetPlacement"
          :field-order-drop-target-key="dropTargetFieldKey"
          :field-order-editable="isContractFieldOrderEditable"
          :field-order-index="contractInlineFieldOrderIndex"
          :field-schemas-for-nodes="nativeFieldSchemasForNodes"
          :field-selection-mode="isContractFieldOrderEditable"
          :is-node-visible="isNativeLayoutNodeVisible"
          :layout-nodes="nativeFormLayoutNodes"
          :layout-visibility-revision="nativeLayoutVisibilityRevision"
          :native-action-handler="runNativeLayoutAction"
          :native-action-state-resolver="resolveNativeActionState"
          :relation-adapter="relationFieldAdapter"
          :root-columns="nativeFormRootColumns"
          :selected-field-key="selectedFormSettingsFieldKey"
          :selected-field-row-label="selectedFormSettingsFieldRow?.label || ''"
          :show-collaboration-panel="(nativeChatterActions.length || nativeAttachments) && !isProjectIntakeCreateMode"
          :show-default-section-title="showNativeDefaultSectionTitle"
          :use-native-form-tree="useNativeFormTree"
          @field-action="onContractFieldAction"
          @field-add-after="onContractInlineFieldAddAfter"
          @field-change="onTemplateFieldChange"
          @field-label-change="onContractInlineFieldLabelChange"
          @field-order-drag-end="onContractInlineFieldOrderDragEnd"
          @field-order-drag-leave="onContractInlineFieldOrderDragLeave"
          @field-order-drag-over="onContractInlineFieldOrderDragOver"
          @field-order-drag-start="onContractInlineFieldOrderDragStart"
          @field-order-drop="onContractInlineFieldOrderDrop"
          @field-order-group-drop="onContractInlineFieldOrderGroupDrop"
          @field-order-move="onContractInlineFieldOrderMove"
          @field-select="onFormSettingsFieldSelect"
          @group-add-field="onContractInlineGroupAddField"
          @group-rename="onContractInlineGroupRename"
          @native-action="runNativeLayoutAction"
        />
        <ContractModeSupportPanel
          :active-actions="activeContractModeActions"
          :advanced-expanded="advancedExpanded"
          :busy="busy"
          :low-code-field-create-dialog="lowCodeFieldCreateDialog"
          :low-code-precheck-warnings="lowCodePrecheckWarnings"
          :mode-feedback="contractModeFeedback"
          :prompt-fields="contractPromptFields"
          :prompt-values="contractPromptValues"
          :prompt-visible="Boolean(contractPromptRule)"
          :show-advanced-toggle="hasAdvancedFields && !isProjectIntakeCreateMode && !useNativeFormTree"
          @cancel-prompt="closeContractPromptAction"
          @close-field-create="closeInlineCustomFieldCreate"
          @field-create-label-change="setFieldCreateLabel"
          @field-create-type-change="setFieldCreateType"
          @open-mode-action="openContractModeAction"
          @prompt-value-change="setContractPromptValue($event.fieldName, $event.value)"
          @submit-field-create="submitInlineCustomFieldCreate"
          @submit-prompt="submitContractPromptAction"
          @toggle-advanced="advancedExpanded = !advancedExpanded"
        />
      </section>

      <PageFooterTemplate v-if="isProjectIntakeCreateMode" hint="填写完成后点击“创建项目”">
        <template #default>
          <button class="ghost" :disabled="busy" @click="cancelIntake">取消</button>
          <button class="primary" :disabled="isIntakeCreateDisabled" @click="() => saveRecord()">
            {{ intakeCreateButtonLabel }}
          </button>
        </template>
      </PageFooterTemplate>

      <NativeCollaborationPanel
        v-if="(nativeChatterActions.length || nativeAttachments) && !isProjectIntakeCreateMode && !hasNativeChatterNode"
        v-bind="nativeCollaborationPanelProps"
        v-on="nativeCollaborationPanelListeners"
      />
    </section>

    <DevContextPanel
      :visible="showHud"
      title="表单上下文"
      :entries="hudEntries"
    />
    <ProductConfirmDialog
      :open="actionSafetyConfirm.state.open"
      :title="actionSafetyConfirm.state.title"
      :message="actionSafetyConfirm.state.message"
      :confirm-label="actionSafetyConfirm.state.confirmLabel"
      :cancel-label="actionSafetyConfirm.state.cancelLabel"
      :tone="actionSafetyConfirm.state.tone"
      @confirm="actionSafetyConfirm.confirm"
      @cancel="actionSafetyConfirm.cancel"
    />
    <ProductInputDialog
      :open="actionInputDialog.state.open"
      :title="actionInputDialog.state.title"
      :label="actionInputDialog.state.label"
      :placeholder="actionInputDialog.state.placeholder"
      :value="actionInputDialog.state.value"
      :confirm-label="actionInputDialog.state.confirmLabel"
      :cancel-label="actionInputDialog.state.cancelLabel"
      :required="actionInputDialog.state.required"
      @confirm="actionInputDialog.confirm"
      @cancel="actionInputDialog.cancel"
    />
    <RelationSearchDialog
      :busy="busy"
      :dialog="relationSearchDialog"
      :record-count-label="relationRecordCountLabel"
      @close="closeRelationSearchDialog"
      @confirm="confirmRelationSearchSelection"
      @create="createRelationFromSearchDialog"
      @keyword-change="setRelationSearchKeyword"
      @search="runRelationSearch"
      @select-row="selectRelationSearchRow"
    />
    <AttachmentViewer ref="attachmentViewerRef" />
  </LayoutShell>
</template>

<script setup lang="ts">
import { computed, nextTick, onActivated, onBeforeUnmount, onDeactivated, onErrorCaptured, onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import StatusPanel from '../components/StatusPanel.vue';
import DevContextPanel from '../components/DevContextPanel.vue';
import ProductConfirmDialog from '../components/ProductConfirmDialog.vue';
import ProductInputDialog from '../components/ProductInputDialog.vue';
import AttachmentViewer from '../components/attachment/AttachmentViewer.vue';
import LayoutShell from '../components/template/LayoutShell.vue';
import PageHeaderTemplate from '../components/template/PageHeader.vue';
import { type NativeFormLayoutNode } from '../components/template/NativeFormTreeRenderer.vue';
import SceneBlocksRenderer from '../components/scene/SceneBlocksRenderer.vue';
import PageFooterTemplate from '../components/template/PageFooter.vue';
import NativeCollaborationPanel, {
  type NativeCollaborationPanelListeners,
  type NativeCollaborationPanelProps,
} from './contractForm/NativeCollaborationPanel.vue';
import ContractFormNativeCanvas from './contractForm/ContractFormNativeCanvas.vue';
import RelationSearchDialog from './contractForm/RelationSearchDialog.vue';
import ContractModeSupportPanel from './contractForm/ContractModeSupportPanel.vue';
import CurrentFormFieldSettingsPanel from './contractForm/CurrentFormFieldSettingsPanel.vue';
import ContractFormActionBlocks from './contractForm/ContractFormActionBlocks.vue';
import type {
  FormSectionFieldActionPayload,
  FormSectionFieldSchema,
  FormSectionFieldChange,
} from '../components/template/formSection.types';
import type { RelationFieldAdapter } from '../components/template/relationField.types';
import { createFormSectionFieldSchemaBuilder } from '../components/template/formSection.adapter';
import { resolveInputPlaceholder, resolveSelectPlaceholder } from '../components/template/placeholder.mapper';
import { resolveFieldSpanClass } from '../components/template/fieldSpan.mapper';
import { mapDescriptorSelectionOptions, mapRelationOptions } from '../components/template/option.mapper';
import { dispatchTemplateFieldChange } from '../components/template/fieldChange.dispatcher';
import { isHudEnabled, isSceneBlocksDebugEnabled } from '../config/debug';
import { config } from '../config';
import { useProductConfirmDialog } from '../composables/useProductConfirmDialog';
import { useProductInputDialog } from '../composables/useProductInputDialog';
import { intentRequest } from '../api/intents';
import { loadActionContractRaw, loadModelContractRaw } from '../api/contract';
import { ApiError } from '../api/client';
import { executeButton } from '../api/executeButton';
import { triggerOnchange } from '../api/onchange';
import type { OnchangeLinePatch } from '../api/onchange';
import type { ActionContract, FieldDescriptor } from '@sc/schema';
import { useSessionStore } from '../stores/session';
import { ErrorCodes } from '../app/error_codes';
import {
  detectObjectMethodFromActionKey,
  normalizeActionKind,
  parseMaybeJsonRecord,
  toPositiveInt,
} from '../app/contractRuntime';
import { validateContractFormData } from '../app/contractValidation';
import { resolveActionIdFromContext } from '../app/actionContext';
import { findActionMeta, findActionMetaByMenu, findMenuNode } from '../app/menu';
import { pickContractNavQuery } from '../app/navigationContext';
import { buildCanonicalSceneRouteTarget, buildEntryTargetRouteTarget } from '../app/routeQuery';
import { readWorkspaceContext } from '../app/workspaceContext';
import { collectPolicyValidationErrors, evaluateActionPolicy, evaluateFieldPolicy } from '../app/contractPolicies';
import { buildRuntimeFieldStates } from '../app/modifierEngine';
import { resolveSceneValidationSuggestedAction } from '../app/sceneValidationRecoveryStrategy';
import { findSceneReadyEntry, resolveFormSceneReady } from '../app/resolvers/sceneReadyResolver';
import { normalizeSceneActionProtocol } from '../app/sceneActionProtocol';
import { executeProjectionRefresh } from '../app/projectionRefreshRuntime';
import {
  createContractFormRecord,
  listContractFormRecords,
  readContractFormRecord,
  writeContractFormRecord,
} from '../app/runtime/contractFormDataRuntime';
import {
  collectContractV2ButtonStatusById,
  collectContractV2FieldStatusByCode,
  ContractV2DecodeError,
  createContractV2Store,
  decodeContractV2Snapshot,
  resolveContractV2ContainerTree,
  resolveContractV2FormStructureContract,
  resolveContractV2GlobalStatus,
  resolveContractV2MainData,
  resolveContractV2SourceContext,
  resolveContractV2ValueSource,
  type ContractV2NormalizedStore,
} from '../app/contracts/v2';
import { executeSceneMutation } from '../app/sceneMutationRuntime';
import { isCoreSceneStrictMode } from '../app/contractStrictMode';
import {
  BUSINESS_CONFIG_ACTION_KEYS,
  BUSINESS_CONFIG_INTENTS,
  BUSINESS_CONFIG_MODES,
  BUSINESS_CONFIG_ROUTE_FLAGS,
  FORM_FIELD_CONFIG_INTENTS,
  isBusinessConfigMode,
  isBusinessConfigRuntimeModel,
} from '../app/businessConfigBoundaries';
import {
  collectUnifiedPageContractV2ButtonStatus,
  collectUnifiedPageContractV2FieldContainerStatus,
  collectUnifiedPageContractV2FieldStatus,
  collectUnifiedPageContractV2FieldWidgets,
  resolveUnifiedPageContractV2BusinessOperationProfile,
  resolveUnifiedPageContractV2FieldGroups,
  resolveUnifiedPageContractV2FormStructureContract,
  resolveUnifiedPageContractV2MainData,
  resolveUnifiedPageContractV2,
  resolveUnifiedPageContractV2GlobalStatus,
  resolveUnifiedPageContractV2SourceContext,
  resolveUnifiedPageContractV2VisibleFields,
} from '../app/contracts/unifiedPageContractV2';
import {
  actionResponseNavQuery as actionResponseNavQueryFromResult,
  actionResponseRouteTarget as actionResponseRouteTargetFromResult,
  buildActiveContractModeActions,
  buildContractFieldActionsFromRules,
  buildFormSettingsFieldActions as buildFormSettingsFieldActionsFromRules,
  contractActionRuleClientMode,
  contractActionRuleControl,
  contractActionRuleKey,
  isTierValidationActionHidden as isTierValidationActionHiddenFromState,
  normalizeActionSafety,
  normalizeActionLabel,
  normalizeRequiredParams,
  resolvePrimaryCreateFooterAction,
  resolveV2ButtonStatus,
} from './contractForm/actionContract';
import { normalizeContractAccessPolicy } from './contractForm/accessPolicy';
import {
  fieldInputType,
  fieldType,
  normalizeRelationIds,
  parseMany2oneDisplay,
  sanitizeUiErrorMessage,
  toDateInputValue,
  toDatetimeInputValue,
} from './contractForm/fieldUtils';
import {
  buildFormConfigFieldLabelReplacementEntries,
  buildFormFieldConfigScope,
  buildCurrentFormGroupOptions,
  buildFormDesignerGroupNavigatorItems,
  buildFormDesignerSearchableFieldRows,
  buildLowCodeApplyBaseParams,
  buildLowCodePreviewQuery,
  buildLowCodeReturnQuery,
  buildLowCodeViewOrchestration as buildLowCodeViewOrchestrationFromDraft,
  changedFieldGroupFromDrafts,
  changedFieldVisibilityFromDrafts,
  collectLowCodeLayoutFromViewOrchestration,
  collectNativeFieldStructureGroups,
  effectiveFieldGroupTitleFromDrafts,
  extractLowCodeFormFieldDraftState,
  extractLowCodeLayoutDraftState,
  filterFormDesignerFieldRows,
  formConfigOperationStatusLabel,
  fieldGroupTitleMatches,
  formatFormConfigAuditSummary,
  formConfigSaveOperationSummary as formConfigSaveOperationSummaryFromDraft,
  formatFormConfigOperationSummary as formatFormConfigOperationSummaryText,
  formatFormConfigOperationTime,
  collectNativeLayoutGroupTitles,
  fieldStructureTitle,
  inferLowCodeLayoutColumns,
  isReadableFieldGroupTitle,
  isSuggestedInternalFormField,
  layoutHasReadableFieldGroups,
  lowCodeFormSpecFromViews,
  lowCodeLayoutFieldLabelFromNodes,
  lowCodeLayoutFromFormSpec,
  lowCodeScopedContractName,
  lowCodeViewsFromContractResponse,
  mergeLowCodeLayoutWithRuntimeGroupShells,
  normalizeConfigPageLabel,
  normalizeFieldGroupTitle,
  normalizeFormConfigAuditResult,
  normalizeLowCodeApplyParams,
  normalizeLowCodeContractListRows,
  contractFieldSequenceFromOrder,
  readableFallbackFieldLabel,
  resolveFormDesignFieldLabel,
  resolveSelectedFormSettingsFieldGroupTitle,
  type LowCodeLayoutDraftRow,
} from './contractForm/formConfigHelpers';
import { useFormConfigOperationLog } from './contractForm/useFormConfigOperationLog';
import {
  isMissingRequiredValue,
  isRequiredFieldEmptyByType,
  normalizeContractFieldValue,
  normalizeComparable,
  normalizeRouteDefault,
  resolveNavigationUrl as resolveNavigationUrlFromOrigin,
} from './contractForm/valueUtils';
import { dictOrEmpty, mergeFieldLabelsFromSource } from './contractForm/recordUtils';
import {
  collectFormDataFieldNames,
  collectNativeFormDesignFields,
  collectNativeFavoriteFieldNames,
  collectNativeVisibleFieldNames,
  collectNativeVisibleFieldOrder,
  collectNativeVisibleSectionTitles,
  countNativeNodesByType,
  evaluateNativeModifierValue as evaluateNativeModifierValueWithResolver,
  findNativeFieldNode as findNativeFieldNodeInTree,
  isNativeFieldLayoutNode,
  isStaticTruthyModifier,
  nativeModifierValue,
  nativeFieldSubview as nativeFieldSubviewFromTree,
  nativeFieldPresentation,
  isCreateWorkflowStateField,
  nativeLayoutNodeType,
  nativeNodeFieldDescriptor as nativeNodeFieldDescriptorFromNode,
  nativeNodeWidget,
  nativeNodeWidgetSemantics,
  normalizeContractFieldSemantics,
  normalizeSemanticFieldGroups,
  isNativeActionVisible,
  resolveNativeButtonLabel as resolveNativeButtonLabelFromNode,
  resolveFieldSemanticMeta,
  resolveNativeFormRootColumns,
  semanticFieldNamesBySurfaceRole,
  buildLegacyLayoutNodes,
  buildNativeFieldSchemas,
  applyReadonlyFieldValues,
  applyNativeFieldOrderPreview as applyNativeFieldOrderPreviewFromTree,
  normalizeContractV2ContainersForNativeForm as normalizeContractV2ContainersForNativeFormFromTree,
  shouldShowRequiredMark as shouldShowRequiredMarkFromNativeLayout,
  isNativeFieldVisible as isNativeFieldVisibleFromNativeLayout,
  isNativeLayoutNodeVisible as isNativeLayoutNodeVisibleFromNativeLayout,
  filterVisibleNativeLayoutNodes as filterVisibleNativeLayoutNodesFromTree,
  type FieldSemanticMeta,
  type NativeLayoutLikeNode,
  type SemanticFieldGroup,
} from './contractForm/nativeLayoutUtils';
import {
  formRuntimeCommandHintLabel,
  formRuntimeReasonLabel,
  formRuntimeRowStateLabel,
  one2manyCanCreateFromPolicies,
  one2manyColumnDisplayValue,
  one2manyColumnInputType,
  one2manyCreateLabelFromPolicies,
  one2manyColumnsFromSubview,
  one2manyDraftSummary,
  one2manyPrimaryColumnFromColumns,
  one2manyRowLabelFromPrimary,
  one2manyRowStateLabel,
  selectOne2manySubview,
  one2manySubviewPolicies,
} from './contractForm/one2manyUtils';
import { useOne2manyRuntime } from './contractForm/useOne2manyRuntime';
import {
  dynamicRelationDomainFromDescriptor,
  relationEntry,
  dynamicDomainDependencyFields,
  fallbackRelationSearchColumns,
  hasAmbiguousRelationMatches,
  isBlockAllDomain,
  mergeRelationDomains,
  normalizeRelationSearchColumns,
  normalizeRouteQueryValues,
  relationDomainFromDescriptor,
  relationCreateMode,
  relationInlineCreate,
  relationModel as relationModelFromDescriptor,
  relationOptionsFromRecords,
  relationOrder,
  relationReadFields,
  relationSearchColumnsFromContract,
  relationSearchDialogContract,
  relationSearchLimit,
  relationSearchOrder,
  relationSearchReadFields,
  relationSearchRowsFromRecords,
  relationUiLabel,
  relationUiLabels,
  runtimeRelationDomainFromModifiers,
  resolveRelationQuickFillOption,
  singleContainingRelationOption,
} from './contractForm/relationDescriptor';
import { useRelationRuntime } from './contractForm/useRelationRuntime';
import {
  buildSceneValidationPanel,
  collectSceneValidationPrecheckErrors as collectSceneValidationPrecheckErrorsFromRules,
  sceneValidationErrorPrefix,
  strictContractDefaultsSummary as strictContractDefaultsSummaryFromGuard,
  strictContractGuardFromSceneReadyEntry,
  strictContractMissingSummary as strictContractMissingSummaryFromGuard,
} from './contractForm/sceneValidation';
import {
  isWorkflowTransitionMethod,
  normalizeWorkflowActionRows,
  normalizeWorkflowEvidenceGateRows,
  normalizeNativeFormStatusbar,
  normalizeWorkflowPhaseStatusbar,
  resolveStatusbarSelectionValue,
  workflowActionMethodAliases,
  workflowActionRowForMethod,
} from './contractForm/workflowContract';
import {
  formUiLabelFromLabels,
  formUiLabelsFromFormView,
  resolvePageDisplaySubtitle,
  resolvePageDisplayTitle,
  resolvePageTitle,
  resolveSubmitButtonLabel,
  layoutContainsType,
} from './contractForm/uiLabels';
import {
  activeChatterPlaceholder as activeChatterPlaceholderFromMode,
  activeChatterPostingLabel as activeChatterPostingLabelFromMode,
  activeChatterSubmitLabel as activeChatterSubmitLabelFromMode,
  nativeActivityFieldLabel,
  nativeAttachmentContractOrNull,
  nativeAttachmentLabel,
  nativeAttachmentLabelsFromContract,
  nativeAttachmentMaxBytes as nativeAttachmentMaxBytesFromContract,
  nativeChatterActionsFromContract,
  nativeCollaborationUnavailableMessage as nativeCollaborationUnavailableMessageFromState,
  resolveNativeAttachmentContract,
  resolveNativeChatterContract,
  resolveRuntimeCollaborationContract,
} from './contractForm/collaborationContract';
import {
  MANY2ONE_CREATE_OPTION,
  MANY2ONE_OPEN_RECORD_OPTION,
  MANY2ONE_SEARCH_MORE_OPTION,
  PROJECT_CONTEXT_CHANGED_EVENT,
  ContractAccessPolicyError,
  type BusyKind,
  type ContractAccessPolicy,
  type ContractAction,
  type ContractFieldGovernanceAction,
  type ContractFieldGovernanceRow,
  type FormConfigAuditResult,
  type LayoutNode,
  type LowCodeFieldSize,
  type NativeChatterAction,
  type NativeStatusbarVm,
  type One2ManyColumn,
  type One2ManyInlineRow,
  type RelationOption,
  type RelationSearchColumn,
  type RelationSearchRow,
  type RelationUiLabels,
  type UiStatus,
} from './contractForm/types';
import {
  clearIntakeAutosavePayload,
  persistIntakeAutosavePayload,
  restoreIntakeAutosavePayload,
} from './contractForm/intakeAutosave';
import {
  applyIncomingFormFieldValue,
  snapshotOriginalFormValues,
  type FormRecordHydrationTarget,
} from './contractForm/recordHydration';
import {
  useNativeAttachmentRuntime,
  type NativeAttachmentViewerLike,
} from './contractForm/useNativeAttachmentRuntime';
import { useNativeChatterRuntime } from './contractForm/useNativeChatterRuntime';
import { useFieldOrderDragRuntime } from './contractForm/useFieldOrderDragRuntime';
import { useLowCodeFieldCreateRuntime } from './contractForm/useLowCodeFieldCreateRuntime';
import { useFormSettingsLayoutRuntime } from './contractForm/useFormSettingsLayoutRuntime';
import { useFormSettingsGroupRuntime } from './contractForm/useFormSettingsGroupRuntime';
import { useFieldOrderMutationRuntime } from './contractForm/useFieldOrderMutationRuntime';
import { useFieldVisibilityDraftRuntime } from './contractForm/useFieldVisibilityDraftRuntime';
import { useInlineFieldPolicyRuntime } from './contractForm/useInlineFieldPolicyRuntime';
import { useContractModeActionRuntime } from './contractForm/useContractModeActionRuntime';
import {
  buildWorkflowTransitions,
  analyzeFormContractReadiness,
  buildRouteContractContext,
  collectPrimaryActionRequiredFields,
  collectRuntimeCapabilities,
  collectRuntimeUserGroups,
  contractModelName,
  normalizeContractWarnings,
  normalizeSearchFilters,
  resolveBusinessCategoryContext,
  validateSurfaceMarkers,
  type FormContractReadiness,
} from './contractForm/contractRuntimeVm';

async function collectActionParams(action: ContractAction): Promise<Record<string, unknown> | null> {
  const requiredParams = new Set((action.requiredParams || []).map((item) => item.toLowerCase()));
  if (!action.requiresReason && !requiredParams.has('reason')) return {};
  const reason = (await actionInputDialog.open({
    title: `${action.label || '操作'}原因`,
    label: '操作原因',
    placeholder: '请填写本次操作原因',
    confirmLabel: '继续',
    cancelLabel: '取消',
    required: true,
  }))?.trim() || '';
  if (!reason) {
    errorMessage.value = '请填写操作原因';
    status.value = 'error';
    return null;
  }
  return { reason };
}

const route = useRoute();
const router = useRouter();
const session = useSessionStore();

function resolveWorkspaceContextQuery() {
  return readWorkspaceContext(route.query as Record<string, unknown>);
}

const status = ref<UiStatus>('loading');
const isComponentActive = ref(true);
const instanceRouteIdentity = ref('');
const retainedRouteIdentity = ref('');
const renderErrorMessage = ref('');
const errorMessage = ref('');
const validationErrors = ref<string[]>([]);
const submissionFeedback = ref<{ kind: 'success' | 'warn' | 'error'; message: string } | null>(null);
const showOne2manyErrors = ref(false);
const busyKind = ref<BusyKind>(null);
const activeContractMode = ref('');
const formSettingsActiveTab = ref<'structure' | 'fields' | 'details' | 'actions'>('fields');
const contractModeFeedback = ref('');
const actionSafetyConfirm = useProductConfirmDialog();
const actionInputDialog = useProductInputDialog();
const contract = ref<ActionContract | null>(null);
const contractMeta = ref<Record<string, unknown> | null>(null);
const v2ContractStore = ref<ContractV2NormalizedStore | null>(null);
const v2ContractDecodeError = ref('');
const v2ShadowStoreReady = computed(() => Boolean(v2ContractStore.value));
const v2ShadowWidgetCount = computed(() => v2ContractStore.value?.widgetsById.size || 0);
const v2ShadowActionCount = computed(() => v2ContractStore.value?.actionsById.size || 0);
const v2ShadowButtonStatusCount = computed(() => v2ContractStore.value?.buttonStatusById.size || 0);

function formRouteIdentity() {
  const query = route.query as Record<string, unknown>;
  return [
    String(route.params.model || ''),
    String(route.params.id || ''),
    String(query.action_id || ''),
    String(query.menu_id || ''),
    String(query.view_id || query.viewId || ''),
    String(query.current_business_category_code || query.default_business_category_code || ''),
    String(query.allowed_business_category_codes || ''),
  ].join('|');
}
const v2ShadowFieldCodes = computed(() => Array.from(v2ContractStore.value?.widgetsByFieldCode.keys() || []));
const v2ShadowFieldCodeCount = computed(() => v2ShadowFieldCodes.value.length);
const v2ShadowLegacyFieldMissing = computed(() => {
  const legacyFields = contract.value?.fields || {};
  return v2ShadowFieldCodes.value.filter((fieldCode) => !(fieldCode in legacyFields));
});
const v2ShadowLegacyFieldOverlapCount = computed(() => v2ShadowFieldCodeCount.value - v2ShadowLegacyFieldMissing.value.length);
const v2ShadowLegacyFieldMissingPreview = computed(() => v2ShadowLegacyFieldMissing.value.slice(0, 8).join(',') || '-');
const v2ShadowFormStructureContract = computed(() => resolveContractV2FormStructureContract(v2ContractStore.value));
const v2ShadowFormStructureSlotCount = computed(() => {
  const slots = v2ShadowFormStructureContract.value.slots;
  return Array.isArray(slots) ? slots.length : 0;
});
const v2ShadowLayoutSourceKind = computed(() => {
  const containers = resolveContractV2ContainerTree(v2ContractStore.value);
  if (containers.length) return 'v2_store';
  return nativeFormLayoutNodes.value.length ? 'legacy_layout' : 'none';
});
const v2ShadowGlobalSourceKind = computed(() => (resolveContractV2GlobalStatus(v2ContractStore.value) ? 'v2_store' : 'legacy_resolver'));
const v2ShadowSourceContextKind = computed(() => (Object.keys(resolveContractV2SourceContext(v2ContractStore.value)).length ? 'v2_store' : 'legacy_resolver'));
const v2ShadowStatusFieldCount = computed(() => Object.keys(collectContractV2FieldStatusByCode(v2ContractStore.value)).length);
const v2ShadowValueSource = computed(() => resolveContractV2ValueSource(v2ContractStore.value));
const v2ShadowValueSourceKind = computed(() => v2ShadowValueSource.value.kind);
const v2ShadowValueFieldCount = computed(() => (
  v2ShadowFieldCodes.value.filter((fieldCode) => (
    Object.prototype.hasOwnProperty.call(v2ShadowValueSource.value.values, fieldCode)
  )).length
));
const v2ShadowMainDataFieldCount = computed(() => (
  v2ShadowFieldCodes.value.filter((fieldCode) => (
    Object.prototype.hasOwnProperty.call(resolveContractV2MainData(v2ContractStore.value), fieldCode)
  )).length
));
const v2ShadowReadonlyValueCount = computed(() => (
  layoutNodes.value.filter((node) => (
    node.kind === 'field'
    && node.readonly
    && Boolean(v2ContractStore.value?.widgetsByFieldCode.has(node.name))
    && Object.prototype.hasOwnProperty.call(v2ShadowValueSource.value.values, node.name)
  )).length
));
const activeFilterKey = ref('');
const originalValues = ref<Record<string, unknown>>({});
const recordVersionToken = ref('');
const formData = reactive<Record<string, unknown>>({});
const nativeLayoutVisibilityRevision = ref(0);
const advancedExpanded = ref(false);
const {
  relationOptions,
  relationFieldDescriptors,
  relationKeywords,
  invalidatedRelationKeywords,
  clearedDynamicRelationFields,
  relationSearchDialog,
  deniedRelationModels,
  relationQueryTimers,
  relationKeyword,
  relationOptionsForField: relationOptionsForFieldFromRuntime,
  selectedRelationOptions: selectedRelationOptionsFromRuntime,
  setRelationKeywordValue,
  filteredRelationOptions: filteredRelationOptionsFromRuntime,
  upsertRelationOption,
  mergeRelationOptions,
  closeRelationSearchDialog,
  setRelationSearchKeyword,
  selectRelationSearchRow,
  openRelationSearch: openRelationSearchFromRuntime,
  runRelationSearch: runRelationSearchFromRuntime,
  confirmRelationSearchSelection: confirmRelationSearchSelectionFromRuntime,
  selectRelationSearchOption: selectRelationSearchOptionFromRuntime,
  queryRelationOptions: queryRelationOptionsFromRuntime,
  fetchRelationOptions: fetchRelationOptionsFromRuntime,
} = useRelationRuntime();
const onchangeModifiersPatch = ref<Record<string, Record<string, unknown>>>({});
const onchangeWarnings = ref<Array<{ title?: string; message?: string; reason_code?: string }>>([]);
const onchangeLinePatches = ref<OnchangeLinePatch[]>([]);
const {
  rowsByField: one2manyRows,
  fieldRows: one2manyFieldRows,
  visibleRows: visibleOne2manyRows,
  removedRows: removedOne2manyRows,
  ensureRows: ensureOne2manyRows,
  clearRows: clearOne2manyRows,
  addRow: addOne2manyRow,
  setRowField: setOne2manyRowField,
  removeRow: removeOne2manyRow,
  restoreRow: restoreOne2manyRow,
  initRows: initOne2manyRows,
  mergeHydratedRecords: mergeHydratedOne2manyRecords,
  buildCommandValue: buildOne2manyCommandValue,
  collectValidation: collectOne2manyDraftValidation,
  rowHints: one2manyRowHints,
  applyLinePatches: applyOnchangeLinePatches,
} = useOne2manyRuntime({
  recordId: () => recordId.value,
  originalValues: () => originalValues.value,
  onchangeLinePatches: () => onchangeLinePatches.value as Array<Record<string, unknown>>,
  resolveColumns: (fieldName) => one2manyColumns(fieldName),
  resolvePrimaryColumn: (fieldName) => one2manyPrimaryColumn(fieldName),
  resolveRelationOptions: (fieldName) => relationOptionsForField(fieldName),
  markFieldChanged,
});
const changedFieldSet = new Set<string>();
const dirtyFieldSet = new Set<string>();
let onchangeTimer: ReturnType<typeof setTimeout> | null = null;
const applyingOnchangePatch = ref(false);
const {
  activeMode: activeChatterMode,
  activeLabel: activeChatterLabel,
  draft: chatterDraft,
  activitySummary,
  activityDeadline,
  activityNote,
  userQuery: collaborationUserQuery,
  userOptions: collaborationUserOptions,
  usersLoading: collaborationUsersLoading,
  selectedMentionUserIds,
  selectedMentionUsers,
  userChoices: collaborationUserChoices,
  activityAssigneeId,
  posting: chatterPosting,
  loading: chatterLoading,
  error: chatterError,
  timeline: chatterTimeline,
  activityUpdatingIds,
  clearForRecordLoad: clearNativeChatterForRecordLoad,
  closeComposer: closeNativeChatterComposer,
  loadTimeline: loadNativeChatterTimeline,
  loadUsers: loadCollaborationUsers,
  selectMentionUser,
  removeMentionUser,
  openAction: openNativeChatterAction,
  send: sendNativeChatter,
  updateActivity: updateNativeActivity,
} = useNativeChatterRuntime({
  model: () => model.value,
  recordId: () => recordId.value,
  activeActivityAction: () => activeActivityAction.value,
});
const attachmentViewerRef = ref<NativeAttachmentViewerLike | null>(null);
const {
  uploading: attachmentUploading,
  error: attachmentError,
  pendingAttachments: pendingNativeAttachments,
  clearError: clearNativeAttachmentError,
  clearPendingAttachments: clearPendingNativeAttachments,
  onAttachmentSelected: onNativeAttachmentSelected,
  removePendingAttachment: removePendingNativeAttachment,
  uploadPendingAttachments: uploadPendingNativeAttachments,
  openAttachment: openNativeAttachment,
} = useNativeAttachmentRuntime({
  model: () => model.value,
  recordId: () => recordId.value,
  maxBytes: () => nativeAttachmentMaxBytes.value,
  resolveLabel: resolveNativeAttachmentLabel,
  reloadTimeline: loadNativeChatterTimeline,
  viewerRef: attachmentViewerRef,
  onPendingUploadFailed: (message) => {
    validationErrors.value = [message];
    submissionFeedback.value = { kind: 'error', message };
    status.value = 'error';
  },
});
const nativeChatterAutoLoadKey = ref('');
let activeReloadToken = 0;
let activeReloadIdentity = '';
let activeReloadPromise: Promise<void> | null = null;

const model = computed(() => String(route.params.model || contract.value?.head?.model || contract.value?.model || ''));
const menuId = computed(() => Number(route.query.menu_id || 0) || 0);
const actionId = computed(() => {
  const rawRecordId = String(route.params.id || '').trim();
  const isCreateRoute = !rawRecordId || rawRecordId === 'new';
  const menuAction = findActionMetaByMenu(session.menuTree, menuId.value);
  return resolveActionIdFromContext({
    routeQuery: route.query as Record<string, unknown>,
    menuActionId: menuAction?.action_id,
    menuActionModel: menuAction?.model,
    currentActionId: isCreateRoute ? session.currentAction?.action_id : null,
    currentActionModel: session.currentAction?.model,
    model: model.value,
  });
});
const currentMenuTitle = computed(() => {
  const node = findMenuNode(session.menuTree, menuId.value);
  return String(node?.label || node?.name || node?.title || '').trim();
});
const recordId = computed(() => {
  const raw = String(route.params.id || '').trim();
  if (!raw || raw === 'new') return null;
  const parsed = Number(raw);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
});
const recordIdDisplay = computed(() => (recordId.value ? String(recordId.value) : 'new'));
const showHud = computed(() => isHudEnabled(route));
const showSceneBlocksDebug = computed(() => isSceneBlocksDebugEnabled(route));
const requestedSurface = computed<'user' | 'native' | 'hud'>(() => {
  const raw = String(route.query.surface || '').trim().toLowerCase();
  if (raw === 'native' || raw === 'hud' || raw === 'user') return raw;
  if (showHud.value) return 'hud';
  return 'user';
});
const requestedSourceMode = computed(() => (
  requestedSurface.value === 'native' ? 'native_parser' : 'governance_pipeline'
));
const busy = computed(() => busyKind.value !== null);

function recordVersionPolicy() {
  const raw = (contract.value as Record<string, unknown> | null)?.record_version;
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null;
  const policy = raw as Record<string, unknown>;
  if (policy.enabled !== true) return null;
  const tokenField = String(policy.token_field || '').trim();
  const requestParam = String(policy.request_param || '').trim();
  if (!tokenField || requestParam !== 'if_match') return null;
  return { tokenField };
}

const renderProfile = computed<'create' | 'edit' | 'readonly'>(() => {
  const storeSourceContext = resolveContractV2SourceContext(v2ContractStore.value);
  const sourceContext = Object.keys(storeSourceContext).length
    ? storeSourceContext
    : resolveUnifiedPageContractV2SourceContext(contract.value);
  const head = (contract.value?.head || {}) as Record<string, unknown>;
  const profile = String(sourceContext.renderProfile || contract.value?.render_profile || head.render_profile || '').trim().toLowerCase();
  if (profile === 'readonly') return 'readonly';
  if (profile === 'edit') return 'edit';
  if (profile === 'create') return 'create';
  if (!canSave.value) return 'readonly';
  return recordId.value ? 'edit' : 'create';
});

const rights = computed(() => {
  const globalStatus = resolveContractV2GlobalStatus(v2ContractStore.value) || resolveUnifiedPageContractV2GlobalStatus(contract.value);
  const pageAuth = String(globalStatus?.pageAuth || '').trim().toLowerCase();
  if (globalStatus?.pageVisible === false || pageAuth === 'none') {
    return { read: false, write: false, create: false, unlink: false };
  }
  const head = contract.value?.head?.permissions;
  const effective = contract.value?.permissions?.effective?.rights;
  const resolve = (key: 'read' | 'write' | 'create' | 'unlink') => {
    const a = head?.[key];
    if (typeof a === 'boolean') return a;
    const b = effective?.[key];
    if (typeof b === 'boolean') return b;
    return true;
  };
  return {
    read: resolve('read'),
    write: pageAuth === 'read' ? false : resolve('write'),
    create: pageAuth === 'read' ? false : resolve('create'),
    unlink: pageAuth === 'read' ? false : resolve('unlink'),
  };
});

const canSave = computed(() => (recordId.value ? rights.value.write : rights.value.create));
const relationRecordCountLabel = computed(() => {
  const template = relationSearchDialog.labels.record_count || '%s 条记录';
  const count = String(relationSearchDialog.rows.length);
  return template.includes('%s') ? template.replace('%s', count) : `${count} ${template}`.trim();
});
const isProjectQuickIntakeMode = computed(() => {
  if (String(model.value || '').trim() !== 'project.project') return false;
  if (recordId.value) return false;
  return String(route.query.intake_mode || '').trim().toLowerCase() === 'quick';
});
const isProjectStandardIntakeMode = computed(() => {
  if (String(model.value || '').trim() !== 'project.project') return false;
  if (recordId.value) return false;
  if (isProjectQuickIntakeMode.value) return false;
  if (String(route.query.intake_mode || '').trim().toLowerCase() === 'standard') return true;
  return String(route.query.scene_key || '').trim() === 'projects.intake';
});
const isProjectIntakeCreateMode = computed(() => isProjectQuickIntakeMode.value || isProjectStandardIntakeMode.value);
const intakeAutosaveKey = computed(() => {
  if (!isProjectIntakeCreateMode.value) return '';
  const mode = isProjectQuickIntakeMode.value ? 'quick' : 'standard';
  const userId = Number(session.user?.id || 0) || 0;
  return `sc:intake:autosave:project.project:${mode}:u${userId}`;
});
const quickRequiredReady = computed(() => {
  if (!isProjectQuickIntakeMode.value) return true;
  const projectName = String(formData.name || '').trim();
  const managerId = Number(formData.manager_id || 0);
  return Boolean(projectName) && Number.isFinite(managerId) && managerId > 0;
});
const standardCreateReady = computed(() => {
  if (!isProjectStandardIntakeMode.value) return true;
  const projectName = String(formData.name || '').trim();
  const managerId = Number(formData.manager_id || 0);
  return Boolean(projectName) && Number.isFinite(managerId) && managerId > 0;
});

function hasPendingInlineRelationChange() {
  return layoutNodes.value.some((node) => {
    if (node.kind !== 'field' || node.readonly) return false;
    const descriptor = contract.value?.fields?.[node.name];
    if (fieldType(descriptor) !== 'many2one') return false;
    const inline = relationInlineCreate(descriptor);
    if (!inline.enabled || !inline.createOnNoMatch) return false;
    const currentId = Number(formData[node.name] || 0);
    if (Number.isFinite(currentId) && currentId > 0) return false;
    return Boolean(relationKeyword(node.name).trim());
  });
}

function hasPendingMany2manyTagCreate() {
  return Object.entries(relationKeywords).some(([name, keyword]) => {
    if (!String(keyword || '').trim()) return false;
    if (!isFieldWritable(name)) return false;
    if (!Array.isArray(formData[name])) return false;
    const descriptor = contract.value?.fields?.[name];
    const inline = relationInlineCreate(descriptor);
    if (!inline.enabled || !inline.createOnNoMatch) return false;
    return Boolean(relationModel(name));
  });
}

function hasOne2manyDraftChanges() {
  return layoutNodes.value.some((node) => {
    if (node.kind !== 'field' || node.readonly) return false;
    const descriptor = contract.value?.fields?.[node.name];
    if (fieldType(descriptor) !== 'one2many') return false;
    return one2manyFieldRows(node.name).some((row) => row.isNew || row.dirty || row.removed);
  });
}

const hasChanges = computed(() => {
  if (hasPendingInlineRelationChange()) return true;
  if (hasPendingMany2manyTagCreate()) return true;
  if (hasOne2manyDraftChanges()) return true;
  const statusField = nativeStatusbar.value.field;
  if (
    statusField
    && !nativeStatusbar.value.readonly
    && comparableFieldValue(statusField, formData[statusField]) !== comparableFieldValue(statusField, originalValues.value[statusField])
  ) {
    return true;
  }
  const keys = Object.keys(formData);
  return keys.some((key) => {
    if (!isFieldWritable(key)) return false;
    return comparableFieldValue(key, formData[key]) !== comparableFieldValue(key, originalValues.value[key]);
  });
});
const writableFieldCount = computed(() =>
  layoutNodes.value.filter((node) => node.kind === 'field' && !node.readonly).length,
);
const changedFieldCount = computed(() =>
  Object.keys(formData).filter((key) => isFieldWritable(key) && comparableFieldValue(key, formData[key]) !== comparableFieldValue(key, originalValues.value[key])).length
    + (hasOne2manyDraftChanges() ? 1 : 0),
);

const intakeRequiredFields = computed(() => {
  if (!isProjectIntakeCreateMode.value) return [];
  return layoutNodes.value
    .filter((node) => node.kind === 'field' && node.required && isFieldVisible(node.name))
    .map((node) => ({ name: node.name, label: node.label || node.name }));
});

const intakeRequiredReadyCount = computed(() => {
  if (!isProjectIntakeCreateMode.value) return 0;
  return intakeRequiredFields.value.filter((field) => {
    const value = formData[field.name];
    if (value === null || value === undefined) return false;
    if (typeof value === 'string') return value.trim().length > 0;
    if (typeof value === 'number') return Number.isFinite(value) && value > 0;
    if (Array.isArray(value)) return value.length > 0;
    if (typeof value === 'boolean') return true;
    return Boolean(value);
  }).length;
});

const intakeMissingRequiredLabels = computed(() => {
  if (!isProjectIntakeCreateMode.value) return [];
  return intakeRequiredFields.value
    .filter((field) => {
      const value = formData[field.name];
      if (value === null || value === undefined) return true;
      if (typeof value === 'string') return value.trim().length === 0;
      if (typeof value === 'number') return !Number.isFinite(value) || value <= 0;
      if (Array.isArray(value)) return value.length === 0;
      return false;
    })
    .map((field) => String(field.label || '').trim())
    .slice(0, 5);
});

const intakeRequiredSummary = computed(() => {
  if (!isProjectIntakeCreateMode.value) return '';
  const total = intakeRequiredFields.value.length;
  const done = intakeRequiredReadyCount.value;
  if (total <= 0) return '当前页面未提供必填字段约束。';
  return `${done}/${total}`;
});

const intakeMissingSummary = computed(() => {
  if (!isProjectIntakeCreateMode.value) return '';
  if (!intakeMissingRequiredLabels.value.length) return '无';
  return intakeMissingRequiredLabels.value.join('、');
});

const one2manyValidation = computed(() => collectOne2manyDraftValidation());

const pageTitle = computed(() => resolvePageTitle({
  menuTitle: currentMenuTitle.value,
  contractTitle: String(contract.value?.head?.title || ''),
  recordTitle: String(formData.display_name || formData.name || ''),
}));

const currentBusinessCategoryContext = computed(() => resolveBusinessCategoryContext({
  contractRecord: contract.value,
  routeQuery: route.query as Record<string, unknown>,
  relationBusinessCategoryLabel: relationKeywords.business_category_id,
}));
const currentBusinessCategoryLabel = computed(() => currentBusinessCategoryContext.value.label);
const currentBusinessCategoryCode = computed(() => currentBusinessCategoryContext.value.code);

const pageDisplayTitle = computed(() => resolvePageDisplayTitle({
  isProjectIntakeCreateMode: isProjectIntakeCreateMode.value,
  currentBusinessCategoryLabel: currentBusinessCategoryLabel.value,
  pageTitle: pageTitle.value,
  recordId: recordId.value,
}));

const pageDisplaySubtitle = computed(() => resolvePageDisplaySubtitle({
  isProjectIntakeCreateMode: isProjectIntakeCreateMode.value,
  currentBusinessCategoryLabel: currentBusinessCategoryLabel.value,
  pageTitle: pageTitle.value,
  recordTitle: String(formData.display_name || formData.name || ''),
  pageDisplayTitle: pageDisplayTitle.value,
  recordId: recordId.value,
}));

const activityPageTitle = computed(() => {
  const recordTitle = String(formData.display_name || formData.name || '').trim();
  if (recordId.value && recordTitle) return recordTitle;
  return pageDisplayTitle.value;
});

watch(
  activityPageTitle,
  (title) => {
    if (!isComponentActive.value) return;
    session.updateActiveActivityTitle(title);
  },
  { immediate: true },
);

const suppressPageHeaderTitle = computed(() => useNativeFormTree.value && !isProjectIntakeCreateMode.value);

const intakeCreateButtonLabel = computed(() => {
  if (!isProjectIntakeCreateMode.value) return '创建项目';
  return busy.value && busyKind.value === 'save' ? '创建中…' : '创建项目';
});

const submitButtonLabel = computed(() => resolveSubmitButtonLabel({
  busy: busy.value,
  busyKind: busyKind.value,
  footerActionLabel: primaryCreateFooterAction.value?.label || '',
  hasFooterAction: Boolean(primaryCreateFooterAction.value),
  hasPrimarySubmitAction: Boolean(primarySubmitAction.value),
  isProjectQuickIntakeMode: isProjectQuickIntakeMode.value,
  isProjectIntakeCreateMode: isProjectIntakeCreateMode.value,
  recordId: recordId.value,
  saveLabel: formUiLabel('save'),
  savingLabel: formUiLabel('saving'),
}));
const showPrimaryBusinessFormAction = computed(() => !showCurrentFormFieldConfigScope.value && !isProjectIntakeCreateMode.value);
const showDraftSaveAction = computed(() => showPrimaryBusinessFormAction.value && !recordId.value && canSave.value && !primaryCreateFooterAction.value);
const draftSaveButtonLabel = computed(() => (busy.value && busyKind.value === 'save' ? formUiLabel('saving') : '保存草稿'));
const showDiscardAction = computed(() => !isProjectIntakeCreateMode.value && Boolean(recordId.value) && hasChanges.value);

const headerActionsVisible = computed(() => {
  if (isProjectIntakeCreateMode.value) return [];
  const filterPrimarySubmit = (actions: ContractAction[]) => actions.filter((action) => !isUnifiedSubmitAction(action));
  if (useNativeFormTree.value) {
    return filterPrimarySubmit(headerActions.value.filter((action) => action.sourceWidgetId === 'page.header'));
  }
  return filterPrimarySubmit(headerActions.value);
});

function isHeaderConfigAction(action: ContractAction) {
  const label = String(action.label || '').trim();
  const key = String(action.key || '').trim().toLowerCase();
  const source = String(action.sourceWidgetId || '').trim().toLowerCase();
  return label.includes('设置') || key.includes('setting') || key.includes('config') || source.includes('setting') || source.includes('config');
}

const headerBusinessActionsVisible = computed(() => {
  if (showCurrentFormFieldConfigScope.value) return [];
  return headerActionsVisible.value.filter((action) => !isHeaderConfigAction(action));
});
const headerConfigActionsVisible = computed(() => headerActionsVisible.value.filter((action) => isHeaderConfigAction(action) && action.enabled));

function headerActionButtonClass(action: ContractAction) {
  return ['sc-btn', 'sc-btn-sm', action.semantic === 'primary_action' && !isHeaderConfigAction(action) ? 'sc-btn-primary' : 'sc-btn-ghost'];
}

function contractV2ActionRules() {
  const v2ActionRules = resolveUnifiedPageContractV2(contract.value)?.actionContract;
  const v2ActionRuleList = parseMaybeJsonRecord(v2ActionRules).actionRuleList;
  return Array.isArray(v2ActionRuleList)
    ? v2ActionRuleList.filter((row): row is Record<string, unknown> => Boolean(row && typeof row === 'object' && !Array.isArray(row)))
    : [];
}

function contractFieldActions(field: FormSectionFieldSchema) {
  return buildContractFieldActionsFromRules({
    rules: contractV2ActionRules(),
    fieldName: field.name,
    mode: activeContractMode.value,
    visibilityDraft: fieldVisibilityDraft,
    busy: busy.value,
  });
}

function formSettingsFieldActions(field: FormSectionFieldSchema) {
  const fieldKey = String(field.name || '').trim();
  const existingRow = activeContractModeFieldRows.value.find((row) => row.fieldKey === fieldKey);
  return buildFormSettingsFieldActionsFromRules({
    fieldName: fieldKey,
    existingActions: existingRow?.actions,
    visibilityDraft: fieldVisibilityDraft,
    busy: busy.value,
  });
}

const activeContractModeActions = computed(() => {
  return buildActiveContractModeActions({
    rules: contractV2ActionRules(),
    mode: activeContractMode.value,
    excludedKeys: [BUSINESS_CONFIG_ACTION_KEYS.currentFormFieldOrderSave],
  });
});


const fieldOrderDraft = ref<string[]>([]);
const fieldOrderPreviewActive = ref(false);
const nativeFormDesignFieldKeys = ref<string[]>([]);
const nativeFormDesignFieldLabels = ref<Record<string, string>>({});
const formConfigFieldLabelCache = reactive<Record<string, string>>({});
const fieldGroupBase = ref<Record<string, string>>({});
const fieldGroupSavedBase = ref<Record<string, string>>({});
const fieldGroupDraft = reactive<Record<string, string>>({});
const formLayoutColumnsBase = ref<1 | 2 | 3>(3);
const formLayoutColumnsDraft = ref<1 | 2 | 3>(3);
const formLayoutColumnsConfigured = ref(false);
const groupVisibilityBase = ref<Record<string, boolean>>({});
const groupVisibilityDraft = reactive<Record<string, boolean>>({});
const groupColumnsBase = ref<Record<string, 1 | 2 | 3>>({});
const groupColumnsDraft = reactive<Record<string, 1 | 2 | 3>>({});
const fieldSizeBase = ref<Record<string, LowCodeFieldSize>>({});
const fieldSizeDraft = reactive<Record<string, LowCodeFieldSize>>({});
const formLayoutDirty = ref(false);
const groupLayoutDirtyKeys = reactive<Record<string, boolean>>({});
const fieldLayoutDirtyKeys = reactive<Record<string, boolean>>({});
const fieldMoveTargetDraft = reactive<Record<string, string>>({});
const {
  draggingFieldKey,
  draggingFieldLabel,
  dropTargetFieldKey,
  dropTargetPlacement,
  dragStart: onFieldOrderDragStart,
  dragOver: onFieldOrderDragOver,
  dragLeave: onFieldOrderDragLeave,
  dragEnd: onFieldOrderDragEnd,
  windowDragOver: onFieldOrderWindowDragOver,
  windowDragStop: onFieldOrderWindowDragStop,
  resetDropTarget: resetFieldOrderDropTarget,
} = useFieldOrderDragRuntime({
  enabled: () => isContractFieldOrderEditable.value,
  resolveFieldLabel: (fieldKey) => formDesignFieldLabel(fieldKey),
});
const selectedFormSettingsFieldKey = ref('');
const selectedFormSettingsFieldLabel = ref('');
const selectedFormSettingsFieldGroupTitleDraft = ref('');
const selectedFormSettingsFieldGroupTitleEdit = ref('');
const formDesignerFieldSearchText = ref('');
const selectedFormSettingsOrderTargetKey = ref('');
const selectedFormSettingsOrderPlacement = ref<'before' | 'after'>('before');
const isContractFieldOrderEditable = computed(() => (
  !isBusinessConfigRuntimeModel(model.value)
  && (
    activeContractMode.value === BUSINESS_CONFIG_MODES.formFieldConfiguration
    || activeContractMode.value === BUSINESS_CONFIG_MODES.lowCode
  )
));
const showReturnToBusinessConfigAction = computed(() => (
  routeQueryText(BUSINESS_CONFIG_ROUTE_FLAGS.returnToBusinessConfig) === '1'
  || activeContractMode.value === BUSINESS_CONFIG_MODES.lowCode
));
const fieldVisibilityBase = ref<Record<string, boolean>>({});
const fieldVisibilityDirty = ref(false);
const fieldVisibilityDraft = reactive<Record<string, boolean>>({});
const fieldVisibilityDirtyKeys = reactive<Record<string, boolean>>({});
const formConfigAuditBusy = ref(false);
const formConfigAuditResult = ref<FormConfigAuditResult | null>(null);
const {
  operationLog: formConfigOperationLog,
  operatorName: formConfigOperatorName,
  appendOperation: appendFormConfigOperation,
  markPendingOperations: markPendingFormConfigOperations,
  clearOperationLog: clearFormConfigOperationLog,
} = useFormConfigOperationLog({
  user: () => session.user as Record<string, unknown> | null,
  db: () => route.query.db,
  modelName: () => model.value || route.params.model,
  actionId: () => actionId.value || route.query.action_id,
  viewId: () => routeQueryText('view_id') || routeQueryText('viewId'),
  page: () => routeQueryText('page_label') || routeQueryText('pageLabel') || route.fullPath,
});
const {
  onFormLayoutColumnsChange,
  onSelectedFormSettingsGroupVisibilityChange,
  onSelectedFormSettingsGroupColumnsChange,
  onSelectedFormSettingsFieldSizeChange,
  resetContractFieldOrder,
} = useFormSettingsLayoutRuntime({
  formLayoutColumnsBase,
  formLayoutColumnsDraft,
  formLayoutDirty,
  formConfigAuditResult,
  groupVisibilityBase,
  groupVisibilityDraft,
  groupColumnsBase,
  groupColumnsDraft,
  groupLayoutDirtyKeys,
  fieldSizeBase,
  fieldSizeDraft,
  fieldLayoutDirtyKeys,
  fieldOrderDraft,
  fieldOrderPreviewActive,
  fieldGroupBase,
  fieldGroupSavedBase,
  fieldGroupDraft,
  fieldMoveTargetDraft,
  fieldVisibilityBase,
  fieldVisibilityDraft,
  fieldVisibilityDirty,
  fieldVisibilityDirtyKeys,
  contractModeFeedback,
  currentDesignFieldKeys: () => currentFormDesignFieldKeys.value,
  visibilityDraftFieldKeys: () => formVisibilityDraftFieldKeys.value,
  baseFieldRows: () => contractModeBaseFieldRows.value,
  currentGroupOptions: () => currentFormGroupOptions.value,
  groupNavigatorItems: () => formDesignerGroupNavigatorItems.value,
  selectedGroupTitle: () => selectedFormSettingsFieldGroupTitle.value,
  selectedFieldKey: () => selectedFormSettingsFieldKey.value,
  effectiveGroupVisible: (key) => effectiveGroupVisible(key),
  effectiveGroupColumns: (key) => effectiveGroupColumns(key),
  effectiveFieldSize: (fieldKey) => effectiveFieldSize(fieldKey),
  formDesignFieldLabel: (fieldKey) => formDesignFieldLabel(fieldKey),
  appendOperation: appendFormConfigOperation,
  markPendingOperations: markPendingFormConfigOperations,
});
const {
  onContractInlineGroupRename,
} = useFormSettingsGroupRuntime({
  busy: () => busy.value,
  nativeFormLayoutNodes: () => nativeFormLayoutNodes.value,
  contractFields: () => (contract.value?.fields || {}) as Record<string, FieldDescriptor>,
  currentOrderedFieldKeys: () => currentFormOrderedFieldKeys.value,
  effectiveFieldGroupTitle: (fieldKey) => effectiveFieldGroupTitleForDraft(fieldKey),
  formDesignFieldLabel: (fieldKey) => formDesignFieldLabel(fieldKey),
  contractFieldLabel: (fieldKey) => contractFieldLabel(fieldKey),
  fieldGroupDraft,
  selectedGroupTitleDraft: selectedFormSettingsFieldGroupTitleDraft,
  selectedGroupTitleEdit: selectedFormSettingsFieldGroupTitleEdit,
  formConfigAuditResult,
  contractModeFeedback,
  appendOperation: appendFormConfigOperation,
});
const {
  moveFieldOrder,
  moveSelectedFormSettingsFieldToOrderTarget,
  onSelectedFormSettingsFieldGroupMoveChange,
  onFieldOrderDrop,
  onFieldOrderGroupDrop,
} = useFieldOrderMutationRuntime({
  isEditable: () => isContractFieldOrderEditable.value,
  ensureDraftStartsFromCurrentLayout: () => ensureFieldOrderDraftStartsFromCurrentLayout(),
  fieldOrderDraft,
  fieldOrderPreviewActive,
  currentOrderedFieldKeys: () => currentFormOrderedFieldKeys.value,
  fieldGroupBase,
  fieldGroupDraft,
  fieldMoveTargetDraft,
  selectedFieldKey: selectedFormSettingsFieldKey,
  selectedFieldLabel: selectedFormSettingsFieldLabel,
  selectedGroupTitleDraft: selectedFormSettingsFieldGroupTitleDraft,
  selectedGroupTitleEdit: selectedFormSettingsFieldGroupTitleEdit,
  selectedOrderTargetKey: selectedFormSettingsOrderTargetKey,
  selectedOrderPlacement: selectedFormSettingsOrderPlacement,
  draggingFieldKey,
  draggingFieldLabel,
  formConfigAuditResult,
  formDesignFieldLabel: (fieldKey) => formDesignFieldLabel(fieldKey),
  appendOperation: appendFormConfigOperation,
  resetDropTarget: resetFieldOrderDropTarget,
});
const {
  hideSuggestedInternalFields,
  onFieldVisibilityDraftChange,
  onSelectedFormSettingsFieldVisibilityChange,
} = useFieldVisibilityDraftRuntime({
  fieldVisibilityDraft,
  fieldVisibilityDirty,
  fieldVisibilityDirtyKeys,
  formConfigAuditResult,
  contractModeFeedback,
  selectedFieldKey: () => selectedFormSettingsFieldKey.value,
  suggestedHiddenRows: () => suggestedHiddenFieldRows.value,
  formDesignFieldLabel: (fieldKey) => formDesignFieldLabel(fieldKey),
  appendOperation: appendFormConfigOperation,
});
const {
  onContractInlineFieldLabelChange,
  setInlineFieldPolicy,
} = useInlineFieldPolicyRuntime({
  busy: () => busy.value,
  busyKind,
  errorMessage,
  status,
  contractModeFeedback,
  lowCodeApplyBaseParams: () => lowCodeApplyBaseParams(),
  contractFieldSequence: (fieldKey) => contractFieldSequence(fieldKey),
  formDesignFieldLabel: (fieldKey) => formDesignFieldLabel(fieldKey),
  appendOperation: appendFormConfigOperation,
  reload: () => reload(),
});
const {
  closeContractPromptAction,
  contractPromptFields,
  contractPromptRule,
  contractPromptValues,
  openContractModeAction,
  runContractRuleAction,
  setContractPromptValue,
  submitContractPromptAction,
} = useContractModeActionRuntime({
  busyKind,
  errorMessage,
  status,
  contractModeFeedback,
  applyClientMode: (mode, toggle) => applyClientMode(mode, toggle),
  reload: () => reload(),
});
const {
  lowCodeFieldCreateDialog,
  openCentralCustomFieldCreate,
  onContractInlineFieldAddAfter,
  onContractInlineGroupAddField,
  closeInlineCustomFieldCreate,
  setFieldCreateLabel,
  setFieldCreateType,
  submitInlineCustomFieldCreate,
} = useLowCodeFieldCreateRuntime({
  busy: () => busy.value,
  selectedFieldKey: () => selectedFormSettingsFieldKey.value,
  selectedGroupTitle: () => selectedFormSettingsFieldGroupTitle.value,
  firstGroupTitle: () => currentFormGroupOptions.value[0] || '',
  fieldOrderLength: () => fieldOrderDraft.value.length,
  fieldSequence: (fieldKey, fallback) => contractFieldSequence(fieldKey, fallback),
  submit: async ({ label, ttype, groupTitle, sequence }) => {
    busyKind.value = 'action';
    try {
      await intentRequest({
        intent: FORM_FIELD_CONFIG_INTENTS.customFieldCreate,
        params: {
          ...lowCodeApplyBaseParams(),
          label,
          ttype,
          group_title: groupTitle,
          sequence,
        },
        context: { view: 'form' },
      });
      contractModeFeedback.value = '字段已添加';
      appendFormConfigOperation('新增字段', `${label} 添加到 ${groupTitle}`, 'done');
      await reload();
      return true;
    } catch (err) {
      errorMessage.value = err instanceof Error ? err.message : '自定义字段创建失败';
      status.value = 'error';
      return false;
    } finally {
      busyKind.value = null;
    }
  },
});
const lowCodeContractLoaded = ref(false);
const lowCodeContractHydrating = ref(false);
const lowCodePrecheckWarnings = ref<string[]>([]);
const lowCodeContractList = ref<Array<{ id: number; name: string; model: string; status: string; version_no: number }>>([]);
const lowCodeSelectedContractName = ref('');
const lowCodeFormLayoutBase = ref<NativeFormLayoutNode[]>([]);
const lowCodeLayoutDraft = ref<LowCodeLayoutDraftRow[]>([]);

const contractModeBaseFieldRows = computed<ContractFieldGovernanceRow[]>(() => {
  const mode = activeContractMode.value;
  if (!mode) return [];
  const rows = new Map<string, ContractFieldGovernanceRow>();
  contractV2ActionRules().forEach((rule) => {
    const sourceWidgetId = String(rule.sourceWidgetId || rule.source_widget_id || '').trim();
    if (!sourceWidgetId.startsWith('field.')) return;
    const expectedMode = contractActionRuleClientMode(rule);
    if (expectedMode && expectedMode !== mode) return;
    const fieldKey = sourceWidgetId.slice('field.'.length);
    if (!fieldKey) return;
    const control = contractActionRuleControl(rule);
    const target = parseMaybeJsonRecord(rule.target);
    const params = parseMaybeJsonRecord(target.params || rule.params);
    const fieldLabel = String(params.label || fieldKey).trim();
    const action: ContractFieldGovernanceAction = {
      key: contractActionRuleKey(rule),
      label: String(control.label || rule.label || contractActionRuleKey(rule)).trim(),
      value: String(control.value || contractActionRuleKey(rule)).trim(),
      checked: control.checked === true,
      disabled: control.disabled === true || busy.value,
      title: String(control.title || '').trim(),
      raw: rule,
    };
    if (!rows.has(fieldKey)) {
      rows.set(fieldKey, { fieldKey, label: fieldLabel, actions: [] });
    }
    rows.get(fieldKey)?.actions.push(action);
  });
  return Array.from(rows.values())
    .map((row) => ({
      ...row,
      actions: row.actions.sort((left, right) => {
        const order = (value: string) => (value === 'show' ? 0 : value === 'hide' ? 1 : 2);
        return order(left.value) - order(right.value) || left.label.localeCompare(right.label);
      }),
    }));
});

const activeContractModeFieldRows = computed<ContractFieldGovernanceRow[]>(() => {
  const computedRows = contractModeBaseFieldRows.value;
  const rowsWithDraftVisibility = computedRows.map((row) => ({
    ...row,
    actions: row.actions.map((action) => ({
      ...action,
      checked: Object.prototype.hasOwnProperty.call(fieldVisibilityDraft, row.fieldKey)
        ? fieldVisibilityDraft[row.fieldKey] === (action.value === 'show')
        : action.checked,
    })),
  }));
  if (!isContractFieldOrderEditable.value || !fieldOrderDraft.value.length) return rowsWithDraftVisibility;
  const rank = new Map(fieldOrderDraft.value.map((key, index) => [key, index]));
  return rowsWithDraftVisibility.sort((left, right) => (rank.get(left.fieldKey) ?? 9999) - (rank.get(right.fieldKey) ?? 9999));
});

watch(contractModeBaseFieldRows, (rows) => {
  const keys = rows.map((row) => row.fieldKey);
  if (!isContractFieldOrderEditable.value || !keys.length) {
    fieldOrderDraft.value = [];
    fieldVisibilityBase.value = {};
    fieldGroupBase.value = {};
    fieldGroupSavedBase.value = {};
    formLayoutColumnsBase.value = 3;
    formLayoutColumnsDraft.value = 3;
    formLayoutColumnsConfigured.value = false;
    groupVisibilityBase.value = {};
    Object.keys(groupVisibilityDraft).forEach((key) => delete groupVisibilityDraft[key]);
    groupColumnsBase.value = {};
    Object.keys(groupColumnsDraft).forEach((key) => delete groupColumnsDraft[key]);
    fieldSizeBase.value = {};
    Object.keys(fieldSizeDraft).forEach((key) => delete fieldSizeDraft[key]);
    formLayoutDirty.value = false;
    Object.keys(groupLayoutDirtyKeys).forEach((key) => delete groupLayoutDirtyKeys[key]);
    Object.keys(fieldLayoutDirtyKeys).forEach((key) => delete fieldLayoutDirtyKeys[key]);
    lowCodeFormLayoutBase.value = [];
    Object.keys(fieldGroupDraft).forEach((key) => delete fieldGroupDraft[key]);
    Object.keys(fieldMoveTargetDraft).forEach((key) => delete fieldMoveTargetDraft[key]);
    return;
  }
  if (!fieldOrderDraft.value.length) {
    fieldOrderDraft.value = [...keys];
    return;
  }
  const inRows = new Set(keys);
  const kept = fieldOrderDraft.value.filter((key) => inRows.has(key));
  const missing = keys.filter((key) => !kept.includes(key));
  fieldOrderDraft.value = [...kept, ...missing];
  const nextVisibilityBase = { ...fieldVisibilityBase.value };
  rows.forEach((row) => {
    const selected = row.actions.find((action) => Boolean(action.checked));
    if (!selected) return;
    const visible = selected.value === 'show';
    if (!Object.prototype.hasOwnProperty.call(nextVisibilityBase, row.fieldKey)) {
      nextVisibilityBase[row.fieldKey] = visible;
    }
    if (!Object.prototype.hasOwnProperty.call(fieldVisibilityDraft, row.fieldKey)) {
      fieldVisibilityDraft[row.fieldKey] = visible;
    }
  });
  fieldVisibilityBase.value = nextVisibilityBase;
}, { immediate: true });

watch(isContractFieldOrderEditable, (enabled) => {
  if (!enabled) {
    lowCodeContractLoaded.value = false;
    selectedFormSettingsFieldKey.value = '';
    selectedFormSettingsFieldLabel.value = '';
    selectedFormSettingsFieldGroupTitleDraft.value = '';
    fieldVisibilityDirty.value = false;
    formConfigAuditResult.value = null;
    return;
  }
  formSettingsActiveTab.value = 'fields';
  syncFieldOrderDraftWithDesignKeys();
  void loadLowCodeContractList();
  void hydrateLowCodeDraftFromContract();
  void refreshLowCodeFormLayoutBase();
}, { immediate: true });

watch(
  () => [v2ContractStore.value, contract.value, isContractFieldOrderEditable.value],
  () => {
    applyRuntimeInferredFormColumns();
  },
  { flush: 'post' },
);

const currentFormDesignFieldKeys = computed(() => {
  const keys = new Set<string>();
  contractModeBaseFieldRows.value.forEach((row) => {
    if (row.fieldKey) keys.add(row.fieldKey);
  });
  nativeFormDesignFieldKeys.value.forEach((fieldKey) => {
    if (fieldKey) keys.add(fieldKey);
  });
  return Array.from(keys);
});

const currentFormOrderedFieldKeys = computed(() => {
  const baseKeys = currentFormDesignFieldKeys.value;
  if (!fieldOrderDraft.value.length) return baseKeys;
  const baseSet = new Set(baseKeys);
  const ordered = fieldOrderDraft.value.filter((fieldKey) => baseSet.has(fieldKey));
  const missing = baseKeys.filter((fieldKey) => !ordered.includes(fieldKey));
  return [...ordered, ...missing];
});

const selectedFormSettingsOrderTargetOptions = computed(() => {
  const selectedFieldKey = selectedFormSettingsFieldKey.value;
  return currentFormOrderedFieldKeys.value
    .filter((fieldKey) => fieldKey && fieldKey !== selectedFieldKey)
    .map((fieldKey) => ({
      fieldKey,
      label: formDesignFieldLabel(fieldKey),
    }));
});

watch([selectedFormSettingsFieldKey, selectedFormSettingsOrderTargetOptions], () => {
  if (!selectedFormSettingsFieldKey.value) {
    selectedFormSettingsOrderTargetKey.value = '';
    return;
  }
  const options = selectedFormSettingsOrderTargetOptions.value;
  if (!options.length) {
    selectedFormSettingsOrderTargetKey.value = '';
    return;
  }
  if (!options.some((option) => option.fieldKey === selectedFormSettingsOrderTargetKey.value)) {
    const selectedIndex = currentFormOrderedFieldKeys.value.indexOf(selectedFormSettingsFieldKey.value);
    const preferred = currentFormOrderedFieldKeys.value[selectedIndex + 1]
      || currentFormOrderedFieldKeys.value[selectedIndex - 1]
      || options[0].fieldKey;
    selectedFormSettingsOrderTargetKey.value = options.some((option) => option.fieldKey === preferred)
      ? preferred
      : options[0].fieldKey;
  }
}, { immediate: true });

function syncFieldOrderDraftWithDesignKeys(rawKeys = currentFormDesignFieldKeys.value) {
  if (!isContractFieldOrderEditable.value) return;
  const keys = Array.from(new Set(rawKeys.map((key) => String(key || '').trim()).filter(Boolean)));
  if (!keys.length) return;
  if (!fieldOrderPreviewActive.value) {
    const same = keys.length === fieldOrderDraft.value.length
      && keys.every((key, index) => fieldOrderDraft.value[index] === key);
    if (!same) fieldOrderDraft.value = keys;
    return;
  }
  const keySet = new Set(keys);
  const kept = fieldOrderDraft.value.filter((key) => keySet.has(key));
  const missing = keys.filter((key) => !kept.includes(key));
  fieldOrderDraft.value = [...kept, ...missing];
}

watch(currentFormDesignFieldKeys, (keys) => {
  syncFieldOrderDraftWithDesignKeys(keys);
  if (isContractFieldOrderEditable.value && keys.length && !lowCodeContractLoaded.value) {
    void hydrateLowCodeDraftFromContract();
  }
  if (isContractFieldOrderEditable.value && keys.length) {
    void refreshLowCodeFormLayoutBase();
  }
}, { immediate: true });

const hasFieldOrderChanges = computed(() => {
  if (!fieldOrderPreviewActive.value) return false;
  const rows = currentFormDesignFieldKeys.value;
  if (!rows.length || !fieldOrderDraft.value.length) return false;
  return rows.some((key, index) => fieldOrderDraft.value[index] !== key);
});

const formVisibilityDraftFieldKeys = computed(() => Array.from(new Set([
  ...currentFormDesignFieldKeys.value,
  ...Object.keys(fieldVisibilityDraft),
  ...Object.keys(fieldVisibilityBase.value),
].map((key) => String(key || '').trim()).filter(Boolean))));

const hasFieldVisibilityChanges = computed(() => formVisibilityDraftFieldKeys.value.some((fieldKey) => {
  if (!Object.prototype.hasOwnProperty.call(fieldVisibilityDraft, fieldKey)) return false;
  if (!Object.prototype.hasOwnProperty.call(fieldVisibilityBase.value, fieldKey)) return false;
  return fieldVisibilityDraft[fieldKey] !== fieldVisibilityBase.value[fieldKey];
}));

const hasFieldGroupChanges = computed(() => Object.keys(fieldGroupDraft).some((fieldKey) => {
  const draft = effectiveFieldGroupTitleForDraft(fieldKey);
  const base = normalizeFieldGroupTitle(fieldGroupSavedBase.value[fieldKey] || fieldGroupBase.value[fieldKey]);
  return Boolean(draft) && draft !== base;
}));

function effectiveGroupVisible(title: string) {
  const key = normalizeFieldGroupTitle(title);
  if (!key) return true;
  if (Object.prototype.hasOwnProperty.call(groupVisibilityDraft, key)) return groupVisibilityDraft[key] !== false;
  if (Object.prototype.hasOwnProperty.call(groupVisibilityBase.value, key)) return groupVisibilityBase.value[key] !== false;
  return true;
}

function effectiveGroupColumns(title: string): 1 | 2 | 3 {
  const key = normalizeFieldGroupTitle(title);
  if (!key) return formLayoutColumnsDraft.value;
  return groupColumnsDraft[key] || groupColumnsBase.value[key] || formLayoutColumnsDraft.value;
}

function effectiveFieldSize(fieldKey: string): LowCodeFieldSize {
  const key = String(fieldKey || '').trim();
  if (!key) return 'normal';
  return fieldSizeDraft[key] || fieldSizeBase.value[key] || 'normal';
}

const hasFormLayoutChanges = computed(() => formLayoutDirty.value);

const hasGroupLayoutChanges = computed(() => Object.keys(groupLayoutDirtyKeys).length > 0);

const hasFieldLayoutChanges = computed(() => Object.keys(fieldLayoutDirtyKeys).length > 0);

const hasCurrentFormFieldDraftChanges = computed(() => (
  hasFieldOrderChanges.value
  || hasFieldVisibilityChanges.value
  || hasFieldGroupChanges.value
  || hasFormLayoutChanges.value
  || hasGroupLayoutChanges.value
  || hasFieldLayoutChanges.value
  || fieldVisibilityDirty.value
));

function formConfigFieldLabelReplacementEntries() {
  return buildFormConfigFieldLabelReplacementEntries({
    cachedLabels: formConfigFieldLabelCache,
    nativeLabels: nativeFormDesignFieldLabels.value,
    activeRows: activeContractModeFieldRows.value,
    fieldKeys: currentFormDesignFieldKeys.value,
    resolveContractLabel: (fieldKey) => contractFieldLabel(fieldKey),
    resolveDescriptorLabel: (fieldKey) => {
      const descriptor = contract.value?.fields?.[fieldKey] as Record<string, unknown> | undefined;
      return String(descriptor?.string || descriptor?.label || '').trim();
    },
  });
}

function formatFormConfigOperationSummary(summary: string) {
  return formatFormConfigOperationSummaryText(summary, formConfigFieldLabelReplacementEntries());
}

function formDesignFieldLabel(fieldKey: string) {
  return resolveFormDesignFieldLabel({
    fieldKey,
    selectedFieldKey: selectedFormSettingsFieldKey.value,
    selectedFieldLabel: selectedFormSettingsFieldLabel.value,
    cachedLabels: formConfigFieldLabelCache,
    nativeLabels: nativeFormDesignFieldLabels.value,
    activeRows: activeContractModeFieldRows.value,
    resolveContractLabel: (key) => contractFieldLabel(key),
    resolveDescriptorLabel: (key) => {
      const descriptor = contract.value?.fields?.[key] as Record<string, unknown> | undefined;
      return String(descriptor?.string || descriptor?.label || '').trim();
    },
  });
}

function rememberFormConfigFieldLabel(fieldKey: string, label: string) {
  const key = String(fieldKey || '').trim();
  const normalizedLabel = String(label || '').trim();
  if (!key || !normalizedLabel || normalizedLabel === key) return;
  formConfigFieldLabelCache[key] = normalizedLabel;
}

const suggestedHiddenFieldRows = computed(() => currentFormDesignFieldKeys.value
  .map((fieldKey) => ({ fieldKey, label: formDesignFieldLabel(fieldKey) }))
  .filter((row) => {
    if (!isSuggestedInternalFormField(row.fieldKey, row.label)) return false;
    return fieldVisibilityDraft[row.fieldKey] !== false;
  }));

watch(hasCurrentFormFieldDraftChanges, (changed) => {
  if (changed) formConfigAuditResult.value = null;
});

function changedFieldVisibilityDraft() {
  return changedFieldVisibilityFromDrafts({
    fieldKeys: formVisibilityDraftFieldKeys.value,
    draft: fieldVisibilityDraft,
    base: fieldVisibilityBase.value,
    dirtyKeys: fieldVisibilityDirtyKeys,
  });
}

function changedFieldGroupDraft() {
  return changedFieldGroupFromDrafts({
    draftGroups: fieldGroupDraft,
    nativeBaseGroups: fieldGroupBase.value,
    savedBaseGroups: fieldGroupSavedBase.value,
    resolveDraftTitle: effectiveFieldGroupTitleForDraft,
  });
}

function effectiveFieldGroupTitleForDraft(fieldKey: string) {
  return effectiveFieldGroupTitleFromDrafts({
    fieldKey,
    draftGroups: fieldGroupDraft,
    nativeBaseGroups: fieldGroupBase.value,
    savedBaseGroups: fieldGroupSavedBase.value,
  });
}

async function auditCurrentFormConfiguration() {
  if (formConfigAuditBusy.value || busy.value) return;
  const params = lowCodeApplyBaseParams();
  const modelName = String(params.model || model.value || '').trim();
  if (!modelName) return;
  formConfigAuditBusy.value = true;
  try {
    const result = await intentRequest<{
      business_config_form_fields?: unknown[];
      business_config_form_layout_fields?: unknown[];
      has_business_config_form_layout?: boolean;
      layout_matches_fields?: boolean;
      legacy_policy_fields?: unknown[];
      skipped_legacy_policy_fields?: unknown[];
      active_legacy_policy_fields?: unknown[];
      has_conflict?: boolean;
    }>({
      intent: BUSINESS_CONFIG_INTENTS.formAudit,
      params: {
        ...params,
        model: modelName,
        view_type: 'form',
      },
      context: { view: 'form' },
    });
    formConfigAuditResult.value = normalizeFormConfigAuditResult(result);
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : '表单配置检查失败';
    status.value = 'error';
  } finally {
    formConfigAuditBusy.value = false;
  }
}

const showCurrentFormFieldConfigScope = computed(() => isContractFieldOrderEditable.value);
const showLowCodeTechnicalDetails = computed(() => {
  if (activeContractMode.value !== BUSINESS_CONFIG_MODES.lowCode) return showHud.value;
  const hudFlag = routeQueryText('hud').toLowerCase();
  const surface = routeQueryText('surface').toLowerCase();
  return hudFlag === '1' || hudFlag === 'true' || surface === 'hud';
});

const currentFormConfigPageLabel = computed(() => normalizeConfigPageLabel(
  routeQueryText('page_label')
  || routeQueryText('pageLabel')
  || currentBusinessCategoryLabel.value
  || pageTitle.value
  || '当前表单',
));

const formFieldConfigScope = computed(() => buildFormFieldConfigScope(currentFormConfigPageLabel.value));

const formConfigAuditSummary = computed(() => {
  return formatFormConfigAuditSummary(formConfigAuditResult.value, showLowCodeTechnicalDetails.value);
});

const selectedFormSettingsFieldRow = computed(() => {
  const fieldKey = selectedFormSettingsFieldKey.value;
  if (!fieldKey) return undefined;
  const row = activeContractModeFieldRows.value.find((item) => item.fieldKey === fieldKey);
  if (!row) {
    const label = selectedFormSettingsFieldLabel.value || fieldKey;
    const visible = Object.prototype.hasOwnProperty.call(fieldVisibilityDraft, fieldKey)
      ? fieldVisibilityDraft[fieldKey]
      : true;
    return {
      fieldKey,
      label,
      actions: [
        {
          key: `${fieldKey}:show`,
          label: '显示',
          value: 'show',
          checked: visible,
          disabled: busy.value,
          title: '在当前页面显示这个字段',
          raw: {},
        },
        {
          key: `${fieldKey}:hide`,
          label: '隐藏',
          value: 'hide',
          checked: !visible,
          disabled: busy.value,
          title: '在当前页面隐藏这个字段',
          raw: {},
        },
      ],
    };
  }
  return {
    ...row,
    label: selectedFormSettingsFieldLabel.value || row.label || fieldKey,
  };
});

const nativeFieldStructureGroups = computed<Array<{ key: string; title: string; fieldKeys: string[] }>>(() => {
  const lowCodeLayout = lowCodeFormLayoutBase.value;
  const useLowCodeLayout = isContractFieldOrderEditable.value && layoutHasReadableFieldGroups(lowCodeLayout);
  const legacyLayout = Array.isArray(contract.value?.views?.form?.layout)
    ? contract.value?.views?.form?.layout as unknown as NativeFormLayoutNode[]
    : [];
  const storeContainers = resolveContractV2ContainerTree(v2ContractStore.value);
  const v2 = storeContainers.length ? null : resolveUnifiedPageContractV2(contract.value);
  const containers = storeContainers.length
    ? storeContainers
    : (Array.isArray(v2?.layoutContract?.containerTree) ? v2.layoutContract.containerTree : []);
  const baseLayout = useLowCodeLayout
    ? mergeLowCodeLayoutWithRuntimeGroupShells(lowCodeLayout, runtimeNativeFormLayoutNodes())
    : (isContractFieldOrderEditable.value && legacyLayout.length
      ? legacyLayout
      : (containers.length
        ? normalizeContractV2ContainersForNativeFormFromTree(containers as unknown as NativeLayoutLikeNode[]) as NativeFormLayoutNode[]
        : legacyLayout));
  return collectNativeFieldStructureGroups(baseLayout as NativeLayoutLikeNode[]);
});

watch(nativeFieldStructureGroups, (groups) => {
  const nextBase: Record<string, string> = {};
  groups.forEach((group) => {
    const title = normalizeFieldGroupTitle(group.title || '主表区域');
    group.fieldKeys.forEach((fieldKey) => {
      if (fieldKey && !nextBase[fieldKey]) nextBase[fieldKey] = title;
    });
  });
  const preservedBase = Object.entries(fieldGroupBase.value).reduce<Record<string, string>>((acc, [fieldKey, title]) => {
    const key = String(fieldKey || '').trim();
    const normalized = normalizeFieldGroupTitle(title);
    if (key && isReadableFieldGroupTitle(normalized)) acc[key] = normalized;
    return acc;
  }, {});
  fieldGroupBase.value = { ...nextBase, ...preservedBase };
  currentFormDesignFieldKeys.value.forEach((fieldKey) => {
    if (!fieldKey) return;
    const title = fieldGroupBase.value[fieldKey];
    if (title && (!Object.prototype.hasOwnProperty.call(fieldGroupDraft, fieldKey) || !isReadableFieldGroupTitle(fieldGroupDraft[fieldKey]))) {
      fieldGroupDraft[fieldKey] = title;
    }
  });
}, { immediate: true });

const currentFormDesignFieldCount = computed(() => {
  if (activeContractModeFieldRows.value.length) return activeContractModeFieldRows.value.length;
  return nativeFieldStructureGroups.value.reduce((total, group) => total + group.fieldKeys.length, 0);
});

const currentFormGroupOptions = computed(() => {
  return buildCurrentFormGroupOptions({
    nativeGroups: nativeFieldStructureGroups.value,
    runtimeGroupTitles: collectNativeLayoutGroupTitles(runtimeNativeFormLayoutNodes()),
    fieldKeys: currentFormDesignFieldKeys.value,
    resolveDraftGroupTitle: effectiveFieldGroupTitleForDraft,
  });
});

const formDesignerGroupNavigatorItems = computed(() => {
  return buildFormDesignerGroupNavigatorItems({
    nativeGroups: nativeFieldStructureGroups.value,
    fieldKeys: currentFormDesignFieldKeys.value,
    selectedGroupTitle: selectedFormSettingsFieldGroupTitle.value,
    resolveDraftGroupTitle: effectiveFieldGroupTitleForDraft,
  });
});

const formDesignerFieldSearchQuery = computed(() => String(formDesignerFieldSearchText.value || '').trim().toLowerCase());

const formDesignerSearchableFieldRows = computed(() => {
  return buildFormDesignerSearchableFieldRows({
    orderedFieldKeys: currentFormOrderedFieldKeys.value,
    fallbackFieldKeys: currentFormDesignFieldKeys.value,
    nativeGroups: nativeFieldStructureGroups.value,
    resolveDraftGroupTitle: effectiveFieldGroupTitleForDraft,
    resolveFieldLabel: formDesignFieldLabel,
  });
});

const formDesignerFilteredFieldRows = computed(() => {
  return filterFormDesignerFieldRows(formDesignerSearchableFieldRows.value, formDesignerFieldSearchQuery.value);
});

const selectedFormSettingsFieldGroupTitle = computed(() => {
  return resolveSelectedFormSettingsFieldGroupTitle({
    fieldKey: selectedFormSettingsFieldKey.value,
    draftGroupTitle: effectiveFieldGroupTitleForDraft(selectedFormSettingsFieldKey.value),
    nativeGroups: nativeFieldStructureGroups.value,
    fallbackDraftTitle: selectedFormSettingsFieldGroupTitleDraft.value,
  });
});

const selectedFormSettingsGroupVisible = computed(() => effectiveGroupVisible(selectedFormSettingsFieldGroupTitle.value));
const selectedFormSettingsGroupColumns = computed(() => effectiveGroupColumns(selectedFormSettingsFieldGroupTitle.value));
const selectedFormSettingsFieldSize = computed(() => effectiveFieldSize(selectedFormSettingsFieldKey.value));

watch(selectedFormSettingsFieldGroupTitle, (title) => {
  selectedFormSettingsFieldGroupTitleEdit.value = title;
});

function syncLayoutDraftFromFormSpec(formSpec: Record<string, unknown>) {
  const runtimeColumns = inferLowCodeLayoutColumns(runtimeNativeFormLayoutNodes()) || inferLowCodeLayoutColumns(rawNativeFormLayoutNodes.value) || 3;
  const next = extractLowCodeLayoutDraftState(formSpec, runtimeColumns);
  formLayoutColumnsConfigured.value = next.columnsConfigured;
  formLayoutColumnsBase.value = next.columns;
  if (!formLayoutDirty.value) {
    formLayoutColumnsDraft.value = next.columns;
  }
  groupVisibilityBase.value = next.groupVisible;
  if (!Object.keys(groupLayoutDirtyKeys).length) {
    Object.keys(groupVisibilityDraft).forEach((key) => delete groupVisibilityDraft[key]);
    Object.entries(next.groupVisible).forEach(([key, value]) => {
      groupVisibilityDraft[key] = value;
    });
  }
  groupColumnsBase.value = next.groupColumns;
  if (!Object.keys(groupLayoutDirtyKeys).length) {
    Object.keys(groupColumnsDraft).forEach((key) => delete groupColumnsDraft[key]);
    Object.entries(next.groupColumns).forEach(([key, value]) => {
      groupColumnsDraft[key] = value;
    });
  }
  fieldSizeBase.value = next.fieldSize;
  if (!Object.keys(fieldLayoutDirtyKeys).length) {
    Object.keys(fieldSizeDraft).forEach((key) => delete fieldSizeDraft[key]);
    Object.entries(next.fieldSize).forEach(([key, value]) => {
      fieldSizeDraft[key] = value;
    });
  }
}

function syncFieldDraftFromFormSpec(
  formSpec: Record<string, unknown>,
  options: { overwriteDraftGroups?: boolean; syncOrder?: boolean; syncVisibility?: boolean } = {},
) {
  const state = extractLowCodeFormFieldDraftState(formSpec);
  if (options.syncOrder !== false && state.orderedFieldNames.length) fieldOrderDraft.value = state.orderedFieldNames;
  if (options.syncVisibility !== false) {
    Object.entries(state.visibility).forEach(([key, visible]) => {
      fieldVisibilityBase.value = { ...fieldVisibilityBase.value, [key]: visible };
      fieldVisibilityDraft[key] = visible;
    });
  }
  Object.entries(state.groups).forEach(([key, groupTitle]) => {
    const previousDraft = normalizeFieldGroupTitle(fieldGroupDraft[key]);
    const previousBase = normalizeFieldGroupTitle(fieldGroupBase.value[key]);
    const shouldSyncDraft = options.overwriteDraftGroups
      || !previousDraft
      || previousDraft === previousBase
      || previousDraft.startsWith('默认分组');
    fieldGroupSavedBase.value = { ...fieldGroupSavedBase.value, [key]: groupTitle };
    fieldGroupBase.value = { ...fieldGroupBase.value, [key]: groupTitle };
    if (shouldSyncDraft) fieldGroupDraft[key] = groupTitle;
  });
}

function applyRuntimeInferredFormColumns() {
  if (!isContractFieldOrderEditable.value || formLayoutColumnsConfigured.value || formLayoutDirty.value) return;
  const runtimeColumns = inferLowCodeLayoutColumns(runtimeNativeFormLayoutNodes());
  if (!runtimeColumns || runtimeColumns === formLayoutColumnsBase.value) return;
  formLayoutColumnsBase.value = runtimeColumns;
  formLayoutColumnsDraft.value = runtimeColumns;
  Object.keys(groupColumnsDraft).forEach((key) => delete groupColumnsDraft[key]);
  groupColumnsBase.value = {};
}

async function hydrateLowCodeDraftFromContract() {
  if (!isContractFieldOrderEditable.value || lowCodeContractLoaded.value || lowCodeContractHydrating.value) return;
  const modelName = String(model.value || '').trim();
  if (!modelName) return;
  let hydrated = false;
  lowCodeContractHydrating.value = true;
  try {
    const base = lowCodeApplyBaseParams();
    const scopedName = lowCodeScopedContractName(modelName, base);
    const listResult = await intentRequest<{
      items?: Array<{ name?: string }>;
    }>({
      intent: BUSINESS_CONFIG_INTENTS.contractList,
      params: { ...base, model: modelName, view_type: 'form' },
    }).catch(() => null);
    const availableNames = new Set((Array.isArray(listResult?.items) ? listResult?.items || [] : [])
      .map((row) => String(row?.name || '').trim())
      .filter(Boolean));
    const contractName = availableNames.has(scopedName) ? scopedName : '';
    if (!contractName) return;
    const res = await intentRequest<{
      contract_json?: {
        objects?: Array<{ name?: string; fields?: Array<{ name?: string; visible?: boolean; order?: number }> }>;
      }
    }>({
      intent: BUSINESS_CONFIG_INTENTS.contractGet,
      params: { ...base, model: modelName, name: contractName, view_type: 'form' },
    }).catch(() => null);
    if (!res) return;
    const orchestrationViews = lowCodeViewsFromContractResponse(res);
    const formSpec = lowCodeFormSpecFromViews(orchestrationViews);
    lowCodeFormLayoutBase.value = lowCodeLayoutFromFormSpec(formSpec) as NativeFormLayoutNode[];
    syncLayoutDraftFromFormSpec(formSpec);
    syncFieldDraftFromFormSpec(formSpec, { overwriteDraftGroups: true });
    lowCodeLayoutDraft.value = collectLowCodeLayoutFromViewOrchestration(orchestrationViews, modelName);
    hydrated = true;
  } catch {
    // ignore low-code contract hydrate failure in form runtime
  } finally {
    if (hydrated) lowCodeContractLoaded.value = true;
    lowCodeContractHydrating.value = false;
  }
}

async function refreshLowCodeFormLayoutBase() {
  if (!isContractFieldOrderEditable.value || lowCodeContractHydrating.value) return;
  const modelName = String(model.value || '').trim();
  if (!modelName) return;
  try {
    const base = lowCodeApplyBaseParams();
    const scopedName = lowCodeScopedContractName(modelName, base);
    const res = await intentRequest<{
      contract_json?: { view_orchestration?: Record<string, unknown> }
    }>({
      intent: BUSINESS_CONFIG_INTENTS.contractGet,
      params: { ...base, model: modelName, name: scopedName, view_type: 'form' },
    }).catch(() => null);
    const orchestrationViews = lowCodeViewsFromContractResponse(res);
    const formSpec = lowCodeFormSpecFromViews(orchestrationViews);
    lowCodeFormLayoutBase.value = lowCodeLayoutFromFormSpec(formSpec) as NativeFormLayoutNode[];
    syncLayoutDraftFromFormSpec(formSpec);
    syncFieldDraftFromFormSpec(formSpec, { syncOrder: false, syncVisibility: false });
  } catch {
    // Form config still works from runtime layout if the saved contract cannot be read.
  }
}

async function loadLowCodeContractList() {
  if (!isContractFieldOrderEditable.value) return;
  const modelName = String(model.value || '').trim();
  if (!modelName) return;
  try {
    const base = lowCodeApplyBaseParams();
    const result = await intentRequest<{
      items?: Array<{ id?: number; name?: string; model?: string; status?: string; version_no?: number }>;
    }>({
      intent: BUSINESS_CONFIG_INTENTS.contractList,
      params: { ...base, model: modelName, view_type: 'form' },
    });
    lowCodeContractList.value = normalizeLowCodeContractListRows(result?.items);
    if (lowCodeSelectedContractName.value && !lowCodeContractList.value.some((row) => row.name === lowCodeSelectedContractName.value)) {
      lowCodeSelectedContractName.value = '';
    }
    if (!lowCodeSelectedContractName.value && lowCodeContractList.value.length) {
      lowCodeSelectedContractName.value = lowCodeContractList.value[0].name;
    }
  } catch {
    lowCodeContractList.value = [];
  }
}

async function switchLowCodeContractByName() {
  const name = String(lowCodeSelectedContractName.value || '').trim();
  const modelName = String(model.value || '').trim();
  if (!name || !modelName) return;
  try {
    const base = lowCodeApplyBaseParams();
    const res = await intentRequest<{
      contract_json?: {
        view_orchestration?: Record<string, unknown>;
      }
    }>({
      intent: BUSINESS_CONFIG_INTENTS.contractGet,
      params: { ...base, model: modelName, name, view_type: 'form' },
    });
    lowCodeContractLoaded.value = false;
    const orchestrationViews = lowCodeViewsFromContractResponse(res);
    const formSpec = lowCodeFormSpecFromViews(orchestrationViews);
    lowCodeFormLayoutBase.value = lowCodeLayoutFromFormSpec(formSpec) as NativeFormLayoutNode[];
    syncLayoutDraftFromFormSpec(formSpec);
    syncFieldDraftFromFormSpec(formSpec, { overwriteDraftGroups: true });
    lowCodeLayoutDraft.value = collectLowCodeLayoutFromViewOrchestration(orchestrationViews, modelName);
  } catch {
    // ignore
  }
}

async function publishSelectedLowCodeContract() {
  const name = String(lowCodeSelectedContractName.value || '').trim();
  const modelName = String(model.value || '').trim();
  if (!name || !modelName || busy.value) return;
  busyKind.value = 'action';
  try {
    const base = lowCodeApplyBaseParams();
    await intentRequest({
      intent: BUSINESS_CONFIG_INTENTS.contractPublish,
      params: { ...base, name, model: modelName, view_type: 'form' },
    });
    contractModeFeedback.value = '配置版本已发布，刷新页面后按新配置生效';
    await loadLowCodeContractList();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : '配置版本发布失败';
    status.value = 'error';
  } finally {
    busyKind.value = null;
  }
}

async function rollbackSelectedLowCodeContract() {
  const name = String(lowCodeSelectedContractName.value || '').trim();
  const modelName = String(model.value || '').trim();
  if (!name || !modelName || busy.value) return;
  busyKind.value = 'action';
  try {
    const base = lowCodeApplyBaseParams();
    await intentRequest({
      intent: BUSINESS_CONFIG_INTENTS.contractRollback,
      params: { ...base, name, model: modelName, view_type: 'form' },
    });
    contractModeFeedback.value = '配置版本已回滚到上一版并发布生效';
    await loadLowCodeContractList();
    await switchLowCodeContractByName();
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : '配置版本回滚失败';
    status.value = 'error';
  } finally {
    busyKind.value = null;
  }
}

function buildLowCodeViewOrchestration() {
  const availableFields = contract.value?.fields || {};
  return buildLowCodeViewOrchestrationFromDraft({
    availableFieldNames: Object.keys(availableFields),
    layoutDraft: lowCodeLayoutDraft.value,
    formOrderDraft: fieldOrderDraft.value,
    formOrderEditable: isContractFieldOrderEditable.value,
    formColumns: formLayoutColumnsDraft.value,
    resolveFieldLabel: (name) => effectiveLowCodeFieldLabel(name, availableFields[name]),
    resolveFieldGroupTitle: effectiveFieldGroupTitleForDraft,
    resolveFieldVisible: (name, groupTitle) => fieldVisibilityDraft[name] !== false && effectiveGroupVisible(groupTitle),
    resolveGroupVisible: effectiveGroupVisible,
    resolveGroupColumns: effectiveGroupColumns,
    resolveFieldSize: effectiveFieldSize,
  });
}

function lowCodeLayoutFieldLabel(name: string) {
  return lowCodeLayoutFieldLabelFromNodes(name, rawNativeFormLayoutNodes.value, lowCodeFormLayoutBase.value);
}

function effectiveLowCodeFieldLabel(name: string, descriptor?: FieldDescriptor) {
  const fieldName = String(name || '').trim();
  return String(
    contractFieldLabel(fieldName)
    || lowCodeLayoutFieldLabel(fieldName)
    || descriptor?.string
    || readableFallbackFieldLabel(fieldName),
  ).trim() || readableFallbackFieldLabel(fieldName);
}

const isQuickSubmitDisabled = computed(() => {
  if (busy.value) return true;
  if (!canSave.value) return true;
  if (isProjectQuickIntakeMode.value) return !quickRequiredReady.value;
  return Boolean(recordId.value) && !hasChanges.value;
});
const primaryFormActionDisabled = computed(() => {
  if (busy.value) return true;
  if (!canSave.value) return true;
  if (primaryCreateFooterAction.value) return false;
  if (primarySubmitAction.value) return false;
  return isQuickSubmitDisabled.value;
});
const draftSaveDisabled = computed(() => {
  if (busy.value) return true;
  if (!canSave.value) return true;
  return Boolean(recordId.value) && !hasChanges.value;
});
const isStandardCreateDisabled = computed(() => {
  if (busy.value) return true;
  if (!canSave.value) return true;
  if (isProjectStandardIntakeMode.value) return !standardCreateReady.value;
  return false;
});

const isIntakeCreateDisabled = computed(() => {
  if (!isProjectIntakeCreateMode.value) return false;
  if (isProjectQuickIntakeMode.value) return isQuickSubmitDisabled.value;
  return isStandardCreateDisabled.value;
});

function persistIntakeAutosave() {
  const key = intakeAutosaveKey.value;
  if (!key || recordId.value) return;
  persistIntakeAutosavePayload(key, formData as Record<string, unknown>);
}

function restoreIntakeAutosave() {
  const key = intakeAutosaveKey.value;
  if (!key || recordId.value) return;
  Object.entries(restoreIntakeAutosavePayload(key)).forEach(([field, value]) => {
    formData[field] = value as never;
  });
}

function clearIntakeAutosave() {
  const key = intakeAutosaveKey.value;
  if (!key) return;
  clearIntakeAutosavePayload(key);
}

const contractMetaLine = computed(() => {
  if (!contract.value) return '';
  const mode = String(contractMeta.value?.contract_mode || '-');
  const surface = String((contract.value as Record<string, unknown>)?.contract_surface || contractMeta.value?.contract_surface || '-');
  const viewType = String(contract.value.head?.view_type || contract.value.view_type || '-');
  const filters = Array.isArray(contract.value.search?.filters) ? contract.value.search.filters.length : 0;
  const transitions = Array.isArray(contract.value.workflow?.transitions) ? contract.value.workflow.transitions.length : 0;
  const profileLabels: Record<string, string> = {
    create: '新建',
    edit: '编辑',
    readonly: '只读',
  };
  const permissionLabels = [
    rights.value.read ? '可查看' : '',
    rights.value.write ? '可编辑' : '',
    rights.value.create ? '可新建' : '',
    rights.value.unlink ? '可删除' : '',
  ].filter(Boolean);
  const valueLabel = (value: string, labels: Record<string, string>) => {
    const normalized = String(value || '').trim().toLowerCase();
    if (!normalized || normalized === '-') return '未配置';
    return labels[normalized] || value;
  };
  const modeLabel = valueLabel(mode, {
    native: '标准表单',
    governed: '受控表单',
    action: '操作页面',
    legacy: '历史承载',
  });
  const surfaceLabel = valueLabel(surface, {
    native: '标准界面',
    governed: '受控界面',
    business_config: '配置界面',
    lowcode_config: '低代码配置',
  });
  const viewTypeLabel = valueLabel(viewType, {
    form: '表单',
    tree: '列表',
    list: '列表',
    kanban: '看板',
    search: '搜索',
    calendar: '日历',
    pivot: '透视',
    graph: '图表',
  });
  return `配置模式：${modeLabel} · 承载界面：${surfaceLabel} · 视图类型：${viewTypeLabel} · 页面状态：${profileLabels[renderProfile.value] || renderProfile.value} · 筛选项：${filters} · 流转项：${transitions} · 操作权限：${permissionLabels.join('、') || '无可用权限'}`;
});

const showDebugActions = computed(() => renderProfile.value !== 'create');
const showDebugActionsVisible = computed(() => showHud.value && showDebugActions.value);
const runtimeRoleCode = computed(() => String(session.roleSurface?.role_code || '').trim().toLowerCase());
const runtimeCapabilities = computed(() => collectRuntimeCapabilities(session));
const runtimeUserGroups = computed(() => collectRuntimeUserGroups(session.user as { groups_xmlids?: unknown } | null));
const policyContext = computed(() => ({
  profile: renderProfile.value,
  formData: formData as Record<string, unknown>,
  capabilities: runtimeCapabilities.value,
  userGroups: runtimeUserGroups.value,
  roleCode: runtimeRoleCode.value,
}));

const warnings = computed(() => normalizeContractWarnings(contract.value?.warnings));

const contractAccessPolicy = computed<ContractAccessPolicy>(() => {
  const raw = (contract.value as Record<string, unknown> | null)?.access_policy;
  return normalizeContractAccessPolicy(raw);
});

const workflowTransitions = computed(() => buildWorkflowTransitions({
  rows: contract.value?.workflow?.transitions,
  actions: contractActions.value,
  profile: renderProfile.value,
  showHud: showHud.value,
}));

const searchFilters = computed(() => normalizeSearchFilters(contract.value?.search?.filters));

const showSearchFilters = computed(() => {
  if (useNativeFormTree.value) return false;
  if (!contract.value) return true;
  if (renderProfile.value !== 'create') return true;
  return !contract.value.hide_filters_on_create;
});

function relationIds(name: string): number[] {
  return normalizeRelationIds(formData[name]);
}

function selectedRelationOptions(name: string): RelationOption[] {
  return selectedRelationOptionsFromRuntime(name, formData[name]);
}

function many2oneValue(name: string) {
  const ids = relationIds(name);
  return ids.length ? String(ids[0]) : '';
}

function relationOptionsForField(name: string) {
  return relationOptionsForFieldFromRuntime(name, formData[name]);
}

async function hydrateSelectedRelationOptions() {
  const fields = contract.value?.fields || {};
  await Promise.all(Object.entries(fields).map(async ([name, descriptor]) => {
    const type = fieldType(descriptor);
    if (!['many2one', 'many2many'].includes(type)) return;
    const relation = relationModel(name);
    if (!relation || deniedRelationModels.has(relation)) return;
    const ids = relationIds(name);
    if (!ids.length) return;
    const existingIds = new Set((relationOptions.value[name] || []).map((option) => option.id));
    const missingIds = ids.filter((id) => !existingIds.has(id));
    if (!missingIds.length) return;
    try {
      const response = await readContractFormRecord({
        model: relation,
        ids: missingIds,
        fields: relationReadFields(descriptor),
      });
      const options = relationOptionsFromRecords(response.records, descriptor);
      if (options.length) mergeRelationOptions(name, options);
    } catch (err) {
      if (err instanceof ApiError) {
        const denied = err.status === 403 || String(err.reasonCode || '').toUpperCase() === 'PERMISSION_DENIED';
        if (denied) deniedRelationModels.add(relation);
      }
    }
  }));
}

function one2manyRelationModel(name: string) {
  const descriptor = contract.value?.fields?.[name] as Record<string, unknown> | undefined;
  return String(descriptor?.relation || '').trim();
}

function one2manyRelationFieldDescriptor(fieldName: string, column: string) {
  const model = one2manyRelationModel(fieldName);
  if (!model) return null;
  const map = relationFieldDescriptors.value[model] || {};
  const descriptor = map[column];
  return descriptor || null;
}

function nativeNodeFieldDescriptor(nodeRaw: NativeFormLayoutNode, fallback?: FieldDescriptor): FieldDescriptor | undefined {
  return nativeNodeFieldDescriptorFromNode(nodeRaw as NativeLayoutLikeNode, fallback, contractFieldLabel);
}

function findNativeFieldNode(name: string): NativeFormLayoutNode | null {
  return findNativeFieldNodeInTree(nativeFormLayoutNodes.value as NativeLayoutLikeNode[], name) as NativeFormLayoutNode | null;
}

function effectiveFieldDescriptor(name: string): FieldDescriptor | undefined {
  const normalized = String(name || '').trim();
  if (!normalized) return undefined;
  const fallback = contract.value?.fields?.[normalized];
  const nativeNode = findNativeFieldNode(normalized);
  return nativeNode ? nativeNodeFieldDescriptor(nativeNode, fallback) : fallback;
}

function mergeNativeLayoutFieldDescriptorsIntoContract() {
  if (!contract.value?.fields) return;
  const fields = { ...(contract.value.fields || {}) };
  let changed = false;
  const walk = (nodes: NativeFormLayoutNode[]) => {
    nodes.forEach((node) => {
      const type = String(node?.type || (node as { containerType?: string })?.containerType || '').trim().toLowerCase();
      const name = String(node?.name || '').trim();
      if (type === 'field' && name) {
        const descriptor = nativeNodeFieldDescriptor(node, fields[name]);
        if (descriptor) {
          fields[name] = descriptor;
          changed = true;
        }
      }
      for (const key of ['children', 'pages', 'tabs', 'nodes', 'items'] as const) {
        const children = node?.[key];
        if (Array.isArray(children)) walk(children as NativeFormLayoutNode[]);
      }
    });
  };
  walk(rawNativeFormLayoutNodes.value);
  if (changed) {
    contract.value = {
      ...contract.value,
      fields,
    };
  }
}

function nativeFieldSubview(name: string): Record<string, unknown> | null {
  return nativeFieldSubviewFromTree(nativeFormLayoutNodes.value as NativeLayoutLikeNode[], name);
}

function one2manyColumns(name: string): One2ManyColumn[] {
  const subviews = (contract.value?.views?.form as Record<string, unknown> | undefined)?.subviews;
  const legacySubview = subviews && typeof subviews === 'object'
    ? (subviews as Record<string, unknown>)[name]
    : undefined;
  const nativeSubview = nativeFieldSubview(name);
  const fieldSubview = selectOne2manySubview(legacySubview, nativeSubview);
  return one2manyColumnsFromSubview(fieldSubview, (column) => one2manyRelationFieldDescriptor(name, column));
}

function one2manyPolicies(name: string) {
  const subviews = (contract.value?.views?.form as Record<string, unknown> | undefined)?.subviews;
  const legacySubview = subviews && typeof subviews === 'object'
    ? (subviews as Record<string, unknown>)[name]
    : undefined;
  const nativeSubview = nativeFieldSubview(name);
  const fieldSubview = selectOne2manySubview(legacySubview, nativeSubview);
  return one2manySubviewPolicies(fieldSubview);
}

function one2manyCanCreate(name: string) {
  return one2manyCanCreateFromPolicies(one2manyPolicies(name));
}

function one2manyCreateLabel(name: string, fieldLabel = '') {
  const label = String(fieldLabel || contractFieldLabel(name) || contract.value?.fields?.[name]?.string || '').trim();
  return one2manyCreateLabelFromPolicies(one2manyPolicies(name), label);
}

function one2manyPrimaryColumn(name: string) {
  return one2manyPrimaryColumnFromColumns(one2manyColumns(name));
}

function one2manyRowLabel(fieldName: string, row: One2ManyInlineRow) {
  return one2manyRowLabelFromPrimary(one2manyPrimaryColumn(fieldName), row);
}

function one2manySummary(name: string) {
  return one2manyDraftSummary(one2manyFieldRows(name));
}

async function hydrateOne2manyRows(name: string) {
  const relation = one2manyRelationModel(name);
  if (!relation) return;
  const rows = ensureOne2manyRows(name).filter((row) => row.id && !row.isNew);
  if (!rows.length) return;
  const columns = one2manyColumns(name);
  if (!columns.length) return;
  const fields = Array.from(new Set(['id', 'display_name', 'name', ...columns.map((column) => column.name)]));
  try {
    const response = await readContractFormRecord({
      model: relation,
      ids: rows.map((row) => Number(row.id)).filter((id) => Number.isFinite(id) && id > 0),
      fields,
    });
    const records = Array.isArray(response.records) ? response.records : [];
    mergeHydratedOne2manyRecords(name, records as Array<Record<string, unknown>>);
  } catch {
    // Keep the id/display-name fallback when the child model is not readable.
  }
}

async function hydrateVisibleOne2manyRows() {
  const fields = contract.value?.fields || {};
  const names = Object.entries(fields)
    .filter(([, descriptor]) => fieldType(descriptor) === 'one2many')
    .map(([name]) => name)
    .filter((name) => isWritableFieldVisible(name) || one2manyFieldRows(name).length > 0);
  await Promise.all(names.map((name) => hydrateOne2manyRows(name)));
}

function one2manyRowErrors(fieldName: string, rowKey: string) {
  return one2manyValidation.value.rowErrors[`${fieldName}:${rowKey}`] || [];
}

function setRelationKeyword(name: string, keyword: string) {
  setRelationKeywordValue(name, keyword);
  const descriptor = effectiveFieldDescriptor(name);
  const widget = String((descriptor as Record<string, unknown> | undefined)?.widget || '').trim().toLowerCase();
  if (fieldType(descriptor) === 'many2many' && widget === 'many2many_tags') {
    markFieldChanged(name);
  }
  if (relationQueryTimers[name]) {
    clearTimeout(relationQueryTimers[name]);
  }
  relationQueryTimers[name] = setTimeout(() => {
    const currentKeyword = relationKeywords[name] || '';
    void queryRelationOptions(name, currentKeyword);
  }, 260);
}

function filteredRelationOptions(name: string) {
  return filteredRelationOptionsFromRuntime(name, formData[name]);
}

function relationModel(name: string) {
  return relationModelFromDescriptor(effectiveFieldDescriptor(name));
}

function formUiLabels(): Record<string, string> {
  return formUiLabelsFromFormView(contract.value?.views?.form);
}

function formUiLabel(key: string) {
  return formUiLabelFromLabels(formUiLabels(), key);
}

function dynamicDomainFromDescriptor(descriptor?: FieldDescriptor) {
  return dynamicRelationDomainFromDescriptor({
    descriptor,
    resolveDependencyValue: resolveDynamicDomainDependencyValue,
    normalizeDependencyValue: normalizeFieldValue,
    currentFieldValue: (fieldName) => formData[fieldName],
  });
}

function resolveDynamicDomainDependencyValue(valueField: string) {
  const direct = formData[valueField]
    ?? route.query[`default_${valueField}`]
    ?? route.query[valueField];
  if (direct !== undefined && direct !== null && direct !== '') return direct;
  const keyword = relationKeyword(valueField).trim().toLowerCase();
  if (!keyword) return direct;
  const option = (relationOptions.value[valueField] || []).find((item) => {
    const label = item.label.trim().toLowerCase();
    return label === keyword || label.includes(keyword) || keyword.includes(label);
  });
  return option?.id || direct;
}

function clearDynamicRelationDependents(changedName: string) {
  const fields = contract.value?.fields || {};
  const changed = String(changedName || '').trim();
  if (!changed) return;
  Object.entries(fields).forEach(([name, descriptor]) => {
    descriptor = effectiveFieldDescriptor(name) || descriptor;
    if (name === changed) return;
    if (!['many2one', 'many2many'].includes(fieldType(descriptor))) return;
    if (!dynamicDomainDependencyFields(descriptor).includes(changed)) return;
    const currentIds = relationIds(name);
    const selectedOption = currentIds.length
      ? (relationOptions.value[name] || []).find((option) => option.id === currentIds[0])
      : null;
    const staleKeyword = relationKeyword(name).trim() || String(selectedOption?.label || '').trim();
    if (staleKeyword) invalidatedRelationKeywords[name] = staleKeyword;
    clearedDynamicRelationFields[name] = true;
    if (fieldType(descriptor) === 'many2many') {
      formData[name] = [];
    } else {
      formData[name] = false;
    }
    if (relationQueryTimers[name]) {
      clearTimeout(relationQueryTimers[name]);
      delete relationQueryTimers[name];
    }
    relationKeywords[name] = '';
    relationOptions.value = {
      ...relationOptions.value,
      [name]: [],
    };
    void queryRelationOptions(name, '');
  });
}

function relationDomain(descriptor?: FieldDescriptor) {
  return relationDomainFromDescriptor({
    descriptor,
    dynamicDomain: dynamicDomainFromDescriptor(descriptor),
    routeDefaultType: String(route.query.default_type || '').trim(),
  });
}

function runtimeRelationDomain(name: string) {
  return runtimeRelationDomainFromModifiers({
    fieldName: name,
    baseModifiers: fieldModifierMap.value,
    patchModifiers: onchangeModifiersPatch.value,
  });
}

function mergedRelationDomain(name: string, descriptor?: FieldDescriptor) {
  return mergeRelationDomains(relationDomain(descriptor), runtimeRelationDomain(name));
}

async function queryRelationOptions(name: string, keyword: string): Promise<RelationOption[]> {
  const descriptor = effectiveFieldDescriptor(name);
  const relation = relationModel(name);
  const entry = relationEntry(descriptor);
  const domain = mergedRelationDomain(name, descriptor);
  return queryRelationOptionsFromRuntime({
    fieldName: name,
    keyword,
    relation,
    canRead: entry?.canRead !== false,
    hasDynamicFallback: Boolean(dynamicDomainDependencyFields(descriptor).length || runtimeRelationDomain(name).length),
    currentValue: formData[name],
    isDeniedError: (err) => err instanceof ApiError && (
      err.status === 403 || String(err.reasonCode || '').toUpperCase() === 'PERMISSION_DENIED'
    ),
    fetchOptions: async (search, limit) => {
      const listed = await listContractFormRecords({
        model: relation,
        fields: relationReadFields(descriptor),
        limit,
        order: relationOrder(descriptor),
        domain,
        search_term: search || undefined,
        silentErrors: true,
      });
      return relationOptionsFromRecords(listed?.records, descriptor);
    },
  });
}

async function fetchRelationOptions(name: string, keyword: string, limit = 80): Promise<RelationOption[]> {
  const descriptor = effectiveFieldDescriptor(name);
  const relation = relationModel(name);
  const entry = relationEntry(descriptor);
  const domain = mergedRelationDomain(name, descriptor);
  return fetchRelationOptionsFromRuntime({
    relation,
    canRead: entry?.canRead !== false,
    keyword,
    limit,
    fetchOptions: async (search, limitValue) => {
      const listed = await listContractFormRecords({
        model: relation,
        fields: relationReadFields(descriptor),
        limit: limitValue,
        order: relationOrder(descriptor),
        domain,
        search_term: search || undefined,
        silentErrors: true,
      });
      return relationOptionsFromRecords(listed?.records, descriptor);
    },
  });
}

async function loadRelationSearchColumns(fieldName: string): Promise<RelationSearchColumn[]> {
  const descriptor = effectiveFieldDescriptor(fieldName);
  const contractColumns = relationSearchColumnsFromContract(relationSearchDialogContract(descriptor));
  if (contractColumns.length) return contractColumns;
  const relation = relationModel(fieldName);
  if (!relation) return fallbackRelationSearchColumns(descriptor);
  try {
    const response = await loadModelContractRaw(relation, {
      viewType: 'tree',
      renderProfile: 'readonly',
    });
    const data = response?.data && typeof response.data === 'object'
      ? response.data as Record<string, unknown>
      : response as unknown as Record<string, unknown>;
    return normalizeRelationSearchColumns(data, descriptor);
  } catch {
    return fallbackRelationSearchColumns(descriptor);
  }
}

async function fetchRelationSearchRows(name: string, keyword: string, limit = 120): Promise<RelationSearchRow[]> {
  const descriptor = effectiveFieldDescriptor(name);
  const relation = relationModel(name);
  if (!relation) return [];
  const entry = relationEntry(descriptor);
  if (entry && entry.canRead === false) return [];
  const domain = mergedRelationDomain(name, descriptor);
  const dialog = relationSearchDialogContract(descriptor);
  const columns = relationSearchDialog.columns.length ? relationSearchDialog.columns : relationSearchColumnsFromContract(dialog);
  const listed = await listContractFormRecords({
    model: relation,
    fields: relationSearchReadFields(columns.length ? columns : fallbackRelationSearchColumns(descriptor), dialog),
    limit: relationSearchLimit(dialog, limit),
    order: relationSearchOrder(dialog),
    domain,
    search_term: String(keyword || '').trim() || undefined,
    silentErrors: true,
  });
  const records = Array.isArray(listed?.records) ? listed.records : [];
  return relationSearchRowsFromRecords(records, columns);
}

function onRelationDialogDocumentKeydown(event: KeyboardEvent) {
  if (!relationSearchDialog.open || event.key !== 'Escape') return;
  event.preventDefault();
  closeRelationSearchDialog();
}

async function openRelationSearchDialog(fieldName: string, descriptor?: FieldDescriptor) {
  const relation = relationModel(fieldName);
  if (!relation) return;
  const labels = relationUiLabels(descriptor);
  const resolvedDescriptor = effectiveFieldDescriptor(fieldName);
  await openRelationSearchFromRuntime({
    fieldName,
    descriptor,
    labels,
    keyword: relationKeyword(fieldName),
    columns: relationSearchColumnsFromContract(relationSearchDialogContract(resolvedDescriptor)),
    createMode: relationCreateMode(resolvedDescriptor),
    loadColumns: () => loadRelationSearchColumns(fieldName),
    runSearch: runRelationSearch,
  });
}

async function runRelationSearch() {
  await runRelationSearchFromRuntime({
    fetchRows: (fieldName, keyword) => fetchRelationSearchRows(fieldName, keyword, 120),
    sanitizeError: (error, fallback) => sanitizeUiErrorMessage(error instanceof Error ? error.message : error, fallback),
  });
}

function confirmRelationSearchSelection(rowArg?: RelationSearchRow) {
  confirmRelationSearchSelectionFromRuntime(selectRelationSearchOption, rowArg);
}

function selectRelationSearchOption(option: RelationOption) {
  selectRelationSearchOptionFromRuntime(option, setMany2oneOption);
}

function setMany2oneOption(fieldName: string, option: RelationOption) {
  formData[fieldName] = option.id;
  relationKeywords[fieldName] = option.label;
  mergeRelationOptions(fieldName, [option]);
  clearDynamicRelationDependents(fieldName);
  markFieldChanged(fieldName);
  void switchFormByRelationOption(fieldName, option);
}

async function switchFormByRelationOption(fieldName: string, option: RelationOption) {
  if (recordId.value) return;
  const descriptor = contract.value?.fields?.[fieldName];
  const entry = relationEntry(descriptor);
  if (!entry?.switchContext?.enabled || !option.switchContext?.code) return;
  const nextCode = option.switchContext.code;
  const currentCode = String(route.query.current_business_category_code || route.query.default_business_category_code || '').trim();
  if (currentCode === nextCode) return;
  const query = normalizeRouteQueryValues(route.query as Record<string, unknown>);
  for (const key of entry.switchContext.defaultClearFields || []) {
    delete query[`default_${key}`];
  }
  query.current_business_category_code = nextCode;
  query.default_business_category_code = nextCode;
  query.current_business_category_label = option.switchContext.label || option.label;
  query.default_business_category_label = option.switchContext.label || option.label;
  query.default_business_category_id = String(option.id);
  query.ctx_source = 'business_category_relation_switch';
  Object.entries(option.switchContext.defaultValues || {}).forEach(([key, value]) => {
    const normalizedKey = String(key || '').trim();
    if (!normalizedKey || value === undefined || value === null) return;
    if (Array.isArray(value) || typeof value === 'object') return;
    query[`default_${normalizedKey}`] = String(value);
  });
  await router.replace({ query });
  await reload();
}

async function createRelationFromSearchDialog() {
  const fieldName = relationSearchDialog.fieldName;
  if (!fieldName) return;
  const descriptor = contract.value?.fields?.[fieldName];
  const label = relationSearchDialog.keyword.trim();
  const mode = relationCreateMode(descriptor);
  const exact = label
    ? relationSearchDialog.options.find((item) => item.label.trim().toLowerCase() === label.toLowerCase())
    : null;
  if (exact && mode !== 'page') {
    selectRelationSearchOption(exact);
    return;
  }
  if (mode === 'quick') {
    if (!label) {
      relationSearchDialog.error = relationSearchDialog.labels.missing_name || '';
      return;
    }
    validationErrors.value = [];
    await quickCreateRelation(fieldName, descriptor, label, { stayInDialog: true });
    if (!validationErrors.value.length) {
      closeRelationSearchDialog();
    } else {
      relationSearchDialog.error = validationErrors.value.join('；');
      validationErrors.value = [];
    }
    return;
  }
  closeRelationSearchDialog();
  await openRelationCreateForm(fieldName, descriptor);
}

async function ensureRelationFieldDescriptors(name: string) {
  const relation = one2manyRelationModel(name);
  if (!relation) return;
  if (relationFieldDescriptors.value[relation]) return;
  try {
    const response = await loadModelContractRaw(relation, {
      viewType: 'form',
      renderProfile: 'edit',
    });
    const fields = response?.data?.fields;
    if (fields && typeof fields === 'object') {
      relationFieldDescriptors.value = {
        ...relationFieldDescriptors.value,
        [relation]: fields as Record<string, FieldDescriptor>,
      };
    }
  } catch {
    // best effort; fallback to char fields
  }
}

async function openRelationCreateForm(fieldName: string, descriptor?: FieldDescriptor) {
  const relation = String((descriptor as Record<string, unknown> | undefined)?.relation || '').trim();
  if (!relation) return;
  const mode = relationCreateMode(descriptor);
  if (mode === 'none') {
    validationErrors.value = [relationUiLabel(descriptor, 'missing_create_entry')];
    return;
  }
  if (mode === 'quick') {
    const currentKeyword = relationKeyword(fieldName).trim();
    if (!currentKeyword) {
      validationErrors.value = [relationUiLabel(descriptor, 'missing_name', relationUiLabel(descriptor, 'quick_create_prompt', '请先输入要新增的名称'))];
      return;
    }
    await quickCreateRelation(fieldName, descriptor, currentKeyword);
    return;
  }
  const entry = relationEntry(descriptor);
  const relationActionId = entry?.actionId || null;
  const menuId = entry?.menuId || 0;
  if (!relationActionId) {
    validationErrors.value = [relationUiLabel(descriptor, 'missing_page_entry')];
    return;
  }
  const defaultQuery = Object.entries(entry?.defaultVals || {}).reduce<Record<string, unknown>>((acc, [key, value]) => {
    if (!key) return acc;
    acc[`default_${key}`] = value;
    return acc;
  }, {});
  Object.entries(entry?.defaultFromFields || {}).forEach(([targetField, sourceFieldRaw]) => {
    const sourceField = String(sourceFieldRaw || '').trim();
    if (!targetField || !sourceField) return;
    const value = normalizeFieldValue(sourceField, formData[sourceField]);
    if (value === undefined || value === null || value === '') return;
    defaultQuery[`default_${targetField}`] = value;
  });
  const nextQuery = pickContractNavQuery(route.query as Record<string, unknown>, {
    action_id: relationActionId,
    menu_id: menuId || undefined,
    view_mode: 'form',
    ...defaultQuery,
  });
  const returnUrl = `${window.location.pathname}${window.location.search}`;
  try {
    await router.push({
      name: 'model-form',
      params: { model: relation, id: 'new' },
      query: {
        ...nextQuery,
        return_url: encodeURIComponent(returnUrl),
        return_field: fieldName,
        return_model: model.value,
        return_action_id: actionId.value || undefined,
        return_menu_id: Number(route.query.menu_id || 0) || undefined,
      },
    });
  } catch (err) {
    if (relation === 'sc.dictionary' && mode === 'page' && entry?.canCreate && Object.keys(entry?.defaultVals || {}).length) {
      const label = String(await actionInputDialog.open({
        title: relationUiLabel(descriptor, 'page_unavailable_prompt'),
        label: relationUiLabel(descriptor, 'create_label_placeholder'),
        placeholder: relationUiLabel(descriptor, 'create_label_placeholder'),
        confirmLabel: relationUiLabel(descriptor, 'quick_create_confirm'),
        cancelLabel: relationUiLabel(descriptor, 'cancel'),
        required: true,
      }) || '').trim();
      if (label) await quickCreateRelation(fieldName, descriptor, label);
      return;
    }
    validationErrors.value = [sanitizeUiErrorMessage(err instanceof Error ? err.message : err, relationUiLabel(descriptor, 'create_page_failed'))];
  }
}

function currentRelationRecordId(fieldName: string) {
  const id = Number(relationIds(fieldName)[0] || 0);
  return Number.isFinite(id) && id > 0 ? Math.trunc(id) : 0;
}

function canOpenRelationRecordForm(fieldName: string, descriptor?: FieldDescriptor) {
  const relation = relationModel(fieldName);
  const entry = relationEntry(descriptor);
  return Boolean(relation && currentRelationRecordId(fieldName) > 0 && entry?.canRead !== false && entry?.canOpen !== false);
}

async function openRelationRecordForm(fieldName: string, descriptor?: FieldDescriptor) {
  const relation = relationModel(fieldName);
  const recordId = currentRelationRecordId(fieldName);
  const entry = relationEntry(descriptor);
  if (!relation || recordId <= 0) return;
  if (entry?.canRead === false) {
    validationErrors.value = [relationUiLabel(descriptor, 'missing_read_entry')];
    return;
  }
  const relationActionId = entry?.actionId || null;
  const menuId = entry?.menuId || 0;
  const nextQuery = pickContractNavQuery(route.query as Record<string, unknown>, {
    action_id: relationActionId || undefined,
    menu_id: menuId || undefined,
    view_mode: 'form',
  });
  const returnUrl = `${window.location.pathname}${window.location.search}`;
  try {
    await router.push({
      name: 'model-form',
      params: { model: relation, id: String(recordId) },
      query: {
        ...nextQuery,
        return_url: encodeURIComponent(returnUrl),
        return_field: fieldName,
        return_model: model.value,
        return_action_id: actionId.value || undefined,
        return_menu_id: Number(route.query.menu_id || 0) || undefined,
      },
    });
  } catch (err) {
    validationErrors.value = [sanitizeUiErrorMessage(err instanceof Error ? err.message : err, relationUiLabel(descriptor, 'open_record_failed'))];
  }
}

async function quickCreateRelation(
  fieldName: string,
  descriptor: FieldDescriptor | undefined,
  label: string,
  options: { stayInDialog?: boolean } = {},
) {
  const relation = String((descriptor as Record<string, unknown> | undefined)?.relation || '').trim();
  if (!relation) return;
  const entry = relationEntry(descriptor);
  try {
    const existing = await fetchRelationOptions(fieldName, label, 20);
    const exact = existing.find((item) => item.label.trim().toLowerCase() === label.trim().toLowerCase());
    if (exact) {
      setMany2oneOption(fieldName, exact);
      return;
    }
    const inline = relationInlineCreate(descriptor);
    const nameField = inline.nameField || 'name';
    const vals: Record<string, unknown> = { ...(entry?.defaultVals || {}), [nameField]: label };
    if (relation === 'sc.dictionary' && typeof vals.type === 'string' && String(vals.type || '').trim()) {
      vals.code = label.toUpperCase().replace(/\\s+/g, '_').slice(0, 60);
    }
    const created = await createContractFormRecord({ model: relation, vals });
    const id = Number(created?.id || 0);
    if (Number.isFinite(id) && id > 0) {
      const option = { id: Math.trunc(id), label };
      setMany2oneOption(fieldName, option);
      if (!options.stayInDialog) await queryRelationOptions(fieldName, label);
    }
  } catch (err) {
    const message = sanitizeUiErrorMessage(err instanceof Error ? err.message : err, relationUiLabel(descriptor, 'quick_create_failed'));
    validationErrors.value = [message];
  }
}

async function loadRelationOptions() {
  const fields = contract.value?.fields || {};
  const visibleRelationFields = new Set(
    layoutNodes.value
      .filter((node) => node.kind === 'field' && isWritableFieldVisible(node.name))
      .map((node) => node.name),
  );
  const entries = Object.entries(fields).filter(([name]) => {
    if (!visibleRelationFields.size) return relationIds(name).length > 0;
    if (visibleRelationFields.has(name)) return true;
    return relationIds(name).length > 0;
  });
  const one2manyNames = entries
    .filter(([, descriptor]) => fieldType(descriptor) === 'one2many')
    .map(([name]) => name);
  await Promise.all(one2manyNames.map((name) => ensureRelationFieldDescriptors(name)));
  const next: Record<string, RelationOption[]> = {};
  await Promise.all(entries.map(async ([name, descriptor]) => {
    if (!descriptor || typeof descriptor !== 'object') return;
    const type = fieldType(descriptor);
    if (!['many2one', 'many2many', 'one2many'].includes(type)) return;
    const relation = String((descriptor as Record<string, unknown>).relation || '').trim();
    if (!relation) return;
    const entry = relationEntry(descriptor as FieldDescriptor);
    if (entry && entry.canRead === false) {
      deniedRelationModels.add(relation);
      next[name] = [];
      return;
    }
    if (deniedRelationModels.has(relation)) {
      next[name] = [];
      return;
    }
    const domain = mergedRelationDomain(name, descriptor as FieldDescriptor);
    try {
      const listed = await listContractFormRecords({
        model: relation,
        fields: relationReadFields(descriptor as FieldDescriptor),
        limit: 80,
        order: relationOrder(descriptor as FieldDescriptor),
        domain,
        silentErrors: true,
      });
      next[name] = relationOptionsFromRecords(listed?.records, descriptor as FieldDescriptor);
    } catch (err) {
      if (err instanceof ApiError) {
        const denied = err.status === 403 || String(err.reasonCode || '').toUpperCase() === 'PERMISSION_DENIED';
        if (denied) deniedRelationModels.add(relation);
      }
      next[name] = [];
    }
  }));
  Object.entries(next).forEach(([fieldName, options]) => {
    mergeRelationOptions(fieldName, options);
  });
}

function toActionId(raw: unknown) {
  return toPositiveInt(raw);
}

function detectMethodName(key: string, payloadMethod: string) {
  return detectObjectMethodFromActionKey(key, payloadMethod);
}

function currentWorkflowContract(): Record<string, unknown> {
  const root = dictOrEmpty(contract.value);
  const storeSnapshot = dictOrEmpty(v2ContractStore.value?.snapshot);
  const storeDirect = dictOrEmpty(storeSnapshot.workflowContract);
  if (Object.keys(storeDirect).length) return storeDirect;
  const storeRuntime = dictOrEmpty(storeSnapshot.runtimeContract);
  const storeNested = dictOrEmpty(storeRuntime.workflowContract);
  if (Object.keys(storeNested).length) return storeNested;
  const direct = root.workflowContract;
  if (direct && typeof direct === 'object' && !Array.isArray(direct)) {
    return direct as Record<string, unknown>;
  }
  const runtime = root.runtimeContract;
  if (runtime && typeof runtime === 'object' && !Array.isArray(runtime)) {
    const nested = (runtime as Record<string, unknown>).workflowContract;
    if (nested && typeof nested === 'object' && !Array.isArray(nested)) {
      return nested as Record<string, unknown>;
    }
  }
  const rawV2 = dictOrEmpty(root.__unified_page_contract_v2);
  const rawDirect = dictOrEmpty(rawV2.workflowContract);
  if (Object.keys(rawDirect).length) return rawDirect;
  const rawRuntime = dictOrEmpty(rawV2.runtimeContract);
  const rawNested = dictOrEmpty(rawRuntime.workflowContract);
  if (Object.keys(rawNested).length) return rawNested;
  return {};
}

function workflowContractActionRows(): Array<Record<string, unknown>> {
  if (!recordId.value) return [];
  return normalizeWorkflowActionRows(currentWorkflowContract(), model.value);
}

function blockingWorkflowEvidenceMessage() {
  const row = workflowEvidenceGateRows.value.find((item) => item.blocking);
  return row?.message || '';
}

function applyWorkflowContractToAction(action: ContractAction): ContractAction {
  const workflow = currentWorkflowContract();
  if (!recordId.value || !action.methodName || !isWorkflowTransitionMethod(workflow, action.methodName)) return action;
  const workflowRow = workflowActionRowForMethod(workflow, action.methodName);
  const blockingMessage = blockingWorkflowEvidenceMessage();
  if (!workflowRow) {
    return {
      ...action,
      enabled: false,
      hint: blockingMessage || '当前流程状态不允许执行该操作',
    };
  }
  if (workflowRow.enabled === false) {
    return {
      ...action,
      enabled: false,
      hint: String(workflowRow.blocked_message || workflowRow.message || blockingMessage || workflowRow.reason_code || workflowRow.reasonCode || '').trim(),
    };
  }
  return action;
}

function hasWorkflowContractActions() {
  const workflow = currentWorkflowContract();
  return Array.isArray(workflow.availableActions);
}

function shouldShowWorkflowNativeAction(methodName: string) {
  const method = String(methodName || '').trim();
  const workflow = currentWorkflowContract();
  if (!recordId.value || !method || !hasWorkflowContractActions() || !isWorkflowTransitionMethod(workflow, method)) return true;
  return Boolean(workflowActionRowForMethod(workflow, method));
}

const workflowEvidenceGateRows = computed(() => {
  return normalizeWorkflowEvidenceGateRows(currentWorkflowContract());
});

const contractActions = computed<ContractAction[]>(() => {
  const mapSceneReadyAction = (row: Record<string, unknown>): ContractAction | null => {
    const protocol = normalizeSceneActionProtocol(row);
    const key = String(row.key || '').trim();
    if (!key) return null;
    const target = parseMaybeJsonRecord(row.target);
    const intent = String(row.intent || '').trim().toLowerCase();
    const tier = String(row.tier || '').trim().toLowerCase();
    const placement = String(row.placement || 'header').trim().toLowerCase();
    const actionId = toActionId(target.action_id) ?? toActionId(target.ref);
    const hasOpenTarget = Boolean(actionId || String(target.url || '').trim() || String(target.route || '').trim());
    const kind = hasOpenTarget || intent === 'ui.contract' ? 'open' : 'object';
    const semantic = tier === 'primary'
      ? 'primary_action'
      : tier === 'secondary'
        ? 'secondary_action'
        : '';
    return {
      key,
      label: String(row.label || key),
      kind,
      level: placement,
      selection: 'none',
      actionId,
      methodName: detectMethodName(key, String(target.method || '').trim()),
      targetModel: String(target.model || model.value || '').trim(),
      context: parseMaybeJsonRecord(target.context_raw),
      domainRaw: String(target.domain_raw || '').trim(),
      target: String(target.target || '').trim(),
      url: String(target.url || target.route || '').trim(),
      enabled: true,
      hint: '',
      intent,
      semantic,
      sourceWidgetId: String(row.sourceWidgetId || row.source_widget_id || '').trim(),
      clientMode: String(target.mode || target.client_mode || row.clientMode || row.client_mode || '').trim(),
      visibleProfiles: ['create', 'edit', 'readonly'],
      requiredParams: normalizeRequiredParams(row.required_params),
      requiresReason: row.requires_reason === true,
      actionSafety: normalizeActionSafety(row.action_safety),
      mutation: protocol?.mutation,
      refreshPolicy: protocol?.refresh_policy,
    };
  };

  const sceneReadyActions = useSceneFormAugmentations.value && Array.isArray(sceneReadyFormSurface.value.actions)
    ? sceneReadyFormSurface.value.actions as Array<Record<string, unknown>>
    : [];
  const storeButtonStatus = collectContractV2ButtonStatusById(v2ContractStore.value);
  const v2ButtonStatus = Object.keys(storeButtonStatus).length
    ? storeButtonStatus
    : collectUnifiedPageContractV2ButtonStatus(contract.value);
  const merged: Array<Record<string, unknown>> = [];
  const workflowRows = workflowContractActionRows();
  const workflowMethods = new Set<string>();
  workflowRows.forEach((row) => {
    const method = String(parseMaybeJsonRecord(row.payload).method || '').trim();
    if (method) workflowMethods.add(method);
    workflowActionMethodAliases(String(row.key || '').trim()).forEach((alias) => workflowMethods.add(alias));
  });
  if (workflowRows.length) {
    merged.push(...workflowRows);
  }
  const nativeFormContract = contract.value?.views?.form as Record<string, unknown> | undefined;
  if (Array.isArray(nativeFormContract?.header_buttons)) {
    merged.push(...(nativeFormContract.header_buttons as Array<Record<string, unknown>>));
  }
  if (Array.isArray(nativeFormContract?.button_box)) {
    merged.push(...(nativeFormContract.button_box as Array<Record<string, unknown>>));
  }
  if (Array.isArray(nativeFormContract?.business_actions)) {
    merged.push(...(nativeFormContract.business_actions as Array<Record<string, unknown>>));
  }
  if (Array.isArray(contract.value?.buttons)) merged.push(...(contract.value?.buttons as Array<Record<string, unknown>>));
  if (Array.isArray(contract.value?.toolbar?.header)) merged.push(...(contract.value?.toolbar?.header as Array<Record<string, unknown>>));
  if (Array.isArray(contract.value?.toolbar?.sidebar)) merged.push(...(contract.value?.toolbar?.sidebar as Array<Record<string, unknown>>));
  if (Array.isArray(contract.value?.toolbar?.footer)) merged.push(...(contract.value?.toolbar?.footer as Array<Record<string, unknown>>));
  const v2ActionRules = resolveUnifiedPageContractV2(contract.value)?.actionContract;
  const v2ActionRuleList = parseMaybeJsonRecord(v2ActionRules).actionRuleList;
  if (Array.isArray(v2ActionRuleList)) {
    v2ActionRuleList.forEach((raw) => {
      if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return;
      const row = raw as Record<string, unknown>;
      const sourceWidgetId = String(row.sourceWidgetId || row.source_widget_id || '').trim();
      const targetScope = String(row.targetScope || row.target_scope || '').trim().toLowerCase();
      const triggerType = String(row.triggerType || row.trigger_type || '').trim();
      if (triggerType && triggerType !== 'click') return;
      const key = String(row.actionKey || row.key || row.actionId || '').trim();
      if (!key) return;
      const target = parseMaybeJsonRecord(row.target);
      const button = parseMaybeJsonRecord(row.button);
      const clientMode = String(target.mode || target.client_mode || '').trim();
      const intent = String(row.intent || '').trim();
      const buttonType = String(button.type || button.buttonType || '').trim();
      const buttonName = String(button.name || button.method || '').trim();
      const isRootObjectAction = sourceWidgetId === 'page.root' && Boolean(buttonName);
      if (sourceWidgetId !== 'page.header' && targetScope !== 'footer' && !isRootObjectAction) return;
      const actionKind = buttonType === 'server' || buttonType === 'server_action'
        ? 'server'
        : buttonName
          ? 'object'
          : (clientMode ? 'client' : 'open');
      merged.push({
        key,
        label: String(row.label || key).trim() || key,
        kind: actionKind,
        intent,
        level: targetScope === 'footer' ? 'footer' : 'header',
        selection: 'none',
        sourceWidgetId,
        target,
        target_model: String(target.model || '').trim(),
        payload: {
          method: buttonName,
          type: buttonType,
          action_id: target.action_id,
          ref: target.ref,
          url: target.url || target.route,
          target: target.target,
          mode: clientMode,
          client_mode: clientMode,
          domain_raw: target.domain_raw,
          context_raw: target.context_raw,
        },
        visible_profiles: ['create', 'edit', 'readonly'],
      });
    });
  }
  if (sceneReadyActions.length) {
    merged.push(...sceneReadyActions);
  }

  const dedup = new Set<string>();
  const out: ContractAction[] = [];
  for (const row of merged) {
    if (sceneReadyActions.length && !String(row.key || '').trim()) {
      const mapped = mapSceneReadyAction(row);
      if (!mapped || dedup.has(mapped.key)) continue;
      const status = resolveV2ButtonStatus(mapped.key, v2ButtonStatus);
      if (status?.visible === false) continue;
      if (status?.disabled === true) {
        mapped.enabled = false;
        mapped.hint = status.reasonCode || mapped.hint || 'disabled_by_status_contract';
      }
      dedup.add(mapped.key);
      out.push(mapped);
      continue;
    }
    if (sceneReadyActions.includes(row)) {
      const mapped = mapSceneReadyAction(row);
      if (!mapped || dedup.has(mapped.key)) continue;
      const status = resolveV2ButtonStatus(mapped.key, v2ButtonStatus);
      if (status?.visible === false) continue;
      if (status?.disabled === true) {
        mapped.enabled = false;
        mapped.hint = status.reasonCode || mapped.hint || 'disabled_by_status_contract';
      }
      dedup.add(mapped.key);
      out.push(mapped);
      continue;
    }
    const rowName = String(row.name || '').trim();
    const rowLabel = normalizeActionLabel(row.label);
    const keyBase = String(row.key || rowName || rowLabel || '').trim();
    const key = dedup.has(keyBase) && rowLabel ? `${keyBase}:${rowLabel}` : keyBase;
    if (!key || dedup.has(key)) continue;
    dedup.add(key);
    const payload = parseMaybeJsonRecord(row.payload);
    const kind = normalizeActionKind(row.kind);
    const protocol = normalizeSceneActionProtocol(row);
    const targetRaw = parseMaybeJsonRecord(row.target);
    const rowIntent = String(row.intent || '').trim();
    const effectiveKind = protocol?.mutation ? 'mutation' : kind;
    const level = String(row.level || 'body').trim().toLowerCase();
    const actionId = toActionId(payload.action_id) ?? toActionId(payload.ref) ?? toActionId(row.actionId) ?? toActionId(row.action_id);
    const methodName = detectMethodName(key, String(payload.method || '').trim());
    const isWorkflowContractAction = row.workflow_contract_action === true;
    if (!isWorkflowContractAction && methodName && workflowMethods.has(methodName)) continue;
    if (isTierValidationActionHidden(methodName)) continue;
    const targetModel = String(row.target_model || row.model || model.value || '').trim();
    const context = parseMaybeJsonRecord(payload.context_raw);
    const domainRaw = String(payload.domain_raw || '').trim();
    const target = String(payload.target || '').trim();
    const selectionRaw = String(row.selection || 'none').trim().toLowerCase();
    const selection = selectionRaw === 'single' || selectionRaw === 'multi' ? selectionRaw : 'none';
    const visibleProfiles = (
      Array.isArray(row.visible_profiles) ? row.visible_profiles : ['create', 'edit']
    )
      .map((item) => String(item || '').trim().toLowerCase())
      .filter((item): item is 'create' | 'edit' | 'readonly' => item === 'create' || item === 'edit' || item === 'readonly');
    const requiredParams = normalizeRequiredParams(row.required_params);
    const policy = evaluateActionPolicy(contract.value, key, policyContext.value);
    if (!policy.visible) continue;
    if (!evaluateNativeActionVisibility(row)) continue;
    const status = resolveV2ButtonStatus(key, v2ButtonStatus);
    if (status?.visible === false) continue;
    const contractAllowed = typeof row.allowed === 'boolean' ? Boolean(row.allowed) : true;
    const needRecord = effectiveKind === 'object' || effectiveKind === 'server' || effectiveKind === 'mutation' || level === 'row' || level === 'smart';
    const blockedMessage = String(row.blocked_message || row.reason || row.reason_code || '').trim();
    const warningMessage = String(row.warning_message || '').trim();
    const enabled = contractAllowed && policy.enabled && (!needRecord || Boolean(recordId.value)) && status?.disabled !== true;
    out.push({
      key,
      label: normalizeActionLabel(row.label, key),
      kind: effectiveKind,
      level,
      selection,
      actionId,
      methodName,
      targetModel,
      context,
      domainRaw,
      target,
      url: String(payload.url || row.url || '').trim(),
      enabled,
      hint: status?.disabled === true
        ? status.reasonCode || 'disabled_by_status_contract'
        : (needRecord && !recordId.value ? 'requires record id' : (contractAllowed ? (warningMessage || policy.reason) : blockedMessage)),
      intent: rowIntent,
      semantic: policy.semantic,
      sourceWidgetId: String(row.sourceWidgetId || row.source_widget_id || '').trim(),
      clientMode: String(targetRaw.mode || targetRaw.client_mode || row.clientMode || row.client_mode || '').trim(),
      visibleProfiles,
      requiredParams,
      requiresReason: row.requires_reason === true || requiredParams.includes('reason'),
      actionSafety: normalizeActionSafety(row.action_safety),
      mutation: protocol?.mutation,
      refreshPolicy: protocol?.refresh_policy,
    });
  }
  if (
    model.value === 'payment.request'
    && recordId.value
    && String(formData.type || 'pay').trim() === 'pay'
    && !out.some((item) => item.methodName === 'action_create_payment_execution')
  ) {
    out.push({
      key: 'action_create_payment_execution',
      label: '生成付款登记',
      kind: 'object',
      level: 'header',
      selection: 'none',
      actionId: null,
      methodName: 'action_create_payment_execution',
      targetModel: 'payment.request',
      context: {},
      domainRaw: '',
      target: '',
      url: '',
      enabled: true,
      hint: '',
      intent: '',
      semantic: 'secondary_action',
      sourceWidgetId: '',
      clientMode: '',
      visibleProfiles: ['edit', 'readonly'],
      requiredParams: [],
      requiresReason: false,
    });
  }
  return out.sort((a, b) => {
    const levelDelta = a.level.localeCompare(b.level);
    if (levelDelta !== 0) return levelDelta;
    return a.label.localeCompare(b.label, 'zh-CN');
  }).filter((item) => {
    const profiles = Array.isArray(item.visibleProfiles) ? item.visibleProfiles : [];
    if (profiles.length && !profiles.includes(renderProfile.value)) return false;
    if (item.selection !== 'none') return false;
    return item.level !== 'toolbar';
  });
});

const headerActions = computed(() => contractActions.value.filter((item) => item.level === 'header' || item.level === 'toolbar'));
const bodyActions = computed(() => contractActions.value.filter((item) => item.level !== 'header' && item.level !== 'toolbar'));

const contractFieldLabels = computed<Record<string, string>>(() => {
  const labels: Record<string, string> = {};
  const snapshot = dictOrEmpty(v2ContractStore.value?.snapshot);
  const source = Object.keys(snapshot).length ? snapshot : contract.value;
  const businessProfile = resolveUnifiedPageContractV2BusinessOperationProfile(source);
  Object.entries(dictOrEmpty(businessProfile.field_labels)).forEach(([name, value]) => {
    const label = String(value || '').trim();
    if (name && label) labels[name] = label;
  });
  mergeFieldLabelsFromSource(resolveUnifiedPageContractV2FormStructureContract(source), labels);
  mergeFieldLabelsFromSource(snapshot.formStructureContract, labels);
  mergeFieldLabelsFromSource((contract.value as Record<string, unknown> | null | undefined)?.formStructureContract, labels);
  return labels;
});

function contractFieldLabel(name: string) {
  return contractFieldLabels.value[String(name || '').trim()] || '';
}

const runtimeCollaborationContract = computed(() => {
  return resolveRuntimeCollaborationContract(
    v2ContractStore.value?.snapshot?.runtimeContract,
    (contract.value as Record<string, unknown> | null | undefined)?.runtimeContract,
  );
});

const nativeChatterContract = computed(() => {
  return resolveNativeChatterContract(contract.value?.views?.form, runtimeCollaborationContract.value);
});

const nativeAttachmentContract = computed(() => {
  return resolveNativeAttachmentContract(contract.value?.views?.form, runtimeCollaborationContract.value);
});

const nativeChatterActions = computed<NativeChatterAction[]>(() => {
  return nativeChatterActionsFromContract(nativeChatterContract.value, {
    recordId: recordId.value,
    model: model.value,
  });
});

const nativeChatterTitle = computed(() => {
  const chatter = nativeChatterContract.value;
  return String(chatter?.label || '').trim();
});

const nativeCollaborationTitle = computed(() => nativeChatterTitle.value || '协作日志');
const nativeCollaborationUnavailableMessage = computed(() => nativeCollaborationUnavailableMessageFromState({
  recordId: recordId.value,
  model: model.value,
  renderProfile: renderProfile.value,
  hasAttachments: Boolean(nativeAttachments.value),
}));

const activeChatterSubmitLabel = computed(() => activeChatterSubmitLabelFromMode(activeChatterMode.value, activeChatterLabel.value));

const activeChatterPostingLabel = computed(() => activeChatterPostingLabelFromMode(activeChatterMode.value));

const activeChatterPlaceholder = computed(() => activeChatterPlaceholderFromMode(activeChatterMode.value));

const activeChatterIsActivity = computed(() => activeChatterMode.value === 'activity');

const activeActivityAction = computed(() => (
  nativeChatterActions.value.find((item) => item.mode === 'activity' && item.label === activeChatterLabel.value)
  || nativeChatterActions.value.find((item) => item.mode === 'activity')
  || null
));

function activityFieldLabel(name: string, fallback: string) {
  return nativeActivityFieldLabel(activeActivityAction.value, name, fallback);
}

const activitySummaryLabel = computed(() => activityFieldLabel('summary', '摘要'));
const activityDeadlineLabel = computed(() => activityFieldLabel('date_deadline', '截止日期'));
const activityNoteLabel = computed(() => activityFieldLabel('note', '备注'));
const activitySummaryPlaceholder = computed(() => `填写需要跟进的计划事项，例如：补充资料、确认付款、复核合同`);
const activityNotePlaceholder = computed(() => '补充计划背景、办理要求或注意事项');
const activityAssigneeOptions = computed(() => collaborationUserOptions.value);
const activityAssigneeLabel = computed(() => activityFieldLabel('user_id', '指派给'));

const isNativeChatterSubmitDisabled = computed(() => {
  if (chatterPosting.value) return true;
  if (activeChatterMode.value === 'activity') return !activitySummary.value.trim();
  return !chatterDraft.value.trim();
});

const nativeAttachments = computed(() => {
  return nativeAttachmentContractOrNull(nativeAttachmentContract.value);
});

const nativeAttachmentLabels = computed<Record<string, string>>(() => {
  return nativeAttachmentLabelsFromContract(nativeAttachments.value);
});

function resolveNativeAttachmentLabel(key: string, fallback: string) {
  return nativeAttachmentLabel(nativeAttachmentLabels.value, key, fallback);
}

const nativeAttachmentUploadLabel = computed(() => resolveNativeAttachmentLabel('upload', '上传附件'));
const nativeAttachmentUploadingLabel = computed(() => resolveNativeAttachmentLabel('uploading', '上传中...'));
const nativeAttachmentViewLabel = computed(() => resolveNativeAttachmentLabel('view', '查看'));
const nativeAttachmentMaxBytes = computed(() => nativeAttachmentMaxBytesFromContract(nativeAttachments.value));

const nativeCollaborationPanelProps = computed<NativeCollaborationPanelProps>(() => ({
  actions: nativeChatterActions.value,
  activityAssigneeId: activityAssigneeId.value,
  activityAssigneeLabel: activityAssigneeLabel.value,
  activityAssigneeOptions: activityAssigneeOptions.value,
  activityDeadline: activityDeadline.value,
  activityDeadlineLabel: activityDeadlineLabel.value,
  activityNote: activityNote.value,
  activityNoteLabel: activityNoteLabel.value,
  activityNotePlaceholder: activityNotePlaceholder.value,
  activitySummary: activitySummary.value,
  activitySummaryLabel: activitySummaryLabel.value,
  activitySummaryPlaceholder: activitySummaryPlaceholder.value,
  activeIsActivity: activeChatterIsActivity.value,
  activeMode: activeChatterMode.value,
  activePlaceholder: activeChatterPlaceholder.value,
  activePostingLabel: activeChatterPostingLabel.value,
  activeSubmitLabel: activeChatterSubmitLabel.value,
  activityUpdatingIds: activityUpdatingIds.value,
  attachmentError: attachmentError.value,
  attachmentUploadLabel: nativeAttachmentUploadLabel.value,
  attachmentUploading: attachmentUploading.value,
  attachmentUploadingLabel: nativeAttachmentUploadingLabel.value,
  attachmentViewLabel: nativeAttachmentViewLabel.value,
  busy: busy.value,
  chatterDraft: chatterDraft.value,
  chatterError: chatterError.value,
  collaborationUserChoices: collaborationUserChoices.value,
  collaborationUserQuery: collaborationUserQuery.value,
  hasAttachments: Boolean(nativeAttachments.value),
  pendingAttachments: pendingNativeAttachments.value,
  posting: chatterPosting.value,
  selectedMentionUsers: selectedMentionUsers.value,
  submitDisabled: isNativeChatterSubmitDisabled.value,
  timeline: chatterTimeline.value,
  title: nativeCollaborationTitle.value,
  unavailableMessage: nativeCollaborationUnavailableMessage.value,
  usersLoading: collaborationUsersLoading.value,
}));

const nativeCollaborationPanelListeners: NativeCollaborationPanelListeners = {
  'attachment-selected': onNativeAttachmentSelected,
  'close-composer': closeNativeChatterComposer,
  'load-users': loadCollaborationUsers,
  'open-action': openNativeChatterAction,
  'open-attachment': openNativeAttachment,
  'remove-mention-user': removeMentionUser,
  'remove-pending-attachment': removePendingNativeAttachment,
  'select-activity-assignee': (id: number) => {
    activityAssigneeId.value = id;
  },
  'select-mention-user': selectMentionUser,
  'send-chatter': sendNativeChatter,
  'update-activity': updateNativeActivity,
  'update:activityDeadline': (value: string) => {
    activityDeadline.value = value;
  },
  'update:activityNote': (value: string) => {
    activityNote.value = value;
  },
  'update:activitySummary': (value: string) => {
    activitySummary.value = value;
  },
  'update:chatterDraft': (value: string) => {
    chatterDraft.value = value;
  },
  'update:collaborationUserQuery': (value: string) => {
    collaborationUserQuery.value = value;
  },
};

const hasNativeChatterNode = computed(() => nativeLayoutContainsType(nativeFormLayoutNodes.value, 'chatter'));

function nativeLayoutContainsType(nodes: NativeFormLayoutNode[], type: string): boolean {
  return layoutContainsType(nodes as Array<Record<string, unknown>>, type);
}

function contractActionFromNativeRow(row: Record<string, unknown>): ContractAction | null {
  const nativeAction = row.action && typeof row.action === 'object' && !Array.isArray(row.action)
    ? row.action as Record<string, unknown>
    : {};
  const payload = parseMaybeJsonRecord(nativeAction.payload || row.payload);
  const rowName = String(nativeAction.name || row.name || payload.method || payload.ref || '').trim();
  const rowLabel = String(nativeAction.label || row.label || '').trim();
  const key = String(nativeAction.key || row.key || rowName || rowLabel || '').trim();
  if (!key) return null;
  const kind = normalizeActionKind(
    nativeAction.kind || row.kind || row.buttonType || payload.type || row.type || (rowName ? 'object' : ''),
  );
  const level = String(nativeAction.level || row.level || 'body').trim().toLowerCase();
  const actionId = toActionId(payload.action_id) ?? toActionId(payload.ref) ?? toActionId(row.action_id) ?? toActionId(row.ref);
  const methodName = detectMethodName(
    key,
    String(payload.method || row.method || (kind === 'object' || kind === 'server' ? rowName : '') || '').trim(),
  );
  if (!shouldShowWorkflowNativeAction(methodName)) return null;
  const needRecord = kind === 'object' || kind === 'server' || level === 'row' || level === 'smart';
  return applyWorkflowContractToAction({
    key,
    label: rowLabel || key,
    kind,
    level,
    selection: 'none',
    actionId,
    methodName,
    targetModel: String(row.target_model || row.model || payload.model || model.value || '').trim(),
    context: parseMaybeJsonRecord(payload.context_raw || row.context),
    domainRaw: String(payload.domain_raw || row.domain_raw || '').trim(),
    target: String(payload.target || row.target || '').trim(),
    url: String(payload.url || row.url || '').trim(),
    enabled: !needRecord || Boolean(recordId.value),
    hint: needRecord && !recordId.value ? 'requires record id' : '',
    intent: String(nativeAction.intent || row.intent || '').trim(),
    semantic: '',
    sourceWidgetId: String(row.sourceWidgetId || row.source_widget_id || '').trim(),
    clientMode: '',
    visibleProfiles: ['create', 'edit', 'readonly'],
    requiredParams: normalizeRequiredParams(nativeAction.required_params || row.required_params),
    requiresReason: nativeAction.requires_reason === true || row.requires_reason === true,
    actionSafety: normalizeActionSafety(nativeAction.action_safety || row.action_safety),
  });
}

function resolveNativeActionState(row: Record<string, unknown>) {
  const action = contractActionFromNativeRow(row);
  if (!action) return {};
  return {
    disabled: busy.value || !action.enabled,
    title: action.hint || '',
  };
}

function isUnifiedSubmitMethod(methodName: string) {
  const method = String(methodName || '').trim();
  return method === 'action_submit'
    || method === 'action_submit_progress'
    || method === 'action_confirm'
    || method === 'button_confirm';
}

function isUnifiedSubmitAction(action: ContractAction | null | undefined) {
  return Boolean(action && isUnifiedSubmitMethod(action.methodName));
}

function nativeHeaderSubmitActionForCreate(): ContractAction | null {
  const nativeFormContract = contract.value?.views?.form as Record<string, unknown> | undefined;
  const rows = Array.isArray(nativeFormContract?.header_buttons)
    ? nativeFormContract.header_buttons as Array<Record<string, unknown>>
    : [];
  for (const row of rows) {
    const action = contractActionFromNativeRow(row);
    if (!isUnifiedSubmitAction(action)) continue;
    return {
      ...action,
      enabled: true,
      hint: '',
    };
  }
  return null;
}

const primarySubmitAction = computed<ContractAction | null>(() => {
  if (isProjectIntakeCreateMode.value) return null;
  if (!model.value) return null;
  if (!recordId.value) return nativeHeaderSubmitActionForCreate();
  const visibleAction = headerActions.value.find((action) => isUnifiedSubmitAction(action) && action.enabled);
  return visibleAction || null;
});

const primaryCreateFooterAction = computed<ContractAction | null>(() => {
  if (isProjectIntakeCreateMode.value) return null;
  if (!model.value || recordId.value) return null;
  if (primarySubmitAction.value) return null;
  const v2 = resolveUnifiedPageContractV2(contract.value);
  return resolvePrimaryCreateFooterAction({
    actions: contractActions.value,
    fallbackRules: parseMaybeJsonRecord(v2?.actionContract).actionRuleList,
    targetModel: model.value,
  });
});

function actionResponseNavQuery(result: object | null | undefined, extra?: Record<string, unknown>) {
  return actionResponseNavQueryFromResult(route.query as Record<string, unknown>, result, extra);
}

function actionResponseRouteTarget(target: unknown, result: object | null | undefined, extra?: Record<string, unknown>) {
  return actionResponseRouteTargetFromResult(route.query as Record<string, unknown>, target, result, extra);
}

async function runNativeLayoutAction(row: Record<string, unknown>) {
  const action = contractActionFromNativeRow(row);
  if (!action) return;
  if ((action.kind === 'object' || action.kind === 'server') && action.methodName && recordId.value) {
    if (!action.enabled || !await confirmActionSafety(action)) return;
    if (!await ensureSavedBeforeRecordAction()) return;
    busyKind.value = 'action';
    try {
      const response = await executeButton({
        model: action.targetModel || model.value,
        res_id: recordId.value,
        button: { name: action.methodName, type: action.kind === 'server' ? 'server' : 'object' },
        context: action.context,
        meta: {
          menu_id: Number(route.query.menu_id || 0) || undefined,
          action_id: actionId.value || undefined,
        },
      });
      const result = response?.result;
      if (result?.entry_target) {
        await router.push(actionResponseRouteTarget(buildEntryTargetRouteTarget(result.entry_target, {
          query: actionResponseNavQuery(result),
          actionId: result.action_id,
        }), result) as never);
        return;
      }
      const nextActionId = toPositiveInt(result?.action_id);
      if (nextActionId) {
        await router.push({
          name: 'action',
          params: { actionId: String(nextActionId) },
          query: actionResponseNavQuery(result, { action_id: nextActionId }),
        });
        return;
      }
      await reload();
      return;
    } catch (err) {
      errorMessage.value = err instanceof Error ? err.message : '操作执行失败';
      status.value = 'error';
      return;
    } finally {
      busyKind.value = null;
    }
  }
  await runAction(action);
}

const semanticFieldGroups = computed<Record<string, SemanticFieldGroup>>(() => {
  const snapshot = dictOrEmpty(v2ContractStore.value?.snapshot);
  const source = Object.keys(snapshot).length ? snapshot : contract.value;
  const raw = resolveUnifiedPageContractV2FieldGroups(source);
  const profile = ((contract.value?.views?.form as Record<string, unknown> | undefined)?.form_profile
    || (contract.value as Record<string, unknown> | undefined)?.form_profile) as Record<string, unknown> | undefined;
  return normalizeSemanticFieldGroups(raw, profile);
});

const contractFieldSemantics = computed<Record<string, FieldSemanticMeta>>(() => {
  return normalizeContractFieldSemantics((contract.value as Record<string, unknown> | null)?.field_semantics);
});

function fieldSemanticMeta(name: string) {
  return resolveFieldSemanticMeta(name, contractFieldSemantics.value, contract.value?.fields?.[name]);
}

const coreFieldNames = computed<string[]>(() => {
  return semanticFieldNamesBySurfaceRole(contract.value?.fields, contractFieldSemantics.value, semanticFieldGroups.value, 'core');
});
const advancedFieldNames = computed<string[]>(() => {
  return semanticFieldNamesBySurfaceRole(contract.value?.fields, contractFieldSemantics.value, semanticFieldGroups.value, 'advanced');
});
const hasAdvancedFields = computed(() => advancedFieldNames.value.length > 0);
const policyRequiredFields = computed(() => collectPrimaryActionRequiredFields(contract.value?.action_policies));
const sceneReadySceneKey = computed(() => String(
  route.query.scene_key
  || route.params.sceneKey
  || findActionMeta(session.menuTree, actionId.value)?.scene_key
  || findActionMeta(session.menuTree, actionId.value)?.sceneKey
  || session.currentAction?.scene_key
  || session.currentAction?.sceneKey
  || '',
).trim());
const sceneReadyHydrateRequested = ref(false);
const useSceneFormAugmentations = computed(() => {
  if (isProjectIntakeCreateMode.value) return true;
  return Boolean(sceneReadySceneKey.value);
});
const sceneReadyEntry = computed<Record<string, unknown> | null>(() => {
  if (!useSceneFormAugmentations.value) return null;
  const key = sceneReadySceneKey.value;
  return key ? findSceneReadyEntry(session.sceneReadyContractV1, key) : null;
});
const strictContractMode = computed(() => isCoreSceneStrictMode(sceneReadySceneKey.value, sceneReadyEntry.value));
const strictContractGuard = computed<Record<string, unknown>>(() => strictContractGuardFromSceneReadyEntry(sceneReadyEntry.value));
const strictContractMissingSummary = computed(() => strictContractMissingSummaryFromGuard(strictContractMode.value, strictContractGuard.value));
const strictContractDefaultsSummary = computed(() => strictContractDefaultsSummaryFromGuard(strictContractMode.value, strictContractGuard.value));
const sceneValidationRequiredFields = computed<string[]>(() => {
  if (!useSceneFormAugmentations.value) return [];
  return resolveFormSceneReady(sceneReadyEntry.value).requiredFields;
});
const sceneReadyFormSurface = computed(() => {
  if (!useSceneFormAugmentations.value) return resolveFormSceneReady(null);
  return resolveFormSceneReady(sceneReadyEntry.value);
});
watch(
  () => [sceneReadySceneKey.value, sceneReadyFormSurface.value.sceneBlocks.length],
  async ([sceneKey, blockCount]) => {
    if (!sceneKey || Number(blockCount || 0) > 0 || sceneReadyHydrateRequested.value) return;
    sceneReadyHydrateRequested.value = true;
    try {
      const result = await intentRequest<Record<string, unknown>>({
        intent: 'system.init',
        params: {
          scene: 'web',
          with_preload: false,
          scene_ready_mode: 'full',
          with: ['workspace_home'],
          ...(config.startupRootXmlid ? { root_xmlid: config.startupRootXmlid } : {}),
          scene_key: sceneKey,
        },
        meta: { startup_chain_bypass: true },
      });
      const contract = result.scene_ready_contract_v1;
      if (contract && typeof contract === 'object' && Array.isArray((contract as Record<string, unknown>).scenes)) {
        session.sceneReadyContractV1 = contract as never;
      }
    } catch (err) {
      void err;
    }
  },
  { immediate: true },
);
const validationRequiredFields = computed(() => {
  const out = new Set<string>();
  const rules = Array.isArray(contract.value?.validation_rules) ? contract.value.validation_rules : [];
  rules.forEach((rule) => {
    if (!rule || typeof rule !== 'object') return;
    const item = rule as Record<string, unknown>;
    if (String(item.code || '').trim().toUpperCase() !== 'REQUIRED') return;
    const field = String(item.field || '').trim();
    if (!field) return;
    const profiles = Array.isArray(item.when_profiles)
      ? item.when_profiles.map((p) => String(p || '').trim().toLowerCase())
      : [];
    if (profiles.length && !profiles.includes(renderProfile.value)) return;
    out.add(field);
  });
  sceneValidationRequiredFields.value.forEach((field) => {
    out.add(field);
  });
  return out;
});
const sceneValidationRequiredErrorPrefix = sceneValidationErrorPrefix(ErrorCodes.SCENE_VALIDATION_REQUIRED);
const sceneValidationPanel = computed(() => {
  const sceneKey = String(route.query.scene_key || route.params.sceneKey || '').trim();
  const modelName = String(model.value || '').trim();
  return buildSceneValidationPanel({
    enabled: useSceneFormAugmentations.value,
    validationErrors: validationErrors.value,
    errorCode: ErrorCodes.SCENE_VALIDATION_REQUIRED,
    suggestedAction: resolveSceneValidationSuggestedAction({
      modelName,
      recordId: recordId.value,
      actionId: actionId.value,
      sceneKey,
      roleCode: runtimeRoleCode.value,
    }),
  });
});
const nonSceneValidationErrors = computed(() => (
  validationErrors.value.filter((item) => !String(item || '').trim().startsWith(sceneValidationRequiredErrorPrefix))
));
const contractVisibleFields = computed<string[]>(() => {
  const snapshot = dictOrEmpty(v2ContractStore.value?.snapshot);
  const source = Object.keys(snapshot).length ? snapshot : contract.value;
  return resolveUnifiedPageContractV2VisibleFields(source);
});

const fieldModifierMap = computed<Record<string, Record<string, unknown>>>(() => {
  const formView = (contract.value?.views?.form || {}) as { field_modifiers?: Record<string, Record<string, unknown>> };
  const out: Record<string, Record<string, unknown>> = { ...(formView.field_modifiers || {}) };
  const fromStore = collectContractV2FieldStatusByCode(v2ContractStore.value);
  const v2FieldStatus = Object.keys(fromStore).length ? fromStore : collectUnifiedPageContractV2FieldStatus(contract.value);
  Object.entries(v2FieldStatus).forEach(([name, status]) => {
    out[name] = {
      ...(out[name] || {}),
      ...(status.visible === false ? { invisible: true } : {}),
      ...(status.readonly === true || status.disabled === true ? { readonly: true } : {}),
      ...(status.required === true ? { required: true } : {}),
    };
  });
  return out;
});
const runtimeFieldStates = computed(() => {
  const storeFieldNames = Array.from(v2ContractStore.value?.widgetsByFieldCode.keys() || []);
  const v2FieldNames = storeFieldNames.length
    ? storeFieldNames
    : collectUnifiedPageContractV2FieldWidgets(contract.value).map((widget) => widget.fieldCode).filter(Boolean);
  const names = Array.from(new Set([...Object.keys(contract.value?.fields || {}), ...v2FieldNames]));
  return buildRuntimeFieldStates({
    fieldNames: names,
    fieldModifiers: fieldModifierMap.value,
    modifierPatch: onchangeModifiersPatch.value,
    values: formData as Record<string, unknown>,
  });
});

function runtimeState(name: string) {
  return runtimeFieldStates.value[name] || { invisible: false, readonly: false, required: false };
}

function isFieldVisible(name: string) {
  if (isProjectQuickIntakeMode.value) {
    return ['name', 'manager_id', 'owner_id'].includes(String(name || '').trim());
  }
  const descriptor = contract.value?.fields?.[String(name || '').trim()];
  if (isCreateWorkflowStateField(name, String(contractFieldLabel(name) || descriptor?.string || ''), !recordId.value)) return false;
  const statusField = nativeStatusbar.value.field;
  if (statusField && String(name || '').trim() === statusField) return false;
  const semantic = fieldSemanticMeta(name);
  if ((semantic.technical || semantic.semantic_type === 'technical') && !showHud.value) return false;
  if (semantic.surface_role === 'hidden' && !showHud.value) return false;
  const state = runtimeState(name);
  if (state.invisible) return false;
  const visible = contractVisibleFields.value;
  if (visible.length && !visible.includes(name)) return false;
  if (semantic.surface_role === 'core') return true;
  if (semantic.surface_role === 'advanced') return advancedExpanded.value;
  const core = coreFieldNames.value;
  const advanced = advancedFieldNames.value;
  const hasCore = core.length > 0;
  const hasAdvanced = advanced.length > 0;
  if (!hasCore && !hasAdvanced) return true;
  if (hasCore && core.includes(name)) return true;
  if (hasAdvanced && advanced.includes(name)) return advancedExpanded.value;
  // Some contracts only tag advanced fields; keep non-tagged fields visible in that case.
  if (!hasCore) return true;
  return renderProfile.value !== 'create';
}

function isWritableFieldVisible(name: string) {
  if (useNativeFormTree.value) return nativeVisibleFieldNames.value.has(String(name || '').trim());
  return isFieldVisible(name);
}

const useNativeFormTree = computed(() => {
  return nativeFormLayoutNodes.value.length > 0;
});

function filterVisibleNativeLayoutNodes(nodes: NativeFormLayoutNode[]): NativeFormLayoutNode[] {
  return filterVisibleNativeLayoutNodesFromTree({
    nodes,
    isNodeVisible: isNativeLayoutNodeVisible,
    groupVisibilityEditable: isContractFieldOrderEditable.value,
    normalizeGroupTitle: normalizeFieldGroupTitle,
    isGroupVisible: effectiveGroupVisible,
  });
}

function applyNativeFieldOrderPreview(nodes: NativeFormLayoutNode[]): NativeFormLayoutNode[] {
  return applyNativeFieldOrderPreviewFromTree({
    nodes,
    fieldOrder: fieldOrderDraft.value,
    movedGroups: changedFieldGroupDraft(),
    moveTargetDraft: fieldMoveTargetDraft,
    normalizeGroupTitle: normalizeFieldGroupTitle,
    isReadableGroupTitle: isReadableFieldGroupTitle,
    groupTitleMatches: fieldGroupTitleMatches,
    baseGroupTitleForField: (fieldName) => fieldGroupBase.value[fieldName] || fieldGroupDraft[fieldName] || '',
  });
}

function runtimeNativeFormLayoutNodes(): NativeFormLayoutNode[] {
  const storeContainers = resolveContractV2ContainerTree(v2ContractStore.value);
  const v2 = storeContainers.length ? null : resolveUnifiedPageContractV2(contract.value);
  const containers = storeContainers.length
    ? storeContainers
    : (Array.isArray(v2?.layoutContract?.containerTree) ? v2.layoutContract.containerTree : []);
  if (containers.length > 0) {
    return normalizeContractV2ContainersForNativeFormFromTree(containers as unknown as NativeLayoutLikeNode[]) as NativeFormLayoutNode[];
  }
  return Array.isArray(contract.value?.views?.form?.layout)
    ? contract.value?.views?.form?.layout as unknown as NativeFormLayoutNode[]
    : [];
}

const rawNativeFormLayoutNodes = computed<NativeFormLayoutNode[]>(() => {
  if (isContractFieldOrderEditable.value && layoutHasReadableFieldGroups(lowCodeFormLayoutBase.value)) {
    return mergeLowCodeLayoutWithRuntimeGroupShells(lowCodeFormLayoutBase.value, runtimeNativeFormLayoutNodes());
  }
  const legacyLayout = Array.isArray(contract.value?.views?.form?.layout)
    ? contract.value?.views?.form?.layout as unknown as NativeFormLayoutNode[]
    : [];
  if (isContractFieldOrderEditable.value && legacyLayout.length) {
    return legacyLayout;
  }
  const storeContainers = resolveContractV2ContainerTree(v2ContractStore.value);
  const v2 = storeContainers.length ? null : resolveUnifiedPageContractV2(contract.value);
  const containers = storeContainers.length
    ? storeContainers
    : (Array.isArray(v2?.layoutContract?.containerTree) ? v2.layoutContract.containerTree : []);
  if (containers.length > 0) {
    return normalizeContractV2ContainersForNativeFormFromTree(containers as unknown as NativeLayoutLikeNode[]) as NativeFormLayoutNode[];
  }
  return legacyLayout;
});

const baseNativeFormLayoutNodes = computed<NativeFormLayoutNode[]>(() => {
  nativeLayoutVisibilityRevision.value;
  return filterVisibleNativeLayoutNodes(rawNativeFormLayoutNodes.value);
});

const nativeFormLayoutNodes = computed<NativeFormLayoutNode[]>(() => {
  const nodes = baseNativeFormLayoutNodes.value;
  if (isContractFieldOrderEditable.value && fieldOrderPreviewActive.value && fieldOrderDraft.value.length) {
    return applyNativeFieldOrderPreview(nodes);
  }
  return nodes;
});

const nativeFormRootColumns = computed<1 | 2 | 3>(() => {
  if (isContractFieldOrderEditable.value) return formLayoutColumnsDraft.value;
  return resolveNativeFormRootColumns(nativeFormLayoutNodes.value as NativeLayoutLikeNode[]);
});

watch(baseNativeFormLayoutNodes, (nodes) => {
  const { keys, labels } = collectNativeFormDesignFields(nodes as NativeLayoutLikeNode[]);
  nativeFormDesignFieldKeys.value = keys;
  nativeFormDesignFieldLabels.value = labels;
}, { immediate: true });

const nativeNotebookPageCount = computed(() => countNativeNodesByType(nativeFormLayoutNodes.value as NativeLayoutLikeNode[], 'page'));
const nativeGroupCount = computed(() => countNativeNodesByType(nativeFormLayoutNodes.value as NativeLayoutLikeNode[], 'group'));
const nativeVisibleSectionTitles = computed(() => collectNativeVisibleSectionTitles(nativeFormLayoutNodes.value as NativeLayoutLikeNode[]));
const showNativeDefaultSectionTitle = computed(() => (
  useNativeFormTree.value
  && nativeVisibleFieldNames.value.size > 0
  && nativeVisibleSectionTitles.value.length === 0
));

function resolveNativeButtonLabel(node: NativeFormLayoutNode) {
  return resolveNativeButtonLabelFromNode(node as NativeLayoutLikeNode, (field) => formData[field]);
}

const nativeVisibleFieldNames = computed(() => collectNativeVisibleFieldNames(
  nativeFormLayoutNodes.value as NativeLayoutLikeNode[],
  (name, node) => isNativeFieldVisible(name, node as NativeFormLayoutNode),
));

function formDataFieldNames() {
  const fieldMap = contract.value?.fields || {};
  const storeMainData = resolveContractV2MainData(v2ContractStore.value);
  const contractMainData = Object.keys(storeMainData).length ? storeMainData : resolveUnifiedPageContractV2MainData(contract.value);
  return collectFormDataFieldNames({
    contract: contract.value,
    fields: fieldMap,
    rawNativeLayoutNodes: rawNativeFormLayoutNodes.value as NativeLayoutLikeNode[],
    layoutFieldNames: layoutNodes.value.filter((node) => node.kind === 'field').map((node) => node.name),
    visibleFields: contractVisibleFields.value,
    statusField: nativeStatusbar.value.field,
    mainData: contractMainData,
  });
}

const nativeFavoriteFieldNames = computed(() => {
  const names = new Set<string>();
  collectNativeFavoriteFieldNames(rawNativeFormLayoutNodes.value, names);
  return names;
});

const nativeStatusbar = computed<NativeStatusbarVm>(() => {
  const storeMainData = resolveContractV2MainData(v2ContractStore.value);
  const contractMainData = Object.keys(storeMainData).length ? storeMainData : resolveUnifiedPageContractV2MainData(contract.value);
  return normalizeNativeFormStatusbar({
    recordId: recordId.value,
    formView: contract.value?.views?.form,
    fields: contract.value?.fields || {},
    formData: formData as Record<string, unknown>,
    mainData: contractMainData,
    fieldReadonly: (field) => runtimeState(field).readonly,
    readonly: renderProfile.value === 'readonly' || (recordId.value ? !rights.value.write : !rights.value.create),
    fallback: normalizeWorkflowPhaseStatusbar(currentWorkflowContract()),
  });
});

function setStatusbarValue(value: string) {
  const field = nativeStatusbar.value.field;
  if (!field || nativeStatusbar.value.readonly) return;
  const descriptor = contract.value?.fields?.[field];
  formData[field] = resolveStatusbarSelectionValue(descriptor, value);
  markFieldChanged(field);
}

function evaluateNativeModifierValue(value: unknown) {
  return evaluateNativeModifierValueWithResolver(value, (field) => formData[field]);
}

function evaluateNativeActionVisibility(row: Record<string, unknown>) {
  return isNativeActionVisible({
    row,
    currentState: String(formData.state || '').trim(),
    evaluateModifier: evaluateNativeModifierValue,
    resolveAction: contractActionFromNativeRow,
  });
}

function isNativeLayoutNodeVisible(nodeRaw: NativeFormLayoutNode) {
  return isNativeLayoutNodeVisibleFromNativeLayout({
    node: nodeRaw,
    editable: isContractFieldOrderEditable.value,
    evaluateModifier: evaluateNativeModifierValue,
    normalizeGroupTitle: normalizeFieldGroupTitle,
    isGroupVisible: effectiveGroupVisible,
    isFieldVisibleInDraft: (fieldName) => (
      Object.prototype.hasOwnProperty.call(fieldVisibilityDraft, fieldName)
        ? fieldVisibilityDraft[fieldName]
        : undefined
    ),
    resolveAction: contractActionFromNativeRow,
  });
}

function isNativeFavoriteField(name: string) {
  return nativeFavoriteFieldNames.value.has(String(name || '').trim());
}

function isNativeFieldVisible(name: string, nodeRaw?: NativeFormLayoutNode) {
  return isNativeFieldVisibleFromNativeLayout({
    name,
    node: nodeRaw,
    statusField: nativeStatusbar.value.field,
    showHud: showHud.value,
    renderProfile: renderProfile.value,
    isCreate: !recordId.value,
    isNodeVisible: (node) => isNativeLayoutNodeVisible(node as NativeFormLayoutNode),
    resolveDescriptor: (fieldName, node) => (node
      ? nativeNodeFieldDescriptor(node as NativeFormLayoutNode, contract.value?.fields?.[fieldName])
      : contract.value?.fields?.[fieldName]),
    resolveFieldLabel: contractFieldLabel,
    semantic: fieldSemanticMeta,
    runtimeState,
    evaluatePolicy: (fieldName, descriptor) => evaluateFieldPolicy(
      contract.value,
      fieldName,
      {
        required: Boolean(descriptor?.required),
        readonly: Boolean(descriptor?.readonly),
      },
      policyContext.value,
    ),
  });
}

function currentNativeFieldOrder() {
  return collectNativeVisibleFieldOrder(
    nativeFormLayoutNodes.value as NativeLayoutLikeNode[],
    (name, node) => isNativeFieldVisible(name, node as NativeFormLayoutNode),
  );
}

function ensureFieldOrderDraftStartsFromCurrentLayout() {
  if (!useNativeFormTree.value || fieldOrderPreviewActive.value) return;
  const current = currentNativeFieldOrder();
  if (!current.length) return;
  const known = new Set(current);
  const extra = fieldOrderDraft.value.filter((name) => name && !known.has(name));
  fieldOrderDraft.value = [...current, ...extra];
}

function nativeLayoutNodeToFieldNode(nodeRaw: NativeFormLayoutNode, index: number): LayoutNode | null {
  const name = String(nodeRaw?.name || '').trim();
  if (!name || !isNativeFieldVisible(name, nodeRaw)) return null;
  const descriptor = nativeNodeFieldDescriptor(nodeRaw, contract.value?.fields?.[name]);
  if (!descriptor) return null;
  const resolved = evaluateFieldPolicy(
    contract.value,
    name,
    {
      required: Boolean(descriptor?.required),
      readonly: Boolean(descriptor?.readonly),
    },
    policyContext.value,
  );
  const state = runtimeState(name);
  const nativeReadonly = isStaticTruthyModifier(nativeModifierValue(nodeRaw, 'readonly'));
  const nativeRequired = isStaticTruthyModifier(nativeModifierValue(nodeRaw, 'required'));
  const presentation = nativeFieldPresentation({
    node: nodeRaw,
    descriptor,
    resolveFieldLabel: contractFieldLabel,
    editable: isContractFieldOrderEditable.value,
    effectiveFieldSize,
  });
  const label = presentation.label;
  rememberFormConfigFieldLabel(name, label);
  return {
    key: `native_field_${name}_${index}`,
    kind: 'field',
    name,
    label,
    readonly: Boolean(nativeReadonly || resolved.readonly || state.readonly || (recordId.value ? !rights.value.write : !rights.value.create)),
    required: Boolean(nativeRequired || resolved.required || state.required || descriptor?.required),
    widget: nativeNodeWidget(nodeRaw),
    widgetSemantics: nativeNodeWidgetSemantics(nodeRaw),
    spanClass: presentation.spanClass,
    descriptor,
  };
}

function nativeFieldSchemasForNodes(nodes: NativeFormLayoutNode[]): FormSectionFieldSchema[] {
  return buildNativeFieldSchemas({
    nodes: nodes as NativeLayoutLikeNode[],
    mapNode: (node, index) => nativeLayoutNodeToFieldNode(node as NativeFormLayoutNode, index),
    buildSchemas: buildSectionFieldSchemas,
    applyReadonlyValues: (schemas) => applyReadonlyFieldValues(schemas, v2FieldValue),
    orderActive: isContractFieldOrderEditable.value && fieldOrderPreviewActive.value,
    fieldOrder: fieldOrderDraft.value,
    favoriteActive: (fieldName) => Boolean(formData[fieldName]),
    favoriteReadonly: (field) => Boolean(field.readonly || busy.value),
  });
}

function v2FieldValue(name: string) {
  const normalized = String(name || '').trim();
  if (!normalized || !v2ContractStore.value?.widgetsByFieldCode.has(normalized)) {
    return { found: false, value: undefined };
  }
  const source = v2ShadowValueSource.value.values;
  if (!Object.prototype.hasOwnProperty.call(source, normalized)) {
    return { found: false, value: undefined };
  }
  return { found: true, value: source[normalized] };
}

function shouldShowRequiredMark(node: LayoutNode) {
  return shouldShowRequiredMarkFromNativeLayout({
    node,
    showHud: showHud.value,
    renderProfile: renderProfile.value,
    policyRequiredFields: policyRequiredFields.value,
    validationRequiredFields: validationRequiredFields.value,
    coreFieldNames: coreFieldNames.value,
  });
}

function collectSceneValidationPrecheckErrors(fieldLabels: Record<string, string>): string[] {
  return collectSceneValidationPrecheckErrorsFromRules({
    requiredFields: sceneValidationRequiredFields.value,
    fieldLabels,
    isFieldVisible,
    fieldValue: (field) => formData[field],
    isMissingValue: isMissingRequiredValue,
    errorCode: ErrorCodes.SCENE_VALIDATION_REQUIRED,
  });
}

const layoutNodes = computed<LayoutNode[]>(() => {
  const fieldMap = contract.value?.fields || {};
  const v2FieldContainerStatus = collectUnifiedPageContractV2FieldContainerStatus(contract.value);
  return buildLegacyLayoutNodes({
    fields: fieldMap,
    order: contract.value?.views?.form?.layout || [],
    containerStatus: v2FieldContainerStatus,
    visibleFields: contractVisibleFields.value,
    fallbackFieldNames: [...coreFieldNames.value, ...advancedFieldNames.value],
    isCreate: !recordId.value,
    readonly: recordId.value ? !rights.value.write : !rights.value.create,
    resolveFieldLabel: contractFieldLabel,
    evaluatePolicy: (name, descriptor) => evaluateFieldPolicy(
      contract.value,
      name,
      {
        required: Boolean(descriptor?.required),
        readonly: Boolean(descriptor?.readonly),
      },
      policyContext.value,
    ),
    runtimeState,
  });
});

const buildSectionFieldSchemas = createFormSectionFieldSchemaBuilder({
  resolveFieldType: (descriptor) => fieldType(descriptor) || 'char',
  resolveRequired: (field) => shouldShowRequiredMark(field as LayoutNode),
  resolveSpanClass: (field) => (field as LayoutNode).spanClass || resolveFieldSpanClass({
    fieldName: field.name,
    fieldType: fieldType(field.descriptor),
  }),
  resolveRawValue: (fieldName) => formData[fieldName],
  resolveMany2oneValue: many2oneValue,
  normalizeDateInputValue: toDateInputValue,
  normalizeDatetimeInputValue: toDatetimeInputValue,
  resolveTextInputValue: inputFieldValue,
  resolveInputPlaceholder: (label) => resolveInputPlaceholder(label),
  resolveSelectionOptions: (descriptor) => mapDescriptorSelectionOptions(descriptor),
  resolveRelationOptions: (fieldName) => mapRelationOptions(relationOptionsForField(fieldName)),
  resolveRelationCreateMode: (_fieldName, descriptor) => relationCreateMode(descriptor),
  resolveRelationInlineCreate: (fieldName, descriptor) => {
    const inline = relationInlineCreate(descriptor);
    return {
      enabled: inline.enabled,
      createOnNoMatch: inline.createOnNoMatch,
      nameField: inline.nameField,
      match: inline.match,
    };
  },
  resolveRelationTextValue: relationKeyword,
  resolveCanOpenRelationRecord: (fieldName, descriptor) => canOpenRelationRecordForm(fieldName, descriptor),
  resolveRelationRecordOpenLabel: (_fieldName, descriptor) => relationUiLabel(descriptor, 'open_existing', '维护当前项'),
  resolveRelationSearchLabel: (_fieldName, descriptor) => relationUiLabel(descriptor, 'search_more'),
  resolveRelationCreateLabel: (_fieldName, descriptor) => {
    const mode = relationCreateMode(descriptor);
    if (mode === 'page') return relationUiLabel(descriptor, 'create_and_edit');
    if (mode === 'quick') return relationUiLabel(descriptor, 'quick_create');
    return '';
  },
  resolveRelationInlineCreateLabel: (_fieldName, descriptor, keyword) => {
    const template = relationUiLabel(descriptor, 'inline_create');
    const label = String(keyword || '').trim();
    return template.includes('%s') ? template.replace('%s', label) : template || label;
  },
  many2oneCreateToken: MANY2ONE_CREATE_OPTION,
  many2oneSearchToken: MANY2ONE_SEARCH_MORE_OPTION,
  many2oneOpenToken: MANY2ONE_OPEN_RECORD_OPTION,
});

function onTemplateFieldChange(payload: FormSectionFieldChange) {
  if (String(payload.type || '').trim().toLowerCase() === 'many2one' && payload.action === 'query') {
    queryMany2oneInline(payload.name, payload.descriptor, String(payload.value ?? ''));
    return;
  }
  if (String(payload.type || '').trim().toLowerCase() === 'many2one' && payload.action === 'commit') {
    void commitMany2oneInline(payload.name, payload.descriptor, String(payload.value ?? ''));
    return;
  }
  dispatchTemplateFieldChange(payload, {
    onBoolean: (name, value) => setBooleanField(name, value),
    onSelection: (name, value) => setSelectionField(name, value),
    onMany2one: (name, descriptor, value) => setMany2oneField(name, descriptor, value),
    onText: (name, value) => setTextField(name, value),
  });
}

const relationFieldAdapter = computed<RelationFieldAdapter>(() => ({
  busy: busy.value,
  showOne2manyErrors: showOne2manyErrors.value,
  relationKeyword,
  setRelationKeyword,
  relationIds,
  selectedRelationOptions,
  filteredRelationOptions,
  setRelationMultiField,
  setRelationIds,
  relationCreateMode: (fieldName: string) => relationCreateMode(contract.value?.fields?.[fieldName]),
  relationCreateLabel: (fieldName: string) => {
    const descriptor = contract.value?.fields?.[fieldName];
    const mode = relationCreateMode(descriptor);
    if (mode === 'page') return relationUiLabel(descriptor, 'create_and_edit');
    if (mode === 'quick') return relationUiLabel(descriptor, 'quick_create');
    return '';
  },
  relationInlineCreateLabel: (fieldName: string) => {
    const descriptor = contract.value?.fields?.[fieldName];
    const template = relationUiLabel(descriptor, 'inline_create');
    const label = relationKeyword(fieldName).trim();
    return template.includes('%s') ? template.replace('%s', label) : template || label;
  },
  canInlineCreateRelation: (fieldName: string) => {
    const descriptor = contract.value?.fields?.[fieldName];
    const inline = relationInlineCreate(descriptor);
    const keyword = relationKeyword(fieldName).trim();
    if (!keyword || !inline.enabled || !inline.createOnNoMatch) return false;
    return !relationOptionsForField(fieldName).some((option) => option.label.trim().toLowerCase() === keyword.toLowerCase());
  },
  openRelationCreate: (fieldName: string) => {
    const descriptor = contract.value?.fields?.[fieldName];
    if (!descriptor) return;
    void openRelationCreateForm(fieldName, descriptor);
  },
  one2manyCanCreate,
  one2manyCreateLabel,
  addOne2manyRow,
  one2manySummary,
  visibleOne2manyRows,
  one2manyRowStateLabel,
  one2manyColumns,
  setOne2manyRowField,
  removeOne2manyRow,
  one2manyRowErrors,
  one2manyRowHints,
  removedOne2manyRows,
  restoreOne2manyRow,
  one2manyRowLabel,
  selectPlaceholder: resolveSelectPlaceholder,
  one2manyColumnInputType,
  one2manyColumnDisplayValue,
  inputFieldValue,
  fieldInputType,
  inputPlaceholder: resolveInputPlaceholder,
  setTextField,
}));

const contractReadiness = computed<FormContractReadiness>(() => {
  if (!contract.value) {
    return { usable: false, issues: ['contract not loaded'], fieldCount: 0, layoutFieldCount: 0, visibleCandidateCount: 0 };
  }
  return analyzeFormContractReadiness(contract.value, { requirePureFormViewType: false });
});

function comparableFieldValue(name: string, value: unknown) {
  const descriptor = contract.value?.fields?.[name];
  const ttype = fieldType(descriptor);
  if (ttype === 'many2many') {
    return JSON.stringify(normalizeRelationIds(value).sort((a, b) => a - b));
  }
  if (ttype === 'one2many') {
    const rows = one2manyFieldRows(name).map((row) => ({
      id: row.id || 0,
      isNew: row.isNew,
      removed: row.removed,
      dirty: row.dirty,
      dirtyFields: row.dirtyFields || [],
      values: row.values || {},
    }));
    return JSON.stringify(rows);
  }
  return normalizeComparable(value);
}

function isFieldWritable(name: string) {
  const node = layoutNodes.value.find((item) => item.kind === 'field' && item.name === name);
  if (node) return !node.readonly;
  const statusField = nativeStatusbar.value.field;
  return Boolean(statusField && statusField === name && !nativeStatusbar.value.readonly);
}

function normalizeFieldValue(name: string, value: unknown) {
  return normalizeContractFieldValue({
    name,
    value,
    descriptor: contract.value?.fields?.[name],
    originalValue: originalValues.value[name],
    buildOne2manyValue: buildOne2manyCommandValue,
  });
}

function inputFieldValue(name: string) {
  const raw = formData[name];
  if (raw === false || raw === null || raw === undefined) return '';
  return String(raw);
}

function setBooleanField(name: string, checked: boolean) {
  const previousValue = formData[name];
  formData[name] = checked;
  if (isNativeFavoriteField(name) && recordId.value && rights.value.write) {
    void persistNativeFavoriteField(name, checked, previousValue);
    return;
  }
  markFieldChanged(name);
}

async function persistNativeFavoriteField(name: string, checked: boolean, previousValue: unknown) {
  try {
    await writeContractFormRecord({
      model: model.value,
      ids: [recordId.value],
      vals: { [name]: checked },
      context: {},
    });
    originalValues.value = {
      ...originalValues.value,
      [name]: checked,
    };
    changedFieldSet.delete(name);
    dirtyFieldSet.delete(name);
  } catch {
    formData[name] = previousValue;
    submissionFeedback.value = {
      kind: 'error',
      message: '收藏状态保存失败，请稍后重试。',
    };
  }
}

function setMany2oneField(name: string, descriptor: FieldDescriptor | undefined, value: string) {
  const normalized = String(value || '').trim();
  if (!normalized) {
    formData[name] = false;
    relationKeywords[name] = '';
    clearDynamicRelationDependents(name);
    markFieldChanged(name);
    return;
  }
  if (normalized === MANY2ONE_CREATE_OPTION) {
    void openRelationCreateForm(name, descriptor);
    return;
  }
  if (normalized === MANY2ONE_SEARCH_MORE_OPTION) {
    void openRelationSearchDialog(name, descriptor);
    return;
  }
  if (normalized === MANY2ONE_OPEN_RECORD_OPTION) {
    void openRelationRecordForm(name, descriptor);
    return;
  }
  const id = Number(normalized);
  if (!Number.isFinite(id) || id <= 0) {
    formData[name] = false;
    relationKeywords[name] = '';
    clearDynamicRelationDependents(name);
    markFieldChanged(name);
    return;
  }
  const normalizedId = Math.trunc(id);
  formData[name] = normalizedId;
  const selected = relationOptionsForField(name).find((option) => option.id === normalizedId);
  if (selected) {
    relationKeywords[name] = selected.label;
    void switchFormByRelationOption(name, selected);
  }
  clearDynamicRelationDependents(name);
  markFieldChanged(name);
}

function queryMany2oneInline(name: string, descriptor: FieldDescriptor | undefined, value: string) {
  const keyword = String(value || '').trim();
  if (keyword && clearedDynamicRelationFields[name]) {
    delete clearedDynamicRelationFields[name];
    delete invalidatedRelationKeywords[name];
  }
  if (keyword && invalidatedRelationKeywords[name] === keyword && !formData[name]) {
    relationKeywords[name] = '';
    return;
  }
  if (keyword && invalidatedRelationKeywords[name] && invalidatedRelationKeywords[name] !== keyword) {
    delete invalidatedRelationKeywords[name];
  }
  relationKeywords[name] = keyword;
  if (!keyword) {
    void queryRelationOptions(name, '');
    return;
  }
  setRelationKeyword(name, keyword);
}

async function commitMany2oneInline(name: string, descriptor: FieldDescriptor | undefined, value: string) {
  const keyword = String(value || '').trim();
  if (keyword && clearedDynamicRelationFields[name] && !formData[name]) {
    relationKeywords[name] = '';
    return;
  }
  if (keyword && invalidatedRelationKeywords[name] === keyword && !formData[name]) {
    relationKeywords[name] = '';
    return;
  }
  if (keyword && invalidatedRelationKeywords[name] && invalidatedRelationKeywords[name] !== keyword) {
    delete invalidatedRelationKeywords[name];
  }
  if (!keyword) {
    formData[name] = false;
    relationKeywords[name] = '';
    markFieldChanged(name);
    return;
  }
  const currentId = Number(formData[name] || 0);
  if (Number.isFinite(currentId) && currentId > 0) {
    const currentOption = relationOptionsForField(name).find((option) => option.id === Math.trunc(currentId));
    if (currentOption && currentOption.label.trim().toLowerCase() === keyword.toLowerCase()) {
      relationKeywords[name] = currentOption.label;
      return;
    }
  }
  const inline = relationInlineCreate(descriptor);
  const localQuickFill = resolveRelationQuickFillOption(relationOptionsForField(name), keyword, inline.match);
  if (localQuickFill) {
    setMany2oneOption(name, localQuickFill);
    return;
  }
  const localSingleMatch = singleContainingRelationOption(relationOptionsForField(name), keyword);
  if (localSingleMatch) {
    setMany2oneOption(name, localSingleMatch);
    return;
  }
  const rows = await queryRelationOptions(name, keyword);
  const remoteQuickFill = resolveRelationQuickFillOption(rows, keyword, inline.match);
  if (remoteQuickFill) {
    setMany2oneOption(name, remoteQuickFill);
    return;
  }
  if (rows.length === 1) {
    setMany2oneOption(name, rows[0]);
    return;
  }
  if (hasAmbiguousRelationMatches(rows, keyword, inline.match)) {
    relationKeywords[name] = keyword;
    formData[name] = false;
    markFieldChanged(name);
    await openRelationSearchDialog(name, descriptor);
    return;
  }
  if (!inline.enabled || !inline.createOnNoMatch) return;
  formData[name] = false;
  relationKeywords[name] = keyword;
  markFieldChanged(name);
}

async function resolvePendingInlineRelationCreates() {
  const issues: string[] = [];
  for (const node of layoutNodes.value) {
    if (node.kind !== 'field' || node.readonly) continue;
    const descriptor = contract.value?.fields?.[node.name];
    if (fieldType(descriptor) !== 'many2one') continue;
    const inline = relationInlineCreate(descriptor);
    if (!inline.enabled || !inline.createOnNoMatch) continue;
    const currentId = Number(formData[node.name] || 0);
    if (Number.isFinite(currentId) && currentId > 0) continue;
    const keyword = relationKeyword(node.name).trim();
    if (!keyword) continue;
    const localQuickFill = resolveRelationQuickFillOption(relationOptionsForField(node.name), keyword, inline.match);
    if (localQuickFill) {
      setMany2oneOption(node.name, localQuickFill);
      continue;
    }
    const rows = await queryRelationOptions(node.name, keyword);
    const remoteQuickFill = resolveRelationQuickFillOption(rows, keyword, inline.match);
    if (remoteQuickFill) {
      setMany2oneOption(node.name, remoteQuickFill);
      continue;
    }
    if (hasAmbiguousRelationMatches(rows, keyword, inline.match)) {
      relationKeywords[node.name] = keyword;
      await openRelationSearchDialog(node.name, descriptor);
      issues.push(`${node.label || descriptor?.string || node.name}存在多个匹配记录，请选择具体记录`);
      continue;
    }
    const beforeErrors = validationErrors.value.slice();
    await quickCreateRelation(node.name, descriptor, keyword);
    const resolvedId = Number(formData[node.name] || 0);
    if (!Number.isFinite(resolvedId) || resolvedId <= 0) {
      const createdErrors = validationErrors.value.length
        ? validationErrors.value.slice()
        : [relationUiLabel(descriptor, 'inline_create_failed', '保存时创建失败')];
      issues.push(...createdErrors);
      validationErrors.value = beforeErrors;
    }
  }
  return Array.from(new Set(issues)).slice(0, 5);
}

async function resolvePendingMany2manyTagCreates() {
  const issues: string[] = [];
  for (const [name, rawKeyword] of Object.entries(relationKeywords)) {
    const keyword = String(rawKeyword || '').trim();
    if (!keyword) continue;
    if (!isFieldWritable(name)) continue;
    if (!Array.isArray(formData[name])) continue;
    const descriptor = contract.value?.fields?.[name];
    if (!relationModel(name)) continue;
    const inline = relationInlineCreate(descriptor);
    if (!inline.enabled || !inline.createOnNoMatch) continue;
    const fieldLabel = layoutNodes.value.find((node) => node.kind === 'field' && node.name === name)?.label
      || descriptor?.string
      || name;
    const localQuickFill = resolveRelationQuickFillOption(relationOptionsForField(name), keyword, inline.match);
    if (localQuickFill) {
      addRelationId(name, localQuickFill);
      continue;
    }
    const rows = await queryRelationOptions(name, keyword);
    const remoteQuickFill = resolveRelationQuickFillOption(rows, keyword, inline.match);
    if (remoteQuickFill) {
      addRelationId(name, remoteQuickFill);
      continue;
    }
    if (hasAmbiguousRelationMatches(rows, keyword, inline.match)) {
      issues.push(`${fieldLabel}存在多个匹配记录，请选择具体记录`);
      continue;
    }
    const beforeErrors = validationErrors.value.slice();
    await quickCreateMany2manyTag(name);
    const created = !relationKeyword(name).trim();
    if (!created) {
      const createdErrors = validationErrors.value.length
        ? validationErrors.value.slice()
        : [relationUiLabel(descriptor, 'inline_create_failed', '保存时创建失败')];
      issues.push(...createdErrors);
      validationErrors.value = beforeErrors;
    }
  }
  return Array.from(new Set(issues)).slice(0, 5);
}

function setSelectionField(name: string, value: string) {
  formData[name] = value || false;
  markFieldChanged(name);
}

function setRelationMultiField(name: string, target: HTMLSelectElement) {
  const ids = Array.from(target.selectedOptions)
    .map((item) => Number(item.value))
    .filter((id) => Number.isFinite(id) && id > 0)
    .map((id) => Math.trunc(id));
  formData[name] = ids;
  markFieldChanged(name);
}

function setRelationIds(name: string, ids: number[]) {
  formData[name] = Array.from(new Set((ids || [])
    .map((id) => Number(id))
    .filter((id) => Number.isFinite(id) && id > 0)
    .map((id) => Math.trunc(id))));
  markFieldChanged(name);
}

function addRelationId(name: string, option: RelationOption) {
  upsertRelationOption(name, option);
  setRelationIds(name, [...relationIds(name), option.id]);
  relationKeywords[name] = '';
}

async function quickCreateMany2manyTag(name: string) {
  const descriptor = contract.value?.fields?.[name];
  const relation = relationModel(name);
  const label = relationKeyword(name).trim();
  if (!relation || !label) return;
  const inline = relationInlineCreate(descriptor);
  if (!inline.enabled || !inline.createOnNoMatch) return;
  const existing = resolveRelationQuickFillOption(relationOptionsForField(name), label, inline.match);
  if (existing) {
    addRelationId(name, existing);
    return;
  }
  const nameField = inline.nameField || 'name';
  try {
    const entry = relationEntry(descriptor);
    const vals: Record<string, unknown> = { ...(entry?.defaultVals || {}), [nameField]: label };
    if (relation === 'sc.dictionary' && typeof vals.type === 'string' && String(vals.type || '').trim()) {
      vals.code = label.toUpperCase().replace(/\s+/g, '_').slice(0, 60);
    }
    const created = await createContractFormRecord({ model: relation, vals });
    const id = Number(created?.id || 0);
    if (Number.isFinite(id) && id > 0) {
      addRelationId(name, { id: Math.trunc(id), label });
      await queryRelationOptions(name, '');
    }
  } catch (err) {
    validationErrors.value = [
      sanitizeUiErrorMessage(err instanceof Error ? err.message : err, relationUiLabel(descriptor, 'quick_create_failed')),
    ];
  }
}

function setTextField(name: string, value: string) {
  formData[name] = value;
  markFieldChanged(name);
}

function markFieldChanged(name: string) {
  const key = String(name || '').trim();
  if (!key || applyingOnchangePatch.value) return;
  dirtyFieldSet.add(key);
  changedFieldSet.add(key);
  scheduleOnchange();
}

function scheduleOnchange() {
  if (onchangeTimer) clearTimeout(onchangeTimer);
  onchangeTimer = setTimeout(() => {
    void runOnchangeRoundtrip();
  }, 300);
}

function buildOnchangeValues() {
  const out: Record<string, unknown> = {};
  Object.keys(contract.value?.fields || {}).forEach((name) => {
    const descriptor = contract.value?.fields?.[name];
    out[name] = normalizeContractFieldValue({
      name,
      value: formData[name],
      descriptor,
      originalValue: originalValues.value[name],
      mode: 'onchange',
      buildOne2manyValue: buildOne2manyCommandValue,
    });
  });
  if (recordId.value) out.id = recordId.value;
  return out;
}

async function runOnchangeRoundtrip() {
  if (!model.value) return;
  if (!changedFieldSet.size) return;
  const changed = Array.from(changedFieldSet);
  changedFieldSet.clear();
  try {
    const response = await triggerOnchange({
      model: model.value,
      res_id: recordId.value,
      values: buildOnchangeValues(),
      changed_fields: changed,
      context: pickContractNavQuery(route.query as Record<string, unknown>),
    });
    const patch = response?.patch;
    const modifiersPatch = response?.modifiers_patch;
    const linePatches = Array.isArray(response?.line_patches) ? response.line_patches : [];
    const warnings = Array.isArray(response?.warnings) ? response.warnings : [];
    onchangeWarnings.value = warnings;
    onchangeLinePatches.value = linePatches;
    if (modifiersPatch && typeof modifiersPatch === 'object') {
      onchangeModifiersPatch.value = {
        ...onchangeModifiersPatch.value,
        ...(modifiersPatch as Record<string, Record<string, unknown>>),
      };
      const patchedFields = Object.keys(modifiersPatch as Record<string, Record<string, unknown>>);
      await Promise.all(
        patchedFields.map(async (name) => {
          const descriptor = contract.value?.fields?.[name];
          const ttype = fieldType(descriptor);
          if (!['many2one', 'many2many', 'one2many'].includes(ttype)) return;
          await queryRelationOptions(name, relationKeyword(name));
        }),
      );
    }
    if (patch && typeof patch === 'object') {
      applyingOnchangePatch.value = true;
      Object.entries(patch).forEach(([name, value]) => {
        if (!(name in (contract.value?.fields || {}))) return;
        const ttype = fieldType(contract.value?.fields?.[name]);
        if (ttype === 'many2many' || ttype === 'one2many') {
          formData[name] = Array.isArray(value) ? value : [];
          if (ttype === 'one2many') initOne2manyRows(name, formData[name]);
        } else if (ttype === 'many2one') {
          const option = parseMany2oneDisplay(value);
          upsertRelationOption(name, option);
          const ids = normalizeRelationIds(value);
          const nextId = ids.length ? ids[0] : false;
          if (!nextId) {
            const currentIds = relationIds(name);
            const selectedOption = currentIds.length
              ? (relationOptions.value[name] || []).find((item) => item.id === currentIds[0])
              : null;
            const staleKeyword = relationKeyword(name).trim() || String(selectedOption?.label || '').trim();
            if (staleKeyword) invalidatedRelationKeywords[name] = staleKeyword;
            clearedDynamicRelationFields[name] = true;
            if (relationQueryTimers[name]) {
              clearTimeout(relationQueryTimers[name]);
              delete relationQueryTimers[name];
            }
          }
          const node = layoutNodes.value.find((item) => item.kind === 'field' && item.name === name);
          const readonly = Boolean(node?.readonly || contract.value?.fields?.[name]?.readonly);
          formData[name] = readonly && option ? [option.id, option.label] : nextId;
          relationKeywords[name] = option?.label || (nextId ? relationKeywords[name] || `#${nextId}` : '');
        } else if (ttype === 'date') {
          formData[name] = toDateInputValue(value);
        } else if (ttype === 'datetime') {
          formData[name] = toDatetimeInputValue(value);
        } else {
          formData[name] = value;
        }
      });
      applyingOnchangePatch.value = false;
    }
    if (linePatches.length) {
      applyingOnchangePatch.value = true;
      applyOnchangeLinePatches(linePatches);
      applyingOnchangePatch.value = false;
    }
  } catch {
    // Onchange is best-effort; keep current values when roundtrip fails.
  }
}

function collectWritableValues() {
  const values = layoutNodes.value
    .filter((node) => node.kind === 'field' && !node.readonly && isWritableFieldVisible(node.name))
    .reduce<Record<string, unknown>>((acc, node) => {
      if (recordId.value && !dirtyFieldSet.has(node.name)) {
        return acc;
      }
      const value = normalizeFieldValue(node.name, formData[node.name]);
      const ttype = fieldType(node.descriptor);
      if ((ttype === 'many2many' || ttype === 'one2many') && Array.isArray(value) && !value.length) {
        return acc;
      }
      acc[node.name] = value;
      return acc;
    }, {});
  const statusField = nativeStatusbar.value.field;
  if (
    recordId.value
    && statusField
    && dirtyFieldSet.has(statusField)
    && !nativeStatusbar.value.readonly
    && statusField in (contract.value?.fields || {})
    && !(statusField in values)
  ) {
    values[statusField] = normalizeFieldValue(statusField, formData[statusField]);
  }
  return values;
}

function isRequiredFieldEmpty(value: unknown, descriptor?: FieldDescriptor | null) {
  return isRequiredFieldEmptyByType(value, fieldType(descriptor));
}

function collectRequiredFieldIssues(values: Record<string, unknown>) {
  const missing = layoutNodes.value
    .filter((node) => node.kind === 'field' && !node.readonly && isWritableFieldVisible(node.name))
    .filter((node) => {
      const descriptor = node.descriptor || contract.value?.fields?.[node.name];
      if (!descriptor?.required) return false;
      const value = Object.prototype.hasOwnProperty.call(values, node.name)
        ? values[node.name]
        : normalizeFieldValue(node.name, formData[node.name]);
      return isRequiredFieldEmpty(value, descriptor);
    })
    .map((node) => String(node.label || node.descriptor?.string || node.name).trim())
    .filter(Boolean);
  if (!missing.length) return [];
  return [`保存前请填写：${Array.from(new Set(missing)).slice(0, 5).join('、')}`];
}

function formCreateContext() {
  const storeContext = resolveContractV2SourceContext(v2ContractStore.value);
  const sourceContext = (Object.keys(storeContext).length ? storeContext : resolveUnifiedPageContractV2SourceContext(contract.value)).context || {};
  return sourceContext;
}

function resolveCreateDefaults() {
  const storeMainData = resolveContractV2MainData(v2ContractStore.value);
  const defaults: Record<string, unknown> = {
    ...(Object.keys(storeMainData).length ? storeMainData : resolveUnifiedPageContractV2MainData(contract.value)),
  };
  Object.entries(route.query as Record<string, unknown>).forEach(([key, value]) => {
    if (key.startsWith('default_')) {
      defaults[key.replace(/^default_/, '')] = normalizeRouteDefault(value);
    }
  });
  const context = formCreateContext();
  Object.entries(context).forEach(([key, value]) => {
    if (key.startsWith('default_') && !(key.replace(/^default_/, '') in defaults)) {
      defaults[key.replace(/^default_/, '')] = value;
    }
  });
  const validator = contract.value?.validator as Record<string, unknown> | undefined;
  const defaultsSample = validator?.defaults_sample;
  if (defaultsSample && typeof defaultsSample === 'object' && !Array.isArray(defaultsSample)) {
    Object.entries(defaultsSample as Record<string, unknown>).forEach(([key, value]) => {
      if (!(key in defaults)) {
        defaults[key] = value === 'dynamic' ? '' : value;
      }
    });
  }
  const selectedProject = session.projectContext?.selected;
  const selectedProjectId = Number(selectedProject?.id || 0);
  if (
    selectedProjectId > 0
    && contract.value?.fields?.project_id
    && normalizeRelationIds(defaults.project_id).length === 0
  ) {
    defaults.project_id = [
      selectedProjectId,
      selectedProject?.display_name || selectedProject?.name || `项目 ${selectedProjectId}`,
    ];
  }
  const selectedStrategy = String(selectedProject?.operation_strategy || '').trim();
  if (
    selectedStrategy
    && contract.value?.fields?.operation_strategy
    && !String(defaults.operation_strategy || '').trim()
  ) {
    defaults.operation_strategy = selectedStrategy;
  }
  const selectedOwnerId = Number(selectedProject?.owner_id || 0);
  if (
    selectedOwnerId > 0
    && contract.value?.fields?.owner_id
    && normalizeRelationIds(defaults.owner_id).length === 0
  ) {
    defaults.owner_id = [
      selectedOwnerId,
      selectedProject?.owner_name || `业主 ${selectedOwnerId}`,
    ];
  }
  return defaults;
}

function resolveNavigationUrl(url: string) {
  return resolveNavigationUrlFromOrigin(url, window.location.origin);
}

function syncContractV2ShadowStore(rawContract: unknown) {
  v2ContractStore.value = null;
  v2ContractDecodeError.value = '';
  try {
    const snapshot = decodeContractV2Snapshot(resolveUnifiedPageContractV2(rawContract) || rawContract);
    v2ContractStore.value = createContractV2Store(snapshot);
  } catch (err) {
    if (err instanceof ContractV2DecodeError) {
      v2ContractDecodeError.value = err.issues.slice(0, 4).map((issue) => `${issue.path} ${issue.message}`).join(' | ');
      return;
    }
    v2ContractDecodeError.value = err instanceof Error ? err.message : '表单配置解析失败';
  }
}

const viewOrchestrationHudSummary = computed(() => {
  const rootGovernance = contract.value && typeof contract.value === 'object'
    ? (contract.value as Record<string, unknown>).governance
    : undefined;
  const governance = rootGovernance && typeof rootGovernance === 'object' && !Array.isArray(rootGovernance)
    ? rootGovernance as Record<string, unknown>
    : {};
  const orchestration = governance.view_orchestration && typeof governance.view_orchestration === 'object' && !Array.isArray(governance.view_orchestration)
    ? governance.view_orchestration as Record<string, unknown>
    : {};
  const views = orchestration.views && typeof orchestration.views === 'object' && !Array.isArray(orchestration.views)
    ? orchestration.views as Record<string, unknown>
    : {};
  const current = (views.form || {}) as Record<string, unknown>;
  const contracts = Array.isArray(current.business_config_contracts)
    ? current.business_config_contracts as Array<Record<string, unknown>>
    : [];
  const businessConfigFormFields = Array.isArray(current.business_config_form_fields)
    ? current.business_config_form_fields.map((item) => String(item || '').trim()).filter(Boolean)
    : [];
  const skippedLegacyPolicyFields = Array.isArray(current.skipped_legacy_policy_fields)
    ? current.skipped_legacy_policy_fields.map((item) => String(item || '').trim()).filter(Boolean)
    : [];
  return {
    applied: Boolean(orchestration.applied || current.applied || contracts.length),
    owner: String(orchestration.owner_layer || current.owner_layer || '-'),
    contractCount: contracts.length,
    contractNames: contracts.map((row) => String(row.name || row.id || '').trim()).filter(Boolean).join(',') || '-',
    legacyOverlay: Boolean(current.legacy_field_policy_overlay),
    businessConfigFieldCount: businessConfigFormFields.length,
    skippedLegacyPolicyFields: skippedLegacyPolicyFields.join(',') || '-',
  };
});

const hudEntries = computed(() => [
  { label: '业务对象', value: model.value || '-' },
  { label: '操作编号', value: actionId.value || '-' },
  { label: '记录编号', value: recordIdDisplay.value },
  { label: '配置已加载', value: Boolean(contract.value) },
  { label: '配置可用', value: contractReadiness.value.usable },
  { label: '配置问题数', value: contractReadiness.value.issues.length },
  { label: '新版配置暂存可用', value: v2ShadowStoreReady.value },
  { label: '新版配置组件数', value: v2ShadowWidgetCount.value },
  { label: '新版配置操作数', value: v2ShadowActionCount.value },
  { label: '新版配置按钮状态数', value: v2ShadowButtonStatusCount.value },
  { label: '新版配置字段编码数', value: v2ShadowFieldCodeCount.value },
  { label: '新版配置字段重叠数', value: v2ShadowLegacyFieldOverlapCount.value },
  { label: '新版配置缺失字段', value: v2ShadowLegacyFieldMissingPreview.value },
  { label: '新版配置布局来源', value: v2ShadowLayoutSourceKind.value },
  { label: '新版配置全局来源', value: v2ShadowGlobalSourceKind.value },
  { label: '新版配置上下文来源', value: v2ShadowSourceContextKind.value },
  { label: '新版配置状态字段数', value: v2ShadowStatusFieldCount.value },
  { label: '新版配置值字段数', value: v2ShadowValueFieldCount.value },
  { label: '新版配置主数据字段数', value: v2ShadowMainDataFieldCount.value },
  { label: '新版配置只读值数', value: v2ShadowReadonlyValueCount.value },
  { label: '新版配置值来源', value: v2ShadowValueSourceKind.value },
  { label: '配置解析问题', value: v2ContractDecodeError.value || '-' },
  { label: '配置视图类型', value: contract.value?.head?.view_type || contract.value?.view_type || '-' },
  { label: '页面编排已应用', value: viewOrchestrationHudSummary.value.applied },
  { label: '页面编排责任层', value: viewOrchestrationHudSummary.value.owner },
  { label: '页面编排配置数', value: viewOrchestrationHudSummary.value.contractCount },
  { label: '页面编排名称', value: viewOrchestrationHudSummary.value.contractNames },
  { label: '表单配置字段数', value: viewOrchestrationHudSummary.value.businessConfigFieldCount },
  { label: '跳过策略字段', value: viewOrchestrationHudSummary.value.skippedLegacyPolicyFields },
  { label: '历史策略覆盖', value: viewOrchestrationHudSummary.value.legacyOverlay },
  { label: '渲染档位', value: renderProfile.value },
  { label: '字段数', value: Object.keys(contract.value?.fields || {}).length },
  { label: '布局节点数', value: layoutNodes.value.length },
  { label: '可写字段数', value: writableFieldCount.value },
  { label: '已变更字段数', value: changedFieldCount.value },
  { label: '操作数', value: contractActions.value.length },
  { label: '权限', value: `${rights.value.read ? 'R' : '-'}${rights.value.write ? 'W' : '-'}${rights.value.create ? 'C' : '-'}${rights.value.unlink ? 'D' : '-'}` },
  { label: '联动提醒数', value: onchangeWarnings.value.length },
  { label: '明细联动补丁数', value: onchangeLinePatches.value.length },
]);

async function loadContract() {
  v2ContractStore.value = null;
  v2ContractDecodeError.value = '';
  const profile = recordId.value ? 'edit' : 'create';
  const currentModel = String(model.value || '').trim();
  const contractContext = buildRouteContractContext(route.query as Record<string, unknown>);
  const contextRaw = String(route.query.context_raw || '').trim();
  const requestedViewId = toPositiveInt(route.query.view_id) || toPositiveInt(route.query.viewId) || 0;
  let response: Awaited<ReturnType<typeof loadActionContractRaw>> | null = null;
  if (actionId.value) {
    try {
      response = await loadActionContractRaw(actionId.value, {
        menuId: menuId.value || undefined,
        viewId: requestedViewId || undefined,
        recordId: recordId.value,
        renderProfile: profile,
        surface: requestedSurface.value,
        sourceMode: requestedSourceMode.value,
        context: contractContext,
        contextRaw,
      });
      const actionReadiness = analyzeFormContractReadiness(response?.data, { requirePureFormViewType: true });
      const actionModel = contractModelName(response?.data);
      if (!actionReadiness.usable || (currentModel && actionModel && actionModel !== currentModel)) {
        response = null;
      }
    } catch {
      response = null;
    }
  }
  if (!response && currentModel) {
    response = await loadModelContractRaw(currentModel, {
      viewType: 'form',
      viewId: requestedViewId || undefined,
      recordId: recordId.value,
      renderProfile: profile,
      surface: requestedSurface.value,
      sourceMode: requestedSourceMode.value,
      context: contractContext,
      contextRaw,
    });
  }
  if (!response?.data || typeof response.data !== 'object') {
    throw new Error('表单配置返回为空');
  }
  const markerCheck = validateSurfaceMarkers(
    response.data,
    (response.meta as Record<string, unknown> | null) || null,
    requestedSurface.value,
  );
  if (!markerCheck.ok) {
    throw new Error(`表单配置标记不完整：${markerCheck.issues.slice(0, 4).join(' | ')}`);
  }
  const readiness = analyzeFormContractReadiness(response.data, { requirePureFormViewType: false });
  if (!readiness.usable) {
    throw new Error(`表单配置暂不可渲染：${readiness.issues.slice(0, 4).join(' | ')}`);
  }
  contract.value = response.data as ActionContract;
  contractMeta.value = response.meta || null;
  syncContractV2ShadowStore(response.data);
  mergeNativeLayoutFieldDescriptorsIntoContract();
  const policy = contractAccessPolicy.value;
  if (policy.mode === 'block') {
    const message = policy.message || 'contract access policy blocked this page';
    throw new ContractAccessPolicyError(message, policy.reasonCode || 'CONTRACT_ACCESS_BLOCKED');
  }
  const hasCore = coreFieldNames.value.length > 0;
  advancedExpanded.value = renderProfile.value !== 'create' || !hasCore;
}

async function loadRecord() {
  const versionPolicy = recordVersionPolicy();
  const fieldNames = formDataFieldNames();
  if (versionPolicy?.tokenField && !fieldNames.includes(versionPolicy.tokenField)) {
    fieldNames.push(versionPolicy.tokenField);
  }
  recordVersionToken.value = '';
  closeNativeChatterComposer();
  clearNativeChatterForRecordLoad();
  clearNativeAttachmentError();
  if (!recordId.value) {
    clearPendingNativeAttachments();
    nativeChatterAutoLoadKey.value = '';
  }
  Object.keys(formData).forEach((key) => {
    delete formData[key];
  });
  Object.keys(relationKeywords).forEach((key) => {
    delete relationKeywords[key];
  });
  relationOptions.value = {};
  clearOne2manyRows();
  onchangeModifiersPatch.value = {};
  onchangeWarnings.value = [];
  onchangeLinePatches.value = [];
  changedFieldSet.clear();
  dirtyFieldSet.clear();
  if (onchangeTimer) {
    clearTimeout(onchangeTimer);
    onchangeTimer = null;
  }
  const hydrationTarget: FormRecordHydrationTarget = {
    formData,
    relationOptions: relationOptions.value,
    relationKeywords,
    upsertRelationOption,
    initOne2manyRows,
  };
  if (!recordId.value) {
    const defaults = resolveCreateDefaults();
    fieldNames.forEach((name) => {
      applyIncomingFormFieldValue({
        fieldName: name,
        descriptor: contract.value?.fields?.[name],
        incoming: name in defaults ? defaults[name] : '',
        target: hydrationTarget,
      });
    });
    originalValues.value = snapshotOriginalFormValues(fieldNames, formData);
    nativeLayoutVisibilityRevision.value += 1;
    restoreIntakeAutosave();
    return;
  }
  const read = await readContractFormRecord({
    model: model.value,
    ids: [recordId.value],
    fields: fieldNames.length ? fieldNames : '*',
  });
  const row = read.records?.[0] || {};
  const storeMainData = resolveContractV2MainData(v2ContractStore.value);
  const contractMainData = Object.keys(storeMainData).length ? storeMainData : resolveUnifiedPageContractV2MainData(contract.value);
  if (versionPolicy?.tokenField) {
    recordVersionToken.value = String((row as Record<string, unknown>)[versionPolicy.tokenField] || '').trim();
  }
  fieldNames.forEach((name) => {
    if (name === versionPolicy?.tokenField && !contract.value?.fields?.[name]) return;
    const incoming = Object.prototype.hasOwnProperty.call(row, name)
      ? (row as Record<string, unknown>)[name]
      : (contractMainData[name] ?? '');
    applyIncomingFormFieldValue({
      fieldName: name,
      descriptor: contract.value?.fields?.[name],
      incoming,
      target: hydrationTarget,
    });
  });
  originalValues.value = snapshotOriginalFormValues(fieldNames, formData);
  nativeLayoutVisibilityRevision.value += 1;
  if (recordId.value && (nativeChatterActions.value.length || nativeAttachments.value)) {
    await loadNativeChatterTimeline(recordId.value, model.value);
  }
}

function handleSceneBlockAction(payload: { action?: { target?: Record<string, unknown> } }) {
  const target = payload?.action?.target && typeof payload.action.target === 'object'
    ? payload.action.target
    : {};
  const targetKind = String(target.kind || '').trim();
  if (targetKind === 'statusbar_value') {
    const value = String(target.value || '').trim();
    if (value) {
      setStatusbarValue(value);
      return;
    }
  }
  const route = String(target.route || '').trim();
  if (route) {
    void router.push(route);
    return;
  }
  const sceneKey = String(target.scene_key || '').trim();
  if (sceneKey) {
    void router.push({ name: 'scene', params: { sceneKey } });
  }
}

async function reload() {
  const reloadIdentity = formRouteIdentity();
  if (activeReloadPromise && reloadIdentity && reloadIdentity === activeReloadIdentity) {
    return activeReloadPromise;
  }
  const run = (async () => {
    const reloadToken = activeReloadToken + 1;
    activeReloadToken = reloadToken;
    renderErrorMessage.value = '';
    status.value = 'loading';
    errorMessage.value = '';
    validationErrors.value = [];
    showOne2manyErrors.value = false;
    try {
      await loadContract();
      if (reloadToken !== activeReloadToken) return;
      await loadRecord();
      if (reloadToken !== activeReloadToken) return;
      status.value = 'ok';
      retainedRouteIdentity.value = formRouteIdentity();
      void preloadFormAuxiliaryData(reloadToken);
    } catch (err) {
      if (reloadToken !== activeReloadToken) return;
      if (err instanceof ContractAccessPolicyError) {
        await router.push({
          name: 'workbench',
          query: pickContractNavQuery(route.query as Record<string, unknown>, {
            reason: ErrorCodes.CAPABILITY_MISSING,
            action_id: actionId.value || undefined,
            menu_id: Number(route.query.menu_id || 0) || undefined,
            diag: showHud.value ? (err.reasonCode || 'CONTRACT_ACCESS_BLOCKED') : undefined,
          }),
        });
        return;
      }
      errorMessage.value = err instanceof Error ? err.message : '表单加载失败';
      status.value = 'error';
    } finally {
      if (activeReloadIdentity === reloadIdentity) {
        activeReloadPromise = null;
        activeReloadIdentity = '';
      }
    }
  })();
  activeReloadIdentity = reloadIdentity;
  activeReloadPromise = run;
  return run;
}

function ensureFormInitialReload() {
  const identity = formRouteIdentity();
  if (!identity) return;
  if (identity === retainedRouteIdentity.value && status.value === 'ok') return;
  if (status.value === 'loading' || !contract.value) {
    void reload();
  }
}

async function preloadFormAuxiliaryData(reloadToken: number) {
  try {
    await loadRelationOptions();
    if (reloadToken !== activeReloadToken) return;
    await hydrateSelectedRelationOptions();
    if (reloadToken !== activeReloadToken) return;
    await hydrateVisibleOne2manyRows();
  } catch {
    // Auxiliary data can be completed by explicit field interactions after the form renders.
  }
}

async function discardChanges() {
  if (!hasChanges.value || busy.value) return;
  await reload();
}

onErrorCaptured((err) => {
  const message = err instanceof Error ? err.message : String(err || '系统处理问题');
  renderErrorMessage.value = `表单页面打开失败：${message}`;
  return false;
});

async function confirmActionSafety(action: ContractAction) {
  const safety = action.actionSafety;
  if (!safety || safety.classification !== 'danger' || !safety.requiresConfirm) return true;
  const message = safety.confirmMessage || action.hint || action.label;
  return actionSafetyConfirm.open({
    title: '确认执行操作',
    message: String(message || '该操作执行后将立即生效，请确认是否继续。'),
    confirmLabel: '继续',
    cancelLabel: '取消',
    tone: 'danger',
  });
}

async function ensureSavedBeforeRecordAction() {
  if (!hasChanges.value) return true;
  return Boolean(await saveRecord({ on_success: ['scene_projection'] }));
}

function applyClientMode(mode: string, toggle = true) {
  const next = String(mode || '').trim();
  if (!next) return false;
  activeContractMode.value = toggle && activeContractMode.value === next ? '' : next;
  contractModeFeedback.value = '';
  if (!activeContractMode.value) closeContractPromptAction();
  return true;
}

function applyRouteConfigMode(rawMode: unknown) {
  const mode = String(rawMode || '').trim();
  if (isBusinessConfigRuntimeModel(model.value)) {
    if (activeContractMode.value === BUSINESS_CONFIG_MODES.formFieldConfiguration || activeContractMode.value === BUSINESS_CONFIG_MODES.lowCode) {
      activeContractMode.value = '';
    }
    return;
  }
  if (isBusinessConfigMode(mode)) {
    applyClientMode(mode, false);
  }
}

async function onContractFieldAction(payload: FormSectionFieldActionPayload) {
  const fieldKey = String(payload.field.name || '').trim();
  const actionValue = String(payload.action.value || '').trim();
  if (isContractFieldOrderEditable.value && fieldKey && ['show', 'hide'].includes(actionValue)) {
    fieldVisibilityDraft[fieldKey] = actionValue === 'show';
    fieldVisibilityDirtyKeys[fieldKey] = true;
    formConfigAuditResult.value = null;
    appendFormConfigOperation(actionValue === 'show' ? '显示字段' : '隐藏字段', `${formDesignFieldLabel(fieldKey)} 设置为${actionValue === 'show' ? '显示' : '隐藏'}`);
    contractModeFeedback.value = '字段显示设置已调整，保存后生效';
    return;
  }
  const raw = payload.action.raw;
  if (!raw) return;
  await runContractRuleAction(raw);
}

function onFormSettingsFieldSelect(payload: { field: FormSectionFieldSchema; groupTitle: string }) {
  if (!isContractFieldOrderEditable.value) return;
  const fieldKey = String(payload.field.name || payload.field.key || '').trim();
  if (!fieldKey) return;
  rememberFormConfigFieldLabel(fieldKey, payload.field.label);
  if (!Object.prototype.hasOwnProperty.call(fieldVisibilityBase.value, fieldKey)) {
    const row = activeContractModeFieldRows.value.find((item) => item.fieldKey === fieldKey);
    const checkedAction = row?.actions.find((action) => Boolean(action.checked));
    fieldVisibilityBase.value = {
      ...fieldVisibilityBase.value,
      [fieldKey]: checkedAction ? checkedAction.value === 'show' : true,
    };
    if (!Object.prototype.hasOwnProperty.call(fieldVisibilityDraft, fieldKey)) {
      fieldVisibilityDraft[fieldKey] = checkedAction ? checkedAction.value === 'show' : true;
    }
  }
  selectedFormSettingsFieldKey.value = fieldKey;
  selectedFormSettingsFieldLabel.value = String(payload.field.label || fieldKey).trim();
  selectedFormSettingsFieldGroupTitleDraft.value = (
    effectiveFieldGroupTitleForDraft(fieldKey)
    || normalizeFieldGroupTitle(payload.groupTitle)
  );
  selectedFormSettingsFieldGroupTitleEdit.value = selectedFormSettingsFieldGroupTitleDraft.value;
  formSettingsActiveTab.value = 'fields';
}

function selectFormDesignerGroup(title: string) {
  const normalizedTitle = normalizeFieldGroupTitle(title);
  if (!normalizedTitle) return;
  const group = formDesignerGroupNavigatorItems.value.find((item) => fieldGroupTitleMatches(item.title, normalizedTitle));
  const orderedKeys = currentFormOrderedFieldKeys.value.length ? currentFormOrderedFieldKeys.value : currentFormDesignFieldKeys.value;
  const fieldKey = orderedKeys.find((key) => group?.fieldKeys.includes(key)) || group?.fieldKeys[0] || '';
  if (!fieldKey) return;
  onFormSettingsFieldSelect({
    field: {
      name: fieldKey,
      key: fieldKey,
      label: formDesignFieldLabel(fieldKey),
    } as FormSectionFieldSchema,
    groupTitle: normalizedTitle,
  });
}

function selectFormDesignerField(fieldKey: string) {
  const key = String(fieldKey || '').trim();
  if (!key) return;
  onFormSettingsFieldSelect({
    field: {
      name: key,
      key,
      label: formDesignFieldLabel(key),
    } as FormSectionFieldSchema,
    groupTitle: effectiveFieldGroupTitleForDraft(key) || '业务配置字段',
  });
}

async function onSelectedFormSettingsGroupTitleChange(event: Event) {
  const oldTitle = selectedFormSettingsFieldGroupTitle.value;
  const target = event.target as HTMLInputElement | null;
  const newTitle = String(selectedFormSettingsFieldGroupTitleEdit.value || target?.value || '').trim();
  if (!oldTitle || !newTitle || oldTitle === newTitle) {
    selectedFormSettingsFieldGroupTitleEdit.value = oldTitle;
    return;
  }
  await onContractInlineGroupRename({ oldTitle, newTitle });
}

async function onSelectedFormSettingsFieldLabelChange(event: Event) {
  const fieldKey = selectedFormSettingsFieldKey.value;
  const target = event.target as HTMLInputElement | null;
  const label = String(target?.value || '').trim();
  if (!fieldKey || !label || label === selectedFormSettingsFieldRow.value?.label) return;
  selectedFormSettingsFieldLabel.value = label;
  await setInlineFieldPolicy(fieldKey, { label });
}

function contractInlineFieldOrderIndex(field: FormSectionFieldSchema) {
  const fieldKey = String(field.name || '').trim();
  if (!fieldKey) return -1;
  return fieldOrderDraft.value.indexOf(fieldKey);
}

function onContractInlineFieldOrderMove(payload: { field: FormSectionFieldSchema; delta: number }) {
  const fieldKey = String(payload.field.name || '').trim();
  if (!fieldKey) return;
  moveFieldOrder(fieldKey, payload.delta);
}

function onContractInlineFieldOrderDragStart(payload: { field: FormSectionFieldSchema; event: DragEvent }) {
  const fieldKey = String(payload.field.name || '').trim();
  if (!fieldKey) return;
  rememberFormConfigFieldLabel(fieldKey, payload.field.label);
  const fieldLabel = String(payload.field.label || '').trim();
  draggingFieldLabel.value = fieldLabel && fieldLabel !== fieldKey ? fieldLabel : formDesignFieldLabel(fieldKey);
  onFieldOrderDragStart(fieldKey, payload.event);
}

function onContractInlineFieldOrderDragOver(payload: { field: FormSectionFieldSchema; groupTitle?: string; placement?: 'before' | 'after' | '' }) {
  const fieldKey = String(payload.field.name || '').trim();
  if (!fieldKey) return;
  rememberFormConfigFieldLabel(fieldKey, payload.field.label);
  onFieldOrderDragOver(fieldKey, payload.placement);
}

function onContractInlineFieldOrderDragLeave(payload: { field: FormSectionFieldSchema; groupTitle?: string }) {
  const fieldKey = String(payload.field.name || '').trim();
  if (!fieldKey) return;
  onFieldOrderDragLeave(fieldKey);
}

function onContractInlineFieldOrderDrop(payload: { field: FormSectionFieldSchema; groupTitle?: string; placement?: 'before' | 'after' | '' }) {
  const fieldKey = String(payload.field.name || '').trim();
  if (!fieldKey) return;
  rememberFormConfigFieldLabel(fieldKey, payload.field.label);
  onFieldOrderDrop(fieldKey, payload.groupTitle, payload.placement);
}

function onContractInlineFieldOrderGroupDrop(payload: { groupTitle: string; groupIndex?: number }) {
  onFieldOrderGroupDrop(payload.groupTitle);
}

function onContractInlineFieldOrderDragEnd() {
  onFieldOrderDragEnd();
}

function lowCodeApplyBaseParams() {
  const configAction = contractV2ActionRules().find((rule) => contractActionRuleKey(rule) === BUSINESS_CONFIG_ACTION_KEYS.currentFormFieldOrderSave);
  const target = parseMaybeJsonRecord(configAction?.target);
  return buildLowCodeApplyBaseParams({
    actionId: actionId.value || route.query.action_id,
    viewId: routeQueryText('view_id') || routeQueryText('viewId'),
    targetParams: parseMaybeJsonRecord(target.params),
    modelName: String(model.value || ''),
  });
}

function contractFieldSequence(fieldKey: string, fallback = 100) {
  return contractFieldSequenceFromOrder(fieldOrderDraft.value, fieldKey, fallback);
}

function fieldGroupTitleForDraft(fieldKey: string) {
  return effectiveFieldGroupTitleForDraft(fieldKey);
}

function routeQueryText(key: string) {
  const value = route.query[key];
  if (Array.isArray(value)) return String(value[0] || '').trim();
  return String(value || '').trim();
}

function lowCodeReturnQuery() {
  return buildLowCodeReturnQuery({
    routeQuery: route.query as Record<string, unknown>,
    modelName: model.value,
    actionId: actionId.value,
    openPagesFlag: BUSINESS_CONFIG_ROUTE_FLAGS.openPages,
  });
}

function previewLowCodeConfiguredPage() {
  const query = buildLowCodePreviewQuery({
    routeQuery: route.query as Record<string, unknown>,
    returnToBusinessConfigFlag: BUSINESS_CONFIG_ROUTE_FLAGS.returnToBusinessConfig,
    openPagesFlag: BUSINESS_CONFIG_ROUTE_FLAGS.openPages,
  });
  router.push({ path: route.path, query });
}

async function previewCurrentFormConfiguration() {
  if (hasCurrentFormFieldDraftChanges.value) {
    const saved = await saveContractFieldOrder();
    if (!saved) return;
  }
  previewLowCodeConfiguredPage();
}

function returnToBusinessConfigDesigner() {
  router.push({
    path: '/admin/business-config',
    query: lowCodeReturnQuery(),
  });
}

function formConfigSaveOperationSummary(changedVisibility: Record<string, boolean>, changedGroups: Record<string, string>) {
  return formConfigSaveOperationSummaryFromDraft({
    hasFieldOrderChanges: hasFieldOrderChanges.value,
    changedVisibility,
    changedGroups,
    hasFormLayoutChanges: hasFormLayoutChanges.value,
    hasGroupLayoutChanges: hasGroupLayoutChanges.value,
    hasFieldLayoutChanges: hasFieldLayoutChanges.value,
  });
}

async function saveContractFieldOrder() {
  if (!hasCurrentFormFieldDraftChanges.value) return true;
  const configAction = contractV2ActionRules().find((rule) => contractActionRuleKey(rule) === BUSINESS_CONFIG_ACTION_KEYS.currentFormFieldOrderSave);
  const target = parseMaybeJsonRecord(configAction?.target);
  const baseParams = normalizeLowCodeApplyParams(parseMaybeJsonRecord(target.params));
  const changedVisibility = changedFieldVisibilityDraft();
  const changedGroups = changedFieldGroupDraft();
  const saveOperationSummary = formConfigSaveOperationSummary(changedVisibility, changedGroups);
  const applyParams: Record<string, unknown> = { ...baseParams };
  if (hasFieldOrderChanges.value) {
    applyParams.field_order = [...fieldOrderDraft.value];
  }
  if (Object.keys(changedGroups).length) {
    applyParams.field_groups = changedGroups;
  }
  if (Object.keys(changedVisibility).length) {
    applyParams.field_visibility = changedVisibility;
  }
  const hasFieldApplyParams = 'field_order' in applyParams || 'field_visibility' in applyParams || 'field_groups' in applyParams;
  if (!hasFieldApplyParams && !hasFormLayoutChanges.value && !hasGroupLayoutChanges.value && !hasFieldLayoutChanges.value) {
    fieldVisibilityDirty.value = false;
    contractModeFeedback.value = '';
    return true;
  }
  busyKind.value = 'action';
  try {
    if (hasFieldApplyParams) {
      await intentRequest({
        intent: BUSINESS_CONFIG_INTENTS.lowCodeApply,
        params: applyParams,
        context: { view: 'form' },
      });
    }
    const saveResult = await intentRequest<{
      precheck?: { warnings?: string[]; errors?: string[] }
    }>({
      intent: BUSINESS_CONFIG_INTENTS.contractSave,
      params: {
        ...baseParams,
        name: lowCodeScopedContractName(String(model.value || 'unknown'), baseParams),
        model: String(model.value || ''),
        view_type: 'form',
        publish: true,
        contract_json: {
          view_orchestration: buildLowCodeViewOrchestration(),
        },
      },
    });
    const warnings = Array.isArray(saveResult?.precheck?.warnings) ? saveResult.precheck?.warnings || [] : [];
    lowCodePrecheckWarnings.value = warnings.map((item) => String(item || '').trim()).filter(Boolean);
    if (Object.keys(changedVisibility).length) {
      fieldVisibilityBase.value = {
        ...fieldVisibilityBase.value,
        ...changedVisibility,
      };
      Object.keys(changedVisibility).forEach((key) => {
        delete fieldVisibilityDirtyKeys[key];
      });
    }
    if (Object.keys(changedGroups).length) {
      fieldGroupSavedBase.value = {
        ...fieldGroupSavedBase.value,
        ...changedGroups,
      };
      fieldGroupBase.value = {
        ...fieldGroupBase.value,
        ...changedGroups,
      };
    }
    formLayoutColumnsBase.value = formLayoutColumnsDraft.value;
    groupVisibilityBase.value = { ...groupVisibilityDraft };
    groupColumnsBase.value = { ...groupColumnsDraft };
    fieldSizeBase.value = { ...fieldSizeDraft };
    formLayoutDirty.value = false;
    Object.keys(groupLayoutDirtyKeys).forEach((key) => delete groupLayoutDirtyKeys[key]);
    Object.keys(fieldLayoutDirtyKeys).forEach((key) => delete fieldLayoutDirtyKeys[key]);
    fieldVisibilityDirty.value = false;
    lowCodeContractLoaded.value = false;
    formConfigAuditResult.value = null;
    contractModeFeedback.value = '表单设置已保存并发布，刷新页面后按新配置生效';
    markPendingFormConfigOperations('saved');
    appendFormConfigOperation('保存发布', saveOperationSummary, 'done');
    await reload();
    await hydrateLowCodeDraftFromContract();
    return true;
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : '表单字段顺序更新失败';
    status.value = 'error';
    return false;
  } finally {
    busyKind.value = null;
  }
}

async function runAction(action: ContractAction) {
  if (!action.enabled) return;
  if (!await confirmActionSafety(action)) return;
  if (action.intent === 'ui.local_mode' || action.intent === 'ui.mode' || action.clientMode) {
    applyClientMode(action.clientMode, true);
    return;
  }
  const actionKey = String(action.key || '').trim().toLowerCase();
  if (actionKey === 'submit_intake' || actionKey === 'save_draft') {
    await saveRecord(action.refreshPolicy);
    return;
  }
  if (actionKey === 'cancel' && !action.methodName) {
    await router.push({
      name: 'workbench',
      query: pickContractNavQuery(route.query as Record<string, unknown>, {
        scene: undefined,
      }),
    });
    return;
  }
  if (action.kind === 'open') {
    if (action.actionId) {
      await router.push({
        name: 'action',
        params: { actionId: String(action.actionId) },
        query: pickContractNavQuery(route.query as Record<string, unknown>, {
          action_id: action.actionId,
          target: action.target || undefined,
          domain_raw: action.domainRaw || undefined,
        }),
      });
      return;
    }
    if (action.url) {
      const navUrl = resolveNavigationUrl(action.url);
      window.open(navUrl, action.target === 'self' ? '_self' : '_blank', 'noopener,noreferrer');
      return;
    }
    errorMessage.value = '打开操作缺少目标页面';
    status.value = 'error';
    return;
  }
  if (action.mutation) {
    const params = await collectActionParams(action);
    if (params === null) return;
    busyKind.value = 'action';
    try {
      await executeSceneMutation({
        mutation: action.mutation,
        actionKey: action.key,
        recordId: recordId.value,
        model: action.targetModel || model.value,
        context: action.context,
        params,
      });
      submissionFeedback.value = {
        kind: 'success',
        message: '操作已完成，页面数据已刷新。',
      };
      await applyProjectionRefreshPolicy(action.refreshPolicy);
      return;
    } catch (err) {
      errorMessage.value = err instanceof Error ? err.message : '场景操作执行失败';
      status.value = 'error';
      return;
    } finally {
      busyKind.value = null;
    }
  }
  if ((action.kind === 'object' || action.kind === 'server') && action.methodName && recordId.value) {
    if (!await ensureSavedBeforeRecordAction()) return;
    busyKind.value = 'action';
    try {
      const response = await executeButton({
        model: action.targetModel || model.value,
        res_id: recordId.value,
        button: { name: action.methodName, type: action.kind === 'server' ? 'server' : 'object' },
        context: action.context,
        meta: {
          menu_id: Number(route.query.menu_id || 0) || undefined,
          action_id: actionId.value || undefined,
        },
      });
      const result = response?.result;
      if (result?.entry_target) {
        await router.push(actionResponseRouteTarget(buildEntryTargetRouteTarget(result.entry_target, {
          query: actionResponseNavQuery(result),
          actionId: result.action_id,
        }), result) as never);
        if (action.refreshPolicy) {
          await applyProjectionRefreshPolicy(action.refreshPolicy);
        }
        return;
      }
      const nextActionId = toPositiveInt(result?.action_id);
      if (nextActionId) {
        await router.push({
          name: 'action',
          params: { actionId: String(nextActionId) },
          query: actionResponseNavQuery(result, { action_id: nextActionId }),
        });
        if (action.refreshPolicy) {
          await applyProjectionRefreshPolicy(action.refreshPolicy);
        }
        return;
      }
      const refresh = result?.type;
      if (refresh === 'refresh' && !action.refreshPolicy) {
        await reload();
        return;
      }
      if (action.refreshPolicy) {
        await applyProjectionRefreshPolicy(action.refreshPolicy);
      } else {
        await reload();
      }
      return;
    } catch (err) {
      errorMessage.value = err instanceof Error ? err.message : '操作执行失败';
      status.value = 'error';
    } finally {
      busyKind.value = null;
    }
  }
}

async function runPrimaryFormAction() {
  const footerAction = primaryCreateFooterAction.value;
  if (footerAction) {
    const saved = await saveRecord(footerAction.refreshPolicy);
    if (!saved) return;
    await nextTick();
    const submittedRecordId = typeof saved === 'number' ? saved : recordId.value;
    if (!submittedRecordId) {
      errorMessage.value = '操作失败：请先保存记录后再执行';
      status.value = 'error';
      return;
    }
    await executePrimarySubmitAction({
      ...footerAction,
      enabled: true,
      hint: '',
    }, submittedRecordId);
    return;
  }
  const submitAction = primarySubmitAction.value;
  if (!submitAction) {
    await saveRecord();
    return;
  }
  const saved = await saveRecord(submitAction.refreshPolicy);
  if (!saved) return;
  await nextTick();
  const submittedRecordId = typeof saved === 'number' ? saved : recordId.value;
  if (!submittedRecordId) {
    errorMessage.value = '提交失败：请先保存记录后再提交';
    status.value = 'error';
    return;
  }
  await executePrimarySubmitAction({
    ...submitAction,
    enabled: true,
    hint: '',
  }, submittedRecordId);
}

async function executePrimarySubmitAction(action: ContractAction, resId: number) {
  if (!await confirmActionSafety(action)) return;
  busyKind.value = 'action';
  try {
    const response = await executeButton({
      model: action.targetModel || model.value,
      res_id: resId,
      button: { name: action.methodName, type: action.kind === 'server' ? 'server' : 'object' },
      context: action.context,
      meta: {
        menu_id: Number(route.query.menu_id || 0) || undefined,
        action_id: actionId.value || undefined,
      },
    });
    const result = response?.result;
    if (result?.entry_target) {
      await router.push(actionResponseRouteTarget(buildEntryTargetRouteTarget(result.entry_target, {
        query: actionResponseNavQuery(result),
        actionId: result.action_id,
      }), result) as never);
      return;
    }
    const nextActionId = toPositiveInt(result?.action_id);
    if (nextActionId) {
      await router.push({
        name: 'action',
        params: { actionId: String(nextActionId) },
        query: actionResponseNavQuery(result, { action_id: nextActionId }),
      });
      return;
    }
    submissionFeedback.value = { kind: 'success', message: '提交成功' };
    await applyProjectionRefreshPolicy(action.refreshPolicy || { on_success: ['scene_projection'] });
    await reload();
  } catch (err) {
    const message = sanitizeUiErrorMessage(err instanceof Error ? err.message : err, '提交失败，请检查填写内容');
    validationErrors.value = [message];
    submissionFeedback.value = { kind: 'error', message: '提交失败，请检查填写内容' };
    status.value = 'error';
  } finally {
    busyKind.value = null;
  }
}

function isTierValidationActionHidden(methodName: string): boolean {
  return isTierValidationActionHiddenFromState({
    methodName,
    validationStatus: formData.validation_status,
    canReview: formData.can_review,
  });
}

async function applyProjectionRefreshPolicy(policy?: ContractAction['refreshPolicy']) {
  if (!policy || !Array.isArray(policy.on_success) || !policy.on_success.length) {
    return;
  }
  await executeProjectionRefresh({
    policy,
    refreshScene: async () => {
      await reload();
    },
    refreshWorkbench: async () => {
      await session.loadAppInit();
    },
    refreshRoleSurface: async () => {
      await session.loadAppInit();
    },
    recordTrace: ({ intent, writeMode, latencyMs }) => {
      session.recordIntentTrace({ intent, writeMode, latencyMs });
    },
  });
}

async function openFilter(filterKey: string) {
  if (!actionId.value) return;
  const selected = searchFilters.value.find((item) => item.key === filterKey);
  activeFilterKey.value = filterKey;
  await router.push({
    name: 'action',
    params: { actionId: String(actionId.value) },
    query: pickContractNavQuery(route.query as Record<string, unknown>, {
      action_id: actionId.value,
      preset_filter: filterKey,
      domain_raw: selected?.domainRaw || undefined,
      context_raw: selected?.contextRaw || undefined,
    }),
  });
}

async function cancelIntake() {
  if (!isProjectIntakeCreateMode.value) return;
  const target = session.resolveLandingPath('/');
  await router.replace({ path: target, query: resolveWorkspaceContextQuery() });
}

async function returnToProjectIntakeList(createdId: number | string) {
  const queryActionId = Number(route.query.action_id || actionId.value || 0) || 0;
  if (queryActionId > 0) {
    await router.replace({
      path: `/a/${queryActionId}`,
      query: pickContractNavQuery(route.query as Record<string, unknown>, {
        project_id: String(createdId),
        view_mode: 'tree',
      }),
    });
    return true;
  }
  return false;
}

async function saveRecord(refreshPolicy?: ContractAction['refreshPolicy']): Promise<boolean | number> {
  if (!canSave.value || !model.value) return false;
  submissionFeedback.value = null;
  validationErrors.value = [];
  const standardCreateMode = isProjectStandardIntakeMode.value;
  if (standardCreateMode) {
    const draftErrors: string[] = [];
    const projectName = String(formData.name || '').trim();
    const managerId = Number(formData.manager_id || 0);
    if (!projectName) draftErrors.push('请填写项目名称');
    if (!Number.isFinite(managerId) || managerId <= 0) draftErrors.push('请填写项目经理');
    if (draftErrors.length) {
      validationErrors.value = draftErrors;
      submissionFeedback.value = { kind: 'warn', message: '创建失败，请检查填写内容' };
      return false;
    }
  }
  const one2manyIssues = one2manyValidation.value.issues;
  if (one2manyIssues.length) {
    showOne2manyErrors.value = true;
    validationErrors.value = one2manyIssues.slice(0, 5);
    submissionFeedback.value = { kind: 'warn', message: '创建失败，请检查填写内容' };
    return false;
  }
  showOne2manyErrors.value = false;
  const labels = layoutNodes.value.reduce<Record<string, string>>((acc, node) => {
    if (node.kind === 'field') acc[node.name] = node.label || node.name;
    return acc;
  }, {});
  const scenePrecheckIssues = collectSceneValidationPrecheckErrors(labels);
  if (scenePrecheckIssues.length) {
    validationErrors.value = scenePrecheckIssues;
    submissionFeedback.value = { kind: 'warn', message: '创建失败，请检查填写内容' };
    return false;
  }
  const relationCreateIssues = await resolvePendingInlineRelationCreates();
  if (relationCreateIssues.length) {
    validationErrors.value = relationCreateIssues;
    submissionFeedback.value = { kind: 'warn', message: '创建失败，请检查填写内容' };
    return false;
  }
  const tagCreateIssues = await resolvePendingMany2manyTagCreates();
  if (tagCreateIssues.length) {
    validationErrors.value = tagCreateIssues;
    submissionFeedback.value = { kind: 'warn', message: '创建失败，请检查填写内容' };
    return false;
  }
  const editableMap = collectWritableValues();
  if (!recordId.value) {
    const requiredIssues = collectRequiredFieldIssues(editableMap);
    if (requiredIssues.length) {
      validationErrors.value = requiredIssues;
      submissionFeedback.value = { kind: 'warn', message: '请先补充必填信息，再保存草稿或提交。' };
      return false;
    }
  }
  if (!standardCreateMode) {
    const issues = validateContractFormData({
      contract: contract.value,
      fieldLabels: labels,
      values: editableMap,
    });
    const basePolicyIssues = collectPolicyValidationErrors(contract.value, policyContext.value);
    const submittedPolicyIssues = collectPolicyValidationErrors(contract.value, {
      ...policyContext.value,
      submittedFields: new Set(Object.keys(editableMap)),
    });
    const policyIssues = [...basePolicyIssues, ...submittedPolicyIssues];
    if (policyIssues.length) {
      validationErrors.value = Array.from(new Set(policyIssues)).slice(0, 5);
      submissionFeedback.value = { kind: 'warn', message: '请先补充必填信息，再保存草稿或提交。' };
      return false;
    }
    if (issues.length) {
      validationErrors.value = Array.from(new Set(issues.map((item) => item.message))).slice(0, 5);
      submissionFeedback.value = { kind: 'warn', message: '请先补充必填信息，再保存草稿或提交。' };
      return false;
    }
  }
  busyKind.value = 'save';
  try {
    const values = Object.entries(editableMap).reduce<Record<string, unknown>>((acc, [key, value]) => {
      if (!recordId.value) {
        acc[key] = value;
        return acc;
      }
      const ttype = fieldType(contract.value?.fields?.[key]);
      if (ttype === 'many2many' || ttype === 'one2many') {
        if (Array.isArray(value) && value.length) {
          acc[key] = value;
        }
        return acc;
      }
      if (!dirtyFieldSet.has(key)) {
        return acc;
      }
      if (comparableFieldValue(key, formData[key]) !== comparableFieldValue(key, originalValues.value[key])) {
        acc[key] = value;
      }
      return acc;
    }, {});
    if (recordId.value && !Object.keys(values).length) {
      busyKind.value = null;
      dirtyFieldSet.clear();
      return true;
    }
    if (recordId.value) {
      await writeContractFormRecord({
        model: model.value,
        ids: [recordId.value],
        vals: values,
        ifMatch: recordVersionPolicy() ? recordVersionToken.value : undefined,
      });
      submissionFeedback.value = { kind: 'success', message: formUiLabel('save_success') };
      dirtyFieldSet.clear();
      await applyProjectionRefreshPolicy(refreshPolicy || { on_success: ['scene_projection'] });
      return true;
    }
    const created = await createContractFormRecord({ model: model.value, vals: values, context: formCreateContext() });
    if (created?.id) {
      const attachmentsUploaded = await uploadPendingNativeAttachments(Number(created.id));
      if (!attachmentsUploaded) {
        return false;
      }
      const title = String(contract.value?.head?.title || '').trim();
      submissionFeedback.value = { kind: 'success', message: `${title || '记录'}已创建` };
      clearIntakeAutosave();
      const nextSceneRoute = String(sceneReadyFormSurface.value.nextSceneRoute || '').trim();
      const nextSceneKey = String(sceneReadyFormSurface.value.nextSceneKey || '').trim();
      const resolvedNextRoute = nextSceneRoute || (nextSceneKey ? `/s/${nextSceneKey}` : '');
      if (isProjectQuickIntakeMode.value && model.value === 'project.project') {
        await applyProjectionRefreshPolicy(refreshPolicy || { on_success: ['scene_projection', 'workbench_projection'] });
        if (await returnToProjectIntakeList(created.id)) return;
        const routePath = resolvedNextRoute || '/s/project.management';
        await router.replace({
          path: routePath,
          query: {
            project_id: String(created.id),
            ...resolveWorkspaceContextQuery(),
          },
        });
        return true;
      }
      if (isProjectStandardIntakeMode.value && resolvedNextRoute) {
        await applyProjectionRefreshPolicy(refreshPolicy || { on_success: ['scene_projection', 'workbench_projection'] });
        if (await returnToProjectIntakeList(created.id)) return true;
        await router.replace({
          path: resolvedNextRoute,
          query: {
            project_id: String(created.id),
            ...resolveWorkspaceContextQuery(),
          },
        });
        return true;
      }
      if (isProjectStandardIntakeMode.value && model.value === 'project.project') {
        await applyProjectionRefreshPolicy(refreshPolicy || { on_success: ['scene_projection', 'workbench_projection'] });
        if (await returnToProjectIntakeList(created.id)) return true;
      }
      const createdRoute = router.resolve({
        name: 'model-form',
        params: { model: model.value, id: String(created.id) },
        query: pickContractNavQuery(route.query as Record<string, unknown>),
      });
      window.location.replace(new URL(createdRoute.href, window.location.origin).toString());
      await new Promise<never>(() => {});
    }
  } catch (err) {
    const fallback = recordId.value ? '保存失败，请检查填写内容' : '创建失败，请检查填写内容';
    const message = sanitizeUiErrorMessage(err instanceof Error ? err.message : err, fallback);
    validationErrors.value = [message];
    submissionFeedback.value = { kind: 'error', message: message && message !== fallback ? message : fallback };
    return false;
  } finally {
    busyKind.value = null;
  }
  return false;
}

async function copyContractJson() {
  if (!contract.value) return;
  const payload = JSON.stringify(
    {
      action_id: actionId.value,
      model: model.value,
      contract: contract.value,
      meta: contractMeta.value || {},
    },
    null,
    2,
  );
  try {
    await navigator.clipboard.writeText(payload);
  } catch {
    // ignore clipboard failure in locked environments
  }
}

function exportContractJson() {
  if (!contract.value) return;
  const payload = JSON.stringify(
    {
      action_id: actionId.value,
      model: model.value,
      contract: contract.value,
      meta: contractMeta.value || {},
    },
    null,
    2,
  );
  const blob = new Blob([payload], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `contract_form_${model.value || 'unknown'}_${actionId.value || 'na'}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

watch(
  () => formRouteIdentity(),
  (identity) => {
    if (!isComponentActive.value) return;
    if (!instanceRouteIdentity.value && identity) instanceRouteIdentity.value = identity;
    if (instanceRouteIdentity.value && identity !== instanceRouteIdentity.value) {
      instanceRouteIdentity.value = identity;
    }
    if (identity && identity === retainedRouteIdentity.value && status.value === 'ok') return;
    void reload();
  },
  { immediate: true },
);

watch(
  () => route.query.config_mode,
  (mode) => {
    applyRouteConfigMode(mode);
  },
  { immediate: true },
);

watch(
  () => ({
    label: currentBusinessCategoryLabel.value,
    code: currentBusinessCategoryCode.value,
  }),
  (state) => {
    if (!isComponentActive.value) return;
    if (!state.label) return;
    const hasRouteLabel = String(route.query.current_business_category_label || route.query.default_business_category_label || '').trim();
    if (hasRouteLabel) return;
    const query: Record<string, string | string[]> = {
      ...Object.fromEntries(
        Object.entries(route.query).map(([key, value]) => [
          key,
          Array.isArray(value)
            ? value.filter((item): item is string => typeof item === 'string')
            : String(value || ''),
        ]),
      ),
      current_business_category_label: state.label,
      default_business_category_label: state.label,
    };
    if (state.code) {
      query.current_business_category_code = String(route.query.current_business_category_code || state.code);
      query.default_business_category_code = String(route.query.default_business_category_code || state.code);
    }
    void router.replace({ query });
  },
);

function projectContextChangedProjectId(event: Event): number {
  const detail = event instanceof CustomEvent && event.detail && typeof event.detail === 'object'
    ? event.detail as Record<string, unknown>
    : {};
  return Number(detail.selected_project_id || session.projectContext?.selected?.id || 0) || 0;
}

function projectContextChangedPreviousProjectId(event: Event): number {
  const detail = event instanceof CustomEvent && event.detail && typeof event.detail === 'object'
    ? event.detail as Record<string, unknown>
    : {};
  return Number(detail.previous_project_id || 0) || 0;
}

function handleProjectContextChanged(event: Event): void {
  if (!isComponentActive.value) return;
  const selectedProjectId = projectContextChangedProjectId(event);
  const previousProjectId = projectContextChangedPreviousProjectId(event);
  if (selectedProjectId > 0 && previousProjectId === selectedProjectId) return;
  if (model.value === 'project.project' && recordId.value === selectedProjectId) return;
  if (model.value === 'project.project' && selectedProjectId > 0) {
    void router.replace({
      name: 'record',
      params: { model: 'project.project', id: String(selectedProjectId) },
      query: resolveWorkspaceContextQuery(),
    });
    return;
  }
  void router.replace(buildCanonicalSceneRouteTarget('projects.list', {
    query: {
      ...resolveWorkspaceContextQuery(),
      ...(selectedProjectId > 0 ? { project_id: String(selectedProjectId) } : {}),
    },
  }));
}

watch(
  () => [
    intakeAutosaveKey.value,
    formData.name,
    formData.manager_id,
    formData.owner_id,
    formData.project_type_id,
    formData.project_category_id,
    formData.location,
    formData.start_date,
    formData.end_date,
  ],
  () => {
    persistIntakeAutosave();
  },
);

watch(
  () => ({
    model: model.value,
    recordId: recordId.value,
    collaborationReady: Boolean(nativeChatterActions.value.length || nativeAttachments.value),
    projectIntake: isProjectIntakeCreateMode.value,
  }),
  (state) => {
    if (!isComponentActive.value) return;
    if (state.projectIntake || !state.model || !state.recordId || !state.collaborationReady) return;
    const key = `${state.model}:${state.recordId}`;
    if (nativeChatterAutoLoadKey.value === key || chatterLoading.value) return;
    nativeChatterAutoLoadKey.value = key;
    void loadNativeChatterTimeline();
  },
  { immediate: true },
);

onMounted(() => {
  if (typeof window !== 'undefined') {
    window.addEventListener(PROJECT_CONTEXT_CHANGED_EVENT, handleProjectContextChanged);
    window.addEventListener('dragover', onFieldOrderWindowDragOver);
    window.addEventListener('drop', onFieldOrderWindowDragStop);
    window.addEventListener('dragend', onFieldOrderWindowDragStop);
  }
  if (typeof document !== 'undefined') {
    document.addEventListener('keydown', onRelationDialogDocumentKeydown);
  }
  void nextTick(() => ensureFormInitialReload());
});

onActivated(() => {
  isComponentActive.value = true;
  const identity = formRouteIdentity();
  if (identity && identity !== retainedRouteIdentity.value) {
    void reload();
  }
  void nextTick(() => ensureFormInitialReload());
});

onDeactivated(() => {
  isComponentActive.value = false;
});

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener(PROJECT_CONTEXT_CHANGED_EVENT, handleProjectContextChanged);
    window.removeEventListener('dragover', onFieldOrderWindowDragOver);
    window.removeEventListener('drop', onFieldOrderWindowDragStop);
    window.removeEventListener('dragend', onFieldOrderWindowDragStop);
  }
  if (typeof document !== 'undefined') {
    document.removeEventListener('keydown', onRelationDialogDocumentKeydown);
  }
  onFieldOrderDragEnd();
});
</script>

<style scoped src="./contractForm/ContractFormPage.css"></style>

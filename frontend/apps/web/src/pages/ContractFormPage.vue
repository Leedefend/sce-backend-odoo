/* eslint-disable @typescript-eslint/no-unused-vars, no-extra-boolean-cast, vue/attributes-order */
<template>
  <LayoutShell
    :width-mode="recordPageWidthMode"
    :class="['sc-page', { 'contract-form-native-shell': useNativeFormTree }]"
    data-product-page-mode="form"
    :data-v2-shadow-store="String(v2ShadowStoreReady)" :data-v2-shadow-widgets="String(v2ShadowWidgetCount)"
    :data-v2-shadow-actions="String(v2ShadowActionCount)" :data-v2-shadow-button-statuses="String(v2ShadowButtonStatusCount)"
    :data-v2-shadow-field-codes="String(v2ShadowFieldCodeCount)" :data-v2-shadow-field-overlap="String(v2ShadowLegacyFieldOverlapCount)"
    :data-v2-shadow-field-missing="v2ShadowLegacyFieldMissingPreview" :data-v2-shadow-layout-source="v2ShadowLayoutSourceKind"
    :data-v2-shadow-global-source="v2ShadowGlobalSourceKind" :data-v2-shadow-source-context="v2ShadowSourceContextKind"
    :data-v2-shadow-status-fields="String(v2ShadowStatusFieldCount)" :data-v2-shadow-value-fields="String(v2ShadowValueFieldCount)"
    :data-v2-shadow-main-data-fields="String(v2ShadowMainDataFieldCount)"
    :data-v2-shadow-readonly-values="String(v2ShadowReadonlyValueCount)"
    :data-v2-shadow-value-source="v2ShadowValueSourceKind"
    :data-v2-shadow-error="v2ContractDecodeError || '-'"
  >
    <ContractFormProductHeader
      :title="pageDisplayTitle" :subtitle="pageDisplaySubtitle" :hide-title="suppressPageHeaderTitle" :show-hud="showHud"
      :model="model" :record-id-display="recordIdDisplay" :action-id="actionId" :contract-meta-line="contractMetaLine"
      :intake-mode="isProjectIntakeCreateMode" :intake-required-summary="intakeRequiredSummary" :intake-missing-summary="intakeMissingSummary" :statusbar="nativeStatusbar"
      :busy="busy" :show-return="showReturnToBusinessConfigAction" :show-draft-save="showDraftSaveAction" :draft-save-disabled="draftSaveDisabled" :draft-save-label="draftSaveButtonLabel"
      :show-primary-form-action="showPrimaryBusinessFormAction" :primary-form-action-disabled="primaryFormActionDisabled" :submit-label="submitButtonLabel"
      :direct-actions="headerBusinessDirectActions" :overflow-actions="headerBusinessOverflowActions" :config-actions="headerConfigActionsVisible"
      :show-discard="showDiscardAction" :show-debug="showDebugActionsVisible" :contract-present="Boolean(contract)" :discard-label="formUiLabel('discard')" :reload-label="formUiLabel('reload')"
      @back="returnToPreviousPage" @set-status="setStatusbarValue" @return-workbench="returnToBusinessConfigDesigner" @save-draft="saveRecord()"
      @run-primary="runPrimaryFormAction" @run-action="runAction" @discard="discardChanges" @copy="copyContractJson" @export="exportContractJson" @reload="reload"
    />

    <StatusPanel v-if="renderErrorMessage" :title="pageDisplayTitle" :message="renderErrorMessage" variant="error" :on-retry="reload" />
    <StatusPanel v-else-if="status === 'loading'" :title="pageDisplayTitle" variant="info" busy />
    <StatusPanel v-else-if="status === 'error'" :title="pageDisplayTitle" :message="errorMessage" :error-code="loadError.status" :reason-code="loadError.reason" :trace-id="loadError.trace" variant="error" :on-retry="reload" />
    <StatusPanel v-else-if="recordMissing" :title="pageDisplayTitle" message="该记录不存在，可能已被删除或当前链接已经失效。" :error-code="404" variant="error" retry-label="返回安全页面" :on-retry="() => router.push('/')" />

    <section v-else :class="['card', 'sc-panel', 'sc-product-main-surface', { 'card--flow': isProjectIntakeCreateMode }]">
      <p v-if="financialWorkspace && submissionFeedback" class="submission-feedback" :class="`submission-feedback--${submissionFeedback.kind}`" role="status">
        {{ submissionFeedback.message }}
      </p>
      <FinancialRelationshipWorkspace v-if="financialWorkspace" :contract="financialWorkspace" />
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

      <section v-if="!financialWorkspace || renderProfile === 'edit'" class="form-grid" :class="{ 'form-grid--designer-workspace': showCurrentFormFieldConfigScope }">
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
        <ProductFormErrorSummary
          :errors="nonSceneValidationErrors"
          :conflict="formConflict"
          @focus-error="focusValidationError"
          @reload-latest="reloadLatestRecord"
        />
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
    <IntentConfirmationDialog ref="intentConfirmationRef" />
    <AttachmentViewer ref="attachmentViewerRef" />
  </LayoutShell>
</template>

<script setup lang="ts">
import { computed, nextTick, onErrorCaptured, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import StatusPanel from '../components/StatusPanel.vue';
import DevContextPanel from '../components/DevContextPanel.vue';
import FinancialRelationshipWorkspace from '../components/business/FinancialRelationshipWorkspace.vue';
import ProductFormErrorSummary from '../components/product-record/ProductFormErrorSummary.vue';
import IntentConfirmationDialog from '../components/business/IntentConfirmationDialog.vue';
import AttachmentViewer from '../components/attachment/AttachmentViewer.vue';
import LayoutShell from '../components/template/LayoutShell.vue';
import { contractPageWidthMode, resolvePageWidthMode } from '../components/design-system/pageWidth';
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
import ContractFormProductHeader from './contractForm/ContractFormProductHeader.vue';
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
import { readWorkspaceContext } from '../app/workspaceContext';
import { resolveFinancialWorkspaceContract } from '../app/financialWorkspaceContract';
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
  resolveUnifiedPageContractV2FieldGroups,
  resolveUnifiedPageContractV2MainData,
  resolveUnifiedPageContractV2,
  resolveUnifiedPageContractV2GlobalStatus,
  resolveUnifiedPageContractV2SourceContext,
  resolveUnifiedPageContractV2VisibleFields,
} from '../app/contracts/unifiedPageContractV2';
import {
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
    normalizeContractFieldValue,
  normalizeComparable,
  normalizeRouteDefault,
  resolveNavigationUrl as resolveNavigationUrlFromOrigin,
} from './contractForm/valueUtils';
import {
  buildOnchangeRequestPayload,
  normalizeOnchangeFieldPatch,
  normalizeOnchangeResponse,
} from './contractForm/onchangeNormalization';
import { fieldRequiresServerOnchange, resolveContractActionRules } from './contractForm/contractActionRules';
import { dictOrEmpty } from './contractForm/recordUtils';
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
  resolveWorkflowContractFromSources,
  applyWorkflowAvailability,
  shouldShowWorkflowAction,
  workflowActionMethodAliases,
  workflowActionRowForMethod,
} from './contractForm/workflowContract';
import {
  formUiLabelFromLabels,
  formUiLabelsFromFormView,
  resolveSubmitButtonLabel,
  layoutContainsType,
} from './contractForm/uiLabels';
import { buildContractFormPageIdentity } from '../app/pageIdentityAdapters';
import { resolveRoutePageIdentity } from '../app/pageIdentityRoute';
import { usePublishedPageIdentity } from '../app/usePublishedPageIdentity';
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
  type FormRuntimeStateEvent,
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
  type SubmissionFeedback,
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
import { useActionResponseNavigation } from './contractForm/useActionResponseNavigation';
import { usePrimaryFormActionRuntime } from './contractForm/usePrimaryFormActionRuntime';
import { useFormActionRuntime } from './contractForm/useFormActionRuntime';
import { useFormConfigSaveRuntime } from './contractForm/useFormConfigSaveRuntime';
import { applyFormRuntimeStatusEvent } from './contractForm/runtimeStateApplier';
import { useContractDebugExportRuntime } from './contractForm/useContractDebugExportRuntime';
import { useProjectContextChangeRuntime } from './contractForm/useProjectContextChangeRuntime';
import { selectAuthoritativeBusinessActionRows } from './contractForm/authoritativeBusinessActionRows';
import { isFormPageRouteOwner, useFormPageLifecycleRuntime } from './contractForm/useFormPageLifecycleRuntime';
import { useFormAuxiliaryWatchersRuntime } from './contractForm/useFormAuxiliaryWatchersRuntime';
import { useUnsavedFormGuard } from './contractForm/useUnsavedFormGuard';
import { buildContractFormActions } from './contractForm/contractActionPresentation';
import { focusProductFormValidationError } from './contractForm/formValidationFocus';
import { groupContractHeaderActions } from './contractForm/contractHeaderActionPresentation';
import { resolveContractFormFieldLabels } from './contractForm/formFieldLabels';
import { buildSaveRecordPayload, validateBeforeSaveRecord } from './contractForm/saveRecordHelpers';
import { useCreatedRecordNavigationRuntime } from './contractForm/useCreatedRecordNavigationRuntime';
import { useRecordCollaborationPresentation } from './contractForm/useRecordCollaborationPresentation';
import { useRecordContractSemantics } from './contractForm/useRecordContractSemantics';
import { useRecordFormLayout } from './contractForm/useRecordFormLayout';
import { useRecordFormFieldSchemas } from './contractForm/useRecordFormFieldSchemas';
import { useRecordFormState } from './contractForm/useRecordFormState';
import { useRecordFormDesigner } from './contractForm/useRecordFormDesigner';
import { useRecordRelationships } from './contractForm/useRecordRelationships';
import { useRecordPageLifecycle } from './contractForm/useRecordPageLifecycle';
import { useRecordActionPresentation } from './contractForm/useRecordActionPresentation';
import { useRecordFormActions } from './contractForm/useRecordFormActions';
import { useFormNavigationActionsRuntime } from './contractForm/useFormNavigationActionsRuntime';
import { applyRouteRelationLabel, isProjectScopeExempt, scopedCreateContext, scopedOnchangeContext } from './contractForm/financialFormScope';
import { collectActionParams as collectActionParamsFromPlan } from './contractForm/actionExecutionPlan';
import {
  formCreateContext as formCreateContextFromState,
  resolveCreateDefaults as resolveCreateDefaultsFromState,
} from './contractForm/createDefaults';
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
const route = useRoute();
const router = useRouter();
const session = useSessionStore();
const {
  actionResponseNavQuery,
  actionResponseRouteTarget,
  navigateActionResponseResult,
} = useActionResponseNavigation({
  router,
  currentQuery: () => route.query,
});
function resolveWorkspaceContextQuery() { return readWorkspaceContext(route.query as Record<string, unknown>); }
function designerRouteQueryText(key: string) {
  const value = route.query[key];
  return String(Array.isArray(value) ? value[0] || '' : value || '').trim();
}
const status = ref<UiStatus>('loading');
const isComponentActive = ref(true);
const instanceRouteIdentity = ref('');
const retainedRouteIdentity = ref('');
const renderErrorMessage = ref('');
const recordMissing = ref(false);
const errorMessage = ref('');
const loadError = reactive<{ status: number | null; reason: string; trace: string }>({ status: null, reason: '', trace: '' });
const validationErrors = ref<string[]>([]);
const submissionFeedback = ref<SubmissionFeedback>(null);
const formConflict = ref(false);
const intentConfirmationRef = ref<InstanceType<typeof IntentConfirmationDialog> | null>(null);
const showOne2manyErrors = ref(false);
const busyKind = ref<BusyKind>(null);
const activeContractMode = ref('');
const formSettingsActiveTab = ref<'structure' | 'fields' | 'details' | 'actions'>('fields');
const contractModeFeedback = ref('');
const contract = ref<ActionContract | null>(null);
const contractMeta = ref<Record<string, unknown> | null>(null);
type PageStatusEvent = Extract<FormRuntimeStateEvent, { kind: 'status' }>;
function applyPageStatusEvent(event: PageStatusEvent) {
  applyFormRuntimeStatusEvent({ status, errorMessage }, event);
}
const {
  copyContractJson,
  exportContractJson,
} = useContractDebugExportRuntime({
  actionId: () => actionId.value || 0,
  contract,
  contractMeta,
  modelName: () => model.value,
});
const {
  handleProjectContextChanged,
} = useProjectContextChangeRuntime({
  isActive: () => isComponentActive.value,
  modelName: () => model.value,
  recordId: () => recordId.value,
  resolveWorkspaceContextQuery: () => resolveWorkspaceContextQuery(),
  router,
  selectedProjectId: () => Number(session.projectContext?.selected?.id || 0) || 0,
});
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
    String(recordId.value ? '' : (query.view_id || query.viewId || '')),
    String(recordId.value ? '' : (query.current_business_category_code || query.default_business_category_code || '')),
    String(recordId.value ? '' : (query.allowed_business_category_codes || '')),
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
  resolveLabel: (key, fallback) => resolveNativeAttachmentLabel(key, fallback),
  reloadTimeline: loadNativeChatterTimeline,
  viewerRef: attachmentViewerRef,
  onPendingUploadFailed: (message) => {
    validationErrors.value = [message];
    submissionFeedback.value = { kind: 'error', message };
    applyPageStatusEvent({ kind: 'status', transaction: 'primaryAction', status: 'error' });
  },
});
const nativeChatterAutoLoadKey = ref('');

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
const recordPageWidthMode = computed(() => resolvePageWidthMode({ contractWidthMode: contractPageWidthMode(contract.value), pageKind: recordId.value ? (route.name === 'model-form' ? 'edit' : 'detail') : 'create' }));
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
const {
  runPrimaryFormAction,
} = usePrimaryFormActionRuntime({
  actionId: () => actionId.value || 0,
  applyProjectionRefreshPolicy: (policy) => applyProjectionRefreshPolicy(policy),
  busyKind,
  confirmActionSafety: (action) => confirmActionSafety(action),
  errorMessage,
  modelName: () => model.value,
  navigateActionResponseResult: (result) => navigateActionResponseResult(result),
  primaryCreateFooterAction: () => primaryCreateFooterAction.value,
  primarySubmitAction: () => primarySubmitAction.value,
  recordId,
  reload: () => reload(),
  routeMenuId: () => route.query.menu_id,
  saveRecord: (refreshPolicy) => saveRecord(refreshPolicy),
  status,
  submissionFeedback,
  validationErrors,
});
const {
  runAction,
} = useFormActionRuntime({
  actionId: () => actionId.value || 0,
  applyClientMode: (mode, toggle) => applyClientMode(mode, toggle),
  applyProjectionRefreshPolicy: (policy) => applyProjectionRefreshPolicy(policy),
  busyKind,
  collectActionParams: (action) => collectActionParamsFromPlan(action, () => applyPageStatusEvent({ kind: 'status', transaction: 'runAction', status: 'error', errorMessage: '请填写操作原因' })),
  confirmActionSafety: (action) => confirmActionSafety(action),
  currentQuery: () => route.query,
  ensureSavedBeforeRecordAction: () => ensureSavedBeforeRecordAction(),
  errorMessage,
  executeSceneMutation: (input) => executeSceneMutation(input),
  modelName: () => model.value,
  navigateActionResponseResult: (result) => navigateActionResponseResult(result),
  recordId: () => recordId.value,
  reload: () => reload(),
  resolveNavigationUrl: (url) => resolveNavigationUrl(url),
  routeMenuId: () => route.query.menu_id,
  router,
  saveRecord: (refreshPolicy) => saveRecord(refreshPolicy),
  status,
  submissionFeedback,
});
const {
  navigateCreatedRecord,
} = useCreatedRecordNavigationRuntime({
  applyProjectionRefreshPolicy: (policy) => applyProjectionRefreshPolicy(policy),
  currentQuery: () => route.query as Record<string, unknown>,
  isProjectQuickIntakeMode: () => isProjectQuickIntakeMode.value,
  isProjectStandardIntakeMode: () => isProjectStandardIntakeMode.value,
  modelName: () => model.value,
  resolveWorkspaceContextQuery: () => resolveWorkspaceContextQuery(),
  returnToProjectIntakeList: (createdId) => returnToProjectIntakeList(createdId),
  router,
});
const {
  cancelIntake,
  openFilter,
  returnToProjectIntakeList,
} = useFormNavigationActionsRuntime({
  actionId: () => actionId.value || 0,
  currentQuery: () => route.query as Record<string, unknown>,
  isProjectIntakeCreateMode: () => isProjectIntakeCreateMode.value,
  resolveLandingPath: (fallback) => session.resolveLandingPath(fallback),
  resolveWorkspaceContextQuery: () => resolveWorkspaceContextQuery(),
  router,
  searchFilters: () => searchFilters.value,
  setActiveFilterKey: (key) => {
    activeFilterKey.value = key;
  },
});
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

const currentActionMeta = computed(() => findActionMetaByMenu(session.menuTree, menuId.value, actionId.value || undefined));
const currentBusinessCategoryContext = computed(() => resolveBusinessCategoryContext({
  contractRecord: contract.value,
  routeQuery: route.query as Record<string, unknown>,
  relationBusinessCategoryLabel: relationKeywords.business_category_id,
}));
const currentBusinessCategoryLabel = computed(() => currentBusinessCategoryContext.value.label);
const currentBusinessCategoryCode = computed(() => currentBusinessCategoryContext.value.code);

const pageIdentityInput = computed(() => buildContractFormPageIdentity({
  action: currentActionMeta.value, breadcrumbs: resolveRoutePageIdentity(route, session.menuTree).breadcrumbs,
  businessCategoryLabel: currentBusinessCategoryLabel.value, contract: contract.value, formData,
  isCreate: !recordId.value, isEdit: route.name === 'model-form', isProjectIntake: isProjectIntakeCreateMode.value,
  menuName: currentMenuTitle.value, modelName: model.value, recordMissing: recordMissing.value,
  renderError: Boolean(renderErrorMessage.value), status: status.value,
}));
const pageIdentity = usePublishedPageIdentity(pageIdentityInput, { routeKey: () => route.fullPath,
  active: () => isComponentActive.value && isFormPageRouteOwner(route.name), onTitle: (title) => session.updateActiveActivityTitle(title) });
const pageDisplayTitle = computed(() => pageIdentity.value.title);
const pageDisplaySubtitle = computed(() => pageIdentity.value.subtitle || '');
const financialWorkspace = computed(() => resolveFinancialWorkspaceContract(contract.value));

const suppressPageHeaderTitle = computed(() => true);
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
const showPrimaryBusinessFormAction = computed(() => (!financialWorkspace.value || renderProfile.value === 'edit') && !showCurrentFormFieldConfigScope.value && !isProjectIntakeCreateMode.value);
const showDraftSaveAction = computed(() => {
  if (!showPrimaryBusinessFormAction.value || !canSave.value || primaryCreateFooterAction.value) return false;
  if (!recordId.value) return true;
  return Boolean(primarySubmitAction.value) && hasChanges.value;
});
const draftSaveButtonLabel = computed(() => {
  if (busy.value && busyKind.value === 'save') return formUiLabel('saving');
  return recordId.value ? formUiLabel('save') : '保存草稿';
});
const showDiscardAction = computed(() => !isProjectIntakeCreateMode.value && Boolean(recordId.value) && hasChanges.value);

const groupedHeaderActions = computed(() => groupContractHeaderActions({
  actions: headerActions.value, intakeMode: isProjectIntakeCreateMode.value, nativeTree: useNativeFormTree.value,
  configurationMode: showCurrentFormFieldConfigScope.value, productRecord: Boolean(financialWorkspace.value),
  isSubmitAction: isUnifiedSubmitAction,
}));
const headerBusinessDirectActions = computed(() => groupedHeaderActions.value.direct);
const headerBusinessOverflowActions = computed(() => groupedHeaderActions.value.overflow);
const headerConfigActionsVisible = computed(() => groupedHeaderActions.value.configuration);

const contractV2ActionRules = computed(() => resolveContractActionRules(contract.value));

function contractFieldActions(field: FormSectionFieldSchema) {
  return buildContractFieldActionsFromRules({
    rules: contractV2ActionRules.value,
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
    rules: contractV2ActionRules.value,
    mode: activeContractMode.value,
    excludedKeys: [BUSINESS_CONFIG_ACTION_KEYS.currentFormFieldOrderSave],
  });
});


const {
  fieldOrderDraft, fieldOrderPreviewActive, nativeFormDesignFieldKeys, nativeFormDesignFieldLabels, formConfigFieldLabelCache,
  fieldGroupBase, fieldGroupSavedBase, fieldGroupDraft, formLayoutColumnsBase, formLayoutColumnsDraft,
  formLayoutColumnsConfigured, groupVisibilityBase, groupVisibilityDraft, groupColumnsBase, groupColumnsDraft,
  fieldSizeBase, fieldSizeDraft, formLayoutDirty, groupLayoutDirtyKeys, fieldLayoutDirtyKeys,
  fieldMoveTargetDraft, draggingFieldKey, draggingFieldLabel, dropTargetFieldKey, dropTargetPlacement,
  onFieldOrderDragStart, onFieldOrderDragOver, onFieldOrderDragLeave, onFieldOrderDragEnd, onFieldOrderWindowDragOver,
  onFieldOrderWindowDragStop, resetFieldOrderDropTarget, selectedFormSettingsFieldKey, selectedFormSettingsFieldLabel, selectedFormSettingsFieldGroupTitleDraft,
  selectedFormSettingsFieldGroupTitleEdit, formDesignerFieldSearchText, selectedFormSettingsOrderTargetKey, selectedFormSettingsOrderPlacement, isContractFieldOrderEditable,
  showReturnToBusinessConfigAction, fieldVisibilityBase, fieldVisibilityDirty, fieldVisibilityDraft, fieldVisibilityDirtyKeys,
  formConfigAuditBusy, formConfigAuditResult, formConfigOperationLog, formConfigOperatorName, appendFormConfigOperation,
  markPendingFormConfigOperations, clearFormConfigOperationLog, onFormLayoutColumnsChange, onSelectedFormSettingsGroupVisibilityChange, onSelectedFormSettingsGroupColumnsChange,
  onSelectedFormSettingsFieldSizeChange, resetContractFieldOrder, onContractInlineGroupRename, moveFieldOrder, moveSelectedFormSettingsFieldToOrderTarget,
  onSelectedFormSettingsFieldGroupMoveChange, onFieldOrderDrop, onFieldOrderGroupDrop, hideSuggestedInternalFields, onFieldVisibilityDraftChange,
  onSelectedFormSettingsFieldVisibilityChange, onContractInlineFieldLabelChange, setInlineFieldPolicy, closeContractPromptAction, contractPromptFields,
  contractPromptRule, contractPromptValues, openContractModeAction, runContractRuleAction, setContractPromptValue,
  submitContractPromptAction, lowCodeFieldCreateDialog, openCentralCustomFieldCreate, onContractInlineFieldAddAfter, onContractInlineGroupAddField,
  closeInlineCustomFieldCreate, setFieldCreateLabel, setFieldCreateType, submitInlineCustomFieldCreate, lowCodeContractLoaded,
  lowCodeContractHydrating, lowCodePrecheckWarnings, lowCodeContractList, lowCodeSelectedContractName, lowCodeFormLayoutBase,
  lowCodeLayoutDraft, saveContractFieldOrder, contractModeBaseFieldRows, activeContractModeFieldRows, currentFormDesignFieldKeys,
  currentFormOrderedFieldKeys, selectedFormSettingsOrderTargetOptions, syncFieldOrderDraftWithDesignKeys, hasFieldOrderChanges, formVisibilityDraftFieldKeys,
  hasFieldVisibilityChanges, hasFieldGroupChanges, effectiveGroupVisible, effectiveGroupColumns, effectiveFieldSize,
  hasFormLayoutChanges, hasGroupLayoutChanges, hasFieldLayoutChanges, hasCurrentFormFieldDraftChanges, formConfigFieldLabelReplacementEntries,
  formatFormConfigOperationSummary, formDesignFieldLabel, rememberFormConfigFieldLabel, suggestedHiddenFieldRows, changedFieldVisibilityDraft,
  changedFieldGroupDraft, effectiveFieldGroupTitleForDraft, auditCurrentFormConfiguration, showCurrentFormFieldConfigScope, showLowCodeTechnicalDetails,
  currentFormConfigPageLabel, formFieldConfigScope, formConfigAuditSummary, selectedFormSettingsFieldRow, nativeFieldStructureGroups,
  currentFormDesignFieldCount, currentFormGroupOptions, formDesignerGroupNavigatorItems, formDesignerFieldSearchQuery, formDesignerSearchableFieldRows,
  formDesignerFilteredFieldRows, selectedFormSettingsFieldGroupTitle, selectedFormSettingsGroupVisible, selectedFormSettingsGroupColumns, selectedFormSettingsFieldSize,
  syncLayoutDraftFromFormSpec, syncFieldDraftFromFormSpec, applyRuntimeInferredFormColumns, hydrateLowCodeDraftFromContract, refreshLowCodeFormLayoutBase,
  loadLowCodeContractList, switchLowCodeContractByName, publishSelectedLowCodeContract, rollbackSelectedLowCodeContract, buildLowCodeViewOrchestration,
  lowCodeLayoutFieldLabel, effectiveLowCodeFieldLabel,
} = useRecordFormDesigner({
  BUSINESS_CONFIG_INTENTS, BUSINESS_CONFIG_MODES, BUSINESS_CONFIG_ROUTE_FLAGS,
  FORM_FIELD_CONFIG_INTENTS, actionId, activeContractMode,
  applyClientMode: (mode: string, toggle?: boolean) => applyClientMode(mode, toggle), applyPageStatusEvent, buildCurrentFormGroupOptions,
  buildFormConfigFieldLabelReplacementEntries, buildFormDesignerGroupNavigatorItems, buildFormDesignerSearchableFieldRows,
  buildFormFieldConfigScope, buildLowCodeViewOrchestrationFromDraft, busy,
  busyKind, changedFieldGroupFromDrafts, changedFieldVisibilityFromDrafts,
  collectLowCodeLayoutFromViewOrchestration, collectNativeFieldStructureGroups, collectNativeLayoutGroupTitles,
  contract, contractActionRuleClientMode, contractActionRuleControl,
  contractActionRuleKey, contractFieldLabel: (...args: [string]) => contractFieldLabel(...args), contractFieldSequence: (fieldKey: string, fallback?: number) => contractFieldSequence(fieldKey, fallback),
  contractModeFeedback, contractV2ActionRules, currentBusinessCategoryLabel,
  effectiveFieldGroupTitleFromDrafts, ensureFieldOrderDraftStartsFromCurrentLayout: (...args: []) => ensureFieldOrderDraftStartsFromCurrentLayout(...args), errorMessage,
  extractLowCodeFormFieldDraftState, extractLowCodeLayoutDraftState, filterFormDesignerFieldRows,
  formSettingsActiveTab, formatFormConfigAuditSummary, formatFormConfigOperationSummaryText,
  inferLowCodeLayoutColumns, intentRequest, isBusinessConfigRuntimeModel,
  isReadableFieldGroupTitle, isSuggestedInternalFormField, layoutHasReadableFieldGroups,
  lowCodeApplyBaseParams: () => lowCodeApplyBaseParams(), lowCodeFormSpecFromViews, lowCodeLayoutFieldLabelFromNodes,
  lowCodeLayoutFromFormSpec, lowCodeScopedContractName, lowCodeViewsFromContractResponse,
  mergeLowCodeLayoutWithRuntimeGroupShells, model, nativeFormLayoutNodes: computed(() => nativeFormLayoutNodes.value),
  normalizeConfigPageLabel, normalizeContractV2ContainersForNativeFormFromTree, normalizeFieldGroupTitle,
  normalizeFormConfigAuditResult, normalizeLowCodeContractListRows, pageDisplayTitle,
  parseMaybeJsonRecord, rawNativeFormLayoutNodes: computed(() => rawNativeFormLayoutNodes.value), readableFallbackFieldLabel,
  reload: (...args: []) => reload(...args), resolveContractV2ContainerTree, resolveFormDesignFieldLabel,
  resolveSelectedFormSettingsFieldGroupTitle, resolveUnifiedPageContractV2, route,
  routeQueryText: designerRouteQueryText, runtimeNativeFormLayoutNodes: (...args: []) => runtimeNativeFormLayoutNodes(...args), session,
  showHud, status, useContractModeActionRuntime,
  useFieldOrderDragRuntime, useFieldOrderMutationRuntime, useFieldVisibilityDraftRuntime,
  useFormConfigOperationLog, useFormConfigSaveRuntime, useFormSettingsGroupRuntime,
  useFormSettingsLayoutRuntime, useInlineFieldPolicyRuntime, useLowCodeFieldCreateRuntime,
  v2ContractStore,
});
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

const {
  relationIds, selectedRelationOptions, many2oneValue, relationOptionsForField, hydrateSelectedRelationOptions,
  one2manyRelationModel, one2manyRelationFieldDescriptor, nativeNodeFieldDescriptor, findNativeFieldNode, effectiveFieldDescriptor,
  mergeNativeLayoutFieldDescriptorsIntoContract, nativeFieldSubview, one2manyColumns, one2manyPolicies, one2manyCanCreate,
  one2manyCreateLabel, one2manyPrimaryColumn, one2manyRowLabel, one2manySummary, hydrateOne2manyRows,
  hydrateVisibleOne2manyRows, one2manyRowErrors, setRelationKeyword, filteredRelationOptions, relationModel,
  formUiLabels, formUiLabel, dynamicDomainFromDescriptor, resolveDynamicDomainDependencyValue, clearDynamicRelationDependents,
  relationDomain, runtimeRelationDomain, mergedRelationDomain, queryRelationOptions, fetchRelationOptions,
  loadRelationSearchColumns, fetchRelationSearchRows, onRelationDialogDocumentKeydown, openRelationSearchDialog, runRelationSearch,
  confirmRelationSearchSelection, selectRelationSearchOption, setMany2oneOption, switchFormByRelationOption, createRelationFromSearchDialog,
  ensureRelationFieldDescriptors, openRelationCreateForm, currentRelationRecordId, canOpenRelationRecordForm, openRelationRecordForm,
  quickCreateRelation, loadRelationOptions,
} = useRecordRelationships({
  ApiError, actionId, clearedDynamicRelationFields,
  closeRelationSearchDialog, confirmRelationSearchSelectionFromRuntime, contract,
  contractFieldLabel: (...args: [string]) => contractFieldLabel(...args), createContractFormRecord, deniedRelationModels,
  dynamicDomainDependencyFields, dynamicRelationDomainFromDescriptor, ensureOne2manyRows,
  fallbackRelationSearchColumns, fetchRelationOptionsFromRuntime, fieldModifierMap: computed(() => fieldModifierMap.value),
  fieldType, filteredRelationOptionsFromRuntime, findNativeFieldNodeInTree,
  formData, formUiLabelFromLabels, formUiLabelsFromFormView,
  invalidatedRelationKeywords, isWritableFieldVisible: (...args: [string]) => isWritableFieldVisible(...args), layoutNodes: computed(() => layoutNodes.value),
  listContractFormRecords, loadModelContractRaw, markFieldChanged,
  menuId, mergeHydratedOne2manyRecords, mergeRelationDomains,
  mergeRelationOptions, model, nativeFieldSubviewFromTree,
  nativeFormLayoutNodes: computed(() => nativeFormLayoutNodes.value), nativeNodeFieldDescriptorFromNode, normalizeFieldValue: (...args: [string, unknown]) => normalizeFieldValue(...args),
  normalizeRelationIds, normalizeRelationSearchColumns, normalizeRouteQueryValues,
  onchangeModifiersPatch, one2manyCanCreateFromPolicies, one2manyColumnsFromSubview,
  one2manyCreateLabelFromPolicies, one2manyDraftSummary, one2manyFieldRows,
  one2manyPrimaryColumnFromColumns, one2manyRowLabelFromPrimary, one2manySubviewPolicies,
  one2manyValidation, openRelationSearchFromRuntime, pickContractNavQuery,
  queryRelationOptionsFromRuntime, rawNativeFormLayoutNodes: computed(() => rawNativeFormLayoutNodes.value), readContractFormRecord,
  recordId, relationCreateMode, relationDomainFromDescriptor,
  relationEntry, relationFieldDescriptors, relationInlineCreate,
  relationKeyword, relationKeywords, relationModelFromDescriptor,
  relationOptions, relationOptionsForFieldFromRuntime, relationOptionsFromRecords,
  relationOrder, relationQueryTimers, relationReadFields,
  relationSearchColumnsFromContract, relationSearchDialog, relationSearchDialogContract,
  relationSearchLimit, relationSearchOrder, relationSearchReadFields,
  relationSearchRowsFromRecords, relationUiLabel, relationUiLabels,
  reload: (...args: []) => reload(...args), route, router,
  runRelationSearchFromRuntime, runtimeRelationDomainFromModifiers, sanitizeUiErrorMessage,
  selectOne2manySubview, selectRelationSearchOptionFromRuntime, selectedRelationOptionsFromRuntime,
  setRelationKeywordValue, validationErrors,
});
const {
  currentWorkflowContract, workflowContractActionRows, blockingWorkflowEvidenceMessage, applyWorkflowContractToAction, shouldShowWorkflowNativeAction,
  workflowEvidenceGateRows, contractActions, headerActions, bodyActions, contractFieldLabels,
  contractFieldLabel, activeActivityAction, nativeAttachmentMaxBytes, nativeChatterActions, nativeAttachments,
  nativeCollaborationPanelProps, nativeCollaborationPanelListeners, resolveNativeAttachmentLabel, hasNativeChatterNode, nativeLayoutContainsType,
  contractActionFromNativeRow, resolveNativeActionState, isUnifiedSubmitMethod, isUnifiedSubmitAction, nativeHeaderSubmitActionForCreate,
  primarySubmitAction, primaryCreateFooterAction, runNativeLayoutAction, advancedFieldNames, contractVisibleFields,
  coreFieldNames, fieldSemanticMeta, focusFirstValidationError, focusValidationError, hasAdvancedFields,
  nonSceneValidationErrors, policyRequiredFields, reloadLatestRecord, sceneReadyFormSurface, sceneValidationPanel,
  sceneValidationRequiredFields, strictContractDefaultsSummary, strictContractGuard, strictContractMissingSummary, strictContractMode,
  useSceneFormAugmentations, validationRequiredFields, baseNativeFormLayoutNodes, currentNativeFieldOrder, ensureFieldOrderDraftStartsFromCurrentLayout,
  evaluateNativeActionVisibility, evaluateNativeModifierValue, fieldModifierMap, formDataFieldNames, isFieldVisible,
  isNativeFavoriteField, isNativeFieldVisible, isNativeLayoutNodeVisible, isWritableFieldVisible, nativeFormLayoutNodes,
  nativeFormRootColumns, nativeGroupCount, nativeNotebookPageCount, nativeStatusbar, nativeVisibleFieldNames,
  nativeVisibleSectionTitles, rawNativeFormLayoutNodes, resolveNativeButtonLabel, runtimeFieldStates, runtimeNativeFormLayoutNodes,
  runtimeState, setStatusbarValue, showNativeDefaultSectionTitle, useNativeFormTree, layoutNodes,
  nativeFieldSchemasForNodes, collectSceneValidationPrecheckErrors, onTemplateFieldChange, relationFieldAdapter,
} = useRecordActionPresentation({
  ErrorCodes, actionId, activeChatterLabel,
  activeChatterMode, activityAssigneeId, activityDeadline,
  activityNote, activitySummary, activityUpdatingIds,
  addOne2manyRow, advancedExpanded, applyPageStatusEvent,
  applyWorkflowAvailability, attachmentError, attachmentUploading,
  buildContractFormActions, busy, busyKind,
  canOpenRelationRecordForm, changedFieldGroupDraft, chatterDraft,
  chatterError, chatterPosting, chatterTimeline,
  closeNativeChatterComposer, collaborationUserChoices, collaborationUserOptions,
  collaborationUserQuery, collaborationUsersLoading, collectContractV2ButtonStatusById,
  collectSceneValidationPrecheckErrorsFromRules, collectUnifiedPageContractV2ButtonStatus, commitMany2oneInline: (...args: Parameters<typeof commitMany2oneInline>) => commitMany2oneInline(...args),
  confirmActionSafety: (action: ContractAction) => confirmActionSafety(action), contract, detectObjectMethodFromActionKey,
  dispatchTemplateFieldChange, effectiveFieldSize, effectiveGroupVisible,
  ensureSavedBeforeRecordAction: () => ensureSavedBeforeRecordAction(), executeButton, fieldGroupBase,
  fieldGroupDraft, fieldInputType, fieldMoveTargetDraft,
  fieldOrderDraft, fieldOrderPreviewActive, fieldVisibilityDraft,
  filteredRelationOptions, focusProductFormValidationError, formConflict,
  formData, formLayoutColumnsDraft, inputFieldValue,
  intentConfirmationRef, isContractFieldOrderEditable, isMissingRequiredValue,
  isProjectIntakeCreateMode, isProjectQuickIntakeMode, isTierValidationActionHidden: (methodName: string) => isTierValidationActionHidden(methodName),
  layoutContainsType, loadCollaborationUsers, lowCodeFormLayoutBase,
  many2oneValue, markFieldChanged, model,
  nativeFormDesignFieldKeys, nativeFormDesignFieldLabels, nativeLayoutVisibilityRevision,
  navigateActionResponseResult, normalizeActionKind, normalizeActionSafety,
  normalizeRequiredParams, normalizeWorkflowActionRows, normalizeWorkflowEvidenceGateRows,
  onNativeAttachmentSelected, onchangeModifiersPatch, one2manyCanCreate,
  one2manyColumnDisplayValue, one2manyColumnInputType, one2manyColumns,
  one2manyCreateLabel, one2manyRowErrors, one2manyRowHints,
  one2manyRowLabel, one2manyRowStateLabel, one2manySummary,
  openNativeAttachment, openNativeChatterAction, openRelationCreateForm,
  parseMaybeJsonRecord, pendingNativeAttachments, policyContext,
  queryMany2oneInline: (...args: Parameters<typeof queryMany2oneInline>) => queryMany2oneInline(...args), recordId, relationCreateMode,
  relationIds, relationInlineCreate, relationKeyword,
  relationOptionsForField, relationUiLabel, reload: (...args: Parameters<typeof reload>) => reload(...args),
  rememberFormConfigFieldLabel, removeMentionUser, removeOne2manyRow,
  removePendingNativeAttachment, removedOne2manyRows, renderProfile,
  resolveContractFormFieldLabels, resolveInputPlaceholder, resolvePrimaryCreateFooterAction,
  resolveSelectPlaceholder, resolveUnifiedPageContractV2, resolveWorkflowContractFromSources,
  restoreOne2manyRow, rights, route,
  runAction, runtimeRoleCode, selectMentionUser,
  selectedMentionUsers, selectedRelationOptions, sendNativeChatter,
  session, setBooleanField: (...args: Parameters<typeof setBooleanField>) => setBooleanField(...args), setMany2oneField: (...args: Parameters<typeof setMany2oneField>) => setMany2oneField(...args),
  setOne2manyRowField, setRelationIds: (...args: Parameters<typeof setRelationIds>) => setRelationIds(...args), setRelationKeyword,
  setRelationMultiField: (...args: Parameters<typeof setRelationMultiField>) => setRelationMultiField(...args), setSelectionField: (...args: Parameters<typeof setSelectionField>) => setSelectionField(...args), setTextField: (...args: Parameters<typeof setTextField>) => setTextField(...args),
  shouldShowWorkflowAction, showHud, showOne2manyErrors,
  toDateInputValue, toDatetimeInputValue, toPositiveInt,
  updateNativeActivity, useRecordCollaborationPresentation, useRecordContractSemantics,
  useRecordFormFieldSchemas, useRecordFormLayout, v2ContractStore,
  validationErrors, visibleOne2manyRows,
});
const contractReadiness = computed<FormContractReadiness>(() => {
  if (!contract.value) {
    return { usable: false, issues: ['contract not loaded'], fieldCount: 0, layoutFieldCount: 0, visibleCandidateCount: 0 };
  }
  return analyzeFormContractReadiness(contract.value, { requirePureFormViewType: false });
});

let recordFormStateRuntime: ReturnType<typeof useRecordFormState>;
function markFieldChanged(name: string) { recordFormStateRuntime.markFieldChanged(name); }
function inputFieldValue(name: string) { return recordFormStateRuntime.inputFieldValue(name); }
recordFormStateRuntime = useRecordFormState({
  contract, model, recordId, rights, formData, originalValues, submissionFeedback, relationKeywords,
  invalidatedRelationKeywords, clearedDynamicRelationFields, relationQueryTimers, relationOptions,
  validationErrors, onchangeModifiersPatch, onchangeWarnings, onchangeLinePatches, applyingOnchangePatch,
  changedFieldSet, dirtyFieldSet, getOnchangeTimer: () => onchangeTimer,
  setOnchangeTimer: (timer) => { onchangeTimer = timer; }, contractV2ActionRules, layoutNodes,
  nativeStatusbar, financialWorkspace, route, isNativeFavoriteField, clearDynamicRelationDependents,
  openRelationCreateForm, openRelationSearchDialog, openRelationRecordForm, relationOptionsForField,
  switchFormByRelationOption, queryRelationOptions, setRelationKeyword, setMany2oneOption,
  relationKeyword, quickCreateRelation, relationUiLabel, relationModel, relationIds, upsertRelationOption,
  buildOne2manyCommandValue, one2manyFieldRows, initOne2manyRows, applyOnchangeLinePatches,
  isWritableFieldVisible,
});
const {
  addRelationId, collectWritableValues, commitMany2oneInline, comparableFieldValue, isFieldWritable,
  normalizeFieldValue, queryMany2oneInline, quickCreateMany2manyTag, resolvePendingInlineRelationCreates,
  resolvePendingMany2manyTagCreates, setBooleanField, setMany2oneField, setRelationIds,
  setRelationMultiField, setSelectionField, setTextField,
} = recordFormStateRuntime;

const {
  resolveNavigationUrl, syncContractV2ShadowStore, viewOrchestrationHudSummary, hudEntries, loadContract,
  loadRecord, handleSceneBlockAction, reload, ensureFormInitialReload, preloadFormAuxiliaryData,
} = useRecordPageLifecycle({
  ApiError, ContractAccessPolicyError, ContractV2DecodeError,
  ErrorCodes, actionId, advancedExpanded,
  analyzeFormContractReadiness, applyIncomingFormFieldValue, applyPageStatusEvent,
  applyRouteRelationLabel, buildRouteContractContext, changedFieldCount,
  changedFieldSet, chatterLoading, clearNativeAttachmentError,
  clearNativeChatterForRecordLoad, clearOne2manyRows, clearPendingNativeAttachments,
  closeNativeChatterComposer, contract, contractAccessPolicy,
  contractActions, contractMeta, contractModelName,
  contractReadiness, coreFieldNames, createContractV2Store,
  decodeContractV2Snapshot, dirtyFieldSet, fieldType,
  financialWorkspace, formData, formDataFieldNames,
  formRouteIdentity, hydrateSelectedRelationOptions, hydrateVisibleOne2manyRows,
  initOne2manyRows, isProjectScopeExempt, layoutNodes,
  loadActionContractRaw, loadError, loadModelContractRaw,
  loadNativeChatterTimeline, loadRelationOptions, menuId,
  mergeNativeLayoutFieldDescriptorsIntoContract, model, nativeAttachments,
  nativeChatterActions, nativeChatterAutoLoadKey, nativeLayoutVisibilityRevision,
  onchangeLinePatches, onchangeModifiersPatch, getOnchangeTimer: () => onchangeTimer,
  setOnchangeTimer: (timer: ReturnType<typeof setTimeout> | null) => { onchangeTimer = timer; }, onchangeWarnings, originalValues,
  pickContractNavQuery, readContractFormRecord, recordId,
  recordIdDisplay, recordMissing, recordVersionPolicy,
  recordVersionToken, relationKeywords, relationOptions,
  renderErrorMessage, renderProfile, requestedSourceMode,
  requestedSurface, resolveContractV2MainData, resolveCreateDefaultsFromState,
  resolveNavigationUrlFromOrigin, resolveUnifiedPageContractV2, resolveUnifiedPageContractV2MainData,
  restoreIntakeAutosave, retainedRouteIdentity, rights,
  route, router, session,
  setStatusbarValue, showHud, showOne2manyErrors,
  snapshotOriginalFormValues, status, toPositiveInt,
  upsertRelationOption, v2ContractDecodeError, v2ContractStore,
  v2ShadowActionCount, v2ShadowButtonStatusCount, v2ShadowFieldCodeCount,
  v2ShadowGlobalSourceKind, v2ShadowLayoutSourceKind, v2ShadowLegacyFieldMissingPreview,
  v2ShadowLegacyFieldOverlapCount, v2ShadowMainDataFieldCount, v2ShadowReadonlyValueCount,
  v2ShadowSourceContextKind, v2ShadowStatusFieldCount, v2ShadowStoreReady,
  v2ShadowValueFieldCount, v2ShadowValueSourceKind, v2ShadowWidgetCount,
  validateSurfaceMarkers, validationErrors, writableFieldCount,
});
const {
  discardChanges, confirmActionSafety, ensureSavedBeforeRecordAction, applyClientMode, applyRouteConfigMode,
  onContractFieldAction, onFormSettingsFieldSelect, selectFormDesignerGroup, selectFormDesignerField, onSelectedFormSettingsGroupTitleChange,
  onSelectedFormSettingsFieldLabelChange, contractInlineFieldOrderIndex, onContractInlineFieldOrderMove, onContractInlineFieldOrderDragStart, onContractInlineFieldOrderDragOver,
  onContractInlineFieldOrderDragLeave, onContractInlineFieldOrderDrop, onContractInlineFieldOrderGroupDrop, onContractInlineFieldOrderDragEnd, lowCodeApplyBaseParams,
  contractFieldSequence, fieldGroupTitleForDraft, routeQueryText, lowCodeReturnQuery, previewLowCodeConfiguredPage,
  previewCurrentFormConfiguration, returnToBusinessConfigDesigner, isTierValidationActionHidden, applyProjectionRefreshPolicy, saveRecord,
} = useRecordFormActions({
  ApiError, BUSINESS_CONFIG_ACTION_KEYS, BUSINESS_CONFIG_MODES,
  BUSINESS_CONFIG_ROUTE_FLAGS, PROJECT_CONTEXT_CHANGED_EVENT, actionId,
  activeContractMode, activeContractModeFieldRows, appendFormConfigOperation,
  buildLowCodeApplyBaseParams, buildLowCodePreviewQuery, buildLowCodeReturnQuery,
  buildSaveRecordPayload, busy, busyKind,
  canSave, clearIntakeAutosave, closeContractPromptAction,
  collectPolicyValidationErrors, collectSceneValidationPrecheckErrors, collectWritableValues,
  comparableFieldValue, contract, contractActionRuleKey,
  contractFieldSequenceFromOrder, contractModeFeedback, contractV2ActionRules,
  createContractFormRecord, currentFormDesignFieldKeys, currentFormOrderedFieldKeys,
  dirtyFieldSet, draggingFieldLabel, effectiveFieldGroupTitleForDraft,
  ensureFormInitialReload, executeProjectionRefresh, fieldGroupTitleMatches,
  fieldOrderDraft, fieldVisibilityBase, fieldVisibilityDirtyKeys,
  fieldVisibilityDraft, focusFirstValidationError, formConfigAuditResult,
  formConflict, formCreateContextFromState, formData,
  formDesignFieldLabel, formDesignerGroupNavigatorItems, formRouteIdentity,
  formSettingsActiveTab, formUiLabel, handleProjectContextChanged,
  hasChanges, hasCurrentFormFieldDraftChanges, instanceRouteIdentity,
  intentConfirmationRef, isBusinessConfigMode, isBusinessConfigRuntimeModel,
  isComponentActive, isContractFieldOrderEditable, isFormPageRouteOwner,
  isProjectStandardIntakeMode, isTierValidationActionHiddenFromState, isWritableFieldVisible,
  layoutNodes, model, moveFieldOrder,
  navigateCreatedRecord, normalizeFieldGroupTitle, normalizeFieldValue,
  onContractInlineGroupRename, onErrorCaptured, onFieldOrderDragEnd,
  onFieldOrderDragLeave, onFieldOrderDragOver, onFieldOrderDragStart,
  onFieldOrderDrop, onFieldOrderGroupDrop, onFieldOrderWindowDragOver,
  onFieldOrderWindowDragStop, onRelationDialogDocumentKeydown, one2manyValidation,
  originalValues, parseMaybeJsonRecord, policyContext,
  recordId, recordVersionPolicy, recordVersionToken,
  reload, rememberFormConfigFieldLabel, renderErrorMessage,
  resolvePendingInlineRelationCreates, resolvePendingMany2manyTagCreates, retainedRouteIdentity,
  route, router, runContractRuleAction,
  sanitizeUiErrorMessage, saveContractFieldOrder, sceneReadyFormSurface,
  scopedCreateContext, selectedFormSettingsFieldGroupTitle, selectedFormSettingsFieldGroupTitleDraft,
  selectedFormSettingsFieldGroupTitleEdit, selectedFormSettingsFieldKey, selectedFormSettingsFieldLabel,
  selectedFormSettingsFieldRow, session, setInlineFieldPolicy,
  showOne2manyErrors, status, submissionFeedback,
  uploadPendingNativeAttachments, useFormPageLifecycleRuntime, v2ContractStore,
  validateBeforeSaveRecord, validateContractFormData, validationErrors,
  writeContractFormRecord,
});
const unsavedFormGuard = useUnsavedFormGuard({
  dirty: () => hasChanges.value,
  busy,
  confirmLeave: async () => intentConfirmationRef.value?.confirm({
    actionLabel: '离开页面',
    message: '当前修改尚未保存。离开后这些修改将丢失，是否继续？',
  }) ?? false,
});
async function returnToPreviousPage() {
  await unsavedFormGuard.navigateAfterConfirm(() => router.back());
}
useFormAuxiliaryWatchersRuntime({
  autosaveSource: () => [
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
  businessCategoryCode: () => currentBusinessCategoryCode.value,
  businessCategoryLabel: () => currentBusinessCategoryLabel.value,
  chatterLoading: () => chatterLoading.value,
  collaborationReady: () => Boolean(nativeChatterActions.value.length || nativeAttachments.value),
  currentQuery: () => route.query as Record<string, unknown>,
  isActive: () => isComponentActive.value,
  isProjectIntake: () => isProjectIntakeCreateMode.value,
  loadNativeChatterTimeline: () => loadNativeChatterTimeline(),
  modelName: () => model.value,
  nativeChatterAutoLoadKey,
  persistIntakeAutosave: () => persistIntakeAutosave(),
  recordId: () => recordId.value,
  router,
});

watch(
  () => route.query.config_mode,
  (mode) => {
    applyRouteConfigMode(mode);
  },
  { immediate: true },
);

</script>

<style scoped src="./contractForm/ContractFormPage.css"></style>

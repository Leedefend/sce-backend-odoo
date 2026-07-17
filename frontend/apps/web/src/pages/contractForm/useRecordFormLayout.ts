/* eslint-disable @typescript-eslint/no-explicit-any */
import { computed, watch, type ComputedRef, type Ref } from 'vue';
import type { ActionContract } from '@sc/schema';
import type { ContractV2NormalizedStore } from '../../app/contracts/v2';
import type { NativeFormLayoutNode } from '../../components/template/NativeFormTreeRenderer.vue';
import { buildRuntimeFieldStates } from '../../app/modifierEngine';
import {
  collectContractV2FieldStatusByCode, resolveContractV2ContainerTree, resolveContractV2MainData,
} from '../../app/contracts/v2';
import {
  collectUnifiedPageContractV2FieldStatus, collectUnifiedPageContractV2FieldWidgets,
  resolveUnifiedPageContractV2, resolveUnifiedPageContractV2MainData,
} from '../../app/contracts/unifiedPageContractV2';
import { evaluateFieldPolicy } from '../../app/contractPolicies';
import {
  applyNativeFieldOrderPreview as applyNativeFieldOrderPreviewFromTree,
  collectFormDataFieldNames, collectNativeFavoriteFieldNames, collectNativeFormDesignFields,
  collectNativeVisibleFieldNames, collectNativeVisibleFieldOrder, collectNativeVisibleSectionTitles,
  countNativeNodesByType, evaluateNativeModifierValue as evaluateNativeModifierValueWithResolver,
  filterVisibleNativeLayoutNodes as filterVisibleNativeLayoutNodesFromTree, isCreateWorkflowStateField,
  isNativeActionVisible, isNativeFieldVisible as isNativeFieldVisibleFromNativeLayout,
  isNativeLayoutNodeVisible as isNativeLayoutNodeVisibleFromNativeLayout,
  normalizeContractV2ContainersForNativeForm as normalizeContractV2ContainersForNativeFormFromTree,
  resolveNativeButtonLabel as resolveNativeButtonLabelFromNode, resolveNativeFormRootColumns,
  type NativeLayoutLikeNode, type FieldSemanticMeta,
} from './nativeLayoutUtils';
import { normalizeNativeFormStatusbar, normalizeWorkflowPhaseStatusbar, resolveStatusbarSelectionValue } from './workflowContract';
import type { NativeStatusbarVm } from './types';
import {
  fieldGroupTitleMatches, isReadableFieldGroupTitle, layoutHasReadableFieldGroups,
  mergeLowCodeLayoutWithRuntimeGroupShells, normalizeFieldGroupTitle,
} from './formConfigHelpers';

export function useRecordFormLayout(context: {
  contract: Ref<ActionContract | null>; v2ContractStore: Ref<ContractV2NormalizedStore | null>;
  contractVisibleFields: ComputedRef<string[]>; onchangeModifiersPatch: Ref<Record<string, Record<string, unknown>>>;
  formData: Record<string, unknown>; isProjectQuickIntakeMode: ComputedRef<boolean>;
  contractFieldLabel: (name: string) => string; fieldSemanticMeta: (name: string) => FieldSemanticMeta;
  showHud: ComputedRef<boolean>; advancedExpanded: Ref<boolean>; coreFieldNames: ComputedRef<string[]>;
  advancedFieldNames: ComputedRef<string[]>; renderProfile: ComputedRef<string>; recordId: ComputedRef<number | null>;
  isContractFieldOrderEditable: ComputedRef<boolean>; fieldOrderDraft: Ref<string[]>; fieldOrderPreviewActive: Ref<boolean>;
  changedFieldGroupDraft: () => Record<string, string>; fieldMoveTargetDraft: Record<string, string>;
  fieldGroupBase: Ref<Record<string, string>>; fieldGroupDraft: Record<string, string>;
  effectiveGroupVisible: (title: string) => boolean; lowCodeFormLayoutBase: Ref<NativeLayoutLikeNode[]>;
  nativeLayoutVisibilityRevision: Ref<number>; nativeFormDesignFieldKeys: Ref<string[]>;
  nativeFormDesignFieldLabels: Ref<Record<string, string>>; formLayoutColumnsDraft: Ref<1|2|3>;
  fieldVisibilityDraft: Record<string, boolean>; contractActionFromNativeRow: (row: Record<string, unknown>) => unknown;
  policyContext: ComputedRef<any>; rights: ComputedRef<{create:boolean;write:boolean}>;
  currentWorkflowContract: () => Record<string, unknown>; markFieldChanged: (name: string) => void;
  layoutNodes: () => Array<{kind:string;name:string}>;
}) {
  const fieldModifierMap = computed<Record<string, Record<string, unknown>>>(() => {
    const formView = (context.contract.value?.views?.form || {}) as { field_modifiers?: Record<string, Record<string, unknown>> };
    const output = { ...(formView.field_modifiers || {}) };
    const fromStore = collectContractV2FieldStatusByCode(context.v2ContractStore.value);
    const statuses = Object.keys(fromStore).length ? fromStore : collectUnifiedPageContractV2FieldStatus(context.contract.value);
    Object.entries(statuses).forEach(([name, status]) => {
      output[name] = { ...(output[name] || {}), ...(status.visible === false ? { invisible: true } : {}),
        ...(status.readonly === true || status.disabled === true ? { readonly: true } : {}),
        ...(status.required === true ? { required: true } : {}) };
    });
    return output;
  });
  const runtimeFieldStates = computed(() => {
    const storeNames = Array.from(context.v2ContractStore.value?.widgetsByFieldCode.keys() || []);
    const contractNames = storeNames.length ? storeNames
      : collectUnifiedPageContractV2FieldWidgets(context.contract.value).map((widget) => widget.fieldCode).filter(Boolean);
    return buildRuntimeFieldStates({
      fieldNames: Array.from(new Set([...Object.keys(context.contract.value?.fields || {}), ...contractNames])),
      fieldModifiers: fieldModifierMap.value, modifierPatch: context.onchangeModifiersPatch.value,
      values: context.formData,
    });
  });
  const runtimeState = (name: string) => runtimeFieldStates.value[name] || { invisible:false, readonly:false, required:false };
  const isFieldVisible = (name: string) => {
    const descriptor = context.contract.value?.fields?.[String(name || '').trim()];
    if (isCreateWorkflowStateField(name, context.contractFieldLabel(name) || descriptor?.string || '', !context.recordId.value)) return false;
    if (nativeStatusbar.value.field === String(name || '').trim()) return false;
    const semantic = context.fieldSemanticMeta(name);
    if ((semantic.technical || semantic.semantic_type === 'technical') && !context.showHud.value) return false;
    if (semantic.surface_role === 'hidden' && !context.showHud.value) return false;
    if (runtimeState(name).invisible) return false;
    if (context.contractVisibleFields.value.length && !context.contractVisibleFields.value.includes(name)) return false;
    if (semantic.surface_role === 'core') return true;
    if (semantic.surface_role === 'advanced') return context.advancedExpanded.value;
    const core = context.coreFieldNames.value; const advanced = context.advancedFieldNames.value;
    if (!core.length && !advanced.length) return true;
    if (core.includes(name)) return true;
    if (advanced.includes(name)) return context.advancedExpanded.value;
    if (!core.length) return true;
    return context.renderProfile.value !== 'create';
  };
  const filterVisibleNativeLayoutNodes = (nodes: NativeFormLayoutNode[]) => filterVisibleNativeLayoutNodesFromTree({
    nodes, isNodeVisible: isNativeLayoutNodeVisible, groupVisibilityEditable: context.isContractFieldOrderEditable.value,
    normalizeGroupTitle: normalizeFieldGroupTitle, isGroupVisible: context.effectiveGroupVisible,
  });
  const applyNativeFieldOrderPreview = (nodes: NativeFormLayoutNode[]) => applyNativeFieldOrderPreviewFromTree({
    nodes, fieldOrder: context.fieldOrderDraft.value, movedGroups: context.changedFieldGroupDraft(),
    moveTargetDraft: context.fieldMoveTargetDraft, normalizeGroupTitle: normalizeFieldGroupTitle,
    isReadableGroupTitle: isReadableFieldGroupTitle, groupTitleMatches: fieldGroupTitleMatches,
    baseGroupTitleForField: (name) => context.fieldGroupBase.value[name] || context.fieldGroupDraft[name] || '',
  });
  const runtimeNativeFormLayoutNodes = () => {
    const storeContainers = resolveContractV2ContainerTree(context.v2ContractStore.value);
    const v2 = storeContainers.length ? null : resolveUnifiedPageContractV2(context.contract.value);
    const containers = storeContainers.length ? storeContainers : (Array.isArray(v2?.layoutContract?.containerTree) ? v2.layoutContract.containerTree : []);
    return containers.length ? normalizeContractV2ContainersForNativeFormFromTree(containers as NativeLayoutLikeNode[]) as NativeFormLayoutNode[]
      : (Array.isArray(context.contract.value?.views?.form?.layout) ? context.contract.value.views.form.layout as NativeFormLayoutNode[] : []);
  };
  const rawNativeFormLayoutNodes = computed<NativeFormLayoutNode[]>(() => {
    if (context.isContractFieldOrderEditable.value && layoutHasReadableFieldGroups(context.lowCodeFormLayoutBase.value)) {
      return mergeLowCodeLayoutWithRuntimeGroupShells(context.lowCodeFormLayoutBase.value, runtimeNativeFormLayoutNodes()) as NativeFormLayoutNode[];
    }
    const legacy = Array.isArray(context.contract.value?.views?.form?.layout) ? context.contract.value.views.form.layout as NativeFormLayoutNode[] : [];
    if (context.isContractFieldOrderEditable.value && legacy.length) return legacy;
    return runtimeNativeFormLayoutNodes();
  });
  const baseNativeFormLayoutNodes = computed(() => { void context.nativeLayoutVisibilityRevision.value; return filterVisibleNativeLayoutNodes(rawNativeFormLayoutNodes.value); });
  const nativeFormLayoutNodes = computed(() => context.isContractFieldOrderEditable.value
    && context.fieldOrderPreviewActive.value && context.fieldOrderDraft.value.length
    ? applyNativeFieldOrderPreview(baseNativeFormLayoutNodes.value) : baseNativeFormLayoutNodes.value);
  const useNativeFormTree = computed(() => nativeFormLayoutNodes.value.length > 0);
  const nativeFormRootColumns = computed<1|2|3>(() => context.isContractFieldOrderEditable.value
    ? context.formLayoutColumnsDraft.value : resolveNativeFormRootColumns(nativeFormLayoutNodes.value as NativeLayoutLikeNode[]));
  watch(baseNativeFormLayoutNodes, (nodes) => {
    const {keys,labels}=collectNativeFormDesignFields(nodes as NativeLayoutLikeNode[]);
    context.nativeFormDesignFieldKeys.value=keys; context.nativeFormDesignFieldLabels.value=labels;
  }, {immediate:true});
  const nativeNotebookPageCount=computed(()=>countNativeNodesByType(nativeFormLayoutNodes.value as NativeLayoutLikeNode[],'page'));
  const nativeGroupCount=computed(()=>countNativeNodesByType(nativeFormLayoutNodes.value as NativeLayoutLikeNode[],'group'));
  const nativeVisibleSectionTitles=computed(()=>collectNativeVisibleSectionTitles(nativeFormLayoutNodes.value as NativeLayoutLikeNode[]));
  const nativeVisibleFieldNames=computed(()=>collectNativeVisibleFieldNames(nativeFormLayoutNodes.value as NativeLayoutLikeNode[],(name,node)=>isNativeFieldVisible(name,node as NativeFormLayoutNode)));
  const showNativeDefaultSectionTitle=computed(()=>useNativeFormTree.value&&nativeVisibleFieldNames.value.size>0&&!nativeVisibleSectionTitles.value.length);
  const resolveNativeButtonLabel=(node:NativeFormLayoutNode)=>resolveNativeButtonLabelFromNode(node as NativeLayoutLikeNode,(field)=>context.formData[field]);
  const nativeFavoriteFieldNames=computed(()=>{const names=new Set<string>();collectNativeFavoriteFieldNames(rawNativeFormLayoutNodes.value,names);return names;});
  const nativeStatusbar=computed<NativeStatusbarVm>(()=>{
    const store=resolveContractV2MainData(context.v2ContractStore.value); const main=Object.keys(store).length?store:resolveUnifiedPageContractV2MainData(context.contract.value);
    return normalizeNativeFormStatusbar({recordId:context.recordId.value,formView:context.contract.value?.views?.form,
      fields:context.contract.value?.fields||{},formData:context.formData,mainData:main,fieldReadonly:(field)=>runtimeState(field).readonly,
      readonly:context.renderProfile.value==='readonly'||(context.recordId.value?!context.rights.value.write:!context.rights.value.create),
      fallback:normalizeWorkflowPhaseStatusbar(context.currentWorkflowContract())});
  });
  const setStatusbarValue=(value:string)=>{const field=nativeStatusbar.value.field;if(!field||nativeStatusbar.value.readonly)return;
    context.formData[field]=resolveStatusbarSelectionValue(context.contract.value?.fields?.[field],value);context.markFieldChanged(field);};
  const evaluateNativeModifierValue=(value:unknown)=>evaluateNativeModifierValueWithResolver(value,(field)=>context.formData[field]);
  const evaluateNativeActionVisibility=(row:Record<string,unknown>)=>isNativeActionVisible({row,currentState:String(context.formData.state||'').trim(),evaluateModifier:evaluateNativeModifierValue,resolveAction:context.contractActionFromNativeRow});
  function isNativeLayoutNodeVisible(node:NativeFormLayoutNode){return isNativeLayoutNodeVisibleFromNativeLayout({node,editable:context.isContractFieldOrderEditable.value,evaluateModifier:evaluateNativeModifierValue,normalizeGroupTitle:normalizeFieldGroupTitle,isGroupVisible:context.effectiveGroupVisible,isFieldVisibleInDraft:(name)=>Object.prototype.hasOwnProperty.call(context.fieldVisibilityDraft,name)?context.fieldVisibilityDraft[name]:undefined,resolveAction:context.contractActionFromNativeRow});}
  function isNativeFieldVisible(name:string,node?:NativeFormLayoutNode){return isNativeFieldVisibleFromNativeLayout({name,node,statusField:nativeStatusbar.value.field,showHud:context.showHud.value,renderProfile:context.renderProfile.value,isCreate:!context.recordId.value,isNodeVisible:(item)=>isNativeLayoutNodeVisible(item as NativeFormLayoutNode),resolveDescriptor:(field,item)=>item?(item as any).descriptor||context.contract.value?.fields?.[field]:context.contract.value?.fields?.[field],resolveFieldLabel:context.contractFieldLabel,semantic:context.fieldSemanticMeta,runtimeState,evaluatePolicy:(field,descriptor)=>evaluateFieldPolicy(context.contract.value,field,{required:Boolean(descriptor?.required),readonly:Boolean(descriptor?.readonly)},context.policyContext.value)});}
  const isWritableFieldVisible=(name:string)=>useNativeFormTree.value?nativeVisibleFieldNames.value.has(String(name||'').trim()):isFieldVisible(name);
  const currentNativeFieldOrder=()=>collectNativeVisibleFieldOrder(nativeFormLayoutNodes.value as NativeLayoutLikeNode[],(name,node)=>isNativeFieldVisible(name,node as NativeFormLayoutNode));
  const ensureFieldOrderDraftStartsFromCurrentLayout=()=>{if(!useNativeFormTree.value||context.fieldOrderPreviewActive.value)return;const current=currentNativeFieldOrder();if(!current.length)return;const known=new Set(current);context.fieldOrderDraft.value=[...current,...context.fieldOrderDraft.value.filter(name=>name&&!known.has(name))];};
  const formDataFieldNames=()=>{const store=resolveContractV2MainData(context.v2ContractStore.value);const main=Object.keys(store).length?store:resolveUnifiedPageContractV2MainData(context.contract.value);return collectFormDataFieldNames({contract:context.contract.value,fields:context.contract.value?.fields||{},rawNativeLayoutNodes:rawNativeFormLayoutNodes.value as NativeLayoutLikeNode[],layoutFieldNames:context.layoutNodes().filter(node=>node.kind==='field').map(node=>node.name),visibleFields:context.contractVisibleFields.value,statusField:nativeStatusbar.value.field,mainData:main});};
  return {baseNativeFormLayoutNodes,currentNativeFieldOrder,ensureFieldOrderDraftStartsFromCurrentLayout,evaluateNativeActionVisibility,evaluateNativeModifierValue,fieldModifierMap,formDataFieldNames,isFieldVisible,isNativeFavoriteField:(name:string)=>nativeFavoriteFieldNames.value.has(String(name||'').trim()),isNativeFieldVisible,isNativeLayoutNodeVisible,isWritableFieldVisible,nativeFormLayoutNodes,nativeFormRootColumns,nativeGroupCount,nativeNotebookPageCount,nativeStatusbar,nativeVisibleFieldNames,nativeVisibleSectionTitles,rawNativeFormLayoutNodes,resolveNativeButtonLabel,runtimeFieldStates,runtimeNativeFormLayoutNodes,runtimeState,setStatusbarValue,showNativeDefaultSectionTitle,useNativeFormTree};
}

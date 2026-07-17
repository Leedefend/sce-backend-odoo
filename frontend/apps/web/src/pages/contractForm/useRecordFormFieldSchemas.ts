/* eslint-disable @typescript-eslint/no-explicit-any, prefer-const */
import { computed, type ComputedRef, type Ref } from 'vue';
import type { ActionContract, FieldDescriptor } from '@sc/schema';
import { resolveContractV2ValueSource, type ContractV2NormalizedStore } from '../../app/contracts/v2';
import type { NativeFormLayoutNode } from '../../components/template/NativeFormTreeRenderer.vue';
import type { FormSectionFieldSchema } from '../../components/template/formSection.types';
import { createFormSectionFieldSchemaBuilder } from '../../components/template/formSection.adapter';
import { resolveInputPlaceholder } from '../../components/template/placeholder.mapper';
import { resolveFieldSpanClass } from '../../components/template/fieldSpan.mapper';
import { mapDescriptorSelectionOptions, mapRelationOptions } from '../../components/template/option.mapper';
import { evaluateFieldPolicy } from '../../app/contractPolicies';
import { collectUnifiedPageContractV2FieldContainerStatus } from '../../app/contracts/unifiedPageContractV2';
import {
  applyReadonlyFieldValues, buildLegacyLayoutNodes, buildNativeFieldSchemas, nativeFieldPresentation,
  nativeNodeFieldDescriptor as nativeNodeFieldDescriptorFromNode, nativeNodeWidget, nativeNodeWidgetSemantics,
  type NativeLayoutLikeNode,
} from './nativeLayoutUtils';
import { fieldType } from './fieldUtils';
import type { LayoutNode, LowCodeFieldSize } from './types';

export function useRecordFormFieldSchemas(context: {
  contract: Ref<ActionContract|null>; v2ContractStore: Ref<ContractV2NormalizedStore|null>;
  nativeFormLayoutNodes: ComputedRef<NativeFormLayoutNode[]>; isNativeFieldVisible:(name:string,node?:NativeFormLayoutNode)=>boolean;
  isNativeLayoutNodeVisible:(node:NativeFormLayoutNode)=>boolean; runtimeState:(name:string)=>{readonly:boolean;required:boolean};
  recordId:ComputedRef<number|null>; rights:ComputedRef<{create:boolean;write:boolean}>;
  contractFieldLabel:(name:string)=>string; isContractFieldOrderEditable:ComputedRef<boolean>;
  effectiveFieldSize:(name:string)=>LowCodeFieldSize; rememberFormConfigFieldLabel:(name:string,label:string)=>void;
  fieldOrderPreviewActive:Ref<boolean>; fieldOrderDraft:Ref<string[]>; formData:Record<string,unknown>;
  isFieldVisible:(name:string)=>boolean; contractVisibleFields:ComputedRef<string[]>; coreFieldNames:ComputedRef<string[]>;
  advancedFieldNames:ComputedRef<string[]>; evaluatePolicyContext:ComputedRef<any>; runtimeFieldStates:ComputedRef<Record<string,any>>;
  validationErrors:Ref<string[]>;
  relationOptionsForField:(name:string)=>any[]; relationCreateMode:(descriptor?:FieldDescriptor)=>'none'|'quick'|'page';
  relationInlineCreate:(descriptor?:FieldDescriptor)=>{enabled:boolean;createOnNoMatch:boolean;nameField:string;match?:string};
  relationKeyword:(name:string)=>string; canOpenRelationRecordForm:(name:string,descriptor?:FieldDescriptor)=>boolean;
  relationUiLabel:(descriptor:FieldDescriptor|undefined,key:string,fallback?:string)=>string;
  inputFieldValue:(name:string)=>string; many2oneValue:(name:string)=>string;
  toDateInputValue:(value:unknown)=>string; toDatetimeInputValue:(value:unknown)=>string;
}) {
  const nativeNodeFieldDescriptor=(node:NativeFormLayoutNode,fallback?:FieldDescriptor)=>nativeNodeFieldDescriptorFromNode(node as NativeLayoutLikeNode,fallback,context.contractFieldLabel);
  const nativeLayoutNodeToFieldNode=(node:NativeFormLayoutNode,index:number):LayoutNode|null=>{
    const name=String(node?.name||'').trim(); if(!name||!context.isNativeFieldVisible(name,node))return null;
    const descriptor=nativeNodeFieldDescriptor(node,context.contract.value?.fields?.[name]); if(!descriptor)return null;
    const source=node as Record<string,unknown>; const state=context.runtimeState(name);
    const nativeReadonly=Boolean(source.readonly); const nativeRequired=Boolean(source.required);
    const resolved=evaluateFieldPolicy(context.contract.value,name,{required:Boolean(descriptor.required),readonly:Boolean(descriptor.readonly)},context.evaluatePolicyContext.value);
    const presentation=nativeFieldPresentation({node:source,descriptor,resolveFieldLabel:context.contractFieldLabel,
      editable:context.isContractFieldOrderEditable.value,effectiveFieldSize:context.effectiveFieldSize});
    context.rememberFormConfigFieldLabel(name,presentation.label);
    return {key:`native_field_${name}_${index}`,kind:'field',name,label:presentation.label,
      readonly:Boolean(nativeReadonly||resolved.readonly||state.readonly||(context.recordId.value?!context.rights.value.write:!context.rights.value.create)),
      required:Boolean(nativeRequired||resolved.required||state.required||descriptor.required),widget:nativeNodeWidget(source),
      widgetSemantics:nativeNodeWidgetSemantics(source),spanClass:presentation.spanClass,descriptor};
  };
  const v2FieldValue=(name:string)=>{const key=String(name||'').trim();if(!key||!context.v2ContractStore.value?.widgetsByFieldCode.has(key))return{found:false,value:undefined};
    const source=resolveContractV2ValueSource(context.v2ContractStore.value).values;if(!Object.prototype.hasOwnProperty.call(source,key))return{found:false,value:undefined};return{found:true,value:source[key]};};
  let buildSectionFieldSchemas:(fields:any[])=>FormSectionFieldSchema[];
  const nativeFieldSchemasForNodes=(nodes:NativeFormLayoutNode[])=>buildNativeFieldSchemas({nodes:nodes as NativeLayoutLikeNode[],mapNode:(node,index)=>nativeLayoutNodeToFieldNode(node as NativeFormLayoutNode,index),buildSchemas:buildSectionFieldSchemas,applyReadonlyValues:(schemas)=>applyReadonlyFieldValues(schemas,v2FieldValue),orderActive:context.isContractFieldOrderEditable.value&&context.fieldOrderPreviewActive.value,fieldOrder:context.fieldOrderDraft.value,favoriteActive:(name)=>Boolean(context.formData[name]),favoriteReadonly:(field)=>Boolean(field.readonly)});
  const layoutNodes=computed<LayoutNode[]>(()=>buildLegacyLayoutNodes({fields:context.contract.value?.fields||{},order:context.contract.value?.views?.form?.layout||[],containerStatus:collectUnifiedPageContractV2FieldContainerStatus(context.contract.value),visibleFields:context.contractVisibleFields.value,fallbackFieldNames:[...context.coreFieldNames.value,...context.advancedFieldNames.value],isCreate:!context.recordId.value,readonly:context.recordId.value?!context.rights.value.write:!context.rights.value.create,resolveFieldLabel:context.contractFieldLabel,evaluatePolicy:(name,descriptor)=>evaluateFieldPolicy(context.contract.value,name,{required:Boolean(descriptor?.required),readonly:Boolean(descriptor?.readonly)},context.evaluatePolicyContext.value),runtimeState:(name)=>context.runtimeFieldStates.value[name]||{invisible:false,readonly:false,required:false}}));
  buildSectionFieldSchemas=createFormSectionFieldSchemaBuilder({
    resolveFieldType:(descriptor)=>fieldType(descriptor)||'char',resolveRequired:(field)=>Boolean((field as LayoutNode).required),
    resolveSpanClass:(field)=>(field as LayoutNode).spanClass||resolveFieldSpanClass({fieldName:field.name,fieldType:fieldType(field.descriptor)}),
    resolveRawValue:(name)=>context.formData[name],resolveMany2oneValue:context.many2oneValue,
    normalizeDateInputValue:context.toDateInputValue,normalizeDatetimeInputValue:context.toDatetimeInputValue,
    resolveTextInputValue:context.inputFieldValue,resolveInputPlaceholder,
    resolveHelpText:(field)=>String((field.descriptor as Record<string,unknown>|undefined)?.help||'').trim(),
    resolveErrorText:(field)=>context.validationErrors.value.find(message=>String(message||'').includes(String(field.label||'').trim()))||'',
    resolveSelectionOptions:mapDescriptorSelectionOptions,resolveRelationOptions:(name)=>mapRelationOptions(context.relationOptionsForField(name)),
    resolveRelationCreateMode:(_name,descriptor)=>context.relationCreateMode(descriptor),
    resolveRelationInlineCreate:(_name,descriptor)=>context.relationInlineCreate(descriptor),resolveRelationTextValue:context.relationKeyword,
    resolveCanOpenRelationRecord:context.canOpenRelationRecordForm,
    resolveRelationRecordOpenLabel:(_name,descriptor)=>context.relationUiLabel(descriptor,'open_existing','维护当前项'),
    resolveRelationSearchLabel:(_name,descriptor)=>context.relationUiLabel(descriptor,'search_more'),
    resolveRelationCreateLabel:(_name,descriptor)=>{const mode=context.relationCreateMode(descriptor);return mode==='page'?context.relationUiLabel(descriptor,'create_and_edit'):mode==='quick'?context.relationUiLabel(descriptor,'quick_create'):'';},
    resolveRelationInlineCreateLabel:(_name,descriptor,keyword)=>{const template=context.relationUiLabel(descriptor,'inline_create');const label=String(keyword||'').trim();return template.includes('%s')?template.replace('%s',label):template||label;},
    many2oneCreateToken:'__create__',many2oneSearchToken:'__search_more__',many2oneOpenToken:'__open_record__',
  });
  return { layoutNodes, nativeFieldSchemasForNodes };
}

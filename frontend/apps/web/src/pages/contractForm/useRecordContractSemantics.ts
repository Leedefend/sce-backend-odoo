/* eslint-disable @typescript-eslint/no-explicit-any */
import { computed, nextTick, ref, watch, type ComputedRef, type Ref } from 'vue';
import type { ActionContract } from '@sc/schema';
import type { ContractV2NormalizedStore } from '../../app/contracts/v2';
import { intentRequest } from '../../api/intents';
import { config } from '../../config';
import { ErrorCodes } from '../../app/error_codes';
import { findActionMeta } from '../../app/menu';
import { resolveSceneValidationSuggestedAction } from '../../app/sceneValidationRecoveryStrategy';
import { findSceneReadyEntry, resolveFormSceneReady } from '../../app/resolvers/sceneReadyResolver';
import { isCoreSceneStrictMode } from '../../app/contractStrictMode';
import { resolveUnifiedPageContractV2FieldGroups, resolveUnifiedPageContractV2VisibleFields } from '../../app/contracts/unifiedPageContractV2';
import { collectPrimaryActionRequiredFields } from './contractRuntimeVm';
import { dictOrEmpty } from './recordUtils';
import {
  normalizeContractFieldSemantics,
  normalizeSemanticFieldGroups,
  resolveFieldSemanticMeta,
  semanticFieldNamesBySurfaceRole,
  type FieldSemanticMeta,
  type SemanticFieldGroup,
} from './nativeLayoutUtils';
import {
  buildSceneValidationPanel,
  sceneValidationErrorPrefix,
  strictContractDefaultsSummary as strictContractDefaultsSummaryFromGuard,
  strictContractGuardFromSceneReadyEntry,
  strictContractMissingSummary as strictContractMissingSummaryFromGuard,
} from './sceneValidation';

export function useRecordContractSemantics(context: {
  contract: Ref<ActionContract | null>;
  v2ContractStore: Ref<ContractV2NormalizedStore | null>;
  route: any;
  session: any;
  actionId: ComputedRef<number | null>;
  recordId: ComputedRef<number | null>;
  model: ComputedRef<string>;
  renderProfile: ComputedRef<string>;
  runtimeRoleCode: ComputedRef<string>;
  validationErrors: Ref<string[]>;
  isProjectIntakeCreateMode: ComputedRef<boolean>;
  intentConfirmationRef: Ref<{ confirm: (input: { actionLabel: string; message: string }) => Promise<boolean> } | null>;
  formConflict: Ref<boolean>;
  layoutNodes: () => Array<{ kind: string; name: string; label: string }>;
  reload: () => Promise<unknown>;
  focusValidationError: (message: string, fields: Array<{ kind: string; name: string; label: string }>) => void;
}) {
  const semanticFieldGroups = computed<Record<string, SemanticFieldGroup>>(() => {
    const snapshot = dictOrEmpty(context.v2ContractStore.value?.snapshot);
    const source = Object.keys(snapshot).length ? snapshot : context.contract.value;
    const raw = resolveUnifiedPageContractV2FieldGroups(source);
    const profile = ((context.contract.value?.views?.form as Record<string, unknown> | undefined)?.form_profile
      || (context.contract.value as Record<string, unknown> | undefined)?.form_profile) as Record<string, unknown> | undefined;
    return normalizeSemanticFieldGroups(raw, profile);
  });
  const contractFieldSemantics = computed<Record<string, FieldSemanticMeta>>(() => normalizeContractFieldSemantics(
    (context.contract.value as Record<string, unknown> | null)?.field_semantics,
  ));
  const fieldSemanticMeta = (name: string) => resolveFieldSemanticMeta(
    name,
    contractFieldSemantics.value,
    context.contract.value?.fields?.[name],
  );
  const coreFieldNames = computed(() => semanticFieldNamesBySurfaceRole(
    context.contract.value?.fields, contractFieldSemantics.value, semanticFieldGroups.value, 'core',
  ));
  const advancedFieldNames = computed(() => semanticFieldNamesBySurfaceRole(
    context.contract.value?.fields, contractFieldSemantics.value, semanticFieldGroups.value, 'advanced',
  ));
  const hasAdvancedFields = computed(() => advancedFieldNames.value.length > 0);
  const policyRequiredFields = computed(() => collectPrimaryActionRequiredFields(context.contract.value?.action_policies));
  const sceneReadySceneKey = computed(() => String(
    context.route.query.scene_key || context.route.params.sceneKey
    || findActionMeta(context.session.menuTree, context.actionId.value)?.scene_key
    || findActionMeta(context.session.menuTree, context.actionId.value)?.sceneKey
    || context.session.currentAction?.scene_key || context.session.currentAction?.sceneKey || '',
  ).trim());
  const sceneReadyHydrateRequested = ref(false);
  const useSceneFormAugmentations = computed(() => context.isProjectIntakeCreateMode.value || Boolean(sceneReadySceneKey.value));
  const sceneReadyEntry = computed<Record<string, unknown> | null>(() => {
    if (!useSceneFormAugmentations.value) return null;
    return sceneReadySceneKey.value ? findSceneReadyEntry(context.session.sceneReadyContractV1, sceneReadySceneKey.value) : null;
  });
  const strictContractMode = computed(() => isCoreSceneStrictMode(sceneReadySceneKey.value, sceneReadyEntry.value));
  const strictContractGuard = computed<Record<string, unknown>>(() => strictContractGuardFromSceneReadyEntry(sceneReadyEntry.value));
  const strictContractMissingSummary = computed(() => strictContractMissingSummaryFromGuard(strictContractMode.value, strictContractGuard.value));
  const strictContractDefaultsSummary = computed(() => strictContractDefaultsSummaryFromGuard(strictContractMode.value, strictContractGuard.value));
  const sceneValidationRequiredFields = computed(() => useSceneFormAugmentations.value
    ? resolveFormSceneReady(sceneReadyEntry.value).requiredFields : []);
  const sceneReadyFormSurface = computed(() => resolveFormSceneReady(useSceneFormAugmentations.value ? sceneReadyEntry.value : null));
  watch(() => [sceneReadySceneKey.value, sceneReadyFormSurface.value.sceneBlocks.length], async ([sceneKey, blockCount]) => {
    if (!sceneKey || Number(blockCount || 0) > 0 || sceneReadyHydrateRequested.value) return;
    sceneReadyHydrateRequested.value = true;
    try {
      const result = await intentRequest<Record<string, unknown>>({
        intent: 'system.init',
        params: { scene: 'web', with_preload: false, scene_ready_mode: 'full', with: ['workspace_home'],
          ...(config.startupRootXmlid ? { root_xmlid: config.startupRootXmlid } : {}), scene_key: sceneKey },
        meta: { startup_chain_bypass: true },
      });
      const readyContract = result.scene_ready_contract_v1;
      if (readyContract && typeof readyContract === 'object' && Array.isArray((readyContract as Record<string, unknown>).scenes)) {
        context.session.sceneReadyContractV1 = readyContract;
      }
    } catch { /* The base form remains usable without optional scene hydration. */ }
  }, { immediate: true });
  const validationRequiredFields = computed(() => {
    const fields = new Set<string>();
    const rules = Array.isArray(context.contract.value?.validation_rules) ? context.contract.value.validation_rules : [];
    rules.forEach((rule) => {
      if (!rule || typeof rule !== 'object') return;
      const item = rule as Record<string, unknown>;
      if (String(item.code || '').trim().toUpperCase() !== 'REQUIRED') return;
      const field = String(item.field || '').trim();
      const profiles = Array.isArray(item.when_profiles) ? item.when_profiles.map((value) => String(value || '').trim().toLowerCase()) : [];
      if (field && (!profiles.length || profiles.includes(context.renderProfile.value))) fields.add(field);
    });
    sceneValidationRequiredFields.value.forEach((field) => fields.add(field));
    return fields;
  });
  const sceneValidationRequiredErrorPrefix = sceneValidationErrorPrefix(ErrorCodes.SCENE_VALIDATION_REQUIRED);
  const sceneValidationPanel = computed(() => buildSceneValidationPanel({
    enabled: useSceneFormAugmentations.value, validationErrors: context.validationErrors.value,
    errorCode: ErrorCodes.SCENE_VALIDATION_REQUIRED,
    suggestedAction: resolveSceneValidationSuggestedAction({
      modelName: context.model.value, recordId: context.recordId.value, actionId: context.actionId.value,
      sceneKey: String(context.route.query.scene_key || context.route.params.sceneKey || '').trim(), roleCode: context.runtimeRoleCode.value,
    }),
  }));
  const nonSceneValidationErrors = computed(() => context.validationErrors.value.filter(
    (item) => !String(item || '').trim().startsWith(sceneValidationRequiredErrorPrefix),
  ));
  const focusValidationError = (message: string) => context.focusValidationError(message, context.layoutNodes());
  const focusFirstValidationError = async () => {
    await nextTick();
    const message = nonSceneValidationErrors.value[0] || context.validationErrors.value[0] || '';
    if (message) focusValidationError(message);
  };
  const reloadLatestRecord = async () => {
    const confirmed = await context.intentConfirmationRef.value?.confirm({
      actionLabel: '加载最新数据', message: '加载最新数据会放弃当前页面尚未保存的修改，是否继续？',
    });
    if (!confirmed) return;
    context.formConflict.value = false;
    await context.reload();
  };
  const contractVisibleFields = computed(() => {
    const snapshot = dictOrEmpty(context.v2ContractStore.value?.snapshot);
    return resolveUnifiedPageContractV2VisibleFields(Object.keys(snapshot).length ? snapshot : context.contract.value);
  });
  return {
    advancedFieldNames, contractVisibleFields, coreFieldNames, fieldSemanticMeta, focusFirstValidationError,
    focusValidationError, hasAdvancedFields, nonSceneValidationErrors, policyRequiredFields, reloadLatestRecord, sceneReadyFormSurface,
    sceneValidationPanel, sceneValidationRequiredFields, strictContractDefaultsSummary, strictContractGuard,
    strictContractMissingSummary, strictContractMode, useSceneFormAugmentations, validationRequiredFields,
  };
}

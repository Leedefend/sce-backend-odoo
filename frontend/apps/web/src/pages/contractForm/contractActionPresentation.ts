import type { ActionContract } from '@sc/schema';
import type { ContractV2ButtonStatus } from '../../app/contracts/v2/types';
import { detectObjectMethodFromActionKey, normalizeActionKind, parseMaybeJsonRecord, toPositiveInt } from '../../app/contractRuntime';
import { resolveUnifiedPageContractV2 } from '../../app/contracts/unifiedPageContractV2';
import { normalizeSceneActionProtocol } from '../../app/sceneActionProtocol';
import { evaluateActionPolicy } from '../../app/contractPolicies';
import {
  normalizeActionLabel,
  normalizeActionSafety,
  normalizeRequiredParams,
  resolveV2ButtonStatus,
} from './actionContract';
import { selectAuthoritativeBusinessActionRows } from './authoritativeBusinessActionRows';
import { workflowActionMethodAliases } from './workflowContract';
import type { ContractAction } from './types';

type ActionPolicy = { visible: boolean; enabled: boolean; reason: string; semantic: string };

export function buildContractFormActions(params: {
  contract: ActionContract | null;
  model: string;
  recordId: number;
  renderProfile: 'create' | 'edit' | 'readonly';
  sceneReadyActions: Array<Record<string, unknown>>;
  v2ButtonStatus: Record<string, ContractV2ButtonStatus>;
  workflowActionRows: Array<Record<string, unknown>>;
  policyContext: Parameters<typeof evaluateActionPolicy>[2];
  evaluateNativeActionVisibility: (row: Record<string, unknown>) => boolean;
  isTierValidationActionHidden: (methodName: string) => boolean;
}): ContractAction[] {
  const mapSceneReadyAction = (row: Record<string, unknown>): ContractAction | null => {
    const protocol = normalizeSceneActionProtocol(row);
    const key = String(row.key || '').trim();
    if (!key) return null;
    const target = parseMaybeJsonRecord(row.target);
    const intent = String(row.intent || '').trim().toLowerCase();
    const presentation = parseMaybeJsonRecord(row.presentation);
    const presentationTier = String(presentation.tier || row.tier || '').trim().toLowerCase();
    const placement = String(row.placement || 'header').trim().toLowerCase();
    const actionId = toPositiveInt(target.action_id) ?? toPositiveInt(target.ref);
    const hasOpenTarget = Boolean(actionId || String(target.url || '').trim() || String(target.route || '').trim());
    return {
      key,
      label: String(row.label || key),
      kind: hasOpenTarget || intent === 'ui.contract' ? 'open' : 'object',
      level: placement,
      selection: 'none',
      actionId,
      methodName: detectObjectMethodFromActionKey(key, String(target.method || '').trim()),
      targetModel: String(target.model || params.model || '').trim(),
      context: parseMaybeJsonRecord(target.context_raw),
      domainRaw: String(target.domain_raw || '').trim(),
      target: String(target.target || '').trim(),
      url: String(target.url || target.route || '').trim(),
      enabled: true,
      hint: '',
      intent,
      semantic: presentationTier === 'primary' ? 'primary_action' : presentationTier === 'secondary' ? 'secondary_action' : '',
      sourceWidgetId: String(row.sourceWidgetId || row.source_widget_id || '').trim(),
      clientMode: String(target.mode || target.client_mode || row.clientMode || row.client_mode || '').trim(),
      visibleProfiles: ['create', 'edit', 'readonly'],
      requiredParams: normalizeRequiredParams(row.required_params),
      requiresReason: row.requires_reason === true,
      presentationTier,
      destructive: presentation.semantic === 'destructive',
      requiresConfirmation: presentation.requires_confirmation === true,
      actionSafety: normalizeActionSafety(row.action_safety),
      mutation: protocol?.mutation,
      refreshPolicy: protocol?.refresh_policy,
    };
  };

  const nativeFormContract = params.contract?.views?.form as Record<string, unknown> | undefined;
  const { workflowRows, nativeRows } = selectAuthoritativeBusinessActionRows(nativeFormContract, params.workflowActionRows);
  const workflowMethods = new Set<string>();
  workflowRows.forEach((row) => {
    const method = String(parseMaybeJsonRecord(row.payload).method || '').trim();
    if (method) workflowMethods.add(method);
    workflowActionMethodAliases(String(row.key || '').trim()).forEach((alias) => workflowMethods.add(alias));
  });
  const merged: Array<Record<string, unknown>> = [...workflowRows, ...nativeRows];
  if (Array.isArray(params.contract?.buttons)) merged.push(...params.contract.buttons as Array<Record<string, unknown>>);
  if (Array.isArray(params.contract?.toolbar?.header)) merged.push(...params.contract.toolbar.header as Array<Record<string, unknown>>);
  if (Array.isArray(params.contract?.toolbar?.sidebar)) merged.push(...params.contract.toolbar.sidebar as Array<Record<string, unknown>>);
  if (Array.isArray(params.contract?.toolbar?.footer)) merged.push(...params.contract.toolbar.footer as Array<Record<string, unknown>>);
  const v2ActionRuleList = parseMaybeJsonRecord(resolveUnifiedPageContractV2(params.contract)?.actionContract).actionRuleList;
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
      const buttonName = String(button.name || button.method || '').trim();
      if (sourceWidgetId !== 'page.header' && targetScope !== 'footer' && !(sourceWidgetId === 'page.root' && buttonName)) return;
      const buttonType = String(button.type || button.buttonType || '').trim();
      merged.push({
        key,
        label: String(row.label || key).trim() || key,
        kind: buttonType === 'server' || buttonType === 'server_action' ? 'server' : buttonName ? 'object' : clientMode ? 'client' : 'open',
        intent: String(row.intent || '').trim(),
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
  merged.push(...params.sceneReadyActions);

  const dedup = new Set<string>();
  const out: ContractAction[] = [];
  for (const row of merged) {
    if (params.sceneReadyActions.includes(row) || (params.sceneReadyActions.length && !String(row.key || '').trim())) {
      const mapped = mapSceneReadyAction(row);
      if (!mapped || dedup.has(mapped.key)) continue;
      const status = resolveV2ButtonStatus(mapped.key, params.v2ButtonStatus);
      if (status?.visible === false) continue;
      if (status?.disabled === true) {
        mapped.enabled = false;
        mapped.hint = status.reasonCode || mapped.hint || 'disabled_by_status_contract';
      }
      dedup.add(mapped.key);
      out.push(mapped);
      continue;
    }
    const rowLabel = normalizeActionLabel(row.label);
    const keyBase = String(row.key || row.name || rowLabel || '').trim();
    const key = dedup.has(keyBase) && rowLabel ? `${keyBase}:${rowLabel}` : keyBase;
    if (!key || dedup.has(key)) continue;
    dedup.add(key);
    const payload = parseMaybeJsonRecord(row.payload);
    const protocol = normalizeSceneActionProtocol(row);
    const targetRaw = parseMaybeJsonRecord(row.target);
    const effectiveKind = protocol?.mutation ? 'mutation' : normalizeActionKind(row.kind);
    const level = String(row.level || 'body').trim().toLowerCase();
    const actionId = toPositiveInt(payload.action_id) ?? toPositiveInt(payload.ref) ?? toPositiveInt(row.actionId) ?? toPositiveInt(row.action_id);
    const methodName = detectObjectMethodFromActionKey(key, String(payload.method || row.method || '').trim());
    if (row.workflow_contract_action !== true && methodName && workflowMethods.has(methodName)) continue;
    if (params.isTierValidationActionHidden(methodName)) continue;
    const selectionRaw = String(row.selection || 'none').trim().toLowerCase();
    const selection = selectionRaw === 'single' || selectionRaw === 'multi' ? selectionRaw : 'none';
    const visibleProfiles = (Array.isArray(row.visible_profiles) ? row.visible_profiles : ['create', 'edit'])
      .map((item) => String(item || '').trim().toLowerCase())
      .filter((item): item is 'create' | 'edit' | 'readonly' => ['create', 'edit', 'readonly'].includes(item));
    const requiredParams = normalizeRequiredParams(row.required_params);
    const presentation = parseMaybeJsonRecord(row.presentation);
    const presentationTier = String(presentation.tier || '').trim().toLowerCase();
    const policy = evaluateActionPolicy(params.contract, key, params.policyContext) as ActionPolicy;
    if (!policy.visible || !params.evaluateNativeActionVisibility(row)) continue;
    const status = resolveV2ButtonStatus(key, params.v2ButtonStatus);
    if (status?.visible === false) continue;
    const contractAllowed = typeof row.allowed === 'boolean' ? row.allowed : true;
    const needRecord = ['object', 'server', 'mutation'].includes(effectiveKind) || ['row', 'smart'].includes(level);
    const enabled = contractAllowed && policy.enabled && (!needRecord || Boolean(params.recordId)) && status?.disabled !== true;
    out.push({
      key,
      label: normalizeActionLabel(row.label, key),
      kind: effectiveKind,
      level,
      selection,
      actionId,
      methodName,
      targetModel: String(row.target_model || row.model || params.model || '').trim(),
      context: parseMaybeJsonRecord(payload.context_raw),
      domainRaw: String(payload.domain_raw || '').trim(),
      target: String(payload.target || '').trim(),
      url: String(payload.url || row.url || '').trim(),
      enabled,
      hint: status?.disabled === true
        ? status.reasonCode || 'disabled_by_status_contract'
        : needRecord && !params.recordId
          ? 'requires record id'
          : contractAllowed
            ? String(row.warning_message || policy.reason || '').trim()
            : String(row.blocked_message || row.reason || row.reason_code || '').trim(),
      intent: String(row.intent || '').trim(),
      semantic: policy.semantic,
      sourceWidgetId: String(row.sourceWidgetId || row.source_widget_id || '').trim(),
      clientMode: String(targetRaw.mode || targetRaw.client_mode || row.clientMode || row.client_mode || '').trim(),
      visibleProfiles,
      requiredParams,
      requiresReason: row.requires_reason === true || requiredParams.includes('reason'),
      presentationTier,
      destructive: presentation.semantic === 'destructive',
      requiresConfirmation: presentation.requires_confirmation === true,
      actionSafety: normalizeActionSafety(row.action_safety),
      mutation: protocol?.mutation,
      refreshPolicy: protocol?.refresh_policy,
    });
  }
  const tierOrder: Record<string, number> = { primary: 0, secondary: 1, overflow: 2 };
  return out.sort((a, b) => (tierOrder[a.presentationTier || ''] ?? 3) - (tierOrder[b.presentationTier || ''] ?? 3)
    || a.level.localeCompare(b.level) || a.label.localeCompare(b.label, 'zh-CN'))
    .filter((item) => (!item.visibleProfiles.length || item.visibleProfiles.includes(params.renderProfile)) && item.selection === 'none' && item.level !== 'toolbar');
}

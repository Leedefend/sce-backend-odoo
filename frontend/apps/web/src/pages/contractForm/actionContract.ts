import type { ContractV2ButtonStatus } from '../../app/contracts/v2';
import { parseMaybeJsonRecord } from '../../app/contractRuntime';
import { pickContractNavQuery } from '../../app/navigationContext';
import type { ContractAction, ContractFieldGovernanceAction, ContractPromptField } from './types';

export function normalizeActionSafety(value: unknown): ContractAction['actionSafety'] | undefined {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return undefined;
  const row = value as Record<string, unknown>;
  const classificationRaw = String(row.classification || '').trim().toLowerCase();
  const classification = classificationRaw === 'danger' ? 'danger' : classificationRaw === 'safe' ? 'safe' : '';
  if (!classification) return undefined;
  return {
    classification,
    requiresConfirm: row.requires_confirm === true,
    confirmMessage: String(row.confirm_message || '').trim(),
    reasonCode: String(row.reason_code || '').trim(),
  };
}

export function normalizeRequiredParams(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => String(item || '').trim())
    .filter(Boolean);
}

export function normalizeActionLabel(raw: unknown, fallback = ''): string {
  const text = String(raw ?? '').trim();
  if (!text) return String(fallback || '').trim();
  if (!text.startsWith('{') || !text.includes('label')) return text;
  const match = text.match(/['"]label['"]\s*:\s*['"]([^'"]+)['"]/);
  if (match?.[1]) return String(match[1]).trim();
  return text;
}

export function isTierValidationActionHidden(params: {
  methodName: string;
  validationStatus: unknown;
  canReview: unknown;
}) {
  const method = String(params.methodName || '').trim();
  const validationStatus = String(params.validationStatus || '').trim();
  if ((method === 'validate_tier' || method === 'reject_tier') && !params.canReview) return true;
  return (
    (method === 'action_confirm' || method === 'action_submit' || method === 'button_confirm')
    && ['waiting', 'pending', 'validated'].includes(validationStatus)
  );
}

export function contractActionRuleClientMode(rule: Record<string, unknown>) {
  const target = parseMaybeJsonRecord(rule.target);
  return String(target.mode || target.client_mode || rule.mode || rule.client_mode || '').trim();
}

export function contractActionRuleKey(rule: Record<string, unknown>) {
  return String(rule.actionKey || rule.key || rule.actionId || '').trim();
}

export function contractActionRuleControl(rule: Record<string, unknown>) {
  const target = parseMaybeJsonRecord(rule.target);
  return parseMaybeJsonRecord(target.control || target.ui_control || rule.control || rule.ui_control);
}

export function contractPromptFieldsFromRule(rule: Record<string, unknown>): ContractPromptField[] {
  const target = parseMaybeJsonRecord(rule.target);
  const promptSchema = parseMaybeJsonRecord(target.prompt_schema || target.promptSchema || rule.prompt_schema || rule.promptSchema);
  const fields = Array.isArray(promptSchema.fields) ? promptSchema.fields : [];
  return fields
    .map((raw) => {
      if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null;
      const field = raw as Record<string, unknown>;
      const name = String(field.name || '').trim();
      if (!name) return null;
      const options = Array.isArray(field.options)
        ? field.options
          .map((item) => parseMaybeJsonRecord(item))
          .map((row) => ({
            value: String(row.value || '').trim(),
            label: String(row.label || row.value || '').trim(),
          }))
          .filter((row) => row.value)
        : [];
      return {
        name,
        label: String(field.label || name).trim(),
        required: field.required !== false,
        defaultValue: String(field.default || '').trim(),
        options,
      };
    })
    .filter((field): field is ContractPromptField => Boolean(field));
}

export function contractPromptParamsFromRule(
  rule: Record<string, unknown>,
  providedValues: Record<string, string> = {},
): Record<string, unknown> | null {
  const target = parseMaybeJsonRecord(rule.target);
  const params = { ...parseMaybeJsonRecord(target.params || rule.params) };
  for (const field of contractPromptFieldsFromRule(rule)) {
    const rawValue = String(providedValues[field.name] || '').trim();
    const optionMatch = field.options.find((row) => (
      String(row.value || '').trim() === rawValue
      || String(row.label || '').trim() === rawValue
    ));
    const value = optionMatch ? String(optionMatch.value || '').trim() : rawValue;
    if (field.required && !value) return null;
    if (value) params[field.name] = value;
  }
  return params;
}

export function buildContractFieldActionsFromRules(params: {
  rules: Record<string, unknown>[];
  fieldName: string;
  mode: string;
  visibilityDraft: Record<string, boolean>;
  busy: boolean;
}): ContractFieldGovernanceAction[] {
  const mode = String(params.mode || '').trim();
  if (!mode) return [];
  const fieldKey = String(params.fieldName || '').trim();
  const fieldWidgetId = `field.${fieldKey}`;
  return params.rules
    .filter((rule) => {
      const triggerType = String(rule.triggerType || rule.trigger_type || '').trim();
      if (triggerType && !['change', 'select', 'click'].includes(triggerType)) return false;
      const sourceWidgetId = String(rule.sourceWidgetId || rule.source_widget_id || '').trim();
      const targetIds = Array.isArray(rule.targetIds || rule.target_ids) ? (rule.targetIds || rule.target_ids) as unknown[] : [];
      if (sourceWidgetId !== fieldWidgetId && !targetIds.map((item) => String(item)).includes(fieldWidgetId)) return false;
      const expectedMode = contractActionRuleClientMode(rule);
      return !expectedMode || expectedMode === mode;
    })
    .map((rule) => {
      const control = contractActionRuleControl(rule);
      const key = contractActionRuleKey(rule);
      const value = String(control.value || key).trim();
      return {
        key,
        label: String(control.label || rule.label || key).trim(),
        value,
        checked: fieldKey && Object.prototype.hasOwnProperty.call(params.visibilityDraft, fieldKey)
          ? params.visibilityDraft[fieldKey] === (value === 'show')
          : control.checked === true,
        disabled: control.disabled === true || params.busy,
        title: String(control.title || '').trim(),
        raw: rule,
      };
    });
}

export function buildFormSettingsFieldActions(params: {
  fieldName: string;
  existingActions?: ContractFieldGovernanceAction[];
  visibilityDraft: Record<string, boolean>;
  busy: boolean;
}): ContractFieldGovernanceAction[] {
  const fieldKey = String(params.fieldName || '').trim();
  if (!fieldKey) return [];
  if (params.existingActions?.length) {
    return params.existingActions.map((action) => ({
      ...action,
      checked: Object.prototype.hasOwnProperty.call(params.visibilityDraft, fieldKey)
        ? params.visibilityDraft[fieldKey] === (action.value === 'show')
        : Boolean(action.checked),
      disabled: Boolean(action.disabled) || params.busy,
    }));
  }
  const visible = Object.prototype.hasOwnProperty.call(params.visibilityDraft, fieldKey)
    ? params.visibilityDraft[fieldKey]
    : true;
  return [
    {
      key: `${fieldKey}:show`,
      label: '显示',
      value: 'show',
      checked: visible,
      disabled: params.busy,
      title: '在当前页面显示这个字段',
      raw: {},
    },
    {
      key: `${fieldKey}:hide`,
      label: '隐藏',
      value: 'hide',
      checked: !visible,
      disabled: params.busy,
      title: '在当前页面隐藏这个字段',
      raw: {},
    },
  ];
}

export function buildActiveContractModeActions(params: {
  rules: Record<string, unknown>[];
  mode: string;
  excludedKeys?: string[];
}) {
  const mode = String(params.mode || '').trim();
  if (!mode) return [];
  const source = `mode.${mode}`;
  const excluded = new Set((params.excludedKeys || []).map((key) => String(key || '').trim()).filter(Boolean));
  return params.rules
    .filter((rule) => {
      const key = contractActionRuleKey(rule);
      if (excluded.has(key)) return false;
      const sourceWidgetId = String(rule.sourceWidgetId || rule.source_widget_id || '').trim();
      if (sourceWidgetId !== source) return false;
      const expectedMode = contractActionRuleClientMode(rule);
      return !expectedMode || expectedMode === mode;
    })
    .map((rule) => {
      const key = contractActionRuleKey(rule);
      return {
        key,
        label: String(rule.label || key).trim(),
        raw: rule,
      };
    });
}

export function createRootActionCandidatesFromRules(params: {
  rules: unknown;
  targetModel: string;
}): ContractAction[] {
  const rows = Array.isArray(params.rules) ? params.rules : [];
  return rows
    .map((raw) => (raw && typeof raw === 'object' && !Array.isArray(raw) ? raw as Record<string, unknown> : null))
    .filter((row): row is Record<string, unknown> => Boolean(row))
    .map((row) => {
      const sourceWidgetId = String(row.sourceWidgetId || row.source_widget_id || '').trim();
      const targetScope = String(row.targetScope || row.target_scope || '').trim().toLowerCase();
      const button = parseMaybeJsonRecord(row.button);
      const buttonName = String(button.name || '').trim();
      const buttonType = String(button.type || 'object').trim();
      const normalizedIntent = String(row.intent || 'execute_button').trim().toLowerCase();
      const normalizedButtonType = buttonType.toLowerCase();
      if (
        !buttonName
        || sourceWidgetId !== 'page.root'
        || (targetScope && targetScope !== 'header' && targetScope !== 'footer')
        || (normalizedIntent && normalizedIntent !== 'execute' && normalizedIntent !== 'execute_button')
        || (normalizedButtonType && normalizedButtonType !== 'object' && normalizedButtonType !== 'server' && normalizedButtonType !== 'server_action')
      ) {
        return null;
      }
      const action: ContractAction = {
        key: String(row.actionKey || row.key || row.actionId || buttonName).trim() || buttonName,
        label: String(row.label || buttonName).trim() || buttonName,
        kind: buttonType === 'server' || buttonType === 'server_action' ? 'server' : 'object',
        level: targetScope === 'footer' ? 'footer' : 'header',
        selection: 'none' as const,
        actionId: null,
        methodName: buttonName,
        targetModel: String(params.targetModel || '').trim(),
        context: {},
        domainRaw: '',
        target: '',
        url: '',
        enabled: true,
        hint: '',
        intent: String(row.intent || 'execute_button').trim(),
        semantic: 'primary_action',
        sourceWidgetId,
        clientMode: '',
        visibleProfiles: ['create', 'edit', 'readonly'] as Array<'create' | 'edit' | 'readonly'>,
        requiredParams: [],
        requiresReason: false,
      };
      return action;
    })
    .filter((action): action is ContractAction => Boolean(action));
}

export function resolvePrimaryCreateFooterAction(params: {
  actions: ContractAction[];
  fallbackRules: unknown;
  targetModel: string;
}): ContractAction | null {
  const mappedCandidates = params.actions.filter((action) => {
    const level = String(action.level || '').trim().toLowerCase();
    const kind = String(action.kind || '').trim().toLowerCase();
    const source = String(action.sourceWidgetId || '').trim();
    const isWizardRootAction = source === 'page.root' && level === 'header';
    return (level === 'footer' || isWizardRootAction)
      && (kind === 'object' || kind === 'server')
      && Boolean(action.methodName)
      && action.selection === 'none';
  });
  const candidates = mappedCandidates.length
    ? mappedCandidates
    : createRootActionCandidatesFromRules({
      rules: params.fallbackRules,
      targetModel: params.targetModel,
    });
  if (candidates.length !== 1) return null;
  return {
    ...candidates[0],
    enabled: true,
    hint: '',
  };
}

export function stableContractId(value: unknown, fallback: string) {
  const raw = String(value || fallback || '').trim();
  const normalized = raw
    .split('')
    .map((char) => {
      if (/^[A-Za-z0-9_.:-]$/.test(char)) return char;
      if (char === ' ' || char === '/') return '.';
      return '';
    })
    .join('')
    .replace(/^\.+|\.+$/g, '');
  const safe = normalized || fallback || 'action';
  return /^[A-Za-z]/.test(safe) ? safe : `id.${safe}`;
}

export function resolveV2ButtonStatus(
  key: string,
  statusById: Record<string, ContractV2ButtonStatus>,
): ContractV2ButtonStatus | null {
  const stableKey = stableContractId(key, 'action');
  const candidates = [`btn.${stableKey}`, key, stableKey].filter(Boolean);
  for (const candidate of candidates) {
    if (statusById[candidate]) return statusById[candidate];
  }
  return null;
}

export function actionResponseNavQuery(
  currentQuery: Record<string, unknown>,
  result: object | null | undefined,
  extra?: Record<string, unknown>,
) {
  const payload = (result && typeof result === 'object' && !Array.isArray(result))
    ? result as Record<string, unknown>
    : {};
  const rawAction = (payload.raw_action && typeof payload.raw_action === 'object' && !Array.isArray(payload.raw_action))
    ? payload.raw_action as Record<string, unknown>
    : {};
  const entryTarget = (payload.entry_target && typeof payload.entry_target === 'object' && !Array.isArray(payload.entry_target))
    ? payload.entry_target as Record<string, unknown>
    : {};
  const refs = (entryTarget.compatibility_refs && typeof entryTarget.compatibility_refs === 'object' && !Array.isArray(entryTarget.compatibility_refs))
    ? entryTarget.compatibility_refs as Record<string, unknown>
    : {};
  return pickContractNavQuery(currentQuery, {
    action_id: payload.action_id || rawAction.id || rawAction.action_id || refs.action_id,
    domain_raw: payload.domain_raw || rawAction.domain_raw || refs.domain_raw,
    context_raw: payload.context_raw || rawAction.context_raw || refs.context_raw,
    ...(extra || {}),
  });
}

export function actionResponseRouteTarget(
  currentQuery: Record<string, unknown>,
  target: unknown,
  result: object | null | undefined,
  extra?: Record<string, unknown>,
) {
  const routeTarget = (target && typeof target === 'object' && !Array.isArray(target))
    ? target as Record<string, unknown>
    : {};
  const targetQuery = (routeTarget.query && typeof routeTarget.query === 'object' && !Array.isArray(routeTarget.query))
    ? routeTarget.query as Record<string, unknown>
    : {};
  return {
    ...routeTarget,
    query: {
      ...targetQuery,
      ...actionResponseNavQuery(currentQuery, result, extra),
    },
  };
}

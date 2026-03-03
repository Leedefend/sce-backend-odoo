import type { ActionContract } from '@sc/schema';

export type RenderProfile = 'create' | 'edit' | 'readonly';

type FieldPolicy = {
  visible_profiles?: string[];
  required_profiles?: string[];
  readonly_profiles?: string[];
  source_required?: boolean;
  source_readonly?: boolean;
};

type ActionPolicy = {
  visible_profiles?: string[];
  enabled_when?: {
    profiles?: string[];
    required_fields?: string[];
    required_capabilities?: string[];
    required_groups?: string[];
    required_roles?: string[];
    conditions?: Array<{
      source?: string;
      field?: string;
      op?: string;
      value?: unknown;
    }>;
    lifecycle?: {
      field?: string;
      disallow_states?: string[];
    };
  };
  disabled_reason?: string;
  semantic?: string;
};

type PolicyContext = {
  profile: RenderProfile;
  formData: Record<string, unknown>;
  capabilities: Set<string>;
  userGroups: Set<string>;
  roleCode: string;
};

function hasProfile(list: unknown, profile: RenderProfile): boolean {
  if (!Array.isArray(list) || !list.length) return true;
  return list.map((x) => String(x || '').trim().toLowerCase()).includes(profile);
}

function matchesProfile(list: unknown, profile: RenderProfile): boolean {
  if (!Array.isArray(list) || !list.length) return false;
  return list.map((x) => String(x || '').trim().toLowerCase()).includes(profile);
}

function isEmpty(value: unknown): boolean {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string') return value.trim() === '';
  if (typeof value === 'boolean') return value === false;
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'number') return Number.isNaN(value);
  return false;
}

function toNormalizedArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map((x) => String(x || '').trim()).filter(Boolean);
}

function compareCondition(actual: unknown, op: string, expected: unknown): boolean {
  const normalizedOp = String(op || '').trim().toLowerCase();
  if (normalizedOp === 'truthy') return !isEmpty(actual);
  if (normalizedOp === 'falsy') return isEmpty(actual);
  if (normalizedOp === 'eq') return String(actual ?? '') === String(expected ?? '');
  if (normalizedOp === 'ne') return String(actual ?? '') !== String(expected ?? '');
  if (normalizedOp === 'in') return toNormalizedArray(expected).includes(String(actual ?? ''));
  if (normalizedOp === 'not_in') return !toNormalizedArray(expected).includes(String(actual ?? ''));
  return true;
}

type RawExpr = Record<string, unknown>;

function evaluateLeafCondition(expr: RawExpr, ctx: PolicyContext): boolean {
  const source = String(expr.source || 'record').trim().toLowerCase();
  const field = String(expr.field || '').trim();
  const op = String(expr.op || '').trim();
  if (!field || !op) return true;
  let actual: unknown = undefined;
  if (source === 'record') {
    actual = ctx.formData[field];
  } else if (source === 'context') {
    if (field === 'role_code') actual = ctx.roleCode;
    if (field === 'profile') actual = ctx.profile;
  }
  return compareCondition(actual, op, expr.value);
}

function evaluateConditionExpr(expr: unknown, ctx: PolicyContext): boolean {
  if (!expr || typeof expr !== 'object') return true;
  const node = expr as RawExpr;
  const op = String(node.op || '').trim().toLowerCase();
  if (!op) {
    return evaluateLeafCondition(node, ctx);
  }
  if (op === 'and') {
    const items = Array.isArray(node.items) ? node.items : [];
    return items.every((item) => evaluateConditionExpr(item, ctx));
  }
  if (op === 'or') {
    const items = Array.isArray(node.items) ? node.items : [];
    return items.some((item) => evaluateConditionExpr(item, ctx));
  }
  if (op === 'not') {
    return !evaluateConditionExpr(node.item, ctx);
  }
  return evaluateLeafCondition(node, ctx);
}

export function getFieldPolicy(contract: ActionContract | null, fieldName: string): FieldPolicy {
  const map = (contract?.field_policies || {}) as Record<string, FieldPolicy>;
  return map[fieldName] || {};
}

export function evaluateFieldPolicy(
  contract: ActionContract | null,
  fieldName: string,
  fallback: { required: boolean; readonly: boolean },
  ctx: PolicyContext,
) {
  const policy = getFieldPolicy(contract, fieldName);
  const requiredProfiles = policy.required_profiles;
  const readonlyProfiles = policy.readonly_profiles;
  const visible = hasProfile(policy.visible_profiles, ctx.profile);
  const required = matchesProfile(requiredProfiles, ctx.profile)
    || (!Array.isArray(requiredProfiles) && !!policy.source_required && ctx.profile !== 'readonly');
  const readonly = matchesProfile(readonlyProfiles, ctx.profile)
    || (!Array.isArray(readonlyProfiles) && !!policy.source_readonly && ctx.profile !== 'create');
  return {
    visible,
    required: required && visible,
    readonly: readonly || fallback.readonly || ctx.profile === 'readonly',
  };
}

export function getActionPolicy(contract: ActionContract | null, actionKey: string): ActionPolicy {
  const map = (contract?.action_policies || {}) as Record<string, ActionPolicy>;
  return map[actionKey] || {};
}

export function evaluateActionPolicy(
  contract: ActionContract | null,
  actionKey: string,
  ctx: PolicyContext,
): { visible: boolean; enabled: boolean; reason: string; semantic: string } {
  const policy = getActionPolicy(contract, actionKey);
  const visible = hasProfile(policy.visible_profiles, ctx.profile);
  if (!visible) {
    return { visible: false, enabled: false, reason: '', semantic: String(policy.semantic || '').trim().toLowerCase() || 'secondary' };
  }
  let enabled = true;
  const enabledWhen = policy.enabled_when || {};
  if (!hasProfile(enabledWhen.profiles, ctx.profile)) {
    enabled = false;
  }
  const requiredFields = Array.isArray(enabledWhen.required_fields)
    ? enabledWhen.required_fields.map((x) => String(x || '').trim()).filter(Boolean)
    : [];
  if (requiredFields.length) {
    const missing = requiredFields.filter((name) => isEmpty(ctx.formData[name]));
    if (missing.length) enabled = false;
  }
  const requiredCapabilities = Array.isArray(enabledWhen.required_capabilities)
    ? enabledWhen.required_capabilities.map((x) => String(x || '').trim()).filter(Boolean)
    : [];
  if (requiredCapabilities.length) {
    const missingCaps = requiredCapabilities.filter((key) => !ctx.capabilities.has(key));
    if (missingCaps.length) enabled = false;
  }
  const requiredGroups = Array.isArray(enabledWhen.required_groups)
    ? enabledWhen.required_groups.map((x) => String(x || '').trim()).filter(Boolean)
    : [];
  if (requiredGroups.length) {
    const matched = requiredGroups.some((group) => ctx.userGroups.has(group));
    if (!matched) enabled = false;
  }
  const requiredRoles = Array.isArray(enabledWhen.required_roles)
    ? enabledWhen.required_roles.map((x) => String(x || '').trim().toLowerCase()).filter(Boolean)
    : [];
  if (requiredRoles.length) {
    if (!requiredRoles.includes(String(ctx.roleCode || '').trim().toLowerCase())) {
      enabled = false;
    }
  }
  const expr = enabledWhen.condition_expr;
  if (expr && typeof expr === 'object') {
    if (!evaluateConditionExpr(expr, ctx)) {
      enabled = false;
    }
  } else {
    const conditions = Array.isArray(enabledWhen.conditions) ? enabledWhen.conditions : [];
    for (const row of conditions) {
      if (!row || typeof row !== 'object') continue;
      if (!evaluateConditionExpr(row, ctx)) {
        enabled = false;
        break;
      }
    }
  }
  const lifecycle = enabledWhen.lifecycle;
  if (lifecycle && typeof lifecycle === 'object') {
    const field = String(lifecycle.field || '').trim();
    const disallowStates = Array.isArray(lifecycle.disallow_states)
      ? lifecycle.disallow_states.map((x) => String(x || '').trim()).filter(Boolean)
      : [];
    if (field && disallowStates.length) {
      const current = String(ctx.formData[field] || '').trim();
      if (current && disallowStates.includes(current)) {
        enabled = false;
      }
    }
  }
  return {
    visible: true,
    enabled,
    reason: enabled ? '' : String(policy.disabled_reason || '').trim(),
    semantic: String(policy.semantic || '').trim().toLowerCase() || 'secondary',
  };
}

export function collectPolicyValidationErrors(contract: ActionContract | null, ctx: PolicyContext): string[] {
  const rules = Array.isArray(contract?.validation_rules) ? contract?.validation_rules : [];
  const errors: string[] = [];
  for (const row of rules || []) {
    if (!row || typeof row !== 'object') continue;
    const item = row as Record<string, unknown>;
    const code = String(item.code || '').trim().toUpperCase();
    if (code !== 'REQUIRED') continue;
    const profiles = item.when_profiles;
    if (!hasProfile(profiles, ctx.profile)) continue;
    const field = String(item.field || '').trim();
    if (!field) continue;
    if (isEmpty(ctx.formData[field])) {
      const message = String(item.message || `${field} is required`).trim();
      errors.push(message);
    }
  }
  return errors;
}

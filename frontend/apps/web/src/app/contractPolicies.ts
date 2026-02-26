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
};

function hasProfile(list: unknown, profile: RenderProfile): boolean {
  if (!Array.isArray(list) || !list.length) return true;
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
  const visible = hasProfile(policy.visible_profiles, ctx.profile);
  const required = hasProfile(policy.required_profiles, ctx.profile) || (!!policy.source_required && ctx.profile !== 'readonly');
  const readonly = hasProfile(policy.readonly_profiles, ctx.profile) || (!!policy.source_readonly && ctx.profile !== 'create');
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

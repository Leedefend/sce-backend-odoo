import type { ContractV2ButtonStatus } from '../../app/contracts/v2';
import { pickContractNavQuery } from '../../app/navigationContext';
import type { ContractAction } from './types';

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

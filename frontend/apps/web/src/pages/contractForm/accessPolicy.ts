import type { ContractAccessPolicy } from './types';

function normalizePolicyRows(value: unknown) {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      if (!item || typeof item !== 'object' || Array.isArray(item)) return null;
      const row = item as Record<string, unknown>;
      return {
        field: String(row.field || '').trim(),
        model: String(row.model || '').trim(),
        reasonCode: String(row.reason_code || '').trim(),
      };
    })
    .filter((item): item is { field: string; model: string; reasonCode: string } => Boolean(item));
}

export function normalizeContractAccessPolicy(raw: unknown): ContractAccessPolicy {
  const row = raw && typeof raw === 'object' && !Array.isArray(raw)
    ? raw as Record<string, unknown>
    : {};
  const modeRaw = String(row.mode || '').trim().toLowerCase();
  const mode: 'allow' | 'degrade' | 'block' = modeRaw === 'block' || modeRaw === 'degrade' ? modeRaw : 'allow';
  return {
    mode,
    reasonCode: String(row.reason_code || '').trim(),
    message: String(row.message || '').trim(),
    blockedFields: normalizePolicyRows(row.blocked_fields),
    degradedFields: normalizePolicyRows(row.degraded_fields),
  };
}

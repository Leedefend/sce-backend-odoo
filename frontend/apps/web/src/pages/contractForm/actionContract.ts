import type { ContractV2ButtonStatus } from '../../app/contracts/v2';
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

import type { ActionContract } from '@sc/schema';
import { parseMaybeJsonRecord } from './contractRuntime';

export function resolveContractViewMode(contract: ActionContract | null, fallback = 'tree') {
  const headMode = String(contract?.head?.view_type || '').trim();
  if (headMode) return headMode;
  const rootMode = String(contract?.view_type || '').trim();
  if (rootMode) return rootMode;
  return fallback;
}

export function resolveContractReadRight(contract: ActionContract | null) {
  const head = contract?.head?.permissions?.read;
  if (typeof head === 'boolean') return head;
  const effective = contract?.permissions?.effective?.rights?.read;
  if (typeof effective === 'boolean') return effective;
  return true;
}

export function parseContractContextRaw(raw: unknown) {
  return parseMaybeJsonRecord(raw);
}


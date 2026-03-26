import type { ActionContract } from '@sc/schema';
import { parseMaybeJsonRecord } from './contractRuntime';

export type ContractAccessPolicyMode = 'allow' | 'degrade' | 'block';

export interface ContractAccessPolicySnapshot {
  mode: ContractAccessPolicyMode;
  reasonCode: string;
}

function pickNestedContract(contract: ActionContract | null): ActionContract | null {
  if (!contract || typeof contract !== 'object') return null;
  const raw = contract as ActionContract & {
    ui_contract?: ActionContract;
  };
  if (raw.ui_contract && typeof raw.ui_contract === 'object') {
    return raw.ui_contract;
  }
  return contract;
}

function normalizeViewMode(raw: unknown): string {
  const mode = String(raw || '').trim().toLowerCase();
  if (!mode) return '';
  if (mode === 'list') return 'tree';
  return mode;
}

function pickPrimaryViewMode(raw: unknown): string {
  if (Array.isArray(raw)) {
    for (const item of raw) {
      const mode = normalizeViewMode(item);
      if (mode) return mode;
    }
    return '';
  }
  const text = String(raw || '').trim();
  if (!text) return '';
  for (const item of text.split(',')) {
    const mode = normalizeViewMode(item);
    if (mode) return mode;
  }
  return '';
}

export function resolveContractRights(contract: ActionContract | null) {
  const normalized = pickNestedContract(contract);
  const head = normalized?.head?.permissions;
  const effective = normalized?.permissions?.effective?.rights;
  const resolve = (key: 'read' | 'write' | 'create' | 'unlink') => {
    const headValue = head?.[key];
    if (typeof headValue === 'boolean') return headValue;
    const effectiveValue = effective?.[key];
    if (typeof effectiveValue === 'boolean') return effectiveValue;
    return true;
  };
  return {
    read: resolve('read'),
    write: resolve('write'),
    create: resolve('create'),
    unlink: resolve('unlink'),
  };
}

export function resolveContractViewMode(contract: ActionContract | null, fallback = '') {
  const normalized = pickNestedContract(contract);
  const headMode = pickPrimaryViewMode(normalized?.head?.view_type);
  if (headMode) return headMode;
  const rootMode = pickPrimaryViewMode(normalized?.view_type);
  if (rootMode) return rootMode;
  return pickPrimaryViewMode(fallback);
}

export function resolveContractAccessPolicy(contract: ActionContract | null): ContractAccessPolicySnapshot {
  const raw = (contract as unknown as Record<string, unknown> | null)?.access_policy;
  const row = raw && typeof raw === 'object' && !Array.isArray(raw)
    ? (raw as Record<string, unknown>)
    : {};
  const modeRaw = String(row.mode || '').trim().toLowerCase();
  const mode: ContractAccessPolicyMode = modeRaw === 'block' || modeRaw === 'degrade' ? modeRaw : 'allow';
  const reasonCode = String(row.reason_code || '').trim();
  return { mode, reasonCode };
}

export function resolveContractReadRight(contract: ActionContract | null) {
  const policy = resolveContractAccessPolicy(contract);
  if (policy.mode === 'block') return false;
  return resolveContractRights(contract).read;
}

export function parseContractContextRaw(raw: unknown) {
  return parseMaybeJsonRecord(raw);
}

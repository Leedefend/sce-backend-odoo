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

export function resolveContractViewMode(contract: ActionContract | null, fallback = '') {
  const normalized = pickNestedContract(contract);
  const headMode = String(normalized?.head?.view_type || '').trim();
  if (headMode) return headMode;
  const rootMode = String(normalized?.view_type || '').trim();
  if (rootMode) return rootMode;
  return fallback;
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
  const head = contract?.head?.permissions?.read;
  if (typeof head === 'boolean') return head;
  const effective = contract?.permissions?.effective?.rights?.read;
  if (typeof effective === 'boolean') return effective;
  return true;
}

export function parseContractContextRaw(raw: unknown) {
  return parseMaybeJsonRecord(raw);
}

import type { ActionContract } from '@sc/schema';
import { parseMaybeJsonRecord } from './contractRuntime';
import {
  resolveUnifiedPageContractV2,
  resolveUnifiedPageContractV2GlobalStatus,
} from './contracts/unifiedPageContractV2';

export type ContractAccessPolicyMode = 'allow' | 'degrade' | 'block';

export interface ContractAccessPolicySnapshot {
  mode: ContractAccessPolicyMode;
  reasonCode: string;
}

export function resolveContractViewMode(contract: ActionContract | null, fallback = '') {
  const v2 = resolveUnifiedPageContractV2(contract);
  const v2Mode = String(v2?.pageInfo?.viewType || '').trim();
  if (v2Mode) {
    const normalizedV2Mode = v2Mode === 'list' ? 'tree' : v2Mode;
    return normalizedV2Mode;
  }
  const headMode = String(contract?.head?.view_type || '').trim();
  if (headMode) return headMode;
  const rootMode = String(contract?.view_type || '').trim();
  if (rootMode) return rootMode;
  return fallback;
}

export function resolveContractAccessPolicy(contract: ActionContract | null): ContractAccessPolicySnapshot {
  const globalStatus = resolveUnifiedPageContractV2GlobalStatus(contract);
  const pageAuth = String(globalStatus?.pageAuth || '').trim().toLowerCase();
  if (globalStatus?.pageVisible === false || pageAuth === 'none') {
    return {
      mode: 'block',
      reasonCode: globalStatus?.reasonCode || 'UNIFIED_PAGE_CONTRACT_V2_PAGE_FORBIDDEN',
    };
  }
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
  const globalStatus = resolveUnifiedPageContractV2GlobalStatus(contract);
  const pageAuth = String(globalStatus?.pageAuth || '').trim().toLowerCase();
  if (globalStatus?.pageVisible === false || pageAuth === 'none') return false;
  const head = contract?.head?.permissions?.read;
  if (typeof head === 'boolean') return head;
  const effective = contract?.permissions?.effective?.rights?.read;
  if (typeof effective === 'boolean') return effective;
  return true;
}

export function parseContractContextRaw(raw: unknown) {
  return parseMaybeJsonRecord(raw);
}

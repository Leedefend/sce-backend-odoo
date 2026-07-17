import type { NavMeta, NavNode } from '@sc/schema';
import { findActionMeta, findActionMetaByMenu } from '../menu';
import { loadActionContract, loadModelLitePreviewContract } from '../../api/contract';
import {
  adaptLiteContractToActionViewContract,
  isLiteContractPilotCandidate,
  needsLiteContractAllTreeViewPreflight,
} from '../runtime/unifiedPageContractLitePilot';

export interface ActionResolution {
  meta: NavMeta;
  contract: Awaited<ReturnType<typeof loadActionContract>>;
}

function splitViewModes(raw: unknown): string[] {
  if (Array.isArray(raw)) {
    return raw
      .map((item) => String(item || '').trim().toLowerCase())
      .filter(Boolean);
  }
  return String(raw || '')
    .split(',')
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
}

function resolveMetaFromContract(contract: unknown, actionId: number): NavMeta {
  const normalized = (contract && typeof contract === 'object' && !Array.isArray(contract))
    ? contract as Record<string, unknown>
    : {};
  const head = (normalized.head && typeof normalized.head === 'object' && !Array.isArray(normalized.head))
    ? (normalized.head as Record<string, unknown>)
    : {};
  const views = (normalized.views && typeof normalized.views === 'object' && !Array.isArray(normalized.views))
    ? (normalized.views as Record<string, unknown>)
    : {};
  const treeView = (views.tree && typeof views.tree === 'object' && !Array.isArray(views.tree))
    ? (views.tree as Record<string, unknown>)
    : {};
  const formView = (views.form && typeof views.form === 'object' && !Array.isArray(views.form))
    ? (views.form as Record<string, unknown>)
    : {};
  const kanbanView = (views.kanban && typeof views.kanban === 'object' && !Array.isArray(views.kanban))
    ? (views.kanban as Record<string, unknown>)
    : {};
  const model = String(head.model || normalized.model || treeView.model || formView.model || kanbanView.model || '').trim();
  const viewModes = splitViewModes(head.view_type || normalized.view_type || '');
  const name = String(head.title || normalized.name || '').trim();
  const actionType = String(normalized.action_type || head.action_type || 'ir.actions.act_window').trim();
  const domain = head.domain ?? normalized.domain;
  const domainRaw = head.domain_raw ?? normalized.domain_raw;
  const context = head.context ?? normalized.context;
  const contextRaw = head.context_raw ?? normalized.context_raw;
  const out: NavMeta = {
    action_id: Number(actionId || 0),
    action_type: actionType || 'ir.actions.act_window',
  };
  if (model) out.model = model;
  if (name) out.name = name;
  if (viewModes.length) out.view_modes = viewModes;
  if (Array.isArray(domain) || typeof domain === 'string') out.domain = domain;
  if (typeof domainRaw === 'string' && domainRaw.trim()) out.domain_raw = domainRaw;
  if ((context && typeof context === 'object' && !Array.isArray(context)) || typeof context === 'string') {
    out.context = context as NavMeta['context'];
  }
  if (typeof contextRaw === 'string' && contextRaw.trim()) out.context_raw = contextRaw;
  return out;
}

function mergeMeta(base: NavMeta | null, fallback: NavMeta): NavMeta {
  const merged: NavMeta = { ...(base || {}), ...fallback };
  const contractModelChanged = Boolean(fallback.model && base?.model && fallback.model !== base.model);
  const baseDomain = base?.domain;
  const baseHasDomain = Array.isArray(baseDomain)
    ? baseDomain.length > 0
    : typeof baseDomain === 'string' && baseDomain.trim().length > 0;
  const baseContext = base?.context;
  const baseHasContext = typeof baseContext === 'string'
    ? baseContext.trim().length > 0
    : Boolean(baseContext && typeof baseContext === 'object' && !Array.isArray(baseContext) && Object.keys(baseContext).length);
  if (base?.action_type) merged.action_type = base.action_type;
  if (base?.menu_id) merged.menu_id = base.menu_id;
  if (base?.menu_xmlid) merged.menu_xmlid = base.menu_xmlid;
  if (base?.groups_xmlids?.length) merged.groups_xmlids = base.groups_xmlids;
  if (fallback.model) merged.model = fallback.model;
  else if (base?.model) merged.model = base.model;
  if (baseHasDomain && !contractModelChanged) merged.domain = baseDomain;
  if (baseHasContext && !contractModelChanged) merged.context = baseContext as NavMeta['context'];
  const baseModes = splitViewModes(base?.view_modes || []);
  if (baseModes.length && !contractModelChanged) {
    merged.view_modes = baseModes;
  } else if (fallback.view_modes?.length) {
    merged.view_modes = fallback.view_modes;
  }
  return merged;
}

export async function resolveAction(
  menuTree: NavNode[],
  actionId: number,
  currentAction?: NavMeta | null,
  options?: { menuId?: number | null; viewType?: string | null; previewToken?: string | null; previewRoleKey?: string | null },
): Promise<ActionResolution> {
  const currentMatches = Boolean(currentAction && Number(currentAction.action_id || 0) === Number(actionId || 0));
  const currentMenuId = Number(options?.menuId || currentAction?.menu_id || 0);
  const contractOptions = {
    menuId: currentMenuId > 0 ? currentMenuId : undefined,
    viewType: String(options?.viewType || '').trim().toLowerCase() as Parameters<typeof loadActionContract>[1] extends infer T
      ? T extends { viewType?: infer V } ? V : never
      : never,
    previewToken: String(options?.previewToken || '').trim() || undefined,
    previewRoleKey: String(options?.previewRoleKey || '').trim() || undefined,
  };
  const metaFromMenu = (
    currentMenuId > 0
      ? findActionMetaByMenu(menuTree, currentMenuId, actionId)
      : null
  ) || findActionMeta(menuTree, actionId);
  // Always prefer menuTree meta to avoid stale/incomplete currentAction snapshots.
  const seedMeta = metaFromMenu || (currentMatches ? currentAction : null);

  let legacyContract: Awaited<ReturnType<typeof loadActionContract>> | null = null;
  let candidateMeta = seedMeta;
  if (needsLiteContractAllTreeViewPreflight(seedMeta)) {
    legacyContract = await loadActionContract(actionId, contractOptions);
    candidateMeta = mergeMeta(seedMeta, resolveMetaFromContract(legacyContract, actionId));
  }

  const hasUnifiedV2Contract = Boolean(
    legacyContract
    && typeof legacyContract === 'object'
    && !Array.isArray(legacyContract)
    && (legacyContract as Record<string, unknown>).__unified_page_contract_v2,
  );
  if (hasUnifiedV2Contract) {
    const meta = mergeMeta(seedMeta, resolveMetaFromContract(legacyContract, actionId));
    if (!meta.action_id) meta.action_id = Number(actionId || 0);
    return { meta, contract: legacyContract };
  }

  if (isLiteContractPilotCandidate(candidateMeta)) {
    const liteContract = await loadModelLitePreviewContract(String(candidateMeta?.model || ''), { viewType: 'tree' });
    if (liteContract) {
      const contract = adaptLiteContractToActionViewContract(liteContract);
      const fallbackMeta = resolveMetaFromContract(contract, actionId);
      const meta = mergeMeta(candidateMeta, fallbackMeta);
      if (!meta.action_id) {
        meta.action_id = Number(actionId || 0);
      }
      return { meta, contract };
    }
  }

  const contract = legacyContract || await loadActionContract(actionId, contractOptions);
  const fallbackMeta = resolveMetaFromContract(contract, actionId);
  const meta = mergeMeta(seedMeta, fallbackMeta);
  if (!meta.action_id) {
    meta.action_id = Number(actionId || 0);
  }
  return { meta, contract };
}

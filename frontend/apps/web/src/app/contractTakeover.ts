type Dict = Record<string, unknown>;

function asDict(value: unknown): Dict {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {};
  return value as Dict;
}

function normalizeViewMode(raw: unknown): string {
  const mode = String(raw || '').trim().toLowerCase();
  if (!mode) return '';
  if (mode === 'list') return 'tree';
  return mode;
}

function getSemanticPage(contract: unknown): Dict {
  const row = asDict(contract);
  return asDict(row.semantic_page);
}

function getCapabilityProfile(contract: unknown): Dict {
  return asDict(getSemanticPage(contract).capability_profile);
}

function getViewProfiles(contract: unknown): Dict {
  return asDict(getCapabilityProfile(contract).view_profiles);
}

function getRenderPolicy(contract: unknown): Dict {
  return asDict(getCapabilityProfile(contract).render_policy);
}

export function resolveContractViewRenderPolicy(contract: unknown, viewModeRaw?: unknown) {
  const mode = normalizeViewMode(viewModeRaw) || normalizeViewMode(getCapabilityProfile(contract).primary_view_type);
  const viewProfiles = getViewProfiles(contract);
  const modeProfile = asDict(mode ? viewProfiles[mode] : undefined);
  const fallbackPolicy = getRenderPolicy(contract);
  const recommendedRuntime = String(modeProfile.recommended_runtime || fallbackPolicy.recommended_runtime || '').trim().toLowerCase();
  const takeoverClass = String(modeProfile.takeover_class || fallbackPolicy.takeover_class || '').trim();
  const supportTier = String(modeProfile.support_tier || fallbackPolicy.support_tier || '').trim();
  const fallbackAction = asDict(fallbackPolicy.fallback_action);
  return {
    mode,
    recommendedRuntime,
    takeoverClass,
    supportTier,
    fallbackAction,
    reasonCodes: Array.isArray(modeProfile.reason_codes) ? modeProfile.reason_codes.map((item) => String(item || '').trim()).filter(Boolean) : [],
    fallbackTriggers: Array.isArray(modeProfile.fallback_triggers) ? modeProfile.fallback_triggers.map((item) => String(item || '').trim()).filter(Boolean) : [],
    notes: Array.isArray(modeProfile.notes) ? modeProfile.notes.map((item) => String(item || '').trim()).filter(Boolean) : [],
  };
}

export function resolveContractListSemantics(contract: unknown): Dict {
  return asDict(getSemanticPage(contract).list_semantics);
}

export function resolveContractFormSemantics(contract: unknown): Dict {
  return asDict(getSemanticPage(contract).form_semantics);
}

export function resolveContractKanbanSemantics(contract: unknown): Dict {
  return asDict(getSemanticPage(contract).kanban_semantics);
}

export function buildNativeFallbackUrl(actionRaw: unknown): string {
  const action = asDict(actionRaw);
  const payload = asDict(action.payload);
  const hashParams = new URLSearchParams();
  const actionId = Number(payload.action_id || 0);
  const menuId = Number(payload.menu_id || 0);
  const resId = Number(payload.res_id || 0);
  const model = String(payload.model || '').trim();
  const viewType = normalizeViewMode(payload.view_type) || 'form';

  if (actionId > 0) hashParams.set('action', String(actionId));
  if (menuId > 0) hashParams.set('menu_id', String(menuId));
  if (resId > 0) hashParams.set('id', String(resId));
  if (model) hashParams.set('model', model);
  if (viewType) hashParams.set('view_type', viewType);
  hashParams.set('cids', '1');

  const hash = hashParams.toString();
  return hash ? `/web#${hash}` : '/web';
}

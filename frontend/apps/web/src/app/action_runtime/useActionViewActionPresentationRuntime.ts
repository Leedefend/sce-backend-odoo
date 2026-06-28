/* eslint-disable @typescript-eslint/no-explicit-any */
import { computed, type Ref } from 'vue';
import {
  resolveUnifiedPageContractV2,
  resolveUnifiedPageContractV2SurfacePolicies,
} from '../contracts/unifiedPageContractV2';
import type { ActionPresentation } from './useActionViewActionGroupingRuntime';

type Dict = Record<string, unknown>;

type ContractActionButton = {
  key: string;
  label: string;
  enabled?: boolean;
  hint?: string;
  selection?: 'none' | 'single' | 'multi';
  level?: string;
  visibleProfiles?: string[];
  kind?: string;
  actionId?: number | null;
  methodName?: string;
  model?: string;
  target?: string;
  url?: string;
  context?: Dict;
  domainRaw?: string;
  mutation?: Dict;
  refreshPolicy?: Dict;
};

type ContractActionGroupRaw = {
  key?: string;
  label?: string;
  actions?: Array<Record<string, unknown>>;
};

type ActionGroup = {
  key: string;
  label: string;
  actions: ContractActionButton[];
};

type UseActionViewActionPresentationRuntimeOptions = {
  actionContract: Ref<Dict | null>;
  strictContractMode: Ref<boolean>;
  toContractActionButton: (row: Dict, dedup: Set<string>) => ContractActionButton | null;
  resolveContractActionPresentation: (options: {
    strictContractMode: boolean;
    actionSurface: Dict;
    contractActionGroupsRaw: ContractActionGroupRaw[];
    allButtons: ContractActionButton[];
    actionPrimaryBudget: number;
    pageText: (key: string, fallback: string) => string;
  }) => ActionPresentation;
  pageText: (key: string, fallback: string) => string;
};

function resolveV2RefreshPolicy(refreshMode: string): Dict | undefined {
  const mode = String(refreshMode || '').trim().toLowerCase();
  if (mode === 'none') return undefined;
  if (mode === 'full') {
    return {
      on_success: ['scene_projection', 'workbench_projection'],
      mode: 'full',
      scope: 'page',
    };
  }
  return {
    on_success: ['scene_projection'],
    mode: mode || 'partial',
    scope: 'page',
  };
}

function normalizeV2ActionRows(contract: Dict | null): Array<Record<string, unknown>> {
  const v2 = resolveUnifiedPageContractV2(contract);
  if (!v2) return [];
  const rows = Array.isArray(v2.actionContract.actionRuleList) ? v2.actionContract.actionRuleList : [];
  const normalized: Array<Record<string, unknown>> = [];
  for (const action of rows) {
    if (!action || typeof action !== 'object') continue;
    const key = String(action.actionKey || action.actionId || '').trim();
    if (!key) continue;
    const intent = String(action.intent || '').trim();
    const target = action.target && typeof action.target === 'object' && !Array.isArray(action.target) ? action.target : {};
    const button = action.button && typeof action.button === 'object' && !Array.isArray(action.button) ? action.button : {};
    const isOpen = intent === 'ui.contract';
    normalized.push({
      key,
      label: String(action.label || key).trim() || key,
      intent,
      kind: isOpen ? 'open' : String(button.type || 'object'),
      level: 'toolbar',
      target,
      payload: isOpen
        ? target
        : {
            method: button.name || key,
            type: button.type || 'object',
          },
      refresh_policy: resolveV2RefreshPolicy(action.refreshMode),
      target_model: String(target.model || '').trim(),
      selection: 'none',
      unified_page_contract_v2_action_id: action.actionId,
      unified_page_contract_v2_source_widget_id: action.sourceWidgetId,
      unified_page_contract_v2_refresh_mode: action.refreshMode,
    });
  }
  return normalized;
}

export function useActionViewActionPresentationRuntime(options: UseActionViewActionPresentationRuntimeOptions) {
  const contractActionButtons = computed<ContractActionButton[]>(() => {
    const contract = options.actionContract.value;
    const merged: Array<Record<string, unknown>> = [];
    if (!contract) return [];
    if (Array.isArray(contract.buttons)) merged.push(...(contract.buttons as Array<Record<string, unknown>>));
    if (Array.isArray(contract.actions)) merged.push(...(contract.actions as Array<Record<string, unknown>>));
    if (contract.toolbar && typeof contract.toolbar === 'object') {
      const toolbar = contract.toolbar as Record<string, unknown>;
      if (Array.isArray(toolbar.header)) merged.push(...(toolbar.header as Array<Record<string, unknown>>));
      if (Array.isArray(toolbar.action)) merged.push(...(toolbar.action as Array<Record<string, unknown>>));
      if (Array.isArray(toolbar.print)) merged.push(...(toolbar.print as Array<Record<string, unknown>>));
      if (Array.isArray(toolbar.sidebar)) merged.push(...(toolbar.sidebar as Array<Record<string, unknown>>));
      if (Array.isArray(toolbar.footer)) merged.push(...(toolbar.footer as Array<Record<string, unknown>>));
    }
    merged.push(...normalizeV2ActionRows(contract));
    const dedup = new Set<string>();
    return merged
      .map((row) => options.toContractActionButton(row, dedup))
      .filter((item): item is ContractActionButton => Boolean(item));
  });

  const actionPrimaryBudget = computed(() => {
    const surfacePolicies = resolveUnifiedPageContractV2SurfacePolicies(options.actionContract.value);
    const raw = Number(surfacePolicies.actions_primary_max ?? 4);
    if (!Number.isFinite(raw) || raw < 0) return 4;
    return Math.floor(raw);
  });

  const contractActionPresentation = computed(() => {
    return options.resolveContractActionPresentation({
      strictContractMode: options.strictContractMode.value,
      actionSurface: {},
      contractActionGroupsRaw: Array.isArray(options.actionContract.value?.action_groups)
        ? (options.actionContract.value?.action_groups as ContractActionGroupRaw[])
        : [],
      allButtons: contractActionButtons.value,
      actionPrimaryBudget: actionPrimaryBudget.value,
      pageText: options.pageText,
    });
  });

  const contractPrimaryActions = computed<ContractActionButton[]>(() => {
    return (contractActionPresentation.value.primaryActions || []) as ContractActionButton[];
  });

  const contractOverflowActionGroups = computed<ActionGroup[]>(() => {
    return (contractActionPresentation.value.overflowActionGroups || []) as ActionGroup[];
  });

  const contractActionCount = computed(() => contractActionButtons.value.length);

  return {
    contractActionButtons,
    contractActionCount,
    contractPrimaryActions,
    contractOverflowActionGroups,
  };
}

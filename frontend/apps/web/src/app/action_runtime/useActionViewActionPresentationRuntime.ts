import { computed, type Ref } from 'vue';

type Dict = Record<string, unknown>;

type ContractActionButton = {
  key: string;
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
  sceneContractV1: Ref<Dict>;
  sceneReadyListSurface: Ref<{ actions: Array<Record<string, unknown>>; actionSurface?: unknown }>;
  strictContractMode: Ref<boolean>;
  toContractActionButton: (row: Dict, dedup: Set<string>) => ContractActionButton | null;
  resolveContractActionPresentation: (options: {
    strictContractMode: boolean;
    actionSurface: Dict;
    contractActionGroupsRaw: ContractActionGroupRaw[];
    allButtons: ContractActionButton[];
    actionPrimaryBudget: number;
    pageText: (key: string, fallback: string) => string;
  }) => {
    primaryActions: ContractActionButton[];
    overflowActionGroups: ActionGroup[];
  };
  pageText: (key: string, fallback: string) => string;
};

const SCENE_ACTION_GROUPS = [
  ['primary_actions', 'basic'],
  ['contextual_actions', 'drilldown'],
  ['secondary_actions', 'other'],
  ['danger_actions', 'other'],
  ['recommended_actions', 'basic'],
] as const;

function sceneActionRows(sceneContractV1: Dict): Array<Record<string, unknown>> {
  const actions = sceneContractV1.actions && typeof sceneContractV1.actions === 'object'
    ? sceneContractV1.actions as Dict
    : {};
  const rows: Array<Record<string, unknown>> = [];
  const seen = new Set<string>();
  SCENE_ACTION_GROUPS.forEach(([sourceKey, groupKey]) => {
    const groupRows = actions[sourceKey];
    if (!Array.isArray(groupRows)) return;
    groupRows.forEach((item) => {
      if (!item || typeof item !== 'object' || Array.isArray(item)) return;
      const row = item as Record<string, unknown>;
      const key = String(row.key || '').trim();
      if (!key || seen.has(key)) return;
      seen.add(key);
      rows.push({ ...row, scene_action_group: sourceKey, group_key: groupKey });
    });
  });
  return rows;
}

function sceneActionGroups(sceneContractV1: Dict): ContractActionGroupRaw[] {
  const actions = sceneContractV1.actions && typeof sceneContractV1.actions === 'object'
    ? sceneContractV1.actions as Dict
    : {};
  const groups: ContractActionGroupRaw[] = [];
  SCENE_ACTION_GROUPS.forEach(([sourceKey, groupKey]) => {
    const groupRows = actions[sourceKey];
    if (!Array.isArray(groupRows) || !groupRows.length) return;
    groups.push({
      key: groupKey,
      label: groupKey,
      actions: groupRows.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === 'object' && !Array.isArray(item)),
    });
  });
  return groups;
}

export function useActionViewActionPresentationRuntime(options: UseActionViewActionPresentationRuntimeOptions) {
  const sceneContractActionRows = computed(() => sceneActionRows(options.sceneContractV1.value));
  const sceneContractActionGroups = computed(() => sceneActionGroups(options.sceneContractV1.value));

  const contractActionButtons = computed<ContractActionButton[]>(() => {
    const contract = options.actionContract.value;
    const merged: Array<Record<string, unknown>> = [];
    if (sceneContractActionRows.value.length) {
      merged.push(...sceneContractActionRows.value);
    } else if (options.sceneReadyListSurface.value.actions.length) {
      merged.push(...options.sceneReadyListSurface.value.actions);
    } else {
      if (!contract) return [];
      if (Array.isArray(contract.actions)) merged.push(...(contract.actions as Array<Record<string, unknown>>));
      if (contract.toolbar && typeof contract.toolbar === 'object') {
        const toolbar = contract.toolbar as Record<string, unknown>;
        if (Array.isArray(toolbar.action)) merged.push(...(toolbar.action as Array<Record<string, unknown>>));
        if (Array.isArray(toolbar.print)) merged.push(...(toolbar.print as Array<Record<string, unknown>>));
        if (Array.isArray(toolbar.sidebar)) merged.push(...(toolbar.sidebar as Array<Record<string, unknown>>));
        if (Array.isArray(toolbar.footer)) merged.push(...(toolbar.footer as Array<Record<string, unknown>>));
      }
    }
    const dedup = new Set<string>();
    return merged
      .map((row) => options.toContractActionButton(row, dedup))
      .filter((item): item is ContractActionButton => Boolean(item))
      .slice(0, 8);
  });

  const actionPrimaryBudget = computed(() => {
    const surfacePolicies = options.actionContract.value?.surface_policies;
    const raw = Number(
      surfacePolicies && typeof surfacePolicies === 'object'
        ? (surfacePolicies as Dict).actions_primary_max ?? 4
        : 4,
    );
    if (!Number.isFinite(raw) || raw < 0) return 4;
    return Math.floor(raw);
  });

  const contractActionPresentation = computed(() => {
    return options.resolveContractActionPresentation({
      strictContractMode: options.strictContractMode.value,
      actionSurface: (options.sceneReadyListSurface.value.actionSurface || {}) as Dict,
      contractActionGroupsRaw: sceneContractActionGroups.value.length
        ? sceneContractActionGroups.value
        : Array.isArray(options.actionContract.value?.action_groups)
          ? (options.actionContract.value?.action_groups as ContractActionGroupRaw[])
          : [],
      allButtons: contractActionButtons.value,
      actionPrimaryBudget: actionPrimaryBudget.value,
      pageText: options.pageText,
    });
  });

  const contractPrimaryActions = computed<ContractActionButton[]>(() => {
    return contractActionPresentation.value.primaryActions;
  });

  const contractOverflowActionGroups = computed<ActionGroup[]>(() => {
    return contractActionPresentation.value.overflowActionGroups;
  });

  const contractActionCount = computed(() => contractActionButtons.value.length);

  return {
    contractActionCount,
    contractPrimaryActions,
    contractOverflowActionGroups,
  };
}

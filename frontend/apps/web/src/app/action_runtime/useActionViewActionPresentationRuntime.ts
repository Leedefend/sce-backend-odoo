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

export function useActionViewActionPresentationRuntime(options: UseActionViewActionPresentationRuntimeOptions) {
  const contractActionButtons = computed<ContractActionButton[]>(() => {
    const contract = options.actionContract.value;
    const merged: Array<Record<string, unknown>> = [];
    const sceneActions = options.sceneReadyListSurface.value.actions;
    if (sceneActions.length) {
      merged.push(...sceneActions);
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
    const raw = Number(options.actionContract.value?.surface_policies?.actions_primary_max ?? 4);
    if (!Number.isFinite(raw) || raw < 0) return 4;
    return Math.floor(raw);
  });

  const contractActionPresentation = computed(() => {
    return options.resolveContractActionPresentation({
      strictContractMode: options.strictContractMode.value,
      actionSurface: (options.sceneReadyListSurface.value.actionSurface || {}) as Dict,
      contractActionGroupsRaw: Array.isArray(options.actionContract.value?.action_groups)
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

  return {
    contractActionButtons,
    contractPrimaryActions,
    contractOverflowActionGroups,
  };
}

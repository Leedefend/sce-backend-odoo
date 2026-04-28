import { computed, type Ref } from 'vue';

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
  }) => any;
  pageText: (key: string, fallback: string) => string;
};

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
    const dedup = new Set<string>();
    return merged
      .map((row) => options.toContractActionButton(row, dedup))
      .filter((item): item is ContractActionButton => Boolean(item));
  });

  const actionPrimaryBudget = computed(() => {
    const surfacePolicies = (
      options.actionContract.value?.surface_policies
      && typeof options.actionContract.value.surface_policies === 'object'
      && !Array.isArray(options.actionContract.value.surface_policies)
    ) ? options.actionContract.value.surface_policies as Dict : {};
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

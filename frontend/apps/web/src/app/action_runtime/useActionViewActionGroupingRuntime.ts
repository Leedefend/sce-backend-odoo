type Dict = Record<string, unknown>;

type ContractActionButton = {
  key: string;
};

type ActionGroup = {
  key: string;
  label: string;
  actions: ContractActionButton[];
};

type ActionPresentation = {
  groups: ActionGroup[];
  primaryActions: ContractActionButton[];
  overflowActionGroups: ActionGroup[];
};

type ContractActionGroupRaw = {
  key?: string;
  label?: string;
  actions?: Array<Record<string, unknown>>;
};

export function useActionViewActionGroupingRuntime() {
  function resolveContractActionGroups(options: {
    strictContractMode: boolean;
    actionSurface: Dict;
    contractActionGroupsRaw: ContractActionGroupRaw[];
    allButtons: ContractActionButton[];
    pageText: (key: string, fallback: string) => string;
  }): ActionGroup[] {
    const all = options.allButtons;
    if (!all.length) return [];
    const map = new Map(all.map((item) => [item.key, item]));

    if (options.strictContractMode) {
      const groupsRaw = Array.isArray(options.actionSurface.groups)
        ? (options.actionSurface.groups as Array<Record<string, unknown>>)
        : [];
      const grouped: ActionGroup[] = [];
      for (const row of groupsRaw) {
        const groupKey = String(row.key || '').trim();
        if (!groupKey) continue;
        const actionKeys = Array.isArray(row.actions) ? row.actions : [];
        const actions = actionKeys
          .map((item) => {
            const actionKey = typeof item === 'string' ? item : String((item as Record<string, unknown>)?.key || '');
            return map.get(actionKey);
          })
          .filter((item): item is ContractActionButton => Boolean(item));
        if (actions.length) grouped.push({ key: groupKey, label: String(row.label || groupKey), actions });
      }
      if (grouped.length) return grouped;
      return [{ key: 'flat', label: options.pageText('group_label_flat', '操作'), actions: all }];
    }

    const grouped: ActionGroup[] = [];
    const used = new Set<string>();
    for (const row of options.contractActionGroupsRaw) {
      const groupKey = String(row?.key || '').trim();
      if (!groupKey) continue;
      const rows = Array.isArray(row?.actions) ? row.actions : [];
      const actions: ContractActionButton[] = [];
      for (const item of rows) {
        const key = String(item?.key || '').trim();
        if (!key || used.has(key)) continue;
        const resolved = map.get(key);
        if (!resolved) continue;
        used.add(key);
        actions.push(resolved);
      }
      if (actions.length) grouped.push({ key: groupKey, label: String(row?.label || groupKey), actions });
    }
    if (!grouped.length) {
      grouped.push({ key: 'flat', label: options.pageText('group_label_flat', '操作'), actions: all });
    }
    return grouped;
  }

  function resolveContractPrimaryActions(options: {
    groups: ActionGroup[];
    allButtons: ContractActionButton[];
    actionPrimaryBudget: number;
  }): ContractActionButton[] {
    const groups = options.groups;
    if (!groups.length) return options.allButtons.slice(0, options.actionPrimaryBudget);
    const primaryGroupOrder = ['basic', 'workflow', 'drilldown'];
    const merged: ContractActionButton[] = [];
    for (const key of primaryGroupOrder) {
      const group = groups.find((item) => item.key === key);
      if (!group) continue;
      for (const action of group.actions) {
        if (merged.some((item) => item.key === action.key)) continue;
        merged.push(action);
        if (merged.length >= options.actionPrimaryBudget) return merged;
      }
    }
    return merged.slice(0, options.actionPrimaryBudget);
  }

  function resolveContractOverflowActions(options: {
    allButtons: ContractActionButton[];
    primaryActions: ContractActionButton[];
  }): ContractActionButton[] {
    const primaryKeys = new Set(options.primaryActions.map((item) => item.key));
    return options.allButtons.filter((item) => !primaryKeys.has(item.key));
  }

  function resolveContractOverflowActionGroups(options: {
    groups: ActionGroup[];
    primaryActions: ContractActionButton[];
  }): ActionGroup[] {
    const primaryKeys = new Set(options.primaryActions.map((item) => item.key));
    const out: ActionGroup[] = [];
    for (const group of options.groups) {
      const actions = group.actions.filter((item) => !primaryKeys.has(item.key));
      if (!actions.length) continue;
      out.push({ key: group.key, label: group.label, actions });
    }
    return out;
  }

  function resolveContractActionPresentation(options: {
    strictContractMode: boolean;
    actionSurface: Dict;
    contractActionGroupsRaw: ContractActionGroupRaw[];
    allButtons: ContractActionButton[];
    actionPrimaryBudget: number;
    pageText: (key: string, fallback: string) => string;
  }): ActionPresentation {
    const groups = resolveContractActionGroups({
      strictContractMode: options.strictContractMode,
      actionSurface: options.actionSurface,
      contractActionGroupsRaw: options.contractActionGroupsRaw,
      allButtons: options.allButtons,
      pageText: options.pageText,
    });
    const primaryActions = resolveContractPrimaryActions({
      groups,
      allButtons: options.allButtons,
      actionPrimaryBudget: options.actionPrimaryBudget,
    });
    const overflowActionGroups = resolveContractOverflowActionGroups({
      groups,
      primaryActions,
    });

    return {
      groups,
      primaryActions,
      overflowActionGroups,
    };
  }

  return {
    resolveContractActionGroups,
    resolveContractPrimaryActions,
    resolveContractOverflowActions,
    resolveContractOverflowActionGroups,
    resolveContractActionPresentation,
  };
}

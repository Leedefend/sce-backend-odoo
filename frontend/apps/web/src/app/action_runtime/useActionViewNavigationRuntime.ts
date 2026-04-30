import type { Ref } from 'vue';
import { pickContractNavQuery } from '../navigationContext';
import { readWorkspaceContext } from '../workspaceContext';
import { buildActionViewRowClickTarget } from '../runtime/actionViewInteractionRuntime';
import { resolveRowClickPushState } from '../runtime/actionViewNavigationApplyRuntime';

type Dict = Record<string, unknown>;

type UseActionViewNavigationRuntimeOptions = {
  routeQueryMap: Ref<Record<string, unknown>>;
  showHud: Ref<boolean>;
  menuId: Ref<number | null>;
  actionId: Ref<number | null>;
  actionContract: Ref<Record<string, unknown> | null>;
  resolvedModelRef: Ref<string>;
  modelRef: Ref<string>;
  routerPush: (target: unknown) => Promise<unknown>;
};

export function useActionViewNavigationRuntime(options: UseActionViewNavigationRuntimeOptions) {
  function resolveWorkspaceContextQuery() {
    return readWorkspaceContext(options.routeQueryMap.value);
  }

  function resolveCarryQuery(extra?: Record<string, unknown>) {
    return {
      ...pickContractNavQuery(options.routeQueryMap.value, extra),
      ...resolveWorkspaceContextQuery(),
    };
  }

  function resolveWorkbenchQuery(
    reason: string,
    payload?: { public?: Record<string, unknown>; diag?: Record<string, unknown> },
  ) {
    return {
      reason,
      ...resolveWorkspaceContextQuery(),
      ...(payload?.public || {}),
      ...(options.showHud.value
        ? {
            menu_id: options.menuId.value || undefined,
            action_id: options.actionId.value || undefined,
            ...(payload?.diag || {}),
          }
        : {}),
    };
  }

  function resolveRowOpenAction() {
    const contract = options.actionContract.value || {};
    const views = ((contract.views || (contract.ui_contract as Dict | undefined)?.views || {}) as Dict);
    const tree = ((views.tree || views.list || {}) as Dict);
    const rows = Array.isArray(tree.row_actions) ? tree.row_actions : [];
    return rows.find((row) => {
      if (!row || typeof row !== 'object') return false;
      const action = row as Dict;
      return String(action.level || '').trim() === 'row'
        && String(action.intent || action.kind || '').trim() === 'open'
        && String(action.trigger || action.display_mode || '').trim() === 'row_click';
    }) as Dict | undefined;
  }

  function handleRowClick(row: Dict) {
    const rowAction = resolveRowOpenAction();
    if (!rowAction) return;
    const payload = (rowAction.payload && typeof rowAction.payload === 'object' ? rowAction.payload : {}) as Dict;
    const viewMode = String(payload.view_mode || '').trim();
    if (viewMode && viewMode !== 'form') return;
    const routeTarget = buildActionViewRowClickTarget({
      targetModel: options.resolvedModelRef.value || options.modelRef.value,
      rawId: row.id,
      menuId: options.menuId.value,
      actionId: options.actionId.value,
      carryQuery: resolveCarryQuery(),
    });
    const rowClickState = resolveRowClickPushState({ routeTarget });
    if (!rowClickState.shouldNavigate) return;
    void options.routerPush(rowClickState.target);
  }

  return {
    resolveWorkspaceContextQuery,
    resolveCarryQuery,
    resolveWorkbenchQuery,
    handleRowClick,
  };
}

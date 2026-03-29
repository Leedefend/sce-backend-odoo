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

  function handleRowClick(row: Dict) {
    const targetModel = options.resolvedModelRef.value || options.modelRef.value;
    const carryQuery = resolveCarryQuery();
    if (targetModel === 'project.project') {
      delete carryQuery.scene;
      delete carryQuery.scene_key;
    }
    const routeTarget = buildActionViewRowClickTarget({
      targetModel,
      rawId: row.id,
      menuId: options.menuId.value,
      actionId: options.actionId.value,
      carryQuery,
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

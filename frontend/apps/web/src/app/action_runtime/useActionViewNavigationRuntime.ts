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
  recordOpenPolicyRef: Ref<{
    carry_query_mode?: string;
    carry_query_keys?: string[];
  } | null>;
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

  function applyRecordOpenPolicy(carryQuery: Dict) {
    const policy = options.recordOpenPolicyRef.value;
    const mode = String(policy?.carry_query_mode || 'preserve').trim().toLowerCase();
    if (mode === 'clear_scene_context') {
      delete carryQuery.scene;
      delete carryQuery.scene_key;
      return carryQuery;
    }
    if (mode === 'whitelist') {
      const keys = Array.isArray(policy?.carry_query_keys)
        ? policy.carry_query_keys.map((item) => String(item || '').trim()).filter(Boolean)
        : [];
      return keys.reduce<Dict>((result, key) => {
        if (key in carryQuery) result[key] = carryQuery[key];
        return result;
      }, {});
    }
    return carryQuery;
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
    const carryQuery = applyRecordOpenPolicy(resolveCarryQuery() as Dict);
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

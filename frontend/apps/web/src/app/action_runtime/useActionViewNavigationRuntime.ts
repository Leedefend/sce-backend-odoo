import type { Ref } from 'vue';
import { pickContractNavQuery } from '../navigationContext';
import { readWorkspaceContext } from '../workspaceContext';
import { buildEntryTargetRouteTarget } from '../routeQuery';
import { buildActionViewRowClickTarget } from '../runtime/actionViewInteractionRuntime';
import { resolveRowClickPushState } from '../runtime/actionViewNavigationApplyRuntime';
import { resolveUnifiedPageContractV2 } from '../contracts/unifiedPageContractV2';

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

  function materializeRowTargetValue(value: unknown, row: Dict): unknown {
    if (typeof value === 'string') {
      return value.replace(/\$\{([A-Za-z_][A-Za-z0-9_]*)\}/g, (_match, key) => String(row[key] ?? ''));
    }
    if (Array.isArray(value)) {
      return value.map((item) => materializeRowTargetValue(item, row));
    }
    if (value && typeof value === 'object') {
      return Object.entries(value as Dict).reduce<Dict>((acc, [key, item]) => {
        acc[key] = materializeRowTargetValue(item, row);
        return acc;
      }, {});
    }
    return value;
  }

  function parseRouteTarget(rawRoute: unknown, query: Dict) {
    const raw = String(rawRoute || '').trim();
    if (!raw) return null;
    const [path, queryRaw] = raw.split('?', 2);
    const routeQuery: Dict = { ...query };
    if (queryRaw) {
      const params = new URLSearchParams(queryRaw);
      params.forEach((value, key) => {
        if (key) routeQuery[key] = value;
      });
    }
    return { path: path || raw, query: routeQuery };
  }

  function routeQueryValue(value: unknown): string | number | undefined {
    if (typeof value === 'number' && Number.isFinite(value)) return value;
    const text = String(value ?? '').trim();
    return text || undefined;
  }

  function buildContractRowClickTarget(rowAction: Dict, row: Dict) {
    const rawTarget = rowAction.target && typeof rowAction.target === 'object' ? rowAction.target as Dict : {};
    const target = materializeRowTargetValue(rawTarget, row) as Dict;
    const carryQuery = resolveCarryQuery();
    const query = {
      ...carryQuery,
      menu_id: options.menuId.value || undefined,
      action_id: options.actionId.value || undefined,
      entry_intent: routeQueryValue(target.entry_intent || target.entryIntent),
      project_id: routeQueryValue(target.project_id || target.projectId),
      record_id: routeQueryValue(target.record_id || target.recordId),
    };
    const entryTarget = target.entry_target && typeof target.entry_target === 'object'
      ? target.entry_target as Dict
      : (String(target.scene_key || target.sceneKey || '').trim()
        ? {
            type: 'scene',
            scene_key: target.scene_key || target.sceneKey,
            route: target.route,
            scene_label: target.scene_label || target.sceneLabel,
          }
        : null);
    if (entryTarget) {
      return buildEntryTargetRouteTarget(entryTarget, {
        query,
        menuId: options.menuId.value,
        actionId: options.actionId.value,
        keepSceneRoute: false,
      });
    }
    if (target.route) {
      return parseRouteTarget(target.route, query);
    }
    return null;
  }

  function resolveRowOpenAction() {
    const contract = options.actionContract.value || {};
    const v2 = resolveUnifiedPageContractV2(contract);
    if (v2) {
      const v2ViewType = String(v2.pageInfo?.viewType || '').trim().toLowerCase();
      if (['list', 'tree', 'kanban'].includes(v2ViewType)) {
        const rows = Array.isArray(v2.actionContract?.actionRuleList) ? v2.actionContract.actionRuleList : [];
        const rowAction = rows.find((action) => {
          if (!action || typeof action !== 'object') return false;
          const typed = action as Dict;
          return String(typed.triggerType || '').trim() === 'row_click'
            || String(typed.sourceWidgetId || '').trim() === 'page.row'
            || String(typed.targetScope || '').trim() === 'row';
        });
        if (rowAction) return rowAction as Dict;
      }
    }
    const views = (contract.views || {}) as Dict;
    const view = ((views.kanban || views.tree || views.list || {}) as Dict);
    const rows = Array.isArray(view.row_actions) ? view.row_actions : [];
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
    const contractTarget = buildContractRowClickTarget(rowAction, row);
    if (contractTarget) {
      const rowClickState = resolveRowClickPushState({ routeTarget: contractTarget });
      if (rowClickState.shouldNavigate) void options.routerPush(rowClickState.target);
      return;
    }
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

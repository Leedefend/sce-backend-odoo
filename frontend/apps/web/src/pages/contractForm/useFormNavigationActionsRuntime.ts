import type { LocationQueryRaw, Router } from 'vue-router';
import { pickContractNavQuery } from '../../app/navigationContext';

export function useFormNavigationActionsRuntime(params: {
  actionId: () => number;
  currentQuery: () => Record<string, unknown>;
  isProjectIntakeCreateMode: () => boolean;
  resolveLandingPath: (fallback: string) => string;
  resolveWorkspaceContextQuery: () => LocationQueryRaw;
  router: Router;
  searchFilters: () => Array<{ key: string; domainRaw?: string; contextRaw?: string }>;
  setActiveFilterKey: (key: string) => void;
}) {
  async function openFilter(filterKey: string) {
    const actionId = params.actionId();
    if (!actionId) return;
    const selected = params.searchFilters().find((item) => item.key === filterKey);
    params.setActiveFilterKey(filterKey);
    await params.router.push({
      name: 'action',
      params: { actionId: String(actionId) },
      query: pickContractNavQuery(params.currentQuery(), {
        action_id: actionId,
        preset_filter: filterKey,
        domain_raw: selected?.domainRaw || undefined,
        context_raw: selected?.contextRaw || undefined,
      }),
    });
  }

  async function cancelIntake() {
    if (!params.isProjectIntakeCreateMode()) return;
    const target = params.resolveLandingPath('/');
    await params.router.replace({ path: target, query: params.resolveWorkspaceContextQuery() });
  }

  async function returnToProjectIntakeList(createdId: number | string) {
    const queryActionId = Number(params.currentQuery().action_id || params.actionId() || 0) || 0;
    if (queryActionId > 0) {
      await params.router.replace({
        path: `/a/${queryActionId}`,
        query: pickContractNavQuery(params.currentQuery(), {
          project_id: String(createdId),
          view_mode: 'tree',
        }),
      });
      return true;
    }
    return false;
  }

  return {
    cancelIntake,
    openFilter,
    returnToProjectIntakeList,
  };
}

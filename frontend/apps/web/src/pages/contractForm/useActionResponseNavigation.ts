import type { LocationQueryRaw, Router } from 'vue-router';
import { toPositiveInt } from '../../app/contractRuntime';
import { buildEntryTargetRouteTarget } from '../../app/routeQuery';
import {
  actionResponseNavQuery,
  actionResponseRouteTarget,
} from './actionContract';

export function useActionResponseNavigation(params: {
  router: Router;
  currentQuery: () => LocationQueryRaw;
}) {
  function navQuery(result: object | null | undefined, extra?: Record<string, unknown>) {
    return actionResponseNavQuery(params.currentQuery() as Record<string, unknown>, result, extra);
  }

  function routeTarget(target: unknown, result: object | null | undefined, extra?: Record<string, unknown>) {
    return actionResponseRouteTarget(params.currentQuery() as Record<string, unknown>, target, result, extra);
  }

  async function navigateActionResponseResult(result: unknown) {
    const resultRecord = result && typeof result === 'object'
      ? result as Record<string, unknown>
      : null;
    const entryTarget = resultRecord?.entry_target && typeof resultRecord.entry_target === 'object'
      ? resultRecord.entry_target as Record<string, unknown>
      : null;
    if (entryTarget) {
      await params.router.push(routeTarget(buildEntryTargetRouteTarget(entryTarget, {
        query: navQuery(resultRecord),
        actionId: resultRecord.action_id,
      }), resultRecord) as never);
      return true;
    }
    const nextActionId = toPositiveInt(resultRecord?.action_id);
    if (nextActionId) {
      await params.router.push({
        name: 'action',
        params: { actionId: String(nextActionId) },
        query: navQuery(resultRecord, { action_id: nextActionId }),
      });
      return true;
    }
    return false;
  }

  return {
    actionResponseNavQuery: navQuery,
    actionResponseRouteTarget: routeTarget,
    navigateActionResponseResult,
  };
}

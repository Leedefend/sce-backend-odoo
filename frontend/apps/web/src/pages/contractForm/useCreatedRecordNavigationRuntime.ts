import type { Router } from 'vue-router';
import { pickContractNavQuery } from '../../app/navigationContext';
import type { ContractAction } from './types';

export function useCreatedRecordNavigationRuntime(params: {
  applyProjectionRefreshPolicy: (policy?: ContractAction['refreshPolicy']) => Promise<void>;
  currentQuery: () => Record<string, unknown>;
  isProjectQuickIntakeMode: () => boolean;
  isProjectStandardIntakeMode: () => boolean;
  modelName: () => string;
  resolveWorkspaceContextQuery: () => Record<string, unknown>;
  returnToProjectIntakeList: (createdId: number | string) => Promise<boolean>;
  router: Router;
}) {
  async function navigateCreatedRecord(options: {
    createdId: number | string;
    nextSceneKey: string;
    nextSceneRoute: string;
    refreshPolicy?: ContractAction['refreshPolicy'];
  }) {
    const resolvedNextRoute = options.nextSceneRoute || (options.nextSceneKey ? `/s/${options.nextSceneKey}` : '');
    if (params.isProjectQuickIntakeMode() && params.modelName() === 'project.project') {
      await params.applyProjectionRefreshPolicy(options.refreshPolicy || { on_success: ['scene_projection', 'workbench_projection'] });
      if (await params.returnToProjectIntakeList(options.createdId)) return true;
      const routePath = resolvedNextRoute || '/s/project.management';
      await params.router.replace({
        path: routePath,
        query: {
          project_id: String(options.createdId),
          ...params.resolveWorkspaceContextQuery(),
        },
      });
      return true;
    }
    if (params.isProjectStandardIntakeMode() && resolvedNextRoute) {
      await params.applyProjectionRefreshPolicy(options.refreshPolicy || { on_success: ['scene_projection', 'workbench_projection'] });
      if (await params.returnToProjectIntakeList(options.createdId)) return true;
      await params.router.replace({
        path: resolvedNextRoute,
        query: {
          project_id: String(options.createdId),
          ...params.resolveWorkspaceContextQuery(),
        },
      });
      return true;
    }
    if (params.isProjectStandardIntakeMode() && params.modelName() === 'project.project') {
      await params.applyProjectionRefreshPolicy(options.refreshPolicy || { on_success: ['scene_projection', 'workbench_projection'] });
      if (await params.returnToProjectIntakeList(options.createdId)) return true;
    }
    const createdRoute = params.router.resolve({
      name: 'model-form',
      params: { model: params.modelName(), id: String(options.createdId) },
      query: pickContractNavQuery(params.currentQuery()),
    });
    window.location.replace(new URL(createdRoute.href, window.location.origin).toString());
    await new Promise<never>(() => {});
    return true;
  }

  return {
    navigateCreatedRecord,
  };
}

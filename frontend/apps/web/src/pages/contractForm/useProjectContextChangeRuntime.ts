import type { LocationQueryRaw, Router } from 'vue-router';
import { buildCanonicalSceneRouteTarget } from '../../app/routeQuery';

export function useProjectContextChangeRuntime(params: {
  isActive: () => boolean;
  modelName: () => string;
  recordId: () => number | null;
  resolveWorkspaceContextQuery: () => LocationQueryRaw;
  router: Router;
  selectedProjectId: () => number;
}) {
  function projectContextChangedProjectId(event: Event): number {
    const detail = event instanceof CustomEvent && event.detail && typeof event.detail === 'object'
      ? event.detail as Record<string, unknown>
      : {};
    return Number(detail.selected_project_id || params.selectedProjectId() || 0) || 0;
  }

  function projectContextChangedPreviousProjectId(event: Event): number {
    const detail = event instanceof CustomEvent && event.detail && typeof event.detail === 'object'
      ? event.detail as Record<string, unknown>
      : {};
    return Number(detail.previous_project_id || 0) || 0;
  }

  function handleProjectContextChanged(event: Event): void {
    if (!params.isActive()) return;
    const selectedProjectId = projectContextChangedProjectId(event);
    const previousProjectId = projectContextChangedPreviousProjectId(event);
    if (selectedProjectId > 0 && previousProjectId === selectedProjectId) return;
    if (params.modelName() === 'project.project' && params.recordId() === selectedProjectId) return;
    if (params.modelName() === 'project.project' && selectedProjectId > 0) {
      void params.router.replace({
        name: 'record',
        params: { model: 'project.project', id: String(selectedProjectId) },
        query: params.resolveWorkspaceContextQuery(),
      });
      return;
    }
    void params.router.replace(buildCanonicalSceneRouteTarget('projects.list', {
      query: {
        ...params.resolveWorkspaceContextQuery(),
        ...(selectedProjectId > 0 ? { project_id: String(selectedProjectId) } : {}),
      },
    }));
  }

  return {
    handleProjectContextChanged,
  };
}

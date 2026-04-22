export const PROJECT_INTAKE_SCENE_KEY = 'projects.intake';
export const PROJECT_INTAKE_SCENE_PATH = `/s/${PROJECT_INTAKE_SCENE_KEY}`;
export const PROJECT_INITIATION_PRODUCT_INTENT = 'project.initiation.enter';
export const PROJECT_DASHBOARD_ENTRY_INTENT = 'project.dashboard.enter';
export const PROJECT_EXECUTION_ENTRY_INTENT = 'project.execution.enter';
export const PROJECT_INITIATION_MENU_XMLID = 'smart_construction_core.menu_sc_project_initiation';

export type PendingProjectContext = {
  project_id: number;
  project_name: string;
};

let pendingProjectContext: PendingProjectContext | null = null;

export function setPendingProjectContext(context: PendingProjectContext | null) {
  pendingProjectContext = context && Number(context.project_id) > 0
    ? {
        project_id: Number(context.project_id),
        project_name: String(context.project_name || ''),
      }
    : null;
}

export function consumePendingProjectContext(): PendingProjectContext | null {
  const current = pendingProjectContext;
  pendingProjectContext = null;
  return current;
}

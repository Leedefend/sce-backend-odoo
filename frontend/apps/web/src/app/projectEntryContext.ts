export type ProjectEntryContext = {
  project_id: number;
  project_name: string;
  stage: string;
  stage_label: string;
  milestone: string;
  milestone_label: string;
  status: string;
  source?: string;
  confidence?: string;
};

export const PROJECT_MANAGEMENT_PATH = '/s/project.management';
export const MY_WORK_PATH = '/my-work';

export function normalizeProjectEntryContext(raw: unknown): ProjectEntryContext | null {
  if (!raw || typeof raw !== 'object') return null;
  const row = raw as Record<string, unknown>;
  const projectId = Number(row.project_id || 0);
  if (!Number.isFinite(projectId) || projectId <= 0) return null;
  return {
    project_id: projectId,
    project_name: String(row.project_name || ''),
    stage: String(row.stage || ''),
    stage_label: String(row.stage_label || ''),
    milestone: String(row.milestone || ''),
    milestone_label: String(row.milestone_label || ''),
    status: String(row.status || ''),
    source: String(row.source || ''),
    confidence: String(row.confidence || ''),
  };
}

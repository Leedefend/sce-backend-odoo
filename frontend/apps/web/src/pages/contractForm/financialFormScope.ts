import type { LocationQuery } from 'vue-router';
import { pickContractNavQuery } from '../../app/navigationContext';

type Query = LocationQuery | Record<string, unknown>;

export function isProjectScopeExempt(query: Query) {
  return String(query.project_scope_policy || '').trim() === 'exempt';
}

export function scopedOnchangeContext(query: Query, projectId: unknown) {
  return pickContractNavQuery(query as Record<string, unknown>, {
    current_project_id: isProjectScopeExempt(query) ? undefined : Number(projectId || 0) || undefined,
  });
}

export function scopedCreateContext(query: Query, base: Record<string, unknown>, projectId: unknown) {
  const context = { ...base, ...pickContractNavQuery(query as Record<string, unknown>) };
  if (isProjectScopeExempt(query)) {
    delete context.current_project_id;
    delete context.default_project_id;
  } else if (Number(projectId || 0) > 0) {
    context.current_project_id = Number(projectId);
  }
  return context;
}

export function applyRouteRelationLabel(
  query: Query,
  fieldName: string,
  relationId: number,
  apply: (label: string) => void,
) {
  const label = String(query[`default_${fieldName}_label`] || '').trim();
  if (relationId > 0 && label) apply(label);
}

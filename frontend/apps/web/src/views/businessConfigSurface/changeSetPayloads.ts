function sequenced(names: string[], key: 'name' | 'field') {
  return names.map((name, index) => ({ [key]: name, sequence: (index + 1) * 10 }));
}

export function contractTargetKey(model: string, viewType: string, actionId = 0, viewId = 0) {
  return `view_orchestration:${model}:${viewType || 'all'}:action:${actionId}:view:${viewId}`;
}

export function listContractPayload(names: string[]) {
  return { view_orchestration: { views: { tree: { columns: sequenced(names, 'name') } } } };
}

export function searchContractPayload(filters: string[], groupBy: string[]) {
  return {
    view_orchestration: {
      views: {
        search: {
          filters: sequenced(filters, 'field'),
          group_by: sequenced(groupBy, 'field'),
        },
      },
    },
  };
}

export function analysisContractPayload(viewType: 'pivot' | 'graph', measures: string[], dimensions: string[], graphType: string) {
  const spec: Record<string, unknown> = {
    measures: sequenced(measures, 'name'),
    dimensions: sequenced(dimensions, 'name'),
    ...(measures[0] ? { measure: measures[0] } : {}),
    ...(dimensions[0] ? { dimension: dimensions[0] } : {}),
  };
  if (viewType === 'graph') spec.type = graphType || 'bar';
  else spec.chart_policy = { type: graphType || 'bar' };
  return {
    view_orchestration: {
      views: { [viewType]: spec },
      context: { source: 'business_config_analysis_editor', source_status: 'tenant_runtime' },
    },
  };
}

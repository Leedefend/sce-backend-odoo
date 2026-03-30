export type SceneReadyEntry = Record<string, unknown>;

function asDict(value: unknown): Record<string, unknown> {
  return (value && typeof value === 'object' && !Array.isArray(value))
    ? (value as Record<string, unknown>)
    : {};
}

function asText(value: unknown): string {
  return typeof value === 'string' ? value.trim() : '';
}

function parseNextSceneFromRoute(route: string): string {
  const value = asText(route);
  if (!value) return '';
  if (value.startsWith('/s/')) {
    return asText(value.replace('/s/', ''));
  }
  return '';
}

export function findSceneReadyEntry(contract: { scenes?: unknown[] } | null | undefined, sceneKey: string) {
  const key = asText(sceneKey);
  if (!key) return null;
  const rows = Array.isArray(contract?.scenes) ? contract?.scenes : [];
  for (const item of rows) {
    const row = asDict(item);
    const scene = asDict(row.scene);
    const page = asDict(row.page);
    const candidate = asText(scene.key || page.scene_key);
    if (candidate && candidate === key) {
      return row;
    }
  }
  return null;
}

export function resolveListSceneReady(entry: SceneReadyEntry | null) {
  const row = asDict(entry);
  const searchSurface = asDict(row.search_surface);
  const permissionSurface = asDict(row.permission_surface);
  const actionSurface = asDict(row.action_surface);
  const workflowSurface = asDict(row.workflow_surface);
  const actions = Array.isArray(row.actions) ? row.actions as Array<Record<string, unknown>> : [];
  const blockRows = Array.isArray(row.blocks) ? row.blocks : [];

  const columns = blockRows
    .map((item) => asDict(item))
    .map((item) => {
      const raw = item.fields;
      if (!Array.isArray(raw)) return [];
      return raw.map((field) => {
        if (typeof field === 'string') return asText(field);
        const payload = asDict(field);
        return asText(payload.name || payload.field || payload.key);
      }).filter(Boolean);
    })
    .find((list) => list.length > 0) || [];

  return {
    columns,
    defaultSort: asText(searchSurface.default_sort),
    mode: asText(searchSurface.mode),
    filters: Array.isArray(searchSurface.filters) ? searchSurface.filters : [],
    groupBy: Array.isArray(searchSurface.group_by) ? searchSurface.group_by : [],
    searchPanel: Array.isArray(searchSurface.searchpanel) ? searchSurface.searchpanel : [],
    searchableFields: Array.isArray(searchSurface.fields) ? searchSurface.fields : [],
    actions,
    actionSurface,
    permissionSurface,
    workflowSurface,
  };
}

export function resolveFormSceneReady(entry: SceneReadyEntry | null) {
  const row = asDict(entry);
  const validationSurface = asDict(row.validation_surface);
  const permissionSurface = asDict(row.permission_surface);
  const workflowSurface = asDict(row.workflow_surface);
  const actionSurface = asDict(row.action_surface);
  const meta = asDict(row.meta);
  const actions = Array.isArray(row.actions) ? row.actions as Array<Record<string, unknown>> : [];

  const preferredAction = actions.find((item) => {
    const key = asText(item.key).toLowerCase();
    const tier = asText(item.tier).toLowerCase();
    return tier === 'primary' || key === 'submit_intake' || key === 'create_project';
  }) || actions[0] || {};
  const preferredTarget = asDict(asDict(preferredAction).target);

  const nextSceneKey =
    asText(row.next_scene)
    || asText(workflowSurface.next_scene)
    || asText(actionSurface.next_scene)
    || asText(meta.next_scene)
    || asText(preferredTarget.scene_key)
    || parseNextSceneFromRoute(asText(preferredTarget.route));
  const nextSceneRoute =
    asText(row.next_scene_route)
    || asText(workflowSurface.next_scene_route)
    || asText(actionSurface.next_scene_route)
    || asText(meta.next_scene_route)
    || asText(preferredTarget.route)
    || (nextSceneKey ? `/s/${nextSceneKey}` : '');

  return {
    requiredFields: Array.isArray(validationSurface.required_fields)
      ? validationSurface.required_fields.map((item) => asText(item)).filter(Boolean)
      : [],
    validationSurface,
    permissionSurface,
    workflowSurface,
    actionSurface,
    actions,
    nextSceneKey,
    nextSceneRoute,
  };
}

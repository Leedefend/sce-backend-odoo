export type SceneReadyEntry = Record<string, unknown>;
export type SceneReadyBlock = Record<string, unknown>;
type SceneViewMode = 'form' | 'list' | 'kanban';

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

function resolveSceneReadyBlocks(entry: SceneReadyEntry | null, mode?: SceneViewMode) {
  const row = asDict(entry);
  const blocksByView = asDict(row.scene_blocks_by_view);
  const viewBlocks = mode ? blocksByView[mode] : undefined;
  const directViewBlocks = Array.isArray(viewBlocks) ? viewBlocks : [];
  const directBlocks = Array.isArray(row.scene_blocks) ? row.scene_blocks : [];
  const surfaceBlocks = asDict(row.surface).blocks;
  const fallbackBlocks = Array.isArray(surfaceBlocks) ? surfaceBlocks : [];
  const raw = directViewBlocks.length
    ? directViewBlocks
    : (directBlocks.length ? directBlocks : fallbackBlocks);
  return raw
    .map((item) => asDict(item))
    .filter((item) => Object.keys(item).length > 0)
    .map((item, index) => ({
      key: asText(item.key || `block_${index + 1}`),
      kind: asText(item.kind || item.type || 'content'),
      title: asText(item.title || item.label || item.key),
      order: Number.isFinite(Number(item.order)) ? Number(item.order) : index + 1,
      visible: item.visible !== false,
      semantic_role: asText(item.semantic_role || item.semanticRole),
      layout: asDict(item.layout),
      data_deps: asDict(item.data_deps || item.dataDeps),
      actions: Array.isArray(item.actions) ? item.actions.map((action) => asDict(action)) : [],
      children: Array.isArray(item.children) ? item.children.map((child) => asDict(child)) : [],
      payload: asDict(item.payload),
    }));
}

function filterSceneReadyBlocksByKinds(
  blocks: Array<Record<string, unknown>>,
  allowedKinds: Set<string>,
) {
  if (!blocks.length) return [];
  return blocks.filter((item) => {
    const kind = asText(item.kind).toLowerCase();
    return kind ? allowedKinds.has(kind) : false;
  });
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

  const sceneBlocks = resolveSceneReadyBlocks(entry, 'list');
  const listBlockKinds = new Set([
    'page_shell',
    'header_bar',
    'toolbar',
    'list_view',
    'kanban_board',
    'overview_strip',
    'pagination',
    'footer',
  ]);
  return {
    columns,
    defaultSort: asText(searchSurface.default_sort),
    filters: Array.isArray(searchSurface.filters) ? searchSurface.filters : [],
    groupBy: Array.isArray(searchSurface.group_by) ? searchSurface.group_by : [],
    searchableFields: Array.isArray(searchSurface.fields) ? searchSurface.fields : [],
    actions,
    sceneBlocks: filterSceneReadyBlocksByKinds(sceneBlocks, listBlockKinds),
    actionSurface,
    permissionSurface,
    workflowSurface,
  };
}

export function resolveCollectionSceneReady(entry: SceneReadyEntry | null, mode: 'list' | 'kanban' = 'list') {
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

  const sceneBlocks = resolveSceneReadyBlocks(entry, mode);
  const allowedKinds = mode === 'kanban'
    ? new Set([
      'page_shell',
      'header_bar',
      'toolbar',
      'overview_strip',
      'kanban_board',
      'footer',
    ])
    : new Set([
      'page_shell',
      'header_bar',
      'toolbar',
      'list_view',
      'pagination',
      'footer',
    ]);
  return {
    columns,
    defaultSort: asText(searchSurface.default_sort),
    filters: Array.isArray(searchSurface.filters) ? searchSurface.filters : [],
    groupBy: Array.isArray(searchSurface.group_by) ? searchSurface.group_by : [],
    searchableFields: Array.isArray(searchSurface.fields) ? searchSurface.fields : [],
    actions,
    sceneBlocks: filterSceneReadyBlocksByKinds(sceneBlocks, allowedKinds),
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

  const sceneBlocks = resolveSceneReadyBlocks(entry, 'form');
  const formBlockKinds = new Set([
    'page_shell',
    'header_bar',
    'statusbar',
    'primary_actions',
    'smart_actions',
    'body',
    'relation_block',
    'chatter',
    'footer',
  ]);
  const resolvedFormBlocks = filterSceneReadyBlocksByKinds(sceneBlocks, formBlockKinds);

  return {
    requiredFields: Array.isArray(validationSurface.required_fields)
      ? validationSurface.required_fields.map((item) => asText(item)).filter(Boolean)
      : [],
    validationSurface,
    permissionSurface,
    workflowSurface,
    actionSurface,
    actions,
    sceneBlocks: resolvedFormBlocks,
    nextSceneKey,
    nextSceneRoute,
  };
}

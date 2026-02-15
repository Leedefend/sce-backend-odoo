export type WorkspacePreset = 'pending_approval' | 'project_intake' | 'cost_watchlist' | '';

export type WorkspaceContext = {
  preset?: WorkspacePreset | string;
  ctx_source?: string;
  search?: string;
};

function text(value: unknown) {
  return String(value || '').trim();
}

export function readWorkspaceContext(query: Record<string, unknown>): WorkspaceContext {
  const preset = text(query.preset);
  const ctxSource = text(query.ctx_source);
  const search = text(query.search);
  const context: WorkspaceContext = {};
  if (preset) context.preset = preset;
  if (ctxSource) context.ctx_source = ctxSource;
  if (search) context.search = search;
  return context;
}

export function mergeWorkspaceContext(
  query: Record<string, unknown>,
  context: WorkspaceContext,
): Record<string, unknown> {
  return { ...query, ...context };
}

export function stripWorkspaceContext(query: Record<string, unknown>): Record<string, unknown> {
  const next = { ...query };
  delete next.preset;
  delete next.ctx_source;
  delete next.search;
  return next;
}

export function hasWorkspaceContext(context: WorkspaceContext) {
  return Boolean(context.preset || context.ctx_source || context.search);
}

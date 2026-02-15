export type WorkspacePreset = 'pending_approval' | 'project_intake' | 'cost_watchlist' | '';

export type WorkspaceContext = {
  preset?: WorkspacePreset | string;
  ctx_source?: string;
  search?: string;
  entry_context?: WorkspaceEntryContext;
};

export type WorkspaceEntryContext = {
  section?: string;
  source?: string;
  reason?: string;
  search?: string;
};

function text(value: unknown) {
  return String(value || '').trim();
}

function normalizeEntryContext(value: unknown): WorkspaceEntryContext | undefined {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return undefined;
  const source = value as Record<string, unknown>;
  const section = text(source.section);
  const rawSource = text(source.source);
  const reason = text(source.reason);
  const search = text(source.search);
  const context: WorkspaceEntryContext = {};
  if (section) context.section = section;
  if (rawSource) context.source = rawSource;
  if (reason) context.reason = reason;
  if (search) context.search = search;
  return Object.keys(context).length ? context : undefined;
}

function readEntryContext(query: Record<string, unknown>): WorkspaceEntryContext | undefined {
  const raw = query.entry_context;
  if (!raw) return undefined;
  if (typeof raw === 'object') return normalizeEntryContext(raw);
  const textValue = text(raw);
  if (!textValue) return undefined;
  try {
    const parsed = JSON.parse(textValue) as unknown;
    return normalizeEntryContext(parsed);
  } catch {
    return undefined;
  }
}

export function readWorkspaceContext(query: Record<string, unknown>): WorkspaceContext {
  const preset = text(query.preset);
  const ctxSource = text(query.ctx_source);
  const search = text(query.search);
  const entryContext = readEntryContext(query);
  const context: WorkspaceContext = {};
  if (preset) context.preset = preset;
  if (ctxSource) context.ctx_source = ctxSource;
  if (search) context.search = search;
  if (entryContext) context.entry_context = entryContext;
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
  delete next.entry_context;
  return next;
}

export function hasWorkspaceContext(context: WorkspaceContext) {
  return Boolean(context.preset || context.ctx_source || context.search || context.entry_context);
}

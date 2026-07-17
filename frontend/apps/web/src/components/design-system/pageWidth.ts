export type WorkspaceFrameMode = 'business';

export type ContentLayoutMode =
  | 'data-grid'
  | 'record-grid'
  | 'form-grid'
  | 'focused-form'
  | 'reading';

export type PageKind =
  | 'list'
  | 'report'
  | 'table'
  | 'workbench'
  | 'detail'
  | 'edit'
  | 'create'
  | 'visualization'
  | 'unknown';

const CONTENT_LAYOUT_MODES = new Set<ContentLayoutMode>([
  'data-grid',
  'record-grid',
  'form-grid',
  'focused-form',
  'reading',
]);

const PAGE_KIND_CONTENT_LAYOUT: Record<PageKind, ContentLayoutMode> = {
  list: 'data-grid',
  report: 'data-grid',
  table: 'data-grid',
  workbench: 'data-grid',
  detail: 'record-grid',
  edit: 'form-grid',
  create: 'focused-form',
  visualization: 'data-grid',
  unknown: 'record-grid',
};

const LEGACY_WIDTH_TO_CONTENT_LAYOUT: Record<string, ContentLayoutMode> = {
  data: 'data-grid',
  standard: 'record-grid',
  focused: 'focused-form',
  fluid: 'data-grid',
};

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null;
}

export function normalizeContentLayoutMode(value: unknown, fallback: ContentLayoutMode = 'record-grid'): ContentLayoutMode {
  const normalized = String(value || '').trim().toLowerCase();
  if (CONTENT_LAYOUT_MODES.has(normalized as ContentLayoutMode)) return normalized as ContentLayoutMode;
  return LEGACY_WIDTH_TO_CONTENT_LAYOUT[normalized] || fallback;
}

export function contractContentLayoutMode(contract: unknown): unknown {
  const root = asRecord(contract);
  if (!root) return '';
  const page = asRecord(root.page);
  const presentation = asRecord(root.presentation);
  const candidates = [
    asRecord(root.layout)?.content_layout_mode,
    asRecord(page?.layout)?.content_layout_mode,
    asRecord(presentation?.layout)?.content_layout_mode,
  ];
  return candidates.find((value) => String(value || '').trim()) || '';
}

export function resolveContentLayoutMode(options: {
  contractContentLayout?: unknown;
  pageKind?: PageKind;
}): ContentLayoutMode {
  const pageKind = options.pageKind || 'unknown';
  const fallback = PAGE_KIND_CONTENT_LAYOUT[pageKind] || 'record-grid';
  if (String(options.contractContentLayout || '').trim()) {
    return normalizeContentLayoutMode(options.contractContentLayout, fallback);
  }
  return fallback;
}

export function contentLayoutModeClass(mode: ContentLayoutMode): string {
  return `sc-content-layout--${mode}`;
}

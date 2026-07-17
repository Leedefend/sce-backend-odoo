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

const LEGACY_WIDTH_TO_CONTENT_LAYOUT: Record<string, ContentLayoutMode | 'page-kind'> = {
  data: 'data-grid',
  standard: 'page-kind',
  focused: 'focused-form',
  fluid: 'data-grid',
};

export type ContractContentLayoutSelection = {
  source: 'content_layout_mode' | 'legacy_width_mode';
  value: unknown;
};

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null;
}

export function normalizeContentLayoutMode(value: unknown, fallback: ContentLayoutMode = 'record-grid'): ContentLayoutMode {
  const normalized = String(value || '').trim().toLowerCase();
  if (CONTENT_LAYOUT_MODES.has(normalized as ContentLayoutMode)) return normalized as ContentLayoutMode;
  const legacy = LEGACY_WIDTH_TO_CONTENT_LAYOUT[normalized];
  return legacy && legacy !== 'page-kind' ? legacy : fallback;
}

export function contractContentLayoutMode(contract: unknown): ContractContentLayoutSelection | '' {
  const root = asRecord(contract);
  if (!root) return '';
  const page = asRecord(root.page);
  const presentation = asRecord(root.presentation);
  const layouts = [
    asRecord(root.layout),
    asRecord(page?.layout),
    asRecord(presentation?.layout),
  ];
  const contentLayout = layouts
    .map((layout) => layout?.content_layout_mode)
    .find((value) => String(value || '').trim());
  if (String(contentLayout || '').trim()) {
    return { source: 'content_layout_mode', value: contentLayout };
  }
  const legacyWidth = layouts
    .map((layout) => layout?.width_mode)
    .find((value) => String(value || '').trim());
  return String(legacyWidth || '').trim()
    ? { source: 'legacy_width_mode', value: legacyWidth }
    : '';
}

export function resolveContentLayoutMode(options: {
  contractContentLayout?: unknown;
  pageKind?: PageKind;
}): ContentLayoutMode {
  const pageKind = options.pageKind || 'unknown';
  const fallback = PAGE_KIND_CONTENT_LAYOUT[pageKind] || 'record-grid';
  const selection = asRecord(options.contractContentLayout);
  if (selection && selection.source === 'content_layout_mode') {
    return normalizeContentLayoutMode(selection.value, fallback);
  }
  if (selection && selection.source === 'legacy_width_mode') {
    const legacyValue = String(selection.value || '').trim().toLowerCase();
    const mapped = LEGACY_WIDTH_TO_CONTENT_LAYOUT[legacyValue];
    return mapped && mapped !== 'page-kind' ? mapped : fallback;
  }
  if (String(options.contractContentLayout || '').trim()) {
    return normalizeContentLayoutMode(options.contractContentLayout, fallback);
  }
  return fallback;
}

export function contentLayoutModeClass(mode: ContentLayoutMode): string {
  return `sc-content-layout--${mode}`;
}

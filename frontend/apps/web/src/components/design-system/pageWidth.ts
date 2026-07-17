export type PageWidthMode = 'data' | 'standard' | 'focused' | 'fluid';

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

const PAGE_WIDTH_MODES = new Set<PageWidthMode>(['data', 'standard', 'focused', 'fluid']);

const PAGE_KIND_WIDTH_MODE: Record<PageKind, PageWidthMode> = {
  list: 'data',
  report: 'data',
  table: 'data',
  workbench: 'data',
  detail: 'standard',
  edit: 'standard',
  create: 'focused',
  visualization: 'fluid',
  unknown: 'standard',
};

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null;
}

export function normalizePageWidthMode(value: unknown): PageWidthMode {
  const normalized = String(value || '').trim().toLowerCase();
  return PAGE_WIDTH_MODES.has(normalized as PageWidthMode)
    ? normalized as PageWidthMode
    : 'standard';
}

export function contractPageWidthMode(contract: unknown): unknown {
  const root = asRecord(contract);
  if (!root) return '';
  const page = asRecord(root.page);
  const presentation = asRecord(root.presentation);
  const candidates = [
    asRecord(root.layout)?.width_mode,
    asRecord(page?.layout)?.width_mode,
    asRecord(presentation?.layout)?.width_mode,
  ];
  return candidates.find((value) => String(value || '').trim()) || '';
}

export function resolvePageWidthMode(options: {
  contractWidthMode?: unknown;
  pageKind?: PageKind;
}): PageWidthMode {
  if (String(options.contractWidthMode || '').trim()) {
    return normalizePageWidthMode(options.contractWidthMode);
  }
  return PAGE_KIND_WIDTH_MODE[options.pageKind || 'unknown'] || 'standard';
}

export function pageWidthModeClass(mode: PageWidthMode): string {
  return `sc-page-frame--${mode}`;
}

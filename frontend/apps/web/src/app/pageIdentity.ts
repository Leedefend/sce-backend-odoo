export type PageIdentitySource = 'record' | 'action' | 'menu' | 'model' | 'product-fallback';

export type PageIdentityState = 'loading' | 'empty' | 'denied' | 'not-found' | 'error' | '';

export interface PageBreadcrumb {
  label: string;
  to?: string;
}

export interface ProductPageIdentity {
  title: string;
  subtitle?: string;
  documentTitle: string;
  breadcrumbs: PageBreadcrumb[];
  source: PageIdentitySource;
}

export interface PageIdentityInput {
  kind?: 'list' | 'detail' | 'create' | 'edit' | 'page';
  actionName?: unknown;
  menuName?: unknown;
  modelName?: unknown;
  modelLabel?: unknown;
  record?: Record<string, unknown> | null;
  recordDisplayName?: unknown;
  primaryFieldNames?: unknown[];
  subtitle?: unknown;
  breadcrumbs?: PageBreadcrumb[];
  state?: PageIdentityState;
  fallbackTitle?: unknown;
}

export const PRODUCT_APP_TITLE = '智能施工企业管理平台';

const GENERIC_TITLES = new Set([
  '业务动作',
  '业务菜单',
  '业务表单',
  '新建业务表单',
  '编辑记录',
  '表单',
]);

const DEFAULT_PRIMARY_FIELDS = [
  'name',
  'code',
  'number',
  'reference',
  'document_no',
  'contract_no',
  'project_code',
];

function text(value: unknown): string {
  if (Array.isArray(value)) return text(value.length > 1 ? value[1] : value[0]);
  if (value === null || value === undefined || typeof value === 'object') return '';
  return String(value).replace(/\s+/g, ' ').trim();
}

export function isTechnicalPageIdentity(value: unknown): boolean {
  const normalized = text(value);
  if (!normalized) return true;
  if (/^(undefined|null|nan)$/i.test(normalized)) return true;
  if (/^\d+$/.test(normalized)) return true;
  if (/^(?:[a-z_][a-z0-9_]*\.)+[a-z_][a-z0-9_]*(?:\s*#\s*\d+)?$/i.test(normalized)) return true;
  if (/\s#\d+$/.test(normalized)) return true;
  return GENERIC_TITLES.has(normalized);
}

export function productIdentityText(value: unknown): string {
  const normalized = text(value);
  return isTechnicalPageIdentity(normalized) ? '' : normalized;
}

function recordIdentity(input: PageIdentityInput): string {
  const direct = productIdentityText(input.recordDisplayName);
  if (direct) return direct;
  const record = input.record || {};
  const displayName = productIdentityText(record.display_name);
  if (displayName) return displayName;
  const primaryNames = Array.from(new Set([
    ...(input.primaryFieldNames || []).map((name) => text(name)).filter(Boolean),
    ...DEFAULT_PRIMARY_FIELDS,
  ]));
  for (const name of primaryNames) {
    const value = productIdentityText(record[name]);
    if (value) return value;
  }
  return '';
}

function objectLabel(input: PageIdentityInput): { label: string; source: PageIdentitySource } {
  const action = productIdentityText(input.actionName);
  if (action) return { label: action, source: 'action' };
  const menu = productIdentityText(input.menuName);
  if (menu) return { label: menu, source: 'menu' };
  const model = productIdentityText(input.modelLabel);
  if (model) return { label: model, source: 'model' };
  return { label: '', source: 'product-fallback' };
}

function stripOperation(value: string): string {
  return value.replace(/^(?:新建|编辑)/, '').replace(/(?:列表|详情)$/, '').trim();
}

function stateLabel(state: PageIdentityState): string {
  const labels: Record<PageIdentityState, string> = {
    loading: '加载中',
    empty: '暂无数据',
    denied: '无权访问',
    'not-found': '记录不存在',
    error: '加载失败',
    '': '',
  };
  return labels[state] || '';
}

export function normalizePageBreadcrumbs(rows: PageBreadcrumb[] | undefined, currentTitle: string): PageBreadcrumb[] {
  const out: PageBreadcrumb[] = [];
  for (const row of rows || []) {
    const label = productIdentityText(row?.label);
    if (!label) continue;
    if (out[out.length - 1]?.label === label) continue;
    out.push({ label, ...(row.to ? { to: String(row.to) } : {}) });
  }
  const current = productIdentityText(currentTitle);
  if (current && out[out.length - 1]?.label !== current) out.push({ label: current });
  if (out.length) delete out[out.length - 1].to;
  return out;
}

export function resolveProductPageIdentity(input: PageIdentityInput): ProductPageIdentity {
  const kind = input.kind || 'page';
  const state = input.state || '';
  const object = objectLabel(input);
  const record = state === 'denied' || state === 'not-found' ? '' : recordIdentity(input);
  let title = '';
  let source: PageIdentitySource = object.source;

  if (kind === 'detail' || kind === 'edit') {
    if (record) {
      title = kind === 'edit' ? `编辑 ${record}` : record;
      source = 'record';
    } else if (object.label) {
      const objectName = stripOperation(object.label);
      title = kind === 'edit' ? `编辑${objectName}` : state ? objectName : `${objectName}详情`;
    } else {
      title = productIdentityText(input.modelLabel) ? `${productIdentityText(input.modelLabel)}详情` : '记录详情';
      source = productIdentityText(input.modelLabel) ? 'model' : 'product-fallback';
    }
  } else if (kind === 'create') {
    const label = stripOperation(object.label || productIdentityText(input.fallbackTitle));
    title = label ? `新建${label}` : '新建记录';
  } else if (kind === 'list') {
    title = object.label || productIdentityText(input.fallbackTitle) || '业务列表';
  } else {
    title = object.label || record || productIdentityText(input.fallbackTitle) || '工作台';
    if (!object.label && record) source = 'record';
  }

  const suffix = stateLabel(state);
  if (suffix) {
    if (state === 'not-found') {
      title = suffix;
      source = 'product-fallback';
    }
    else if (state === 'denied' && !object.label) title = suffix;
    else title = `${title} · ${suffix}`;
  }
  if (isTechnicalPageIdentity(title)) {
    title = state === 'denied' ? '无权访问' : state === 'not-found' ? '记录不存在' : '工作台';
    source = 'product-fallback';
  }

  const subtitle = productIdentityText(input.subtitle) || undefined;
  return {
    title,
    ...(subtitle ? { subtitle } : {}),
    documentTitle: `${title} - ${PRODUCT_APP_TITLE}`,
    breadcrumbs: normalizePageBreadcrumbs(input.breadcrumbs, title),
    source,
  };
}

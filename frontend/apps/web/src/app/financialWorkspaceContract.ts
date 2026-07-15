export type WorkspaceCurrency = {
  id: number;
  name: string;
  symbol: string;
  position: 'before' | 'after' | string;
  decimal_places: number;
};

export type WorkspaceFact = {
  key: string;
  label: string;
  kind: 'money' | 'relation' | 'date' | 'datetime' | string;
  value: unknown;
  currency?: WorkspaceCurrency | null;
};

export type WorkspaceRouteTarget = {
  name: string;
  params: { model: string; id: number | string };
  query?: Record<string, string | number>;
};

export type WorkspaceRelatedRecord = {
  model: string;
  id: number;
  label: string;
  route?: WorkspaceRouteTarget | null;
  inline_only?: boolean;
  amount?: number | null;
  currency?: WorkspaceCurrency | null;
  date?: string | null;
  status?: string;
};

export type WorkspaceRelationship = {
  key: string;
  label: string;
  empty_text: string;
  records: WorkspaceRelatedRecord[];
};

export type WorkspaceDetailCell = {
  key: string;
  label: string;
  kind?: string;
  value: unknown;
  currency?: WorkspaceCurrency | null;
};
export type WorkspaceDetailSection = {
  key: string;
  label: string;
  empty_text: string;
  rows: Array<{ key: string; cells: WorkspaceDetailCell[] }>;
};

export type FinancialWorkspaceContract = {
  version: string;
  kind: string;
  model: string;
  record_id: number;
  record_label: string;
  state: { value: string; label: string };
  currency?: WorkspaceCurrency | null;
  facts: WorkspaceFact[];
  relationships: WorkspaceRelationship[];
  details: WorkspaceDetailSection[];
  entry_actions?: Array<{
    key: string;
    label: string;
    route: WorkspaceRouteTarget;
    source_authority?: string;
  }>;
  audit: WorkspaceFact[];
  currency_risk?: { mismatch: boolean; message: string };
  source?: { kind: string; authorities?: string[]; projection_only?: boolean };
};

function record(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : {};
}

export function resolveFinancialWorkspaceContract(source: unknown): FinancialWorkspaceContract | null {
  const root = record(source);
  const form = record(record(root.views).form);
  const candidate = record(form.business_workspace);
  const recordId = Number(candidate.record_id || 0);
  const facts = Array.isArray(candidate.facts) ? candidate.facts : [];
  if (String(candidate.version || '') !== '1.0' || !recordId || !facts.length) return null;
  return candidate as unknown as FinancialWorkspaceContract;
}

export function formatWorkspaceMoney(value: unknown, currency?: WorkspaceCurrency | null): string {
  if (value === null || value === undefined || value === '') return '—';
  const amount = Number(value);
  if (!Number.isFinite(amount)) return '—';
  const code = String(currency?.name || '').trim();
  const digits = Math.max(0, Math.min(6, Number(currency?.decimal_places ?? 2)));
  if (/^[A-Z]{3}$/.test(code)) {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: code,
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    }).format(amount);
  }
  const number = new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(amount);
  const symbol = String(currency?.symbol || code || '').trim();
  if (!symbol) return number;
  return currency?.position === 'after' ? `${number} ${symbol}` : `${symbol}${number}`;
}

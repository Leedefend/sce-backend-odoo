type Dict = Record<string, unknown>;

export type ActionViewSurfaceKind = 'risk' | 'contract' | 'cost' | 'project' | 'generic';

export type ProjectionMetricItem = {
  key: string;
  label: string;
  value: string;
  tone: string;
};

function normalizeSurfaceKind(raw: unknown): ActionViewSurfaceKind {
  const value = String(raw || '').trim().toLowerCase();
  if (value === 'risk' || value === 'contract' || value === 'cost' || value === 'project') {
    return value;
  }
  return 'generic';
}

export function resolveActionViewSurfaceKind(options: {
  strictContractMode: boolean;
  strictSurfaceContract: Dict;
  contractSurfaceKind: unknown;
  extensionSurfaceKind: unknown;
}): ActionViewSurfaceKind {
  const contractKind = normalizeSurfaceKind(options.contractSurfaceKind);
  const extensionKind = normalizeSurfaceKind(options.extensionSurfaceKind);
  if (options.strictContractMode) {
    const strictKind = normalizeSurfaceKind(options.strictSurfaceContract.kind);
    if (strictKind !== 'generic') return strictKind;
    if (contractKind !== 'generic') return contractKind;
    return extensionKind;
  }
  if (contractKind !== 'generic') return contractKind;
  return extensionKind;
}

export function mapProjectionMetricItems(rowsRaw: unknown, keyPrefix: string): ProjectionMetricItem[] {
  const rows = Array.isArray(rowsRaw) ? (rowsRaw as Array<Record<string, unknown>>) : [];
  return rows
    .map((row, index) => ({
      key: String(row.key || `${keyPrefix}_${index + 1}`),
      label: String(row.label || row.key || ''),
      value: String(row.value ?? ''),
      tone: String(row.tone || 'neutral'),
    }))
    .filter((item) => item.label);
}

type Dict = Record<string, unknown>;

export function resolveAssigneeOptionsLoadGuard(options: {
  hasAssigneeField: boolean;
}): { ok: true } | { ok: false; assigneeOptions: Array<{ id: number; name: string }>; selectedAssigneeId: null } {
  if (options.hasAssigneeField) return { ok: true };
  return {
    ok: false,
    assigneeOptions: [],
    selectedAssigneeId: null,
  };
}

export function resolveAssigneeOptions(recordsRaw: unknown[]): Array<{ id: number; name: string }> {
  const rows = Array.isArray(recordsRaw) ? recordsRaw : [];
  return rows
    .map((row) => {
      const item = row as Dict;
      const id = typeof item.id === 'number' ? item.id : Number(item.id);
      const name = String(item.name || '');
      if (!id || Number.isNaN(id) || !name) return null;
      return { id, name };
    })
    .filter((row): row is { id: number; name: string } => Boolean(row));
}

export function resolveAssigneeLoadSuccessState(options: {
  selectedAssigneeId: number | null;
  assigneeOptions: Array<{ id: number; name: string }>;
}): {
  assigneeOptions: Array<{ id: number; name: string }>;
  selectedAssigneeId: number | null;
} {
  return {
    assigneeOptions: options.assigneeOptions,
    selectedAssigneeId: reconcileSelectedAssigneeId({
      selectedAssigneeId: options.selectedAssigneeId,
      assigneeOptions: options.assigneeOptions,
    }),
  };
}

export function resolveAssigneeLoadFailureState(): {
  assigneeOptions: Array<{ id: number; name: string }>;
  selectedAssigneeId: null;
} {
  return {
    assigneeOptions: [],
    selectedAssigneeId: null,
  };
}

export function reconcileSelectedAssigneeId(options: {
  selectedAssigneeId: number | null;
  assigneeOptions: Array<{ id: number; name: string }>;
}): number | null {
  if (!options.selectedAssigneeId) return null;
  return options.assigneeOptions.some((opt) => opt.id === options.selectedAssigneeId)
    ? options.selectedAssigneeId
    : null;
}

export function resolveAssigneePermissionWarning(options: {
  reasonCodeRaw: unknown;
  modelRaw: unknown;
  opRaw: unknown;
}): { model: string; op: string } | null {
  const reasonCode = String(options.reasonCodeRaw || '').trim().toUpperCase();
  if (reasonCode !== 'PERMISSION_DENIED') return null;
  return {
    model: String(options.modelRaw || 'res.users').trim(),
    op: String(options.opRaw || 'list').trim().toLowerCase(),
  };
}

export function resolveAssigneePermissionWarningMessage(options: {
  warning: { model: string; op: string } | null;
  text: (key: string, fallback: string) => string;
}): string {
  if (!options.warning) return '';
  return `${options.text('batch_msg_assignee_options_limited_prefix', '负责人候选加载受限（')}${options.warning.model}/${options.warning.op}${options.text('batch_msg_assignee_options_limited_suffix', '）')}`;
}

export function resolveExportGuard(options: {
  targetModel: string;
  scope: 'selected' | 'all';
  selectedCount: number;
}): { ok: true } | { ok: false; reason: 'missing_target_model' | 'missing_selection' } {
  if (!options.targetModel) return { ok: false, reason: 'missing_target_model' };
  if (options.scope === 'selected' && options.selectedCount <= 0) {
    return { ok: false, reason: 'missing_selection' };
  }
  return { ok: true };
}

export function resolveExportGuardMessage(options: {
  reason: 'missing_target_model' | 'missing_selection';
  text: (key: string, fallback: string) => string;
}): string {
  if (options.reason === 'missing_selection') {
    return options.text('batch_msg_no_selected_records_export', '没有可导出的选中记录');
  }
  return '';
}

export function resolveExportNoContentMessage(text: (key: string, fallback: string) => string): string {
  return text('batch_msg_no_records_export', '没有可导出的记录');
}

export function resolveExportDoneMessage(options: {
  countRaw: unknown;
  text: (key: string, fallback: string) => string;
}): string {
  return `${options.text('batch_msg_export_done_prefix', '已导出 ')}${Number(options.countRaw || 0)}${options.text('batch_msg_export_done_suffix', ' 条记录')}`;
}

export function resolveExportFailedMessage(text: (key: string, fallback: string) => string): string {
  return text('batch_msg_export_failed', '批量导出失败');
}

export function buildExportRequest(options: {
  model: string;
  scope: 'selected' | 'all';
  selectedIds: number[];
  domain: unknown[];
  columns: string[];
  order: string;
  context: Dict;
}): Dict {
  const fields = options.columns.length ? ['id', ...options.columns.filter((col) => col !== 'id')] : ['id', 'name'];
  return {
    model: options.model,
    fields,
    ids: options.scope === 'selected' ? options.selectedIds : [],
    domain: options.scope === 'all' ? options.domain : [],
    order: options.order,
    limit: options.scope === 'all' ? 10000 : 5000,
    context: options.context,
  };
}

import { ApiError } from '../../api/client';
import { collectErrorContextIssue, issueScopeLabel } from '../errorContext';

export function resolveBatchActionGuard(options: {
  targetModel: string;
  selectedCount: number;
  action: 'archive' | 'activate' | 'delete';
  hasActiveField: boolean;
  deleteMode: string;
}):
  | { ok: true }
  | {
      ok: false;
      reason:
        | 'missing_target_model'
        | 'missing_selection'
        | 'active_field_required'
        | 'delete_mode_unavailable';
    } {
  if (!options.targetModel) return { ok: false, reason: 'missing_target_model' };
  if (options.selectedCount <= 0) return { ok: false, reason: 'missing_selection' };
  if (options.action !== 'delete' && !options.hasActiveField) {
    return { ok: false, reason: 'active_field_required' };
  }
  if (options.action === 'delete' && options.deleteMode !== 'unlink') {
    return { ok: false, reason: 'delete_mode_unavailable' };
  }
  return { ok: true };
}

export function resolveBatchActionGuardMessage(options: {
  reason: 'missing_target_model' | 'missing_selection' | 'active_field_required' | 'delete_mode_unavailable';
  text: (key: string, fallback: string) => string;
}): string {
  if (options.reason === 'active_field_required') {
    return options.text('batch_msg_model_no_active_field', '当前模型不支持 active 字段，无法批量归档/激活');
  }
  if (options.reason === 'delete_mode_unavailable') {
    return options.text('batch_msg_delete_mode_unavailable', '当前场景暂不支持删除，请联系管理员检查删除权限。');
  }
  return '';
}

export function resolveBatchAssignGuard(options: {
  targetModel: string;
  selectedCount: number;
  hasAssigneeField: boolean;
  assigneeId: number;
}):
  | { ok: true }
  | { ok: false; reason: 'missing_target_model' | 'missing_selection' | 'missing_assignee_field' | 'missing_assignee' } {
  if (!options.targetModel) return { ok: false, reason: 'missing_target_model' };
  if (options.selectedCount <= 0) return { ok: false, reason: 'missing_selection' };
  if (!options.hasAssigneeField) return { ok: false, reason: 'missing_assignee_field' };
  if (!options.assigneeId) return { ok: false, reason: 'missing_assignee' };
  return { ok: true };
}

export function resolveBatchAssignGuardMessage(options: {
  reason: 'missing_target_model' | 'missing_selection' | 'missing_assignee_field' | 'missing_assignee';
  text: (key: string, fallback: string) => string;
}): string {
  if (options.reason === 'missing_assignee_field') {
    return options.text('batch_msg_model_no_assignee_field', '当前模型不支持负责人字段，无法批量指派');
  }
  if (options.reason === 'missing_assignee') {
    return options.text('batch_msg_select_assignee_first', '请先选择负责人');
  }
  return '';
}

export function buildBatchUpdateRequest(options: {
  model: string;
  ids: number[];
  action: 'archive' | 'activate' | 'assign';
  assigneeId?: number;
  ifMatchMap: Record<number, string>;
  idempotencyKey: string;
  context: Record<string, unknown>;
}): Record<string, unknown> {
  return {
    model: options.model,
    ids: options.ids,
    action: options.action,
    assigneeId: options.assigneeId,
    ifMatchMap: options.ifMatchMap,
    idempotencyKey: options.idempotencyKey,
    failedPreviewLimit: 12,
    failedOffset: 0,
    failedLimit: 12,
    exportFailedCsv: true,
    context: options.context,
  };
}

export function resolveBatchActionResultMessage(options: {
  action: 'archive' | 'activate' | 'delete';
  idempotentReplay: boolean;
  succeeded: number;
  failed: number;
  text: (key: string, fallback: string) => string;
}): string {
  if (options.idempotentReplay) {
    return options.text('batch_msg_idempotent_replay', '批量操作已幂等处理（重复请求被忽略）');
  }
  if (options.action === 'delete') {
    return `${options.text('batch_msg_delete_done_prefix', '批量删除完成：成功 ')}${options.succeeded}${options.text('batch_msg_done_middle', '，失败 ')}${options.failed}`;
  }
  if (options.action === 'activate') {
    return `${options.text('batch_msg_activate_done_prefix', '批量激活完成：成功 ')}${options.succeeded}${options.text('batch_msg_done_middle', '，失败 ')}${options.failed}`;
  }
  return `${options.text('batch_msg_archive_done_prefix', '批量归档完成：成功 ')}${options.succeeded}${options.text('batch_msg_done_middle', '，失败 ')}${options.failed}`;
}

export function resolveBatchActionFailureMessage(options: {
  action: 'archive' | 'activate' | 'delete' | 'assign';
  text: (key: string, fallback: string) => string;
  assigneeName?: string;
  idempotentReplay?: boolean;
  succeeded?: number;
  failed?: number;
}): string {
  if (options.action === 'assign') {
    const assignee = options.assigneeName || '';
    if (options.idempotentReplay) {
      return `${options.text('batch_msg_assign_idempotent_prefix', '批量指派给 ')}${assignee}${options.text('batch_msg_assign_idempotent_suffix', ' 已幂等处理（重复请求被忽略）')}`;
    }
    return `${options.text('batch_msg_assign_done_prefix', '批量指派给 ')}${assignee}${options.text('batch_msg_assign_done_middle', '：成功 ')}${options.succeeded || 0}${options.text('batch_msg_done_middle', '，失败 ')}${options.failed || 0}`;
  }
  return options.action === 'activate'
    ? options.text('batch_msg_activate_failed', '批量激活失败')
    : options.action === 'archive'
      ? options.text('batch_msg_archive_failed', '批量归档失败')
      : options.text('batch_msg_delete_failed', '批量删除失败');
}

export function resolveBatchActionErrorLabel(options: {
  action: 'archive' | 'activate' | 'delete';
  text: (key: string, fallback: string) => string;
}): string {
  if (options.action === 'activate') return options.text('batch_label_activate', '批量激活');
  if (options.action === 'archive') return options.text('batch_label_archive', '批量归档');
  return options.text('batch_label_delete', '批量删除');
}

export function buildBatchErrorLine(options: {
  err: unknown;
  fallback: { model: string; op: string; label: string };
  text: (key: string, fallback: string) => string;
  resolveHint: (input: { suggestedAction: string; reasonCode: string; retryable: boolean | undefined }) => string;
}): string {
  const issueCounter = new Map<string, { model: string; op: string; reasonCode: string; count: number }>();
  const issue = collectErrorContextIssue(issueCounter, options.err, { model: options.fallback.model, op: options.fallback.op });
  const scope = issueScopeLabel(issue);
  const reasonText = issue.reasonCode ? `${options.text('batch_error_reason_prefix', '原因=')}${issue.reasonCode}` : '';
  if (!(options.err instanceof ApiError)) {
    return [
      options.fallback.label,
      scope ? `${options.text('batch_error_scope_prefix', '范围=')}${scope}` : '',
      reasonText,
    ].filter(Boolean).join(' | ');
  }
  const hint = options.resolveHint({
    suggestedAction: options.err.suggestedAction,
    reasonCode: options.err.reasonCode,
    retryable: options.err.retryable,
  });
  return [
    options.fallback.label,
    scope ? `${options.text('batch_error_scope_prefix', '范围=')}${scope}` : '',
    reasonText,
    hint,
  ].filter(Boolean).join(' | ');
}

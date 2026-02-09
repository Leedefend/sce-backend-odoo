import type { ExecuteButtonResponse, ViewButton } from '@sc/schema';

const EXACT_LABELS: Record<string, string> = {
  action_submit: '提交',
  action_confirm: '确认',
  action_approve: '审批',
  action_reject: '退回',
  action_cancel: '取消',
  action_done: '完成',
  action_complete: '完成',
  action_set_approved: '批准',
  action_reset_draft: '回到草稿',
  action_archive: '归档',
  action_unarchive: '恢复',
  action_activate: '激活',
  action_deactivate: '停用',
};

function toTitleWords(value: string) {
  return value
    .replace(/^action_/, '')
    .replace(/^btn_/, '')
    .replace(/_/g, ' ')
    .trim()
    .replace(/\s+/g, ' ');
}

function inferLabelFromName(name: string) {
  if (!name) return '';
  const key = String(name).trim();
  if (EXACT_LABELS[key]) return EXACT_LABELS[key];
  if (key.includes('submit')) return '提交';
  if (key.includes('approve')) return '审批';
  if (key.includes('reject')) return '退回';
  if (key.includes('confirm')) return '确认';
  if (key.includes('cancel')) return '取消';
  if (key.includes('done') || key.includes('complete')) return '完成';
  if (key.includes('archive')) return '归档';
  if (key.includes('active')) return '激活';
  return toTitleWords(key) || key;
}

function isTechnicalLabel(value: string) {
  if (!value) return true;
  return value.includes('_') || value.startsWith('action.');
}

export function semanticButtonLabel(btn: ViewButton) {
  const text = String(btn?.string || '').trim();
  if (text && !isTechnicalLabel(text)) {
    return text;
  }
  return inferLabelFromName(String(btn?.name || '')) || text || '操作';
}

export function parseExecuteResult(response: ExecuteButtonResponse | null | undefined) {
  const result = (response?.result || {}) as Record<string, unknown>;
  const effect = (response?.effect || {}) as Record<string, unknown>;
  const reasonCode = String(result.reason_code || 'OK');
  const status = String(result.status || '').toLowerCase();
  const success =
    typeof result.success === 'boolean'
      ? Boolean(result.success)
      : status
        ? status === 'success'
        : reasonCode === 'OK' || reasonCode === 'DRY_RUN';
  const message =
    String(result.message || effect.message || '') ||
    defaultMessage(reasonCode, success);
  return { message, reasonCode, success };
}

function defaultMessage(reasonCode: string, success: boolean) {
  if (success) return '操作成功';
  if (reasonCode === 'PERMISSION_DENIED') return '无权限执行该操作';
  if (reasonCode === 'NOT_FOUND') return '记录不存在或已删除';
  if (reasonCode === 'BUSINESS_RULE_FAILED') return '当前状态不允许此操作';
  if (reasonCode === 'MISSING_PARAMS') return '操作参数不完整';
  return '操作失败';
}

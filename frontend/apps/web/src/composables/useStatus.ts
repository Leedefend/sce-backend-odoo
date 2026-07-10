import { ref } from 'vue';
import { ApiError } from '../api/client';
import { describeSuggestedAction } from './useSuggestedAction';

export interface StatusError {
  message?: string;
  code?: number | string;
  traceId?: string;
  hint?: string;
  kind?: string;
  errorCategory?: string;
  retryable?: boolean;
  reasonCode?: string;
  suggestedAction?: string;
  details?: Record<string, unknown>;
}

export interface StatusCopy {
  title: string;
  message: string;
  hint?: string;
}

export function resolveSuggestedAction(
  suggestedAction?: string,
  reasonCode?: string,
  retryable?: boolean,
): string {
  const hintByAction = describeSuggestedAction(suggestedAction).hint;
  if (hintByAction) return hintByAction;

  const code = String(reasonCode || '').toUpperCase();
  if (code.includes('PERMISSION') || code.includes('FORBIDDEN')) return '请核对当前角色权限，必要时联系管理员处理。';
  if (code.includes('NOT_FOUND')) return '请刷新列表，记录可能已被删除或当前不可见。';
  if (code.includes('CONFLICT')) return '请重新加载最新数据后再尝试。';
  if (code.includes('NETWORK')) return '请检查网络连接后再尝试。';

  if (retryable === true) return '该失败可重试，请立即重试或稍后再试。';
  if (retryable === false) return '该失败不可直接重试，请先处理数据或权限问题。';
  return '';
}

export function buildStatusError(err: unknown, fallbackMessage: string, kind?: string): StatusError {
  if (err instanceof ApiError) {
    const code = err.status;
    const suggestedAction = err.suggestedAction || resolveSuggestedAction(undefined, err.reasonCode, err.retryable);
    return {
      message: err.message,
      code,
      traceId: err.traceId,
      hint: err.hint || getHint(code, err.kind, err.errorCategory, err.retryable),
      kind: kind || err.kind,
      errorCategory: err.errorCategory,
      retryable: err.retryable,
      reasonCode: err.reasonCode,
      suggestedAction: suggestedAction || undefined,
      details: err.details,
    };
  }
  const message = err instanceof Error ? err.message : fallbackMessage;
  return { message, kind };
}

function normalizeCode(code?: number | string) {
  if (typeof code === 'number') return code;
  if (typeof code === 'string') {
    const parsed = Number(code);
    return Number.isNaN(parsed) ? undefined : parsed;
  }
  return undefined;
}

function normalizeCategory(category?: string): string {
  return String(category || '')
    .trim()
    .toLowerCase();
}

function mergeHint(...parts: Array<string | undefined>): string | undefined {
  const text = parts
    .map((part) => String(part || '').trim())
    .filter(Boolean)
    .join(' ');
  return text || undefined;
}

function errorContextHint(err?: StatusError | null): string {
  const model = String(err?.details?.model || '').trim();
  const op = String(err?.details?.op || '').trim().toLowerCase();
  const reasonCode = String(err?.reasonCode || '').trim().toUpperCase();
  const scope = [model, op].filter(Boolean).join('/');
  if (!scope && !reasonCode) return '';
  if (scope && reasonCode) return `上下文：${scope} [${reasonCode}]。`;
  if (scope) return `上下文：${scope}。`;
  return `上下文：[${reasonCode}]。`;
}

function getHint(code?: number | string, kind?: string, errorCategory?: string, retryable?: boolean): string {
  const numericCode = normalizeCode(code);
  const category = normalizeCategory(errorCategory);
  if (category === 'auth') return '登录状态可能已失效，请重新登录。';
  if (category === 'permission') return '当前访问受限，请核对角色或功能权限后再尝试。';
  if (category === 'validation') return '提交参数不符合要求，请修正后再尝试。';
  if (category === 'conflict') return '服务端数据已变化，请加载最新数据后再尝试。';
  if (category === 'business') return '当前操作被业务规则阻止，请先处理阻塞项。';
  if (category === 'system') return '系统服务处理异常，请稍后重试或联系管理员。';
  if (retryable === true) return '该失败可重试，请立即重试或稍后再试。';
  if (retryable === false) return '该失败不可直接重试，请先处理数据或权限问题。';
  if (kind === 'network' || numericCode === 0) return '请检查网络连接和服务可用状态。';
  if (numericCode === 401) return '登录已过期，请重新登录。';
  if (numericCode === 403) return '请核对当前角色的访问权限。';
  if (numericCode === 404) return '资源不存在或当前用户不可见。';
  if (numericCode === 409) return '记录已被更新，请刷新后再尝试。';
  if (numericCode && numericCode >= 500) return '系统服务异常，请稍后重试或联系管理员。';
  return '';
}

export function resolveErrorCopy(err: StatusError | null, fallbackMessage = '请求处理失败'): StatusCopy {
  const code = normalizeCode(err?.code);
  const category = normalizeCategory(err?.errorCategory);
  const hint = err?.hint || getHint(err?.code, err?.kind, err?.errorCategory, err?.retryable);
  const contextHint = errorContextHint(err);
  if (category === 'auth') {
    return {
      title: '需要重新登录',
      message: '当前登录状态无法完成该操作。',
      hint: mergeHint(hint, contextHint),
    };
  }
  if (category === 'permission') {
    return {
      title: '权限不足',
      message: '当前角色不能执行该操作。',
      hint: mergeHint(hint, contextHint),
    };
  }
  if (category === 'validation') {
    return {
      title: '参数不符合要求',
      message: '提交内容未通过系统校验。',
      hint: mergeHint(hint, contextHint),
    };
  }
  if (category === 'conflict') {
    return {
      title: '数据已变化',
      message: '当前数据不是最新版本，请刷新后再试。',
      hint: mergeHint(hint, contextHint),
    };
  }
  if (category === 'business') {
    return {
      title: '业务规则阻止',
      message: '当前操作不满足业务规则要求。',
      hint: mergeHint(hint, contextHint),
    };
  }
  if (category === 'system') {
    return {
      title: '系统处理异常',
      message: '系统服务未能完成本次请求。',
      hint: mergeHint(hint, contextHint),
    };
  }
  if (err?.kind === 'network' || code === 0) {
    return {
      title: '网络连接异常',
      message: '暂时无法连接系统服务，请检查网络或服务状态。',
      hint: mergeHint(hint, contextHint),
    };
  }
  if (code === 401) {
    return {
      title: '需要重新登录',
      message: '登录状态已失效，请重新登录。',
      hint: mergeHint(hint, contextHint),
    };
  }
  if (code === 403) {
    return {
      title: '权限不足',
      message: '当前账号没有执行该操作的权限。',
      hint: mergeHint(hint, contextHint),
    };
  }
  if (code === 404) {
    return {
      title: '资源不可用',
      message: '请求的资源不存在或已不可访问。',
      hint: mergeHint(hint, contextHint),
    };
  }
  if (code === 409) {
    return {
      title: '数据已变化',
      message: '记录已被其他操作更新，请刷新后再试。',
      hint: mergeHint(hint, contextHint),
    };
  }
  if (code && code >= 500) {
    return {
      title: '系统处理异常',
      message: '系统服务未能完成本次请求，请稍后重试。',
      hint: mergeHint(hint, contextHint),
    };
  }
  return {
    title: '请求处理失败',
    message: err?.message || fallbackMessage,
    hint: mergeHint(hint, contextHint),
  };
}

export function resolveEmptyCopy(type: 'list' | 'card' | 'record' | 'my_work' = 'list'): StatusCopy {
  if (type === 'record') {
    return { title: '暂无数据', message: '记录不存在或当前账号不可查看。' };
  }
  if (type === 'my_work') {
    return { title: '暂无工作事项', message: '当前分区没有待处理事项。' };
  }
  if (type === 'card') {
    return { title: '暂无数据', message: '当前操作没有返回卡片数据。' };
  }
  return { title: '暂无数据', message: '当前操作没有返回记录。' };
}

export function useStatus() {
  const error = ref<StatusError | null>(null);

  function clearError() {
    error.value = null;
  }

  function setError(err: unknown, fallbackMessage: string, kind?: string) {
    error.value = buildStatusError(err, fallbackMessage, kind);
  }

  return { error, clearError, setError };
}

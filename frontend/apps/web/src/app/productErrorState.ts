export type ProductErrorState = {
  title: string;
  message: string;
  actionLabel: string;
  kind: 'session' | 'permission' | 'missing' | 'conflict' | 'validation' | 'network' | 'server' | 'unknown';
};

const TECHNICAL_TEXT = /(traceback|python\s+exception|sql(?:state)?|odoo\.[a-z_]+|token\s*[:=]|https?:\/\/(?:localhost|127\.0\.0\.1|\d{1,3}(?:\.\d{1,3}){3})|<\/?(?:html|body|pre|script)\b)/i;

function safeMessage(value: unknown, fallback: string): string {
  const text = String(value || '').replace(/\s+/g, ' ').trim();
  if (!text || TECHNICAL_TEXT.test(text)) return fallback;
  return text.slice(0, 320);
}

export function resolveProductErrorState(input: {
  status?: number | string | null;
  message?: string;
  reasonCode?: string;
}): ProductErrorState {
  const hasStatus = input.status !== undefined && input.status !== null && String(input.status).trim() !== '';
  const status = Number(input.status || 0);
  const reason = String(input.reasonCode || '').trim().toUpperCase();
  const rawMessage = String(input.message || '');
  if (status === 401 || /SESSION|TOKEN.*EXPIRED/.test(reason)) return {
    kind: 'session', title: '登录已失效', message: '为保护业务数据，请重新登录后继续。', actionLabel: '重新登录',
  };
  if (status === 403 || /PERMISSION|FORBIDDEN|ACCESS_DENIED/.test(reason)) return {
    kind: 'permission', title: '无权访问', message: '当前账号无权访问此内容，请返回已授权的工作区。', actionLabel: '返回安全页面',
  };
  if (status === 404 || /NOT_FOUND|MISSING_RECORD/.test(reason)) return {
    kind: 'missing', title: '记录不存在', message: '该记录可能已被删除，或链接已经失效。', actionLabel: '返回安全页面',
  };
  if (status === 409 || /CONFLICT|STALE|VERSION/.test(reason)) return {
    kind: 'conflict', title: '数据已发生变化', message: '其他操作已更新这条数据，请获取最新版本后继续。', actionLabel: '获取最新数据',
  };
  if (status === 422 || /VALIDATION|BUSINESS_RULE/.test(reason)) return {
    kind: 'validation', title: '请检查业务信息', message: safeMessage(input.message, '部分内容不符合业务要求，请检查后重试。'), actionLabel: '返回修改',
  };
  if ((hasStatus && status === 0) || /NETWORK|TIMEOUT|FETCH/.test(reason) || /network|timeout|failed to fetch/i.test(rawMessage)) return {
    kind: 'network', title: '网络连接异常', message: '暂时无法连接服务，请检查网络后重试。', actionLabel: '重试',
  };
  if (status >= 500) return {
    kind: 'server', title: '服务暂时不可用', message: '服务当前无法完成请求，请稍后重试。', actionLabel: '重试',
  };
  return {
    kind: 'unknown', title: '操作未完成', message: safeMessage(input.message, '请求未能完成，请重试或返回安全页面。'), actionLabel: '重试',
  };
}

export type SemanticTone = 'neutral' | 'success' | 'warning' | 'danger' | 'info';

type SemanticCell = {
  text: string;
  tone: SemanticTone;
};

const STATUS_TEXT: Record<string, string> = {
  draft: '草稿',
  done: '已完成',
  cancelled: '已取消',
  cancel: '已取消',
  open: '进行中',
  active: '进行中',
  archived: '已归档',
  pending: '待处理',
  blocked: '受阻',
  overdue: '逾期',
  rejected: '已驳回',
  approved: '已审批',
  paid: '已支付',
  unpaid: '未支付',
  new: '新建',
  in_progress: '进行中',
  '01_in_progress': '进行中',
  to_do: '待处理',
  todo: '待处理',
  normal: '正常',
  risk: '风险',
  warning: '预警',
  high_risk: '高风险',
};

export function statusTone(value: unknown): SemanticTone {
  const raw = String(value || '').trim().toLowerCase();
  if (!raw) return 'neutral';
  if (['done', 'approved', 'paid', 'completed', 'normal'].includes(raw)) return 'success';
  if (['warning', 'pending', 'unpaid', 'to_do', 'todo'].includes(raw)) return 'warning';
  if (['high_risk', 'risk', 'blocked', 'overdue', 'cancel', 'cancelled', 'rejected'].includes(raw)) return 'danger';
  if (['open', 'active', 'in_progress', '01_in_progress'].includes(raw)) return 'info';
  return 'neutral';
}

export function semanticStatus(value: unknown): SemanticCell {
  const normalizedValue = Array.isArray(value)
    ? (value.length > 1 ? value[1] : value[0])
    : value;
  const raw = String(normalizedValue ?? '').trim();
  if (!raw) return { text: '--', tone: 'neutral' };
  const key = raw.toLowerCase();
  if (raw.includes('风险') || raw.includes('逾期') || raw.includes('异常')) {
    return { text: raw, tone: 'danger' };
  }
  if (raw.includes('预警')) {
    return { text: raw, tone: 'warning' };
  }
  if (raw.includes('完成') || raw.includes('归档')) {
    return { text: raw, tone: 'success' };
  }
  return {
    text: STATUS_TEXT[key] || raw,
    tone: statusTone(raw),
  };
}

export function semanticBoolean(value: unknown): string {
  if (value === true || value === 1 || String(value).toLowerCase() === 'true') return '是';
  if (value === false || value === 0 || String(value).toLowerCase() === 'false') return '否';
  return '--';
}

export function formatAmountCN(value: unknown): string {
  const amount = Number(value || 0);
  if (!Number.isFinite(amount)) return '--';
  const abs = Math.abs(amount);
  if (abs >= 100000000) return `${(amount / 100000000).toFixed(2)}亿`;
  if (abs >= 10000) return `${(amount / 10000).toFixed(2)}万`;
  return `${amount.toFixed(2)}`;
}

export function semanticValueByField(field: string, value: unknown): SemanticCell {
  const key = String(field || '').trim().toLowerCase();
  if (key.includes('state') || key.includes('status') || key.includes('stage')) {
    return semanticStatus(value);
  }
  if (key.startsWith('is_') || key.startsWith('has_') || typeof value === 'boolean') {
    return { text: semanticBoolean(value), tone: 'neutral' };
  }
  if (key.includes('amount') || key.includes('total') || key.includes('cost') || key.includes('revenue')) {
    const amount = Number(value);
    if (Number.isFinite(amount)) {
      return { text: formatAmountCN(amount), tone: amount < 0 ? 'danger' : 'neutral' };
    }
  }
  if (key.includes('percent') || key.endsWith('_rate')) {
    const num = Number(value);
    if (Number.isFinite(num)) {
      return { text: `${Math.round(num)}%`, tone: num < 50 ? 'warning' : 'success' };
    }
  }
  if (Array.isArray(value)) {
    if (value.length > 1 && value[1] !== null && value[1] !== undefined) {
      return { text: String(value[1]), tone: 'neutral' };
    }
    if (value.length) {
      return { text: String(value[0]), tone: 'neutral' };
    }
  }
  if (value === null || value === undefined || value === '') {
    return { text: '--', tone: 'neutral' };
  }
  return { text: String(value), tone: 'neutral' };
}

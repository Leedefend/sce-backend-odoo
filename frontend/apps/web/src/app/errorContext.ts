import { ApiError } from '../api/client';

export type ErrorContextIssue = {
  model: string;
  op: string;
  reasonCode: string;
  count: number;
};

function normalizeModel(model: unknown, fallback = '') {
  return String(model || fallback || '').trim();
}

function normalizeOp(op: unknown, fallback = '') {
  return String(op || fallback || '').trim().toLowerCase();
}

function normalizeReasonCode(reasonCode: unknown) {
  return String(reasonCode || '').trim().toUpperCase() || 'UNKNOWN';
}

export function issueCounterKey(issue: Pick<ErrorContextIssue, 'model' | 'op' | 'reasonCode'>) {
  return `${issue.model}|${issue.op}|${issue.reasonCode}`;
}

export function collectErrorContextIssue(
  counter: Map<string, ErrorContextIssue>,
  error: unknown,
  fallback: { model?: string; op?: string } = {},
) {
  const modelFallback = normalizeModel(fallback.model);
  const opFallback = normalizeOp(fallback.op);
  const issue: ErrorContextIssue = {
    model: modelFallback,
    op: opFallback,
    reasonCode: 'UNKNOWN',
    count: 1,
  };
  if (error instanceof ApiError) {
    issue.model = normalizeModel(error.details?.model, modelFallback);
    issue.op = normalizeOp(error.details?.op, opFallback);
    issue.reasonCode = normalizeReasonCode(error.reasonCode);
  }
  const key = issueCounterKey(issue);
  const current = counter.get(key);
  if (current) {
    current.count += 1;
    counter.set(key, current);
    return current;
  }
  counter.set(key, issue);
  return issue;
}

export function summarizeErrorContextIssues(counter: Map<string, ErrorContextIssue>, maxItems = 3) {
  return Array.from(counter.values())
    .sort((a, b) => b.count - a.count || a.model.localeCompare(b.model))
    .slice(0, Math.max(1, maxItems));
}

export function issueScopeLabel(issue: Pick<ErrorContextIssue, 'model' | 'op'>) {
  return [String(issue.model || '').trim(), String(issue.op || '').trim().toLowerCase()]
    .filter(Boolean)
    .join('/');
}

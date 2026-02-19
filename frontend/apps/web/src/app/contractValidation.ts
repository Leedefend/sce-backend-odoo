import type { ActionContract } from '@sc/schema';

type ValidationIssue = {
  code: string;
  message: string;
};

function isEmpty(value: unknown) {
  if (value === null || value === undefined) return true;
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'string') return value.trim() === '';
  return false;
}

function toComparableDate(value: unknown): number | null {
  if (value === null || value === undefined) return null;
  if (typeof value === 'string') {
    const ts = Date.parse(value);
    return Number.isFinite(ts) ? ts : null;
  }
  if (value instanceof Date) {
    const ts = value.getTime();
    return Number.isFinite(ts) ? ts : null;
  }
  return null;
}

export function validateContractFormData(params: {
  contract: ActionContract | null;
  fieldLabels: Record<string, string>;
  values: Record<string, unknown>;
}): ValidationIssue[] {
  const { contract, fieldLabels, values } = params;
  if (!contract) return [];
  const issues: ValidationIssue[] = [];

  Object.entries(contract.fields || {}).forEach(([name, descriptor]) => {
    if (!descriptor?.required) return;
    if (isEmpty(values[name])) {
      issues.push({
        code: 'REQUIRED',
        message: `必填项未填写: ${fieldLabels[name] || name}`,
      });
    }
  });

  const validator = contract.validator as Record<string, unknown> | undefined;
  const recordRules = validator?.record_rules as Record<string, unknown> | undefined;
  const uniqueRules = Array.isArray(recordRules?.unique) ? (recordRules?.unique as Array<Record<string, unknown>>) : [];
  uniqueRules.forEach((rule) => {
    const fields = Array.isArray(rule.fields) ? (rule.fields as string[]) : [];
    if (!fields.length) return;
    const missing = fields.find((field) => isEmpty(values[field.toLowerCase()]) && isEmpty(values[field]));
    if (!missing) return;
    issues.push({
      code: String(rule.name || 'UNIQUE_PRECHECK'),
      message: String(rule.message || `${fields.join(',')} 需要填写后才能校验唯一性`),
    });
  });

  const sqlChecks = Array.isArray(recordRules?.sql_checks) ? (recordRules?.sql_checks as Array<Record<string, unknown>>) : [];
  sqlChecks.forEach((check) => {
    const definition = String(check.definition || '').toLowerCase();
    if (!definition.includes('date') || !definition.includes('date_start')) return;
    const endTs = toComparableDate(values.date);
    const startTs = toComparableDate(values.date_start);
    if (endTs === null || startTs === null) return;
    if (endTs < startTs) {
      issues.push({
        code: String(check.name || 'SQL_CHECK'),
        message: String(check.message || '开始日期必须小于等于结束日期'),
      });
    }
  });

  return issues;
}


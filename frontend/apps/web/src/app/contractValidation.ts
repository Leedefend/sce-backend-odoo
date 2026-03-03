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
  const renderProfile = String(contract.render_profile || '').trim().toLowerCase();
  const validationRules = Array.isArray(contract.validation_rules)
    ? (contract.validation_rules as Array<Record<string, unknown>>)
    : [];
  const requiredRules = validationRules.filter((rule) => String(rule?.code || '').trim().toUpperCase() === 'REQUIRED');
  requiredRules.forEach((rule) => {
    const field = String(rule.field || '').trim();
    if (!field) return;
    const whenProfiles = Array.isArray(rule.when_profiles)
      ? rule.when_profiles.map((item) => String(item || '').trim().toLowerCase()).filter(Boolean)
      : [];
    if (whenProfiles.length && renderProfile && !whenProfiles.includes(renderProfile)) return;
    if (isEmpty(values[field])) {
      issues.push({
        code: 'REQUIRED',
        message: `必填项未填写: ${fieldLabels[field] || field}`,
      });
    }
  });

  const validator = contract.validator as Record<string, unknown> | undefined;
  const recordRules = validator?.record_rules as Record<string, unknown> | undefined;
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

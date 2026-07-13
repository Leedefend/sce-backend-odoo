export type SceneValidationPanelInput = {
  enabled: boolean;
  validationErrors: string[];
  errorCode: string;
  suggestedAction: string;
};

export type SceneValidationPanelVm = {
  code: string;
  message: string;
  hint: string;
  suggestedAction: string;
};

export type SceneValidationPrecheckInput = {
  requiredFields: string[];
  fieldLabels: Record<string, string>;
  isFieldVisible: (field: string) => boolean;
  fieldValue: (field: string) => unknown;
  isMissingValue: (value: unknown) => boolean;
  errorCode: string;
};

export function sceneValidationErrorPrefix(errorCode: string) {
  return `${errorCode}:`;
}

export function buildSceneValidationPanel(input: SceneValidationPanelInput): SceneValidationPanelVm | null {
  if (!input.enabled) return null;
  const prefix = sceneValidationErrorPrefix(input.errorCode);
  const rows = input.validationErrors
    .map((item) => String(item || '').trim())
    .filter((item) => item.startsWith(prefix));
  if (!rows.length) return null;
  const normalized = rows
    .map((item) => item.slice(prefix.length).trim())
    .filter(Boolean);
  return {
    code: input.errorCode,
    message: normalized.join('；') || '场景约束校验未通过，请补齐必填字段。',
    hint: '请补齐必填字段后重试。',
    suggestedAction: input.suggestedAction,
  };
}

export function collectSceneValidationPrecheckErrors(input: SceneValidationPrecheckInput): string[] {
  const out: string[] = [];
  for (const field of input.requiredFields) {
    if (!input.isFieldVisible(field)) continue;
    const value = input.fieldValue(field);
    if (input.isMissingValue(value)) {
      out.push(`${input.errorCode}: ${input.fieldLabels[field] || field} 为必填项`);
    }
  }
  return Array.from(new Set(out)).slice(0, 5);
}

export function strictContractGuardFromSceneReadyEntry(entry: unknown): Record<string, unknown> {
  const row = entry && typeof entry === 'object' && !Array.isArray(entry)
    ? entry as Record<string, unknown>
    : {};
  const direct = row.contract_guard;
  if (direct && typeof direct === 'object' && !Array.isArray(direct)) return direct as Record<string, unknown>;
  const meta = row.meta && typeof row.meta === 'object' && !Array.isArray(row.meta)
    ? row.meta as Record<string, unknown>
    : {};
  const nested = meta.contract_guard;
  if (nested && typeof nested === 'object' && !Array.isArray(nested)) return nested as Record<string, unknown>;
  return {};
}

export function strictContractMissingSummary(enabled: boolean, guard: Record<string, unknown>) {
  if (!enabled) return '';
  const raw = guard.missing;
  if (!Array.isArray(raw) || !raw.length) return '';
  const missing = raw.map((item) => String(item || '').trim()).filter(Boolean);
  return missing.length ? `严格模式检测到页面配置不完整：${missing.join(', ')}` : '';
}

export function strictContractDefaultsSummary(enabled: boolean, guard: Record<string, unknown>) {
  if (!enabled) return '';
  const raw = guard.defaults_applied;
  if (!Array.isArray(raw) || !raw.length) return '';
  const defaults = raw.map((item) => String(item || '').trim()).filter(Boolean);
  return defaults.length ? `系统已自动补齐：${defaults.join(', ')}` : '';
}

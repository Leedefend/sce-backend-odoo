import type { ActionContract } from '@sc/schema';
import { fieldType } from './fieldUtils';
import { isRequiredFieldEmptyByType } from './valueUtils';
import type { LayoutNode } from './types';

type SubmissionFeedback = { kind: 'success' | 'warn' | 'error'; message: string } | null;

export type SaveRecordValidationResult = {
  editableMap?: Record<string, unknown>;
  ok: boolean;
  showOne2manyErrors?: boolean;
  validationErrors?: string[];
  submissionFeedback?: SubmissionFeedback;
};

export async function validateBeforeSaveRecord(params: {
  collectPolicyValidationErrors: (submittedFields: Set<string>) => string[];
  collectSceneValidationPrecheckErrors: (fieldLabels: Record<string, string>) => string[];
  collectWritableValues: () => Record<string, unknown>;
  formData: Record<string, unknown>;
  isProjectStandardIntakeMode: boolean;
  isWritableFieldVisible: (name: string) => boolean;
  layoutNodes: LayoutNode[];
  layoutFieldLabels: () => Record<string, string>;
  normalizeFieldValue: (name: string, value: unknown) => unknown;
  one2manyIssues: string[];
  projectManagerId: unknown;
  projectName: unknown;
  recordId: number | null;
  resolvePendingInlineRelationCreates: () => Promise<string[]>;
  resolvePendingMany2manyTagCreates: () => Promise<string[]>;
  validateContractFormData: (fieldLabels: Record<string, string>, values: Record<string, unknown>) => string[];
}): Promise<SaveRecordValidationResult> {
  if (params.isProjectStandardIntakeMode) {
    const draftErrors: string[] = [];
    const projectName = String(params.projectName || '').trim();
    const managerId = Number(params.projectManagerId || 0);
    if (!projectName) draftErrors.push('请填写项目名称');
    if (!Number.isFinite(managerId) || managerId <= 0) draftErrors.push('请填写项目经理');
    if (draftErrors.length) {
      return {
        ok: false,
        validationErrors: draftErrors,
        submissionFeedback: { kind: 'warn', message: '创建失败，请检查填写内容' },
      };
    }
  }
  if (params.one2manyIssues.length) {
    return {
      ok: false,
      showOne2manyErrors: true,
      validationErrors: params.one2manyIssues.slice(0, 5),
      submissionFeedback: { kind: 'warn', message: '创建失败，请检查填写内容' },
    };
  }
  const labels = params.layoutFieldLabels();
  const scenePrecheckIssues = params.collectSceneValidationPrecheckErrors(labels);
  if (scenePrecheckIssues.length) {
    return {
      ok: false,
      showOne2manyErrors: false,
      validationErrors: scenePrecheckIssues,
      submissionFeedback: { kind: 'warn', message: '创建失败，请检查填写内容' },
    };
  }
  const relationCreateIssues = await params.resolvePendingInlineRelationCreates();
  if (relationCreateIssues.length) {
    return {
      ok: false,
      showOne2manyErrors: false,
      validationErrors: relationCreateIssues,
      submissionFeedback: { kind: 'warn', message: '创建失败，请检查填写内容' },
    };
  }
  const tagCreateIssues = await params.resolvePendingMany2manyTagCreates();
  if (tagCreateIssues.length) {
    return {
      ok: false,
      showOne2manyErrors: false,
      validationErrors: tagCreateIssues,
      submissionFeedback: { kind: 'warn', message: '创建失败，请检查填写内容' },
    };
  }
  const editableMap = params.collectWritableValues();
  if (!params.recordId) {
    const requiredIssues = collectRequiredFieldIssues({
      formData: params.formData,
      isWritableFieldVisible: params.isWritableFieldVisible,
      layoutNodes: params.layoutNodes,
      normalizeFieldValue: params.normalizeFieldValue,
      values: editableMap,
    });
    if (requiredIssues.length) {
      return {
        ok: false,
        showOne2manyErrors: false,
        validationErrors: requiredIssues,
        submissionFeedback: { kind: 'warn', message: '请先补充必填信息，再保存草稿或提交。' },
      };
    }
  }
  if (!params.isProjectStandardIntakeMode) {
    const policyIssues = params.collectPolicyValidationErrors(new Set(Object.keys(editableMap)));
    if (policyIssues.length) {
      return {
        ok: false,
        showOne2manyErrors: false,
        validationErrors: Array.from(new Set(policyIssues)).slice(0, 5),
        submissionFeedback: { kind: 'warn', message: '请先补充必填信息，再保存草稿或提交。' },
      };
    }
    const issues = params.validateContractFormData(labels, editableMap);
    if (issues.length) {
      return {
        ok: false,
        showOne2manyErrors: false,
        validationErrors: Array.from(new Set(issues)).slice(0, 5),
        submissionFeedback: { kind: 'warn', message: '请先补充必填信息，再保存草稿或提交。' },
      };
    }
  }
  return {
    editableMap,
    ok: true,
    showOne2manyErrors: false,
  };
}

export function collectRequiredFieldIssues(params: {
  formData: Record<string, unknown>;
  isWritableFieldVisible: (name: string) => boolean;
  layoutNodes: LayoutNode[];
  normalizeFieldValue: (name: string, value: unknown) => unknown;
  values: Record<string, unknown>;
}) {
  const missing = params.layoutNodes
    .filter((node) => node.kind === 'field' && !node.readonly && params.isWritableFieldVisible(node.name))
    .filter((node) => {
      const descriptor = node.descriptor;
      if (!descriptor?.required) return false;
      const value = Object.prototype.hasOwnProperty.call(params.values, node.name)
        ? params.values[node.name]
        : params.normalizeFieldValue(node.name, params.formData[node.name]);
      return isRequiredFieldEmptyByType(value, fieldType(descriptor));
    })
    .map((node) => String(node.label || node.descriptor?.string || node.name).trim())
    .filter(Boolean);
  if (!missing.length) return [];
  return [`保存前请填写：${Array.from(new Set(missing)).slice(0, 5).join('、')}`];
}

export function collectRecordSaveValues(params: {
  comparableFieldValue: (name: string, value: unknown) => unknown;
  contract: ActionContract | null;
  dirtyFieldSet: Set<string>;
  editableMap: Record<string, unknown>;
  formData: Record<string, unknown>;
  originalValues: Record<string, unknown>;
  recordId: number | null;
}) {
  return Object.entries(params.editableMap).reduce<Record<string, unknown>>((acc, [key, value]) => {
    if (!params.recordId) {
      acc[key] = value;
      return acc;
    }
    const ttype = fieldType(params.contract?.fields?.[key]);
    if (ttype === 'many2many' || ttype === 'one2many') {
      if (Array.isArray(value) && value.length) {
        acc[key] = value;
      }
      return acc;
    }
    if (!params.dirtyFieldSet.has(key)) {
      return acc;
    }
    if (params.comparableFieldValue(key, params.formData[key]) !== params.comparableFieldValue(key, params.originalValues[key])) {
      acc[key] = value;
    }
    return acc;
  }, {});
}

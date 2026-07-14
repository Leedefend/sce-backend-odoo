import type { PageBreadcrumb, PageIdentityInput } from './pageIdentity';
export { resolveRoutePageIdentity } from './pageIdentityRoute';

type BusinessMetadata = Record<string, unknown> | null | undefined;

function actionName(action: BusinessMetadata): string {
  return String(action?.ui_title || action?.scene_title || action?.menu_title || action?.name || '').trim();
}

function formPrimaryFields(contract: BusinessMetadata): unknown[] {
  const views = contract?.views && typeof contract.views === 'object' ? contract.views as Record<string, unknown> : {};
  const form = views.form && typeof views.form === 'object' ? views.form as Record<string, unknown> : {};
  const profile = form.profile && typeof form.profile === 'object' ? form.profile as Record<string, unknown> : {};
  const primaryFields = Array.isArray(profile.primary_fields) ? profile.primary_fields : [];
  return [profile.title_field, ...primaryFields].filter(Boolean);
}

export function buildContractFormPageIdentity(input: {
  action: BusinessMetadata;
  breadcrumbs?: PageBreadcrumb[];
  businessCategoryLabel?: unknown;
  contract: BusinessMetadata;
  formData: Record<string, unknown>;
  isCreate: boolean;
  isEdit: boolean;
  isProjectIntake: boolean;
  menuName?: unknown;
  modelName?: unknown;
  recordMissing: boolean;
  renderError: boolean;
  status: string;
}): PageIdentityInput {
  const head = input.contract?.head && typeof input.contract.head === 'object'
    ? input.contract.head as Record<string, unknown>
    : {};
  const businessName = input.businessCategoryLabel || head.title || actionName(input.action);
  const recordName = String(input.formData.display_name || '').trim();
  return {
    kind: input.isCreate ? 'create' : input.isEdit ? 'edit' : 'detail',
    actionName: businessName,
    menuName: input.menuName,
    modelName: input.modelName,
    modelLabel: head.model_label || input.action?.model_label,
    record: input.formData,
    recordDisplayName: recordName,
    primaryFieldNames: formPrimaryFields(input.contract),
    subtitle: input.isProjectIntake ? '填写核心信息即可完成项目立项' : recordName ? businessName || input.menuName : '',
    breadcrumbs: input.breadcrumbs,
    state: input.recordMissing ? 'not-found' : input.status === 'loading' ? 'loading' : input.status === 'error' || input.renderError ? 'error' : '',
  };
}

export function buildRecordPageIdentity(input: {
  action: BusinessMetadata;
  breadcrumbs?: PageBreadcrumb[];
  menuName?: unknown;
  modelName?: unknown;
  record: Record<string, unknown> | null;
  recordDisplayName?: unknown;
  status: string;
}): PageIdentityInput {
  return {
    kind: input.status === 'editing' || input.status === 'saving' ? 'edit' : 'detail',
    actionName: actionName(input.action),
    menuName: input.menuName,
    modelName: input.modelName,
    modelLabel: input.action?.model_label,
    record: input.record,
    recordDisplayName: input.recordDisplayName,
    subtitle: input.status === 'editing' ? '正在编辑' : actionName(input.action),
    breadcrumbs: input.breadcrumbs,
    state: input.status === 'loading' || input.status === 'idle' ? 'loading' : input.status === 'empty' ? 'not-found' : input.status === 'error' ? 'error' : '',
  };
}

export function buildActionPageIdentity(input: {
  action: BusinessMetadata;
  actionContractTitle?: unknown;
  breadcrumbs?: PageBreadcrumb[];
  legacyTitle?: unknown;
  menuName?: unknown;
  modelName?: unknown;
  status: string;
  subtitle?: unknown;
}): PageIdentityInput {
  return {
    kind: 'list',
    actionName: input.actionContractTitle || actionName(input.action) || input.legacyTitle,
    menuName: input.menuName,
    modelName: input.modelName,
    modelLabel: input.action?.model_label,
    subtitle: input.subtitle,
    breadcrumbs: input.breadcrumbs,
    state: input.status === 'ok' ? '' : input.status === 'empty' ? 'empty' : input.status === 'error' ? 'error' : 'loading',
  };
}

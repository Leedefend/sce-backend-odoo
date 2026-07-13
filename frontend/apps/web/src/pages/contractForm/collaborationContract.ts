import { dictOrEmpty } from './recordUtils';
import {
  activityFieldLabel,
  labelFromMap,
  nativeChatterActionLabel,
  normalizeLabelMap,
} from './uiLabels';
import type { NativeChatterAction } from './types';

export function resolveRuntimeCollaborationContract(
  v2RuntimeContract: unknown,
  legacyRuntimeContract: unknown,
) {
  const fromV2Store = dictOrEmpty(v2RuntimeContract);
  const fromLegacy = dictOrEmpty(legacyRuntimeContract);
  return dictOrEmpty(Object.keys(fromV2Store).length ? fromV2Store.collaboration : fromLegacy.collaboration);
}

export function resolveNativeChatterContract(formView: unknown, runtimeCollaborationContract: unknown) {
  const projected = dictOrEmpty(dictOrEmpty(formView).chatter);
  if (Object.keys(projected).length) return projected;
  return dictOrEmpty(dictOrEmpty(runtimeCollaborationContract).chatter);
}

export function resolveNativeAttachmentContract(formView: unknown, runtimeCollaborationContract: unknown) {
  const projected = dictOrEmpty(dictOrEmpty(formView).attachments);
  if (Object.keys(projected).length) return projected;
  return dictOrEmpty(dictOrEmpty(runtimeCollaborationContract).attachments);
}

export function nativeChatterActionsFromContract(
  chatter: Record<string, unknown>,
  context: { recordId: number; model: string },
): NativeChatterAction[] {
  if (!chatter || chatter.enabled !== true) return [];
  const actions = Array.isArray(chatter.actions) ? chatter.actions as Array<Record<string, unknown>> : [];
  return actions
    .map((row) => {
      const key = String(row.key || row.label || '').trim();
      const intent = String(row.intent || row.kind || key).trim().toLowerCase();
      const payload = row.payload && typeof row.payload === 'object' && !Array.isArray(row.payload)
        ? row.payload as Record<string, unknown>
        : {};
      const mode = String(payload.mode || intent || key).trim().toLowerCase();
      return {
        key,
        label: nativeChatterActionLabel(mode, row),
        intent,
        mode,
        payload,
        enabled: Boolean(context.recordId) && Boolean(context.model),
        hint: intent,
      };
    })
    .filter((row) => row.key && row.label);
}

export function nativeAttachmentContractOrNull(raw: Record<string, unknown>) {
  if (!raw || raw.enabled !== true) return null;
  return raw;
}

export function nativeAttachmentLabelsFromContract(raw: Record<string, unknown> | null | undefined) {
  return normalizeLabelMap(raw?.ui_labels);
}

export function nativeAttachmentLabel(labels: Record<string, string>, key: string, fallback: string) {
  return labelFromMap(labels, key, fallback);
}

export function nativeAttachmentMaxBytes(raw: Record<string, unknown> | null | undefined) {
  const upload = raw?.upload;
  const value = upload && typeof upload === 'object' && !Array.isArray(upload)
    ? Number((upload as Record<string, unknown>).max_bytes || 0)
    : 0;
  return Number.isFinite(value) && value > 0 ? value : 5 * 1024 * 1024;
}

export function nativeActivityFieldLabel(
  action: NativeChatterAction | null | undefined,
  name: string,
  fallback: string,
) {
  return activityFieldLabel(action?.payload, name, fallback);
}

export function nativeCollaborationUnavailableMessage(params: {
  recordId: number;
  model: string;
  renderProfile: string;
  hasAttachments: boolean;
}) {
  if (params.recordId && params.model) return '';
  if (params.renderProfile === 'create') {
    return params.hasAttachments
      ? '保存草稿或提交生成单据后，可记录沟通、记录备注和安排计划；附件会随保存草稿或提交一起上传。'
      : '保存草稿或提交生成单据后，可记录沟通、记录备注和安排计划。';
  }
  return '当前记录尚未加载完成，暂不能写入协作日志。';
}

export function activeChatterSubmitLabel(mode: string, activityLabel: string) {
  if (mode === 'activity') return String(activityLabel || '').trim() || '安排计划';
  if (mode === 'note') return '记录备注';
  return '记录沟通';
}

export function activeChatterPostingLabel(mode: string) {
  return mode === 'activity' ? '安排中...' : '发布中...';
}

export function activeChatterPlaceholder(mode: string) {
  return mode === 'note' ? '输入备注内容' : '输入沟通内容';
}

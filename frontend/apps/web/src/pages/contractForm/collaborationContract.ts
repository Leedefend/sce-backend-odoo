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

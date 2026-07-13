import { reactive } from 'vue';
import type { LowCodeFieldCreateDialogState } from './LowCodeFieldCreateDialog.vue';

type LowCodeFieldCreateType = LowCodeFieldCreateDialogState['ttype'];

export type LowCodeFieldCreatePayload = {
  label: string;
  ttype: LowCodeFieldCreateType;
  groupTitle: string;
  sequence: number;
};

export function useLowCodeFieldCreateRuntime(params: {
  busy: () => boolean;
  selectedFieldKey: () => string;
  selectedGroupTitle: () => string;
  firstGroupTitle: () => string;
  fieldOrderLength: () => number;
  fieldSequence: (fieldKey: string, fallback?: number) => number;
  submit: (payload: LowCodeFieldCreatePayload) => Promise<boolean | void>;
}) {
  const dialog = reactive<LowCodeFieldCreateDialogState>({
    open: false,
    afterFieldKey: '',
    groupTitle: '',
    sequence: 100,
    label: '',
    ttype: 'char',
  });

  function fallbackSequence() {
    const length = params.fieldOrderLength();
    return length ? (length + 1) * 10 : 100;
  }

  function openInlineCustomFieldCreate(groupTitle: string, afterFieldKey = '') {
    dialog.open = true;
    dialog.afterFieldKey = afterFieldKey;
    dialog.groupTitle = String(groupTitle || '').trim() || '业务配置字段';
    dialog.sequence = params.fieldSequence(afterFieldKey, fallbackSequence()) + 5;
    dialog.label = '';
    dialog.ttype = 'char';
  }

  function openCentralCustomFieldCreate() {
    openInlineCustomFieldCreate(
      params.selectedGroupTitle() || params.firstGroupTitle() || '业务配置字段',
      params.selectedFieldKey(),
    );
  }

  function onContractInlineFieldAddAfter(payload: { field: { name?: unknown }; groupTitle: string }) {
    openInlineCustomFieldCreate(payload.groupTitle || '业务配置字段', String(payload.field.name || '').trim());
  }

  function onContractInlineGroupAddField(payload: { groupTitle: string }) {
    openInlineCustomFieldCreate(payload.groupTitle || '业务配置字段');
  }

  function closeInlineCustomFieldCreate() {
    dialog.open = false;
  }

  function setFieldCreateLabel(label: string) {
    dialog.label = label;
  }

  function setFieldCreateType(ttype: LowCodeFieldCreateType) {
    dialog.ttype = ttype || 'char';
  }

  async function submitInlineCustomFieldCreate() {
    const label = String(dialog.label || '').trim();
    if (!label || params.busy()) return;
    const succeeded = await params.submit({
      label,
      ttype: dialog.ttype || 'char',
      groupTitle: dialog.groupTitle || '业务配置字段',
      sequence: dialog.sequence || 100,
    });
    if (succeeded !== false) closeInlineCustomFieldCreate();
  }

  return {
    lowCodeFieldCreateDialog: dialog,
    openCentralCustomFieldCreate,
    openInlineCustomFieldCreate,
    onContractInlineFieldAddAfter,
    onContractInlineGroupAddField,
    closeInlineCustomFieldCreate,
    setFieldCreateLabel,
    setFieldCreateType,
    submitInlineCustomFieldCreate,
  };
}

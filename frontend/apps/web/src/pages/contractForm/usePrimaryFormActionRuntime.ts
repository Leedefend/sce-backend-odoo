import { nextTick, type Ref } from 'vue';
import { executeButton } from '../../api/executeButton';
import { sanitizeUiErrorMessage } from './fieldUtils';
import type { BusyKind, ContractAction, SubmissionFeedback } from './types';

export function usePrimaryFormActionRuntime(params: {
  actionId: () => number;
  applyProjectionRefreshPolicy: (policy?: ContractAction['refreshPolicy']) => Promise<void>;
  busyKind: Ref<BusyKind>;
  confirmActionSafety: (action: ContractAction) => Promise<boolean>;
  errorMessage: Ref<string>;
  modelName: () => string;
  navigateActionResponseResult: (result: unknown) => Promise<boolean>;
  primaryCreateFooterAction: () => ContractAction | null;
  primarySubmitAction: () => ContractAction | null;
  recordId: Ref<number>;
  reload: () => Promise<void>;
  routeMenuId: () => unknown;
  saveRecord: (refreshPolicy?: ContractAction['refreshPolicy']) => Promise<boolean | number>;
  status: Ref<string>;
  submissionFeedback: Ref<SubmissionFeedback>;
  validationErrors: Ref<string[]>;
}) {
  async function executePrimarySubmitAction(action: ContractAction, resId: number) {
    if (!await params.confirmActionSafety(action)) return;
    params.busyKind.value = 'action';
    try {
      const response = await executeButton({
        model: action.targetModel || params.modelName(),
        res_id: resId,
        button: { name: action.methodName, type: action.kind === 'server' ? 'server' : 'object' },
        context: action.context,
        meta: {
          menu_id: Number(params.routeMenuId() || 0) || undefined,
          action_id: params.actionId() || undefined,
        },
      });
      const result = response?.result;
      if (await params.navigateActionResponseResult(result)) {
        return;
      }
      params.submissionFeedback.value = { kind: 'success', message: '提交成功' };
      await params.applyProjectionRefreshPolicy(action.refreshPolicy || { on_success: ['scene_projection'] });
      await params.reload();
    } catch (err) {
      const message = sanitizeUiErrorMessage(err instanceof Error ? err.message : err, '提交失败，请检查填写内容');
      params.validationErrors.value = [message];
      params.submissionFeedback.value = { kind: 'error', message: '提交失败，请检查填写内容' };
      params.status.value = 'error';
    } finally {
      params.busyKind.value = null;
    }
  }

  async function runPrimaryFormAction() {
    const footerAction = params.primaryCreateFooterAction();
    if (footerAction) {
      const saved = await params.saveRecord(footerAction.refreshPolicy);
      if (!saved) return;
      await nextTick();
      const submittedRecordId = typeof saved === 'number' ? saved : params.recordId.value;
      if (!submittedRecordId) {
        params.errorMessage.value = '操作失败：请先保存记录后再执行';
        params.status.value = 'error';
        return;
      }
      await executePrimarySubmitAction({
        ...footerAction,
        enabled: true,
        hint: '',
      }, submittedRecordId);
      return;
    }
    const submitAction = params.primarySubmitAction();
    if (!submitAction) {
      await params.saveRecord();
      return;
    }
    const saved = await params.saveRecord(submitAction.refreshPolicy);
    if (!saved) return;
    await nextTick();
    const submittedRecordId = typeof saved === 'number' ? saved : params.recordId.value;
    if (!submittedRecordId) {
      params.errorMessage.value = '提交失败：请先保存记录后再提交';
      params.status.value = 'error';
      return;
    }
    await executePrimarySubmitAction({
      ...submitAction,
      enabled: true,
      hint: '',
    }, submittedRecordId);
  }

  return {
    executePrimarySubmitAction,
    runPrimaryFormAction,
  };
}

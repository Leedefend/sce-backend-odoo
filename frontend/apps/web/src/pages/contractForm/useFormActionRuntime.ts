import type { Ref } from 'vue';
import type { Router, LocationQueryRaw } from 'vue-router';
import { executeButton } from '../../api/executeButton';
import { pickContractNavQuery } from '../../app/navigationContext';
import type { BusyKind, ContractAction } from './types';

type SubmissionFeedback = { kind: 'success' | 'warn' | 'error'; message: string } | null;

type SceneMutationInput = {
  mutation: NonNullable<ContractAction['mutation']>;
  actionKey: string;
  recordId: number | null;
  model: string;
  context?: Record<string, unknown>;
  params: Record<string, unknown>;
};

export function useFormActionRuntime(params: {
  actionId: () => number;
  applyClientMode: (mode: string, toggle?: boolean) => boolean | void;
  applyProjectionRefreshPolicy: (policy?: ContractAction['refreshPolicy']) => Promise<void>;
  busyKind: Ref<BusyKind>;
  collectActionParams: (action: ContractAction) => Promise<Record<string, unknown> | null>;
  confirmActionSafety: (action: ContractAction) => Promise<boolean>;
  currentQuery: () => LocationQueryRaw;
  ensureSavedBeforeRecordAction: () => Promise<boolean>;
  errorMessage: Ref<string>;
  executeSceneMutation: (input: SceneMutationInput) => Promise<unknown>;
  modelName: () => string;
  navigateActionResponseResult: (result: unknown) => Promise<boolean>;
  recordId: () => number | null;
  reload: () => Promise<void>;
  resolveNavigationUrl: (url: string) => string;
  routeMenuId: () => unknown;
  router: Router;
  saveRecord: (refreshPolicy?: ContractAction['refreshPolicy']) => Promise<boolean | number>;
  status: Ref<string>;
  submissionFeedback: Ref<SubmissionFeedback>;
}) {
  async function runAction(action: ContractAction) {
    if (!action.enabled) return;
    if (!await params.confirmActionSafety(action)) return;
    if (action.intent === 'ui.local_mode' || action.intent === 'ui.mode' || action.clientMode) {
      params.applyClientMode(action.clientMode, true);
      return;
    }
    const actionKey = String(action.key || '').trim().toLowerCase();
    if (actionKey === 'submit_intake' || actionKey === 'save_draft') {
      await params.saveRecord(action.refreshPolicy);
      return;
    }
    if (actionKey === 'cancel' && !action.methodName) {
      await params.router.push({
        name: 'workbench',
        query: pickContractNavQuery(params.currentQuery() as Record<string, unknown>, {
          scene: undefined,
        }),
      });
      return;
    }
    if (action.kind === 'open') {
      if (action.actionId) {
        await params.router.push({
          name: 'action',
          params: { actionId: String(action.actionId) },
          query: pickContractNavQuery(params.currentQuery() as Record<string, unknown>, {
            action_id: action.actionId,
            target: action.target || undefined,
            domain_raw: action.domainRaw || undefined,
          }),
        });
        return;
      }
      if (action.url) {
        const navUrl = params.resolveNavigationUrl(action.url);
        window.open(navUrl, action.target === 'self' ? '_self' : '_blank', 'noopener,noreferrer');
        return;
      }
      params.errorMessage.value = '打开操作缺少目标页面';
      params.status.value = 'error';
      return;
    }
    if (action.mutation) {
      const actionParams = await params.collectActionParams(action);
      if (actionParams === null) return;
      params.busyKind.value = 'action';
      try {
        await params.executeSceneMutation({
          mutation: action.mutation,
          actionKey: action.key || '',
          recordId: params.recordId(),
          model: action.targetModel || params.modelName(),
          context: action.context,
          params: actionParams,
        });
        params.submissionFeedback.value = {
          kind: 'success',
          message: '操作已完成，页面数据已刷新。',
        };
        await params.applyProjectionRefreshPolicy(action.refreshPolicy);
        return;
      } catch (err) {
        params.errorMessage.value = err instanceof Error ? err.message : '场景操作执行失败';
        params.status.value = 'error';
        return;
      } finally {
        params.busyKind.value = null;
      }
    }
    const recordId = params.recordId();
    if ((action.kind === 'object' || action.kind === 'server') && action.methodName && recordId) {
      if (!await params.ensureSavedBeforeRecordAction()) return;
      params.busyKind.value = 'action';
      try {
        const response = await executeButton({
          model: action.targetModel || params.modelName(),
          res_id: recordId,
          button: { name: action.methodName, type: action.kind === 'server' ? 'server' : 'object' },
          context: action.context,
          meta: {
            menu_id: Number(params.routeMenuId() || 0) || undefined,
            action_id: params.actionId() || undefined,
          },
        });
        const result = response?.result;
        if (await params.navigateActionResponseResult(result)) {
          if (action.refreshPolicy) {
            await params.applyProjectionRefreshPolicy(action.refreshPolicy);
          }
          return;
        }
        const refresh = result?.type;
        if (refresh === 'refresh' && !action.refreshPolicy) {
          await params.reload();
          return;
        }
        if (action.refreshPolicy) {
          await params.applyProjectionRefreshPolicy(action.refreshPolicy);
        } else {
          await params.reload();
        }
        return;
      } catch (err) {
        params.errorMessage.value = err instanceof Error ? err.message : '操作执行失败';
        params.status.value = 'error';
      } finally {
        params.busyKind.value = null;
      }
    }
  }

  return {
    runAction,
  };
}

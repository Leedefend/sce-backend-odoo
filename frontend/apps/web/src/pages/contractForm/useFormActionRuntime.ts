import type { Ref } from 'vue';
import type { Router, LocationQueryRaw } from 'vue-router';
import { executeButton } from '../../api/executeButton';
import { pickContractNavQuery } from '../../app/navigationContext';
import { buildFormActionExecutionPlan } from './actionExecutionPlan';
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
    const plan = buildFormActionExecutionPlan({
      action,
      modelName: params.modelName(),
      recordId: params.recordId(),
    });
    if (plan.kind === 'disabled') return;
    if (plan.kind === 'local_mode') {
      params.applyClientMode(plan.mode, plan.toggle);
      return;
    }
    if (plan.kind === 'save') {
      await params.saveRecord(plan.refreshPolicy);
      return;
    }
    if (plan.kind === 'cancel') {
      await params.router.push({
        name: 'workbench',
        query: pickContractNavQuery(params.currentQuery() as Record<string, unknown>, {
          scene: undefined,
        }),
      });
      return;
    }
    if (plan.kind === 'open_action') {
      await params.router.push({
        name: 'action',
        params: { actionId: String(plan.actionId) },
        query: pickContractNavQuery(params.currentQuery() as Record<string, unknown>, {
          action_id: plan.actionId,
          target: plan.target || undefined,
          domain_raw: plan.domainRaw || undefined,
        }),
      });
      return;
    }
    if (plan.kind === 'open_url') {
      const navUrl = params.resolveNavigationUrl(plan.url);
      window.open(navUrl, plan.target === 'self' ? '_self' : '_blank', 'noopener,noreferrer');
      return;
    }
    if (plan.kind === 'open_missing_target') {
      params.errorMessage.value = '打开操作缺少目标页面';
      params.status.value = 'error';
      return;
    }
    if (plan.kind === 'scene_mutation') {
      const actionParams = await params.collectActionParams(action);
      if (actionParams === null) return;
      params.busyKind.value = 'action';
      try {
        await params.executeSceneMutation({
          mutation: plan.mutation,
          actionKey: plan.actionKey,
          recordId: plan.recordId,
          model: plan.model,
          context: plan.context,
          params: actionParams,
        });
        params.submissionFeedback.value = {
          kind: 'success',
          message: '操作已完成，页面数据已刷新。',
        };
        await params.applyProjectionRefreshPolicy(plan.refreshPolicy);
        return;
      } catch (err) {
        params.errorMessage.value = err instanceof Error ? err.message : '场景操作执行失败';
        params.status.value = 'error';
        return;
      } finally {
        params.busyKind.value = null;
      }
    }
    if (plan.kind === 'record_button') {
      if (!await params.ensureSavedBeforeRecordAction()) return;
      params.busyKind.value = 'action';
      try {
        const response = await executeButton({
          model: plan.model,
          res_id: plan.recordId,
          button: { name: plan.methodName, type: plan.buttonType },
          context: plan.context,
          meta: {
            menu_id: Number(params.routeMenuId() || 0) || undefined,
            action_id: params.actionId() || undefined,
          },
        });
        const result = response?.result;
        if (await params.navigateActionResponseResult(result)) {
          if (plan.refreshPolicy) {
            await params.applyProjectionRefreshPolicy(plan.refreshPolicy);
          }
          return;
        }
        const refresh = result?.type;
        if (refresh === 'refresh' && !plan.refreshPolicy) {
          await params.reload();
          return;
        }
        if (plan.refreshPolicy) {
          await params.applyProjectionRefreshPolicy(plan.refreshPolicy);
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

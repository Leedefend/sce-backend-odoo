import { resolveDefaultSortFromContract } from '../../runtime/actionViewRequestRuntime';
import { semanticStatus } from '../../../utils/semantic';

export function useActionViewProjectMetricRuntime() {
  function resolveProjectStateCell(row: Record<string, unknown>) {
    return semanticStatus(row.stage_id || row.state || row.status || row.kanban_state || row.health_state);
  }

  function resolveProjectAmount(row: Record<string, unknown>) {
    const candidates = [
      row.contract_amount,
      row.contract_income_total,
      row.dashboard_invoice_amount,
      row.amount_total,
      row.total_amount,
      row.planned_revenue,
      row.budget_total,
    ];
    for (const candidate of candidates) {
      const amount = Number(candidate);
      if (Number.isFinite(amount) && amount > 0) return amount;
    }
    return 0;
  }

  function isCompletedState(stateText: string, tone: string) {
    if (tone === 'success') return true;
    const text = String(stateText || '');
    return ['完成', '完工', '归档', '关闭', '交付'].some((keyword) => text.includes(keyword));
  }

  function resolveDefaultSort(fields: Record<string, unknown>) {
    return resolveDefaultSortFromContract(fields);
  }

  return {
    resolveProjectStateCell,
    resolveProjectAmount,
    isCompletedState,
    resolveDefaultSort,
  };
}


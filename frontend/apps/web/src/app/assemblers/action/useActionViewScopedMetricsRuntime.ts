import { readTotalFromListResult } from '../../runtime/actionViewRequestRuntime';

type Dict = Record<string, unknown>;

type UseActionViewScopedMetricsRuntimeOptions = {
  listRecordsRaw: (payload: Dict) => Promise<{ data: unknown }>;
  resolveProjectStateCell: (row: Record<string, unknown>) => { text: string; tone: string };
  isCompletedState: (stateText: string, tone: string) => boolean;
  resolveProjectAmount: (row: Record<string, unknown>) => number;
};

export function useActionViewScopedMetricsRuntime(options: UseActionViewScopedMetricsRuntimeOptions) {
  async function fetchScopedTotal(params: {
    model: string;
    domain: unknown[];
    domainRaw: string;
    context: Record<string, unknown>;
    contextRaw: string;
    searchTerm: string;
    order: string;
  }) {
    const result = await options.listRecordsRaw({
      model: params.model,
      fields: ['id'],
      domain: params.domain,
      domain_raw: params.domainRaw,
      need_total: true,
      context: params.context,
      context_raw: params.contextRaw,
      limit: 1,
      offset: 0,
      search_term: params.searchTerm || undefined,
      order: params.order,
    });
    return readTotalFromListResult(result.data);
  }

  async function fetchProjectScopeMetrics(params: {
    model: string;
    domain: unknown[];
    domainRaw: string;
    context: Record<string, unknown>;
    contextRaw: string;
    searchTerm: string;
    order: string;
  }) {
    const fields = [
      'id',
      'stage_id',
      'state',
      'status',
      'contract_income_total',
      'contract_amount',
      'amount_total',
      'total_amount',
      'budget_total',
    ];
    const pageLimit = 200;
    const maxPages = 25;
    let page = 0;
    let offset = 0;
    let warning = 0;
    let done = 0;
    let amount = 0;
    while (page < maxPages) {
      const result = await options.listRecordsRaw({
        model: params.model,
        fields,
        domain: params.domain,
        domain_raw: params.domainRaw,
        context: params.context,
        context_raw: params.contextRaw,
        limit: pageLimit,
        offset,
        search_term: params.searchTerm || undefined,
        order: params.order,
      });
      const payload = result.data && typeof result.data === 'object'
        ? (result.data as Record<string, unknown>)
        : {};
      const pageRows = Array.isArray(payload.records)
        ? (payload.records as Array<Record<string, unknown>>)
        : [];
      if (!pageRows.length) break;
      pageRows.forEach((row) => {
        const state = options.resolveProjectStateCell(row);
        if (state.tone === 'danger' || state.tone === 'warning') warning += 1;
        if (options.isCompletedState(String(state.text || ''), state.tone)) done += 1;
        amount += options.resolveProjectAmount(row);
      });
      const nextOffset = Number(payload.next_offset || 0);
      if (!Number.isFinite(nextOffset) || nextOffset <= offset) {
        offset += pageRows.length;
      } else {
        offset = Math.trunc(nextOffset);
      }
      if (pageRows.length < pageLimit) break;
      page += 1;
    }
    return { warning, done, amount };
  }

  return {
    fetchScopedTotal,
    fetchProjectScopeMetrics,
  };
}


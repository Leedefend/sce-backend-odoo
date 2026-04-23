type Dict = Record<string, unknown>;

type ScopeTotals = { all: number; active: number; archived: number } | null;
type ScopeMetrics = { warning: number; done: number; amount: number } | null;

export async function loadActionViewProjectScopeSnapshot(options: {
  enabled: boolean;
  model: string;
  baseDomain: unknown[];
  domainRaw: string;
  context: Dict;
  contextRaw: string;
  searchTerm: string;
  order: string;
  fetchScopedTotal: (params: {
    model: string;
    domain: unknown[];
    domainRaw: string;
    context: Dict;
    contextRaw: string;
    searchTerm: string;
    order: string;
  }) => Promise<number | null>;
  fetchProjectScopeMetrics: (params: {
    model: string;
    domain: unknown[];
    domainRaw: string;
    context: Dict;
    contextRaw: string;
    searchTerm: string;
    order: string;
  }) => Promise<ScopeMetrics>;
}): Promise<{ totals: ScopeTotals; metrics: ScopeMetrics }> {
  if (!options.enabled) {
    return { totals: null, metrics: null };
  }
  try {
    const term = options.searchTerm.trim();
    const [allTotal, activeTotal, archivedTotal, metrics] = await Promise.all([
      options.fetchScopedTotal({
        model: options.model,
        domain: options.baseDomain,
        domainRaw: options.domainRaw,
        context: options.context,
        contextRaw: options.contextRaw,
        searchTerm: term,
        order: options.order,
      }),
      options.fetchScopedTotal({
        model: options.model,
        domain: [...options.baseDomain, ['active', '=', true]],
        domainRaw: options.domainRaw,
        context: options.context,
        contextRaw: options.contextRaw,
        searchTerm: term,
        order: options.order,
      }),
      options.fetchScopedTotal({
        model: options.model,
        domain: [...options.baseDomain, ['active', '=', false]],
        domainRaw: options.domainRaw,
        context: options.context,
        contextRaw: options.contextRaw,
        searchTerm: term,
        order: options.order,
      }),
      options.fetchProjectScopeMetrics({
        model: options.model,
        domain: options.baseDomain,
        domainRaw: options.domainRaw,
        context: options.context,
        contextRaw: options.contextRaw,
        searchTerm: term,
        order: options.order,
      }),
    ]);

    const totals = allTotal !== null && activeTotal !== null && archivedTotal !== null
      ? { all: allTotal, active: activeTotal, archived: archivedTotal }
      : null;
    return { totals, metrics };
  } catch {
    return { totals: null, metrics: null };
  }
}

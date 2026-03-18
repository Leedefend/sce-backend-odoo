type Dict = Record<string, unknown>;

type BuildLoadSuccessPhaseInputOptions = {
  result: Dict;
  contractColumns: string[];
  baseDomain: unknown[];
  requestContext: Dict;
  requestContextRaw: string;
  startedAt: number;
  resolvedModel: string;
};

export function useActionViewLoadSuccessPhaseInputRuntime() {
  function buildLoadSuccessPhaseInput(input: BuildLoadSuccessPhaseInputOptions): Dict {
    return {
      result: input.result,
      contractColumns: input.contractColumns,
      baseDomain: input.baseDomain,
      requestContext: input.requestContext,
      requestContextRaw: input.requestContextRaw,
      startedAt: input.startedAt,
      resolvedModel: input.resolvedModel,
    };
  }

  return {
    buildLoadSuccessPhaseInput,
  };
}


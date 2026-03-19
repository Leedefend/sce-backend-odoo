type Dict = Record<string, unknown>;

type BuildLoadRequestDynamicInputOptions = {
  contract: unknown;
  typedContract: Dict;
  viewMode: string;
  resolvedModel: string;
  searchTerm: string;
  sortLabel: string;
  activeGroupByField: string;
  groupWindowOffset: number;
  groupSampleLimit: number;
  contractLimit: number;
  groupPageOffsets: Record<string, number>;
  metaDomainRaw: unknown;
  sceneFiltersRaw: unknown;
  metaContextRaw: unknown;
};

export function useActionViewLoadRequestDynamicInputRuntime() {
  function buildLoadRequestDynamicInput(input: BuildLoadRequestDynamicInputOptions): Dict {
    return {
      contract: input.contract,
      typedContract: input.typedContract,
      viewMode: input.viewMode,
      resolvedModel: input.resolvedModel,
      searchTerm: input.searchTerm,
      sortLabel: input.sortLabel,
      activeGroupByField: input.activeGroupByField,
      groupWindowOffset: input.groupWindowOffset,
      groupSampleLimit: input.groupSampleLimit,
      contractLimit: input.contractLimit,
      groupPageOffsets: input.groupPageOffsets,
      metaDomainRaw: input.metaDomainRaw,
      sceneFiltersRaw: input.sceneFiltersRaw,
      metaContextRaw: input.metaContextRaw,
    };
  }

  return {
    buildLoadRequestDynamicInput,
  };
}


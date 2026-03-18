type Dict = Record<string, unknown>;

type UseActionViewLoadMainPhaseInputRuntimeOptions = {
  staticInput: Dict | (() => Dict);
};

export function useActionViewLoadMainPhaseInputRuntime(options: UseActionViewLoadMainPhaseInputRuntimeOptions) {
  function buildLoadMainPhaseInput(input: { startedAt: number }): Dict {
    const staticInput = typeof options.staticInput === 'function'
      ? options.staticInput()
      : options.staticInput;
    return {
      ...staticInput,
      startedAt: input.startedAt,
    };
  }

  return {
    buildLoadMainPhaseInput,
  };
}


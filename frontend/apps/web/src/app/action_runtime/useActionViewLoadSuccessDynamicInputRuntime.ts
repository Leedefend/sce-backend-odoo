type Dict = Record<string, unknown>;

type UseActionViewLoadSuccessDynamicInputRuntimeOptions = {
  staticInput: Dict | (() => Dict);
};

export function useActionViewLoadSuccessDynamicInputRuntime(options: UseActionViewLoadSuccessDynamicInputRuntimeOptions) {
  function buildLoadSuccessDynamicInput(input: Dict): Dict {
    const staticInput = typeof options.staticInput === 'function'
      ? options.staticInput()
      : options.staticInput;
    return {
      ...input,
      ...staticInput,
    };
  }

  return {
    buildLoadSuccessDynamicInput,
  };
}

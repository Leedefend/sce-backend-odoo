type Dict = Record<string, unknown>;

type UseActionViewLoadRequestInputRuntimeOptions = {
  staticInput: Dict | (() => Dict);
};

export function useActionViewLoadRequestInputRuntime(options: UseActionViewLoadRequestInputRuntimeOptions) {
  function buildLoadRequestInput(input: Dict): Dict {
    const staticInput = typeof options.staticInput === 'function'
      ? options.staticInput()
      : options.staticInput;
    return {
      ...input,
      ...staticInput,
    };
  }

  return {
    buildLoadRequestInput,
  };
}

type Dict = Record<string, unknown>;

type UseActionViewLoadBeginInputRuntimeOptions = {
  staticInput: Dict | (() => Dict);
};

export function useActionViewLoadBeginInputRuntime(options: UseActionViewLoadBeginInputRuntimeOptions) {
  function buildLoadBeginInput(input: Dict): Dict {
    const staticInput = typeof options.staticInput === 'function'
      ? options.staticInput()
      : options.staticInput;
    return {
      ...input,
      ...staticInput,
    };
  }

  return {
    buildLoadBeginInput,
  };
}


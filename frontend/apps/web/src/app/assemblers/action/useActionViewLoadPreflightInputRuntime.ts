type Dict = Record<string, unknown>;

type UseActionViewLoadPreflightInputRuntimeOptions = {
  staticInput: Dict | (() => Dict);
};

export function useActionViewLoadPreflightInputRuntime(options: UseActionViewLoadPreflightInputRuntimeOptions) {
  function buildLoadPreflightInput(input: Dict): Dict {
    const staticInput = typeof options.staticInput === 'function'
      ? options.staticInput()
      : options.staticInput;
    return {
      ...input,
      ...staticInput,
    };
  }

  return {
    buildLoadPreflightInput,
  };
}


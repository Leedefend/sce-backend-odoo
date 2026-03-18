type Dict = Record<string, unknown>;

type UseActionViewHudEntriesInputRuntimeOptions = {
  staticInput: Dict | (() => Dict);
};

export function useActionViewHudEntriesInputRuntime(options: UseActionViewHudEntriesInputRuntimeOptions) {
  function buildHudEntriesInput(): Dict {
    return typeof options.staticInput === 'function'
      ? options.staticInput()
      : options.staticInput;
  }

  return {
    buildHudEntriesInput,
  };
}


type UseActionViewModeRuntimeOptions = {
  strictContractMode: { value: boolean };
  strictViewModeLabelMap: { value: Record<string, string> };
  pageText: (key: string, fallback: string) => string;
  preferredViewMode: { value: string };
  viewMode: { value: string };
  normalizeActionViewMode: (mode: string) => string;
  resolveActionViewModeLabel: (input: {
    mode: string;
    strictContractMode: boolean;
    strictLabelMap: Record<string, string>;
    pageText: (key: string, fallback: string) => string;
  }) => string;
  load: () => Promise<void>;
};

export function useActionViewModeRuntime(options: UseActionViewModeRuntimeOptions) {
  function viewModeLabel(mode: string) {
    return options.resolveActionViewModeLabel({
      mode,
      strictContractMode: options.strictContractMode.value,
      strictLabelMap: options.strictViewModeLabelMap.value,
      pageText: options.pageText,
    });
  }

  function switchViewMode(mode: string) {
    const normalized = options.normalizeActionViewMode(mode);
    if (!normalized || normalized === options.viewMode.value) return;
    options.preferredViewMode.value = normalized;
    void options.load();
  }

  return {
    viewModeLabel,
    switchViewMode,
  };
}

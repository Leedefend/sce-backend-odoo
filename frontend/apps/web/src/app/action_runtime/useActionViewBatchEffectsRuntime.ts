type Dict = Record<string, unknown>;

type UseActionViewBatchEffectsRuntimeOptions = {
  setError: (err: unknown, fallback: string) => void;
  load: () => Promise<void>;
  clearSelection: () => void;
  resolveRequestContext: () => Record<string, unknown>;
  mergeContext: (base: unknown, extra: unknown) => Record<string, unknown>;
  actionMetaContext: () => unknown;
  downloadCsvBase64: (filename: string, mimeType: string, contentB64: string) => void;
};

export function useActionViewBatchEffectsRuntime(options: UseActionViewBatchEffectsRuntimeOptions) {
  function reportBatchError(err: unknown, fallback: string) {
    options.setError(err, fallback);
  }

  function buildBatchRequestContext(): Dict {
    return options.mergeContext(options.actionMetaContext(), options.resolveRequestContext());
  }

  async function applyBatchSuccessReload() {
    options.clearSelection();
    await options.load();
  }

  function downloadCsv(filename: string, mimeType: string, contentB64: string) {
    options.downloadCsvBase64(filename, mimeType, contentB64);
  }

  return {
    reportBatchError,
    buildBatchRequestContext,
    applyBatchSuccessReload,
    downloadCsv,
  };
}

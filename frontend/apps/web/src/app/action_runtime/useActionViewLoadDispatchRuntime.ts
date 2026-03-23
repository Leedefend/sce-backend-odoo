type LoadHandler = () => Promise<void>;

type UseActionViewLoadDispatchRuntimeResult = {
  bindLoad: (handler: LoadHandler) => void;
  requestLoad: () => Promise<void>;
};

export function useActionViewLoadDispatchRuntime(): UseActionViewLoadDispatchRuntimeResult {
  let loadHandler: LoadHandler = async () => {};

  function bindLoad(handler: LoadHandler) {
    loadHandler = handler;
  }

  function requestLoad(): Promise<void> {
    return loadHandler();
  }

  return {
    bindLoad,
    requestLoad,
  };
}

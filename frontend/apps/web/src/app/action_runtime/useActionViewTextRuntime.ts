type PageText = (key: string, fallback?: string) => string;

type UseActionViewTextRuntimeOptions = {
  pageText: PageText;
};

export function useActionViewTextRuntime(options: UseActionViewTextRuntimeOptions) {
  function t(key: string, fallback?: string): string {
    return options.pageText(key, fallback);
  }

  return {
    t,
  };
}


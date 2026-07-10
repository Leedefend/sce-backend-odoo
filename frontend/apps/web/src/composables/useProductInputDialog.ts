import { reactive } from 'vue';

export type ProductInputOptions = {
  title: string;
  label: string;
  placeholder?: string;
  defaultValue?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  required?: boolean;
};

export function useProductInputDialog() {
  let resolver: ((value: string | null) => void) | null = null;
  const state = reactive({
    open: false,
    title: '',
    label: '',
    placeholder: '',
    value: '',
    confirmLabel: '确定',
    cancelLabel: '取消',
    required: false,
  });

  function close(value: string | null) {
    state.open = false;
    const resolve = resolver;
    resolver = null;
    resolve?.(value);
  }

  function open(options: ProductInputOptions) {
    if (resolver) close(null);
    state.title = options.title;
    state.label = options.label;
    state.placeholder = options.placeholder || '';
    state.value = options.defaultValue || '';
    state.confirmLabel = options.confirmLabel || '确定';
    state.cancelLabel = options.cancelLabel || '取消';
    state.required = Boolean(options.required);
    state.open = true;
    return new Promise<string | null>((resolve) => {
      resolver = resolve;
    });
  }

  return {
    state,
    open,
    confirm: (value: string) => close(value),
    cancel: () => close(null),
  };
}

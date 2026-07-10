import { reactive } from 'vue';

export type ProductConfirmTone = 'normal' | 'danger';

export type ProductConfirmOptions = {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: ProductConfirmTone;
};

export function useProductConfirmDialog() {
  let resolver: ((value: boolean) => void) | null = null;
  const state = reactive({
    open: false,
    title: '',
    message: '',
    confirmLabel: '确认',
    cancelLabel: '取消',
    tone: 'normal' as ProductConfirmTone,
  });

  function close(value: boolean) {
    state.open = false;
    const resolve = resolver;
    resolver = null;
    resolve?.(value);
  }

  function open(options: ProductConfirmOptions) {
    if (resolver) close(false);
    state.title = options.title;
    state.message = options.message;
    state.confirmLabel = options.confirmLabel || '确认';
    state.cancelLabel = options.cancelLabel || '取消';
    state.tone = options.tone || 'normal';
    state.open = true;
    return new Promise<boolean>((resolve) => {
      resolver = resolve;
    });
  }

  return {
    state,
    open,
    confirm: () => close(true),
    cancel: () => close(false),
  };
}

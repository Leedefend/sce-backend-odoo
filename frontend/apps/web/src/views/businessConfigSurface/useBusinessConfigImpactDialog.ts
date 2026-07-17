import { ref } from 'vue';

export function useBusinessConfigImpactDialog() {
  const impactDialog = ref({
    open: false,
    summary: '',
    immediate: true,
    rollbackText: '系统保留配置版本，可从版本记录恢复。',
  });
  let resolver: ((confirmed: boolean) => void) | null = null;

  function openImpactDialog(options: { summary: string; immediate?: boolean; rollbackText?: string }) {
    impactDialog.value = {
      open: true,
      summary: options.summary,
      immediate: options.immediate !== false,
      rollbackText: options.rollbackText || '系统保留配置版本，可从版本记录恢复。',
    };
    return new Promise<boolean>((resolve) => { resolver = resolve; });
  }

  function resolveImpactDialog(confirmed: boolean) {
    impactDialog.value.open = false;
    resolver?.(confirmed);
    resolver = null;
  }

  const rollbackConfirm = {
    open: ({ message }: { message: string }) => openImpactDialog({
      summary: message,
      rollbackText: '确认后可再次从版本记录恢复到其他稳定版本。',
    }),
  };

  return { impactDialog, openImpactDialog, resolveImpactDialog, rollbackConfirm };
}

import { ref } from 'vue';

export function useFieldOrderDragRuntime(params: {
  enabled: () => boolean;
  resolveFieldLabel: (fieldKey: string) => string;
  onDragEnd?: () => void;
}) {
  const draggingFieldKey = ref('');
  const draggingFieldLabel = ref('');
  const dropTargetFieldKey = ref('');
  const dropTargetPlacement = ref<'before' | 'after'>('before');
  const autoScrollDirection = ref(0);
  let autoScrollFrame = 0;

  function resetDropTarget() {
    dropTargetFieldKey.value = '';
    dropTargetPlacement.value = 'before';
  }

  function stopAutoScroll() {
    autoScrollDirection.value = 0;
    if (autoScrollFrame) {
      cancelAnimationFrame(autoScrollFrame);
      autoScrollFrame = 0;
    }
  }

  function runAutoScroll() {
    if (!autoScrollDirection.value || !draggingFieldKey.value) {
      stopAutoScroll();
      return;
    }
    const viewportHeight = typeof window !== 'undefined' ? window.innerHeight : 0;
    const maxScrollTop = typeof document !== 'undefined'
      ? Math.max(
        document.documentElement.scrollHeight,
        document.body?.scrollHeight || 0,
      ) - viewportHeight
      : 0;
    const currentScrollTop = typeof window !== 'undefined' ? window.scrollY : 0;
    const atStart = currentScrollTop <= 0 && autoScrollDirection.value < 0;
    const atEnd = currentScrollTop >= maxScrollTop && autoScrollDirection.value > 0;
    if (atStart || atEnd) {
      stopAutoScroll();
      return;
    }
    window.scrollBy({
      top: autoScrollDirection.value * 18,
      behavior: 'auto',
    });
    autoScrollFrame = requestAnimationFrame(runAutoScroll);
  }

  function scheduleAutoScroll(direction: number) {
    if (autoScrollDirection.value === direction && autoScrollFrame) return;
    stopAutoScroll();
    if (!direction) return;
    autoScrollDirection.value = direction;
    autoScrollFrame = requestAnimationFrame(runAutoScroll);
  }

  function dragStart(fieldKey: string, event?: DragEvent) {
    if (!params.enabled()) return;
    draggingFieldKey.value = fieldKey;
    draggingFieldLabel.value = draggingFieldLabel.value || params.resolveFieldLabel(fieldKey);
    resetDropTarget();
    if (event?.dataTransfer) {
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('text/plain', fieldKey);
    }
  }

  function windowDragOver(event: DragEvent) {
    if (!params.enabled() || !draggingFieldKey.value) return;
    const viewportHeight = window.innerHeight || 0;
    if (!viewportHeight) return;
    const edgeSize = Math.min(132, Math.max(72, Math.round(viewportHeight * 0.16)));
    if (event.clientY <= edgeSize) {
      scheduleAutoScroll(-1);
      return;
    }
    if (event.clientY >= viewportHeight - edgeSize) {
      scheduleAutoScroll(1);
      return;
    }
    scheduleAutoScroll(0);
  }

  function dragOver(fieldKey: string, placement: 'before' | 'after' | '' = 'before') {
    if (!params.enabled() || !draggingFieldKey.value || draggingFieldKey.value === fieldKey) return;
    dropTargetFieldKey.value = fieldKey;
    dropTargetPlacement.value = placement === 'after' ? 'after' : 'before';
  }

  function dragLeave(fieldKey: string) {
    if (dropTargetFieldKey.value === fieldKey) resetDropTarget();
  }

  function dragEnd() {
    draggingFieldKey.value = '';
    draggingFieldLabel.value = '';
    resetDropTarget();
    stopAutoScroll();
    params.onDragEnd?.();
  }

  function windowDragStop() {
    dragEnd();
  }

  return {
    draggingFieldKey,
    draggingFieldLabel,
    dropTargetFieldKey,
    dropTargetPlacement,
    dragStart,
    dragOver,
    dragLeave,
    dragEnd,
    windowDragOver,
    windowDragStop,
    resetDropTarget,
  };
}

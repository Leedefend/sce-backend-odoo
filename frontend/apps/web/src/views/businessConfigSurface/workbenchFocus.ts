import { nextTick } from 'vue';

const ACTIVE_EDITOR_SCROLL_OPTIONS = { block: 'start', behavior: 'auto' } as const;
const ACTIVE_EDITOR_VIEWPORT_TOP = 96;

export async function focusActiveEditorPanel() {
  await nextTick();
  const panel = document.querySelector<HTMLElement>('.config-editor-panel');
  if (!panel) return;
  await new Promise<void>((resolve) => window.requestAnimationFrame(() => resolve()));
  const scrollContainer = panel.closest<HTMLElement>('.content');
  const rect = panel.getBoundingClientRect();
  if (scrollContainer) {
    const containerRect = scrollContainer.getBoundingClientRect();
    scrollContainer.scrollBy({ top: rect.top - containerRect.top - ACTIVE_EDITOR_VIEWPORT_TOP, behavior: 'auto' });
    return;
  }
  window.scrollBy({ top: rect.top - ACTIVE_EDITOR_VIEWPORT_TOP, behavior: 'auto' });
}

export async function focusSelectedConfigPanelOnMobile() {
  await nextTick();
  if (!window.matchMedia('(max-width: 900px)').matches) return;
  document.querySelector<HTMLElement>('.page-config-panel')?.scrollIntoView(ACTIVE_EDITOR_SCROLL_OPTIONS);
}

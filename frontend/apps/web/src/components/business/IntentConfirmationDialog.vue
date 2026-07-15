<template>
  <dialog
    v-if="open"
    ref="dialogElement"
    class="intent-confirmation"
    aria-labelledby="intent-confirmation-title"
    aria-describedby="intent-confirmation-message"
    @cancel.prevent="settle(false)"
  >
    <form @submit.prevent="settle(true)">
      <header>
        <p>业务状态将发生变化</p>
        <h2 id="intent-confirmation-title">确认{{ actionLabel }}</h2>
      </header>
      <p id="intent-confirmation-message">{{ message }}</p>
      <footer>
        <button type="button" class="sc-btn sc-btn-ghost" @click="settle(false)">取消</button>
        <button ref="confirmButton" type="submit" class="sc-btn sc-btn-primary">确认{{ actionLabel }}</button>
      </footer>
    </form>
  </dialog>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue';

const open = ref(false);
const actionLabel = ref('操作');
const message = ref('');
const dialogElement = ref<HTMLDialogElement | null>(null);
const confirmButton = ref<HTMLButtonElement | null>(null);
let pendingResolve: ((confirmed: boolean) => void) | null = null;
let trigger: HTMLElement | null = null;

watch(open, async (visible) => {
  if (!visible) return;
  await nextTick();
  dialogElement.value?.showModal();
  confirmButton.value?.focus();
});

function confirm(input: { actionLabel: string; message: string }) {
  if (pendingResolve) return Promise.resolve(false);
  trigger = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  actionLabel.value = input.actionLabel || '操作';
  message.value = input.message || '该操作执行后将立即生效，请确认是否继续。';
  open.value = true;
  return new Promise<boolean>((resolve) => { pendingResolve = resolve; });
}

async function settle(confirmed: boolean) {
  const resolve = pendingResolve;
  pendingResolve = null;
  open.value = false;
  resolve?.(confirmed);
  await nextTick();
  trigger?.focus();
  trigger = null;
}

defineExpose({ confirm });
</script>

<style scoped>
.intent-confirmation { width: min(calc(100% - 2 * var(--sc-product-space-2)), 460px); max-height: calc(100dvh - 2 * var(--sc-product-space-2)); padding: var(--sc-product-space-3); border: 1px solid var(--sc-app-border); border-radius: var(--sc-component-dialog-radius); background: var(--sc-app-panel); color: var(--sc-app-text-primary); box-shadow: var(--sc-app-shadow); overflow: auto; }
.intent-confirmation::backdrop { background: color-mix(in srgb, var(--sc-app-text-primary) 52%, transparent); }
.intent-confirmation form { display: grid; gap: var(--sc-product-space-2); }
.intent-confirmation header p { margin: 0 0 var(--sc-product-space-1); color: var(--sc-app-text-secondary); font-size: var(--sc-product-text-sm); }
.intent-confirmation h2 { margin: 0; font-size: 20px; }
.intent-confirmation > p { margin: var(--sc-product-space-2) 0; line-height: 1.6; }
.intent-confirmation footer { display: flex; justify-content: flex-end; gap: var(--sc-product-space-1); }
</style>

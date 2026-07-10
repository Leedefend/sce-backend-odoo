<template>
  <div
    v-if="open"
    class="product-confirm-backdrop"
    role="dialog"
    aria-modal="true"
    :aria-label="title"
    @click.self="$emit('cancel')"
  >
    <section class="product-confirm">
      <header class="product-confirm__head">
        <h3>{{ title }}</h3>
        <button type="button" class="product-confirm__close" aria-label="关闭" @click="$emit('cancel')">×</button>
      </header>
      <p class="product-confirm__message">{{ message }}</p>
      <footer class="product-confirm__actions">
        <button type="button" class="product-confirm__cancel" @click="$emit('cancel')">
          {{ cancelLabel }}
        </button>
        <button type="button" class="product-confirm__confirm" :class="`is-${tone}`" @click="$emit('confirm')">
          {{ confirmLabel }}
        </button>
      </footer>
    </section>
  </div>
</template>

<script setup lang="ts">
import type { ProductConfirmTone } from '../composables/useProductConfirmDialog';

withDefaults(defineProps<{
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: ProductConfirmTone;
}>(), {
  confirmLabel: '确认',
  cancelLabel: '取消',
  tone: 'normal',
});

defineEmits<{
  (event: 'confirm'): void;
  (event: 'cancel'): void;
}>();
</script>

<style scoped>
.product-confirm-backdrop {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: grid;
  place-items: center;
  padding: 20px;
  background: var(--sc-semantic-overlay-bg);
}

.product-confirm {
  width: min(420px, 100%);
  border: 1px solid var(--sc-app-border);
  border-radius: var(--sc-component-dialog-radius);
  background: var(--sc-app-panel);
  box-shadow: var(--sc-semantic-shadow-modal);
}

.product-confirm__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 18px 10px;
}

.product-confirm__head h3 {
  margin: 0;
  font-size: 16px;
}

.product-confirm__close {
  border: 0;
  background: transparent;
  color: var(--sc-app-text-secondary);
  cursor: pointer;
  font-size: 20px;
  line-height: 1;
}

.product-confirm__message {
  margin: 0;
  padding: 0 18px 16px;
  color: var(--sc-app-text-secondary);
  font-size: 14px;
  line-height: 1.6;
}

.product-confirm__actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 18px 16px;
  border-top: 1px solid var(--sc-app-border);
}

.product-confirm__cancel,
.product-confirm__confirm {
  border-radius: var(--sc-component-button-radius);
  padding: 8px 14px;
  cursor: pointer;
}

.product-confirm__cancel {
  border: 1px solid var(--sc-app-border-strong);
  background: var(--sc-app-panel);
  color: var(--sc-app-text-primary);
}

.product-confirm__confirm {
  border: 1px solid var(--sc-app-primary);
  background: var(--sc-app-primary);
  color: var(--sc-semantic-text-on-interactive);
}

.product-confirm__confirm.is-danger {
  border-color: var(--sc-app-danger-border);
  background: var(--sc-app-danger-text);
}
</style>

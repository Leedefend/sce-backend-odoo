<template>
  <div
    v-if="open"
    class="product-input-backdrop"
    role="dialog"
    aria-modal="true"
    :aria-label="title"
    @click.self="$emit('cancel')"
  >
    <form class="product-input" @submit.prevent="$emit('confirm', localValue.trim())">
      <header class="product-input__head">
        <h3>{{ title }}</h3>
        <button type="button" class="product-input__close" aria-label="关闭" @click="$emit('cancel')">×</button>
      </header>
      <label class="product-input__field">
        <span>{{ label }}</span>
        <input v-model="localValue" :placeholder="placeholder" :required="required" autofocus />
      </label>
      <footer class="product-input__actions">
        <button type="button" class="product-input__cancel" @click="$emit('cancel')">{{ cancelLabel }}</button>
        <button type="submit" class="product-input__confirm">{{ confirmLabel }}</button>
      </footer>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

const props = withDefaults(defineProps<{
  open: boolean;
  title: string;
  label: string;
  placeholder?: string;
  value?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  required?: boolean;
}>(), {
  placeholder: '',
  value: '',
  confirmLabel: '确定',
  cancelLabel: '取消',
  required: false,
});

defineEmits<{
  (event: 'confirm', value: string): void;
  (event: 'cancel'): void;
}>();

const localValue = ref(props.value);

watch(() => props.open, (open) => {
  if (open) localValue.value = props.value;
});
</script>

<style scoped>
.product-input-backdrop {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: grid;
  place-items: center;
  padding: 20px;
  background: var(--sc-semantic-overlay-bg);
}

.product-input {
  width: min(440px, 100%);
  border: 1px solid var(--sc-app-border);
  border-radius: var(--sc-component-dialog-radius);
  background: var(--sc-app-panel);
  box-shadow: var(--sc-semantic-shadow-modal);
}

.product-input__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 18px 10px;
}

.product-input__head h3 {
  margin: 0;
  font-size: 16px;
}

.product-input__close {
  border: 0;
  background: transparent;
  color: var(--sc-app-text-secondary);
  cursor: pointer;
  font-size: 20px;
  line-height: 1;
}

.product-input__field {
  display: grid;
  gap: 8px;
  padding: 0 18px 16px;
  color: var(--sc-app-text-secondary);
  font-size: 13px;
}

.product-input__field input {
  border: 1px solid var(--sc-app-border-strong);
  border-radius: var(--sc-component-input-radius);
  padding: 9px 11px;
  color: var(--sc-app-text-primary);
  background: var(--sc-app-input-bg);
}

.product-input__actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 18px 16px;
  border-top: 1px solid var(--sc-app-border);
}

.product-input__cancel,
.product-input__confirm {
  border-radius: var(--sc-component-button-radius);
  padding: 8px 14px;
  cursor: pointer;
}

.product-input__cancel {
  border: 1px solid var(--sc-app-border-strong);
  background: var(--sc-app-panel);
  color: var(--sc-app-text-primary);
}

.product-input__confirm {
  border: 1px solid var(--sc-app-primary);
  background: var(--sc-app-primary);
  color: var(--sc-semantic-text-on-interactive);
}
</style>

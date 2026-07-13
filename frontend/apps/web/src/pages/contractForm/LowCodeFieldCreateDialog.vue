<template>
  <div
    v-if="dialog.open"
    class="contract-field-create-backdrop"
    role="presentation"
    @click.self="$emit('close')"
    @keydown.esc="$emit('close')"
  >
    <form
      class="contract-field-create-dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="contract-field-create-title"
      @submit.prevent="$emit('submit')"
    >
      <header class="contract-field-create-head">
        <h3 id="contract-field-create-title">新增字段</h3>
        <button type="button" class="contract-field-create-close" :disabled="busy" aria-label="取消新增字段" @click="$emit('close')">x</button>
      </header>
      <label class="contract-mode-prompt-field">
        <span>字段标题</span>
        <input ref="labelInputRef" :value="dialog.label" required :disabled="busy" @input="$emit('update:label', inputValue($event))" />
      </label>
      <label class="contract-mode-prompt-field">
        <span>字段类型</span>
        <select :value="dialog.ttype" required :disabled="busy" @change="$emit('update:ttype', inputValue($event))">
          <option value="char">单行文本</option>
          <option value="text">多行文本</option>
          <option value="integer">整数</option>
          <option value="float">小数</option>
          <option value="boolean">是/否</option>
          <option value="date">日期</option>
          <option value="datetime">日期时间</option>
          <option value="html">富文本</option>
        </select>
      </label>
      <footer class="contract-field-create-actions">
        <button type="submit" class="chip-btn" :disabled="busy">创建字段</button>
        <button type="button" class="ghost" :disabled="busy" @click="$emit('close')">取消</button>
      </footer>
    </form>
  </div>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue';

export type LowCodeFieldCreateDialogState = {
  open: boolean;
  afterFieldKey: string;
  groupTitle: string;
  sequence: number;
  label: string;
  ttype: string;
};

const props = defineProps<{
  dialog: LowCodeFieldCreateDialogState;
  busy: boolean;
}>();

defineEmits<{
  close: [];
  submit: [];
  'update:label': [value: string];
  'update:ttype': [value: string];
}>();

const labelInputRef = ref<HTMLInputElement | null>(null);

watch(
  () => props.dialog.open,
  async (open) => {
    if (!open) return;
    await nextTick();
    labelInputRef.value?.focus();
  },
);

function inputValue(event: Event) {
  return String((event.target as HTMLInputElement | HTMLSelectElement).value || '');
}
</script>

<style scoped src="./LowCodeFieldCreateDialog.css"></style>

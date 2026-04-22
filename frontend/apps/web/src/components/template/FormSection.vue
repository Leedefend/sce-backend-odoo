<template>
  <section :class="['template-form-section', toneClass, { 'template-form-section--native': nativeLike }]" data-component="FormSection">
    <div v-if="title || $slots.action" class="template-form-section-head">
      <h3 class="template-form-section-title">{{ title }}</h3>
      <slot name="action" />
    </div>
    <p v-if="hint" class="template-form-section-hint">{{ hint }}</p>
    <div class="template-form-section-grid" :style="gridStyle">
      <template v-if="fields.length">
        <div
          v-for="field in fields"
          :key="field.key"
          :class="['field', field.spanClass || defaultSpanClass(field.type)]"
          :data-field-type="field.type"
        >
          <label class="label">{{ field.label }}<span v-if="field.required" class="required">*</span></label>
          <template v-if="field.readonly">
            <slot name="readonly" :field="field">
              <span class="readonly-value">{{ readonlyText(field.value) }}</span>
            </slot>
          </template>
          <template v-else-if="isBaseFieldType(field.type)">
            <input
              v-if="field.type === 'boolean'"
              :checked="Boolean(field.value)"
              class="input-checkbox"
              type="checkbox"
              @change="emitFieldChange(field, ($event.target as HTMLInputElement).checked)"
            />
            <select
              v-else-if="field.type === 'selection'"
              :value="String(field.inputValue ?? '')"
              class="input"
              @change="emitFieldChange(field, ($event.target as HTMLSelectElement).value)"
            >
              <option v-if="!field.required" value="">{{ selectPlaceholderText(field) }}</option>
              <option v-for="option in field.selectionOptions || []" :key="`${field.name}-${option.value}`" :value="option.value">
                {{ option.label }}
              </option>
            </select>
            <select
              v-else-if="field.type === 'many2one'"
              class="input"
              :value="String(field.inputValue ?? '')"
              @change="emitFieldChange(field, ($event.target as HTMLSelectElement).value)"
            >
              <option value="">{{ selectPlaceholderText(field) }}</option>
              <option v-for="option in field.relationOptions || []" :key="`${field.name}-${option.value}`" :value="option.value">
                {{ option.label }}
              </option>
              <option
                v-if="field.relationCreateMode && field.relationCreateMode !== 'none' && field.many2oneCreateToken"
                :value="field.many2oneCreateToken"
              >
                {{ field.relationCreateMode === 'page' ? '+ 新建并维护...' : '+ 快速新建...' }}
              </option>
            </select>
            <input
              v-else
              :value="String(field.inputValue ?? '')"
              class="input"
              :type="inputType(field.type)"
              :placeholder="field.inputPlaceholder || inputPlaceholderText(field)"
              @input="emitFieldChange(field, ($event.target as HTMLInputElement).value)"
            />
          </template>
          <template v-else>
            <slot name="fallback" :field="field">
              <input
                :value="String(field.inputValue ?? '')"
                class="input"
                :type="inputType(field.type)"
                :placeholder="field.inputPlaceholder || inputPlaceholderText(field)"
                @input="emitFieldChange(field, ($event.target as HTMLInputElement).value)"
              />
            </slot>
          </template>
        </div>
      </template>
      <slot v-else />
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { FormSectionFieldSchema, FormSectionFieldChange, TemplateFieldType } from './formSection.types';
import { resolveInputPlaceholder, resolveSelectPlaceholder } from './placeholder.mapper';

const props = withDefaults(defineProps<{
  title: string;
  hint?: string;
  columns?: 1 | 2;
  tone?: 'core' | 'advanced';
  fields?: FormSectionFieldSchema[];
  nativeLike?: boolean;
  selectPlaceholder?: (label: string) => string;
  inputPlaceholder?: (label: string) => string;
}>(), {
  hint: '',
  columns: 2,
  tone: 'core',
  fields: () => [],
  nativeLike: false,
  selectPlaceholder: (label: string) => resolveSelectPlaceholder(label),
  inputPlaceholder: (label: string) => resolveInputPlaceholder(label),
});

const emit = defineEmits<{
  (e: 'field-change', payload: FormSectionFieldChange): void;
}>();

const toneClass = computed(() => (props.tone === 'advanced' ? 'template-form-section--advanced' : 'template-form-section--core'));
const gridStyle = computed(() => ({
  gridTemplateColumns: props.columns === 1 ? '1fr' : 'repeat(2, minmax(0, 1fr))',
}));

function isBaseFieldType(type: TemplateFieldType) {
  return ['char', 'text', 'selection', 'many2one', 'boolean', 'date', 'datetime'].includes(String(type || '').trim().toLowerCase());
}

function defaultSpanClass(type: TemplateFieldType) {
  return String(type || '').trim().toLowerCase() === 'text' ? 'field--full' : 'field--half';
}

function inputType(type: TemplateFieldType) {
  const t = String(type || '').trim().toLowerCase();
  if (t === 'date') return 'date';
  if (t === 'datetime') return 'datetime-local';
  return 'text';
}

function selectPlaceholderText(field: FormSectionFieldSchema) {
  return props.selectPlaceholder(field.label);
}

function inputPlaceholderText(field: FormSectionFieldSchema) {
  return props.inputPlaceholder(field.label);
}

function readonlyText(value: unknown) {
  if (value === null || value === undefined || value === false) return '-';
  if (Array.isArray(value)) return value.join(', ');
  return String(value);
}

function emitFieldChange(field: FormSectionFieldSchema, value: string | number | boolean | null) {
  emit('field-change', {
    name: field.name,
    type: field.type,
    value,
    descriptor: field.descriptor,
  });
}
</script>

<style scoped>
.template-form-section {
  grid-column: 1 / -1;
  border: 0;
  border-top: 1px solid var(--ui-color-border-muted);
  border-radius: 0;
  background: transparent;
  padding: var(--ui-space-4) 0 0;
}

.template-form-section--core {
  border-top: 0;
  padding-top: 0;
}

.template-form-section--advanced {
  border-top: 1px solid var(--ui-color-border);
  margin-top: 2px;
}

.template-form-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--ui-space-3);
  margin-bottom: var(--ui-space-3);
}

.template-form-section-title {
  margin: 0;
  font-size: var(--ui-font-size-md);
  color: var(--ui-color-ink-strong);
  font-weight: var(--ui-font-weight-bold);
  letter-spacing: 0.01em;
}

.template-form-section-hint {
  margin: -2px 0 var(--ui-space-3);
  font-size: var(--ui-font-size-xs);
  color: var(--ui-color-ink-muted);
  line-height: 1.45;
}

.template-form-section-grid {
  display: grid;
  row-gap: 18px;
  column-gap: var(--ui-space-6);
}

.template-form-section--native {
  padding-top: 0;
  border-top: 0;
}

.template-form-section--native .template-form-section-grid {
  row-gap: 6px;
  column-gap: 32px;
}

.field {
  display: grid;
  gap: 6px;
  min-width: 0;
  align-content: start;
}

.template-form-section--native .field {
  grid-template-columns: minmax(96px, 26%) minmax(0, 1fr);
  align-items: center;
  column-gap: var(--ui-space-3);
  min-height: 28px;
}

.template-form-section--native .field--full {
  grid-template-columns: 1fr;
}

.template-form-section--native .field--full[data-field-type='one2many'] > .label,
.template-form-section--native .field--full[data-field-type='many2many'] > .label {
  display: none;
}

.field--half {
  grid-column: span 1;
}

.field--full {
  grid-column: 1 / -1;
}

.label {
  font-size: var(--ui-font-size-xs);
  color: var(--ui-color-ink-muted);
  font-weight: var(--ui-font-weight-bold);
  margin-bottom: 0;
  letter-spacing: 0.01em;
}

.template-form-section--native .label {
  margin-bottom: 0;
  color: var(--ui-color-ink);
  font-size: var(--ui-font-size-xs);
  font-weight: var(--ui-font-weight-medium);
  line-height: 1.3;
  text-align: left;
}

.required {
  color: var(--ui-color-danger-600);
  margin-left: 2px;
}

.readonly-value {
  font-size: 13px;
  color: var(--ui-color-ink-strong);
  min-height: 40px;
  display: inline-flex;
  align-items: center;
  line-height: 1.45;
}

.template-form-section--native .readonly-value {
  min-height: 28px;
  color: var(--ui-color-ink-strong);
}

.template-form-section--native :deep(.relation-editor) {
  gap: 4px;
}

.template-form-section--native :deep(.o2m-toolbar) {
  justify-content: flex-start;
  min-height: 26px;
  border-bottom: 1px solid var(--ui-color-border);
  padding-bottom: 4px;
}

.template-form-section--native :deep(.o2m-list) {
  display: block;
  border: 1px solid var(--ui-color-border);
  border-top: 0;
}

.template-form-section--native :deep(.o2m-row) {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 4px 8px;
  align-items: center;
  padding: 4px 6px;
  border-top: 1px solid var(--ui-color-border-muted);
}

.template-form-section--native :deep(.o2m-row-state) {
  display: none;
}

.template-form-section--native :deep(.o2m-fields) {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
  gap: 4px;
}

.template-form-section--native :deep(.o2m-field) {
  gap: 2px;
}

.template-form-section--native :deep(.o2m-field .meta) {
  color: var(--ui-color-ink-muted);
  font-size: var(--ui-font-size-xs);
}

.input {
  border: 1px solid var(--ui-color-border);
  border-radius: var(--ui-radius-xs);
  padding: 8px 12px;
  height: 40px;
  min-height: 40px;
  width: 100%;
  min-width: 0;
  font-size: var(--ui-font-size-md);
  line-height: 1.35;
  color: var(--ui-color-ink-strong);
  background: var(--ui-color-surface-strong);
  box-sizing: border-box;
  transition:
    border-color var(--ui-transition-fast),
    box-shadow var(--ui-transition-fast),
    background-color var(--ui-transition-fast);
}

.input::placeholder {
  color: var(--ui-color-ink-soft);
}

.input:focus {
  outline: none;
  border-color: rgba(61, 120, 159, 0.42);
  box-shadow: 0 0 0 3px rgba(61, 120, 159, 0.14);
}

select.input {
  appearance: none;
  background-image:
    linear-gradient(45deg, transparent 50%, var(--ui-color-ink-soft) 50%),
    linear-gradient(135deg, var(--ui-color-ink-soft) 50%, transparent 50%);
  background-position: calc(100% - 16px) calc(50% - 2px), calc(100% - 11px) calc(50% - 2px);
  background-size: 5px 5px, 5px 5px;
  background-repeat: no-repeat;
  padding-right: 30px;
}

.input[type='date'] {
  min-width: 0;
  padding-right: 10px;
}

@media (max-width: 860px) {
  .template-form-section-grid {
    grid-template-columns: 1fr !important;
    row-gap: 16px;
    column-gap: 0;
  }

  .template-form-section--native .field {
    grid-template-columns: 1fr;
    row-gap: 2px;
  }
}
</style>

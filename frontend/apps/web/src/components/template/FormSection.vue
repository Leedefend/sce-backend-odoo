<template>
  <section :class="['template-form-section', toneClass]" data-component="FormSection">
    <div v-if="showHead" class="template-form-section-head">
      <h3 v-if="title" class="template-form-section-title">{{ title }}</h3>
      <slot name="action" />
    </div>
    <p v-if="hint" class="template-form-section-hint">{{ hint }}</p>
    <div class="template-form-section-grid" :style="gridStyle">
      <template v-if="fields.length">
        <div
          v-for="field in fields"
          :key="field.key"
          :class="['field', field.spanClass || defaultSpanClass(field.type), fieldWidgetClass(field)]"
        >
          <div class="field-label-row">
            <label class="label">{{ field.label }}<span v-if="field.required" class="required">*</span></label>
          </div>
          <div :class="['field-control-row', { 'field-control-row--favorite': field.favoriteToggle }]">
            <button
              v-if="field.favoriteToggle"
              type="button"
              class="field-favorite-toggle"
              :class="{ 'field-favorite-toggle--active': field.favoriteToggle.active }"
              :aria-label="field.favoriteToggle.label"
              :aria-pressed="field.favoriteToggle.active"
              :title="field.favoriteToggle.label"
              :disabled="field.favoriteToggle.readonly"
              @click="emitFavoriteToggle(field)"
            >
              <span aria-hidden="true">{{ field.favoriteToggle.active ? '★' : '☆' }}</span>
            </button>
            <div class="field-control-main">
              <div
                v-if="field.type === 'selection' && isRadioWidget(field)"
                class="native-radio-group"
                role="radiogroup"
                :aria-label="field.label"
              >
                <label
                  v-for="option in field.selectionOptions || []"
                  :key="`${field.name}-radio-${option.value}`"
                  class="native-radio-option"
                >
                  <input
                    class="native-radio-input"
                    type="radio"
                    :name="field.key"
                    :value="option.value"
                    :checked="String(field.inputValue ?? '') === String(option.value)"
                    :disabled="field.readonly"
                    @change="!field.readonly && emitFieldChange(field, option.value)"
                  />
                  <span>{{ option.label }}</span>
                </label>
              </div>
              <template v-else-if="field.readonly">
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
                <div v-else-if="field.type === 'many2one'" :class="['many2one-widget-shell', { 'many2one-widget-shell--avatar': isAvatarMany2oneWidget(field) }]">
                  <span v-if="isAvatarMany2oneWidget(field)" class="many2one-avatar" aria-hidden="true">
                    {{ avatarText(many2oneTextValue(field)) }}
                  </span>
                  <div class="many2one-combobox">
                    <input
                      class="input"
                      type="text"
                      :list="many2oneListId(field)"
                      :value="many2oneTextValue(field)"
                      :placeholder="selectPlaceholderText(field)"
                      autocomplete="off"
                      @input="emitMany2oneQuery(field, ($event.target as HTMLInputElement).value)"
                      @change="emitMany2oneCommit(field, ($event.target as HTMLInputElement).value)"
                      @keydown.enter.prevent="emitMany2oneCommit(field, ($event.target as HTMLInputElement).value)"
                      @blur="emitMany2oneCommit(field, ($event.target as HTMLInputElement).value)"
                    />
                    <datalist :id="many2oneListId(field)">
                      <option v-for="option in field.relationOptions || []" :key="`${field.name}-${option.value}`" :value="option.label" />
                    </datalist>
                    <div class="many2one-actions">
                      <button
                        v-if="field.many2oneSearchToken"
                        type="button"
                        class="many2one-action"
                        @click="emitFieldChange(field, field.many2oneSearchToken || '')"
                      >
                        {{ field.many2oneSearchLabel }}
                      </button>
                      <button
                        v-if="field.relationCreateMode && field.relationCreateMode !== 'none' && field.many2oneCreateToken"
                        type="button"
                        class="many2one-action"
                        @click="emitFieldChange(field, field.many2oneCreateToken || '')"
                      >
                        {{ field.many2oneCreateLabel }}
                      </button>
                    </div>
                    <button
                      v-if="showMany2oneInlineCreate(field)"
                      type="button"
                      class="many2one-inline-create"
                      @mousedown.prevent
                      @click="emitMany2oneCommit(field, many2oneTextValue(field))"
                    >
                      {{ field.many2oneInlineCreateLabel }}
                    </button>
                  </div>
                </div>
                <div v-else-if="isDateRangeWidget(field)" class="native-date-range">
                  <input
                    :value="String(field.inputValue ?? '')"
                    class="input"
                    type="date"
                    :placeholder="field.inputPlaceholder || inputPlaceholderText(field)"
                    @input="emitFieldChange(field, ($event.target as HTMLInputElement).value)"
                  />
                  <span v-if="field.dateRangeEndField" class="native-date-range-separator" aria-hidden="true">→</span>
                  <input
                    v-if="field.dateRangeEndField"
                    :value="String(field.dateRangeEndInputValue ?? '')"
                    class="input"
                    type="date"
                    :placeholder="field.inputPlaceholder || inputPlaceholderText(field)"
                    @input="emitDateRangeEndChange(field, ($event.target as HTMLInputElement).value)"
                  />
                </div>
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
          </div>
        </div>
      </template>
      <slot v-else />
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, useSlots } from 'vue';
import type { FormSectionFieldSchema, FormSectionFieldChange, TemplateFieldType } from './formSection.types';
import { resolveInputPlaceholder, resolveSelectPlaceholder } from './placeholder.mapper';

const props = withDefaults(defineProps<{
  title: string;
  hint?: string;
  columns?: 1 | 2;
  tone?: 'core' | 'advanced';
  fields?: FormSectionFieldSchema[];
  selectPlaceholder?: (label: string) => string;
  inputPlaceholder?: (label: string) => string;
}>(), {
  hint: '',
  columns: 2,
  tone: 'core',
  fields: () => [],
  selectPlaceholder: (label: string) => resolveSelectPlaceholder(label),
  inputPlaceholder: (label: string) => resolveInputPlaceholder(label),
});

const emit = defineEmits<{
  (e: 'field-change', payload: FormSectionFieldChange): void;
}>();

const slots = useSlots();
const toneClass = computed(() => (props.tone === 'advanced' ? 'template-form-section--advanced' : 'template-form-section--core'));
const showHead = computed(() => Boolean(props.title || slots.action));
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

function fieldWidget(field: FormSectionFieldSchema) {
  return String(field.widget || '').trim().toLowerCase();
}

function fieldWidgetClass(field: FormSectionFieldSchema) {
  const widget = fieldWidget(field);
  return widget ? `field--widget-${widget.replace(/[^a-z0-9_-]/g, '-')}` : '';
}

function isRadioWidget(field: FormSectionFieldSchema) {
  return fieldWidget(field) === 'radio';
}

function isAvatarMany2oneWidget(field: FormSectionFieldSchema) {
  return ['many2one_avatar_user', 'many2one_avatar_employee'].includes(fieldWidget(field));
}

function isDateRangeWidget(field: FormSectionFieldSchema) {
  return fieldWidget(field) === 'daterange';
}

function selectedRelationLabel(field: FormSectionFieldSchema) {
  const value = String(field.inputValue ?? '').trim();
  if (!value) return '';
  const option = (field.relationOptions || []).find((item) => String(item.value) === value);
  return option?.label || '';
}

function many2oneTextValue(field: FormSectionFieldSchema) {
  return String(field.many2oneTextValue || selectedRelationLabel(field) || '').trim();
}

function many2oneListId(field: FormSectionFieldSchema) {
  return `many2one-list-${field.key.replace(/[^a-zA-Z0-9_-]/g, '-')}`;
}

function showMany2oneInlineCreate(field: FormSectionFieldSchema) {
  const text = many2oneTextValue(field);
  if (!text || !field.relationInlineCreate?.enabled || !field.relationInlineCreate.createOnNoMatch) return false;
  const options = field.relationOptions || [];
  if (options.length) return false;
  return true;
}

function avatarText(label: string) {
  const text = String(label || '').trim();
  return text ? text.slice(0, 1).toUpperCase() : '';
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
    widget: field.widget,
    value,
    descriptor: field.descriptor,
  });
}

function emitMany2oneQuery(field: FormSectionFieldSchema, value: string) {
  emit('field-change', {
    name: field.name,
    type: field.type,
    widget: field.widget,
    value,
    action: 'query',
    descriptor: field.descriptor,
  });
}

function emitMany2oneCommit(field: FormSectionFieldSchema, value: string) {
  emit('field-change', {
    name: field.name,
    type: field.type,
    widget: field.widget,
    value,
    action: 'commit',
    descriptor: field.descriptor,
  });
}

function emitDateRangeEndChange(field: FormSectionFieldSchema, value: string | number | boolean | null) {
  const name = String(field.dateRangeEndField || '').trim();
  if (!name) return;
  emit('field-change', {
    name,
    type: field.type,
    widget: field.widget,
    value,
    descriptor: field.descriptor,
  });
}

function emitFavoriteToggle(field: FormSectionFieldSchema) {
  const favorite = field.favoriteToggle;
  if (!favorite || favorite.readonly) return;
  emit('field-change', {
    name: favorite.name,
    type: 'boolean',
    value: !favorite.active,
    descriptor: favorite.descriptor,
  });
}
</script>

<style scoped>
.template-form-section {
  grid-column: 1 / -1;
  border: 0;
  border-top: 1px solid #f1f3f6;
  border-radius: 0;
  background: transparent;
  padding: 14px 0 0;
}

.template-form-section--core {
  border-top: 0;
  padding-top: 0;
}

.template-form-section--advanced {
  border-top: 1px solid #f2f4f7;
  margin-top: 2px;
}

.template-form-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.template-form-section-title {
  margin: 0;
  font-size: 14px;
  color: #374151;
  font-weight: 500;
}

.template-form-section-hint {
  margin: -4px 0 10px;
  font-size: 12px;
  color: #9ca3af;
}

.template-form-section-grid {
  display: grid;
  row-gap: 16px;
  column-gap: 24px;
}

.field {
  display: grid;
  gap: 0;
  min-width: 0;
  align-content: start;
}

.field--half {
  grid-column: span 1;
}

.field--full {
  grid-column: 1 / -1;
}

.field-label-row {
  display: inline-flex;
  align-items: center;
  min-width: 0;
  margin-bottom: 4px;
}

.label {
  font-size: 13px;
  color: #111827;
  font-weight: 600;
  margin: 0;
}

.field-favorite-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: 0;
  border-radius: 4px;
  background: transparent;
  color: #94a3b8;
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
}

.field-favorite-toggle:hover:not(:disabled) {
  background: #f8fafc;
  color: #64748b;
}

.field-favorite-toggle--active {
  color: #f59e0b;
}

.field-favorite-toggle:disabled {
  cursor: default;
  opacity: 0.62;
}

.required {
  color: #b91c1c;
  margin-left: 2px;
}

.field-control-row {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.field-control-main {
  flex: 1 1 auto;
  display: grid;
  min-width: 0;
}

.readonly-value {
  font-size: 13px;
  color: #475569;
  min-height: 40px;
  display: inline-flex;
  align-items: center;
}

.input {
  border: 1px solid #e9ebef;
  border-radius: 8px;
  padding: 8px 12px;
  height: 40px;
  min-height: 40px;
  width: 100%;
  min-width: 0;
  font-size: 14px;
  line-height: 1.35;
  color: #0f172a;
  background: #ffffff;
  box-sizing: border-box;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease;
}

.input::placeholder {
  color: #94a3b8;
}

.input:focus {
  outline: none;
  border-color: #94a3b8;
  box-shadow: 0 0 0 3px rgba(148, 163, 184, 0.2);
}

select.input {
  appearance: none;
  background-image: linear-gradient(45deg, transparent 50%, #64748b 50%), linear-gradient(135deg, #64748b 50%, transparent 50%);
  background-position: calc(100% - 16px) calc(50% - 2px), calc(100% - 11px) calc(50% - 2px);
  background-size: 5px 5px, 5px 5px;
  background-repeat: no-repeat;
  padding-right: 30px;
}

.native-radio-group {
  display: grid;
  gap: 8px;
  align-items: start;
}

.native-radio-option {
  display: inline-flex;
  align-items: flex-start;
  gap: 8px;
  min-width: 0;
  color: #334155;
  font-size: 13px;
  line-height: 1.35;
}

.native-radio-input {
  margin-top: 2px;
  accent-color: #374151;
}

.native-radio-input:disabled {
  cursor: default;
}

.native-radio-input:disabled + span {
  color: #64748b;
}

.many2one-widget-shell {
  position: relative;
  display: flex;
  align-items: center;
  min-width: 0;
}

.many2one-widget-shell--avatar .many2one-combobox > .input {
  padding-left: 42px;
}

.many2one-combobox {
  display: grid;
  gap: 6px;
  width: 100%;
  min-width: 0;
}

.many2one-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.many2one-action,
.many2one-inline-create {
  min-height: 28px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #ffffff;
  color: #475569;
  padding: 4px 8px;
  font-size: 12px;
  line-height: 1.2;
  cursor: pointer;
}

.many2one-action:hover,
.many2one-inline-create:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.many2one-inline-create {
  justify-self: start;
  color: #0f172a;
}

.many2one-avatar {
  position: absolute;
  left: 10px;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 999px;
  background: #e5e7eb;
  color: #475569;
  font-size: 11px;
  font-weight: 700;
  pointer-events: none;
}

.native-date-range {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  gap: 6px;
  align-items: center;
  min-width: 0;
}

.native-date-range-separator {
  color: #64748b;
  font-size: 13px;
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
}
</style>

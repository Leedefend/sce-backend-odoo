<template>
  <div v-if="field.type === 'many2many'" class="relation-editor">
    <div v-if="isMany2manyTags(field)" class="relation-tag-picker">
      <div class="relation-tags-control">
        <div v-if="adapter.selectedRelationOptions(field.name).length" class="relation-tag-list">
          <button
            v-for="option in adapter.selectedRelationOptions(field.name)"
            :key="`${field.name}-tag-${option.id}`"
            type="button"
            class="relation-tag"
            :style="tagColorStyle(option.color)"
            :disabled="adapter.busy"
            :title="`移除${option.label}`"
            @click="toggleRelationId(field.name, option.id, false)"
          >
            {{ option.label }}
            <span aria-hidden="true">×</span>
          </button>
        </div>
        <input
          class="relation-tags-input"
          type="text"
          :value="adapter.relationKeyword(field.name)"
          :placeholder="field.inputPlaceholder || adapter.inputPlaceholder(field.label)"
          autocomplete="off"
          @input="adapter.setRelationKeyword(field.name, ($event.target as HTMLInputElement).value)"
          @keydown.enter.prevent="commitTagKeyword(field.name)"
        />
        <div v-if="hasTagDropdown(field.name)" class="relation-tag-dropdown">
          <button
            v-for="option in adapter.filteredRelationOptions(field.name).slice(0, 8)"
            :key="`${field.name}-tag-option-${option.id}`"
            type="button"
            class="relation-tag-option"
            @mousedown.prevent
            @click="toggleRelationId(field.name, option.id, true)"
          >
            <span class="relation-tag-swatch" :style="tagColorStyle(option.color)" aria-hidden="true"></span>
            <span>{{ option.label }}</span>
          </button>
          <div v-if="hasTagCreateActions(field.name)" class="relation-tag-actions">
            <div
              v-if="adapter.canInlineCreateRelation(field.name)"
              class="relation-tag-hint"
              role="note"
            >
              {{ adapter.relationInlineCreateLabel(field.name) }}
            </div>
            <button
              v-if="adapter.relationCreateMode(field.name) === 'page'"
              type="button"
              class="relation-tag-action"
              @mousedown.prevent
              @click="adapter.openRelationCreate(field.name)"
            >
              {{ adapter.relationCreateLabel(field.name) }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="relation-select-editor">
      <input
        class="input relation-search"
        type="text"
        :value="adapter.relationKeyword(field.name)"
        :placeholder="field.inputPlaceholder || adapter.inputPlaceholder(field.label)"
        @input="adapter.setRelationKeyword(field.name, ($event.target as HTMLInputElement).value)"
      />
      <select
        class="input"
        multiple
        size="6"
        :value="adapter.relationIds(field.name).map((id) => String(id))"
        @change="adapter.setRelationMultiField(field.name, $event.target as HTMLSelectElement)"
      >
        <option
          v-for="option in adapter.filteredRelationOptions(field.name)"
          :key="`${field.name}-${option.id}`"
          :value="String(option.id)"
        >
          {{ option.label }}
        </option>
      </select>
    </div>
  </div>
  <div v-else-if="field.type === 'one2many'" class="relation-editor">
    <div class="o2m-toolbar">
      <button
        v-if="adapter.one2manyCanCreate(field.name)"
        class="chip-btn"
        type="button"
        :disabled="adapter.busy"
        @click="adapter.addOne2manyRow(field.name)"
      >
        {{ adapter.one2manyCreateLabel(field.name, field.label) }}
      </button>
      <span v-if="adapter.one2manySummary(field.name)" class="o2m-summary">{{ adapter.one2manySummary(field.name) }}</span>
    </div>
    <div v-if="adapter.one2manyColumns(field.name).length" class="o2m-table">
      <div class="o2m-header">
        <span
          v-for="column in adapter.one2manyColumns(field.name)"
          :key="`${field.name}-header-${column.name}`"
          class="o2m-header-cell"
        >
          {{ column.label }}
        </span>
      </div>
      <div class="o2m-list">
        <div v-for="row in adapter.visibleOne2manyRows(field.name)" :key="row.key" class="o2m-row">
          <p class="o2m-row-state">{{ adapter.one2manyRowStateLabel(row) }}</p>
          <div class="o2m-fields">
            <label
              v-for="column in adapter.one2manyColumns(field.name)"
              :key="`${row.key}-${column.name}`"
              class="o2m-field"
            >
              <span class="meta">{{ column.label }}</span>
              <input
                v-if="column.ttype === 'boolean'"
                class="input-checkbox"
                type="checkbox"
                :disabled="column.readonly || adapter.busy"
                :checked="Boolean(row.values[column.name])"
                @change="adapter.setOne2manyRowField(field.name, row.key, column, ($event.target as HTMLInputElement).checked)"
              />
              <select
                v-else-if="column.ttype === 'selection'"
                class="input"
                :disabled="column.readonly || adapter.busy"
                :value="String(row.values[column.name] ?? '')"
                @change="adapter.setOne2manyRowField(field.name, row.key, column, ($event.target as HTMLSelectElement).value)"
              >
                <option value="">{{ adapter.selectPlaceholder(column.label) }}</option>
                <option v-for="option in column.selection || []" :key="String(option[0])" :value="String(option[0])">
                  {{ String(option[1]) }}
                </option>
              </select>
              <span
                v-else-if="isDateLikeColumn(column.ttype)"
                :class="['relation-date-input-shell', { 'relation-date-input-shell--has-value': Boolean(adapter.one2manyColumnDisplayValue(column, row.values[column.name])) }]"
              >
                <input
                  :class="['input', 'relation-date-input', { 'relation-date-input--empty': !adapter.one2manyColumnDisplayValue(column, row.values[column.name]) }]"
                  :type="adapter.one2manyColumnInputType(column)"
                  :disabled="column.readonly || adapter.busy"
                  :value="adapter.one2manyColumnDisplayValue(column, row.values[column.name])"
                  :placeholder="column.label"
                  @input="adapter.setOne2manyRowField(field.name, row.key, column, ($event.target as HTMLInputElement).value)"
                />
                <span
                  v-if="adapter.one2manyColumnDisplayValue(column, row.values[column.name])"
                  class="relation-date-display"
                >
                  {{ formatRelationDateDisplay(adapter.one2manyColumnDisplayValue(column, row.values[column.name]), column.ttype) }}
                </span>
                <span
                  v-if="!adapter.one2manyColumnDisplayValue(column, row.values[column.name])"
                  class="relation-date-placeholder"
                >
                  {{ localizedDateColumnPlaceholder(column.ttype) }}
                </span>
              </span>
              <input
                v-else
                class="input"
                :type="adapter.one2manyColumnInputType(column)"
                :disabled="column.readonly || adapter.busy"
                :value="adapter.one2manyColumnDisplayValue(column, row.values[column.name])"
                :placeholder="column.label"
                @input="adapter.setOne2manyRowField(field.name, row.key, column, ($event.target as HTMLInputElement).value)"
              />
            </label>
          </div>
          <button class="ghost" type="button" :disabled="adapter.busy" @click="adapter.removeOne2manyRow(field.name, row.key)">移除</button>
          <p v-if="adapter.showOne2manyErrors && adapter.one2manyRowErrors(field.name, row.key).length" class="o2m-row-error">
            {{ adapter.one2manyRowErrors(field.name, row.key).join('；') }}
          </p>
          <p v-if="adapter.one2manyRowHints(field.name, row).length" class="o2m-row-hint">
            {{ adapter.one2manyRowHints(field.name, row).join('；') }}
          </p>
        </div>
        <div v-if="!adapter.visibleOne2manyRows(field.name).length" class="o2m-empty">
          <strong>暂无{{ field.label }}</strong>
          <span>点击上方按钮添加明细。</span>
        </div>
      </div>
    </div>
    <div v-if="adapter.removedOne2manyRows(field.name).length" class="o2m-removed">
      <p class="meta">已移除 {{ adapter.removedOne2manyRows(field.name).length }} 行</p>
      <div class="chips">
        <button
          v-for="row in adapter.removedOne2manyRows(field.name)"
          :key="`rm-${row.key}`"
          class="chip-btn"
          type="button"
          :disabled="adapter.busy"
          @click="adapter.restoreOne2manyRow(field.name, row.key)"
        >
          撤销移除 · {{ adapter.one2manyRowLabel(field.name, row) }} · 待删除
        </button>
      </div>
    </div>
  </div>
  <input
  v-else
    :value="adapter.inputFieldValue(field.name)"
    class="input"
    :type="adapter.fieldInputType(field.type)"
    :placeholder="adapter.inputPlaceholder(field.label)"
    @input="adapter.setTextField(field.name, ($event.target as HTMLInputElement).value)"
  />
</template>

<script setup lang="ts">
import type { FormSectionFieldSchema } from './formSection.types';
import type { X2ManyRelationRendererProps } from './relationField.types';

const props = defineProps<X2ManyRelationRendererProps>();

function isMany2manyTags(field: FormSectionFieldSchema) {
  return String(field.widget || '').trim().toLowerCase() === 'many2many_tags';
}

function relationIdSet(name: string) {
  return new Set(props.adapter.relationIds(name));
}

function toggleRelationId(name: string, id: number, checked: boolean) {
  const current = relationIdSet(name);
  if (checked) {
    current.add(id);
  } else {
    current.delete(id);
  }
  props.adapter.setRelationIds(name, Array.from(current));
  props.adapter.setRelationKeyword(name, '');
}

function hasTagCreateActions(name: string) {
  const keyword = props.adapter.relationKeyword(name).trim();
  return Boolean(keyword) && (
    props.adapter.canInlineCreateRelation(name) || props.adapter.relationCreateMode(name) === 'page'
  );
}

function hasTagDropdown(name: string) {
  return props.adapter.filteredRelationOptions(name).length > 0 || hasTagCreateActions(name);
}

function commitTagKeyword(name: string) {
  const options = props.adapter.filteredRelationOptions(name);
  if (options.length === 1) {
    toggleRelationId(name, options[0].id, true);
  }
}

function tagColorStyle(color: unknown) {
  const idx = Number(color);
  if (!Number.isFinite(idx)) return {};
  const palette = [
    'var(--sc-app-muted-bg)',
    'var(--sc-app-danger-bg)',
    'var(--sc-app-warning-bg)',
    'var(--sc-app-info-bg)',
    'var(--sc-app-success-bg)',
    'var(--sc-app-subtle-bg)',
    'var(--sc-app-hover-bg)',
    'var(--sc-app-info-bg)',
    'var(--sc-app-muted-bg)',
    'var(--sc-app-warning-bg)',
    'var(--sc-app-danger-bg)',
    'var(--sc-app-border)',
  ];
  const bg = palette[Math.abs(Math.trunc(idx)) % palette.length];
  return { '--tag-bg': bg };
}

function isDateLikeColumn(type: unknown) {
  return ['date', 'datetime'].includes(String(type || '').trim().toLowerCase());
}

function localizedDateColumnPlaceholder(type: unknown) {
  return String(type || '').trim().toLowerCase() === 'datetime' ? '请选择日期时间' : '请选择日期';
}

function formatRelationDateDisplay(value: unknown, type: unknown) {
  const text = String(value ?? '').trim();
  if (!text) return '';
  const match = text.match(/^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2}))?)?/);
  if (!match) return text;
  const [, year, month, day, hour = '', minute = ''] = match;
  if (String(type || '').trim().toLowerCase() === 'datetime' && hour) {
    return `${year}-${month}-${day} ${minute ? `${hour}:${minute}` : `${hour}:00`}`;
  }
  return `${year}-${month}-${day}`;
}
</script>

<style scoped>
.relation-editor {
  display: grid;
  gap: 6px;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.relation-tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.relation-tag-picker,
.relation-select-editor {
  display: grid;
  gap: 8px;
}

.relation-tags-control {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  min-height: 40px;
  padding: 5px 8px;
  border: 1px solid var(--sc-app-border-strong);
  border-radius: 6px;
  background: var(--sc-app-input-bg);
}

.relation-tags-input {
  flex: 1 1 140px;
  min-width: 120px;
  border: 0;
  outline: none;
  color: var(--sc-app-text-primary);
  font-size: 14px;
  line-height: 1.4;
}

.relation-tag-dropdown {
  position: absolute;
  z-index: 20;
  top: calc(100% + 2px);
  left: 0;
  right: 0;
  display: none;
  max-height: 260px;
  overflow: auto;
  border: 1px solid var(--sc-app-border-strong);
  border-radius: 6px;
  background: var(--sc-app-panel);
  box-shadow: 0 12px 28px var(--sc-app-shadow);
}

.relation-tags-control:focus-within .relation-tag-dropdown {
  display: grid;
}

.relation-tag-option,
.relation-tag-action,
.relation-tag-hint {
  display: flex;
  align-items: center;
  gap: 7px;
  min-height: 32px;
  border: 0;
  border-bottom: 1px solid var(--sc-app-border);
  background: var(--sc-app-panel);
  padding: 6px 10px;
  color: var(--sc-app-text-primary);
  text-align: left;
  cursor: pointer;
  font-size: 12px;
  line-height: 1.25;
}

.relation-tag-option:hover {
  background: var(--sc-app-hover-bg);
}

.relation-tag-actions {
  display: grid;
  border-top: 1px solid var(--sc-app-border);
}

.relation-tag-action {
  color: var(--sc-semantic-surface-interactive);
}

.relation-tag-hint {
  color: var(--sc-app-text-secondary);
  cursor: default;
}

.relation-tag-action:hover {
  background: var(--sc-app-hover-bg);
}

.relation-tag-swatch {
  flex: 0 0 auto;
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: var(--tag-bg, var(--sc-app-muted-bg));
  border: 1px solid var(--sc-app-border);
}

.relation-choice-panel {
  border: 1px solid var(--sc-app-border-strong);
  border-radius: 6px;
  background: var(--sc-app-panel);
}

.relation-choice-panel > summary {
  min-height: 32px;
  padding: 7px 10px;
  color: var(--sc-app-text-primary);
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
}

.relation-choice-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px 10px;
  max-height: 220px;
  overflow: auto;
  padding: 0 8px 8px;
}

.relation-choice {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  min-height: 28px;
  padding: 5px 8px;
  border: 1px solid var(--sc-app-border-strong);
  border-radius: 6px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
  font-size: 12px;
  line-height: 1.35;
}

.relation-choice-check {
  margin-top: 1px;
  flex: 0 0 auto;
}

.relation-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  max-width: 100%;
  min-height: 24px;
  border: 0;
  padding: 3px 8px;
  border-radius: 4px;
  background: var(--tag-bg, var(--sc-app-muted-bg));
  color: var(--sc-app-text-primary);
  font-size: 12px;
  line-height: 1.35;
  cursor: pointer;
}

.relation-tag:hover {
  background: var(--sc-app-info-bg);
}

.chip-btn {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 999px;
  border: 1px solid var(--sc-app-border-strong);
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
  cursor: pointer;
}

.meta {
  margin: 1px 0;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.required {
  color: var(--sc-app-danger-text);
  margin-left: 2px;
}

.o2m-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.o2m-summary {
  font-size: 12px;
  color: var(--sc-app-text-secondary);
}

.o2m-table {
  display: grid;
  min-width: 0;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-panel);
  overflow: hidden;
}

.o2m-header {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 1px;
  background: var(--sc-app-border);
}

.o2m-header-cell {
  min-height: 28px;
  padding: 6px 8px;
  background: var(--sc-app-muted-bg);
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  line-height: 1.35;
  font-weight: 600;
}

.o2m-list {
  display: grid;
  gap: 0;
  min-width: 0;
}

.o2m-row {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
  padding: 8px;
  border-top: 1px solid var(--sc-app-border);
}

.o2m-row-state {
  margin: 0;
  font-size: 12px;
  color: var(--sc-app-text-secondary);
  white-space: nowrap;
}

.o2m-fields {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 6px;
  min-width: 0;
}

.o2m-field {
  display: grid;
  min-width: 0;
}

.o2m-field .meta {
  display: none;
}

.o2m-removed {
  display: grid;
  gap: 4px;
}

.o2m-row-error {
  grid-column: 1 / -1;
  margin: 0;
  color: var(--sc-app-danger-text);
  font-size: 12px;
}

.o2m-row-hint {
  grid-column: 1 / -1;
  margin: 0;
  color: var(--sc-app-warning-text);
  font-size: 12px;
}

.o2m-empty {
  margin: 0;
  min-height: 72px;
  display: grid;
  align-items: center;
  justify-items: center;
  gap: 4px;
  padding: 16px 12px;
  border-top: 1px solid var(--sc-app-border);
  background: var(--sc-app-panel-muted);
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  line-height: 1.4;
  text-align: center;
}

.o2m-empty strong {
  color: var(--sc-app-text-primary);
  font-size: 13px;
  line-height: 1.35;
}

.o2m-empty span {
  color: var(--sc-app-text-secondary);
}

.relation-search {
  font-size: 14px;
}

.input {
  border: 1px solid var(--sc-app-border-strong);
  border-radius: 8px;
  padding: 8px 12px;
  height: 40px;
  min-height: 40px;
  width: 100%;
  min-width: 0;
  font-size: 14px;
  line-height: 1.35;
  color: var(--sc-app-text-primary);
  background: var(--sc-app-input-bg);
  box-sizing: border-box;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease;
}

.input::placeholder {
  color: var(--sc-app-text-secondary);
}

.input:focus {
  outline: none;
  border-color: var(--sc-semantic-surface-interactive);
  box-shadow: 0 0 0 3px var(--sc-app-focus-ring);
}

.input:disabled {
  color: var(--sc-app-text-secondary);
  background: var(--sc-app-muted-bg);
  cursor: not-allowed;
}

.relation-date-input-shell {
  position: relative;
  display: grid;
  min-width: 0;
}

.relation-date-input-shell--has-value .relation-date-input {
  color: transparent;
}

.relation-date-input-shell--has-value:focus-within .relation-date-input {
  color: var(--sc-app-text-primary);
}

.relation-date-input[type='date'],
.relation-date-input[type='datetime-local'] {
  padding-right: 34px;
}

.relation-date-display {
  position: absolute;
  left: 10px;
  right: 34px;
  top: 50%;
  z-index: 1;
  overflow: hidden;
  color: var(--sc-app-text-primary);
  font-size: 13px;
  line-height: 1.35;
  pointer-events: none;
  text-overflow: ellipsis;
  transform: translateY(-50%);
  white-space: nowrap;
}

.relation-date-input-shell--has-value:focus-within .relation-date-display {
  opacity: 0;
}

.relation-date-input--empty::-webkit-datetime-edit {
  color: transparent;
}

.relation-date-input--empty:focus::-webkit-datetime-edit {
  color: var(--sc-app-text-primary);
}

.relation-date-placeholder {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  max-width: calc(100% - 42px);
  color: var(--sc-app-text-secondary);
  font-size: 13px;
  line-height: 1;
  pointer-events: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.relation-date-input-shell:focus-within .relation-date-placeholder {
  display: none;
}

select.input {
  appearance: none;
  background-image: linear-gradient(45deg, transparent 50%, var(--sc-app-text-secondary) 50%), linear-gradient(135deg, var(--sc-app-text-secondary) 50%, transparent 50%);
  background-position: calc(100% - 16px) calc(50% - 2px), calc(100% - 11px) calc(50% - 2px);
  background-size: 5px 5px, 5px 5px;
  background-repeat: no-repeat;
  padding-right: 32px;
}

@media (max-width: 760px) {
  .o2m-header {
    display: none;
  }

  .o2m-row {
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: start;
  }

  .o2m-row-state {
    grid-column: 1 / -1;
  }

  .o2m-fields {
    grid-template-columns: 1fr;
  }

  .o2m-field {
    gap: 4px;
  }

  .o2m-field .meta {
    display: block;
  }
}

.ghost {
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid var(--sc-app-border);
  background: var(--sc-app-panel);
  font-weight: 500;
  color: var(--sc-semantic-text-muted);
}
</style>

<template>
  <div v-if="field.type === 'many2many'" class="relation-editor">
    <div v-if="isMany2manyTags(field)" class="relation-tag-picker">
      <div class="relation-selected-block">
        <div class="relation-selected-title">已选{{ field.label }}</div>
        <div v-if="adapter.selectedRelationOptions(field.name).length" class="relation-tag-list">
          <span
            v-for="option in adapter.selectedRelationOptions(field.name)"
            :key="`${field.name}-tag-${option.id}`"
            class="relation-tag"
          >
            {{ option.label }}
          </span>
        </div>
        <div v-else class="relation-empty">未选择</div>
      </div>
      <details class="relation-choice-panel">
        <summary>调整{{ field.label }}</summary>
        <div class="relation-choice-list">
          <label
            v-for="option in adapter.filteredRelationOptions(field.name)"
            :key="`${field.name}-choice-${option.id}`"
            class="relation-choice"
          >
            <input
              class="relation-choice-check"
              type="checkbox"
              :checked="relationIdSet(field.name).has(option.id)"
              :disabled="adapter.busy"
              @change="toggleRelationId(field.name, option.id, ($event.target as HTMLInputElement).checked)"
            />
            <span>{{ option.label }}</span>
          </label>
        </div>
      </details>
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
        {{ adapter.one2manyCreateLabel(field.name) }}
      </button>
      <span v-if="adapter.one2manySummary(field.name)" class="o2m-summary">{{ adapter.one2manySummary(field.name) }}</span>
    </div>
    <div v-if="adapter.one2manyColumns(field.name).length" class="o2m-header">
      <span
        v-for="column in adapter.one2manyColumns(field.name)"
        :key="`${field.name}-header-${column.name}`"
        class="o2m-header-cell"
      >
        {{ column.label }}<span v-if="column.required" class="required">*</span>
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
            <span class="meta">{{ column.label }}<span v-if="column.required" class="required">*</span></span>
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
import type { RelationFallbackRendererProps } from './relationFallback.types';

const props = defineProps<RelationFallbackRendererProps>();

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

.relation-selected-block {
  display: grid;
  gap: 6px;
  padding: 8px;
  border: 1px solid #d7deea;
  border-radius: 6px;
  background: #f8fafc;
}

.relation-selected-title {
  color: #475569;
  font-size: 12px;
  font-weight: 600;
}

.relation-empty {
  color: #94a3b8;
  font-size: 12px;
}

.relation-choice-panel {
  border: 1px solid #d7deea;
  border-radius: 6px;
  background: #fff;
}

.relation-choice-panel > summary {
  min-height: 32px;
  padding: 7px 10px;
  color: #334155;
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
  border: 1px solid #d7deea;
  border-radius: 6px;
  background: #fff;
  color: #334155;
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
  max-width: 100%;
  min-height: 24px;
  padding: 3px 8px;
  border-radius: 4px;
  background: #eef2f7;
  color: #334155;
  font-size: 12px;
  line-height: 1.35;
}

.chip-btn {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #fff;
  cursor: pointer;
}

.meta {
  margin: 1px 0;
  color: #64748b;
  font-size: 12px;
}

.required {
  color: #b91c1c;
  margin-left: 2px;
}

.o2m-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.o2m-summary {
  font-size: 12px;
  color: #475569;
}

.o2m-header {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 1px;
  border: 1px solid #d8dee9;
  background: #d8dee9;
  overflow: hidden;
}

.o2m-header-cell {
  min-height: 28px;
  padding: 6px 8px;
  background: #f8fafc;
  color: #475569;
  font-size: 12px;
  line-height: 1.35;
  font-weight: 600;
}

.o2m-list {
  display: grid;
  gap: 6px;
}

.o2m-row {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
  padding: 4px 0;
  border-bottom: 1px solid #eef2f7;
}

.o2m-row-state {
  margin: 0;
  font-size: 12px;
  color: #64748b;
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
  color: #b91c1c;
  font-size: 12px;
}

.o2m-row-hint {
  grid-column: 1 / -1;
  margin: 0;
  color: #92400e;
  font-size: 12px;
}

.relation-search {
  font-size: 14px;
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

.input:disabled {
  color: #64748b;
  background: #f8fafc;
  cursor: not-allowed;
}

select.input {
  appearance: none;
  background-image: linear-gradient(45deg, transparent 50%, #64748b 50%), linear-gradient(135deg, #64748b 50%, transparent 50%);
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
  border: 1px solid #e5e7eb;
  background: #fff;
  font-weight: 500;
  color: #6b7280;
}
</style>

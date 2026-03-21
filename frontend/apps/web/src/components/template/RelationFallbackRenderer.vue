<template>
  <div v-if="field.type === 'many2many'" class="relation-editor">
    <input
      class="input relation-search"
      type="text"
      :value="adapter.relationKeyword(field.name)"
      placeholder="搜索并多选..."
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
  <div v-else-if="field.type === 'one2many'" class="relation-editor">
    <div class="o2m-toolbar">
      <button class="chip-btn" type="button" :disabled="adapter.busy" @click="adapter.addOne2manyRow(field.name)">+ 新增行</button>
      <span v-if="adapter.one2manySummary(field.name)" class="o2m-summary">{{ adapter.one2manySummary(field.name) }}</span>
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
              :checked="Boolean(row.values[column.name])"
              @change="adapter.setOne2manyRowField(field.name, row.key, column, ($event.target as HTMLInputElement).checked)"
            />
            <select
              v-else-if="column.ttype === 'selection'"
              class="input"
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
import type { RelationFallbackRendererProps } from './relationFallback.types';

defineProps<RelationFallbackRendererProps>();
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

.o2m-list {
  display: grid;
  gap: 6px;
}

.o2m-row {
  display: grid;
  grid-template-columns: minmax(120px, 1fr) auto;
  gap: 6px;
  align-items: center;
}

.o2m-row-state {
  grid-column: 1 / -1;
  margin: 0;
  font-size: 12px;
  color: #475569;
}

.o2m-fields {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 6px;
}

.o2m-field {
  display: grid;
  gap: 4px;
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
  padding-right: 30px;
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

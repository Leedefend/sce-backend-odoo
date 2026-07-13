<template>
  <div
    v-if="dialog.open"
    class="relation-dialog-backdrop"
    role="dialog"
    aria-modal="true"
    @keydown.esc="$emit('close')"
  >
    <section class="relation-dialog">
      <header class="relation-dialog-head">
        <h3>{{ dialog.title }}</h3>
        <button
          class="relation-dialog-close"
          type="button"
          :disabled="busy"
          :aria-label="dialog.labels.close || '关闭'"
          @click="$emit('close')"
        >
          x
        </button>
      </header>
      <div class="relation-dialog-search">
        <input
          ref="searchInputRef"
          class="input"
          type="text"
          :value="dialog.keyword"
          :placeholder="dialog.labels.search_placeholder || '输入名称搜索'"
          @input="$emit('keyword-change', inputValue($event))"
          @keydown.enter.prevent="$emit('search')"
        />
        <button class="chip-btn" type="button" :disabled="dialog.loading" @click="$emit('search')">
          {{ dialog.labels.search || '搜索' }}
        </button>
      </div>
      <p v-if="dialog.error" class="validation-error">{{ dialog.error }}</p>
      <div class="relation-dialog-table-wrap">
        <table class="relation-dialog-table">
          <thead>
            <tr>
              <th class="relation-dialog-select-col"></th>
              <th v-for="column in dialog.columns" :key="column.name">
                {{ column.label }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in dialog.rows"
              :key="`rel-${row.id}`"
              :class="{ 'relation-dialog-row--active': dialog.selectedId === row.id }"
              @click="$emit('select-row', row)"
              @dblclick="$emit('confirm', row)"
            >
              <td class="relation-dialog-select-col">
                <input
                  type="radio"
                  name="relation-search-select"
                  :checked="dialog.selectedId === row.id"
                  @change="$emit('select-row', row)"
                />
              </td>
              <td v-for="column in dialog.columns" :key="`${row.id}-${column.name}`">
                {{ relationSearchCell(row, column.name) }}
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="!dialog.loading && !dialog.rows.length" class="relation-dialog-empty">
          {{ dialog.labels.empty || '未找到匹配记录' }}
        </p>
      </div>
      <footer class="relation-dialog-footer">
        <span class="relation-dialog-count">{{ recordCountLabel }}</span>
        <span class="relation-dialog-footer-spacer"></span>
        <button
          class="primary"
          type="button"
          :disabled="busy || dialog.loading || !dialog.selectedId"
          @click="$emit('confirm')"
        >
          {{ dialog.labels.select || '选择' }}
        </button>
        <button
          v-if="dialog.createMode !== 'none'"
          class="ghost"
          type="button"
          :disabled="busy || dialog.loading"
          @click="$emit('create')"
        >
          {{ dialog.labels.create || '新建' }}
        </button>
        <button class="ghost" type="button" :disabled="busy" @click="$emit('close')">
          {{ dialog.labels.cancel || '取消' }}
        </button>
      </footer>
    </section>
  </div>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue';
import type { RelationOption, RelationSearchColumn, RelationSearchRow, RelationUiLabels } from './types';

export type RelationSearchDialogState = {
  open: boolean;
  fieldName: string;
  title: string;
  keyword: string;
  loading: boolean;
  error: string;
  options: RelationOption[];
  rows: RelationSearchRow[];
  columns: RelationSearchColumn[];
  selectedId: number | null;
  createMode: 'none' | 'quick' | 'page';
  labels: RelationUiLabels;
};

const props = defineProps<{
  dialog: RelationSearchDialogState;
  busy: boolean;
  recordCountLabel: string;
}>();

defineEmits<{
  close: [];
  search: [];
  create: [];
  confirm: [row?: RelationSearchRow];
  'select-row': [row: RelationSearchRow];
  'keyword-change': [keyword: string];
}>();

const searchInputRef = ref<HTMLInputElement | null>(null);

watch(
  () => props.dialog.open,
  async (open) => {
    if (!open) return;
    await nextTick();
    searchInputRef.value?.focus();
  },
);

function inputValue(event: Event) {
  return String((event.target as HTMLInputElement).value || '');
}

function relationSearchCell(row: RelationSearchRow, columnName: string) {
  const value = row.values[columnName];
  if (value === null || value === undefined || value === false) return '';
  if (Array.isArray(value)) {
    if (value.length >= 2) return String(value[1] ?? '');
    return value.map((item) => String(item ?? '')).filter(Boolean).join(', ');
  }
  if (typeof value === 'object') {
    const rec = value as Record<string, unknown>;
    return String(rec.display_name || rec.name || rec.id || '');
  }
  if (typeof value === 'boolean') return value ? '是' : '否';
  return String(value);
}
</script>

<style scoped src="./RelationSearchDialog.css"></style>

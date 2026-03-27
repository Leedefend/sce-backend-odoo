<template>
  <section class="toolbar">
    <div class="search">
      <input
        type="search"
        placeholder="搜索关键字"
        :value="inputValue"
        :disabled="loading"
        @input="onSearchInput"
        @compositionstart="onCompositionStart"
        @compositionend="onCompositionEnd"
        @keydown.enter.prevent="submitSearch"
      />
      <button
        type="button"
        class="search-btn"
        :disabled="loading"
        @click="submitSearch"
      >
        搜索
      </button>
    </div>
    <div class="filters">
      <button
        type="button"
        class="filter"
        :class="{ active: filterValue === 'all' }"
        :disabled="loading"
        @click="onFilter('all')"
      >
        全部
      </button>
      <button
        type="button"
        class="filter"
        :class="{ active: filterValue === 'active' }"
        :disabled="loading"
        @click="onFilter('active')"
      >
        在办
      </button>
      <button
        type="button"
        class="filter"
        :class="{ active: filterValue === 'archived' }"
        :disabled="loading"
        @click="onFilter('archived')"
      >
        已归档
      </button>
    </div>
    <div class="sort">
      <span class="label">排序</span>
      <div class="sort-options">
        <button
          v-for="opt in sortOptions"
          :key="opt.value"
          type="button"
          class="sort-option"
          :class="{ active: opt.value === sortValue }"
          @click="onSort(opt.value)"
        >
          {{ opt.label }}
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

const props = defineProps<{
  loading: boolean;
  searchTerm: string;
  sortOptions: Array<{ label: string; value: string }>;
  sortValue: string;
  filterValue: 'all' | 'active' | 'archived';
  onSearch: (value: string) => void;
  onSort: (value: string) => void;
  onFilter: (value: 'all' | 'active' | 'archived') => void;
}>();

const inputValue = ref(props.searchTerm || '');
const isComposing = ref(false);

watch(
  () => props.searchTerm,
  (next) => {
    if (isComposing.value) return;
    inputValue.value = next || '';
  },
);

function onSearchInput(event: Event) {
  const target = event.target as HTMLInputElement;
  inputValue.value = target.value;
}

function onCompositionStart() {
  isComposing.value = true;
}

function onCompositionEnd(event: CompositionEvent) {
  const target = event.target as HTMLInputElement | null;
  inputValue.value = target?.value || inputValue.value;
  isComposing.value = false;
}

function submitSearch() {
  if (isComposing.value) return;
  props.onSearch(inputValue.value || '');
}
</script>

<style scoped>
.toolbar {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 12px;
  background: white;
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 14px 24px rgba(15, 23, 42, 0.08);
  align-items: center;
}

.search input {
  width: 100%;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid rgba(15, 23, 42, 0.1);
  background: #f8fafc;
}

.search {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  align-items: center;
}

.search-btn {
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  background: #111827;
  color: #f8fafc;
  cursor: pointer;
}

.search-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.filters {
  display: flex;
  gap: 8px;
}

.filter {
  border: 1px solid transparent;
  padding: 6px 10px;
  border-radius: 999px;
  background: #f1f5f9;
  font-size: 12px;
  color: #475569;
  cursor: pointer;
}

.filter.active {
  border-color: #111827;
  background: #111827;
  color: #f8fafc;
}

.sort {
  display: grid;
  justify-items: end;
  gap: 4px;
}

.sort .label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #94a3b8;
}

.sort-options {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.sort-option {
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  background: #f8fafc;
  font-size: 12px;
  color: #475569;
}

.sort-option.active {
  background: #111827;
  color: #f8fafc;
}
</style>

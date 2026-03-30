<template>
  <section class="toolbar">
    <div class="search">
      <input
        type="search"
        :placeholder="searchPlaceholderText"
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
    <div v-if="showLegacyStatusFilters" class="filters">
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
    <div v-if="showSortBlock" class="sort">
      <span class="label">排序</span>
      <div v-if="showSortControls" class="sort-options">
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
      <div v-else class="sort-summary">
        <span class="sort-current">{{ sortLabelText }}</span>
        <span v-if="sortSourceLabelText" class="sort-source">{{ sortSourceLabelText }}</span>
      </div>
    </div>
  </section>
  <section v-if="hasContractControls" class="contract-toolbar">
    <div v-if="activeStateChips.length" class="contract-group">
      <span class="contract-group__label">当前条件（{{ activeStateChips.length }}）</span>
      <div class="contract-group__chips">
        <span
          v-for="chip in activeStateChips"
          :key="`active-${chip.key}`"
          class="contract-chip static active-summary"
        >
          {{ chip.label }}
        </span>
        <button
          type="button"
          class="contract-chip ghost"
          :disabled="loading"
          @click="resetActiveConditions"
        >
          重置条件
        </button>
      </div>
    </div>
    <div v-if="routePresetLabelText" class="contract-group">
      <span class="contract-group__label">推荐筛选</span>
      <div class="contract-group__chips">
        <span class="contract-chip static">{{ routePresetChipLabel }}</span>
        <button
          type="button"
          class="contract-chip ghost"
          :disabled="loading"
          @click="onClearRoutePreset?.()"
        >
          清除推荐
        </button>
      </div>
    </div>
    <div v-if="searchModeLabelText" class="contract-group">
      <span class="contract-group__label">搜索模式（原生）</span>
      <div class="contract-group__chips">
        <span class="contract-chip static">{{ searchModeLabelText }}</span>
      </div>
    </div>
    <div v-if="searchableFieldOptions.length" class="contract-group">
      <span class="contract-group__label">可搜索字段（{{ searchableFieldCountText }}）</span>
      <div class="contract-group__chips">
        <span
          v-for="chip in searchableFieldOptions"
          :key="`searchable-${chip.key}`"
          class="contract-chip static"
        >
          {{ chip.label }}
        </span>
      </div>
    </div>
    <div v-if="quickFilters.length" class="contract-group">
      <span class="contract-group__label">快速筛选（{{ quickFilters.length }}）</span>
      <div class="contract-group__chips">
        <button
          v-for="chip in quickFilters"
          :key="`quick-${chip.key}`"
          type="button"
          class="contract-chip"
          :class="{ active: activeContractFilterKey === chip.key }"
          :disabled="loading"
          @click="onApplyContractFilter?.(chip.key)"
        >
          {{ chip.label }}
        </button>
        <button
          v-if="activeContractFilterKey"
          type="button"
          class="contract-chip ghost"
          :disabled="loading"
          @click="onClearContractFilter?.()"
        >
          清除
        </button>
      </div>
    </div>
    <div v-if="savedFilters.length" class="contract-group">
      <span class="contract-group__label">已保存筛选（{{ savedFilterCountText }}）</span>
      <div class="contract-group__chips">
        <button
          v-for="chip in savedFilters"
          :key="`saved-${chip.key}`"
          type="button"
          class="contract-chip"
          :class="{ active: activeSavedFilterKey === chip.key }"
          :disabled="loading"
          @click="onApplySavedFilter?.(chip.key)"
        >
          {{ chip.label }}
        </button>
        <button
          v-if="activeSavedFilterKey"
          type="button"
          class="contract-chip ghost"
          :disabled="loading"
          @click="onClearSavedFilter?.()"
        >
          清除
        </button>
      </div>
    </div>
    <div v-if="groupByOptions.length" class="contract-group">
      <span class="contract-group__label">分组查看（{{ groupByCountText }}）</span>
      <div class="contract-group__chips">
        <button
          v-for="chip in groupByOptions"
          :key="`group-${chip.key}`"
          type="button"
          class="contract-chip"
          :class="{ active: activeGroupByField === chip.key }"
          :disabled="loading"
          @click="onApplyGroupBy?.(chip.key)"
        >
          {{ chip.label }}
        </button>
        <button
          v-if="activeGroupByField"
          type="button"
          class="contract-chip ghost"
          :disabled="loading"
          @click="onClearGroupBy?.()"
        >
          清除
        </button>
      </div>
    </div>
    <div v-if="searchPanelOptions.length" class="contract-group">
      <span class="contract-group__label">分面维度（{{ searchPanelCountText }}）</span>
      <div class="contract-group__chips">
        <span
          v-for="chip in searchPanelOptions"
          :key="`searchpanel-${chip.key}`"
          class="contract-chip static"
        >
          {{ chip.label }}
        </span>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

type ToolbarChip = { key: string; label: string };

const props = defineProps<{
  loading: boolean;
  searchTerm: string;
  searchPlaceholder?: string;
  sortOptions?: Array<{ label: string; value: string }>;
  sortValue?: string;
  sortLabel?: string;
  sortSourceLabel?: string;
  filterValue: 'all' | 'active' | 'archived';
  onSearch: (value: string) => void;
  onSort: (value: string) => void;
  onFilter: (value: 'all' | 'active' | 'archived') => void;
  quickFilters?: ToolbarChip[];
  savedFilters?: ToolbarChip[];
  groupByOptions?: ToolbarChip[];
  searchPanelOptions?: ToolbarChip[];
  searchableFieldOptions?: ToolbarChip[];
  searchableFieldTotalCount?: number;
  searchableFieldCountLabel?: string;
  savedFilterCountLabel?: string;
  groupByCountLabel?: string;
  searchPanelCountLabel?: string;
  routePresetLabel?: string;
  routePresetSource?: string;
  searchModeLabel?: string;
  activeContractFilterKey?: string;
  activeSavedFilterKey?: string;
  activeGroupByField?: string;
  onApplyContractFilter?: (key: string) => void;
  onClearContractFilter?: () => void;
  onApplySavedFilter?: (key: string) => void;
  onClearSavedFilter?: () => void;
  onApplyGroupBy?: (key: string) => void;
  onClearGroupBy?: () => void;
  onClearRoutePreset?: () => void;
}>();

const inputValue = ref(props.searchTerm || '');
const isComposing = ref(false);
const sortOptions = computed(() => Array.isArray(props.sortOptions) ? props.sortOptions : []);
const quickFilters = computed(() => Array.isArray(props.quickFilters) ? props.quickFilters : []);
const savedFilters = computed(() => Array.isArray(props.savedFilters) ? props.savedFilters : []);
const groupByOptions = computed(() => Array.isArray(props.groupByOptions) ? props.groupByOptions : []);
const searchPanelOptions = computed(() => Array.isArray(props.searchPanelOptions) ? props.searchPanelOptions : []);
const searchableFieldOptions = computed(() => Array.isArray(props.searchableFieldOptions) ? props.searchableFieldOptions : []);
const routePresetLabelText = computed(() => String(props.routePresetLabel || '').trim());
const routePresetSourceText = computed(() => {
  const raw = String(props.routePresetSource || '').trim().toLowerCase();
  if (!raw) return '';
  if (raw === 'scene' || raw === 'route' || raw === 'query' || raw === 'url') return '';
  if (raw === 'menu') return '菜单';
  if (raw === 'recommended' || raw === 'preset') return '系统推荐';
  return raw.replace(/[_-]+/g, ' ');
});
const routePresetChipLabel = computed(() => {
  if (!routePresetLabelText.value) return '';
  if (!routePresetSourceText.value) return routePresetLabelText.value;
  return `${routePresetLabelText.value}（来源：${routePresetSourceText.value}）`;
});
const savedFilterCountText = computed(() => String(props.savedFilterCountLabel || '').trim() || String(savedFilters.value.length));
const groupByCountText = computed(() => String(props.groupByCountLabel || '').trim() || String(groupByOptions.value.length));
const searchPanelCountText = computed(() => String(props.searchPanelCountLabel || '').trim() || String(searchPanelOptions.value.length));
const searchableFieldCountText = computed(() => {
  const label = String(props.searchableFieldCountLabel || '').trim();
  if (label) return label;
  const total = Number(props.searchableFieldTotalCount || 0);
  if (Number.isFinite(total) && total > 0) return String(total);
  return String(searchableFieldOptions.value.length);
});
const searchModeLabelText = computed(() => String(props.searchModeLabel || '').trim());
const activeStateChips = computed(() => {
  const chips: ToolbarChip[] = [];
  if (routePresetLabelText.value) {
    chips.push({ key: `preset:${routePresetLabelText.value}`, label: `推荐筛选：${routePresetChipLabel.value}` });
  }
  const searchText = String(props.searchTerm || '').trim();
  if (searchText) {
    chips.push({ key: `search:${searchText}`, label: `搜索：${searchText}` });
  }
  const activeQuick = quickFilters.value.find((item) => item.key === String(props.activeContractFilterKey || '').trim());
  if (activeQuick) {
    chips.push({ key: `quick:${activeQuick.key}`, label: `快速筛选：${activeQuick.label}` });
  }
  const activeSaved = savedFilters.value.find((item) => item.key === String(props.activeSavedFilterKey || '').trim());
  if (activeSaved) {
    chips.push({ key: `saved:${activeSaved.key}`, label: `已保存筛选：${activeSaved.label}` });
  }
  const activeGroup = groupByOptions.value.find((item) => item.key === String(props.activeGroupByField || '').trim());
  if (activeGroup) {
    chips.push({ key: `group:${activeGroup.key}`, label: `分组：${activeGroup.label}` });
  }
  const sortLabel = String(props.sortLabel || '').trim();
  const sortSource = String(props.sortSourceLabel || '').trim();
  if (sortLabel) {
    const prefix = sortSource || '排序';
    chips.push({ key: `sort:${sortLabel}`, label: `${prefix}：${sortLabel}` });
  }
  return chips;
});
const showSortControls = computed(() => sortOptions.value.length > 0);
const sortLabelText = computed(() => String(props.sortLabel || '').trim() || '默认');
const sortSourceLabelText = computed(() => String(props.sortSourceLabel || '').trim());
const showSortBlock = computed(() => showSortControls.value || Boolean(sortLabelText.value));
const searchPlaceholderText = computed(() => String(props.searchPlaceholder || '').trim() || '搜索关键字');
const hasContractControls = computed(() =>
  quickFilters.value.length > 0
  || savedFilters.value.length > 0
  || groupByOptions.value.length > 0
  || searchPanelOptions.value.length > 0
  || searchableFieldOptions.value.length > 0
  || Boolean(searchModeLabelText.value),
);
const showLegacyStatusFilters = computed(() => !hasContractControls.value);

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

function resetActiveConditions() {
  if (isComposing.value) return;
  inputValue.value = '';
  props.onSearch('');
  props.onClearRoutePreset?.();
  props.onClearContractFilter?.();
  props.onClearSavedFilter?.();
  props.onClearGroupBy?.();
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

.sort-summary {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sort-current {
  color: #475569;
  font-size: 13px;
  font-weight: 600;
}

.sort-source {
  color: #94a3b8;
  font-size: 12px;
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

.contract-toolbar {
  display: grid;
  gap: 10px;
  margin-top: 10px;
  background: white;
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 14px 24px rgba(15, 23, 42, 0.06);
}

.contract-group {
  display: grid;
  gap: 6px;
}

.contract-group__label {
  font-size: 12px;
  font-weight: 700;
  color: #475569;
}

.contract-group__chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.contract-chip {
  border: 1px solid rgba(15, 23, 42, 0.12);
  padding: 6px 10px;
  border-radius: 999px;
  background: #f8fafc;
  font-size: 12px;
  color: #334155;
  cursor: pointer;
}

.contract-chip.active {
  background: #111827;
  border-color: #111827;
  color: #f8fafc;
}

.contract-chip.ghost {
  background: #fff;
}

.contract-chip.static {
  cursor: default;
  background: #eef2ff;
  border-color: rgba(79, 70, 229, 0.16);
  color: #4338ca;
}
</style>

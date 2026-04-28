<template>
  <section ref="toolbarRoot" class="action-toolbar">
    <div v-if="showViewSwitch" class="toolbar-section view-switch">
      <p class="contract-label">{{ viewLabel }}</p>
      <div class="contract-chips">
        <button
          v-for="mode in viewModes"
          :key="`view-mode-${mode}`"
          class="contract-chip"
          :class="{ active: currentViewMode === mode }"
          :disabled="loading"
          @click="$emit('switch-view', mode)"
        >
          {{ viewModeLabels[mode] || mode }}
        </button>
      </div>
    </div>

    <div class="native-search">
      <div class="native-searchbox">
        <button
          v-if="activeFilterChip"
          class="search-facet"
          type="button"
          :disabled="loading"
          @click="$emit('clear-filter')"
        >
          <span>{{ activeFilterChip.label }}</span>
          <span class="facet-remove">{{ clearSymbol }}</span>
        </button>
        <button
          v-if="activeSavedFilterChip"
          class="search-facet"
          type="button"
          :disabled="loading"
          @click="$emit('clear-saved-filter')"
        >
          <span>{{ activeSavedFilterChip.label }}</span>
          <span class="facet-remove">{{ clearSymbol }}</span>
        </button>
        <button
          v-if="activeGroupChip"
          class="search-facet"
          type="button"
          :disabled="loading"
          @click="$emit('clear-group')"
        >
          <span>{{ activeGroupChip.label }}</span>
          <span class="facet-remove">{{ clearSymbol }}</span>
        </button>
        <input
          type="search"
          :value="searchValue"
          :disabled="loading"
          :placeholder="searchPlaceholder"
          @compositionstart="$emit('search-composition-start')"
          @compositionend="$emit('search-composition-end', $event)"
          @input="$emit('search-input', $event)"
          @keydown.enter.prevent="$emit('search-submit')"
          @keydown.esc="searchMenuOpen = false"
        />
        <button
          v-if="searchValue"
          class="toolbar-search-clear"
          type="button"
          :disabled="loading"
          @click="$emit('clear-search')"
        >
          {{ clearLabel }}
        </button>
        <button
          class="search-menu-toggle"
          type="button"
          :class="{ active: searchMenuOpen }"
          :disabled="loading || !hasSearchMenu"
          aria-label="展开搜索菜单"
          @click="searchMenuOpen = !searchMenuOpen"
        >
          <span class="search-menu-caret">{{ searchMenuOpen ? '▴' : '▾' }}</span>
        </button>
      </div>
      <div v-if="searchMenuOpen && hasSearchMenu" class="search-dropdown">
        <section v-if="showFilterColumn" class="search-dropdown-section">
          <p class="search-dropdown-title">{{ filterLabel }}</p>
          <div class="search-dropdown-items">
            <button
              v-for="chip in allFilterChips"
              :key="`filter-${chip.key}`"
              class="search-menu-item"
              :class="{ selected: activeFilterKey === chip.key }"
              :disabled="loading"
              @click="selectFilter(chip.key)"
            >
              <span class="menu-check">{{ activeFilterKey === chip.key ? selectedSymbol : '' }}</span>
              <span>{{ chip.label }}</span>
            </button>
            <p v-if="!allFilterChips.length" class="search-menu-empty">暂无筛选</p>
          </div>
        </section>

        <section v-if="showGroupColumn" class="search-dropdown-section">
          <p class="search-dropdown-title">{{ groupLabel }}</p>
          <div class="search-dropdown-items">
            <button
              v-for="chip in allGroupChips"
              :key="`group-${chip.key}`"
              class="search-menu-item"
              :class="{ selected: activeGroupKey === chip.key }"
              :disabled="loading"
              @click="selectGroup(chip.key)"
            >
              <span class="menu-check">{{ activeGroupKey === chip.key ? selectedSymbol : '' }}</span>
              <span>{{ chip.label }}</span>
            </button>
            <p v-if="!allGroupChips.length" class="search-menu-empty">暂无分组</p>
          </div>
        </section>

        <section v-if="showSavedFilterColumn" class="search-dropdown-section">
          <p class="search-dropdown-title">{{ savedFilterLabel }}</p>
          <div class="search-dropdown-items">
            <button
              v-for="chip in allSavedFilterChips"
              :key="`saved-filter-${chip.key}`"
              class="search-menu-item"
              :class="{ selected: activeSavedFilterKey === chip.key }"
              :disabled="loading"
              @click="selectSavedFilter(chip.key)"
            >
              <span class="menu-check">{{ activeSavedFilterKey === chip.key ? selectedSymbol : '' }}</span>
              <span>{{ chip.label }}</span>
            </button>
            <p v-if="!allSavedFilterChips.length" class="search-menu-empty">暂无收藏</p>
          </div>
        </section>
      </div>
    </div>

    <div v-if="sortOptions.length" class="toolbar-section sort-switch">
      <p class="contract-label">{{ sortLabel }}</p>
      <div class="contract-chips">
        <button
          v-for="option in sortOptions"
          :key="`sort-${option.value}`"
          class="contract-chip"
          :class="{ active: option.value === sortValue }"
          :disabled="loading"
          @click="$emit('sort', option.value)"
        >
          {{ option.label }}
        </button>
      </div>
    </div>

    <div v-if="canCreateRecord" class="toolbar-actions">
      <button class="contract-chip primary" type="button" :disabled="loading" @click="$emit('create')">
        {{ createLabel }}
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';

type SearchChip = { key: string; label: string };

const props = defineProps<{
  loading: boolean;
  showViewSwitch: boolean;
  viewLabel: string;
  viewModes: string[];
  currentViewMode: string;
  viewModeLabels: Record<string, string>;
  searchValue: string;
  searchPlaceholder: string;
  clearLabel: string;
  showFilter: boolean;
  filterLabel: string;
  filterPrimary: Array<{ key: string; label: string }>;
  filterOverflow: Array<{ key: string; label: string }>;
  activeFilterKey: string;
  showSavedFilter: boolean;
  savedFilterLabel: string;
  savedFilterPrimary: Array<{ key: string; label: string }>;
  savedFilterOverflow: Array<{ key: string; label: string }>;
  activeSavedFilterKey: string;
  sortLabel: string;
  sortOptions: Array<{ label: string; value: string }>;
  sortValue: string;
  showGroup: boolean;
  groupLabel: string;
  groupPrimary: Array<{ key: string; label: string }>;
  groupOverflow: Array<{ key: string; label: string }>;
  activeGroupKey: string;
  canCreateRecord: boolean;
  createLabel: string;
}>();

const emit = defineEmits<{
  'switch-view': [mode: string];
  'search-input': [event: Event];
  'search-composition-start': [];
  'search-composition-end': [event: CompositionEvent];
  'search-submit': [];
  'clear-search': [];
  filter: [key: string];
  'clear-filter': [];
  'saved-filter': [key: string];
  'clear-saved-filter': [];
  sort: [value: string];
  group: [key: string];
  'clear-group': [];
  create: [];
}>();

const searchMenuOpen = ref(false);
const toolbarRoot = ref<HTMLElement | null>(null);
const selectedSymbol = '✓';
const clearSymbol = '×';

const allFilterChips = computed(() => [...props.filterPrimary, ...props.filterOverflow]);
const allSavedFilterChips = computed(() => [...props.savedFilterPrimary, ...props.savedFilterOverflow]);
const allGroupChips = computed(() => [...props.groupPrimary, ...props.groupOverflow]);
const activeFilterChip = computed<SearchChip | null>(() =>
  allFilterChips.value.find((chip) => chip.key === props.activeFilterKey) || null,
);
const activeSavedFilterChip = computed<SearchChip | null>(() =>
  allSavedFilterChips.value.find((chip) => chip.key === props.activeSavedFilterKey) || null,
);
const activeGroupChip = computed<SearchChip | null>(() =>
  allGroupChips.value.find((chip) => chip.key === props.activeGroupKey) || null,
);
const showFilterColumn = computed(() =>
  props.showFilter
  || props.showGroup
  || props.showSavedFilter
  || allFilterChips.value.length > 0
  || allGroupChips.value.length > 0
  || allSavedFilterChips.value.length > 0,
);
const showGroupColumn = computed(() =>
  props.showGroup
  || props.showFilter
  || props.showSavedFilter
  || allFilterChips.value.length > 0
  || allGroupChips.value.length > 0
  || allSavedFilterChips.value.length > 0,
);
const showSavedFilterColumn = computed(() =>
  props.showSavedFilter
  || showFilterColumn.value
  || showGroupColumn.value
  || allSavedFilterChips.value.length > 0,
);
const hasSearchMenu = computed(() =>
  showFilterColumn.value
  || showGroupColumn.value
  || showSavedFilterColumn.value,
);

function selectFilter(key: string) {
  searchMenuOpen.value = false;
  emit('filter', key);
}

function selectSavedFilter(key: string) {
  searchMenuOpen.value = false;
  emit('saved-filter', key);
}

function selectGroup(key: string) {
  searchMenuOpen.value = false;
  emit('group', key);
}

function handleDocumentPointerDown(event: PointerEvent) {
  const root = toolbarRoot.value;
  if (!root || root.contains(event.target as Node | null)) return;
  searchMenuOpen.value = false;
}

onMounted(() => {
  document.addEventListener('pointerdown', handleDocumentPointerDown);
});

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown);
});
</script>

<style scoped>
.action-toolbar {
  display: grid;
  grid-template-columns: auto minmax(320px, 1fr) auto auto;
  align-items: start;
  gap: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  padding: 8px 10px;
}

.toolbar-section,
.view-switch,
.filter-switch,
.saved-filter-switch,
.sort-switch,
.group-switch {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.view-switch {
  width: 120px;
}

.group-switch {
  flex-wrap: wrap;
}

.filter-switch,
.saved-filter-switch {
  flex-wrap: wrap;
}

.native-search {
  position: relative;
  display: flex;
  align-items: center;
  justify-self: stretch;
  min-width: 320px;
}

.native-searchbox {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  flex: 1 1 auto;
  min-height: 30px;
  gap: 5px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #f8fafc;
  padding: 3px 4px 3px 6px;
}

.native-searchbox input {
  flex: 1 1 160px;
  min-width: 120px;
  height: 22px;
  border: 0;
  background: transparent;
  color: #0f172a;
  font-size: 12px;
  padding: 2px 4px;
}

.native-searchbox input:focus {
  outline: none;
}

.toolbar-search-clear {
  flex: 0 0 auto;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
  color: #475569;
  padding: 5px 8px;
  font-size: 12px;
  cursor: pointer;
}

.search-facet {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-height: 22px;
  border: 1px solid #bfdbfe;
  border-radius: 5px;
  background: #eff6ff;
  color: #1e40af;
  padding: 2px 6px;
  font-size: 12px;
  cursor: pointer;
}

.facet-remove {
  color: #dc2626;
  font-weight: 700;
}

.search-menu-toggle {
  flex: 0 0 auto;
  width: 28px;
  min-height: 24px;
  border: 0;
  border-left: 1px solid #cbd5e1;
  background: transparent;
  color: #334155;
  padding: 0;
  font-size: 12px;
  cursor: pointer;
}

.search-menu-toggle.active {
  color: #1d4ed8;
}

.search-menu-caret {
  display: inline-block;
  line-height: 1;
}

.search-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 20;
  display: grid;
  grid-template-columns: repeat(3, minmax(180px, 1fr));
  width: min(760px, 92vw);
  max-height: 420px;
  overflow: auto;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.18);
  padding: 8px 0;
}

.search-dropdown-section {
  min-width: 0;
}

.search-dropdown-section + .search-dropdown-section {
  border-left: 1px solid #e2e8f0;
}

.search-dropdown-title {
  margin: 0;
  padding: 5px 12px;
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}

.search-dropdown-items {
  display: grid;
}

.search-menu-item {
  display: grid;
  grid-template-columns: 18px minmax(0, 1fr);
  align-items: center;
  gap: 6px;
  border: 0;
  background: #fff;
  color: #0f172a;
  padding: 7px 12px;
  text-align: left;
  font-size: 13px;
  cursor: pointer;
}

.search-menu-item:hover,
.search-menu-item.selected {
  background: #eff6ff;
  color: #1d4ed8;
}

.search-menu-empty {
  margin: 0;
  padding: 7px 12px 7px 36px;
  color: #94a3b8;
  font-size: 13px;
}

.menu-check {
  color: #2563eb;
  font-weight: 700;
}

.toolbar-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.contract-label {
  margin: 0;
  font-size: 13px;
  color: #334155;
  white-space: nowrap;
}

.contract-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.contract-chips.overflow-row {
  flex: 1 1 100%;
  padding-left: 36px;
}

.contract-chip {
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  background: #fff;
  color: #0f172a;
  padding: 5px 11px;
  font-size: 12px;
  cursor: pointer;
}

.contract-chip.active {
  border-color: #2563eb;
  color: #1d4ed8;
  background: #eff6ff;
}

.contract-chip.primary {
  border-color: #2563eb;
  background: #2563eb;
  color: #fff;
}

.contract-chip.ghost {
  border-style: dashed;
}

.contract-chip:disabled,
.toolbar-search-clear:disabled,
.search-menu-toggle:disabled,
.search-facet:disabled,
.search-menu-item:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

@media (max-width: 1120px) {
  .action-toolbar {
    grid-template-columns: 1fr;
  }

  .toolbar-section,
  .view-switch,
  .filter-switch,
  .saved-filter-switch,
  .sort-switch,
  .group-switch,
  .toolbar-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .native-search {
    width: 100%;
    min-width: 0;
  }

  .native-searchbox {
    min-width: 0;
  }

  .search-dropdown {
    grid-template-columns: 1fr;
    width: min(520px, 92vw);
  }

  .search-dropdown-section + .search-dropdown-section {
    border-left: 0;
    border-top: 1px solid #e2e8f0;
  }
}
</style>

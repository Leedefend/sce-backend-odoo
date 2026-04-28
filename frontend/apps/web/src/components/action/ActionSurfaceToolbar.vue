<template>
  <section class="action-toolbar">
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

    <div class="toolbar-search">
      <input
        type="search"
        :value="searchValue"
        :disabled="loading"
        :placeholder="searchPlaceholder"
        @compositionstart="$emit('search-composition-start')"
        @compositionend="$emit('search-composition-end', $event)"
        @input="$emit('search-input', $event)"
        @keydown.enter.prevent="$emit('search-submit')"
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

    <div v-if="showGroup" class="toolbar-section group-switch">
      <p class="contract-label">{{ groupLabel }}</p>
      <div class="contract-chips">
        <button
          v-for="chip in groupPrimary"
          :key="`group-${chip.key}`"
          class="contract-chip"
          :class="{ active: activeGroupKey === chip.key }"
          :disabled="loading"
          @click="$emit('group', chip.key)"
        >
          {{ chip.label }}
        </button>
        <button
          v-if="activeGroupKey"
          class="contract-chip ghost"
          :disabled="loading"
          @click="$emit('clear-group')"
        >
          {{ clearLabel }}
        </button>
        <button
          v-if="groupOverflow.length"
          class="contract-chip ghost"
          :disabled="loading"
          @click="$emit('toggle-more-group')"
        >
          {{ showMoreGroup ? collapseGroupLabel : moreGroupLabel }}
        </button>
      </div>
      <div v-if="showMoreGroup && groupOverflow.length" class="contract-chips overflow-row">
        <button
          v-for="chip in groupOverflow"
          :key="`group-overflow-${chip.key}`"
          class="contract-chip"
          :class="{ active: activeGroupKey === chip.key }"
          :disabled="loading"
          @click="$emit('group', chip.key)"
        >
          {{ chip.label }}
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
defineProps<{
  loading: boolean;
  showViewSwitch: boolean;
  viewLabel: string;
  viewModes: string[];
  currentViewMode: string;
  viewModeLabels: Record<string, string>;
  searchValue: string;
  searchPlaceholder: string;
  clearLabel: string;
  sortLabel: string;
  sortOptions: Array<{ label: string; value: string }>;
  sortValue: string;
  showGroup: boolean;
  groupLabel: string;
  groupPrimary: Array<{ key: string; label: string }>;
  groupOverflow: Array<{ key: string; label: string }>;
  activeGroupKey: string;
  showMoreGroup: boolean;
  moreGroupLabel: string;
  collapseGroupLabel: string;
  canCreateRecord: boolean;
  createLabel: string;
}>();

defineEmits<{
  'switch-view': [mode: string];
  'search-input': [event: Event];
  'search-composition-start': [];
  'search-composition-end': [event: CompositionEvent];
  'search-submit': [];
  'clear-search': [];
  sort: [value: string];
  group: [key: string];
  'clear-group': [];
  'toggle-more-group': [];
  create: [];
}>();
</script>

<style scoped>
.action-toolbar {
  display: grid;
  grid-template-columns: auto minmax(220px, 1fr) auto auto auto;
  align-items: start;
  gap: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  padding: 8px 10px;
}

.toolbar-section,
.view-switch,
.sort-switch,
.group-switch {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.group-switch {
  flex-wrap: wrap;
}

.toolbar-search {
  display: flex;
  align-items: center;
  justify-self: stretch;
  min-width: 220px;
  gap: 6px;
}

.toolbar-search input {
  width: 100%;
  height: 28px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #f8fafc;
  color: #0f172a;
  font-size: 12px;
  padding: 5px 9px;
}

.toolbar-search input:focus {
  border-color: #2563eb;
  background: #fff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.12);
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
.toolbar-search-clear:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

@media (max-width: 1120px) {
  .action-toolbar {
    grid-template-columns: 1fr;
  }

  .toolbar-section,
  .view-switch,
  .sort-switch,
  .group-switch,
  .toolbar-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .toolbar-search {
    width: 100%;
    min-width: 0;
  }
}
</style>

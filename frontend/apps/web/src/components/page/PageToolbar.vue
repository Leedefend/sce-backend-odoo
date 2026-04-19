<template>
  <section v-if="showPrimaryToolbar" class="toolbar">
    <div v-if="showSearchBlock" class="search">
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
          :disabled="loading"
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

  <section v-if="hasContractControls && usesOptimizationComposition" class="contract-toolbar contract-toolbar--optimized">
    <div
      v-for="section in renderedSections"
      :key="`section-${section.key}`"
      class="contract-group"
      :class="`contract-group--${section.key}`"
    >
      <template v-if="section.key === 'active_conditions' && visibleActiveStateChips.length">
        <span class="contract-group__label">当前条件（{{ visibleActiveStateChips.length }}）</span>
        <span class="contract-group__caption">清空时会一并移除隐藏的筛选和分组状态</span>
        <div class="contract-group__chips">
          <span
            v-for="chip in visibleActiveStateChips"
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
            清空全部条件
          </button>
        </div>
      </template>

      <template v-else-if="section.key === 'route_preset' && routePresetLabelText">
        <span class="contract-group__label">推荐筛选</span>
        <span class="contract-group__caption">保留当前推荐筛选上下文，可单独清除</span>
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
      </template>

      <template v-else-if="section.key === 'quick_filters' && prioritizedQuickFilters.length">
        <span class="contract-group__label">高频筛选优先项（{{ prioritizedQuickFilters.length }}）</span>
        <span class="contract-group__caption">仅展示后端标记的优先筛选，其余筛选项收纳到高级筛选</span>
        <div class="contract-group__chips">
          <button
            v-for="chip in prioritizedQuickFilters"
            :key="`quick-priority-${chip.key}`"
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
      </template>

      <template v-else-if="section.key === 'advanced_filters' && showAdvancedFiltersSection">
        <span class="contract-group__label">高级筛选</span>
        <span class="contract-group__caption">承接其余筛选项，默认折叠</span>
        <div class="contract-group__chips">
          <button
            v-if="advancedFiltersCollapsible"
            type="button"
            class="contract-chip ghost"
            :disabled="loading"
            @click="toggleAdvancedFilters"
          >
            {{ advancedFiltersToggleText }}
          </button>
        </div>
        <div v-if="showAdvancedFilters" class="contract-advanced">
          <div v-if="advancedQuickFilters.length" class="contract-advanced__group">
            <span class="contract-advanced__label">剩余筛选</span>
            <div class="contract-group__chips">
              <button
                v-for="chip in advancedQuickFilters"
                :key="`advanced-quick-${chip.key}`"
                type="button"
                class="contract-chip"
                :class="{ active: activeContractFilterKey === chip.key }"
                :disabled="loading"
                @click="onApplyContractFilter?.(chip.key)"
              >
                {{ chip.label }}
              </button>
            </div>
          </div>
          <div v-if="advancedSavedFilters.length" class="contract-advanced__group">
            <span class="contract-advanced__label">已保存筛选</span>
            <div class="contract-group__chips">
              <button
                v-for="chip in advancedSavedFilters"
                :key="`advanced-saved-${chip.key}`"
                type="button"
                class="contract-chip"
                :class="{ active: activeSavedFilterKey === chip.key }"
                :disabled="loading"
                @click="onApplySavedFilter?.(chip.key)"
              >
                {{ chip.label }}
              </button>
            </div>
          </div>
          <div v-if="advancedSearchPanelOptions.length" class="contract-advanced__group">
            <span class="contract-advanced__label">分面维度</span>
            <div class="contract-group__chips">
              <span
                v-for="chip in advancedSearchPanelOptions"
                :key="`advanced-searchpanel-${chip.key}`"
                class="contract-chip static"
              >
                {{ chip.label }}
              </span>
            </div>
          </div>
        </div>
      </template>

      <template v-else-if="section.key === 'grouping' && groupByOptions.length">
        <span class="contract-group__label">分组策略（{{ groupByCountText }}）</span>
        <span class="contract-group__caption">按场景契约开放的分组维度查看列表</span>
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
      </template>

      <template v-else-if="section.key === 'secondary_metadata' && showSecondaryMetadataSection">
        <span class="contract-group__label">辅助信息</span>
        <span class="contract-group__caption">{{ secondaryMetadataCaptionText }}</span>
        <div class="contract-group__chips">
          <span v-if="searchModeLabelText" class="contract-chip static">{{ searchModeLabelText }}</span>
          <span
            v-for="chip in searchableFieldOptions"
            :key="`searchable-${chip.key}`"
            class="contract-chip static"
          >
            {{ chip.label }}
          </span>
          <span
            v-for="chip in secondarySearchPanelOptions"
            :key="`secondary-searchpanel-${chip.key}`"
            class="contract-chip static"
          >
            {{ chip.label }}
          </span>
        </div>
      </template>
    </div>
  </section>

  <section v-else-if="hasContractControls" class="contract-toolbar">
    <div v-if="activeStateChips.length" class="contract-group">
      <span class="contract-group__label">当前条件（{{ activeStateChips.length }}）</span>
      <span class="contract-group__caption">清空时会一并移除隐藏的筛选和分组状态</span>
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
          清空全部条件
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
import { computed, onBeforeUnmount, ref, watch } from 'vue';

type ToolbarChip = { key: string; label: string };
type ToolbarSection = {
  key: string;
  kind: string;
  priority: number;
  visible: boolean;
  collapsible: boolean;
  defaultOpen: boolean;
};

const props = defineProps<{
  loading: boolean;
  searchTerm: string;
  searchPlaceholder?: string;
  sortOptions?: Array<{ label: string; value: string }>;
  sortValue?: string;
  sortLabel?: string;
  sortSourceLabel?: string;
  filterValue: 'all' | 'active' | 'archived';
  hasActiveField?: boolean;
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
  optimizationComposition?: {
    toolbarSections?: ToolbarSection[];
    activeConditions?: {
      visible?: boolean;
      include?: string[];
      mergeRules?: Record<string, unknown>;
    };
    highFrequencyFilters?: Array<{ key: string }>;
    advancedFilters?: {
      visible?: boolean;
      collapsible?: boolean;
      defaultOpen?: boolean;
      source?: Record<string, unknown>;
    };
  } | null;
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
const autoSearchTimer = ref<ReturnType<typeof setTimeout> | null>(null);
const showAdvancedFilters = ref(false);
const sortOptions = computed(() => Array.isArray(props.sortOptions) ? props.sortOptions : []);
const quickFilters = computed(() => Array.isArray(props.quickFilters) ? props.quickFilters : []);
const savedFilters = computed(() => Array.isArray(props.savedFilters) ? props.savedFilters : []);
const groupByOptions = computed(() => Array.isArray(props.groupByOptions) ? props.groupByOptions : []);
const searchPanelOptions = computed(() => Array.isArray(props.searchPanelOptions) ? props.searchPanelOptions : []);
const searchableFieldOptions = computed(() => Array.isArray(props.searchableFieldOptions) ? props.searchableFieldOptions : []);
const optimizationComposition = computed(() => {
  const raw = props.optimizationComposition;
  return raw && typeof raw === 'object' ? raw : null;
});
const optimizationToolbarSections = computed(() =>
  Array.isArray(optimizationComposition.value?.toolbarSections)
    ? optimizationComposition.value?.toolbarSections || []
    : [],
);
const baseRenderedSections = computed(() =>
  optimizationToolbarSections.value
    .filter((item) => item && item.visible !== false)
    .sort((a, b) => Number(a.priority || 0) - Number(b.priority || 0)),
);
const usesOptimizationComposition = computed(() => baseRenderedSections.value.length > 0);
const optimizationSearchSection = computed(() =>
  optimizationToolbarSections.value.find((item) => item && item.key === 'search') || null,
);
const routePresetLabelText = computed(() => String(props.routePresetLabel || '').trim());
const routePresetSourceText = computed(() => {
  const raw = String(props.routePresetSource || '').trim().toLowerCase();
  if (!raw) return '';
  if (raw === 'scene' || raw === 'route' || raw === 'query' || raw === 'url') return '路由上下文';
  if (raw === 'menu') return '菜单';
  if (raw === 'recommended' || raw === 'preset') return '系统推荐';
  return raw.replace(/[_-]+/g, ' ');
});
const routePresetChipLabel = computed(() => {
  if (!routePresetLabelText.value) return '';
  if (!routePresetSourceText.value) return routePresetLabelText.value;
  return `${routePresetLabelText.value}（来源：${routePresetSourceText.value}）`;
});
const renderedSections = computed(() => {
  const rows = [...baseRenderedSections.value];
  if (!usesOptimizationComposition.value || !routePresetLabelText.value) return rows;
  if (rows.some((item) => item.key === 'route_preset')) return rows;
  const activeConditionsPriority = rows.find((item) => item.key === 'active_conditions')?.priority;
  rows.push({
    key: 'route_preset',
    kind: 'route_preset',
    priority: Number.isFinite(Number(activeConditionsPriority)) ? Number(activeConditionsPriority) + 1 : 15,
    visible: true,
    collapsible: false,
    defaultOpen: true,
  });
  return rows.sort((a, b) => Number(a.priority || 0) - Number(b.priority || 0));
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
const activeConditionsConfig = computed(() => {
  const payload = optimizationComposition.value?.activeConditions;
  return payload && typeof payload === 'object' ? payload : null;
});
const activeConditionInclude = computed(() => {
  const rows = Array.isArray(activeConditionsConfig.value?.include) ? activeConditionsConfig.value?.include : [];
  return rows.map((item) => String(item || '').trim()).filter(Boolean);
});
const routePresetOverridesSearchTerm = computed(() => Boolean(activeConditionsConfig.value?.mergeRules?.route_preset_overrides_search_term));
const prioritizedQuickFilterKeys = computed(() => {
  const rows = Array.isArray(optimizationComposition.value?.highFrequencyFilters) ? optimizationComposition.value?.highFrequencyFilters : [];
  return rows.map((item) => String(item?.key || '').trim()).filter(Boolean);
});
const prioritizedQuickFilters = computed(() => {
  if (!prioritizedQuickFilterKeys.value.length) return quickFilters.value;
  const allowed = new Set(prioritizedQuickFilterKeys.value);
  return quickFilters.value.filter((chip) => allowed.has(String(chip.key || '').trim()));
});
const advancedQuickFilters = computed(() => {
  if (!prioritizedQuickFilterKeys.value.length) return [];
  const allowed = new Set(prioritizedQuickFilterKeys.value);
  return quickFilters.value.filter((chip) => !allowed.has(String(chip.key || '').trim()));
});
const advancedFiltersConfig = computed(() => {
  const payload = optimizationComposition.value?.advancedFilters;
  return payload && typeof payload === 'object' ? payload : null;
});
const advancedFiltersSource = computed(() => {
  const payload = advancedFiltersConfig.value?.source;
  return payload && typeof payload === 'object' ? payload : {};
});
const advancedFiltersCollapsible = computed(() => advancedFiltersConfig.value?.collapsible !== false);
const advancedSavedFilters = computed(() =>
  advancedFiltersSource.value.includeSavedFilters ? savedFilters.value : [],
);
const advancedSearchPanelOptions = computed(() =>
  advancedFiltersSource.value.includeSearchpanel ? searchPanelOptions.value : [],
);
const secondarySearchPanelOptions = computed(() =>
  advancedFiltersSource.value.includeSearchpanel ? [] : searchPanelOptions.value,
);
const activeStateChips = computed(() => {
  const chips: ToolbarChip[] = [];
  if (usesOptimizationComposition.value && routePresetChipLabel.value) {
    chips.push({ key: `preset:${routePresetLabelText.value}`, label: `推荐筛选：${routePresetChipLabel.value}` });
  }
  const searchText = String(props.searchTerm || '').trim();
  if (searchText && !(routePresetOverridesSearchTerm.value && routePresetLabelText.value)) {
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
  if (sortLabel && sortSource !== '原生默认排序') {
    const prefix = sortSource || '排序';
    chips.push({ key: `sort:${sortLabel}`, label: `${prefix}：${sortLabel}` });
  }
  return chips;
});
const visibleActiveStateChips = computed(() => {
  if (!activeConditionInclude.value.length) return activeStateChips.value;
  const allowed = new Set(activeConditionInclude.value);
  return activeStateChips.value.filter((chip) => {
    if (chip.key.startsWith('preset:')) return allowed.has('route_preset');
    if (chip.key.startsWith('search:')) return allowed.has('search_term');
    if (chip.key.startsWith('quick:')) return allowed.has('quick_filter');
    if (chip.key.startsWith('saved:')) return allowed.has('saved_filter');
    if (chip.key.startsWith('group:')) return allowed.has('group_by');
    if (chip.key.startsWith('sort:')) return allowed.has('sort');
    return true;
  });
});
const showSortControls = computed(() => sortOptions.value.length > 0);
const explicitSortLabelText = computed(() => String(props.sortLabel || '').trim());
const sortSourceLabelText = computed(() => String(props.sortSourceLabel || '').trim());
const sortLabelText = computed(() => {
  if (explicitSortLabelText.value) return explicitSortLabelText.value;
  if (showSortControls.value) return '默认';
  return '';
});
const showSortBlock = computed(() =>
  showSortControls.value
  || Boolean(explicitSortLabelText.value)
  || Boolean(sortSourceLabelText.value),
);
const showSearchBlock = computed(() => {
  if (!usesOptimizationComposition.value) return true;
  return optimizationSearchSection.value?.visible !== false;
});
const searchPlaceholderText = computed(() => String(props.searchPlaceholder || '').trim() || '搜索关键字');
const hasContractControls = computed(() =>
  Boolean(routePresetLabelText.value)
  || quickFilters.value.length > 0
  || savedFilters.value.length > 0
  || groupByOptions.value.length > 0
  || searchPanelOptions.value.length > 0
  || searchableFieldOptions.value.length > 0
  || Boolean(searchModeLabelText.value),
);
const showLegacyStatusFilters = computed(() => !hasContractControls.value && Boolean(props.hasActiveField));
const showPrimaryToolbar = computed(() => {
  if (!usesOptimizationComposition.value) return true;
  return showSearchBlock.value || showSortBlock.value;
});
const showAdvancedFiltersSection = computed(() =>
  Boolean(advancedFiltersConfig.value?.visible !== false)
  && Boolean(advancedQuickFilters.value.length || advancedSavedFilters.value.length || advancedSearchPanelOptions.value.length),
);
const showSecondaryMetadataSection = computed(() =>
  Boolean(searchModeLabelText.value || searchableFieldOptions.value.length || secondarySearchPanelOptions.value.length),
);
const secondaryMetadataCaptionText = computed(() => {
  const segments: string[] = [];
  if (searchableFieldOptions.value.length) {
    segments.push(`可搜索字段（${searchableFieldCountText.value}）`);
  }
  if (secondarySearchPanelOptions.value.length) {
    segments.push(`分面维度（${searchPanelCountText.value}）`);
  }
  if (!segments.length) return '补充说明当前搜索模式与可读元数据';
  return segments.join(' / ');
});
const advancedFilterCountText = computed(() => {
  const total = advancedQuickFilters.value.length
    + advancedSavedFilters.value.length
    + advancedSearchPanelOptions.value.length;
  return String(total);
});
const advancedFiltersToggleText = computed(() => {
  if (showAdvancedFilters.value) return '收起高级筛选';
  const count = Number(advancedFilterCountText.value || '0');
  if (Number.isFinite(count) && count > 0) {
    return `展开高级筛选（${advancedFilterCountText.value}）`;
  }
  return '展开高级筛选';
});

watch(
  () => props.searchTerm,
  (next) => {
    if (isComposing.value) return;
    inputValue.value = next || '';
  },
);

watch(
  advancedFiltersConfig,
  (next) => {
    showAdvancedFilters.value = Boolean(next?.defaultOpen);
  },
  { immediate: true },
);

function onSearchInput(event: Event) {
  if (props.loading) return;
  const target = event.target as HTMLInputElement;
  inputValue.value = target.value;
  if (isComposing.value) return;
  if (autoSearchTimer.value) {
    clearTimeout(autoSearchTimer.value);
  }
  autoSearchTimer.value = setTimeout(() => {
    autoSearchTimer.value = null;
    submitSearch();
  }, 320);
}

function onCompositionStart() {
  isComposing.value = true;
}

function onCompositionEnd(event: CompositionEvent) {
  if (props.loading) return;
  const target = event.target as HTMLInputElement | null;
  inputValue.value = target?.value || inputValue.value;
  isComposing.value = false;
}

function submitSearch() {
  if (props.loading) return;
  if (isComposing.value) return;
  if (autoSearchTimer.value) {
    clearTimeout(autoSearchTimer.value);
    autoSearchTimer.value = null;
  }
  props.onSearch(inputValue.value || '');
}

function resetActiveConditions() {
  if (props.loading) return;
  if (isComposing.value) return;
  inputValue.value = '';
  props.onSearch('');
  props.onClearRoutePreset?.();
  props.onClearContractFilter?.();
  props.onClearSavedFilter?.();
  props.onClearGroupBy?.();
}

function toggleAdvancedFilters() {
  if (props.loading) return;
  showAdvancedFilters.value = !showAdvancedFilters.value;
}

onBeforeUnmount(() => {
  if (autoSearchTimer.value) {
    clearTimeout(autoSearchTimer.value);
    autoSearchTimer.value = null;
  }
});
</script>

<style scoped>
.toolbar {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: var(--ui-space-3);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 245, 239, 0.94));
  border: 1px solid var(--ui-color-border);
  border-radius: var(--ui-radius-md);
  padding: var(--ui-space-3) var(--ui-space-4);
  box-shadow: var(--ui-shadow-sm);
  align-items: center;
}

.search input {
  width: 100%;
  min-height: 40px;
  padding: 0 var(--ui-space-3);
  border-radius: var(--ui-radius-sm);
  border: 1px solid var(--ui-color-border);
  background: rgba(255, 255, 255, 0.84);
}

.search {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  align-items: center;
}

.search-btn {
  padding: 10px 14px;
  border-radius: var(--ui-radius-sm);
  border: 1px solid var(--ui-color-primary-700);
  background: var(--ui-color-primary-700);
  color: #f8fafc;
  cursor: pointer;
  font-weight: var(--ui-font-weight-semibold);
  box-shadow: var(--ui-shadow-xs);
}

.search-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.filter {
  border: 1px solid var(--ui-color-border);
  padding: 6px 12px;
  border-radius: var(--ui-radius-pill);
  background: rgba(255, 255, 255, 0.84);
  font-size: var(--ui-font-size-xs);
  color: var(--ui-color-ink-muted);
  cursor: pointer;
  font-weight: var(--ui-font-weight-medium);
}

.filter.active {
  border-color: var(--ui-color-primary-700);
  background: var(--ui-color-primary-700);
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
  color: var(--ui-color-ink-soft);
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
  color: var(--ui-color-ink-muted);
  font-size: var(--ui-font-size-sm);
  font-weight: var(--ui-font-weight-semibold);
}

.sort-source {
  color: var(--ui-color-ink-soft);
  font-size: var(--ui-font-size-xs);
}

.sort-option {
  padding: 6px 12px;
  border-radius: var(--ui-radius-pill);
  border: 1px solid var(--ui-color-border);
  background: rgba(255, 255, 255, 0.84);
  font-size: var(--ui-font-size-xs);
  color: var(--ui-color-ink-muted);
}

.sort-option.active {
  background: var(--ui-color-primary-700);
  color: #f8fafc;
  border-color: var(--ui-color-primary-700);
}

.contract-toolbar {
  display: grid;
  gap: var(--ui-space-3);
  margin-top: var(--ui-space-3);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 245, 239, 0.94));
  border: 1px solid var(--ui-color-border);
  border-radius: var(--ui-radius-md);
  padding: var(--ui-space-3) var(--ui-space-4);
  box-shadow: var(--ui-shadow-sm);
}

.contract-toolbar--optimized {
  border: 1px solid rgba(61, 120, 159, 0.18);
  background:
    linear-gradient(180deg, rgba(238, 245, 250, 0.94), rgba(255, 255, 255, 0.98));
}

.contract-group {
  display: grid;
  gap: var(--ui-space-2);
  padding: var(--ui-space-3);
  border-radius: var(--ui-radius-sm);
  border: 1px solid var(--ui-color-border);
  background: rgba(255, 255, 255, 0.82);
  box-shadow: var(--ui-shadow-xs);
}

.contract-group--quick_filters,
.contract-group--advanced_filters,
.contract-group--grouping {
  border-color: rgba(14, 116, 144, 0.18);
}

.contract-group__label {
  font-size: var(--ui-font-size-xs);
  font-weight: var(--ui-font-weight-bold);
  color: var(--ui-color-ink);
}

.contract-group__caption {
  font-size: var(--ui-font-size-xs);
  color: var(--ui-color-ink-soft);
}

.contract-group__chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.contract-advanced {
  display: grid;
  gap: 8px;
}

.contract-advanced__group {
  display: grid;
  gap: 6px;
}

.contract-advanced__label {
  font-size: var(--ui-font-size-xs);
  color: var(--ui-color-ink-soft);
}

.contract-chip {
  border: 1px solid var(--ui-color-border);
  padding: 6px 10px;
  border-radius: var(--ui-radius-pill);
  background: rgba(255, 255, 255, 0.84);
  font-size: var(--ui-font-size-xs);
  color: var(--ui-color-ink);
  cursor: pointer;
  font-weight: var(--ui-font-weight-medium);
}

.contract-chip.active {
  background: var(--ui-color-primary-700);
  border-color: var(--ui-color-primary-700);
  color: #f8fafc;
}

.contract-chip.ghost {
  background: rgba(255, 255, 255, 0.9);
}

.contract-chip.static {
  cursor: default;
  background: var(--ui-color-primary-050);
  border-color: rgba(61, 120, 159, 0.16);
  color: var(--ui-color-primary-700);
}

@media (max-width: 960px) {
  .toolbar {
    grid-template-columns: 1fr;
  }
}
</style>

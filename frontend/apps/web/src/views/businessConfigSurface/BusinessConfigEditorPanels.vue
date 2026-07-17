<template>
<section v-if="analysisPanelOpen" class="edit-panel config-editor-panel">
  <div class="edit-panel-head">
    <div>
      <h2>分析视图设置</h2>
      <p>选择这个页面默认用于统计分析的指标和维度。</p>
    </div>
    <div class="edit-panel-actions">
      <ScButton v-if="hasAnalysisDraftChanges" variant="primary" :disabled="listSearchSaving" @click="$emit('inspectAnalysisDraft')">
        检查当前修改
      </ScButton>
      <ScButton variant="secondary" :disabled="listSearchSaving || !runtimeRouteTarget.path" @click="$emit('openCurrentEffectivePage')">
        打开当前生效页面
      </ScButton>
      <ScButton variant="secondary" :disabled="listSearchSaving || !hasAnalysisDraftChanges" @click="$emit('saveAnalysisConfig')">
        {{ listSearchSaving ? '保存中...' : '保存分析视图' }}
      </ScButton>
      <ScButton variant="ghost" :disabled="listSearchSaving || !hasAnalysisDraftChanges" @click="$emit('resetAnalysisDraft')">
        放弃调整
      </ScButton>
    </div>
  </div>
  <div class="list-search-tabs" role="group" aria-label="分析视图配置类型">
    <ScButton
      v-for="tab in analysisEditorTabs"
      :key="tab.key"
      type="button"
      :class="{ active: activeAnalysisEditor === tab.key }"
      @click="$emit('setActiveAnalysisEditor', tab.key)"
    >
      <span>{{ tab.label }}</span>
      <em>{{ analysisEditorCount(tab.key) }}</em>
    </ScButton>
  </div>
  <div class="edit-grid edit-grid--single">
    <LowCodeFieldChipEditor
      :title="analysisEditorLabel(activeAnalysisEditor)"
      :names="parseNames(analysisEditorState(activeAnalysisEditor).text.value)"
      :field-options="availableAnalysisFieldOptions"
      :field-option-total="analysisFieldOptionCandidates().length"
      :search-value="analysisFieldOptionSearch"
      :draft-value="analysisEditorState(activeAnalysisEditor).draft.value"
      :advanced-panel-open="advancedPanelOpen"
      :chip-key-prefix="`analysis-${activeAnalysisEditor}`"
      :option-key-prefix="`analysis-option-${activeAnalysisEditor}`"
      :show-graph-type="activeAnalysisEditor === 'graphMeasure' || activeAnalysisEditor === 'graphDimension'"
      :graph-type="graphType"
      :field-display-label="fieldDisplayLabel"
      :field-help-text="fieldHelpText"
      :field-option-help-text="fieldOptionHelpText"
      :field-option-label="fieldOptionLabel"
      :is-dragging="(name) => isAnalysisChipDragging(activeAnalysisEditor, name)"
      :is-drop-target="(name) => isAnalysisChipDropTarget(activeAnalysisEditor, name)"
      @update:search-value="$emit('updateAnalysisSearch', $event)"
      @update:draft-value="$emit('setAnalysisDraft', activeAnalysisEditor, $event)"
      @update:graph-type="$emit('updateGraphType', $event)"
      @add-name="$emit('addAnalysisName', activeAnalysisEditor, $event)"
      @add-visible-options="$emit('addVisibleAnalysisOptions', activeAnalysisEditor)"
      @remove-name="$emit('removeAnalysisName', activeAnalysisEditor, $event)"
      @move-name="(name, delta) => $emit('moveAnalysisName', activeAnalysisEditor, name, delta)"
      @start-drag="(name, event) => $emit('startAnalysisChipDrag', activeAnalysisEditor, name, event)"
      @hover-drop="$emit('hoverAnalysisChipDrop', activeAnalysisEditor, $event)"
      @drop="$emit('dropAnalysisChip', activeAnalysisEditor, $event)"
      @clear-drag="$emit('clearChipDrag')"
    />
  </div>
  <div class="edit-meta">
    <span v-if="hasAnalysisDraftChanges" class="edit-dirty">配置已调整；可先检查修改，保存后才会发布生效</span>
    <span v-if="advancedPanelOpen">生效来源：{{ boundaryLabel(analysisAudit?.business_config_boundary || 'business_contract') }}</span>
  </div>
</section>

<section v-if="listSearchPanelOpen" class="edit-panel config-editor-panel">
  <div class="edit-panel-head">
    <div>
      <h2>列表与搜索设置</h2>
      <p>{{ listSearchPanelDescription }}</p>
    </div>
    <div class="edit-panel-actions">
      <ScButton variant="ghost" :disabled="listSearchSaving" @click="$emit('closeListSearch')">
        返回工作台
      </ScButton>
      <ScButton v-if="hasListSearchDraftChanges" variant="primary" :disabled="listSearchSaving" @click="$emit('inspectListSearchDraft')">
        检查当前修改
      </ScButton>
      <ScButton variant="secondary" :disabled="listSearchSaving || !runtimeRouteTarget.path" @click="$emit('openCurrentEffectivePage')">
        打开当前生效页面
      </ScButton>
      <ScButton variant="secondary" :disabled="listSearchSaving || !hasListSearchDraftChanges" @click="$emit('saveListSearchConfig')">
        {{ listSearchSaving ? '保存中...' : '保存列表与搜索' }}
      </ScButton>
      <ScButton variant="ghost" :disabled="listSearchSaving || !hasListSearchDraftChanges" @click="$emit('resetListSearchDraft')">
        放弃调整
      </ScButton>
    </div>
  </div>
  <div class="list-search-tabs" role="group" aria-label="列表搜索配置类型">
    <ScButton
      v-for="tab in listSearchEditorTabs"
      :key="tab.key"
      type="button"
      :class="{ active: activeListSearchEditor === tab.key }"
      @click="$emit('setActiveListSearchEditor', tab.key)"
    >
      <span>{{ tab.label }}</span>
      <em>{{ listSearchEditorCount(tab.key) }}</em>
    </ScButton>
  </div>
  <div class="edit-grid edit-grid--single">
    <LowCodeFieldChipEditor
      v-if="activeListSearchEditor === 'list'"
      title="默认列表列"
      :names="parseNames(listColumnsText)"
      :field-options="availableListFieldOptions"
      :field-option-total="fieldOptionAvailableCount('list')"
      :search-value="listFieldOptionSearch"
      :draft-value="listColumnDraft"
      :advanced-panel-open="advancedPanelOpen"
      chip-key-prefix="list"
      option-key-prefix="list-option"
      :field-display-label="fieldDisplayLabel"
      :field-help-text="fieldHelpText"
      :field-option-help-text="fieldOptionHelpText"
      :field-option-label="fieldOptionLabel"
      :is-dragging="(name) => isListSearchChipDragging('list', name)"
      :is-drop-target="(name) => isListSearchChipDropTarget('list', name)"
      @update:search-value="$emit('updateListSearchSearch', 'list', $event)"
      @update:draft-value="$emit('updateListSearchDraft', 'list', $event)"
      @add-name="$emit('addListSearchName', 'list', $event)"
      @add-visible-options="$emit('addVisibleListSearchOptions', 'list')"
      @remove-name="$emit('removeListSearchName', 'list', $event)"
      @move-name="(name, delta) => $emit('moveListSearchName', 'list', name, delta)"
      @start-drag="(name, event) => $emit('startListSearchChipDrag', 'list', name, event)"
      @hover-drop="$emit('hoverListSearchChipDrop', 'list', $event)"
      @drop="$emit('dropListSearchChip', 'list', $event)"
      @clear-drag="$emit('clearChipDrag')"
    />
    <LowCodeFieldChipEditor
      v-if="activeListSearchEditor === 'filter'"
      title="搜索筛选字段"
      :names="parseNames(searchFiltersText)"
      :field-options="availableFilterFieldOptions"
      :field-option-total="fieldOptionAvailableCount('filter')"
      :search-value="filterFieldOptionSearch"
      :draft-value="searchFilterDraft"
      :advanced-panel-open="advancedPanelOpen"
      chip-key-prefix="filter"
      option-key-prefix="filter-option"
      :field-display-label="fieldDisplayLabel"
      :field-help-text="fieldHelpText"
      :field-option-help-text="fieldOptionHelpText"
      :field-option-label="fieldOptionLabel"
      :is-dragging="(name) => isListSearchChipDragging('filter', name)"
      :is-drop-target="(name) => isListSearchChipDropTarget('filter', name)"
      @update:search-value="$emit('updateListSearchSearch', 'filter', $event)"
      @update:draft-value="$emit('updateListSearchDraft', 'filter', $event)"
      @add-name="$emit('addListSearchName', 'filter', $event)"
      @add-visible-options="$emit('addVisibleListSearchOptions', 'filter')"
      @remove-name="$emit('removeListSearchName', 'filter', $event)"
      @move-name="(name, delta) => $emit('moveListSearchName', 'filter', name, delta)"
      @start-drag="(name, event) => $emit('startListSearchChipDrag', 'filter', name, event)"
      @hover-drop="$emit('hoverListSearchChipDrop', 'filter', $event)"
      @drop="$emit('dropListSearchChip', 'filter', $event)"
      @clear-drag="$emit('clearChipDrag')"
    />
    <LowCodeFieldChipEditor
      v-if="activeListSearchEditor === 'group'"
      title="搜索分组字段"
      :names="parseNames(searchGroupByText)"
      :field-options="availableGroupFieldOptions"
      :field-option-total="fieldOptionAvailableCount('group')"
      :search-value="groupFieldOptionSearch"
      :draft-value="searchGroupDraft"
      :advanced-panel-open="advancedPanelOpen"
      chip-key-prefix="group"
      option-key-prefix="group-option"
      :field-display-label="fieldDisplayLabel"
      :field-help-text="fieldHelpText"
      :field-option-help-text="fieldOptionHelpText"
      :field-option-label="fieldOptionLabel"
      :is-dragging="(name) => isListSearchChipDragging('group', name)"
      :is-drop-target="(name) => isListSearchChipDropTarget('group', name)"
      @update:search-value="$emit('updateListSearchSearch', 'group', $event)"
      @update:draft-value="$emit('updateListSearchDraft', 'group', $event)"
      @add-name="$emit('addListSearchName', 'group', $event)"
      @add-visible-options="$emit('addVisibleListSearchOptions', 'group')"
      @remove-name="$emit('removeListSearchName', 'group', $event)"
      @move-name="(name, delta) => $emit('moveListSearchName', 'group', name, delta)"
      @start-drag="(name, event) => $emit('startListSearchChipDrag', 'group', name, event)"
      @hover-drop="$emit('hoverListSearchChipDrop', 'group', $event)"
      @drop="$emit('dropListSearchChip', 'group', $event)"
      @clear-drag="$emit('clearChipDrag')"
    />
  </div>
  <div class="edit-meta">
    <span v-if="hasListSearchDraftChanges" class="edit-dirty">配置已调整；可先检查修改，保存后才会发布生效</span>
    <span v-if="advancedPanelOpen">个人设置记录：{{ listSearchAudit?.user_preference_count ?? 0 }}</span>
    <span v-if="advancedPanelOpen">生效来源：{{ boundaryLabel(listSearchAudit?.user_preference_boundary || 'ui_only') }}</span>
  </div>
  <div v-if="advancedPanelOpen && listSearchAudit?.user_preferences?.length" class="preference-list">
    <span
      v-for="item in listSearchAudit.user_preferences.slice(0, 6)"
      :key="item.id || item.scope_key"
    >
      {{ item.user_name || '用户' }} · {{ viewTypeLabel(item.view_type || 'list') }} · {{ item.column_count }}列
    </span>
  </div>
</section>
</template>

<script setup lang="ts">
import LowCodeFieldChipEditor from './LowCodeFieldChipEditor.vue';
import ScButton from '../../components/design-system/ScButton.vue';

type ListSearchEditorKind = 'list' | 'filter' | 'group';
type AnalysisEditorKind = 'pivotMeasure' | 'pivotDimension' | 'graphMeasure' | 'graphDimension';
type FieldOption = { name: string; label: string; type: string };

defineProps<{
  analysisPanelOpen: boolean;
  listSearchPanelOpen: boolean;
  listSearchSaving: boolean;
  runtimeRouteTarget: { path: string; query: Record<string, string> };
  hasAnalysisDraftChanges: boolean;
  hasListSearchDraftChanges: boolean;
  analysisEditorTabs: Array<{ key: AnalysisEditorKind; label: string }>;
  listSearchEditorTabs: Array<{ key: ListSearchEditorKind; label: string }>;
  activeAnalysisEditor: AnalysisEditorKind;
  activeListSearchEditor: ListSearchEditorKind;
  graphType: string;
  analysisFieldOptionSearch: string;
  listFieldOptionSearch: string;
  filterFieldOptionSearch: string;
  groupFieldOptionSearch: string;
  listColumnDraft: string;
  searchFilterDraft: string;
  searchGroupDraft: string;
  advancedPanelOpen: boolean;
  availableAnalysisFieldOptions: FieldOption[];
  availableListFieldOptions: FieldOption[];
  availableFilterFieldOptions: FieldOption[];
  availableGroupFieldOptions: FieldOption[];
  listColumnsText: string;
  searchFiltersText: string;
  searchGroupByText: string;
  listSearchPanelDescription: string;
  listSearchAudit: { user_preference_count?: number; user_preference_boundary?: string; user_preferences?: Array<{ id: number; scope_key: string; user_name?: string; view_type?: string; column_count: number }> } | null;
  analysisAudit: { business_config_boundary?: string } | null;
  parseNames: (raw: string) => string[];
  analysisEditorState: (kind: AnalysisEditorKind) => { text: { value: string }; draft: { value: string } };
  analysisEditorLabel: (kind: AnalysisEditorKind) => string;
  analysisEditorCount: (kind: AnalysisEditorKind) => number;
  analysisFieldOptionCandidates: () => FieldOption[];
  listSearchEditorCount: (kind: ListSearchEditorKind) => number;
  fieldOptionAvailableCount: (kind: ListSearchEditorKind) => number;
  fieldDisplayLabel: (name: string) => string;
  fieldHelpText: (name: string) => string;
  fieldOptionHelpText: (field: FieldOption) => string;
  fieldOptionLabel: (field: FieldOption) => string;
  isAnalysisChipDragging: (kind: AnalysisEditorKind, name: string) => boolean;
  isAnalysisChipDropTarget: (kind: AnalysisEditorKind, name: string) => boolean;
  isListSearchChipDragging: (kind: ListSearchEditorKind, name: string) => boolean;
  isListSearchChipDropTarget: (kind: ListSearchEditorKind, name: string) => boolean;
  boundaryLabel: (boundary: unknown) => string;
  viewTypeLabel: (viewType: string) => string;
}>();

defineEmits<{
  inspectAnalysisDraft: [];
  openCurrentEffectivePage: [];
  saveAnalysisConfig: [];
  resetAnalysisDraft: [];
  setActiveAnalysisEditor: [kind: AnalysisEditorKind];
  updateAnalysisSearch: [value: string];
  setAnalysisDraft: [kind: AnalysisEditorKind, value: string];
  updateGraphType: [value: string];
  addAnalysisName: [kind: AnalysisEditorKind, name?: string];
  addVisibleAnalysisOptions: [kind: AnalysisEditorKind];
  removeAnalysisName: [kind: AnalysisEditorKind, name: string];
  moveAnalysisName: [kind: AnalysisEditorKind, name: string, delta: number];
  startAnalysisChipDrag: [kind: AnalysisEditorKind, name: string, event: DragEvent];
  hoverAnalysisChipDrop: [kind: AnalysisEditorKind, name: string];
  dropAnalysisChip: [kind: AnalysisEditorKind, name: string];
  clearChipDrag: [];
  closeListSearch: [];
  inspectListSearchDraft: [];
  saveListSearchConfig: [];
  resetListSearchDraft: [];
  setActiveListSearchEditor: [kind: ListSearchEditorKind];
  updateListSearchSearch: [kind: ListSearchEditorKind, value: string];
  updateListSearchDraft: [kind: ListSearchEditorKind, value: string];
  addListSearchName: [kind: ListSearchEditorKind, name?: string];
  addVisibleListSearchOptions: [kind: ListSearchEditorKind];
  removeListSearchName: [kind: ListSearchEditorKind, name: string];
  moveListSearchName: [kind: ListSearchEditorKind, name: string, delta: number];
  startListSearchChipDrag: [kind: ListSearchEditorKind, name: string, event: DragEvent];
  hoverListSearchChipDrop: [kind: ListSearchEditorKind, name: string];
  dropListSearchChip: [kind: ListSearchEditorKind, name: string];
}>();
</script>

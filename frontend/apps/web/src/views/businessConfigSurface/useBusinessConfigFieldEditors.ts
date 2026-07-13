import { computed, ref, type Ref } from 'vue';
import type { RouteLocationNormalizedLoaded, Router } from 'vue-router';
import type {
  BusinessConfigAnalysisAuditPayload,
  BusinessConfigListSearchAuditPayload,
} from '../../api/businessConfig';
import {
  cleanBusinessFieldLabel,
  fieldTypeLabel,
  namesToText,
  normalizeNamesText,
  parseNames,
  shortFieldNameHint,
} from './formatters';

export type ListSearchEditorKind = 'list' | 'filter' | 'group';
export type AnalysisEditorKind = 'pivotMeasure' | 'pivotDimension' | 'graphMeasure' | 'graphDimension';

type FieldOption = { name: string; label: string; type: string };

type UseBusinessConfigFieldEditorsOptions = {
  route: RouteLocationNormalizedLoaded;
  router: Router;
  listSearchAudit: Ref<BusinessConfigListSearchAuditPayload | null>;
  analysisAudit: Ref<BusinessConfigAnalysisAuditPayload | null>;
  listSearchPanelOpen: Ref<boolean>;
  analysisPanelOpen: Ref<boolean>;
  advancedPanelOpen: Ref<boolean>;
  setMessage: (text: string, detail?: string) => void;
  clearMessage: () => void;
};

export function useBusinessConfigFieldEditors(options: UseBusinessConfigFieldEditorsOptions) {
  const listColumnsText = ref('');
  const searchFiltersText = ref('');
  const searchGroupByText = ref('');
  const pivotMeasuresText = ref('');
  const pivotDimensionsText = ref('');
  const graphMeasuresText = ref('');
  const graphDimensionsText = ref('');
  const graphType = ref('bar');
  const listSearchBase = ref({ list: '', filter: '', group: '' });
  const analysisBase = ref({ pivotMeasures: '', pivotDimensions: '', graphMeasures: '', graphDimensions: '', graphType: 'bar' });
  const listColumnDraft = ref('');
  const searchFilterDraft = ref('');
  const searchGroupDraft = ref('');
  const pivotMeasureDraft = ref('');
  const pivotDimensionDraft = ref('');
  const graphMeasureDraft = ref('');
  const graphDimensionDraft = ref('');
  const activeListSearchEditor = ref<ListSearchEditorKind>('list');
  const activeAnalysisEditor = ref<AnalysisEditorKind>('pivotMeasure');
  const chipDrag = ref<{
    area: 'list_search' | 'analysis';
    kind: ListSearchEditorKind | AnalysisEditorKind;
    name: string;
  } | null>(null);
  const chipDropTarget = ref<{
    area: 'list_search' | 'analysis';
    kind: ListSearchEditorKind | AnalysisEditorKind;
    name: string;
  } | null>(null);
  const listFieldOptionSearch = ref('');
  const filterFieldOptionSearch = ref('');
  const groupFieldOptionSearch = ref('');
  const analysisFieldOptionSearch = ref('');

  const requestedListSearchTab = computed<ListSearchEditorKind>(() => {
    const value = String(options.route.query.list_search_tab || '').trim();
    return value === 'filter' || value === 'group' ? value : 'list';
  });
  const requestedAnalysisTab = computed<AnalysisEditorKind>(() => {
    const value = String(options.route.query.analysis_tab || '').trim();
    if (value === 'pivotDimension' || value === 'graphMeasure' || value === 'graphDimension') return value;
    return 'pivotMeasure';
  });
  const listSearchEditorTabs: Array<{ key: ListSearchEditorKind; label: string }> = [
    { key: 'list', label: '列表列' },
    { key: 'filter', label: '搜索条件' },
    { key: 'group', label: '默认分组' },
  ];
  const analysisEditorTabs: Array<{ key: AnalysisEditorKind; label: string }> = [
    { key: 'pivotMeasure', label: '透视指标' },
    { key: 'pivotDimension', label: '透视维度' },
    { key: 'graphMeasure', label: '图表指标' },
    { key: 'graphDimension', label: '图表维度' },
  ];
  const availableModelFields = computed(() => (options.listSearchAudit.value?.available_model_fields || [])
    .concat(options.analysisAudit.value?.available_model_fields || [])
    .map((field) => ({
      name: String(field.name || '').trim(),
      label: cleanBusinessFieldLabel(field.name, field.label || field.name),
      type: String(field.type || '').trim(),
    }))
    .filter((field) => field.name)
    .filter((field, index, rows) => rows.findIndex((row) => row.name === field.name) === index)
  );
  const configuredListColumnLabels = computed(() => {
    const labels = options.listSearchAudit.value?.business_config_list_column_labels || {};
    return Object.entries(labels).reduce<Record<string, string>>((acc, [name, label]) => {
      const fieldName = String(name || '').trim();
      const cleanLabel = cleanBusinessFieldLabel(fieldName, label);
      if (fieldName && cleanLabel) acc[fieldName] = cleanLabel;
      return acc;
    }, {});
  });
  const duplicatedFieldLabels = computed(() => {
    const counts = new Map<string, number>();
    availableModelFields.value.forEach((field) => {
      const label = field.label || field.name;
      counts.set(label, (counts.get(label) || 0) + 1);
    });
    return new Set([...counts.entries()].filter(([, count]) => count > 1).map(([label]) => label));
  });
  const availableListFieldOptions = computed(() => fieldOptionsNotIn('list'));
  const availableFilterFieldOptions = computed(() => fieldOptionsNotIn('filter'));
  const availableGroupFieldOptions = computed(() => fieldOptionsNotIn('group'));
  const availableAnalysisFieldOptions = computed(() => analysisFieldOptionCandidates().slice(0, analysisFieldOptionSearch.value.trim() ? 80 : 24));
  const hasListSearchDraftChanges = computed(() => (
    normalizeNamesText(listColumnsText.value) !== listSearchBase.value.list
    || normalizeNamesText(searchFiltersText.value) !== listSearchBase.value.filter
    || normalizeNamesText(searchGroupByText.value) !== listSearchBase.value.group
  ));
  const hasAnalysisDraftChanges = computed(() => (
    normalizeNamesText(pivotMeasuresText.value) !== analysisBase.value.pivotMeasures
    || normalizeNamesText(pivotDimensionsText.value) !== analysisBase.value.pivotDimensions
    || normalizeNamesText(graphMeasuresText.value) !== analysisBase.value.graphMeasures
    || normalizeNamesText(graphDimensionsText.value) !== analysisBase.value.graphDimensions
    || String(graphType.value || 'bar') !== analysisBase.value.graphType
  ));

  function listSearchEditorState(kind: ListSearchEditorKind) {
    if (kind === 'list') return { text: listColumnsText, draft: listColumnDraft };
    if (kind === 'filter') return { text: searchFiltersText, draft: searchFilterDraft };
    return { text: searchGroupByText, draft: searchGroupDraft };
  }

  function listSearchEditorCount(kind: ListSearchEditorKind) {
    return parseNames(listSearchEditorState(kind).text.value).length;
  }

  function fieldOptionSearchState(kind: ListSearchEditorKind) {
    if (kind === 'list') return listFieldOptionSearch;
    if (kind === 'filter') return filterFieldOptionSearch;
    return groupFieldOptionSearch;
  }

  function updateListSearchFieldSearch(kind: ListSearchEditorKind, value: string) {
    fieldOptionSearchState(kind).value = value;
  }

  function updateListSearchDraft(kind: ListSearchEditorKind, value: string) {
    listSearchEditorState(kind).draft.value = value;
  }

  async function setActiveListSearchEditor(kind: ListSearchEditorKind) {
    activeListSearchEditor.value = kind;
    if (!options.listSearchPanelOpen.value) return;
    await options.router.replace({
      path: options.route.path,
      query: {
        ...options.route.query,
        list_search_tab: kind === 'list' ? undefined : kind,
      },
    });
  }

  async function setActiveAnalysisEditor(kind: AnalysisEditorKind) {
    activeAnalysisEditor.value = kind;
    if (!options.analysisPanelOpen.value) return;
    await options.router.replace({
      path: options.route.path,
      query: {
        ...options.route.query,
        analysis_tab: kind === 'pivotMeasure' ? undefined : kind,
      },
    });
  }

  function setListSearchNames(kind: ListSearchEditorKind, names: string[]) {
    const state = listSearchEditorState(kind);
    state.text.value = namesToText(names);
    options.clearMessage();
  }

  function resetListSearchDraft() {
    listColumnsText.value = listSearchBase.value.list;
    searchFiltersText.value = listSearchBase.value.filter;
    searchGroupByText.value = listSearchBase.value.group;
    listColumnDraft.value = '';
    searchFilterDraft.value = '';
    searchGroupDraft.value = '';
    options.setMessage('已放弃列表与搜索调整');
  }

  function fieldOptionsNotIn(kind: ListSearchEditorKind) {
    return fieldOptionCandidates(kind).slice(0, fieldOptionSearchState(kind).value.trim() ? 80 : 24);
  }

  function fieldOptionAvailableCount(kind: ListSearchEditorKind) {
    return fieldOptionCandidates(kind).length;
  }

  function fieldOptionCandidates(kind: ListSearchEditorKind) {
    const selected = new Set(parseNames(listSearchEditorState(kind).text.value));
    const keyword = fieldOptionSearchState(kind).value.trim().toLowerCase();
    return availableModelFields.value
      .filter((field) => !selected.has(field.name))
      .filter((field) => {
        if (!keyword) return true;
        return [field.name, field.label, field.type]
          .some((text) => String(text || '').toLowerCase().includes(keyword));
      });
  }

  function analysisEditorState(kind: AnalysisEditorKind) {
    if (kind === 'pivotMeasure') return { text: pivotMeasuresText, draft: pivotMeasureDraft };
    if (kind === 'pivotDimension') return { text: pivotDimensionsText, draft: pivotDimensionDraft };
    if (kind === 'graphMeasure') return { text: graphMeasuresText, draft: graphMeasureDraft };
    return { text: graphDimensionsText, draft: graphDimensionDraft };
  }

  function analysisEditorLabel(kind: AnalysisEditorKind) {
    const tab = analysisEditorTabs.find((item) => item.key === kind);
    return tab?.label || '分析字段';
  }

  function setAnalysisDraft(kind: AnalysisEditorKind, value: string) {
    analysisEditorState(kind).draft.value = value;
  }

  function analysisEditorCount(kind: AnalysisEditorKind) {
    return parseNames(analysisEditorState(kind).text.value).length;
  }

  function analysisFieldOptionCandidates() {
    const selected = new Set(parseNames(analysisEditorState(activeAnalysisEditor.value).text.value));
    const keyword = analysisFieldOptionSearch.value.trim().toLowerCase();
    return availableModelFields.value
      .filter((field) => !selected.has(field.name))
      .filter((field) => {
        if (!keyword) return true;
        return [field.name, field.label, field.type]
          .some((text) => String(text || '').toLowerCase().includes(keyword));
      });
  }

  function fieldDisplayLabel(name: string) {
    const fieldName = String(name || '').trim();
    const configuredLabel = configuredListColumnLabels.value[fieldName];
    if (configuredLabel) return configuredLabel;
    const field = availableModelFields.value.find((item) => item.name === fieldName);
    if (!field) return cleanBusinessFieldLabel(fieldName, fieldName);
    return fieldOptionLabel(field);
  }

  function fieldOptionLabel(field: FieldOption) {
    const label = field.label || field.name;
    if (!duplicatedFieldLabels.value.has(label)) return label;
    const type = fieldTypeLabel(field.type);
    const hint = shortFieldNameHint(field.name);
    return `${label}（${[type, options.advancedPanelOpen.value ? hint : ''].filter(Boolean).join(' · ')}）`;
  }

  function fieldOptionHelpText(field: FieldOption) {
    return [field.label || field.name, field.name, field.type].filter(Boolean).join(' · ');
  }

  function fieldHelpText(name: string) {
    const fieldName = String(name || '').trim();
    const configuredLabel = configuredListColumnLabels.value[fieldName];
    if (configuredLabel) return [configuredLabel, fieldName].filter(Boolean).join(' · ');
    const field = availableModelFields.value.find((item) => item.name === fieldName);
    return field ? fieldOptionHelpText(field) : cleanBusinessFieldLabel(fieldName, fieldName);
  }

  function addListSearchName(kind: ListSearchEditorKind, explicitName = '') {
    const state = listSearchEditorState(kind);
    const name = String(explicitName || state.draft.value || '').trim();
    if (!name) return;
    const names = parseNames(state.text.value);
    if (!names.includes(name)) names.push(name);
    setListSearchNames(kind, names);
    if (!explicitName) state.draft.value = '';
  }

  function addVisibleListSearchOptions(kind: ListSearchEditorKind) {
    const names = parseNames(listSearchEditorState(kind).text.value);
    const existing = new Set(names);
    let addedCount = 0;
    fieldOptionsNotIn(kind).forEach((field) => {
      if (!existing.has(field.name)) {
        names.push(field.name);
        existing.add(field.name);
        addedCount += 1;
      }
    });
    setListSearchNames(kind, names);
    options.setMessage(addedCount ? `已添加 ${addedCount} 个字段` : '当前显示字段已全部添加');
  }

  function removeListSearchName(kind: ListSearchEditorKind, name: string) {
    setListSearchNames(kind, parseNames(listSearchEditorState(kind).text.value).filter((item) => item !== name));
  }

  function moveListSearchName(kind: ListSearchEditorKind, name: string, delta: number) {
    const names = parseNames(listSearchEditorState(kind).text.value);
    const index = names.indexOf(name);
    const nextIndex = index + delta;
    if (index < 0 || nextIndex < 0 || nextIndex >= names.length) return;
    const [moved] = names.splice(index, 1);
    names.splice(nextIndex, 0, moved);
    setListSearchNames(kind, names);
  }

  function reorderNamesByDrop(names: string[], sourceName: string, targetName: string) {
    const sourceIndex = names.indexOf(sourceName);
    const targetIndex = names.indexOf(targetName);
    if (sourceIndex < 0 || targetIndex < 0 || sourceIndex === targetIndex) return names;
    const next = [...names];
    const [moved] = next.splice(sourceIndex, 1);
    next.splice(targetIndex, 0, moved);
    return next;
  }

  function startChipDrag(
    area: 'list_search' | 'analysis',
    kind: ListSearchEditorKind | AnalysisEditorKind,
    name: string,
    event: DragEvent,
  ) {
    chipDrag.value = { area, kind, name };
    chipDropTarget.value = null;
    event.dataTransfer?.setData('text/plain', name);
    if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move';
  }

  function hoverChipDrop(
    area: 'list_search' | 'analysis',
    kind: ListSearchEditorKind | AnalysisEditorKind,
    name: string,
  ) {
    const current = chipDrag.value;
    if (!current || current.area !== area || current.kind !== kind || current.name === name) {
      chipDropTarget.value = null;
      return;
    }
    chipDropTarget.value = { area, kind, name };
  }

  function clearChipDrag() {
    chipDrag.value = null;
    chipDropTarget.value = null;
  }

  function startListSearchChipDrag(kind: ListSearchEditorKind, name: string, event: DragEvent) {
    startChipDrag('list_search', kind, name, event);
  }

  function hoverListSearchChipDrop(kind: ListSearchEditorKind, name: string) {
    hoverChipDrop('list_search', kind, name);
  }

  function dropListSearchChip(kind: ListSearchEditorKind, targetName: string) {
    const current = chipDrag.value;
    if (!current || current.area !== 'list_search' || current.kind !== kind) return;
    const names = parseNames(listSearchEditorState(kind).text.value);
    setListSearchNames(kind, reorderNamesByDrop(names, current.name, targetName));
    clearChipDrag();
  }

  function isListSearchChipDragging(kind: ListSearchEditorKind, name: string) {
    const current = chipDrag.value;
    return current?.area === 'list_search' && current.kind === kind && current.name === name;
  }

  function isListSearchChipDropTarget(kind: ListSearchEditorKind, name: string) {
    const current = chipDropTarget.value;
    return current?.area === 'list_search' && current.kind === kind && current.name === name;
  }

  function setAnalysisNames(kind: AnalysisEditorKind, names: string[]) {
    analysisEditorState(kind).text.value = namesToText(names);
    options.clearMessage();
  }

  function addAnalysisName(kind: AnalysisEditorKind, explicitName = '') {
    const state = analysisEditorState(kind);
    const name = String(explicitName || state.draft.value || '').trim();
    if (!name) return;
    const names = parseNames(state.text.value);
    if (!names.includes(name)) names.push(name);
    setAnalysisNames(kind, names);
    if (!explicitName) state.draft.value = '';
  }

  function addVisibleAnalysisOptions(kind: AnalysisEditorKind) {
    const names = parseNames(analysisEditorState(kind).text.value);
    const existing = new Set(names);
    let addedCount = 0;
    availableAnalysisFieldOptions.value.forEach((field) => {
      if (!existing.has(field.name)) {
        names.push(field.name);
        existing.add(field.name);
        addedCount += 1;
      }
    });
    setAnalysisNames(kind, names);
    options.setMessage(addedCount ? `已添加 ${addedCount} 个分析字段` : '当前显示字段已全部添加');
  }

  function removeAnalysisName(kind: AnalysisEditorKind, name: string) {
    setAnalysisNames(kind, parseNames(analysisEditorState(kind).text.value).filter((item) => item !== name));
  }

  function moveAnalysisName(kind: AnalysisEditorKind, name: string, delta: number) {
    const names = parseNames(analysisEditorState(kind).text.value);
    const index = names.indexOf(name);
    const nextIndex = index + delta;
    if (index < 0 || nextIndex < 0 || nextIndex >= names.length) return;
    const [moved] = names.splice(index, 1);
    names.splice(nextIndex, 0, moved);
    setAnalysisNames(kind, names);
  }

  function startAnalysisChipDrag(kind: AnalysisEditorKind, name: string, event: DragEvent) {
    startChipDrag('analysis', kind, name, event);
  }

  function hoverAnalysisChipDrop(kind: AnalysisEditorKind, name: string) {
    hoverChipDrop('analysis', kind, name);
  }

  function dropAnalysisChip(kind: AnalysisEditorKind, targetName: string) {
    const current = chipDrag.value;
    if (!current || current.area !== 'analysis' || current.kind !== kind) return;
    const names = parseNames(analysisEditorState(kind).text.value);
    setAnalysisNames(kind, reorderNamesByDrop(names, current.name, targetName));
    clearChipDrag();
  }

  function isAnalysisChipDragging(kind: AnalysisEditorKind, name: string) {
    const current = chipDrag.value;
    return current?.area === 'analysis' && current.kind === kind && current.name === name;
  }

  function isAnalysisChipDropTarget(kind: AnalysisEditorKind, name: string) {
    const current = chipDropTarget.value;
    return current?.area === 'analysis' && current.kind === kind && current.name === name;
  }

  function resetAnalysisDraft() {
    pivotMeasuresText.value = analysisBase.value.pivotMeasures;
    pivotDimensionsText.value = analysisBase.value.pivotDimensions;
    graphMeasuresText.value = analysisBase.value.graphMeasures;
    graphDimensionsText.value = analysisBase.value.graphDimensions;
    graphType.value = analysisBase.value.graphType || 'bar';
    pivotMeasureDraft.value = '';
    pivotDimensionDraft.value = '';
    graphMeasureDraft.value = '';
    graphDimensionDraft.value = '';
    options.setMessage('已放弃分析视图调整');
  }

  return {
    listColumnsText,
    searchFiltersText,
    searchGroupByText,
    pivotMeasuresText,
    pivotDimensionsText,
    graphMeasuresText,
    graphDimensionsText,
    graphType,
    listSearchBase,
    analysisBase,
    listColumnDraft,
    searchFilterDraft,
    searchGroupDraft,
    activeListSearchEditor,
    activeAnalysisEditor,
    listFieldOptionSearch,
    filterFieldOptionSearch,
    groupFieldOptionSearch,
    analysisFieldOptionSearch,
    requestedListSearchTab,
    requestedAnalysisTab,
    listSearchEditorTabs,
    analysisEditorTabs,
    availableListFieldOptions,
    availableFilterFieldOptions,
    availableGroupFieldOptions,
    availableAnalysisFieldOptions,
    hasListSearchDraftChanges,
    hasAnalysisDraftChanges,
    listSearchEditorState,
    listSearchEditorCount,
    updateListSearchFieldSearch,
    updateListSearchDraft,
    setActiveListSearchEditor,
    setActiveAnalysisEditor,
    resetListSearchDraft,
    fieldOptionAvailableCount,
    analysisEditorState,
    analysisEditorLabel,
    setAnalysisDraft,
    analysisEditorCount,
    analysisFieldOptionCandidates,
    fieldDisplayLabel,
    fieldOptionHelpText,
    fieldOptionLabel,
    fieldHelpText,
    addListSearchName,
    addVisibleListSearchOptions,
    removeListSearchName,
    moveListSearchName,
    clearChipDrag,
    startListSearchChipDrag,
    hoverListSearchChipDrop,
    dropListSearchChip,
    isListSearchChipDragging,
    isListSearchChipDropTarget,
    addAnalysisName,
    addVisibleAnalysisOptions,
    removeAnalysisName,
    moveAnalysisName,
    startAnalysisChipDrag,
    hoverAnalysisChipDrop,
    dropAnalysisChip,
    isAnalysisChipDragging,
    isAnalysisChipDropTarget,
    resetAnalysisDraft,
  };
}

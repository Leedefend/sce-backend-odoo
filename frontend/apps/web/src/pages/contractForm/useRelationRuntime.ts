import type { FieldDescriptor } from '@sc/schema';
import { reactive, ref } from 'vue';
import type { RelationSearchDialogState } from './RelationSearchDialog.vue';
import {
  closedRelationSearchDialogState,
  mergeRelationOptionRows,
  openRelationSearchDialogState,
  relationOptionsWithSelectedFallback,
  selectedRelationOptionsFromValue,
  upsertRelationOptionRows,
} from './relationDescriptor';
import type { RelationOption, RelationSearchColumn, RelationSearchRow, RelationUiLabels } from './types';

export function useRelationRuntime() {
  const relationOptions = ref<Record<string, RelationOption[]>>({});
  const relationFieldDescriptors = ref<Record<string, Record<string, FieldDescriptor>>>({});
  const relationKeywords = reactive<Record<string, string>>({});
  const invalidatedRelationKeywords = reactive<Record<string, string>>({});
  const clearedDynamicRelationFields = reactive<Record<string, boolean>>({});
  const relationSearchDialog = reactive<RelationSearchDialogState>(closedRelationSearchDialogState());
  const deniedRelationModels = new Set<string>();
  const relationQueryTimers: Record<string, ReturnType<typeof setTimeout>> = {};

  function relationKeyword(name: string) {
    return String(relationKeywords[name] || '');
  }

  function relationOptionsForField(name: string, value: unknown) {
    return relationOptionsWithSelectedFallback(relationOptions.value[name], value);
  }

  function selectedRelationOptions(name: string, value: unknown) {
    return selectedRelationOptionsFromValue(relationOptions.value[name], value);
  }

  function setRelationKeywordValue(name: string, keyword: string) {
    relationKeywords[name] = keyword;
  }

  function filteredRelationOptions(name: string, value: unknown) {
    const rows = relationOptionsForField(name, value);
    const kw = relationKeyword(name).trim().toLowerCase();
    if (!kw) return rows;
    return rows.filter((row) => row.label.toLowerCase().includes(kw) || String(row.id).includes(kw));
  }

  function upsertRelationOption(fieldName: string, option: RelationOption | null) {
    const merged = upsertRelationOptionRows(relationOptions.value[fieldName], option);
    if (merged === relationOptions.value[fieldName]) return;
    relationOptions.value = {
      ...relationOptions.value,
      [fieldName]: merged,
    };
  }

  function mergeRelationOptions(fieldName: string, options: RelationOption[]) {
    relationOptions.value = {
      ...relationOptions.value,
      [fieldName]: mergeRelationOptionRows(relationOptions.value[fieldName], options),
    };
  }

  function clearRelationRuntime() {
    Object.keys(relationKeywords).forEach((key) => {
      delete relationKeywords[key];
    });
    Object.keys(invalidatedRelationKeywords).forEach((key) => {
      delete invalidatedRelationKeywords[key];
    });
    Object.keys(clearedDynamicRelationFields).forEach((key) => {
      delete clearedDynamicRelationFields[key];
    });
    Object.keys(relationQueryTimers).forEach((key) => {
      clearTimeout(relationQueryTimers[key]);
      delete relationQueryTimers[key];
    });
    relationOptions.value = {};
    relationFieldDescriptors.value = {};
    Object.assign(relationSearchDialog, closedRelationSearchDialogState());
    deniedRelationModels.clear();
  }

  function closeRelationSearchDialog() {
    Object.assign(relationSearchDialog, closedRelationSearchDialogState());
  }

  function setRelationSearchKeyword(keyword: string) {
    relationSearchDialog.keyword = keyword;
  }

  function selectRelationSearchRow(row: { id: number }) {
    relationSearchDialog.selectedId = row.id;
  }

  async function openRelationSearch(params: {
    fieldName: string;
    descriptor?: FieldDescriptor;
    labels: RelationUiLabels;
    keyword: string;
    columns: RelationSearchColumn[];
    createMode: 'none' | 'quick' | 'page';
    loadColumns: () => Promise<RelationSearchColumn[]>;
    runSearch: () => Promise<void>;
  }) {
    Object.assign(relationSearchDialog, openRelationSearchDialogState({
      fieldName: params.fieldName,
      descriptor: params.descriptor,
      labels: params.labels,
      keyword: params.keyword,
      columns: params.columns,
      createMode: params.createMode,
    }));
    relationSearchDialog.columns = await params.loadColumns();
    await params.runSearch();
  }

  async function runRelationSearch(params: {
    fetchRows: (fieldName: string, keyword: string) => Promise<RelationSearchRow[]>;
    sanitizeError: (error: unknown, fallback: string) => string;
  }) {
    const fieldName = relationSearchDialog.fieldName;
    if (!fieldName) return;
    relationSearchDialog.loading = true;
    relationSearchDialog.error = '';
    try {
      const rows = await params.fetchRows(fieldName, relationSearchDialog.keyword);
      relationSearchDialog.rows = rows;
      relationSearchDialog.options = rows.map((row) => ({ id: row.id, label: row.label }));
      relationSearchDialog.selectedId = null;
      relationOptions.value = {
        ...relationOptions.value,
        [fieldName]: relationSearchDialog.options,
      };
    } catch (err) {
      relationSearchDialog.error = params.sanitizeError(err, relationSearchDialog.labels.search_failed || '');
    } finally {
      relationSearchDialog.loading = false;
    }
  }

  function confirmRelationSearchSelection(selectOption: (option: RelationOption) => void, rowArg?: RelationSearchRow) {
    const row = rowArg || relationSearchDialog.rows.find((item) => item.id === relationSearchDialog.selectedId);
    if (!row) return;
    selectOption({ id: row.id, label: row.label });
  }

  function selectRelationSearchOption(option: RelationOption, applyOption: (fieldName: string, option: RelationOption) => void) {
    const fieldName = relationSearchDialog.fieldName;
    if (!fieldName) return;
    applyOption(fieldName, option);
    closeRelationSearchDialog();
  }

  return {
    relationOptions,
    relationFieldDescriptors,
    relationKeywords,
    invalidatedRelationKeywords,
    clearedDynamicRelationFields,
    relationSearchDialog,
    deniedRelationModels,
    relationQueryTimers,
    relationKeyword,
    relationOptionsForField,
    selectedRelationOptions,
    setRelationKeywordValue,
    filteredRelationOptions,
    upsertRelationOption,
    mergeRelationOptions,
    closeRelationSearchDialog,
    setRelationSearchKeyword,
    selectRelationSearchRow,
    openRelationSearch,
    runRelationSearch,
    confirmRelationSearchSelection,
    selectRelationSearchOption,
    clearRelationRuntime,
  };
}

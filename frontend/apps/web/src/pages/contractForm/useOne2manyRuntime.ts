import { reactive } from 'vue';
import type { One2ManyColumn, One2ManyInlineRow, RelationOption } from './types';
import {
  appendOne2manyDraftRow,
  buildOne2manyCommandValue,
  collectOne2manyDraftValidationFromRows,
  ensureOne2manyRows,
  initOne2manyRowsFromRelationSource,
  mergeOne2manyHydratedRecords,
  one2manyRowHintsFromPatches,
  removeOne2manyDraftRow,
  restoreOne2manyDraftRow,
  setOne2manyDraftRowField,
} from './one2manyUtils';

function makeOne2manyKey() {
  return `o2m_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`;
}

export function useOne2manyRuntime(params: {
  recordId: () => number;
  originalValues: () => Record<string, unknown>;
  onchangeLinePatches: () => Array<Record<string, unknown>>;
  resolveColumns: (fieldName: string) => One2ManyColumn[];
  resolvePrimaryColumn: (fieldName: string) => string;
  resolveRelationOptions: (fieldName: string) => RelationOption[];
  markFieldChanged: (fieldName: string) => void;
}) {
  const rowsByField = reactive<Record<string, One2ManyInlineRow[]>>({});

  function fieldRows(name: string) {
    return Array.isArray(rowsByField[name]) ? rowsByField[name] : [];
  }

  function visibleRows(name: string) {
    return fieldRows(name).filter((row) => !row.removed);
  }

  function removedRows(name: string) {
    return fieldRows(name).filter((row) => row.removed);
  }

  function ensureRows(name: string) {
    return ensureOne2manyRows(rowsByField, name);
  }

  function clearRows() {
    Object.keys(rowsByField).forEach((key) => {
      delete rowsByField[key];
    });
  }

  function addRow(name: string) {
    appendOne2manyDraftRow({
      rowsByField,
      fieldName: name,
      key: makeOne2manyKey(),
      primary: params.resolvePrimaryColumn(name),
      columns: params.resolveColumns(name),
    });
    params.markFieldChanged(name);
  }

  function setRowField(fieldName: string, rowKey: string, column: One2ManyColumn, value: unknown) {
    const changed = setOne2manyDraftRowField({ rowsByField, fieldName, rowKey, column, value });
    if (changed) params.markFieldChanged(fieldName);
  }

  function removeRow(fieldName: string, rowKey: string) {
    if (removeOne2manyDraftRow(rowsByField, fieldName, rowKey)) params.markFieldChanged(fieldName);
  }

  function restoreRow(fieldName: string, rowKey: string) {
    if (restoreOne2manyDraftRow(rowsByField, fieldName, rowKey)) params.markFieldChanged(fieldName);
  }

  function initRows(name: string, source: unknown) {
    rowsByField[name] = initOne2manyRowsFromRelationSource({
      source,
      relationOptions: params.resolveRelationOptions(name),
      primary: params.resolvePrimaryColumn(name),
    });
  }

  function mergeHydratedRecords(fieldName: string, records: Array<Record<string, unknown>>) {
    mergeOne2manyHydratedRecords({
      rows: ensureRows(fieldName).filter((row) => row.id && !row.isNew),
      columns: params.resolveColumns(fieldName),
      records,
    });
  }

  function buildCommandValue(name: string, mode: 'onchange' | 'write') {
    return buildOne2manyCommandValue(params.originalValues()[name], fieldRows(name), mode);
  }

  function collectValidation() {
    return collectOne2manyDraftValidationFromRows({
      rowsByField,
      recordId: params.recordId(),
      resolvePrimaryColumn: params.resolvePrimaryColumn,
      resolveColumns: params.resolveColumns,
    });
  }

  function rowHints(fieldName: string, row: One2ManyInlineRow) {
    return one2manyRowHintsFromPatches({
      patches: params.onchangeLinePatches(),
      fieldName,
      row,
    });
  }

  function applyLinePatches(linePatches: Array<{ field?: unknown; row_key?: unknown; row_id?: unknown; patch?: unknown }>) {
    if (!Array.isArray(linePatches) || !linePatches.length) return;
    linePatches.forEach((line) => {
      const fieldName = String(line.field || '').trim();
      if (!fieldName) return;
      const rowKey = String(line.row_key || '').trim();
      const rowId = Number(line.row_id || 0);
      const rows = ensureRows(fieldName);
      const row = rows.find((item) => (rowKey && item.key === rowKey) || (rowId > 0 && Number(item.id || 0) === rowId));
      if (!row) return;
      const patch = line.patch;
      if (patch && typeof patch === 'object') {
        row.values = {
          ...(row.values || {}),
          ...(patch as Record<string, unknown>),
        };
      }
    });
  }

  return {
    rowsByField,
    fieldRows,
    visibleRows,
    removedRows,
    ensureRows,
    clearRows,
    addRow,
    setRowField,
    removeRow,
    restoreRow,
    initRows,
    mergeHydratedRecords,
    buildCommandValue,
    collectValidation,
    rowHints,
    applyLinePatches,
  };
}

import type { RelationFallbackAdapter } from './relationFallback.types';

export type CreateRelationFallbackAdapterContext = RelationFallbackAdapter;

export function createRelationFallbackAdapter(context: CreateRelationFallbackAdapterContext): RelationFallbackAdapter {
  return {
    busy: context.busy,
    showOne2manyErrors: context.showOne2manyErrors,
    relationKeyword: context.relationKeyword,
    setRelationKeyword: context.setRelationKeyword,
    relationIds: context.relationIds,
    filteredRelationOptions: context.filteredRelationOptions,
    setRelationMultiField: context.setRelationMultiField,
    addOne2manyRow: context.addOne2manyRow,
    one2manySummary: context.one2manySummary,
    visibleOne2manyRows: context.visibleOne2manyRows,
    one2manyRowStateLabel: context.one2manyRowStateLabel,
    one2manyColumns: context.one2manyColumns,
    setOne2manyRowField: context.setOne2manyRowField,
    removeOne2manyRow: context.removeOne2manyRow,
    one2manyRowErrors: context.one2manyRowErrors,
    one2manyRowHints: context.one2manyRowHints,
    removedOne2manyRows: context.removedOne2manyRows,
    restoreOne2manyRow: context.restoreOne2manyRow,
    one2manyRowLabel: context.one2manyRowLabel,
    selectPlaceholder: context.selectPlaceholder,
    one2manyColumnInputType: context.one2manyColumnInputType,
    one2manyColumnDisplayValue: context.one2manyColumnDisplayValue,
    inputFieldValue: context.inputFieldValue,
    fieldInputType: context.fieldInputType,
    inputPlaceholder: context.inputPlaceholder,
    setTextField: context.setTextField,
  };
}

import type { FormSectionFieldSchema } from './formSection.types';

export type RelationFallbackOption = {
  id: number;
  label: string;
};

export type RelationFallbackRow = {
  key: string;
  values: Record<string, unknown>;
};

export type RelationFallbackColumn = {
  name: string;
  label: string;
  ttype: string;
  required: boolean;
  selection?: Array<[string, string]>;
};

export type RelationFallbackAdapter = {
  busy: boolean;
  showOne2manyErrors: boolean;
  relationKeyword: (name: string) => string;
  setRelationKeyword: (name: string, value: string) => void;
  relationIds: (name: string) => number[];
  selectedRelationOptions: (name: string) => RelationFallbackOption[];
  filteredRelationOptions: (name: string) => RelationFallbackOption[];
  setRelationMultiField: (name: string, target: HTMLSelectElement) => void;
  one2manyCanCreate: (name: string) => boolean;
  addOne2manyRow: (name: string) => void;
  one2manySummary: (name: string) => string;
  visibleOne2manyRows: (name: string) => RelationFallbackRow[];
  one2manyRowStateLabel: (row: RelationFallbackRow) => string;
  one2manyColumns: (name: string) => RelationFallbackColumn[];
  setOne2manyRowField: (name: string, rowKey: string, column: RelationFallbackColumn, value: unknown) => void;
  removeOne2manyRow: (name: string, rowKey: string) => void;
  one2manyRowErrors: (name: string, rowKey: string) => string[];
  one2manyRowHints: (name: string, row: RelationFallbackRow) => string[];
  removedOne2manyRows: (name: string) => RelationFallbackRow[];
  restoreOne2manyRow: (name: string, rowKey: string) => void;
  one2manyRowLabel: (name: string, row: RelationFallbackRow) => string;
  selectPlaceholder: (label: string) => string;
  one2manyColumnInputType: (column: RelationFallbackColumn) => string;
  one2manyColumnDisplayValue: (column: RelationFallbackColumn, value: unknown) => string;
  inputFieldValue: (name: string) => string;
  fieldInputType: (type: string) => string;
  inputPlaceholder: (label: string) => string;
  setTextField: (name: string, value: string) => void;
};

export type RelationFallbackRendererProps = {
  field: FormSectionFieldSchema;
  adapter: RelationFallbackAdapter;
};

import type { FormSectionFieldSchema } from './formSection.types';

export type RelationFieldOption = {
  id: number;
  label: string;
  color?: number | null;
};

export type RelationFieldRow = {
  key: string;
  values: Record<string, unknown>;
};

export type RelationFieldColumn = {
  name: string;
  label: string;
  ttype: string;
  required: boolean;
  readonly?: boolean;
  selection?: Array<[string, string]>;
};

export type RelationFieldAdapter = {
  busy: boolean;
  showOne2manyErrors: boolean;
  relationKeyword: (name: string) => string;
  setRelationKeyword: (name: string, value: string) => void;
  relationIds: (name: string) => number[];
  selectedRelationOptions: (name: string) => RelationFieldOption[];
  filteredRelationOptions: (name: string) => RelationFieldOption[];
  setRelationMultiField: (name: string, target: HTMLSelectElement) => void;
  setRelationIds: (name: string, ids: number[]) => void;
  relationCreateMode: (name: string) => 'none' | 'quick' | 'page';
  relationCreateLabel: (name: string) => string;
  relationInlineCreateLabel: (name: string) => string;
  canInlineCreateRelation: (name: string) => boolean;
  openRelationCreate: (name: string) => void;
  one2manyCanCreate: (name: string) => boolean;
  one2manyCreateLabel: (name: string, fieldLabel?: string) => string;
  addOne2manyRow: (name: string) => void;
  one2manySummary: (name: string) => string;
  visibleOne2manyRows: (name: string) => RelationFieldRow[];
  one2manyRowStateLabel: (row: RelationFieldRow) => string;
  one2manyColumns: (name: string) => RelationFieldColumn[];
  setOne2manyRowField: (name: string, rowKey: string, column: RelationFieldColumn, value: unknown) => void;
  removeOne2manyRow: (name: string, rowKey: string) => void;
  one2manyRowErrors: (name: string, rowKey: string) => string[];
  one2manyRowHints: (name: string, row: RelationFieldRow) => string[];
  removedOne2manyRows: (name: string) => RelationFieldRow[];
  restoreOne2manyRow: (name: string, rowKey: string) => void;
  one2manyRowLabel: (name: string, row: RelationFieldRow) => string;
  selectPlaceholder: (label: string) => string;
  one2manyColumnInputType: (column: RelationFieldColumn) => string;
  one2manyColumnDisplayValue: (column: RelationFieldColumn, value: unknown) => string;
  inputFieldValue: (name: string) => string;
  fieldInputType: (type: string) => string;
  inputPlaceholder: (label: string) => string;
  setTextField: (name: string, value: string) => void;
};

export type X2ManyRelationRendererProps = {
  field: FormSectionFieldSchema;
  adapter: RelationFieldAdapter;
};

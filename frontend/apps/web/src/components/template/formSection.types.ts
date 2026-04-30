import type { FieldDescriptor } from '@sc/schema';

export type TemplateFieldType =
  | 'char'
  | 'text'
  | 'selection'
  | 'many2one'
  | 'boolean'
  | 'date'
  | 'datetime'
  | 'many2many'
  | 'one2many'
  | string;

export type TemplateSelectOption = {
  value: string;
  label: string;
};

export type FormSectionFieldSchema = {
  key: string;
  name: string;
  label: string;
  type: TemplateFieldType;
  widget?: string;
  widgetSemantics?: Record<string, unknown>;
  required: boolean;
  readonly: boolean;

  // Presentational override for current template stage.
  // Prefer replacing with semantic span in later phases.
  spanClass?: string;

  favoriteToggle?: {
    name: string;
    label: string;
    active: boolean;
    readonly: boolean;
    descriptor?: FieldDescriptor;
  };

  // Raw value for readonly display or fallback usage.
  value?: unknown;

  // Value normalized by page layer for direct control binding.
  // For date/datetime, this must already match native input format.
  inputValue?: string | number | boolean | null;
  dateRangeEndField?: string;
  dateRangeEndInputValue?: string | number | boolean | null;

  inputPlaceholder?: string;
  selectionOptions?: TemplateSelectOption[];
  relationOptions?: TemplateSelectOption[];

  // many2one-only relation entry extension
  relationCreateMode?: 'none' | 'quick' | 'page';
  relationInlineCreate?: {
    enabled: boolean;
    createOnNoMatch: boolean;
    nameField: string;
  };
  many2oneCreateToken?: string;
  many2oneSearchToken?: string;
  many2oneTextValue?: string;
  many2oneSearchLabel?: string;
  many2oneCreateLabel?: string;
  many2oneInlineCreateLabel?: string;
  descriptor?: FieldDescriptor;
};

export type FormSectionFieldChange = {
  name: string;
  type: TemplateFieldType;
  widget?: string;
  value: string | number | boolean | null;
  action?: 'change' | 'query' | 'commit';
  descriptor?: FieldDescriptor;
};

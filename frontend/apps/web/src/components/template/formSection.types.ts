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
  required: boolean;
  readonly: boolean;

  // Presentational override for current template stage.
  // Prefer replacing with semantic span in later phases.
  spanClass?: string;

  // Raw value for readonly display or fallback usage.
  value?: unknown;

  // Value normalized by page layer for direct control binding.
  // For date/datetime, this must already match native input format.
  inputValue?: string | number | boolean | null;

  inputPlaceholder?: string;
  selectionOptions?: TemplateSelectOption[];
  relationOptions?: TemplateSelectOption[];

  // many2one-only relation entry extension
  relationCreateMode?: 'none' | 'quick' | 'page';
  many2oneCreateToken?: string;
  descriptor?: FieldDescriptor;
};

export type FormSectionFieldChange = {
  name: string;
  type: TemplateFieldType;
  value: string | number | boolean | null;
  descriptor?: FieldDescriptor;
};

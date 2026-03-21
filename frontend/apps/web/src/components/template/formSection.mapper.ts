import type { FieldDescriptor } from '@sc/schema';
import type { FormSectionFieldSchema, TemplateSelectOption } from './formSection.types';

export type ResolveTemplateInputValueOptions = {
  fieldName: string;
  fieldType: string;
  rawValue: unknown;
  resolveMany2oneValue: (fieldName: string) => string;
  normalizeDateInputValue: (value: unknown) => string;
  normalizeDatetimeInputValue: (value: unknown) => string;
  resolveTextInputValue: (fieldName: string) => string;
};

export type FormSectionMapperFieldNode = {
  key: string;
  name: string;
  label: string;
  required: boolean;
  readonly: boolean;
  descriptor?: FieldDescriptor;
};

export type BuildFormSectionFieldSchemasOptions = {
  resolveFieldType: (descriptor?: FieldDescriptor) => string;
  resolveRequired: (field: FormSectionMapperFieldNode) => boolean;
  resolveSpanClass: (field: FormSectionMapperFieldNode) => string;
  resolveInputValue: (fieldName: string, fieldType: string) => string | number | boolean | null;
  resolveRawValue: (fieldName: string) => unknown;
  resolveInputPlaceholder: (fieldLabel: string) => string;
  resolveSelectionOptions: (descriptor?: FieldDescriptor) => TemplateSelectOption[];
  resolveRelationOptions: (fieldName: string) => TemplateSelectOption[];
  resolveRelationCreateMode: (fieldName: string, descriptor?: FieldDescriptor) => 'none' | 'quick' | 'page';
  many2oneCreateToken?: string;
};

export function buildFormSectionFieldSchemas(
  fields: FormSectionMapperFieldNode[],
  options: BuildFormSectionFieldSchemasOptions,
): FormSectionFieldSchema[] {
  return fields.map((field) => {
    const type = options.resolveFieldType(field.descriptor) || 'char';
    return {
      key: field.key,
      name: field.name,
      label: field.label,
      type,
      required: options.resolveRequired(field),
      readonly: field.readonly,
      spanClass: options.resolveSpanClass(field),
      value: options.resolveRawValue(field.name),
      inputValue: options.resolveInputValue(field.name, type),
      inputPlaceholder: options.resolveInputPlaceholder(field.label),
      selectionOptions: options.resolveSelectionOptions(field.descriptor),
      relationOptions: options.resolveRelationOptions(field.name),
      relationCreateMode: type === 'many2one' ? options.resolveRelationCreateMode(field.name, field.descriptor) : 'none',
      many2oneCreateToken: type === 'many2one' ? options.many2oneCreateToken : undefined,
      descriptor: field.descriptor,
    };
  });
}

export function resolveTemplateInputValue(options: ResolveTemplateInputValueOptions): string | number | boolean | null {
  const type = String(options.fieldType || '').trim().toLowerCase();
  if (type === 'many2one') {
    return options.resolveMany2oneValue(options.fieldName);
  }
  const raw = options.rawValue;
  if (raw === null || raw === undefined || raw === false) {
    return '';
  }
  if (type === 'date') {
    return options.normalizeDateInputValue(raw);
  }
  if (type === 'datetime') {
    return options.normalizeDatetimeInputValue(raw);
  }
  if (typeof raw === 'number' || typeof raw === 'boolean') {
    return raw;
  }
  return options.resolveTextInputValue(options.fieldName);
}

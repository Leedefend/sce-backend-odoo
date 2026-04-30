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
  widget?: string;
  widgetSemantics?: Record<string, unknown>;
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
  resolveRelationInlineCreate: (fieldName: string, descriptor?: FieldDescriptor) => FormSectionFieldSchema['relationInlineCreate'];
  resolveRelationTextValue: (fieldName: string) => string;
  resolveRelationSearchLabel: (fieldName: string, descriptor?: FieldDescriptor) => string;
  resolveRelationCreateLabel: (fieldName: string, descriptor?: FieldDescriptor) => string;
  resolveRelationInlineCreateLabel: (fieldName: string, descriptor?: FieldDescriptor, keyword?: string) => string;
  many2oneCreateToken?: string;
  many2oneSearchToken?: string;
};

export function buildFormSectionFieldSchemas(
  fields: FormSectionMapperFieldNode[],
  options: BuildFormSectionFieldSchemasOptions,
): FormSectionFieldSchema[] {
  return fields.map((field) => {
    const type = options.resolveFieldType(field.descriptor) || 'char';
    const descriptorWidget = field.descriptor && typeof field.descriptor === 'object'
      ? String((field.descriptor as Record<string, unknown>).widget || '').trim()
      : '';
    const widget = String(field.widget || descriptorWidget || '').trim().toLowerCase();
    const semantics = field.widgetSemantics && typeof field.widgetSemantics === 'object' ? field.widgetSemantics : {};
    const dateRangeEndField = widget === 'daterange' && String(semantics.kind || '').trim() === 'date_range'
      ? String(semantics.end_field || '').trim()
      : '';
    return {
      key: field.key,
      name: field.name,
      label: field.label,
      type,
      widget,
      widgetSemantics: semantics,
      required: options.resolveRequired(field),
      readonly: field.readonly,
      spanClass: options.resolveSpanClass(field),
      value: options.resolveRawValue(field.name),
      inputValue: options.resolveInputValue(field.name, type),
      dateRangeEndField: dateRangeEndField || undefined,
      dateRangeEndInputValue: dateRangeEndField ? options.resolveInputValue(dateRangeEndField, type) : undefined,
      inputPlaceholder: options.resolveInputPlaceholder(field.label),
      selectionOptions: options.resolveSelectionOptions(field.descriptor),
      relationOptions: options.resolveRelationOptions(field.name),
      relationCreateMode: type === 'many2one' ? options.resolveRelationCreateMode(field.name, field.descriptor) : 'none',
      relationInlineCreate: type === 'many2one' ? options.resolveRelationInlineCreate(field.name, field.descriptor) : undefined,
      many2oneCreateToken: type === 'many2one' ? options.many2oneCreateToken : undefined,
      many2oneSearchToken: type === 'many2one' ? options.many2oneSearchToken : undefined,
      many2oneTextValue: type === 'many2one' ? options.resolveRelationTextValue(field.name) : undefined,
      many2oneSearchLabel: type === 'many2one' ? options.resolveRelationSearchLabel(field.name, field.descriptor) : undefined,
      many2oneCreateLabel: type === 'many2one' ? options.resolveRelationCreateLabel(field.name, field.descriptor) : undefined,
      many2oneInlineCreateLabel: type === 'many2one'
        ? options.resolveRelationInlineCreateLabel(field.name, field.descriptor, options.resolveRelationTextValue(field.name))
        : undefined,
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

import type { FieldDescriptor } from '@sc/schema';
import {
  buildFormSectionFieldSchemas,
  resolveTemplateInputValue,
  type FormSectionMapperFieldNode,
} from './formSection.mapper';

export type CreateFormSectionFieldSchemaBuilderContext = {
  resolveFieldType: (descriptor?: FieldDescriptor) => string;
  resolveRequired: (field: FormSectionMapperFieldNode) => boolean;
  resolveSpanClass: (field: FormSectionMapperFieldNode) => string;
  resolveRawValue: (fieldName: string) => unknown;
  resolveMany2oneValue: (fieldName: string) => string;
  normalizeDateInputValue: (value: unknown) => string;
  normalizeDatetimeInputValue: (value: unknown) => string;
  resolveTextInputValue: (fieldName: string) => string;
  resolveInputPlaceholder: (fieldLabel: string) => string;
  resolveSelectionOptions: (descriptor?: FieldDescriptor) => Array<{ value: string; label: string }>;
  resolveRelationOptions: (fieldName: string) => Array<{ value: string; label: string }>;
  resolveRelationCreateMode: (fieldName: string, descriptor?: FieldDescriptor) => 'none' | 'quick' | 'page';
  many2oneCreateToken?: string;
};

export function createFormSectionFieldSchemaBuilder(context: CreateFormSectionFieldSchemaBuilderContext) {
  return (fields: FormSectionMapperFieldNode[]) => buildFormSectionFieldSchemas(fields, {
    resolveFieldType: context.resolveFieldType,
    resolveRequired: context.resolveRequired,
    resolveSpanClass: context.resolveSpanClass,
    resolveRawValue: context.resolveRawValue,
    resolveInputValue: (fieldName, type) => resolveTemplateInputValue({
      fieldName,
      fieldType: type,
      rawValue: context.resolveRawValue(fieldName),
      resolveMany2oneValue: context.resolveMany2oneValue,
      normalizeDateInputValue: context.normalizeDateInputValue,
      normalizeDatetimeInputValue: context.normalizeDatetimeInputValue,
      resolveTextInputValue: context.resolveTextInputValue,
    }),
    resolveInputPlaceholder: context.resolveInputPlaceholder,
    resolveSelectionOptions: context.resolveSelectionOptions,
    resolveRelationOptions: context.resolveRelationOptions,
    resolveRelationCreateMode: context.resolveRelationCreateMode,
    many2oneCreateToken: context.many2oneCreateToken,
  });
}

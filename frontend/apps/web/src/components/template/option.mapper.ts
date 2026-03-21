import type { FieldDescriptor } from '@sc/schema';
import type { TemplateSelectOption } from './formSection.types';

export type RelationOptionLike = {
  id: number;
  label: string;
};

export function mapDescriptorSelectionOptions(descriptor?: FieldDescriptor): TemplateSelectOption[] {
  if (!Array.isArray(descriptor?.selection)) return [];
  return descriptor.selection.map((option) => ({
    value: String(option[0]),
    label: String(option[1]),
  }));
}

export function mapRelationOptions(options: RelationOptionLike[]): TemplateSelectOption[] {
  return options.map((option) => ({
    value: String(option.id),
    label: option.label,
  }));
}

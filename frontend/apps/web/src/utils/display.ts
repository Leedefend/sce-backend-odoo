import type { FieldDescriptor } from '@sc/schema';

export type DisplayFormatOptions = {
  emptyText?: string;
  booleanTrueText?: string;
  booleanFalseText?: string;
};

const DEFAULT_OPTIONS: Required<DisplayFormatOptions> = {
  emptyText: '-',
  booleanTrueText: 'Yes',
  booleanFalseText: 'No',
};

function normalizeOptions(options?: DisplayFormatOptions): Required<DisplayFormatOptions> {
  return {
    emptyText: options?.emptyText ?? DEFAULT_OPTIONS.emptyText,
    booleanTrueText: options?.booleanTrueText ?? DEFAULT_OPTIONS.booleanTrueText,
    booleanFalseText: options?.booleanFalseText ?? DEFAULT_OPTIONS.booleanFalseText,
  };
}

export function formatDisplayValue(
  value: unknown,
  field?: Pick<FieldDescriptor, 'ttype' | 'type' | 'selection'>,
  options?: DisplayFormatOptions,
): string {
  const normalized = normalizeOptions(options);
  const fieldType = field?.ttype || field?.type;

  if (value === null || value === undefined || value === '') {
    return normalized.emptyText;
  }

  if (typeof value === 'boolean') {
    return value ? normalized.booleanTrueText : normalized.booleanFalseText;
  }

  if (fieldType === 'boolean') {
    return value ? normalized.booleanTrueText : normalized.booleanFalseText;
  }

  if (fieldType === 'selection' && Array.isArray(field?.selection)) {
    const match = field.selection.find((item) => item[0] === value);
    return match ? String(match[1]) : String(value);
  }

  if (fieldType === 'many2one' && Array.isArray(value)) {
    if (value.length > 1 && value[1] != null) {
      return String(value[1]);
    }
    if (value[0] != null) {
      return String(value[0]);
    }
    return normalized.emptyText;
  }

  if (Array.isArray(value)) {
    if (!value.length) {
      return normalized.emptyText;
    }
    return value.map((item) => String(item)).join(', ');
  }

  if (typeof value === 'object') {
    return normalized.emptyText;
  }

  return String(value);
}

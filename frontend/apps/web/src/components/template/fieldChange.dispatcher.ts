import type { FormSectionFieldChange } from './formSection.types';

export type FieldChangeDispatcherHandlers = {
  onBoolean: (name: string, value: boolean) => void;
  onSelection: (name: string, value: string) => void;
  onMany2one: (name: string, descriptor: FormSectionFieldChange['descriptor'], value: string) => void;
  onText: (name: string, value: string) => void;
};

function normalizeText(value: string | number | boolean | null): string {
  if (value === null || value === undefined) return '';
  return String(value);
}

function normalizeBoolean(value: string | number | boolean | null): boolean {
  if (typeof value === 'boolean') return value;
  if (typeof value === 'number') return value !== 0;
  const normalized = String(value ?? '').trim().toLowerCase();
  return normalized === '1' || normalized === 'true' || normalized === 'yes' || normalized === 'on';
}

export function dispatchTemplateFieldChange(
  payload: FormSectionFieldChange,
  handlers: FieldChangeDispatcherHandlers,
): void {
  const fieldName = String(payload.name || '').trim();
  if (!fieldName) return;
  const type = String(payload.type || '').trim().toLowerCase();
  switch (type) {
    case 'boolean': {
      handlers.onBoolean(fieldName, normalizeBoolean(payload.value));
      return;
    }
    case 'selection': {
      handlers.onSelection(fieldName, normalizeText(payload.value));
      return;
    }
    case 'many2one': {
      handlers.onMany2one(fieldName, payload.descriptor, normalizeText(payload.value));
      return;
    }
    case 'date':
    case 'datetime':
    case 'char':
    case 'text':
    default: {
      handlers.onText(fieldName, normalizeText(payload.value));
    }
  }
}


import type { FieldDescriptor } from '@sc/schema';

export type DisplayFormatOptions = {
  emptyText?: string;
  booleanTrueText?: string;
  booleanFalseText?: string;
};

const DEFAULT_OPTIONS: Required<DisplayFormatOptions> = {
  emptyText: '-',
  booleanTrueText: '是',
  booleanFalseText: '否',
};

function normalizeOptions(options?: DisplayFormatOptions): Required<DisplayFormatOptions> {
  return {
    emptyText: options?.emptyText ?? DEFAULT_OPTIONS.emptyText,
    booleanTrueText: options?.booleanTrueText ?? DEFAULT_OPTIONS.booleanTrueText,
    booleanFalseText: options?.booleanFalseText ?? DEFAULT_OPTIONS.booleanFalseText,
  };
}

function numericValue(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value !== 'string') return null;
  const normalized = value.replace(/,/g, '').trim();
  if (!normalized) return null;
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : null;
}

export function formatAttachmentReferenceValue(value: unknown): string {
  return parseAttachmentReferenceLinks(value).map((item) => item.name).join('、');
}

export function parseAttachmentReferenceLinks(value: unknown): Array<{ name: string; url: string }> {
  const rawItems = Array.isArray(value) ? value.map((item) => String(item ?? '')) : [String(value ?? '')];
  const seen = new Set<string>();
  const links: Array<{ name: string; url: string }> = [];
  const urlStartPattern = '(?:legacy-file-id|legacy-file|https?|file):\\/\\/|\\/web\\/content\\/';
  const itemBoundary = new RegExp(`\\s+(?=[^\\s|]+\\s+\\|\\s+(?:${urlStartPattern}))`, 'i');
  const itemPattern = new RegExp(`^(.*?)\\s+\\|\\s+((?:${urlStartPattern}).+)$`, 'i');

  rawItems
    .flatMap((item) => item.split(itemBoundary))
    .forEach((item) => {
      const raw = item.trim();
      if (!raw) return;
      const match = raw.match(itemPattern);
      if (!match) return;
      const name = match[1].trim();
      const url = match[2].trim();
      const key = `${name}\n${url}`;
      if (!name || !url || seen.has(key)) return;
      seen.add(key);
      links.push({ name, url });
    });

  return links;
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

  if (fieldType === 'boolean') {
    return value ? normalized.booleanTrueText : normalized.booleanFalseText;
  }

  if (typeof value === 'boolean') {
    return value ? String(value) : normalized.emptyText;
  }

  if (fieldType === 'selection' && Array.isArray(field?.selection)) {
    const match = field.selection.find((item) => item[0] === value);
    return match ? String(match[1]) : String(value);
  }

  if (fieldType === 'integer' || fieldType === 'float' || fieldType === 'monetary') {
    const parsed = numericValue(value);
    if (parsed !== null) {
      return parsed.toLocaleString('zh-CN', {
        maximumFractionDigits: fieldType === 'integer' ? 0 : 2,
        minimumFractionDigits: fieldType === 'integer' ? 0 : 2,
      });
    }
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
    const attachmentText = formatAttachmentReferenceValue(value);
    if (attachmentText && value.some((item) => /\|\s*(?:(?:legacy-file-id|legacy-file|https?|file):\/\/|\/web\/content\/)/i.test(String(item ?? '')))) {
      return attachmentText;
    }
    return value.map((item) => String(item)).join(', ');
  }

  if (typeof value === 'object') {
    return normalized.emptyText;
  }

  const rawText = String(value);
  if (/\|\s*(?:(?:legacy-file-id|legacy-file|https?|file):\/\/|\/web\/content\/)/i.test(rawText)) {
    return formatAttachmentReferenceValue(rawText) || rawText;
  }
  return rawText;
}

export type ValidationField = { kind: string; name: string; label: string };

export function focusProductFormValidationError(message: string, fields: ValidationField[]) {
  const text = String(message || '');
  const field = fields.find((item) => item.kind === 'field' && Boolean(item.label) && text.includes(item.label));
  const selector = field
    ? `[data-field-name="${CSS.escape(field.name)}"]`
    : '[data-product-page-mode="form"] [aria-required="true"]';
  const container = document.querySelector<HTMLElement>(selector);
  const control = container?.matches('input, select, textarea, button')
    ? container
    : container?.querySelector<HTMLElement>('input, select, textarea, button, [tabindex]');
  control?.focus();
  container?.scrollIntoView({ block: 'center', behavior: 'smooth' });
}

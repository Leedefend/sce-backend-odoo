import assert from 'node:assert/strict';
import { resolveFieldSpanClass } from '../../frontend/apps/web/src/components/template/fieldSpan.mapper.ts';

const matrix = [
  { fieldType: 'char', expected: 'field--normal' },
  { fieldType: 'monetary', expected: 'field--normal' },
  { fieldType: 'date', expected: 'field--normal' },
  { fieldType: 'text', expected: 'field--full' },
  { fieldType: 'html', expected: 'field--full' },
  { fieldType: 'many2many', expected: 'field--full' },
  { fieldType: 'one2many', expected: 'field--full' },
];

for (const row of matrix) {
  assert.equal(resolveFieldSpanClass({ fieldType: row.fieldType }), row.expected, row.fieldType);
}

console.log(`[frontend_form_canvas_layout_contract_test] PASS matrix=${matrix.length}`);

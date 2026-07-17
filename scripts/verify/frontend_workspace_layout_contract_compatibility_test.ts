import assert from 'node:assert/strict';
import {
  contractContentLayoutMode,
  resolveContentLayoutMode,
  type PageKind,
} from '../../frontend/apps/web/src/components/design-system/pageWidth.ts';

type MatrixRow = {
  name: string;
  contract: Record<string, unknown>;
  pageKind: PageKind;
  expected: string;
};

const resolve = (contract: Record<string, unknown>, pageKind: PageKind) => resolveContentLayoutMode({
  contractContentLayout: contractContentLayoutMode(contract),
  pageKind,
});

const matrix: MatrixRow[] = [
  { name: 'new field wins over legacy', contract: { layout: { content_layout_mode: 'data-grid', width_mode: 'focused' } }, pageKind: 'create', expected: 'data-grid' },
  { name: 'legacy data', contract: { layout: { width_mode: 'data' } }, pageKind: 'list', expected: 'data-grid' },
  { name: 'legacy focused', contract: { layout: { width_mode: 'focused' } }, pageKind: 'create', expected: 'focused-form' },
  { name: 'legacy standard detail', contract: { layout: { width_mode: 'standard' } }, pageKind: 'detail', expected: 'record-grid' },
  { name: 'legacy standard edit', contract: { layout: { width_mode: 'standard' } }, pageKind: 'edit', expected: 'form-grid' },
  { name: 'legacy standard create', contract: { layout: { width_mode: 'standard' } }, pageKind: 'create', expected: 'focused-form' },
  { name: 'legacy fluid visualization', contract: { layout: { width_mode: 'fluid' } }, pageKind: 'visualization', expected: 'data-grid' },
  { name: 'invalid new field safely falls back without legacy override', contract: { layout: { content_layout_mode: 'invalid', width_mode: 'standard' } }, pageKind: 'edit', expected: 'form-grid' },
  { name: 'empty unknown', contract: {}, pageKind: 'unknown', expected: 'record-grid' },
  { name: 'legacy root location', contract: { layout: { width_mode: 'focused' } }, pageKind: 'create', expected: 'focused-form' },
  { name: 'legacy page location', contract: { page: { layout: { width_mode: 'data' } } }, pageKind: 'list', expected: 'data-grid' },
  { name: 'legacy presentation location', contract: { presentation: { layout: { width_mode: 'standard' } } }, pageKind: 'edit', expected: 'form-grid' },
];

for (const row of matrix) {
  assert.equal(resolve(row.contract, row.pageKind), row.expected, row.name);
}

assert.deepEqual(
  contractContentLayoutMode({ layout: { content_layout_mode: 'form-grid', width_mode: 'focused' } }),
  { source: 'content_layout_mode', value: 'form-grid' },
  'selection records new-field authority',
);
assert.deepEqual(
  contractContentLayoutMode({ presentation: { layout: { width_mode: 'standard' } } }),
  { source: 'legacy_width_mode', value: 'standard' },
  'selection records compatibility authority',
);

console.log(`[frontend_workspace_layout_contract_compatibility_test] PASS matrix=${matrix.length}`);

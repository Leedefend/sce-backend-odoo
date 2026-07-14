import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(new URL('..', import.meta.url).pathname);
const styles = fs.readFileSync(path.join(root, 'src/styles/design-system.css'), 'utf8');
const patterns = fs.readFileSync(path.join(root, 'src/styles/product-patterns.css'), 'utf8');
const session = fs.readFileSync(path.join(root, 'src/stores/session.ts'), 'utf8');

const requiredTokens = [
  '--sc-product-space-1', '--sc-product-page-gutter', '--sc-product-page-max-width',
  '--sc-product-control-height', '--sc-product-table-row-height', '--sc-product-radius-panel',
];
for (const token of requiredTokens) {
  if (!styles.includes(token)) throw new Error(`missing design token: ${token}`);
}
for (const pattern of ['.sc-product-workspace-stack', '.sc-product-table', '.amount']) {
  if (!patterns.includes(pattern)) throw new Error(`missing product pattern: ${pattern}`);
}
if (!session.includes('Array.isArray(releaseNavigation?.nav)')) throw new Error('authoritative release nav handling missing');
if (session.includes('find(nav => nav.length > 0)')) throw new Error('unsafe non-empty navigation fallback detected');
console.log('[frontend_product_baseline_guard] PASS');

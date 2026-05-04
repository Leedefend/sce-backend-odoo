import { cpSync, existsSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const source = resolve(process.cwd(), 'dist/build/h5');
const target = process.env.SC_MOBILE_HARMONY_WINDOWS_DIR || '/mnt/c/Users/12472/sce-mobile-harmony-h5';

if (!existsSync(source)) {
  console.error(`harmony_h5 build output not found: ${source}`);
  process.exit(1);
}

mkdirSync(target, { recursive: true });
cpSync(source, target, { recursive: true, force: true });

console.log(`harmony_h5 project synced to ${target}`);

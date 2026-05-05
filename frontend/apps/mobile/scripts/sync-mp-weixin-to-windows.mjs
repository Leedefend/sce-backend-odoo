import { cpSync, existsSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const source = resolve(process.cwd(), 'dist/build/mp-weixin');
const target = process.env.SC_MOBILE_WX_WINDOWS_DIR || '/mnt/c/Users/12472/sce-mobile-mp-weixin';

if (!existsSync(source)) {
  console.error(`mp-weixin build output not found: ${source}`);
  process.exit(1);
}

mkdirSync(target, { recursive: true });
cpSync(source, target, { recursive: true, force: true });

console.log(`mp-weixin project synced to ${target}`);

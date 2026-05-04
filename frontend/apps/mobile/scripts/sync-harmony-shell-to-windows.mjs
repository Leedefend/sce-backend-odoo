import { cpSync, existsSync, mkdirSync, rmSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(__dirname, '../../../..');
const sourceDir = resolve(repoRoot, 'frontend/apps/mobile-harmony-shell');
const targetDir = process.env.SC_MOBILE_HARMONY_SHELL_WINDOWS_DIR || '/mnt/c/Users/12472/sce-mobile-harmony-shell';

if (!existsSync(sourceDir)) {
  throw new Error(`Harmony shell source directory not found: ${sourceDir}`);
}

mkdirSync(targetDir, { recursive: true });

for (const name of [
  'AppScope',
  'entry',
  'hvigor',
  'build-profile.json5',
  'hvigorfile.ts',
  'oh-package.json5',
  'oh-package-lock.json5',
]) {
  const target = resolve(targetDir, name);
  if (existsSync(target)) {
    rmSync(target, { recursive: true, force: true });
  }
}

cpSync(sourceDir, targetDir, { recursive: true, force: true });

console.log(`harmony_shell project synced to ${targetDir}`);

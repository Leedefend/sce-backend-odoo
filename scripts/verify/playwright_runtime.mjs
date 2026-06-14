import fs from 'node:fs';
import { createRequire } from 'node:module';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');

function isExecutable(filePath) {
  try {
    fs.accessSync(filePath, fs.constants.X_OK);
    return true;
  } catch {
    return false;
  }
}

function revisionOf(dirName) {
  const match = String(dirName || '').match(/-(\d+)$/);
  return match ? Number(match[1]) : 0;
}

function cachedChromiumCandidates() {
  const root = process.env.PLAYWRIGHT_BROWSERS_PATH || path.join(os.homedir(), '.cache', 'ms-playwright');
  let entries = [];
  try {
    entries = fs.readdirSync(root, { withFileTypes: true });
  } catch {
    return [];
  }
  return entries
    .filter((entry) => entry.isDirectory() && entry.name.startsWith('chromium-'))
    .sort((a, b) => revisionOf(b.name) - revisionOf(a.name))
    .map((entry) => path.join(root, entry.name, 'chrome-linux64', 'chrome'))
    .filter(isExecutable);
}

export function resolveChromiumExecutablePath() {
  const explicit = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE;
  if (explicit && isExecutable(explicit)) {
    return explicit;
  }
  return cachedChromiumCandidates()[0] || '';
}

function loadPlaywrightChromium() {
  const modulePath = require.resolve('playwright', {
    paths: [
      process.cwd(),
      path.join(repoRoot, 'frontend', 'apps', 'web', 'node_modules'),
      path.join(repoRoot, 'frontend', 'node_modules'),
    ],
  });
  return require(modulePath).chromium;
}

export async function launchChromium(options = {}) {
  const chromium = loadPlaywrightChromium();
  const executablePath = resolveChromiumExecutablePath();
  if (executablePath) {
    return chromium.launch({ ...options, executablePath });
  }
  return chromium.launch(options);
}

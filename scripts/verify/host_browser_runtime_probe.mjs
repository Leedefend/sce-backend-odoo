import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const playwrightEntry = require.resolve('playwright', { paths: [path.resolve(process.cwd(), 'frontend')] });
const { chromium } = require(playwrightEntry);

const LOCAL_RUNTIME_LIB_ROOT = path.resolve(process.cwd(), '.codex-runtime', 'playwright-libs');
const ARTIFACTS_DIR = String(process.env.ARTIFACTS_DIR || 'artifacts').trim() || 'artifacts';
const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'host-browser-runtime-probe', ts);

function primeLocalRuntimeLibraries() {
  const candidateDirs = [
    path.join(LOCAL_RUNTIME_LIB_ROOT, 'usr', 'lib', 'x86_64-linux-gnu'),
    path.join(LOCAL_RUNTIME_LIB_ROOT, 'lib', 'x86_64-linux-gnu'),
  ].filter((dir) => fs.existsSync(dir));
  if (!candidateDirs.length) return;
  const existing = String(process.env.LD_LIBRARY_PATH || '').trim();
  const segments = existing ? existing.split(':').filter(Boolean) : [];
  const merged = [...segments, ...candidateDirs].filter((item, idx, arr) => item && arr.indexOf(item) === idx);
  process.env.LD_LIBRARY_PATH = merged.join(':');
}

function writeJson(fileName, payload) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, fileName), `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
}

primeLocalRuntimeLibraries();

const summary = {
  status: 'PENDING',
  ts,
  runtime_root: LOCAL_RUNTIME_LIB_ROOT,
  ld_library_path: String(process.env.LD_LIBRARY_PATH || ''),
};

let browser;
try {
  browser = await chromium.launch({
    headless: true,
    timeout: 20000,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-seccomp-filter-sandbox',
      '--disable-namespace-sandbox',
    ],
  });
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto('about:blank', { waitUntil: 'domcontentloaded', timeout: 10000 });
  await context.close();
  summary.status = 'PASS';
  console.log('[host_browser_runtime_probe] PASS launch and about:blank ok');
  console.log(`[host_browser_runtime_probe] artifacts: ${outDir}`);
  writeJson('summary.json', summary);
} catch (error) {
  summary.status = 'FAIL';
  summary.error = String(error?.message || error);
  console.log('[host_browser_runtime_probe] FAIL launch probe');
  console.log(`[host_browser_runtime_probe] artifacts: ${outDir}`);
  writeJson('summary.json', summary);
  throw error;
} finally {
  if (browser) {
    await browser.close().catch(() => {});
  }
}

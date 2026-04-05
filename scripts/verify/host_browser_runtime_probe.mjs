import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const playwrightEntry = require.resolve('playwright', { paths: [path.resolve(process.cwd(), 'frontend')] });
const { chromium } = require(playwrightEntry);

const LOCAL_RUNTIME_LIB_ROOT = path.resolve(process.cwd(), '.codex-runtime', 'playwright-libs');
const ARTIFACTS_DIR = String(process.env.ARTIFACTS_DIR || 'artifacts').trim() || 'artifacts';
const FULL_CHROME_PATH = '/home/odoo/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome';
const PROBE_MAX_AGE_SEC = Number(process.env.HOST_RUNTIME_PROBE_MAX_AGE_SEC || 0);
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

function findRecentPassProbe(maxAgeSec) {
  if (!(Number.isFinite(maxAgeSec) && maxAgeSec > 0)) return null;
  const rootDir = path.join(ARTIFACTS_DIR, 'codex', 'host-browser-runtime-probe');
  if (!fs.existsSync(rootDir)) return null;
  const nowMs = Date.now();
  const entries = fs.readdirSync(rootDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => ({
      name: entry.name,
      fullPath: path.join(rootDir, entry.name),
    }))
    .sort((left, right) => right.name.localeCompare(left.name));
  for (const entry of entries) {
    const summaryPath = path.join(entry.fullPath, 'summary.json');
    if (!fs.existsSync(summaryPath)) continue;
    try {
      const payload = JSON.parse(fs.readFileSync(summaryPath, 'utf8'));
      if (String(payload?.status || '') !== 'PASS') continue;
      const stat = fs.statSync(summaryPath);
      const ageSec = (nowMs - stat.mtimeMs) / 1000;
      if (ageSec <= maxAgeSec) {
        return {
          summaryPath,
          age_sec: Number(ageSec.toFixed(3)),
          source_ts: String(payload?.ts || entry.name),
        };
      }
    } catch {}
  }
  return null;
}

function shouldUseFullChromeFallback(errorMessage) {
  const text = String(errorMessage || '').toLowerCase();
  return (
    text.includes('error while loading shared libraries')
    || text.includes('sandbox_host_linux.cc')
    || text.includes('operation not permitted')
    || text.includes('target page, context or browser has been closed')
  );
}

primeLocalRuntimeLibraries();

const summary = {
  status: 'PENDING',
  ts,
  runtime_root: LOCAL_RUNTIME_LIB_ROOT,
  ld_library_path: String(process.env.LD_LIBRARY_PATH || ''),
  probe_cache_max_age_sec: PROBE_MAX_AGE_SEC,
};

const recentPass = findRecentPassProbe(PROBE_MAX_AGE_SEC);
if (recentPass) {
  summary.status = 'PASS';
  summary.launch_mode = 'cached_recent_pass';
  summary.cached_from = recentPass;
  console.log('[host_browser_runtime_probe] PASS reused recent probe result');
  console.log(`[host_browser_runtime_probe] artifacts: ${outDir}`);
  writeJson('summary.json', summary);
  process.exit(0);
}

let browser;
try {
  const launchBase = {
    headless: true,
    timeout: 20000,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-seccomp-filter-sandbox',
      '--disable-namespace-sandbox',
      '--disable-crash-reporter',
      '--disable-crashpad-for-testing',
    ],
  };
  const launchProfiles = [
    { mode: 'default', options: launchBase, attempts: 3 },
    { mode: 'full_chrome_fallback', options: { ...launchBase, executablePath: FULL_CHROME_PATH }, attempts: 2 },
    { mode: 'default_retry_tail', options: launchBase, attempts: 1 },
  ];
  let lastError;
  summary.launch_attempts = [];
  for (const profile of launchProfiles) {
    if (profile.mode === 'full_chrome_fallback' && !fs.existsSync(FULL_CHROME_PATH)) continue;
    if (profile.mode === 'full_chrome_fallback' && !shouldUseFullChromeFallback(String(lastError?.message || lastError || summary.default_launch_error || ''))) {
      continue;
    }
    for (let attempt = 1; attempt <= profile.attempts; attempt += 1) {
      try {
        browser = await chromium.launch(profile.options);
        summary.launch_mode = profile.mode;
        summary.launch_attempt = attempt;
        break;
      } catch (error) {
        lastError = error;
        const message = String(error?.message || error);
        summary.default_launch_error = message;
        summary.launch_attempts.push({ mode: profile.mode, attempt, error: message });
        await new Promise((resolve) => setTimeout(resolve, attempt * 400));
      }
    }
    if (browser) break;
  }
  if (!browser) throw lastError;

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

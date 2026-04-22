import fs from 'node:fs';
import path from 'node:path';
import { bootstrapPortalBrowserAuth, launchPortalChromium, resolvePortalSmokeConfig, waitForPortalBootstrapReady } from './playwright_portal_bootstrap.mjs';

const { baseUrl: BASE_URL, apiBaseUrl: API_BASE_URL, dbName: DB_NAME, login: LOGIN, password: PASSWORD, artifactsDir: ARTIFACTS_DIR } = resolvePortalSmokeConfig();
const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'release-navigation-browser-smoke', ts);
const EXPECTED_ROOT_LABEL = '系统菜单';
const MIN_EXPECTED_LEAF_COUNT = 6;
const EXPECTED_SCENE_KEY_OPTIONS = [
  ['projects.intake', 'project.initiation'],
  ['project.management'],
  ['my_work.workspace'],
];

fs.mkdirSync(outDir, { recursive: true });

const summary = {
  base_url: BASE_URL,
  db_name: DB_NAME,
  login: LOGIN,
  expected_root_label: EXPECTED_ROOT_LABEL,
  min_expected_leaf_count: MIN_EXPECTED_LEAF_COUNT,
  expected_scene_key_options: EXPECTED_SCENE_KEY_OPTIONS,
  console_errors: [],
  page_errors: [],
  cases: [],
};

function log(message) {
  console.log(`[release_navigation_browser_smoke] ${message}`);
}

function writeJson(fileName, payload) {
  fs.writeFileSync(path.join(outDir, fileName), `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function recoverFromTransientFailure(page) {
  const retryButton = page.getByRole('button', { name: /Retry|重试/ });
  if (await retryButton.count()) {
    await retryButton.first().click().catch(() => {});
  } else {
    await page.reload({ waitUntil: 'domcontentloaded' }).catch(() => {});
  }
  await page.waitForTimeout(1500);
}

async function waitForSidebar(page) {
  let lastError;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      await page.locator('.sidebar').waitFor({ timeout: 20000 });
      return;
    } catch (error) {
      lastError = error;
      await recoverFromTransientFailure(page);
    }
  }
  throw lastError;
}

async function expandSidebarTree(page) {
  for (let round = 0; round < 3; round += 1) {
    const toggles = page.locator('.sidebar .toggle');
    const count = await toggles.count();
    if (!count) return;
    for (let index = 0; index < count; index += 1) {
      const toggle = toggles.nth(index);
      const marker = String((await toggle.textContent().catch(() => '')) || '').trim();
      if (marker.includes('▸')) {
        await toggle.click().catch(() => {});
      }
    }
    await page.waitForTimeout(400);
  }
}

async function waitForReleaseNavigation(page) {
  let lastError;
  for (let attempt = 0; attempt < 4; attempt += 1) {
    try {
      await expandSidebarTree(page);
      await page.waitForFunction(({ expectedRoot, minLeafCount }) => {
        const cacheKey = Object.keys(localStorage).find((key) => key.startsWith('sc_frontend_session_v0_5'));
        const cache = cacheKey ? JSON.parse(localStorage.getItem(cacheKey) || 'null') : null;
        const roots = Array.isArray(cache?.releaseNavigationTree) ? cache.releaseNavigationTree : [];
        if (!roots.length) {
          return false;
        }
        const root = roots[0] || {};
        const rootLabel = String(root.label || root.title || '').trim();
        if (rootLabel !== expectedRoot) {
          return false;
        }
        let leafCount = 0;
        const walk = (nodes) => {
          for (const node of nodes || []) {
            if (!node || typeof node !== 'object') continue;
            const children = Array.isArray(node.children) ? node.children : [];
            if (children.length) {
              walk(children);
            } else {
              leafCount += 1;
            }
          }
        };
        walk(roots);
        return leafCount >= minLeafCount;
      }, { expectedRoot: EXPECTED_ROOT_LABEL, minLeafCount: MIN_EXPECTED_LEAF_COUNT }, { timeout: 12000 });
      return;
    } catch (error) {
      lastError = error;
      await recoverFromTransientFailure(page);
    }
  }
  throw lastError;
}

let browser;
let page;
try {
  browser = await launchPortalChromium();
  page = await browser.newPage({ viewport: { width: 1440, height: 960 } });

  page.on('console', (msg) => {
    if (msg.type() === 'error') summary.console_errors.push(msg.text());
  });
  page.on('pageerror', (err) => {
    summary.page_errors.push(String(err?.message || err));
  });

  log('login demo_pm');
  await bootstrapPortalBrowserAuth(page, {
    apiBaseUrl: API_BASE_URL || BASE_URL,
    dbName: DB_NAME,
    login: LOGIN,
    password: PASSWORD,
  });
  await page.goto(`${BASE_URL}/?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'domcontentloaded' });
  await waitForPortalBootstrapReady(page);
  await waitForSidebar(page);
  await waitForReleaseNavigation(page);

  const snapshot = await page.evaluate(() => {
    const cacheKey = Object.keys(localStorage).find((key) => key.startsWith('sc_frontend_session_v0_5'));
    const cache = cacheKey ? JSON.parse(localStorage.getItem(cacheKey) || 'null') : null;
    const sidebarText = Array.from(
      document.querySelectorAll('.sidebar .label, .sidebar .role-menu-item, .sidebar .title, .sidebar .role-label')
    )
      .map((el) => (el.textContent || '').trim())
      .filter(Boolean);
    return {
      href: window.location.href,
      pathname: window.location.pathname,
      search: window.location.search,
      title: document.title,
      sidebar_text: sidebarText,
      cache_release_root_label: String((cache?.releaseNavigationTree || [])[0]?.label || ''),
      cache_release_leaf_count: (() => {
        let leafCount = 0;
        const walk = (nodes) => {
          for (const node of nodes || []) {
            if (!node || typeof node !== 'object') continue;
            const children = Array.isArray(node.children) ? node.children : [];
            if (children.length) {
              walk(children);
            } else {
              leafCount += 1;
            }
          }
        };
        walk(cache?.releaseNavigationTree || []);
        return leafCount;
      })(),
      cache_release_scene_keys: (() => {
        const out = new Set();
        const walk = (nodes) => {
          for (const node of nodes || []) {
            if (!node || typeof node !== 'object') continue;
            const children = Array.isArray(node.children) ? node.children : [];
            if (children.length) {
              walk(children);
              continue;
            }
            const sceneKey = String((node.meta || {}).scene_key || '').trim();
            if (sceneKey) out.add(sceneKey);
          }
        };
        walk(cache?.releaseNavigationTree || []);
        return Array.from(out);
      })(),
    };
  });
  assert(snapshot.cache_release_root_label === EXPECTED_ROOT_LABEL, `release root label drift: ${snapshot.cache_release_root_label}`);
  assert(
    Number(snapshot.cache_release_leaf_count || 0) >= MIN_EXPECTED_LEAF_COUNT,
    `release leaf count drift: ${snapshot.cache_release_leaf_count}`,
  );
  for (const optionGroup of EXPECTED_SCENE_KEY_OPTIONS) {
    const matched = optionGroup.some((sceneKey) => snapshot.cache_release_scene_keys.includes(sceneKey));
    assert(matched, `release scene option missing: ${optionGroup.join('|')}`);
  }
  writeJson('sidebar_snapshot.json', snapshot);
  await page.screenshot({ path: path.join(outDir, 'sidebar.png'), fullPage: true });

  summary.cases.push({
    case_id: 'release_navigation_visible_for_demo_pm',
    status: 'PASS',
    route: `${snapshot.pathname}${snapshot.search}`,
  });
  writeJson('summary.json', summary);
  fs.writeFileSync(
    path.join(outDir, 'summary.md'),
    [
      '# Release Navigation Browser Smoke',
      '',
      `- base_url: \`${BASE_URL}\``,
      `- db_name: \`${DB_NAME}\``,
      `- login: \`${LOGIN}\``,
      '',
      '## Expected Runtime Semantics',
      `- root_label: ${EXPECTED_ROOT_LABEL}`,
      `- min_leaf_count: ${MIN_EXPECTED_LEAF_COUNT}`,
      ...EXPECTED_SCENE_KEY_OPTIONS.map((item) => `- scene_key option: ${item.join(' | ')}`),
      '',
      '## Cases',
      ...summary.cases.map((item) => `- ${item.case_id}: ${item.status} (${item.route})`),
    ].join('\n'),
    'utf8',
  );
  log(`PASS artifacts=${outDir}`);
} catch (error) {
  summary.status = 'FAIL';
  summary.error = String(error?.message || error);
  try {
    if (page) {
      await page.screenshot({ path: path.join(outDir, 'failure.png'), fullPage: true });
    }
  } catch {
    // ignore screenshot failure
  }
  writeJson('summary.json', summary);
  log(`FAIL ${summary.error}`);
  throw error;
} finally {
  if (browser) {
    await browser.close();
  }
}

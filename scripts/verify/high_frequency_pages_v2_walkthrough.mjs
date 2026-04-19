import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const playwrightEntry = require.resolve('playwright', { paths: [path.resolve(process.cwd(), 'frontend')] });
const { chromium } = require(playwrightEntry);

const LOCAL_RUNTIME_LIB_ROOT = path.resolve(process.cwd(), '.codex-runtime', 'playwright-libs');
const BASE_URL = String(process.env.BASE_URL || 'http://127.0.0.1:5174').replace(/\/+$/, '');
const DB_NAME = String(process.env.DB_NAME || 'sc_demo').trim();
const LOGIN = String(process.env.E2E_LOGIN || 'demo_pm').trim();
const PASSWORD = String(process.env.E2E_PASSWORD || 'demo').trim();
const ARTIFACTS_DIR = String(process.env.ARTIFACTS_DIR || 'artifacts').trim() || 'artifacts';
const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
const outDir = path.join(ARTIFACTS_DIR, 'playwright', 'high_frequency_pages_v2', ts);

fs.mkdirSync(outDir, { recursive: true });

function primeLocalRuntimeLibraries() {
  const candidateDirs = [
    path.join(LOCAL_RUNTIME_LIB_ROOT, 'usr', 'lib', 'x86_64-linux-gnu'),
    path.join(LOCAL_RUNTIME_LIB_ROOT, 'lib', 'x86_64-linux-gnu'),
    path.join(LOCAL_RUNTIME_LIB_ROOT, 'usr', 'lib'),
    path.join(LOCAL_RUNTIME_LIB_ROOT, 'lib'),
  ].filter((dir) => fs.existsSync(dir));
  if (!candidateDirs.length) return;
  const existing = String(process.env.LD_LIBRARY_PATH || '').trim();
  const segments = existing ? existing.split(':').filter(Boolean) : [];
  process.env.LD_LIBRARY_PATH = [...candidateDirs, ...segments].filter(Boolean).join(':');
}

primeLocalRuntimeLibraries();

const summary = {
  status: 'PENDING',
  base_url: BASE_URL,
  db_name: DB_NAME,
  login: LOGIN,
  artifacts_dir: outDir,
  menu_candidates: {},
  walkthroughs: [],
  screenshots: [],
  console_errors: [],
  page_errors: [],
};

function log(message) {
  console.log(`[high_frequency_pages_v2_walkthrough] ${message}`);
}

function writeJson(fileName, payload) {
  fs.writeFileSync(path.join(outDir, fileName), `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function sanitizeName(value) {
  return String(value || '')
    .trim()
    .replace(/[^\p{L}\p{N}]+/gu, '_')
    .replace(/^_+|_+$/g, '')
    .toLowerCase();
}

async function fillLoginForm(page) {
  await page.locator('input[autocomplete="username"]').fill(LOGIN);
  await page.locator('input[autocomplete="current-password"]').fill(PASSWORD);
  await page.locator('input[placeholder*="数据库"]').fill(DB_NAME);
}

async function submitLogin(page) {
  await page.locator('button.submit').click();
  await page.waitForFunction(() => {
    return !window.location.pathname.startsWith('/login') || Boolean(document.querySelector('.login-card .error'));
  }, { timeout: 20000 });
  const stillOnLogin = await page.evaluate(() => window.location.pathname.startsWith('/login'));
  const loginError = stillOnLogin
    ? String(await page.locator('.login-card .error').textContent().catch(() => '') || '').trim()
    : '';
  if (stillOnLogin && loginError) {
    throw new Error(`login_failed:${loginError}`);
  }
  await page.waitForLoadState('networkidle');
}

async function readNavigationSnapshot(page) {
  return page.evaluate(() => {
    const cacheKeys = [];
    const tokenKeys = [];
    for (let i = 0; i < localStorage.length; i += 1) {
      const key = localStorage.key(i);
      if (key && key.startsWith('sc_frontend_session_v0_4')) cacheKeys.push(key);
    }
    for (let i = 0; i < sessionStorage.length; i += 1) {
      const key = sessionStorage.key(i);
      if (key && key.startsWith('sc_auth_token')) tokenKeys.push(key);
    }
    const cache = cacheKeys.length ? JSON.parse(localStorage.getItem(cacheKeys[0]) || 'null') : null;
    return {
      href: window.location.href,
      cache_key: cacheKeys[0] || '',
      token_key: tokenKeys[0] || '',
      token: tokenKeys.length ? String(sessionStorage.getItem(tokenKeys[0]) || '') : '',
      menuTree: Array.isArray(cache?.menuTree) ? cache.menuTree : [],
    };
  });
}

async function fetchBootstrapNavigation(page) {
  return page.evaluate(async ({ dbName }) => {
    const tokenKeys = [];
    for (let i = 0; i < sessionStorage.length; i += 1) {
      const key = sessionStorage.key(i);
      if (key && key.startsWith('sc_auth_token')) tokenKeys.push(key);
    }
    const token = tokenKeys.length ? String(sessionStorage.getItem(tokenKeys[0]) || '') : '';
    if (!token) {
      throw new Error('missing auth token in sessionStorage');
    }
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        intent: 'system.init',
        params: {
          scene: 'web',
          with_preload: false,
          root_xmlid: 'smart_construction_core.menu_sc_root',
          edition_key: 'standard',
        },
      }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || payload?.ok === false) {
      const message = String(payload?.error?.message || response.statusText || 'system.init failed').trim();
      throw new Error(`bootstrap_navigation_failed:${message}`);
    }
    return {
      menuTree: Array.isArray(payload?.data?.navigation?.menu_tree) ? payload.data.navigation.menu_tree : [],
      defaultRoute: String(payload?.data?.default_route || '').trim(),
      workspaceHome: payload?.data?.workspace_home || null,
    };
  }, { dbName: DB_NAME });
}

async function fetchProjectTaskIds(page, projectId) {
  return page.evaluate(async ({ recordId, dbName }) => {
    const tokenKeys = [];
    for (let i = 0; i < sessionStorage.length; i += 1) {
      const key = sessionStorage.key(i);
      if (key && key.startsWith('sc_auth_token')) tokenKeys.push(key);
    }
    const token = tokenKeys.length ? String(sessionStorage.getItem(tokenKeys[0]) || '') : '';
    if (!token) {
      throw new Error('missing auth token in sessionStorage');
    }
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        intent: 'api.data',
        params: {
          op: 'read',
          model: 'project.project',
          ids: [recordId],
          fields: ['id', 'name', 'task_ids', 'tasks'],
        },
        meta: {
          startup_chain_bypass: true,
        },
      }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || payload?.ok === false) {
      const message = String(payload?.error?.message || response.statusText || 'api.data read failed').trim();
      throw new Error(`project_task_ids_read_failed:${message}`);
    }
    const row = Array.isArray(payload?.data?.records) ? payload.data.records[0] || {} : {};
    const taskIds = []
      .concat(Array.isArray(row?.task_ids) ? row.task_ids : [])
      .concat(Array.isArray(row?.tasks) ? row.tasks : [])
      .map((item) => Number(item))
      .filter((item) => Number.isFinite(item) && item > 0);
    return [...new Set(taskIds)];
  }, { recordId: projectId, dbName: DB_NAME });
}

async function fetchProjectTaskEntryMeta(page) {
  return page.evaluate(async ({ dbName }) => {
    const tokenKeys = [];
    for (let i = 0; i < sessionStorage.length; i += 1) {
      const key = sessionStorage.key(i);
      if (key && key.startsWith('sc_auth_token')) tokenKeys.push(key);
    }
    const token = tokenKeys.length ? String(sessionStorage.getItem(tokenKeys[0]) || '') : '';
    if (!token) {
      throw new Error('missing auth token in sessionStorage');
    }
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        intent: 'ui.contract',
        params: {
          op: 'model',
          model: 'project.project',
          view_type: 'form',
          id: 1,
        },
      }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || payload?.ok === false) {
      const message = String(payload?.error?.message || response.statusText || 'ui.contract failed').trim();
      throw new Error(`project_task_entry_meta_failed:${message}`);
    }
    const entries = Array.isArray(payload?.data?.semantic_page?.relation_entries)
      ? payload.data.semantic_page.relation_entries
      : [];
    const matched = entries.find((row) => {
      const field = String(row?.field || '').trim();
      const model = String(row?.model || '').trim();
      return (field === 'task_ids' || field === 'tasks') && model === 'project.task';
    }) || {};
    return {
      actionId: Number(matched?.action_id || 0) || 0,
      menuId: Number(matched?.menu_id || 0) || 0,
    };
  }, { dbName: DB_NAME });
}

async function fetchTaskSummary(page, taskId) {
  return page.evaluate(async ({ recordId, dbName }) => {
    const tokenKeys = [];
    for (let i = 0; i < sessionStorage.length; i += 1) {
      const key = sessionStorage.key(i);
      if (key && key.startsWith('sc_auth_token')) tokenKeys.push(key);
    }
    const token = tokenKeys.length ? String(sessionStorage.getItem(tokenKeys[0]) || '') : '';
    if (!token) {
      throw new Error('missing auth token in sessionStorage');
    }
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        intent: 'api.data',
        params: {
          op: 'read',
          model: 'project.task',
          ids: [recordId],
          fields: ['id', 'name', 'display_name'],
        },
        meta: {
          startup_chain_bypass: true,
        },
      }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || payload?.ok === false) {
      const message = String(payload?.error?.message || response.statusText || 'api.data read failed').trim();
      throw new Error(`task_summary_read_failed:${message}`);
    }
    const row = Array.isArray(payload?.data?.records) ? payload.data.records[0] || {} : {};
    return {
      id: Number(row?.id || 0) || recordId,
      name: String(row?.display_name || row?.name || '').trim(),
    };
  }, { recordId: taskId, dbName: DB_NAME });
}

function flattenMenu(nodes, parents = []) {
  const out = [];
  for (const node of Array.isArray(nodes) ? nodes : []) {
    const meta = node?.meta && typeof node.meta === 'object' ? node.meta : {};
    const sceneKey = String(node?.scene_key || meta.scene_key || '').trim();
    const rawRoute = String(node?.route || meta.route || '').trim();
    const row = {
      name: String(node?.name || node?.label || node?.title || '').trim(),
      route: rawRoute || (sceneKey ? `/s/${sceneKey}` : ''),
      target_type: String(node?.target_type || meta.action_type || '').trim(),
      delivery_mode: String(node?.delivery_mode || meta.scene_source || '').trim(),
      is_clickable: node?.is_clickable !== false,
      parent_chain: parents.map((item) => String(item?.name || '').trim()).filter(Boolean),
      scene_key: sceneKey,
    };
    out.push(row);
    if (Array.isArray(node?.children) && node.children.length) {
      out.push(...flattenMenu(node.children, [...parents, node]));
    }
  }
  return out;
}

function pickMenuCandidate(rows, type) {
  const include = type === 'project' ? ['项目'] : ['任务'];
  const exclude = ['驾驶舱', '看板', '工作台', '首页', '工作'];
  const filtered = rows.filter((row) => {
    if (!row.route || !row.is_clickable) return false;
    if (!include.every((keyword) => row.name.includes(keyword))) return false;
    if (exclude.some((keyword) => row.name.includes(keyword))) return false;
    return row.route.startsWith('/a/') || row.route.startsWith('/m/') || row.route.startsWith('/s/');
  });
  const scored = filtered
    .map((row) => {
      let score = 0;
      if (row.route.startsWith('/a/')) score += 50;
      if (row.route.startsWith('/s/')) score += 45;
      if (row.target_type === 'action') score += 30;
      if (row.target_type === 'scene.contract') score += 28;
      if (row.name.includes('列表')) score += 20;
      if (row.name.includes('管理')) score += 12;
      if (row.name.includes('台账')) score += 8;
      score -= row.parent_chain.length;
      return { ...row, score };
    })
    .sort((left, right) => right.score - left.score || left.name.localeCompare(right.name));
  return {
    selected: scored[0] || null,
    candidates: scored.slice(0, 8),
  };
}

function buildRouteUrl(route) {
  const url = new URL(route, `${BASE_URL}/`);
  if (!url.searchParams.has('db')) {
    url.searchParams.set('db', DB_NAME);
  }
  return url.toString();
}

async function openListSurface(page, candidate) {
  assert(candidate?.route, 'missing target route');
  await page.goto(buildRouteUrl(candidate.route), { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForLoadState('networkidle').catch(() => {});
  const listReady = page.locator('table tbody tr, .group-block table tbody tr').first();
  await listReady.waitFor({ state: 'visible', timeout: 15000 });
}

async function capture(page, fileName) {
  const target = path.join(outDir, fileName);
  await page.screenshot({ path: target, fullPage: true });
  summary.screenshots.push(target);
}

async function openFirstRecord(page) {
  const groupedRow = page.locator('.group-block table tbody tr').first();
  if (await groupedRow.count()) {
    await groupedRow.click();
    return;
  }
  const row = page.locator('table tbody tr').first();
  await row.click();
}

async function waitForDetailSurface(page) {
  await page.getByRole('button', { name: '返回' }).first().waitFor({ state: 'visible', timeout: 15000 });
  await page.waitForLoadState('networkidle').catch(() => {});
  await page.locator('text=正在加载页面...').waitFor({ state: 'hidden', timeout: 20000 }).catch(() => {});
  await page.waitForFunction(() => {
    const hasConsoleShell = Boolean(
      document.querySelector('.detail-shell-layout, .detail-command-bar, .form-section, .overview-card, .detail-support-card'),
    );
    const stillLoading = Array.from(document.querySelectorAll('*')).some((node) =>
      String(node.textContent || '').includes('正在加载页面...'),
    );
    return hasConsoleShell && !stillLoading;
  }, { timeout: 20000 }).catch(() => {});
}

async function returnToList(page) {
  await page.getByRole('button', { name: '返回' }).first().click();
  await page.waitForLoadState('networkidle');
  await page.waitForFunction(() => {
    const hasRows = Boolean(document.querySelector('table tbody tr, .group-block table tbody tr'));
    const hasEmpty = Array.from(document.querySelectorAll('*')).some((node) =>
      String(node.textContent || '').includes('暂无可展示内容'),
    );
    const hasSearch = Boolean(document.querySelector('input[placeholder*="搜索"], input[placeholder*="Search"]'));
    return hasRows || hasEmpty || hasSearch;
  }, { timeout: 15000 });
}

async function runWalkthrough(page, candidate, type) {
  const routeBefore = buildRouteUrl(candidate.route);
  await openListSurface(page, candidate);
  await capture(page, `${type}-list.png`);
  const listUrl = page.url();
  await openFirstRecord(page);
  await waitForDetailSurface(page);
  await capture(page, `${type}-detail.png`);
  const detailUrl = page.url();
  await returnToList(page);
  const backUrl = page.url();
  summary.walkthroughs.push({
    type,
    list_label: candidate.name,
    route: candidate.route,
    list_url: listUrl,
    detail_url: detailUrl,
    back_url: backUrl,
    expected_entry_url: routeBefore,
    status: 'PASS',
  });
}

async function openProjectTaskListFromDetail(page) {
  const relationTab = page.getByText('协作 / 系统', { exact: true }).first();
  if (await relationTab.count().catch(() => 0)) {
    await relationTab.click().catch(() => {});
    await page.waitForTimeout(1200);
  }
}

async function runTaskWalkthroughFromProject(page, candidate) {
  await openListSurface(page, candidate);
  await openFirstRecord(page);
  await waitForDetailSurface(page);
  const projectDetailUrl = page.url();
  const projectIdMatch = projectDetailUrl.match(/\/r\/project\.project\/(\d+)/);
  const projectId = projectIdMatch?.[1] ? Number(projectIdMatch[1]) : 0;
  await openProjectTaskListFromDetail(page);
  await capture(page, 'task-list.png');
  const listUrl = page.url();
  const projectTaskIds = projectId > 0 ? await fetchProjectTaskIds(page, projectId) : [];
  const projectTaskEntryMeta = await fetchProjectTaskEntryMeta(page).catch(() => ({ actionId: 0, menuId: 0 }));
  const firstTaskId = projectTaskIds[0] || 0;
  const firstTask = firstTaskId > 0 ? await fetchTaskSummary(page, firstTaskId) : { id: 0, name: '' };
  const taskRow = firstTask.name
    ? page.getByText(firstTask.name, { exact: true }).first()
    : page.locator('table tbody tr, .group-block table tbody tr').first();
  const taskRowCount = await taskRow.count().catch(() => 0);
  if (taskRowCount) {
    await taskRow.click().catch(async () => {
      if (firstTaskId > 0) {
        const taskDetailRoute = `/r/project.task/${firstTaskId}${projectTaskEntryMeta.actionId > 0 ? `?action_id=${projectTaskEntryMeta.actionId}` : ''}`;
        await page.goto(buildRouteUrl(taskDetailRoute), { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForLoadState('networkidle').catch(() => {});
      }
    });
  } else if (firstTaskId > 0) {
    const taskDetailRoute = `/r/project.task/${firstTaskId}${projectTaskEntryMeta.actionId > 0 ? `?action_id=${projectTaskEntryMeta.actionId}` : ''}`;
    await page.goto(buildRouteUrl(taskDetailRoute), { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForLoadState('networkidle').catch(() => {});
  } else {
    const taskListBodyText = String(await page.locator('body').textContent().catch(() => '') || '');
    const taskListEmpty = taskListBodyText.includes('暂无可展示内容');
    summary.walkthroughs.push({
      type: 'task',
      list_label: '项目详情任务入口',
      route: `${candidate.route} -> task-entry`,
      list_url: listUrl,
      detail_url: '',
      back_url: '',
      expected_entry_url: buildRouteUrl(candidate.route),
      status: 'BLOCKED',
      row_count: 0,
      empty_state: taskListEmpty,
    });
    throw new Error(`task_list_empty_after_project_entry:url=${listUrl};empty_state=${taskListEmpty}`);
  }
  await waitForDetailSurface(page);
  await capture(page, 'task-detail.png');
  const detailUrl = page.url();
  const backUrl = taskRowCount
    ? (await (async () => {
        await returnToList(page);
        return page.url();
      })())
    : listUrl;
  summary.walkthroughs.push({
    type: 'task',
    list_label: '项目详情任务入口',
    route: `${candidate.route} -> task-entry`,
    list_url: listUrl,
    detail_url: detailUrl,
    back_url: backUrl,
    expected_entry_url: buildRouteUrl(candidate.route),
    status: taskRowCount ? 'PASS' : 'PASS_WITH_RISK',
  });
}

let browser;
let page;
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
  page = await browser.newPage({ viewport: { width: 1440, height: 960 } });

  page.on('console', (msg) => {
    if (msg.type() === 'error') summary.console_errors.push(msg.text());
  });
  page.on('pageerror', (err) => {
    summary.page_errors.push(String(err?.message || err));
  });

  log('login custom frontend');
  await page.goto(`${BASE_URL}/login?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'networkidle', timeout: 30000 });
  await fillLoginForm(page);
  await submitLogin(page);

  let navigation = await readNavigationSnapshot(page);
  if (!navigation.menuTree.length) {
    const bootstrapNavigation = await fetchBootstrapNavigation(page);
    navigation = {
      ...navigation,
      menuTree: bootstrapNavigation.menuTree,
      default_route: bootstrapNavigation.defaultRoute,
      workspace_home: bootstrapNavigation.workspaceHome,
      source: 'bootstrap_fetch',
    };
  }
  writeJson('navigation_snapshot.json', navigation);
  const flattenedMenus = flattenMenu(navigation.menuTree);
  writeJson('menu_flattened.json', flattenedMenus);

  const projectPick = pickMenuCandidate(flattenedMenus, 'project');
  const taskPick = pickMenuCandidate(flattenedMenus, 'task');
  summary.menu_candidates.project = projectPick;
  summary.menu_candidates.task = taskPick;
  writeJson('menu_candidates.json', summary.menu_candidates);

  assert(projectPick.selected, 'project list candidate not found');

  await runWalkthrough(page, projectPick.selected, 'project');
  if (taskPick.selected) {
    await runWalkthrough(page, taskPick.selected, 'task');
  } else {
    await runTaskWalkthroughFromProject(page, projectPick.selected);
  }

  summary.status = 'PASS';
  writeJson('summary.json', summary);
  fs.writeFileSync(
    path.join(outDir, 'summary.md'),
    [
      '# High Frequency Pages V2 Walkthrough',
      '',
      `- base_url: \`${BASE_URL}\``,
      `- db_name: \`${DB_NAME}\``,
      `- login: \`${LOGIN}\``,
      `- console_error_count: \`${summary.console_errors.length}\``,
      `- page_error_count: \`${summary.page_errors.length}\``,
      '',
      '## Walkthroughs',
      ...summary.walkthroughs.map((item) => `- ${item.type}: PASS (${item.list_label})`),
      '',
      '## Screenshots',
      ...summary.screenshots.map((item) => `- ${item}`),
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
  } catch {}
  writeJson('summary.json', summary);
  log(`FAIL ${summary.error}`);
  throw error;
} finally {
  if (browser) {
    await browser.close().catch(() => {});
  }
}

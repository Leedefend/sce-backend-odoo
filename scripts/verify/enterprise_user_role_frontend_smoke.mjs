import fs from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';

const require = createRequire(import.meta.url);
const playwrightEntry = require.resolve('playwright', { paths: [path.resolve(process.cwd(), 'frontend')] });
const { chromium } = require(playwrightEntry);
const LOCAL_RUNTIME_LIB_ROOT = path.resolve(process.cwd(), '.codex-runtime', 'playwright-libs');

function primeLocalRuntimeLibraries() {
  const candidateDirs = [
    path.join(LOCAL_RUNTIME_LIB_ROOT, 'lib', 'x86_64-linux-gnu'),
    path.join(LOCAL_RUNTIME_LIB_ROOT, 'usr', 'lib', 'x86_64-linux-gnu'),
    path.join(LOCAL_RUNTIME_LIB_ROOT, 'usr', 'lib'),
    path.join(LOCAL_RUNTIME_LIB_ROOT, 'lib'),
  ].filter((dir) => fs.existsSync(dir));
  if (!candidateDirs.length) return;
  const existing = String(process.env.LD_LIBRARY_PATH || '').trim();
  const segments = existing ? existing.split(':').filter(Boolean) : [];
  process.env.LD_LIBRARY_PATH = [...candidateDirs, ...segments].join(':');
}

primeLocalRuntimeLibraries();

const BASE_URL = String(process.env.BASE_URL || 'http://127.0.0.1').replace(/\/+$/, '');
const DB_NAME = String(process.env.DB_NAME || 'sc_demo').trim();
const ADMIN_LOGIN = String(process.env.E2E_LOGIN || 'admin').trim();
const ADMIN_PASSWORD = String(process.env.E2E_PASSWORD || 'admin').trim();
const ARTIFACTS_DIR = String(process.env.ARTIFACTS_DIR || 'artifacts').trim() || 'artifacts';
const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'enterprise-user-role-smoke', ts);
const unique = Date.now();

fs.mkdirSync(outDir, { recursive: true });

const summary = {
  base_url: BASE_URL,
  db_name: DB_NAME,
  admin_login: ADMIN_LOGIN,
  status: 'PASS',
  created_users: [],
  role_checks: [],
  console_errors: [],
  page_errors: [],
};

const userFixtures = [
  {
    key: 'pm',
    label: '项目经理',
    name: 'Sprint1 项目经理',
    login: `sprint1.pm.${unique}@example.com`,
    password: 'Pass1234',
    expectedRoleCode: 'pm',
    expectedLandingPrefix: 'project',
  },
  {
    key: 'finance',
    label: '财务人员',
    name: 'Sprint1 财务人员',
    login: `sprint1.finance.${unique}@example.com`,
    password: 'Pass1234',
    expectedRoleCode: 'finance',
    expectedLandingPrefix: 'finance',
  },
];

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function writeJson(fileName, payload) {
  fs.writeFileSync(path.join(outDir, fileName), `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
}

async function writeCreateFormDebug(page, fileName = 'user_form_debug.json') {
  const snapshot = await page.evaluate(() => {
    const collectText = (selector) =>
      Array.from(document.querySelectorAll(selector))
        .map((node) => String(node.textContent || '').trim())
        .filter(Boolean);

    return {
      href: window.location.href,
      title: document.title,
      headings: collectText('h1, h2, h3'),
      labels: collectText('.label, label').slice(0, 80),
      buttons: collectText('button').slice(0, 40),
      alerts: collectText('[role="alert"], [role="status"]').slice(0, 20),
      page_text_sample: String(document.body?.innerText || '').split('\n').map((line) => line.trim()).filter(Boolean).slice(0, 80),
      form_debug: window.__scFormDebug || null,
    };
  });
  writeJson(fileName, snapshot);
}

async function fillLoginForm(page, login, password) {
  await page.locator('input[autocomplete="username"]').fill(login);
  await page.locator('input[autocomplete="current-password"]').fill(password);
  await page.locator('input[placeholder*="数据库"]').fill(DB_NAME);
}

async function submitLogin(page) {
  await page.locator('button.submit').click();
  await page.waitForURL((url) => !url.pathname.startsWith('/login'), { timeout: 20000, waitUntil: 'commit' });
}

async function loginToFrontend(browser, login, password) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1080 } });
  const page = await context.newPage();
  page.on('console', (msg) => {
    if (msg.type() === 'error') summary.console_errors.push(msg.text());
  });
  page.on('pageerror', (error) => summary.page_errors.push(String(error?.message || error)));
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded' });
  await fillLoginForm(page, login, password);
  await submitLogin(page);
  await page.locator('.router-host, .sidebar').first().waitFor({ state: 'visible', timeout: 30000 });
  return { context, page };
}

async function readSessionSnapshot(page) {
  return page.evaluate(() => {
    const cacheKey = Object.keys(localStorage).find((key) => key.startsWith('sc_frontend_session_v0_4'));
    const cache = cacheKey ? JSON.parse(localStorage.getItem(cacheKey) || 'null') : null;
    return {
      href: window.location.href,
      cache_key: cacheKey || '',
      enterprise_enablement: cache?.enterpriseEnablement || null,
      role_surface: cache?.roleSurface || null,
      user: cache?.user || null,
    };
  });
}

async function fetchIntent(page, intent, params) {
  return page.evaluate(async ({ dbName, intentName, paramsPayload }) => {
    const sessionKeys = Object.keys(sessionStorage);
    const tokenKey = sessionKeys.find((key) => key.startsWith('sc_auth_token'));
    const token = tokenKey ? String(sessionStorage.getItem(tokenKey) || '').trim() : '';
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        intent: intentName,
        params: paramsPayload,
      }),
    });
    const payload = await response.json();
    return { status: response.status, payload };
  }, { dbName: DB_NAME, intentName: intent, paramsPayload: params });
}

async function ensureDepartmentFixture(page, companyId) {
  const fixtureName = `Sprint1 组织部 ${unique}`;
  const created = await fetchIntent(page, 'api.data', {
    op: 'create',
    model: 'hr.department',
    vals: {
      name: fixtureName,
      company_id: companyId,
    },
  });
  const createdId = Number(created?.payload?.data?.id || 0);
  assert(createdId > 0, 'failed to create department fixture');
  return { id: createdId, name: fixtureName };
}

function fieldByLabel(page, labelText) {
  return page.locator('.field').filter({
    has: page.locator('.label', { hasText: labelText }),
  }).first();
}

async function fillTextField(page, labelText, value) {
  const field = fieldByLabel(page, labelText);
  await field.waitFor({ state: 'visible', timeout: 20000 });
  await field.locator('input').first().fill(value);
}

async function selectFieldByLabel(page, labelText, optionLabel) {
  const field = fieldByLabel(page, labelText);
  await field.waitFor({ state: 'visible', timeout: 20000 });
  const select = field.locator('select').first();
  await select.waitFor({ state: 'visible', timeout: 20000 });
  await select.selectOption({ label: optionLabel });
}

async function ensureCompanySelected(page) {
  const field = fieldByLabel(page, '所属公司');
  await field.waitFor({ state: 'visible', timeout: 20000 });
  const select = field.locator('select').first();
  const value = await select.inputValue();
  if (String(value || '').trim()) return;
  const options = await select.locator('option').evaluateAll((nodes) => nodes.map((node) => ({
    value: String(node.getAttribute('value') || ''),
    label: String(node.textContent || '').trim(),
  })));
  const firstReal = options.find((row) => row.value && !row.label.startsWith('+'));
  assert(firstReal?.value, 'company options are missing');
  await select.selectOption(firstReal.value);
}

async function createUserThroughUi(page, userFixture, departmentName) {
  const createButton = page.getByRole('button', { name: '新建用户' });
  await createButton.waitFor({ state: 'visible', timeout: 20000 });
  await createButton.click();
  await page.waitForURL((url) => url.pathname === '/f/res.users/new', { timeout: 20000 });
  await page.locator('.template-form-section').first().waitFor({ state: 'visible', timeout: 20000 });

  try {
    await fillTextField(page, '姓名', userFixture.name);
    await fillTextField(page, '登录账号', userFixture.login);
    await fillTextField(page, '初始密码', userFixture.password);
    await ensureCompanySelected(page);
    await selectFieldByLabel(page, '所属部门', departmentName);
    await selectFieldByLabel(page, '产品角色', userFixture.label);
  } catch (error) {
    await writeCreateFormDebug(page);
    throw error;
  }

  await page.getByRole('button', { name: '保存' }).first().click();
  await page.getByText('保存成功').waitFor({ state: 'visible', timeout: 30000 });
}

async function readRoleHomeEvidence(page) {
  await page.locator('.role-label').waitFor({ state: 'visible', timeout: 30000 });
  return page.evaluate(() => {
    const cacheKey = Object.keys(localStorage).find((key) => key.startsWith('sc_frontend_session_v0_4'));
    const cache = cacheKey ? JSON.parse(localStorage.getItem(cacheKey) || 'null') : null;
    const roleMenus = Array.from(document.querySelectorAll('.role-menu-item'))
      .map((el) => String(el.textContent || '').trim())
      .filter(Boolean);
    const roleLabel = document.querySelector('.role-label');
    return {
      href: window.location.href,
      role_label_text: roleLabel ? String(roleLabel.textContent || '').trim() : '',
      role_menus: roleMenus,
      role_surface: cache?.roleSurface || null,
    };
  });
}

async function run() {
  const browser = await chromium.launch({ headless: true });
  try {
    const adminSession = await loginToFrontend(browser, ADMIN_LOGIN, ADMIN_PASSWORD);
    const adminPage = adminSession.page;
    const sessionSnapshot = await readSessionSnapshot(adminPage);
    writeJson('admin_session_snapshot.json', sessionSnapshot);

    const companyId = Number(sessionSnapshot?.enterprise_enablement?.current_company_id || sessionSnapshot?.user?.company?.id || 0);
    assert(companyId > 0, 'current company id is missing');
    const userStep = (sessionSnapshot?.enterprise_enablement?.steps || []).find((step) => step?.key === 'user');
    const userTarget = userStep?.target || sessionSnapshot?.enterprise_enablement?.primary_action || null;
    const userRoute = String(userTarget?.route || '').trim();
    assert(userRoute, 'user settings route is missing');

    const department = await ensureDepartmentFixture(adminPage, companyId);
    writeJson('department_fixture.json', department);

    await adminPage.goto(`${BASE_URL}${userRoute}`, { waitUntil: 'domcontentloaded' });
    await adminPage.locator('.router-host').waitFor({ state: 'visible', timeout: 30000 });

    for (const userFixture of userFixtures) {
      await createUserThroughUi(adminPage, userFixture, department.name);
      summary.created_users.push({
        key: userFixture.key,
        login: userFixture.login,
      });
      await adminPage.goto(`${BASE_URL}${userRoute}`, { waitUntil: 'domcontentloaded' });
      await adminPage.locator('.router-host').waitFor({ state: 'visible', timeout: 30000 });
    }

    await adminSession.context.close();

    for (const userFixture of userFixtures) {
      const userSession = await loginToFrontend(browser, userFixture.login, userFixture.password);
      const evidence = await readRoleHomeEvidence(userSession.page);
      summary.role_checks.push({
        key: userFixture.key,
        login: userFixture.login,
        ...evidence,
      });
      assert(String(evidence?.role_surface?.role_code || '').trim() === userFixture.expectedRoleCode, `${userFixture.key} role code mismatch`);
      assert(String(evidence?.role_surface?.landing_scene_key || '').startsWith(userFixture.expectedLandingPrefix), `${userFixture.key} landing scene mismatch`);
      assert(String(evidence?.role_label_text || '').includes(userFixture.label), `${userFixture.key} role label not visible`);
      await userSession.context.close();
    }
  } catch (error) {
    summary.status = 'FAIL';
    summary.error = String(error?.message || error);
    throw error;
  } finally {
    writeJson('summary.json', summary);
    await browser.close();
  }
}

run().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

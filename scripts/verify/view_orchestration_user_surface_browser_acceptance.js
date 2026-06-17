#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const { createRequire } = require('module');

const requireBase = fs.existsSync(path.join(process.cwd(), 'frontend/apps/web/package.json'))
  ? path.join(process.cwd(), 'frontend/apps/web/package.json')
  : path.join(process.cwd(), 'package.json');
const requireFromRoot = createRequire(requireBase);
const { chromium } = requireFromRoot('playwright');

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5174';
const DB_NAME = process.env.DB_NAME || process.env.E2E_DB || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const ODOO_CONTAINER = process.env.ODOO_CONTAINER || 'sc-backend-odoo-dev-odoo-1';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const MARKER = process.env.VIEW_ORCH_BROWSER_MARKER || `codex_view_orch_surface_${Date.now()}`;
const ACTION_ID = Number(process.env.ACTION_ID || 506);
const MENU_ID = Number(process.env.MENU_ID || 379);
const MODEL_NAME = process.env.MVP_MODEL || 'project.project';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'playwright', 'view-orchestration-user-surface', ts);

function ensureOutDir() {
  fs.mkdirSync(outDir, { recursive: true });
}

function writeJson(name, data) {
  ensureOutDir();
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

function clean(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function runOdooShell(script) {
  const result = spawnSync(
    'docker',
    ['exec', '-i', ODOO_CONTAINER, 'odoo', 'shell', '-d', DB_NAME, '-c', '/var/lib/odoo/odoo.conf'],
    { input: script, encoding: 'utf8', maxBuffer: 20 * 1024 * 1024 },
  );
  if (result.status !== 0) {
    throw new Error(`odoo shell failed\nSTDOUT:\n${result.stdout}\nSTDERR:\n${result.stderr}`);
  }
  const lines = String(result.stdout || '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const jsonLine = [...lines].reverse().find((line) => line.startsWith('{') && line.endsWith('}'));
  return jsonLine ? JSON.parse(jsonLine) : {};
}

function setupScript() {
  return `
import json
marker = ${JSON.stringify(MARKER)}
action_id = ${Number.isFinite(ACTION_ID) ? Math.trunc(ACTION_ID) : 0}
model_name = ${JSON.stringify(MODEL_NAME)}
Contract = env['ui.business.config.contract'].sudo()
Contract.search([('name', 'ilike', marker)]).unlink()
action = env['ir.actions.act_window'].sudo().browse(action_id).exists()
if not action:
    raise RuntimeError('action not found: %s' % action_id)
if action.res_model != model_name:
    raise RuntimeError('action %s model mismatch: expected %s got %s' % (action_id, model_name, action.res_model))
payloads = {
    'tree': {
        'view_orchestration': {'views': {'tree': {
            'columns': [
                {'name': 'partner_id', 'label': 'CODEX_PARTNER_COLUMN', 'sequence': 10},
                {'name': 'name', 'label': 'CODEX_NAME_COLUMN', 'sequence': 20},
                {'name': 'stage_id', 'label': 'CODEX_STAGE_HIDDEN', 'visible': False, 'sequence': 30},
            ]
        }}}
    },
    'kanban': {
        'view_orchestration': {'views': {'kanban': {
            'fields': [
                {'name': 'partner_id', 'label': 'CODEX_PARTNER_CARD', 'sequence': 10},
                {'name': 'name', 'label': 'CODEX_NAME_CARD', 'sequence': 20},
                {'name': 'stage_id', 'label': 'CODEX_STAGE_CARD_HIDDEN', 'visible': False, 'sequence': 30},
            ],
            'slots': {'primary': ['name', 'stage_id', 'partner_id']},
        }}}
    },
    'graph': {
        'view_orchestration': {'views': {'graph': {
            'type': 'bar',
            'dimension': 'partner_id',
            'measure': 'color',
            'dimensions': [{'name': 'partner_id', 'label': 'CODEX_PARTNER_DIM', 'sequence': 10}],
            'measures': [{'name': 'color', 'label': 'CODEX_COLOR_MEASURE', 'sequence': 20}],
        }}}
    },
    'search': {
        'view_orchestration': {'views': {'search': {
            'filters': [{'name': 'codex_active', 'label': 'CODEX_FILTER_ACTIVE', 'domain': [('active', '=', True)], 'sequence': 10}],
            'groupBys': [{'name': 'codex_partner_group', 'field': 'partner_id', 'label': 'CODEX_PARTNER_GROUP', 'sequence': 10}],
        }}}
    },
}
config_ids = []
for view_type, payload in payloads.items():
    rec = Contract.create({
        'name': '%s:%s' % (marker, view_type),
        'model': model_name,
        'view_type': view_type,
        'action_id': action_id,
        'priority': 99999,
        'status': 'published',
        'contract_json': payload,
    })
    config_ids.append(rec.id)
env.cr.commit()
print(json.dumps({'marker': marker, 'action_id': action_id, 'model': model_name, 'config_ids': config_ids}, ensure_ascii=False))
`;
}

function cleanupScript() {
  return `
import json
marker = ${JSON.stringify(MARKER)}
Contract = env['ui.business.config.contract'].sudo()
configs = Contract.search([('name', 'ilike', marker)])
summary = {'config_ids': configs.ids}
configs.unlink()
env.cr.commit()
print(json.dumps(summary, ensure_ascii=False))
`;
}

async function login(page) {
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  const dbInput = inputs.nth(2);
  if ((await dbInput.count()) && await dbInput.isEnabled().catch(() => false)) {
    await dbInput.fill(DB_NAME);
  }
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 30000 });
}

async function waitForActionReady(page) {
  await page.locator('.page, .status-panel, body').first().waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.body?.textContent || '');
    return !text.includes('正在加载列表') && !text.includes('正在加载页面') && !text.includes('Loading cards');
  }, null, { timeout: 30000 });
}

async function openAction(page, actionId, mode) {
  const menu = Number.isFinite(MENU_ID) && MENU_ID > 0 ? `menu_id=${Math.trunc(MENU_ID)}&` : '';
  await page.goto(`${FRONTEND_URL}/a/${actionId}?${menu}view_mode=${mode}&t=${Date.now()}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await waitForActionReady(page);
}

async function listSnapshot(page) {
  return page.evaluate(() => ({
    headers: Array.from(document.querySelectorAll('table thead th, .list-header-cell, [data-column-name], .cell-header'))
      .map((node) => String(node.textContent || '').replace(/\s+/g, ' ').trim())
      .filter(Boolean),
    body: String(document.body?.textContent || '').replace(/\s+/g, ' ').trim(),
  }));
}

async function kanbanSnapshot(page) {
  return page.evaluate(() => ({
    body: String(document.body?.textContent || '').replace(/\s+/g, ' ').trim(),
    cardCount: document.querySelectorAll('.kanban-card, [data-component="KanbanCard"], .kanban-column article').length,
  }));
}

async function advancedSnapshot(page) {
  return page.evaluate(() => ({
    modeText: String(document.querySelector('.advanced-contract')?.textContent || '').replace(/\s+/g, ' ').trim(),
    items: Array.from(document.querySelectorAll('.advanced-item-meta'))
      .map((node) => String(node.textContent || '').replace(/\s+/g, ' ').trim()),
    body: String(document.body?.textContent || '').replace(/\s+/g, ' ').trim(),
  }));
}

async function searchSnapshot(page) {
  const toggle = page.locator('.search-menu-toggle').first();
  await toggle.waitFor({ timeout: 10000 });
  await toggle.click();
  await page.locator('.search-dropdown').waitFor({ timeout: 10000 });
  return page.evaluate(() => ({
    dropdownText: String(document.querySelector('.search-dropdown')?.textContent || '').replace(/\s+/g, ' ').trim(),
  }));
}

function assert(condition, message, errors) {
  if (!condition) errors.push(message);
}

function summarizeContractPayload(payload) {
  const findContract = (value, depth = 0) => {
    if (!value || typeof value !== 'object' || Array.isArray(value) || depth > 5) return {};
    if (value.views && typeof value.views === 'object') return value;
    for (const key of ['data', 'result', 'payload', 'rawBody', 'body']) {
      const found = findContract(value[key], depth + 1);
      if (found && found.views && typeof found.views === 'object') return found;
    }
    const v2 = value.__unified_page_contract_v2;
    const foundV2 = findContract(v2, depth + 1);
    if (foundV2 && foundV2.views && typeof foundV2.views === 'object') return foundV2;
    return {};
  };
  const data = findContract(payload);
  const views = data && typeof data === 'object' ? data.views || {} : {};
  const summarizeView = (key) => {
    const view = views && typeof views === 'object' ? views[key] || {} : {};
    const labels = {};
    ['fields', 'columns', 'columns_schema', 'measures', 'dimensions'].forEach((slot) => {
      const rows = Array.isArray(view[slot]) ? view[slot] : [];
      rows.forEach((row) => {
        if (!row || typeof row !== 'object') return;
        const name = String(row.name || row.field || row.field_name || '').trim();
        const label = String(row.label || row.string || row.display_label || '').trim();
        if (name && label) labels[name] = label;
      });
    });
    return {
      present: Boolean(view && typeof view === 'object' && Object.keys(view).length),
      labels,
      fields: Array.isArray(view.fields) ? view.fields.map((row) => typeof row === 'string' ? row : row && row.name).filter(Boolean) : [],
      columns: Array.isArray(view.columns) ? view.columns.map((row) => typeof row === 'string' ? row : row && row.name).filter(Boolean) : [],
      profile: view.kanban_profile || null,
    };
  };
  return {
    view_type: data?.head?.view_type || data?.view_type || '',
    view_keys: Object.keys(views || {}),
    tree: summarizeView('tree'),
    kanban: summarizeView('kanban'),
    search_filters: Array.isArray(data?.search?.filters) ? data.search.filters.map((row) => ({ key: row.key, name: row.name, label: row.label })) : [],
    search_group_by: Array.isArray(data?.search?.group_by) ? data.search.group_by.map((row) => ({ field: row.field, name: row.name, label: row.label })) : [],
  };
}

async function main() {
  ensureOutDir();
  const setup = runOdooShell(setupScript());
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, locale: 'zh-CN' });
  const consoleErrors = [];
  const pageEvents = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => consoleErrors.push(err.message));
  page.on('close', () => pageEvents.push('page.close'));
  page.on('crash', () => pageEvents.push('page.crash'));

  const summary = {
    pass: false,
    marker: MARKER,
    frontend_url: FRONTEND_URL,
    db: DB_NAME,
    setup,
    artifact_dir: outDir,
    errors: [],
    console_errors: consoleErrors,
    page_events: pageEvents,
    contract_responses: [],
  };
  page.on('response', async (response) => {
    try {
      if (!response.url().includes('/api/v1/intent')) return;
      const request = response.request();
      const raw = request.postData() || '';
      if (!raw.includes('ui.contract.v2')) return;
      const payload = await response.json();
      summary.contract_responses.push(summarizeContractPayload(payload));
    } catch {
      // Debug-only capture must never change acceptance behavior.
    }
  });

  try {
    await login(page);

    await openAction(page, setup.action_id, 'tree');
    await page.waitForFunction(() => String(document.body?.textContent || '').includes('CODEX_PARTNER_COLUMN'), null, { timeout: 30000 });
    summary.list = await listSnapshot(page);
    await page.screenshot({ path: path.join(outDir, 'list.png'), fullPage: true });
    const listText = summary.list.headers.length ? summary.list.headers.join(' ') : summary.list.body;
    const emailIndex = listText.indexOf('CODEX_PARTNER_COLUMN');
    const nameIndex = listText.indexOf('CODEX_NAME_COLUMN');
    assert(emailIndex >= 0, 'list must show orchestrated partner label', summary.errors);
    assert(nameIndex >= 0, 'list must show orchestrated name label', summary.errors);
    assert(emailIndex >= 0 && nameIndex >= 0 && emailIndex < nameIndex, 'list column order must follow orchestration sequence', summary.errors);
    assert(!summary.list.body.includes('CODEX_STAGE_HIDDEN'), 'list hidden field must not be visible', summary.errors);

    summary.search = await searchSnapshot(page);
    assert(summary.search.dropdownText.includes('CODEX_PARTNER_GROUP'), 'search group label must come from orchestration', summary.errors);
    assert(summary.search.dropdownText.includes('CODEX_FILTER_ACTIVE'), 'search filter label must come from orchestration', summary.errors);

    await openAction(page, setup.action_id, 'kanban');
    summary.kanban = await kanbanSnapshot(page);
    await page.screenshot({ path: path.join(outDir, 'kanban.png'), fullPage: true });
    const partnerCardIndex = Math.max(
      summary.kanban.body.indexOf('CODEX_PARTNER_CARD'),
      summary.kanban.body.indexOf('CODEX_PARTNER_COLUMN'),
    );
    const defaultProjectCodeIndex = summary.kanban.body.indexOf('项目编号');
    assert(partnerCardIndex >= 0, 'kanban must show the orchestrated partner field on user cards', summary.errors);
    assert(
      partnerCardIndex >= 0 && defaultProjectCodeIndex >= 0 && partnerCardIndex < defaultProjectCodeIndex,
      'kanban card field order must put orchestrated partner before default project code',
      summary.errors,
    );
    assert(!summary.kanban.body.includes('CODEX_STAGE_CARD_HIDDEN'), 'kanban hidden field must not be visible', summary.errors);

    summary.pass = summary.errors.length === 0 && consoleErrors.length === 0;
  } catch (err) {
    summary.errors.push(err instanceof Error ? err.message : String(err));
    summary.current_url = page.isClosed() ? '<page closed>' : page.url();
    if (!page.isClosed()) {
      summary.failure_text = await page.evaluate(() => String(document.body?.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 2000)).catch(() => '');
    }
    try {
      if (!page.isClosed()) {
        await page.screenshot({ path: path.join(outDir, 'failure.png'), fullPage: true });
      }
    } catch {
      // ignore screenshot failure
    }
  } finally {
    await browser.close().catch(() => undefined);
    summary.cleanup = runOdooShell(cleanupScript());
    writeJson('summary.json', summary);
  }

  if (!summary.pass) {
    console.error('[view_orchestration_user_surface_browser_acceptance] FAIL');
    console.error(JSON.stringify(summary, null, 2));
    process.exit(1);
  }
  console.log('[view_orchestration_user_surface_browser_acceptance] PASS');
  console.log(JSON.stringify({
    artifact_dir: outDir,
    action_id: setup.action_id,
    list_headers: summary.list.headers,
    search: summary.search.dropdownText,
    kanban_card_count: summary.kanban.cardCount,
  }, null, 2));
}

main().catch((err) => {
  console.error(`[view_orchestration_user_surface_browser_acceptance] FAIL: ${err.message}`);
  process.exit(1);
});

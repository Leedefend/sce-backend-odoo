const { chromium } = require('playwright');
const fs = require('node:fs');

const base = process.env.BASE_URL || 'http://127.0.0.1:18081';
const outPath = process.env.OUT || '/tmp/user_list_field_data_coverage.json';
const loginName = process.env.LOGIN || 'demo_pm';
const password = process.env.PASSWORD || 'demo';
const dbName = process.env.DB || 'sc_demo';
const startIndex = Number(process.env.START_INDEX || 0);
const limit = Number(process.env.LIMIT || 0);
const helperHeaders = new Set(['', '序号', '列', '操作', 'Actions']);

function flattenNav(nodes, path = []) {
  const out = [];
  for (const node of nodes || []) {
    const label = String(node?.label || node?.title || '').trim();
    const nextPath = label ? [...path, label] : path;
    const meta = node?.meta || {};
    const target = meta.entry_target || {};
    const refs = target.compatibility_refs || {};
    const actionId = Number(meta.action_id || refs.action_id || 0);
    const menuId = Number(meta.menu_id || node?.menu_id || refs.menu_id || 0);
    const model = String(meta.model || refs.model || '').trim();
    const sceneKey = String(meta.scene_key || target.scene_key || '').trim();
    if (actionId || sceneKey) {
      out.push({ label, path: nextPath.join(' / '), actionId, menuId, model, sceneKey });
    }
    out.push(...flattenNav(node?.children || [], nextPath));
  }
  return out;
}

function uniqEntries(rows) {
  const seen = new Set();
  const out = [];
  for (const row of rows) {
    const key = row.actionId ? `a:${row.actionId}:${row.menuId || 0}` : `s:${row.sceneKey}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(row);
  }
  return out;
}

function normalizeText(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function extractRecords(data) {
  if (!data || typeof data !== 'object') return [];
  if (Array.isArray(data.records)) return data.records;
  if (Array.isArray(data.rows)) return data.rows;
  if (Array.isArray(data.data)) return data.data;
  const list = data.list || data.result || {};
  if (Array.isArray(list.records)) return list.records;
  if (Array.isArray(list.rows)) return list.rows;
  return [];
}

function extractDataEnvelope(body) {
  if (!body || typeof body !== 'object') return {};
  return body.data && typeof body.data === 'object' ? body.data : body;
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, locale: 'zh-CN' });
  const consoleErrors = [];
  let currentProbe = '';
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push({ probe: currentProbe, text: msg.text().slice(0, 500) });
  });
  page.on('pageerror', (err) => consoleErrors.push({ probe: currentProbe, text: err.message.slice(0, 500) }));

  await page.goto(`${base}/login`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.locator('input').nth(0).fill(loginName);
  await page.locator('input[type="password"]').fill(password);
  if (await page.locator('input').count() >= 3) {
    const db = page.locator('input').nth(2);
    if (await db.isEnabled().catch(() => false)) await db.fill(dbName);
  }
  await page.locator('button[type="submit"]').click();
  await page.waitForLoadState('networkidle', { timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(1000);

  const token = await page.evaluate(() => {
    const key = Object.keys(sessionStorage).find((item) => item.startsWith('sc_auth_token')) || '';
    return key ? sessionStorage.getItem(key) : '';
  });
  if (!token) throw new Error('login token missing');

  async function intent(intentName, params) {
    return await page.evaluate(async ({ intentName, params, token, dbName }) => {
      const res = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Odoo-DB': dbName, Authorization: `Bearer ${token}` },
        body: JSON.stringify({ intent: intentName, params, meta: { startup_chain_bypass: true } }),
      });
      const body = await res.json();
      if (!res.ok || body.ok === false) throw new Error(JSON.stringify(body.error || body).slice(0, 700));
      return body.data || body;
    }, { intentName, params, token, dbName });
  }

  const init = await intent('system.init', {
    with_preload: false,
    with: ['workspace_home'],
    root_xmlid: 'smart_construction_core.menu_sc_root',
  });
  let entries = uniqEntries(flattenNav(init.nav || []));
  const totalDiscovered = entries.length;
  if (startIndex > 0 || limit > 0) {
    entries = entries.slice(Math.max(0, startIndex), limit > 0 ? Math.max(0, startIndex) + limit : undefined);
  }

  const results = [];
  let lastLoggedIndex = -1;

  function writeProgress() {
    const summary = {
      totalDiscovered,
      startIndex,
      limit,
      totalScanned: entries.length,
      ok: results.filter((row) => row.ok).length,
      failed: results.filter((row) => !row.ok).length,
      withVisibleTable: results.filter((row) => row.visibleHeaders.length > 0).length,
      withVisibleRows: results.filter((row) => row.visibleRowCount > 0).length,
      dataCalls: results.reduce((sum, row) => sum + row.dataCalls.length, 0),
      dataCallFailures: results.reduce((sum, row) => sum + row.dataCalls.filter((call) => !call.ok).length, 0),
      fieldIssues: results.reduce((sum, row) => sum + row.fieldIssues.length, 0),
      consoleErrorCount: consoleErrors.length,
    };
    fs.writeFileSync(outPath, JSON.stringify({
      summary,
      failures: results.filter((row) => !row.ok).slice(0, 100),
      consoleErrors: consoleErrors.slice(0, 100),
      results,
    }, null, 2));
    return summary;
  }

  function logProgress(index) {
    if (lastLoggedIndex === index) return;
    lastLoggedIndex = index;
    const summary = writeProgress();
    console.log(`[user-list-field-data] ${index + 1}/${entries.length} failed=${summary.failed} field_issues=${summary.fieldIssues} data_call_failures=${summary.dataCallFailures}`);
  }

  for (let index = 0; index < entries.length; index += 1) {
    const entry = entries[index];
    const route = entry.actionId
      ? `/a/${entry.actionId}?db=${dbName}${entry.menuId ? `&menu_id=${entry.menuId}` : ''}`
      : `/s/${encodeURIComponent(entry.sceneKey)}?db=${dbName}`;
    currentProbe = `list-field-data:${entry.path}`;
    const dataCalls = [];
    const failedResponses = [];

    const onResponse = async (response) => {
      if (!response.url().includes('/api/v1/intent')) return;
      let requestPayload = {};
      try {
        requestPayload = JSON.parse(response.request().postData() || '{}');
      } catch {
        requestPayload = {};
      }
      const intentName = String(requestPayload.intent || '').trim();
      if (!intentName) return;
      let body = {};
      try {
        body = await response.json();
      } catch {
        body = {};
      }
      if (!response.ok() || body.ok === false) {
        failedResponses.push({
          intent: intentName,
          status: response.status(),
          error: body.error || body.message || '',
        });
      }
      if (intentName !== 'api.data') return;
      const params = requestPayload.params || {};
      const data = extractDataEnvelope(body);
      const records = extractRecords(data);
      const fields = Array.isArray(params.fields) ? params.fields.map(String) : [];
      const recordKeys = [...new Set(records.flatMap((row) => Object.keys(row || {})))].sort();
      const missingRequestedFields = records.length > 0
        ? fields.filter((field) => field !== 'id' && !recordKeys.includes(field))
        : [];
      dataCalls.push({
        ok: response.ok() && body.ok !== false,
        status: response.status(),
        op: String(params.op || ''),
        model: String(params.model || ''),
        fields,
        requestedFieldCount: fields.length,
        recordCount: records.length,
        recordKeys,
        missingRequestedFields,
        error: body.error || body.message || '',
      });
    };

    page.on('response', onResponse);
    let row = {
      index,
      ...entry,
      route,
      ok: false,
      visibleHeaders: [],
      visibleRowCount: 0,
      visibleFirstRow: [],
      hasEmptyState: false,
      failedResponses: [],
      dataCalls,
      fieldIssues: [],
      issue: '',
    };
    try {
      await page.goto(`${base}${route}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await page.waitForLoadState('networkidle', { timeout: 8000 }).catch(() => {});
      await page.waitForTimeout(900);
      const text = await page.locator('body').innerText({ timeout: 10000 }).catch(() => '');
      const pageHasError = /render error|contract not renderable|missing required nav|页面加载失败|异常|Traceback|Cannot read/i.test(text);
      const visible = await page.evaluate((helperHeadersList) => {
        const helperHeaders = new Set(helperHeadersList);
        function normalize(value) {
          return String(value || '').replace(/\s+/g, ' ').trim();
        }
        function visibleTable(table) {
          const rect = table.getBoundingClientRect();
          return rect.width > 0 && rect.height > 0;
        }
        function headerText(node) {
          const clone = node.cloneNode(true);
          for (const child of Array.from(clone.querySelectorAll('svg,.sort-indicator,.column-resize-handle,[aria-hidden="true"]'))) {
            child.remove();
          }
          return normalize(clone.textContent);
        }
        const tables = Array.from(document.querySelectorAll('table.flat-table, table.group-table, .table table, table')).filter(visibleTable);
        const tableInfos = tables.map((table) => {
          const headers = Array.from(table.querySelectorAll('thead th'))
            .map(headerText)
            .filter((item) => !helperHeaders.has(item));
          const rows = Array.from(table.querySelectorAll('tbody tr'));
          const firstRow = rows[0]
            ? Array.from(rows[0].querySelectorAll('td'))
              .filter((cell) => !cell.classList.contains('cell-select')
                && !cell.classList.contains('cell-row-number')
                && !cell.classList.contains('cell-column-picker'))
              .map((cell) => normalize(cell.textContent))
            : [];
          return { headers, rowCount: rows.length, firstRow };
        });
        tableInfos.sort((left, right) => {
          if (right.headers.length !== left.headers.length) return right.headers.length - left.headers.length;
          return right.rowCount - left.rowCount;
        });
        const best = tableInfos[0] || { headers: [], rowCount: 0, firstRow: [] };
        return {
          headers: best.headers,
          rowCount: best.rowCount,
          firstRow: best.firstRow,
          emptyState: /没有匹配记录|暂无数据|0 条|无数据/.test(String(document.body?.textContent || '')),
        };
      }, Array.from(helperHeaders));
      await page.waitForTimeout(100);
      const fieldIssues = [];
      for (const call of dataCalls) {
        for (const field of call.missingRequestedFields) {
          fieldIssues.push({ model: call.model, field, reason: 'requested field missing from returned records' });
        }
      }
      const hasFailedDataCall = dataCalls.some((call) => !call.ok);
      const hasFailedResponse = failedResponses.length > 0;
      const hasRowsButNoHeaders = visible.rowCount > 0 && visible.headers.length === 0;
      const hasDataButNoVisibleRows = dataCalls.some((call) => call.recordCount > 0) && visible.rowCount === 0 && !/看板|仪表盘|驾驶舱/.test(text);
      const issueParts = [];
      if (pageHasError) issueParts.push('page has visible error text');
      if (hasFailedResponse) issueParts.push('intent response failed');
      if (fieldIssues.length > 0) issueParts.push('returned records missing requested fields');
      if (hasRowsButNoHeaders) issueParts.push('visible rows without visible headers');
      if (hasDataButNoVisibleRows) issueParts.push('api data returned rows but no visible table rows');
      row = {
        ...row,
        visibleHeaders: visible.headers,
        visibleRowCount: visible.rowCount,
        visibleFirstRow: visible.firstRow,
        hasEmptyState: visible.emptyState,
        failedResponses,
        fieldIssues,
        ok: issueParts.length === 0 && !hasFailedDataCall,
        issue: issueParts.join('; '),
      };
    } catch (err) {
      row = { ...row, failedResponses, ok: false, issue: err instanceof Error ? err.message : String(err) };
    } finally {
      page.off('response', onResponse);
    }
    results.push(row);
    if ((index + 1) % 10 === 0 || index === entries.length - 1) logProgress(index);
  }

  const summary = writeProgress();
  const report = JSON.parse(fs.readFileSync(outPath, 'utf8'));
  console.log(JSON.stringify({
    summary,
    outPath,
    failures: report.failures.slice(0, 12),
    consoleErrors: report.consoleErrors.slice(0, 12),
  }, null, 2));
  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

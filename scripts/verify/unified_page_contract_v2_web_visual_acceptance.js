#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

const root = path.resolve(__dirname, '../..');
const requireFromWeb = createRequire(path.join(root, 'frontend/apps/web/package.json'));
const { chromium } = requireFromWeb('playwright');

const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || path.join(root, 'artifacts');
const REPORT = process.env.REPORT || path.join(ARTIFACTS_DIR, 'backend', 'unified_page_contract_v2_web_visual_acceptance.json');
const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\..+$/, '');
const outDir = path.join(ARTIFACTS_DIR, 'playwright', 'web_v2_visual_acceptance', ts);

function readJson(file) {
  return JSON.parse(fs.readFileSync(path.join(root, file), 'utf8'));
}

function writeJson(file, data) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n', 'utf8');
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function walkContainers(containers, result = []) {
  for (const container of asArray(containers)) {
    result.push(container);
    walkContainers(container.children, result);
  }
  return result;
}

function collectWidgets(contract) {
  const containers = walkContainers(contract.layoutContract && contract.layoutContract.containerTree);
  return containers.flatMap((container) => asArray(container.widgetList).map((widget) => ({ ...widget, container })));
}

function statusMap(rows, key) {
  return new Map(asArray(rows).map((row) => [String(row[key] || ''), row]));
}

function renderBadges(items) {
  return items.map((item) => `<span class="badge">${escapeHtml(item)}</span>`).join('');
}

function renderActions(contract) {
  const buttonStatus = statusMap(contract.statusContract && contract.statusContract.buttonStatus, 'btnId');
  return asArray(contract.actionContract && contract.actionContract.actionRuleList)
    .map((action) => {
      const status = buttonStatus.get(action.actionId) || buttonStatus.get(action.btnId) || {};
      return `
        <button class="action" data-v2-action="${escapeHtml(action.actionId)}" ${status.disabled ? 'disabled' : ''}>
          <span>${escapeHtml(action.triggerType || 'action')}</span>
          <strong>${escapeHtml(action.actionId)}</strong>
        </button>`;
    })
    .join('');
}

function renderField(contract, widget) {
  const widgetStatus = statusMap(contract.statusContract && contract.statusContract.widgetStatus, 'widgetId').get(widget.widgetId) || {};
  const value = contract.dataContract && contract.dataContract.mainData
    ? contract.dataContract.mainData[widget.fieldCode]
    : '';
  const tags = [
    widget.componentKey,
    widgetStatus.required ? 'required' : 'optional',
    widgetStatus.readonly ? 'readonly' : 'editable',
  ].filter(Boolean);
  return `
    <label class="field" data-v2-field="${escapeHtml(widget.fieldCode)}">
      <span class="field-label">${escapeHtml(widget.label || widget.fieldCode)}</span>
      <input value="${escapeHtml(Array.isArray(value) ? value.join(', ') : value)}" ${widgetStatus.disabled || widgetStatus.readonly ? 'disabled' : ''} />
      <span class="field-tags">${renderBadges(tags)}</span>
    </label>`;
}

function renderTable(contract, widget) {
  const dataKey = widget.componentConfig && widget.componentConfig.dataKey ? widget.componentConfig.dataKey : widget.fieldCode;
  const rows = asArray(contract.dataContract && contract.dataContract.tableRows && contract.dataContract.tableRows[dataKey]);
  const columns = Array.from(new Set(rows.flatMap((row) => Object.keys(row))));
  return `
    <div class="table-wrap" data-v2-table="${escapeHtml(dataKey)}">
      <table>
        <thead><tr>${columns.map((col) => `<th>${escapeHtml(col)}</th>`).join('')}</tr></thead>
        <tbody>
          ${rows.map((row) => `<tr>${columns.map((col) => `<td>${escapeHtml(row[col])}</td>`).join('')}</tr>`).join('')}
        </tbody>
      </table>
    </div>`;
}

function renderContract(contract) {
  const widgets = collectWidgets(contract);
  const selectors = asArray(contract.statusContract && contract.statusContract.selectorStatus);
  const dataSources = Object.keys((contract.dataContract && contract.dataContract.dataSource) || {});
  const page = contract.pageInfo || {};
  return `
    <section class="surface" data-v2-surface="${escapeHtml(page.viewType)}">
      <header class="surface-header">
        <div>
          <p class="eyebrow">Unified Page Contract v2</p>
          <h1>${escapeHtml(page.pageName || page.pageId)}</h1>
        </div>
        <div class="meta">
          ${renderBadges([page.clientType, page.viewType, page.contractVersion, page.model].filter(Boolean))}
        </div>
      </header>
      <div class="summary">
        <div><span>auth</span><strong>${escapeHtml(contract.statusContract && contract.statusContract.globalStatus && contract.statusContract.globalStatus.pageAuth)}</strong></div>
        <div><span>widgets</span><strong>${widgets.length}</strong></div>
        <div><span>actions</span><strong>${asArray(contract.actionContract && contract.actionContract.actionRuleList).length}</strong></div>
        <div><span>dataSource</span><strong>${dataSources.length}</strong></div>
      </div>
      <div class="content">
        ${widgets.map((widget) => widget.widgetType === 'table' ? renderTable(contract, widget) : renderField(contract, widget)).join('')}
      </div>
      <footer class="footer">
        <div class="actions">${renderActions(contract)}</div>
        <div class="selectors">${renderBadges(selectors.map((row) => `${row.selector}:${row.reasonCode || row.readonly || 'status'}`))}</div>
      </footer>
    </section>`;
}

function buildHtml(contracts) {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Web v2 visual acceptance</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: #f5f6f8;
      color: #1e293b;
      font: 14px/1.45 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    main { width: min(1180px, calc(100vw - 32px)); margin: 24px auto; display: grid; gap: 16px; }
    .surface { background: #fff; border: 1px solid #d7dde5; border-radius: 8px; overflow: hidden; }
    .surface-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; padding: 18px 20px; border-bottom: 1px solid #e5e9ef; }
    .eyebrow { margin: 0 0 4px; color: #64748b; font-size: 12px; font-weight: 700; text-transform: uppercase; }
    h1 { margin: 0; font-size: 22px; letter-spacing: 0; }
    .meta, .field-tags, .selectors { display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }
    .badge { border: 1px solid #cbd5e1; border-radius: 999px; padding: 3px 8px; color: #334155; background: #f8fafc; font-size: 12px; white-space: nowrap; }
    .summary { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); border-bottom: 1px solid #e5e9ef; }
    .summary div { padding: 12px 20px; border-right: 1px solid #e5e9ef; }
    .summary div:last-child { border-right: 0; }
    .summary span { display: block; color: #64748b; font-size: 12px; }
    .summary strong { display: block; margin-top: 2px; font-size: 16px; }
    .content { padding: 18px 20px; display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); gap: 14px; }
    .field { grid-column: span 6; min-width: 0; display: grid; gap: 8px; }
    .field-label { font-weight: 700; }
    input { width: 100%; min-height: 38px; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px 10px; background: #fff; color: #0f172a; }
    input:disabled { background: #eef2f7; color: #475569; }
    .table-wrap { grid-column: 1 / -1; overflow: auto; border: 1px solid #d7dde5; border-radius: 6px; }
    table { width: 100%; min-width: 540px; border-collapse: collapse; }
    th, td { padding: 10px 12px; border-bottom: 1px solid #e5e9ef; text-align: left; }
    th { background: #f8fafc; color: #475569; font-size: 12px; text-transform: uppercase; }
    .footer { display: flex; justify-content: space-between; align-items: center; gap: 16px; padding: 14px 20px; border-top: 1px solid #e5e9ef; background: #fbfcfd; }
    .actions { display: flex; gap: 8px; flex-wrap: wrap; }
    .action { border: 1px solid #2563eb; border-radius: 6px; background: #2563eb; color: #fff; padding: 7px 10px; display: inline-grid; gap: 1px; text-align: left; }
    .action span { font-size: 11px; opacity: .82; }
    .action strong { font-size: 12px; }
    @media (max-width: 720px) {
      main { width: min(100vw - 20px, 480px); margin: 10px auto; gap: 10px; }
      .surface-header, .footer { flex-direction: column; align-items: stretch; }
      .meta, .selectors { justify-content: flex-start; }
      .summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .summary div { border-bottom: 1px solid #e5e9ef; }
      .field { grid-column: 1 / -1; }
      table { min-width: 420px; }
    }
  </style>
</head>
<body>
  <main>${contracts.map(renderContract).join('')}</main>
</body>
</html>`;
}

async function inspectViewport(browser, name, viewport, html) {
  const page = await browser.newPage({ viewport });
  const consoleErrors = [];
  const pageErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => pageErrors.push(err.message));
  await page.setContent(html, { waitUntil: 'load' });
  await page.screenshot({ path: path.join(outDir, `${name}.png`), fullPage: true });
  const metrics = await page.evaluate(() => {
    const visible = (selector) => Array.from(document.querySelectorAll(selector)).filter((el) => {
      const rect = el.getBoundingClientRect();
      const style = window.getComputedStyle(el);
      return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
    }).length;
    return {
      viewportWidth: window.innerWidth,
      scrollWidth: document.documentElement.scrollWidth,
      bodyText: document.body.innerText,
      surfaces: visible('[data-v2-surface]'),
      fields: visible('[data-v2-field]'),
      tables: visible('[data-v2-table]'),
      actions: visible('[data-v2-action]'),
      badges: visible('.badge'),
    };
  });
  await page.close();
  return {
    name,
    viewport,
    screenshot: path.join(outDir, `${name}.png`),
    consoleErrors,
    pageErrors,
    metrics,
  };
}

async function run() {
  fs.mkdirSync(outDir, { recursive: true });
  const contracts = [
    readJson('docs/architecture/unified_page_contract_v2/examples/list_project.json'),
    readJson('docs/architecture/unified_page_contract_v2/examples/form_project.json'),
  ];
  const html = buildHtml(contracts);
  const htmlPath = path.join(outDir, 'web_v2_visual_acceptance.html');
  fs.writeFileSync(htmlPath, html, 'utf8');

  const browser = await chromium.launch({ headless: true });
  const results = [];
  try {
    results.push(await inspectViewport(browser, 'desktop', { width: 1366, height: 900 }, html));
    results.push(await inspectViewport(browser, 'narrow', { width: 390, height: 844 }, html));
  } finally {
    await browser.close().catch(() => undefined);
  }

  const errors = [];
  for (const result of results) {
    const { metrics } = result;
    const bodyText = String(metrics.bodyText || '').toLowerCase();
    if (result.consoleErrors.length) errors.push(`${result.name}: browser console errors`);
    if (result.pageErrors.length) errors.push(`${result.name}: page errors`);
    if (metrics.scrollWidth > metrics.viewportWidth + 1) {
      errors.push(`${result.name}: horizontal overflow ${metrics.scrollWidth} > ${metrics.viewportWidth}`);
    }
    if (metrics.surfaces < 2) errors.push(`${result.name}: expected list and form v2 surfaces`);
    if (metrics.fields < 2) errors.push(`${result.name}: expected visible v2 fields`);
    if (metrics.tables < 1) errors.push(`${result.name}: expected visible v2 table`);
    if (metrics.actions < 2) errors.push(`${result.name}: expected visible v2 actions`);
    if (!bodyText.includes('unified page contract v2')) errors.push(`${result.name}: missing v2 title`);
    if (!bodyText.includes('web_pc')) errors.push(`${result.name}: missing web_pc client badge`);
    if (!bodyText.includes('datasource')) errors.push(`${result.name}: missing dataSource summary`);
  }

  const report = {
    ok: errors.length === 0,
    decision: errors.length === 0 ? 'web_v2_browser_visual_acceptance_passed' : 'web_v2_browser_visual_acceptance_failed',
    html: htmlPath,
    results,
    errors,
    fixtures: contracts.map((contract) => contract.pageInfo && contract.pageInfo.pageId).filter(Boolean),
  };
  writeJson(REPORT, report);
  writeJson(path.join(outDir, 'summary.json'), report);
  if (errors.length) {
    console.error('[web_v2_visual_acceptance] failed');
    for (const error of errors) console.error(`- ${error}`);
    console.error(`[web_v2_visual_acceptance] report: ${REPORT}`);
    process.exitCode = 1;
    return;
  }
  console.log('[web_v2_visual_acceptance] passed');
  console.log(`[web_v2_visual_acceptance] report: ${REPORT}`);
  for (const result of results) {
    console.log(`[web_v2_visual_acceptance] screenshot: ${result.screenshot}`);
  }
}

run().catch((err) => {
  console.error(`[web_v2_visual_acceptance] failed: ${err && err.message ? err.message : String(err)}`);
  process.exitCode = 1;
});

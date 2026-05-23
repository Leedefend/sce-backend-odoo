#!/usr/bin/env node
'use strict';

const path = require('path');

const { chromium } = require(path.resolve(__dirname, '../../frontend/apps/web/node_modules/playwright'));

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:18081';
const DB_NAME = process.env.DB_NAME || process.env.E2E_DB || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'demo_role_finance';
const PASSWORD = process.env.E2E_PASSWORD || 'demo';
const ACTION_ID = Number(process.env.INVOICE_OUTPUT_ACTION_ID || 755);

function fail(message) {
  throw new Error(message);
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const listResponses = [];

  page.on('response', async (response) => {
    if (!response.url().includes('/api/v1/intent')) return;
    try {
      const body = await response.json();
      const meta = body && body.meta ? body.meta : {};
      const data = body && body.data ? body.data : {};
      if (meta.intent !== 'api.data' || meta.model !== 'sc.receipt.invoice.line') return;
      const rowCount = Array.isArray(data.rows)
        ? data.rows.length
        : (Array.isArray(data.records)
          ? data.records.length
          : (Array.isArray(data.grouped_rows)
            ? data.grouped_rows.reduce((count, row) => count + (Array.isArray(row.sample_rows) ? row.sample_rows.length : 0), 0)
            : 0));
      listResponses.push({
        status: response.status(),
        total: Number(data.total || 0),
        sample_count: rowCount,
      });
    } catch (_err) {
      // Ignore unrelated non-JSON responses.
    }
  });

  try {
    await page.goto(`${FRONTEND_URL}/login?db=${encodeURIComponent(DB_NAME)}`, {
      waitUntil: 'networkidle',
      timeout: 30000,
    });
    await page.locator('input[placeholder="请输入账号"]').fill(LOGIN);
    await page.locator('input[placeholder="请输入密码"]').fill(PASSWORD);
    await page.locator('button').filter({ hasText: /登录|登陆/ }).click();
    await page.waitForURL((url) => !String(url).includes('/login'), { timeout: 30000 });

    await page.goto(`${FRONTEND_URL}/a/${ACTION_ID}?db=${encodeURIComponent(DB_NAME)}`, {
      waitUntil: 'networkidle',
      timeout: 30000,
    });
    await page.waitForTimeout(1500);

    const bodyText = await page.locator('body').innerText({ timeout: 10000 });
    for (const label of ['销项发票', '发票号码', '开票单位', '发票金额']) {
      if (!bodyText.includes(label)) {
        fail(`browser output invoice detail missing label: ${label}`);
      }
    }

    const latest = listResponses[listResponses.length - 1];
    if (!latest) fail('api.data response for sc.receipt.invoice.line was not observed');
    if (latest.total !== 4454) fail(`visible output invoice total expected 4454, got ${latest.total}`);
    if (latest.sample_count <= 0) fail('visible output invoice should expose sample rows');

    console.log('[verify.invoice_output_detail.browser_smoke] PASS');
    console.log(JSON.stringify({ url: page.url(), total: latest.total, sample_count: latest.sample_count }));
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error(`[verify.invoice_output_detail.browser_smoke] FAIL: ${err.message}`);
  process.exit(1);
});

#!/usr/bin/env node
'use strict';

const path = require('path');

const { chromium } = require(path.resolve(__dirname, '../../frontend/apps/web/node_modules/playwright'));

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:18081';
const DB_NAME = process.env.DB_NAME || process.env.E2E_DB || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'demo_role_finance';
const PASSWORD = process.env.E2E_PASSWORD || 'demo';
const ACTION_ID = Number(process.env.INVOICE_LEDGER_ACTION_ID || 630);

function fail(message) {
  throw new Error(message);
}

async function main() {
  if (!ACTION_ID) fail('INVOICE_LEDGER_ACTION_ID is required');
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const groupedResponses = [];

  page.on('response', async (response) => {
    if (!response.url().includes('/api/v1/intent')) return;
    try {
      const body = await response.json();
      const meta = body && body.meta ? body.meta : {};
      const data = body && body.data ? body.data : {};
      if (meta.intent !== 'api.data' || meta.group_by_field !== 'source_kind') return;
      groupedResponses.push({
        status: response.status(),
        group_count: Number(meta.group_count || 0),
        groups: (data.group_summary || []).map((row) => ({
          label: String(row.label || ''),
          count: Number(row.count || 0),
        })),
        grouped_rows: (data.grouped_rows || []).map((row) => ({
          label: String(row.label || ''),
          count: Number(row.count || 0),
          sample_count: Array.isArray(row.sample_rows) ? row.sample_rows.length : 0,
        })),
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
    for (const label of ['发票总台账', '销项开票申请', '销项发票登记', '进项税额上报', '分组结果']) {
      if (!bodyText.includes(label)) {
        fail(`browser invoice ledger missing label: ${label}`);
      }
    }

    const latest = groupedResponses[groupedResponses.length - 1];
    if (!latest) {
      fail('api.data grouped response for source_kind was not observed');
    }
    const labels = new Set(latest.groups.map((row) => row.label));
    for (const label of ['发票登记', '进项税额', '销项税额', '预缴税']) {
      if (!labels.has(label)) {
        fail(`api.data group_summary missing label: ${label}`);
      }
    }
    if (!latest.grouped_rows.length || latest.grouped_rows.some((row) => row.sample_count <= 0)) {
      fail('api.data grouped_rows must include visible invoice sample rows');
    }

    console.log('[invoice_entry_fact_browser_smoke] PASS');
    console.log(JSON.stringify({
      url: page.url(),
      groups: latest.groups,
      grouped_rows: latest.grouped_rows,
    }));
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error(`[invoice_entry_fact_browser_smoke] FAIL: ${err.message}`);
  process.exit(1);
});

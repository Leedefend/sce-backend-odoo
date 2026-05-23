#!/usr/bin/env node
'use strict';

const path = require('path');

const { chromium } = require(path.resolve(__dirname, '../../frontend/apps/web/node_modules/playwright'));

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:18081';
const DB_NAME = process.env.DB_NAME || process.env.E2E_DB || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'demo_role_finance';
const PASSWORD = process.env.E2E_PASSWORD || 'demo';
const ACTION_ID = Number(process.env.PAYMENT_REQUEST_RECEIVE_ACTION_ID || 672);

function fail(message) {
  throw new Error(message);
}

async function main() {
  if (!ACTION_ID) fail('PAYMENT_REQUEST_RECEIVE_ACTION_ID is required');
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const groupedResponses = [];

  page.on('response', async (response) => {
    if (!response.url().includes('/api/v1/intent')) return;
    try {
      const body = await response.json();
      const meta = body && body.meta ? body.meta : {};
      const data = body && body.data ? body.data : {};
      if (meta.intent !== 'api.data' || meta.group_by_field !== 'receipt_type') return;
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
      // Non-JSON responses are unrelated to this smoke.
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

    const targetUrl = `${FRONTEND_URL}/a/${ACTION_ID}?db=${encodeURIComponent(DB_NAME)}&group_by=receipt_type`;
    await page.goto(targetUrl, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(1500);

    const bodyText = await page.locator('body').innerText({ timeout: 10000 });
    for (const label of ['正常类型收款', '其他类型收款']) {
      if (!bodyText.includes(label)) {
        fail(`browser grouped list missing label: ${label}`);
      }
    }
    if (!bodyText.includes('分组结果')) {
      fail('browser grouped list missing grouped result section');
    }

    const latest = groupedResponses[groupedResponses.length - 1];
    if (!latest) {
      fail('api.data grouped response for receipt_type was not observed');
    }
    const labels = new Set(latest.groups.map((row) => row.label));
    for (const label of ['正常类型收款', '其他类型收款']) {
      if (!labels.has(label)) {
        fail(`api.data group_summary missing label: ${label}`);
      }
    }
    if (!latest.grouped_rows.length || latest.grouped_rows.some((row) => row.sample_count <= 0)) {
      fail('api.data grouped_rows must include visible sample rows');
    }

    console.log('[payment_request_receipt_type_browser_group_smoke] PASS');
    console.log(
      JSON.stringify({
        url: page.url(),
        groups: latest.groups,
        grouped_rows: latest.grouped_rows,
      }),
    );
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error(`[payment_request_receipt_type_browser_group_smoke] FAIL: ${err.message}`);
  process.exit(1);
});

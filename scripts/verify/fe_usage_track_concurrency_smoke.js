#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const { assertIntentEnvelope, extractTraceId } = require('./intent_smoke_utils');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const LOGIN = process.env.E2E_LOGIN || process.env.SCENE_LOGIN || 'admin';
const PASSWORD = process.env.E2E_PASSWORD || process.env.SCENE_PASSWORD || process.env.ADMIN_PASSWD || 'admin';
const AUTH_TOKEN = process.env.AUTH_TOKEN || '';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const REQUEST_TOTAL = Number(process.env.USAGE_TRACK_REQUEST_TOTAL || 120);
const CONCURRENCY = Number(process.env.USAGE_TRACK_CONCURRENCY || 24);
const SCENE_KEY = String(process.env.USAGE_TRACK_SCENE_KEY || 'projects.intake').trim();

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'usage-track-concurrency-smoke', ts);

function log(message) {
  console.log(`[fe_usage_track_concurrency_smoke] ${message}`);
}

function writeJson(filePath, data) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
}

function writeSummary(lines) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, 'summary.md'), lines.join('\n'));
}

function requestJson(url, payload, headers = {}) {
  return new Promise((resolve, reject) => {
    const parsedUrl = new URL(url);
    const body = JSON.stringify(payload || {});
    const options = {
      method: 'POST',
      hostname: parsedUrl.hostname,
      port: parsedUrl.port || (parsedUrl.protocol === 'https:' ? 443 : 80),
      path: parsedUrl.pathname + parsedUrl.search,
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
        ...headers,
      },
    };
    const client = parsedUrl.protocol === 'https:' ? https : http;
    const req = client.request(options, (res) => {
      let raw = '';
      res.on('data', (chunk) => {
        raw += chunk;
      });
      res.on('end', () => {
        let parsed = {};
        try {
          parsed = JSON.parse(raw || '{}');
        } catch {
          parsed = { raw };
        }
        resolve({ status: res.statusCode || 0, body: parsed });
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

async function runWithConcurrency(items, workerLimit, handler) {
  const results = [];
  let pointer = 0;

  async function worker() {
    while (true) {
      const index = pointer;
      pointer += 1;
      if (index >= items.length) {
        return;
      }
      // eslint-disable-next-line no-await-in-loop
      const result = await handler(items[index], index);
      results[index] = result;
    }
  }

  const workers = [];
  const size = Math.max(1, workerLimit);
  for (let index = 0; index < size; index += 1) {
    workers.push(worker());
  }
  await Promise.all(workers);
  return results;
}

async function main() {
  if (!DB_NAME) {
    throw new Error('DB_NAME is required');
  }
  if (!SCENE_KEY) {
    throw new Error('USAGE_TRACK_SCENE_KEY is required');
  }

  const intentUrl = `${BASE_URL}/api/v1/intent`;
  let token = AUTH_TOKEN;

  if (!token) {
    const loginResponse = await requestJson(
      intentUrl,
      { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } },
      { 'X-Anonymous-Intent': '1' }
    );
    writeJson(path.join(outDir, 'login.log'), loginResponse);
    assertIntentEnvelope(loginResponse, 'login');
    token = (((loginResponse.body || {}).data) || {}).token || '';
    if (!token) {
      throw new Error('login response missing token');
    }
  }

  const headers = { Authorization: `Bearer ${token}`, 'X-Odoo-DB': DB_NAME };
  const sequence = Array.from({ length: REQUEST_TOTAL }, (_, index) => index + 1);
  const startedAt = Date.now();

  const results = await runWithConcurrency(sequence, CONCURRENCY, async (index) => {
    const payload = {
      intent: 'usage.track',
      params: {
        db: DB_NAME,
        event_type: 'scene_open',
        scene_key: SCENE_KEY,
      },
    };
    const response = await requestJson(intentUrl, payload, headers);
    const traceId = extractTraceId(response.body || {});
    const okEnvelope = response.status < 400 && response.body && response.body.ok === true;
    const errorCode = ((response.body || {}).error || {}).code || '';
    const errorMessage = ((response.body || {}).error || {}).message || '';

    return {
      index,
      status: response.status,
      ok: okEnvelope,
      trace_id: traceId,
      error_code: errorCode,
      error_message: errorMessage,
      body: okEnvelope ? undefined : response.body,
    };
  });

  const durationMs = Date.now() - startedAt;
  const failed = results.filter((item) => !item.ok);
  const statusCounts = {};
  const errorCodeCounts = {};
  for (const item of results) {
    const statusKey = String(item.status);
    statusCounts[statusKey] = (statusCounts[statusKey] || 0) + 1;
    if (item.error_code) {
      errorCodeCounts[item.error_code] = (errorCodeCounts[item.error_code] || 0) + 1;
    }
  }

  writeJson(path.join(outDir, 'responses.log'), {
    db: DB_NAME,
    request_total: REQUEST_TOTAL,
    concurrency: CONCURRENCY,
    scene_key: SCENE_KEY,
    duration_ms: durationMs,
    status_counts: statusCounts,
    error_code_counts: errorCodeCounts,
    failed_count: failed.length,
    failed_samples: failed.slice(0, 8),
  });

  const summary = [
    `db: ${DB_NAME}`,
    `request_total: ${REQUEST_TOTAL}`,
    `concurrency: ${CONCURRENCY}`,
    `scene_key: ${SCENE_KEY}`,
    `duration_ms: ${durationMs}`,
    `failed_count: ${failed.length}`,
    `status_counts: ${JSON.stringify(statusCounts)}`,
    `error_code_counts: ${JSON.stringify(errorCodeCounts)}`,
  ];
  writeSummary(summary);

  if (failed.length > 0) {
    throw new Error(`usage.track concurrency failed_count=${failed.length}`);
  }

  log('PASS usage.track concurrency smoke');
  log(`artifacts: ${outDir}`);
}

main().catch((error) => {
  console.error(`[fe_usage_track_concurrency_smoke] FAIL: ${error.message}`);
  process.exit(1);
});


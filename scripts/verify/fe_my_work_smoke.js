#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const { assertIntentEnvelope } = require('./intent_smoke_utils');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const LOGIN =
  process.env.E2E_LOGIN ||
  process.env.ROLE_PM_LOGIN ||
  process.env.SCENE_LOGIN ||
  '';
const PASSWORD =
  process.env.E2E_PASSWORD ||
  process.env.ROLE_PM_PASSWORD ||
  process.env.SCENE_PASSWORD ||
  process.env.ADMIN_PASSWD ||
  '';
const AUTH_TOKEN = process.env.AUTH_TOKEN || '';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const ALLOW_SKIP_UNKNOWN_INTENT = ['1', 'true', 'yes', 'on'].includes(
  String(process.env.MY_WORK_SMOKE_ALLOW_SKIP || '').trim().toLowerCase()
);

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'my-work-smoke-v10_2', ts);

function log(msg) {
  console.log(`[fe_my_work_smoke] ${msg}`);
}

function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2));
}

function writeSummary(lines) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, 'summary.md'), lines.join('\n'));
}

function requestJson(url, payload, headers = {}) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const body = JSON.stringify(payload || {});
    const opts = {
      method: 'POST',
      hostname: u.hostname,
      port: u.port || (u.protocol === 'https:' ? 443 : 80),
      path: u.pathname + u.search,
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
        ...headers,
      },
    };
    const client = u.protocol === 'https:' ? https : http;
    const req = client.request(opts, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => {
        let parsed = {};
        try {
          parsed = JSON.parse(data || '{}');
        } catch {
          parsed = { raw: data };
        }
        resolve({ status: res.statusCode || 0, body: parsed });
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

function buildLoginCandidates() {
  const candidates = [];
  const seen = new Set();
  const pushCandidate = (loginRaw, passwordRaw, source) => {
    const login = String(loginRaw || '').trim();
    const password = String(passwordRaw || '').trim();
    if (!login || !password) return;
    const key = `${login}::${password}`;
    if (seen.has(key)) return;
    seen.add(key);
    candidates.push({ login, password, source });
  };

  pushCandidate(LOGIN, PASSWORD, 'explicit_env');
  pushCandidate(process.env.ADMIN_LOGIN || 'admin', process.env.ADMIN_PASSWD || 'admin', 'admin_fallback');
  pushCandidate('demo_role_project_manager', 'demo', 'pm_demo_fallback');
  return candidates;
}

function assertSortedById(items, dir) {
  let prev = null;
  for (const row of items || []) {
    const current = Number(row && row.id ? row.id : 0);
    if (prev !== null) {
      if (dir === 'asc' && current < prev) return false;
      if (dir === 'desc' && current > prev) return false;
    }
    prev = current;
  }
  return true;
}

function collectSourceModels(items) {
  const models = new Set();
  for (const row of items || []) {
    const model = String((row && row.source_model) || '').trim();
    if (model) models.add(model);
  }
  return Array.from(models).sort();
}

async function main() {
  if (!DB_NAME) throw new Error('DB_NAME is required');

  const intentUrl = `${BASE_URL}/api/v1/intent`;
  const summary = [];

  let token = AUTH_TOKEN;
  let loginUsed = '';
  if (!token) {
    const attempts = [];
    const candidates = buildLoginCandidates();
    for (const candidate of candidates) {
      const loginResp = await requestJson(
        intentUrl,
        { intent: 'login', params: { db: DB_NAME, login: candidate.login, password: candidate.password } },
        { 'X-Anonymous-Intent': '1' }
      );
      attempts.push({
        source: candidate.source,
        login: candidate.login,
        status: loginResp.status || 0,
        ok: Boolean((loginResp.body || {}).ok),
        error: ((loginResp.body || {}).error || {}).message || '',
      });
      try {
        assertIntentEnvelope(loginResp, 'login');
      } catch (_err) {
        continue;
      }
      const loginData = (loginResp.body || {}).data || {};
      const session = loginData.session || {};
      const candidateToken = session.token || loginData.token || '';
      if (!candidateToken) continue;
      token = candidateToken;
      loginUsed = candidate.login;
      writeJson(path.join(outDir, 'login.log'), { candidate, response: loginResp });
      break;
    }
    writeJson(path.join(outDir, 'login_attempts.log'), { candidates: attempts });
    if (!token) {
      const last = attempts.length ? attempts[attempts.length - 1] : null;
      throw new Error(`login failed: status=${last ? last.status : 0}`);
    }
  }

  const authHeader = { Authorization: `Bearer ${token}`, 'X-Odoo-DB': DB_NAME };

  const pageContractResp = await requestJson(
    intentUrl,
    { intent: 'page.contract', params: { page_key: 'my_work', scene: 'web', root_xmlid: 'smart_construction_core.menu_sc_root' } },
    authHeader,
  );
  writeJson(path.join(outDir, 'page_contract_my_work.log'), pageContractResp);
  assertIntentEnvelope(pageContractResp, 'page.contract');
  const pageContractData = (pageContractResp.body || {}).data || {};
  const pageContract = pageContractData.page_contract || {};
  const orchestration = pageContract.page_orchestration_v1 || {};
  const pageMeta = orchestration.page || {};
  const zones = Array.isArray(orchestration.zones) ? orchestration.zones : [];
  const title = String(pageMeta.title || '').trim();
  if (title !== '我的工作') throw new Error(`page.contract title mismatch: ${title || '-'}`);
  const forbiddenTitles = new Set(['页面头部', '主体内容', '辅助信息', '扩展信息', 'hero', 'todo_focus', 'list_main']);
  for (const zone of zones) {
    const zoneTitle = String((zone && zone.title) || '').trim();
    if (forbiddenTitles.has(zoneTitle)) throw new Error(`zone title leaked technical label: ${zoneTitle}`);
    const blocks = Array.isArray(zone && zone.blocks) ? zone.blocks : [];
    for (const block of blocks) {
      const blockTitle = String((block && block.title) || '').trim();
      if (forbiddenTitles.has(blockTitle)) throw new Error(`block title leaked technical label: ${blockTitle}`);
    }
  }

  const req1 = {
    intent: 'my.work.summary',
    params: {
      limit: 80,
      limit_each: 16,
      page: 1,
      page_size: 10,
      sort_by: 'id',
      sort_dir: 'desc',
      section: 'all',
      source: 'all',
      reason_code: 'all',
      search: '',
    },
  };
  const resp1 = await requestJson(intentUrl, req1, authHeader);
  writeJson(path.join(outDir, 'my_work_page1_desc.log'), resp1);
  try {
    assertIntentEnvelope(resp1, 'my.work.summary');
  } catch (_err) {
    const errMsg = String((((resp1.body || {}).error) || {}).message || '');
    if (errMsg.includes('Unknown intent: my.work.summary')) {
      if (ALLOW_SKIP_UNKNOWN_INTENT) {
        summary.push('status: SKIP');
        summary.push('reason: my.work.summary intent not registered in current DB');
        summary.push(`db: ${DB_NAME}`);
        writeSummary(summary);
        log('SKIP my-work smoke (intent not registered)');
        log(`artifacts: ${outDir}`);
        return;
      }
      throw new Error(
        'my.work.summary is not registered; run `make policy.ensure.extension_modules DB_NAME=<db>` ' +
          '(or set AUTO_FIX_EXTENSION_MODULES=1 for auto-fix + restart)'
      );
    }
    throw new Error(`my.work.summary page1 failed: status=${resp1.status} message=${errMsg || '-'}`);
  }
  const data1 = (resp1.body || {}).data || {};
  const filters1 = data1.filters || {};
  const items1 = Array.isArray(data1.items) ? data1.items : [];
  const sourceModels1 = collectSourceModels(items1);
  if (Number(filters1.page || 0) !== 1) throw new Error('page=1 not reflected');
  const reflectedPageSize = Number(filters1.page_size || 0);
  if (!Number.isFinite(reflectedPageSize) || reflectedPageSize <= 0) {
    throw new Error('page_size not reflected as positive number');
  }
  if (String(filters1.sort_by || '') !== 'id') throw new Error('sort_by=id not reflected');
  if (String(filters1.sort_dir || '') !== 'desc') throw new Error('sort_dir=desc not reflected');
  if (!assertSortedById(items1, 'desc')) throw new Error('items are not sorted by id desc');
  if (items1.length > reflectedPageSize) throw new Error('items length exceeds page_size');

  const totalPages = Math.max(1, Number(filters1.total_pages || 1));
  const targetPage = Math.min(2, totalPages);
  const req2 = {
    intent: 'my.work.summary',
    params: {
      limit: 80,
      limit_each: 16,
      page: targetPage,
      page_size: 10,
      sort_by: 'id',
      sort_dir: 'asc',
      section: 'all',
      source: 'all',
      reason_code: 'all',
      search: '',
    },
  };
  const resp2 = await requestJson(intentUrl, req2, authHeader);
  writeJson(path.join(outDir, 'my_work_page2_asc.log'), resp2);
  assertIntentEnvelope(resp2, 'my.work.summary');
  const data2 = (resp2.body || {}).data || {};
  const filters2 = data2.filters || {};
  const items2 = Array.isArray(data2.items) ? data2.items : [];
  const sourceModels2 = collectSourceModels(items2);
  if (Number(filters2.page || 0) !== targetPage) throw new Error('target page not reflected');
  const filteredCount2 = Number(filters2.filtered_count || 0);
  if (filteredCount2 > 0) {
    if (String(filters2.sort_dir || '') !== 'asc') throw new Error('sort_dir=asc not reflected');
    if (!assertSortedById(items2, 'asc')) throw new Error('items are not sorted by id asc');
  }
  const reflectedPageSize2 = Number(filters2.page_size || reflectedPageSize || 0);
  if (!Number.isFinite(reflectedPageSize2) || reflectedPageSize2 <= 0) {
    throw new Error('page_size not reflected on page2');
  }
  if (items2.length > reflectedPageSize2) throw new Error('items length exceeds page_size on page2');

  summary.push(`db: ${DB_NAME}`);
  summary.push(`login: ${loginUsed || LOGIN || 'AUTH_TOKEN'}`);
  summary.push(`page_contract_title: ${title}`);
  summary.push(`page_contract_zone_titles: ${zones.map((zone) => String(zone.title || '').trim() || '(blank)').join(',') || '-'}`);
  summary.push(`page1_count: ${items1.length}`);
  summary.push(`page2_count: ${items2.length}`);
  summary.push(`page1_source_models: ${sourceModels1.join(',') || '-'}`);
  summary.push(`page2_source_models: ${sourceModels2.join(',') || '-'}`);
  summary.push(`page_size_reflected: ${reflectedPageSize}`);
  summary.push(`total_pages: ${totalPages}`);
  summary.push(`sort_check_desc: ok`);
  summary.push(`sort_check_asc: ${filteredCount2 > 0 ? 'ok' : 'skip(empty)'}`);
  writeSummary(summary);
  log('PASS my-work pagination/sort smoke');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_my_work_smoke] FAIL: ${err.message}`);
  process.exit(1);
});

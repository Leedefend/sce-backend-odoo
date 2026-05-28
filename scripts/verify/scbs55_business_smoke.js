#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');

const BASE_URL = process.env.BASE_URL || 'http://1.95.85.92:18081';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || process.env.SCBS55_LOGIN || 'caisiqi';
const PASSWORD = process.env.E2E_PASSWORD || process.env.SCBS55_PASSWORD || '123456';
const AUTH_TOKEN = process.env.AUTH_TOKEN || '';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'scbs55-business-smoke', ts);

const DEFAULT_MENUS = [
  ['基础资料', '供应商/合作单位', 652, 706, 'sc.business.entity'],
  ['基础资料', '往来单位', 653, 706, 'sc.business.entity'],
  ['合同', '施工合同', 655, 562, 'construction.contract'],
  ['办公资料', '公司资料存档', 657, 615, 'sc.document.admin.document'],
  ['人事行政', '请假/休假审批单', 659, 642, 'sc.office.admin.document'],
  ['人事行政', '印章使用审批表', 660, 643, 'sc.office.admin.document'],
  ['人事行政', '社保人员登记', 664, 644, 'sc.hr.payroll.document'],
  ['人事行政', '社保登记', 665, 645, 'sc.hr.payroll.document'],
  ['人事行政', '工资登记', 666, 647, 'sc.hr.payroll.document'],
  ['人事行政', '补助', 667, 646, 'sc.hr.payroll.document'],
  ['人事行政', '奖金', 668, 648, 'sc.hr.payroll.document'],
  ['组织人员', '组织机构', 662, 705, 'hr.department'],
  ['组织人员', '公司人员名册（配置）', 663, 720, 'sc.legacy.user.profile'],
  ['证照资料', '证照登记', 670, 649, 'sc.document.admin.document'],
  ['证照资料', '借阅申请', 671, 650, 'sc.document.admin.document'],
  ['投标', '投标报名管理', 673, 565, 'tender.bid'],
  ['投标', '投标报名费申请', 674, 553, 'payment.request'],
  ['资金保证金', '自筹保证金', 676, 750, 'tender.guarantee'],
  ['资金保证金', '自筹保证金退回', 677, 750, 'tender.guarantee'],
  ['资金保证金', '付款还保证金', 678, 750, 'tender.guarantee'],
  ['资金保证金', '付款还保证金退回', 679, 750, 'tender.guarantee'],
  ['资金借还', '借款申请', 681, 775, 'sc.financing.loan'],
  ['资金借还', '还款登记', 682, 631, 'sc.financing.loan'],
  ['费用报销', '报销申请', 684, 764, 'sc.expense.claim'],
  ['收支', '收入', 686, 778, 'sc.receipt.income'],
  ['收支', '公司财务支出', 687, 626, 'sc.expense.claim'],
  ['项目资金', '承包人还项目款', 689, 631, 'sc.financing.loan'],
  ['项目资金', '承包人借项目款', 690, 776, 'sc.financing.loan'],
  ['项目资金', '项目借公司款登记', 704, 777, 'sc.financing.loan'],
  ['项目资金', '项目还公司款登记', 705, 631, 'sc.financing.loan'],
  ['付款', '支付申请', 692, 780, 'payment.request'],
  ['付款', '往来单位付款', 695, 781, 'sc.payment.execution'],
  ['扣款', '扣款单', 694, 761, 'sc.tax.deduction.registration'],
  ['扣款', '扣款实缴登记', 698, 761, 'sc.tax.deduction.registration'],
  ['扣款', '扣款实缴退回', 699, 761, 'sc.tax.deduction.registration'],
  ['资金账户', '账户间资金往来', 697, 782, 'sc.fund.account.operation'],
  ['收款', '到款确认表', 701, 783, 'sc.legacy.fund.confirmation.document'],
  ['资金日报', '资金日报表', 703, 598, 'sc.legacy.fund.daily.line'],
  ['发票税务', '开票申请', 707, 630, 'sc.invoice.registration'],
  ['发票税务', '开票登记', 708, 630, 'sc.invoice.registration'],
  ['发票税务', '预缴税款', 709, 759, 'sc.invoice.registration'],
  ['发票税务', '进项上报', 710, 589, 'sc.legacy.invoice.tax.fact'],
  ['发票税务', '抵扣登记', 711, 761, 'sc.tax.deduction.registration'],
  ['发票税务', '外经证登记', 712, 762, 'sc.legacy.payment.residual.fact'],
  ['成本报表', '供货合同分析', 714, 790, 'sc.legacy.supplier.contract.pricing.fact'],
  ['成本报表', '库存统计表（新）', 715, 686, 'sc.material.stock.summary'],
  ['成本报表', '账户收支统计表', 716, 681, 'sc.account.income.expense.summary'],
  ['成本报表', '成本统计表（综合）', 717, 687, 'sc.comprehensive.cost.summary'],
  ['成本报表', '投标保证金报表', 718, 849, 'sc.tender.guarantee.summary'],
  ['成本报表', '发票成本进度报表', 719, 848, 'sc.invoice.cost.progress.summary'],
  ['成本报表', '发票分析报表', 720, 850, 'sc.invoice.analysis.summary'],
  ['财税报表', '项目经营统计表', 722, 851, 'sc.project.operation.summary'],
  ['财税报表', '应收应付报表', 723, 852, 'sc.ar.ap.report.summary'],
  ['分析大屏', '成本大屏', 725, 788, 'sc.dashboard.cockpit.fact'],
  ['分析大屏', '经营大屏', 726, 789, 'sc.operating.metrics.project'],
].map(([group, label, menuId, actionId, model]) => ({ group, label, menuId, actionId, model }));

function loadMenus() {
  const file = process.env.SCBS55_MENU_MAP_JSON || '';
  if (!file) return DEFAULT_MENUS;
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function writeJson(name, obj) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(obj, null, 2));
}

function requestJson(url, payload, headers = {}) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const body = JSON.stringify(payload);
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

function errorOf(resp) {
  const error = (resp.body || {}).error || {};
  return {
    status: resp.status,
    code: error.code || '',
    message: error.message || '',
    reason_code: error.reason_code || (error.details || {}).reason_code || '',
  };
}

function okEnvelope(resp) {
  return resp.status >= 200 && resp.status < 300 && resp.body && resp.body.ok !== false;
}

async function main() {
  const intentUrl = `${BASE_URL}/api/v1/intent`;
  const menus = loadMenus();

  let token = AUTH_TOKEN;
  if (!token) {
    const loginResp = await requestJson(
      intentUrl,
      { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } },
      { 'X-Anonymous-Intent': '1' },
    );
    if (!okEnvelope(loginResp) || !(loginResp.body.data || {}).token) {
      writeJson('login.json', loginResp);
      throw new Error(`login failed: ${JSON.stringify(errorOf(loginResp))}`);
    }
    token = loginResp.body.data.token;
  }

  const headers = { Authorization: `Bearer ${token}`, 'X-Odoo-DB': DB_NAME };
  const rows = [];
  const failures = [];

  for (const menu of menus) {
    const row = { ...menu, checks: {} };

    const actionResp = await requestJson(intentUrl, {
      intent: 'ui.contract',
      params: {
        op: 'action_open',
        action_id: menu.actionId,
        menu_id: menu.menuId,
        source_mode: 'backend_internal',
      },
    }, headers);
    row.checks.action_contract = okEnvelope(actionResp) ? 'ok' : errorOf(actionResp);
    const head = ((actionResp.body || {}).data || {}).head || {};
    const model = head.model || menu.model;
    const domain = Array.isArray(head.domain) ? head.domain : [];
    const canRead = !!((head.permissions || {}).read);
    row.resolvedModel = model;
    row.readable = canRead;
    if (!okEnvelope(actionResp) || !canRead) {
      failures.push({
        group: menu.group,
        label: menu.label,
        menu_id: menu.menuId,
        action_id: menu.actionId,
        model,
        check: 'action_contract_readable',
        error: okEnvelope(actionResp) ? { message: 'action contract reports read=false', reason_code: (head.access_policy || {}).reason_code || '' } : errorOf(actionResp),
      });
    }

    const listResp = await requestJson(intentUrl, {
      intent: 'api.data',
      params: { op: 'list', model, fields: ['id', 'display_name'], domain, limit: 3 },
    }, headers);
    row.checks.list_data = okEnvelope(listResp) ? 'ok' : errorOf(listResp);
    const records = (((listResp.body || {}).data || {}).records || []).filter(Boolean);
    row.recordCountSample = records.length;
    if (!okEnvelope(listResp)) {
      failures.push({ group: menu.group, label: menu.label, menu_id: menu.menuId, action_id: menu.actionId, model, check: 'list_data', error: errorOf(listResp) });
    }

    const formResp = await requestJson(intentUrl, {
      intent: 'ui.contract',
      params: { op: 'model', model, view_type: 'form', source_mode: 'backend_internal' },
    }, headers);
    row.checks.form_contract = okEnvelope(formResp) ? 'ok' : errorOf(formResp);
    if (!okEnvelope(formResp)) {
      failures.push({ group: menu.group, label: menu.label, menu_id: menu.menuId, action_id: menu.actionId, model, check: 'form_contract', error: errorOf(formResp) });
    }

    if (records.length) {
      const readResp = await requestJson(intentUrl, {
        intent: 'api.data',
        params: { op: 'read', model, ids: [records[0].id], fields: ['id', 'display_name'] },
      }, headers);
      row.sampleRecordId = records[0].id;
      row.checks.record_read = okEnvelope(readResp) ? 'ok' : errorOf(readResp);
      if (!okEnvelope(readResp)) {
        failures.push({ group: menu.group, label: menu.label, menu_id: menu.menuId, action_id: menu.actionId, model, check: 'record_read', error: errorOf(readResp) });
      }
    } else {
      row.checks.record_read = 'empty_list_skipped';
    }

    rows.push(row);
  }

  const byModel = {};
  const byCheck = {};
  for (const failure of failures) {
    byModel[failure.model] = (byModel[failure.model] || 0) + 1;
    byCheck[failure.check] = (byCheck[failure.check] || 0) + 1;
  }
  const summary = {
    pass: failures.length === 0,
    outDir,
    baseUrl: BASE_URL,
    db: DB_NAME,
    login: LOGIN,
    menuCount: menus.length,
    failureCount: failures.length,
    byModel,
    byCheck,
    failures,
  };

  writeJson('rows.json', rows);
  writeJson('summary.json', summary);

  console.log(`[scbs55_business_smoke] ${summary.pass ? 'PASS' : 'FAIL'} menuCount=${menus.length} failureCount=${failures.length}`);
  console.log(`[scbs55_business_smoke] artifacts: ${outDir}`);
  if (!summary.pass) {
    process.exitCode = 1;
  }
}

main().catch((err) => {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, 'error.log'), `${err.stack || err.message}\n`);
  console.error(`[scbs55_business_smoke] FAIL: ${err.message}`);
  process.exit(1);
});

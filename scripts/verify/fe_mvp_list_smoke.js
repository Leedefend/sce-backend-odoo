#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const LOGIN = process.env.E2E_LOGIN || 'admin';
const PASSWORD = process.env.E2E_PASSWORD || process.env.ADMIN_PASSWD || 'admin';
const ROOT_XMLID = process.env.ROOT_XMLID !== undefined
  ? process.env.ROOT_XMLID
  : 'smart_construction_core.menu_sc_root';
const ROOT_MENU_ID = process.env.ROOT_MENU_ID ? Number(process.env.ROOT_MENU_ID) : 0;
const MVP_MENU_ID = process.env.MVP_MENU_ID ? Number(process.env.MVP_MENU_ID) : 0;
const MVP_MENU_XMLID = process.env.MVP_MENU_XMLID || '';
const MVP_MENU_MODEL = process.env.MVP_MENU_MODEL || '';
const SCENE = process.env.SCENE || 'web';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-shell-v0_5', ts);

function log(msg) {
  console.log(`[fe_mvp_list_smoke] ${msg}`);
}

function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2));
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

function unwrap(body) {
  if (body && typeof body === 'object' && 'data' in body) {
    return body.data || {};
  }
  return body || {};
}

function walkMenu(nodes, predicate) {
  for (const node of nodes || []) {
    if (predicate(node)) {
      return node;
    }
    if (node.children && node.children.length) {
      const found = walkMenu(node.children, predicate);
      if (found) {
        return found;
      }
    }
  }
  return null;
}

function findMenuById(nodes, menuId) {
  if (!menuId) return null;
  return walkMenu(nodes, (n) => n.menu_id === menuId);
}

function findMenuByXmlid(nodes, xmlid) {
  if (!xmlid) return null;
  return walkMenu(nodes, (n) => n.meta && n.meta.menu_xmlid === xmlid);
}

function writeSummary({ menuId, actionId, model, viewMode, recordId, navVersion, listStatus, recordStatus, rootXmlidFound, rootMenuId, rootAccessible }) {
  const safe = (value) => (value === undefined || value === null ? '' : value);
  const summary = [
    `menu_id: ${safe(menuId)}`,
    `action_id: ${safe(actionId)}`,
    `model: ${safe(model)}`,
    `view_mode: ${safe(viewMode)}`,
    `record_id: ${safe(recordId)}`,
    `nav_version: ${safe(navVersion)}`,
    `list_status: ${safe(listStatus)}`,
    `record_status: ${safe(recordStatus)}`,
    `root_xmlid_found: ${rootXmlidFound === true ? 'true' : 'false'}`,
    `root_menu_id: ${safe(rootMenuId)}`,
    `root_accessible: ${rootAccessible === true ? 'true' : 'false'}`,
  ].join('\n');
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, 'summary.md'), summary);
}

async function main() {
  if (!DB_NAME) {
    throw new Error('DB_NAME is required (set DB_NAME or E2E_DB)');
  }

  const intentUrl = `${BASE_URL}/api/v1/intent`;

  log(`login: ${LOGIN} db=${DB_NAME}`);
  const loginPayload = { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } };
  const loginResp = await requestJson(intentUrl, loginPayload, { 'X-Anonymous-Intent': '1' });
  if (loginResp.status >= 400 || !loginResp.body.ok) {
    writeJson(path.join(outDir, 'fe_mvp_list.log'), loginResp);
    throw new Error(`login failed: status=${loginResp.status}`);
  }
  const token = (loginResp.body.data || {}).token;
  if (!token) {
    throw new Error('login response missing token');
  }

  const authHeader = {
    Authorization: `Bearer ${token}`,
    'X-Odoo-DB': DB_NAME,
  };

  log('app.init');
  const initParams = { db: DB_NAME, scene: SCENE, with_preload: false };
  if (ROOT_XMLID) {
    initParams.root_xmlid = ROOT_XMLID;
  }
  if (ROOT_MENU_ID) {
    initParams.root_menu_id = ROOT_MENU_ID;
  }
  const initPayload = { intent: 'app.init', params: initParams };
  const initResp = await requestJson(intentUrl, initPayload, authHeader);
  if (initResp.status >= 400 || !initResp.body.ok) {
    writeJson(path.join(outDir, 'fe_mvp_list.log'), initResp);
    writeSummary({
      menuId: '',
      actionId: '',
      model: '',
      viewMode: '',
      recordId: '',
      navVersion: '',
      listStatus: '',
      recordStatus: '',
      rootXmlidFound: false,
      rootMenuId: ROOT_MENU_ID || '',
      rootAccessible: false,
    });
    throw new Error(`app.init failed: status=${initResp.status}`);
  }
  const initData = unwrap(initResp.body);
  const navTree = initData.nav || [];
  const navMeta = initData.nav_meta || {};
  const navVersion = navMeta.menu || (initData.meta || {}).nav_version || (((initData.meta || {}).parts || {}).nav) || '';
  const rootNodeById = findMenuById(navTree, ROOT_MENU_ID);
  const rootNodeByXmlid = findMenuByXmlid(navTree, ROOT_XMLID);
  const rootNode = rootNodeById || rootNodeByXmlid;
  const rootMenuId = ROOT_MENU_ID || (rootNode ? rootNode.menu_id : '') || '';
  const rootXmlidFound = Boolean(rootNodeByXmlid);
  const rootAccessible = Boolean(rootNode);

  const candidates = [];
  if (MVP_MENU_ID) {
    const node = walkMenu(navTree, (n) => n.menu_id === MVP_MENU_ID);
    if (node) candidates.push(node);
  } else if (MVP_MENU_XMLID) {
    const node = walkMenu(navTree, (n) => n.meta && n.meta.menu_xmlid === MVP_MENU_XMLID);
    if (node) candidates.push(node);
  } else if (MVP_MENU_MODEL) {
    const walkAll = (nodes) => {
      (nodes || []).forEach((n) => {
        if (n.meta && n.meta.model === MVP_MENU_MODEL) {
          candidates.push(n);
        }
        if (n.children && n.children.length) walkAll(n.children);
      });
    };
    walkAll(navTree);
  } else {
    throw new Error('MVP menu anchor is required: set MVP_MENU_ID or MVP_MENU_XMLID or MVP_MENU_MODEL');
  }

  if (!candidates.length) {
    writeJson(path.join(outDir, 'fe_mvp_list.log'), {
      error: 'no menu candidates',
      anchor: { MVP_MENU_ID, MVP_MENU_XMLID, MVP_MENU_MODEL },
    });
    throw new Error('menu not found for MVP anchor');
  }
  if (MVP_MENU_MODEL && candidates.length > 1) {
    writeJson(path.join(outDir, 'fe_mvp_list.log'), {
      error: 'multiple menu candidates for model',
      anchor: { MVP_MENU_MODEL },
      candidates: candidates.map((c) => ({ menu_id: c.menu_id, menu_xmlid: c.meta ? c.meta.menu_xmlid : '' })),
    });
    throw new Error('multiple menu candidates for MVP_MENU_MODEL; use MVP_MENU_ID or MVP_MENU_XMLID');
  }

  let menuNode = null;
  let menuId = null;
  let actionId = null;
  let model = '';
  let viewMode = '';
  let columns = [];
  let records = [];
  let listStatus = 'empty';
  let recordStatus = 'empty';
  let recordId = null;
  let recordLog = { status: 'empty' };
  const attempts = [];

  for (const candidate of candidates) {
    try {
      recordId = null;
      recordStatus = 'empty';
      menuId = candidate.menu_id;
      actionId = candidate.meta ? candidate.meta.action_id : undefined;
      if (!actionId) {
        attempts.push({ menu_id: menuId, error: 'menu has no action_id' });
        continue;
      }

      log(`ui.contract action_open action_id=${actionId}`);
      const contractPayload = { intent: 'ui.contract', params: { db: DB_NAME, op: 'action_open', action_id: actionId } };
      const contractResp = await requestJson(intentUrl, contractPayload, authHeader);
      if (contractResp.status >= 400 || !contractResp.body.ok) {
        attempts.push({ menu_id: menuId, error: 'ui.contract failed', status: contractResp.status, body: contractResp.body });
        continue;
      }
      const contract = unwrap(contractResp.body);
      model = contract.model || (candidate.meta ? candidate.meta.model : '') || '';
      viewMode = contract.view_type || ((candidate.meta && candidate.meta.view_modes && candidate.meta.view_modes[0]) || 'tree');
      columns = (contract.ui_contract && contract.ui_contract.columns)
        || (contract.ui_contract && contract.ui_contract.columnsSchema ? contract.ui_contract.columnsSchema.map((c) => c.name).filter(Boolean) : null)
        || Object.keys((contract.ui_contract_raw || {}).fields || {})
        || [];
      const fields = columns.length ? columns : ['id', 'name'];
      if (!model) {
        attempts.push({ menu_id: menuId, error: 'resolved action has no model' });
        continue;
      }

      log(`api.data list model=${model}`);
      const listPayload = {
        intent: 'api.data',
        params: {
          op: 'list',
          model,
          fields,
          domain: (candidate.meta && candidate.meta.domain) || [],
          context: (candidate.meta && candidate.meta.context) || {},
          limit: 5,
          offset: 0,
          order: '',
        },
      };
      const listResp = await requestJson(intentUrl, listPayload, authHeader);
      if (listResp.status >= 400 || !listResp.body.ok) {
        attempts.push({ menu_id: menuId, error: 'api.data list failed', status: listResp.status, body: listResp.body });
        continue;
      }
      const listData = unwrap(listResp.body);
      records = listData.records || [];
      listStatus = records.length ? 'ok' : 'empty';

      if (!records.length) {
        menuNode = candidate;
        recordStatus = 'empty';
        recordLog = { status: 'empty' };
        break;
      }

      recordId = records[0].id;
      log(`load_view + api.data read model=${model} id=${recordId}`);
      const viewPayload = { intent: 'load_view', params: { model, view_type: 'form' } };
      const viewResp = await requestJson(intentUrl, viewPayload, authHeader);
      if (viewResp.status >= 400 || !viewResp.body.ok) {
        attempts.push({ menu_id: menuId, error: 'load_view failed', status: viewResp.status, body: viewResp.body });
        continue;
      }
      const viewData = unwrap(viewResp.body);
      const fieldNames = [];
      ((viewData.layout || {}).groups || []).forEach((g) => {
        (g.fields || []).forEach((f) => {
          if (f && f.name) fieldNames.push(f.name);
        });
        (g.sub_groups || []).forEach((sg) => {
          (sg.fields || []).forEach((f) => {
            if (f && f.name) fieldNames.push(f.name);
          });
        });
      });
      ((viewData.layout || {}).notebooks || []).forEach((nb) => {
        (nb.pages || []).forEach((page) => {
          (page.groups || []).forEach((g) => {
            (g.fields || []).forEach((f) => {
              if (f && f.name) fieldNames.push(f.name);
            });
          });
        });
      });
      if ((viewData.layout && viewData.layout.titleField)) {
        fieldNames.push(viewData.layout.titleField);
      }
      const uniqueFields = Array.from(new Set(fieldNames)).filter(Boolean);
      const readPayload = {
        intent: 'api.data',
        params: {
          op: 'read',
          model,
          ids: [recordId],
          fields: uniqueFields.length ? uniqueFields : ['id', 'name'],
          context: (candidate.meta && candidate.meta.context) || {},
        },
      };
      const readResp = await requestJson(intentUrl, readPayload, authHeader);
      if (readResp.status >= 400 || !readResp.body.ok) {
        attempts.push({ menu_id: menuId, error: 'api.data read failed', status: readResp.status, body: readResp.body });
        continue;
      }
      const readData = unwrap(readResp.body);
      const rec = (readData.records || [])[0] || {};
      recordStatus = Object.keys(rec).length ? 'ok' : 'empty';
      recordLog = {
        status: recordStatus,
        record_id: recordId,
        fields_count: Object.keys(rec).length,
        title_field: (viewData.layout && viewData.layout.titleField) || '',
      };
      menuNode = candidate;
      break;
    } catch (err) {
      attempts.push({ menu_id: candidate.menu_id, error: err.message || 'unknown error' });
    }
  }

  if (!menuNode) {
    writeJson(path.join(outDir, 'fe_mvp_list.log'), { error: 'no viable menu candidate', attempts });
    throw new Error('no viable menu candidate');
  }

  const listLog = {
    menu_id: menuId,
    menu_xmlid: menuNode.meta && menuNode.meta.menu_xmlid || '',
    action_id: actionId,
    model,
    view_mode: viewMode,
    nav_version: navVersion,
    list_status: listStatus,
    list_empty_reason: listStatus === 'empty' ? 'business_empty' : '',
    columns_count: columns.length,
    record_count: records.length,
    root_xmlid: ROOT_XMLID || '',
    root_menu_id: rootMenuId,
    root_xmlid_found: rootXmlidFound,
    root_accessible: rootAccessible,
    attempts,
  };
  writeJson(path.join(outDir, 'fe_mvp_list.log'), listLog);

  writeJson(path.join(outDir, 'fe_mvp_record.log'), recordLog);

  writeSummary({
    menuId,
    actionId,
    model,
    viewMode,
    recordId: recordId || '',
    navVersion,
    listStatus,
    recordStatus,
    rootXmlidFound,
    rootMenuId,
    rootAccessible,
  });

  log(`PASS list_status=${listStatus} record_status=${recordStatus}`);
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`FAIL: ${err.message}`);
  process.exit(1);
});

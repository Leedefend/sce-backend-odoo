#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const { assertIntentEnvelope } = require('./intent_smoke_utils');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const LOGIN = process.env.E2E_LOGIN || 'admin';
const PASSWORD = process.env.E2E_PASSWORD || process.env.ADMIN_PASSWD || 'admin';
const AUTH_TOKEN = process.env.AUTH_TOKEN || '';
const BOOTSTRAP_SECRET = process.env.BOOTSTRAP_SECRET || '';
const BOOTSTRAP_LOGIN = process.env.BOOTSTRAP_LOGIN || '';
const MODEL = process.env.MVP_MODEL || 'project.project';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const REQUIRE_GROUPED_ROWS = process.env.REQUIRE_GROUPED_ROWS === '1';
const TREE_GROUPED_SNAPSHOT_UPDATE = process.env.TREE_GROUPED_SNAPSHOT_UPDATE === '1';
const TREE_GROUPED_BASELINE = process.env.TREE_GROUPED_BASELINE
  || path.join(__dirname, 'baselines', 'fe_tree_grouped_signature.json');

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-shell-v0_8-6', ts);

function log(msg) {
  console.log(`[fe_tree_view_smoke] ${msg}`);
}

function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2));
}

function writeSummary(lines) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, 'summary.md'), lines.join('\n'));
}

function stable(obj) {
  if (Array.isArray(obj)) return obj.map(stable);
  if (!obj || typeof obj !== 'object') return obj;
  const out = {};
  for (const key of Object.keys(obj).sort()) out[key] = stable(obj[key]);
  return out;
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

function pickColumns(contract) {
  const views = contract && typeof contract === 'object' ? contract.views : null;
  if (views && typeof views === 'object') {
    const tree = views.tree || views.list;
    if (tree && Array.isArray(tree.columns) && tree.columns.length) {
      return tree.columns;
    }
  }
  return [];
}

function pickGroupByField(contract) {
  const search = contract && typeof contract === 'object' ? contract.search : null;
  const rows = search && typeof search === 'object' && Array.isArray(search.group_by) ? search.group_by : [];
  for (const row of rows) {
    if (typeof row === 'string' && row.trim()) return row.trim();
    if (row && typeof row === 'object') {
      const field = String(row.field || '').trim();
      if (field) return field;
    }
  }
  return 'create_uid';
}

function unwrapIntentData(body) {
  const rootData = body && typeof body === 'object' ? body.data : null;
  if (rootData && typeof rootData === 'object' && rootData.data && typeof rootData.data === 'object') {
    return rootData.data;
  }
  if (rootData && typeof rootData === 'object') return rootData;
  return {};
}

function toSafeInt(value, fallback = 0) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.trunc(parsed);
}

function buildGroupedPaginationSemanticSummary(groupedRows, requestPageLimit, requestOffset) {
  const pageLimit = Math.max(1, toSafeInt(requestPageLimit, 3));
  const requestedOffset = Math.max(0, toSafeInt(requestOffset, 0));
  const normalizedRequestOffset = Math.floor(requestedOffset / pageLimit) * pageLimit;
  const firstGroup = Array.isArray(groupedRows) && groupedRows.length > 0 && groupedRows[0] && typeof groupedRows[0] === 'object'
    ? groupedRows[0]
    : null;
  const count = firstGroup ? Math.max(0, toSafeInt(firstGroup.count, 0)) : 0;
  const sampleRows = firstGroup && Array.isArray(firstGroup.sample_rows) ? firstGroup.sample_rows : [];
  const pageWindow = firstGroup && firstGroup.page_window && typeof firstGroup.page_window === 'object'
    ? firstGroup.page_window
    : null;
  const groupOffsetRaw = firstGroup ? Math.max(0, toSafeInt(firstGroup.page_offset, normalizedRequestOffset)) : normalizedRequestOffset;
  const pageOffset = Math.floor(groupOffsetRaw / pageLimit) * pageLimit;
  const totalPages = Math.max(1, Math.ceil(count / pageLimit));
  const currentPage = Math.floor(pageOffset / pageLimit) + 1;
  const rangeStart = count > 0 ? pageOffset + 1 : 0;
  const rangeEnd = count > 0 ? Math.min(count, pageOffset + pageLimit) : 0;
  const offsetAlignedToPageLimit = pageOffset % pageLimit === 0;
  const requestOffsetMatchesObserved = !firstGroup || normalizedRequestOffset === pageOffset;
  const pageWindowStart = pageWindow ? Math.max(0, toSafeInt(pageWindow.start, rangeStart)) : rangeStart;
  const pageWindowEnd = pageWindow ? Math.max(0, toSafeInt(pageWindow.end, rangeEnd)) : rangeEnd;
  const pageWindowMatchesRange = !firstGroup || (pageWindowStart === rangeStart && pageWindowEnd === rangeEnd);
  return {
    formulas: {
      page_offset_normalize: 'floor(offset / page_limit) * page_limit',
      current_page: 'floor(page_offset / page_limit) + 1',
      total_pages: 'max(1, ceil(count / page_limit))',
      page_range: 'start=page_offset+1,end=min(count,page_offset+page_limit)',
    },
    field_types: {
      page_limit: 'number',
      page_offset: 'number',
      current_page: 'number',
      total_pages: 'number',
      range_start: 'number',
      range_end: 'number',
      offset_aligned_to_page_limit: 'boolean',
      request_offset_matches_observed: 'boolean',
    },
    request: {
      page_limit: pageLimit,
      request_offset: requestedOffset,
      normalized_request_offset: normalizedRequestOffset,
    },
    first_group_observation: {
      present: Boolean(firstGroup),
      count,
      sample_rows_count: sampleRows.length,
      page_limit: pageLimit,
      page_offset: pageOffset,
      current_page: currentPage,
      total_pages: totalPages,
      range_start: rangeStart,
      range_end: rangeEnd,
      page_window_start: pageWindowStart,
      page_window_end: pageWindowEnd,
      page_window_matches_range: pageWindowMatchesRange,
      offset_aligned_to_page_limit: offsetAlignedToPageLimit,
    },
    consistency: {
      request_offset_matches_observed: requestOffsetMatchesObserved,
      request_offset_aligned_to_page_limit: normalizedRequestOffset % pageLimit === 0,
      first_group_offset_aligned_to_page_limit: offsetAlignedToPageLimit,
      first_group_page_window_matches_range: pageWindowMatchesRange,
    },
  };
}

function buildGroupedOffsetReplaySummary(groupPaging, requestGroupOffset) {
  const requestOffset = Math.max(0, toSafeInt(requestGroupOffset, 0));
  const paging = groupPaging && typeof groupPaging === 'object' ? groupPaging : {};
  const observedOffset = Math.max(0, toSafeInt(paging.group_offset, 0));
  const nextOffsetRaw = paging.next_group_offset;
  const prevOffsetRaw = paging.prev_group_offset;
  const nextOffset = Number.isFinite(Number(nextOffsetRaw)) ? Math.max(0, toSafeInt(nextOffsetRaw, 0)) : null;
  const prevOffset = Number.isFinite(Number(prevOffsetRaw)) ? Math.max(0, toSafeInt(prevOffsetRaw, 0)) : null;
  return {
    formulas: {
      offset_roundtrip: 'response.group_paging.group_offset == request.group_offset',
      prev_when_offset_positive: 'request.group_offset>0 -> prev_group_offset is number|null',
      next_signal_type: 'next_group_offset is number|null',
    },
    request: {
      group_offset: requestOffset,
    },
    response: {
      group_offset: observedOffset,
      next_group_offset: nextOffset,
      prev_group_offset: prevOffset,
      has_more: Boolean(paging.has_more),
      group_count: Math.max(0, toSafeInt(paging.group_count, 0)),
    },
    consistency: {
      offset_roundtrip_match: requestOffset === observedOffset,
      prev_signal_typed: requestOffset <= 0 ? prevOffset === null : (prevOffset === null || Number.isInteger(prevOffset)),
      next_signal_typed: nextOffset === null || Number.isInteger(nextOffset),
    },
  };
}

function buildGroupedIdentitySummary(groupPaging) {
  const paging = groupPaging && typeof groupPaging === 'object' ? groupPaging : {};
  const identity = paging.window_identity && typeof paging.window_identity === 'object' ? paging.window_identity : {};
  const identityModel = typeof identity.model === 'string' ? identity.model.trim() : '';
  const identityGroupByField = typeof identity.group_by_field === 'string' ? identity.group_by_field.trim() : '';
  const identityWindowEmpty = typeof identity.window_empty === 'boolean' ? identity.window_empty : null;
  const windowId = typeof identity.window_id === 'string'
    ? identity.window_id.trim()
    : (typeof paging.window_id === 'string' ? paging.window_id.trim() : '');
  const queryFingerprint = typeof identity.query_fingerprint === 'string'
    ? identity.query_fingerprint.trim()
    : (typeof paging.query_fingerprint === 'string' ? paging.query_fingerprint.trim() : '');
  const windowDigest = typeof identity.window_digest === 'string'
    ? identity.window_digest.trim()
    : (typeof paging.window_digest === 'string' ? paging.window_digest.trim() : '');
  const identityVersion = typeof identity.version === 'string' ? identity.version.trim() : '';
  const identityAlgo = typeof identity.algo === 'string' ? identity.algo.trim().toLowerCase() : '';
  const identityKey = typeof identity.key === 'string' ? identity.key.trim() : '';
  const identityGroupOffset = Number.isFinite(Number(identity.group_offset)) ? Math.max(0, toSafeInt(identity.group_offset, 0)) : null;
  const identityGroupLimit = Number.isFinite(Number(identity.group_limit)) ? Math.max(0, toSafeInt(identity.group_limit, 0)) : null;
  const identityGroupCount = Number.isFinite(Number(identity.group_count)) ? Math.max(0, toSafeInt(identity.group_count, 0)) : null;
  const identityGroupTotal = Number.isFinite(Number(identity.group_total)) ? Math.max(0, toSafeInt(identity.group_total, 0)) : null;
  const identityPageSize = Number.isFinite(Number(identity.page_size)) ? Math.max(1, toSafeInt(identity.page_size, 1)) : null;
  const identityHasGroupPageOffsets = typeof identity.has_group_page_offsets === 'boolean' ? identity.has_group_page_offsets : null;
  const identityWindowStart = Number.isFinite(Number(identity.window_start)) ? Math.max(0, toSafeInt(identity.window_start, 0)) : null;
  const identityWindowEnd = Number.isFinite(Number(identity.window_end)) ? Math.max(0, toSafeInt(identity.window_end, 0)) : null;
  const identityWindowSpan = Number.isFinite(Number(identity.window_span)) ? Math.max(0, toSafeInt(identity.window_span, 0)) : null;
  const identityPrevOffset = Number.isFinite(Number(identity.prev_group_offset)) ? Math.max(0, toSafeInt(identity.prev_group_offset, 0)) : null;
  const identityNextOffset = Number.isFinite(Number(identity.next_group_offset)) ? Math.max(0, toSafeInt(identity.next_group_offset, 0)) : null;
  const identityHasMore = typeof identity.has_more === 'boolean' ? identity.has_more : null;
  const flatWindowKey = typeof paging.window_key === 'string' ? paging.window_key.trim() : '';
  const flatWindowId = typeof paging.window_id === 'string' ? paging.window_id.trim() : '';
  const flatQueryFingerprint = typeof paging.query_fingerprint === 'string' ? paging.query_fingerprint.trim() : '';
  const flatWindowDigest = typeof paging.window_digest === 'string' ? paging.window_digest.trim() : '';
  return {
    formulas: {
      window_id_shape: 'window_id must be non-empty string for grouped responses',
      query_fingerprint_shape: 'query_fingerprint must be non-empty hex string',
      window_digest_shape: 'window_digest must be non-empty hex string',
      window_identity_object: 'window_identity object should be present and match flat fields when both exist',
      window_identity_meta: 'window_identity.version/algo must be non-empty, algo currently sha1',
      window_identity_key: 'window_identity.key must be non-empty and match version/algo/window_id/window_digest tuple',
      window_key_flat_compat: 'window_key flat field should match window_identity.key when both exist',
      window_identity_window_shape: 'window_identity.group_offset/group_limit/group_count should be non-negative integers and align with group_paging',
      window_identity_total_shape: 'window_identity.group_total should be non-negative integer when present and align with group_paging.group_total',
      window_identity_page_shape: 'window_identity.page_size/has_group_page_offsets should align with group_paging',
      window_identity_range_shape: 'window_identity.window_start/window_end should be non-negative integers and align with group_paging',
      window_identity_nav_shape: 'window_identity prev/next/has_more should align with group_paging',
      window_identity_group_by_shape: 'window_identity.group_by_field should align with group_paging.group_by_field',
      window_identity_model_shape: 'window_identity.model should align with request model',
      window_identity_empty_shape: 'window_identity.window_empty should align with group_count/window range',
      window_identity_span_shape: 'window_identity.window_span should align with window_start/window_end/group_count',
    },
    response: {
      window_id: windowId,
      query_fingerprint: queryFingerprint,
      window_digest: windowDigest,
      window_identity_present: Boolean(paging.window_identity && typeof paging.window_identity === 'object'),
      window_identity_model: identityModel,
      window_identity_group_by_field: identityGroupByField,
      window_identity_window_empty: identityWindowEmpty === null ? false : identityWindowEmpty,
      window_identity_version: identityVersion,
      window_identity_algo: identityAlgo,
      window_identity_key: identityKey || flatWindowKey,
      window_key: flatWindowKey,
      window_identity_group_offset: identityGroupOffset === null ? -1 : identityGroupOffset,
      window_identity_group_limit: identityGroupLimit === null ? -1 : identityGroupLimit,
      window_identity_group_count: identityGroupCount === null ? -1 : identityGroupCount,
      window_identity_group_total: identityGroupTotal === null ? -1 : identityGroupTotal,
      window_identity_page_size: identityPageSize === null ? -1 : identityPageSize,
      window_identity_has_group_page_offsets: identityHasGroupPageOffsets === null ? false : identityHasGroupPageOffsets,
      window_identity_window_start: identityWindowStart === null ? -1 : identityWindowStart,
      window_identity_window_end: identityWindowEnd === null ? -1 : identityWindowEnd,
      window_identity_window_span: identityWindowSpan === null ? -1 : identityWindowSpan,
      window_identity_prev_group_offset: identityPrevOffset === null ? -1 : identityPrevOffset,
      window_identity_next_group_offset: identityNextOffset === null ? -1 : identityNextOffset,
      window_identity_has_more: identityHasMore === null ? false : identityHasMore,
    },
    consistency: {
      has_window_id: windowId.length > 0,
      has_query_fingerprint: queryFingerprint.length > 0,
      query_fingerprint_hex: /^[a-f0-9]{40}$/i.test(queryFingerprint),
      has_window_digest: windowDigest.length > 0,
      window_digest_hex: /^[a-f0-9]{40}$/i.test(windowDigest),
      identity_object_present: Boolean(paging.window_identity && typeof paging.window_identity === 'object'),
      identity_object_matches_flat: (
        !flatWindowId || flatWindowId === windowId
      ) && (
        !flatQueryFingerprint || flatQueryFingerprint === queryFingerprint
      ) && (
        !flatWindowDigest || flatWindowDigest === windowDigest
      ),
      identity_version_present: identityVersion.length > 0,
      identity_algo_present: identityAlgo.length > 0,
      identity_algo_supported: identityAlgo === 'sha1',
      identity_key_present: (identityKey || flatWindowKey).length > 0,
      identity_key_matches_tuple: (identityKey || flatWindowKey).length > 0
        && (identityKey || flatWindowKey) === `${identityVersion || 'v1'}:${identityAlgo || 'sha1'}:${windowId || '-'}:${windowDigest || '-'}`,
      identity_key_matches_flat: !flatWindowKey || !identityKey || flatWindowKey === identityKey,
      identity_window_numbers_present: identityGroupOffset !== null && identityGroupLimit !== null && identityGroupCount !== null,
      identity_window_numbers_match_flat: (
        identityGroupOffset === null || identityGroupOffset === Math.max(0, toSafeInt(paging.group_offset, 0))
      ) && (
        identityGroupLimit === null || identityGroupLimit === Math.max(0, toSafeInt(paging.group_limit, 0))
      ) && (
        identityGroupCount === null || identityGroupCount === Math.max(0, toSafeInt(paging.group_count, 0))
      ),
      identity_total_optional_typed: identityGroupTotal === null || Number.isInteger(identityGroupTotal),
      identity_total_match_flat: (
        identityGroupTotal === null
        || identityGroupTotal === (Number.isFinite(Number(paging.group_total)) ? Math.max(0, toSafeInt(paging.group_total, 0)) : null)
      ),
      identity_group_by_match_flat: (
        !identityGroupByField
        || identityGroupByField === String(paging.group_by_field || '').trim()
      ),
      identity_model_match_request: !identityModel || identityModel === String(MODEL || '').trim(),
      identity_window_empty_typed: identityWindowEmpty !== null,
      identity_window_empty_match_flat: (
        identityWindowEmpty === null
        || identityWindowEmpty === (Math.max(0, toSafeInt(paging.group_count, 0)) <= 0)
      ),
      identity_page_meta_present: identityPageSize !== null && identityHasGroupPageOffsets !== null,
      identity_page_meta_match_flat: (
        identityPageSize === null || identityPageSize === Math.max(1, toSafeInt(paging.page_size, 1))
      ) && (
        identityHasGroupPageOffsets === null || identityHasGroupPageOffsets === Boolean(paging.has_group_page_offsets)
      ),
      identity_range_numbers_present: identityWindowStart !== null && identityWindowEnd !== null,
      identity_range_numbers_match_flat: (
        identityWindowStart === null || identityWindowStart === Math.max(0, toSafeInt(paging.window_start, 0))
      ) && (
        identityWindowEnd === null || identityWindowEnd === Math.max(0, toSafeInt(paging.window_end, 0))
      ),
      identity_span_present: identityWindowSpan !== null,
      identity_span_match_flat: (
        identityWindowSpan === null
        || identityWindowSpan === Math.max(0, (
          (Number.isFinite(Number(paging.window_end)) ? Math.max(0, toSafeInt(paging.window_end, 0)) : 0)
          - (Number.isFinite(Number(paging.window_start)) ? Math.max(0, toSafeInt(paging.window_start, 0)) : 0)
          + ((Math.max(0, toSafeInt(paging.group_count, 0)) > 0) ? 1 : 0)
        ))
      ),
      identity_nav_present: identityHasMore !== null,
      identity_nav_match_flat: (
        identityPrevOffset === null || identityPrevOffset === (Number.isFinite(Number(paging.prev_group_offset)) ? Math.max(0, toSafeInt(paging.prev_group_offset, 0)) : null)
      ) && (
        identityNextOffset === null || identityNextOffset === (Number.isFinite(Number(paging.next_group_offset)) ? Math.max(0, toSafeInt(paging.next_group_offset, 0)) : null)
      ) && (
        identityHasMore === null || identityHasMore === Boolean(paging.has_more)
      ),
    },
  };
}

async function main() {
  if (!DB_NAME) {
    throw new Error('DB_NAME is required (set DB_NAME or E2E_DB)');
  }

  const intentUrl = `${BASE_URL}/api/v1/intent`;
  const summary = [];

  let token = AUTH_TOKEN;
  if (!token && BOOTSTRAP_SECRET) {
    log('bootstrap: session.bootstrap');
    const bootstrapPayload = { intent: 'bootstrap', params: { db: DB_NAME, login: BOOTSTRAP_LOGIN } };
    const bootstrapResp = await requestJson(intentUrl, bootstrapPayload, {
      'X-Bootstrap-Secret': BOOTSTRAP_SECRET,
      'X-Anonymous-Intent': '1',
    });
    try {
      assertIntentEnvelope(bootstrapResp, 'bootstrap', { allowMetaIntentAliases: ['session.bootstrap'] });
    } catch (_err) {
      writeJson(path.join(outDir, 'bootstrap.log'), bootstrapResp);
      throw new Error(`bootstrap failed: status=${bootstrapResp.status || 0}`);
    }
    token = (bootstrapResp.body.data || {}).token || '';
  }
  if (!token) {
    log(`login: ${LOGIN} db=${DB_NAME}`);
    const loginPayload = { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } };
    const loginResp = await requestJson(intentUrl, loginPayload, { 'X-Anonymous-Intent': '1' });
    try {
      assertIntentEnvelope(loginResp, 'login');
    } catch (_err) {
      writeJson(path.join(outDir, 'login.log'), loginResp);
      throw new Error(`login failed: status=${loginResp.status || 0}`);
    }
    token = (loginResp.body.data || {}).token || '';
    if (!token) {
      throw new Error('login response missing token');
    }
  }

  const authHeader = {
    Authorization: `Bearer ${token}`,
    'X-Odoo-DB': DB_NAME,
  };

  log('ui.contract (tree view)');
  const contractPayload = { intent: 'ui.contract', params: { op: 'model', model: MODEL, view_type: 'tree' } };
  const contractResp = await requestJson(intentUrl, contractPayload, authHeader);
  writeJson(path.join(outDir, 'contract.log'), contractResp);
  assertIntentEnvelope(contractResp, 'ui.contract');

  const contract = unwrapIntentData(contractResp.body);
  const columns = pickColumns(contract);
  summary.push(`columns_count: ${columns.length}`);
  if (!columns.length) {
    writeSummary(summary);
    throw new Error('tree columns missing');
  }

  log('api.data.list (tree columns)');
  const listPayload = {
    intent: 'api.data',
    params: { op: 'list', model: MODEL, fields: columns, limit: 5 },
  };
  const listResp = await requestJson(intentUrl, listPayload, authHeader);
  writeJson(path.join(outDir, 'list.log'), listResp);
  assertIntentEnvelope(listResp, 'api.data');
  const listData = unwrapIntentData(listResp.body);
  const records = Array.isArray(listData.records) ? listData.records : [];
  if (!records.length) {
    throw new Error('list returned no records');
  }
  const first = records[0] || {};
  const missing = columns.filter((col) => !Object.prototype.hasOwnProperty.call(first, col));
  summary.push(`missing_columns: ${missing.length}`);
  if (missing.length) {
    summary.push(`missing_columns_list: ${missing.join(', ')}`);
    writeSummary(summary);
    throw new Error('record missing tree columns');
  }

  log('api.data.list (grouped rows)');
  const groupByField = pickGroupByField(contract);
  const groupedPayload = {
    intent: 'api.data',
    params: {
      op: 'list',
      model: MODEL,
      fields: columns,
      group_by: groupByField,
      group_offset: 0,
      group_page_offsets: {},
      group_sample_limit: 3,
      limit: 12,
      offset: 0,
    },
  };
  const groupedResp = await requestJson(intentUrl, groupedPayload, authHeader);
  writeJson(path.join(outDir, 'grouped.log'), groupedResp);
  assertIntentEnvelope(groupedResp, 'api.data');
  const groupedData = unwrapIntentData(groupedResp.body);
  const groupedRows = Array.isArray(groupedData.grouped_rows) ? groupedData.grouped_rows : [];
  const groupSummary = Array.isArray(groupedData.group_summary) ? groupedData.group_summary : [];
  const firstGroupedRow = groupedRows.length && groupedRows[0] && typeof groupedRows[0] === 'object' ? groupedRows[0] : null;
  const groupedHasGroupKey = firstGroupedRow ? typeof firstGroupedRow.group_key === 'string' && firstGroupedRow.group_key.length > 0 : true;
  const groupedHasPageFlags = firstGroupedRow
    ? typeof firstGroupedRow.page_has_prev === 'boolean' && typeof firstGroupedRow.page_has_next === 'boolean'
    : true;
  const groupedHasPageWindow = firstGroupedRow
    ? typeof firstGroupedRow.page_window === 'object' && firstGroupedRow.page_window !== null
      && Number.isFinite(Number(firstGroupedRow.page_window.start))
      && Number.isFinite(Number(firstGroupedRow.page_window.end))
    : true;
  const groupedPaginationSemanticSummary = buildGroupedPaginationSemanticSummary(
    groupedRows,
    groupedPayload.params.group_sample_limit,
    groupedPayload.params.offset,
  );
  const groupedOffsetPayload = {
    intent: 'api.data',
    params: {
      op: 'list',
      model: MODEL,
      fields: columns,
      group_by: groupByField,
      group_offset: 5,
      group_page_offsets: {},
      group_sample_limit: 3,
      limit: 12,
      offset: 0,
    },
  };
  const groupedOffsetResp = await requestJson(intentUrl, groupedOffsetPayload, authHeader);
  writeJson(path.join(outDir, 'grouped_offset.log'), groupedOffsetResp);
  assertIntentEnvelope(groupedOffsetResp, 'api.data');
  const groupedOffsetData = unwrapIntentData(groupedOffsetResp.body);
  const groupedOffsetPaging =
    groupedOffsetData && typeof groupedOffsetData.group_paging === 'object'
      ? groupedOffsetData.group_paging
      : {};
  const groupedOffsetReplaySummary = buildGroupedOffsetReplaySummary(
    groupedOffsetPaging,
    groupedOffsetPayload.params.group_offset,
  );
  const groupedIdentitySummary = buildGroupedIdentitySummary(groupedOffsetPaging);
  const groupedIdentityBaselineSummary = stable({
    ...groupedIdentitySummary,
    response: {
      ...groupedIdentitySummary.response,
      query_fingerprint: groupedIdentitySummary.response.query_fingerprint ? '__hex40__' : '',
      window_digest: groupedIdentitySummary.response.window_digest ? '__hex40__' : '',
      window_id: groupedIdentitySummary.response.window_id ? '__window_id__' : '',
      window_identity_key: groupedIdentitySummary.response.window_identity_key ? '__identity_key__' : '',
      window_key: groupedIdentitySummary.response.window_key ? '__identity_key__' : '',
    },
  });
  summary.push(`group_by_field: ${groupByField}`);
  summary.push(`group_summary_count: ${groupSummary.length}`);
  summary.push(`grouped_rows_count: ${groupedRows.length}`);
  const hasGroupedPayload = Array.isArray(groupedData.group_summary) && Array.isArray(groupedData.grouped_rows);
  summary.push(`grouped_payload_present: ${hasGroupedPayload ? 'yes' : 'no'}`);
  summary.push(`grouped_group_key_present: ${groupedHasGroupKey ? 'yes' : 'no'}`);
  summary.push(`grouped_page_flags_present: ${groupedHasPageFlags ? 'yes' : 'no'}`);
  summary.push(`grouped_page_window_present: ${groupedHasPageWindow ? 'yes' : 'no'}`);
  summary.push(`grouped_pagination_normalized_offset: ${groupedPaginationSemanticSummary.request.normalized_request_offset}`);
  summary.push(`grouped_pagination_first_group_present: ${groupedPaginationSemanticSummary.first_group_observation.present ? 'yes' : 'no'}`);
  summary.push(`grouped_pagination_first_group_page: ${groupedPaginationSemanticSummary.first_group_observation.current_page}/${groupedPaginationSemanticSummary.first_group_observation.total_pages}`);
  summary.push(`grouped_offset_roundtrip_match: ${groupedOffsetReplaySummary.consistency.offset_roundtrip_match ? 'yes' : 'no'}`);
  summary.push(`grouped_offset_prev_signal_typed: ${groupedOffsetReplaySummary.consistency.prev_signal_typed ? 'yes' : 'no'}`);
  summary.push(`grouped_offset_next_signal_typed: ${groupedOffsetReplaySummary.consistency.next_signal_typed ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_has_window_id: ${groupedIdentitySummary.consistency.has_window_id ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_has_query_fingerprint: ${groupedIdentitySummary.consistency.has_query_fingerprint ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_query_fingerprint_hex: ${groupedIdentitySummary.consistency.query_fingerprint_hex ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_has_window_digest: ${groupedIdentitySummary.consistency.has_window_digest ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_window_digest_hex: ${groupedIdentitySummary.consistency.window_digest_hex ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_object_present: ${groupedIdentitySummary.consistency.identity_object_present ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_object_matches_flat: ${groupedIdentitySummary.consistency.identity_object_matches_flat ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_version_present: ${groupedIdentitySummary.consistency.identity_version_present ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_algo_supported: ${groupedIdentitySummary.consistency.identity_algo_supported ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_key_present: ${groupedIdentitySummary.consistency.identity_key_present ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_key_matches_tuple: ${groupedIdentitySummary.consistency.identity_key_matches_tuple ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_key_matches_flat: ${groupedIdentitySummary.consistency.identity_key_matches_flat ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_window_numbers_present: ${groupedIdentitySummary.consistency.identity_window_numbers_present ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_window_numbers_match_flat: ${groupedIdentitySummary.consistency.identity_window_numbers_match_flat ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_total_match_flat: ${groupedIdentitySummary.consistency.identity_total_match_flat ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_model_match_request: ${groupedIdentitySummary.consistency.identity_model_match_request ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_window_empty_match_flat: ${groupedIdentitySummary.consistency.identity_window_empty_match_flat ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_group_by_match_flat: ${groupedIdentitySummary.consistency.identity_group_by_match_flat ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_page_meta_match_flat: ${groupedIdentitySummary.consistency.identity_page_meta_match_flat ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_range_numbers_present: ${groupedIdentitySummary.consistency.identity_range_numbers_present ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_range_numbers_match_flat: ${groupedIdentitySummary.consistency.identity_range_numbers_match_flat ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_span_match_flat: ${groupedIdentitySummary.consistency.identity_span_match_flat ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_nav_present: ${groupedIdentitySummary.consistency.identity_nav_present ? 'yes' : 'no'}`);
  summary.push(`grouped_identity_nav_match_flat: ${groupedIdentitySummary.consistency.identity_nav_match_flat ? 'yes' : 'no'}`);
  if (!hasGroupedPayload && REQUIRE_GROUPED_ROWS) {
    writeSummary(summary);
    throw new Error('grouped response missing group_summary/grouped_rows (REQUIRE_GROUPED_ROWS=1)');
  }

  const groupedSignature = stable({
    version: 'v0_5_mini',
    model: MODEL,
    group_by_field: groupByField,
    grouped_payload_present: hasGroupedPayload,
    grouped_response_keys: Object.keys(groupedData || {}).sort(),
    grouped_request_keys: Object.keys(groupedPayload.params || {}).sort(),
    grouped_pagination_route_state: {
      key: 'group_page',
      mode: 'per-group offset map',
    },
    grouped_contract_fields: {
      group_key: groupedHasGroupKey,
      page_has_prev: groupedHasPageFlags,
      page_has_next: groupedHasPageFlags,
      page_window: groupedHasPageWindow,
    },
    grouped_pagination_semantic_summary: groupedPaginationSemanticSummary,
    grouped_offset_replay_summary: groupedOffsetReplaySummary,
    grouped_identity_summary: groupedIdentityBaselineSummary,
  });
  writeJson(path.join(outDir, 'grouped_signature.current.json'), groupedSignature);
  if (TREE_GROUPED_SNAPSHOT_UPDATE) {
    fs.mkdirSync(path.dirname(TREE_GROUPED_BASELINE), { recursive: true });
    fs.writeFileSync(TREE_GROUPED_BASELINE, JSON.stringify(groupedSignature, null, 2));
    summary.push(`grouped_signature_updated: ${TREE_GROUPED_BASELINE}`);
  } else {
    if (!fs.existsSync(TREE_GROUPED_BASELINE)) {
      writeSummary(summary);
      throw new Error(`grouped signature baseline missing: ${TREE_GROUPED_BASELINE} (run with TREE_GROUPED_SNAPSHOT_UPDATE=1)`);
    }
    const baseline = stable(JSON.parse(fs.readFileSync(TREE_GROUPED_BASELINE, 'utf-8') || '{}'));
    if (JSON.stringify(baseline) !== JSON.stringify(groupedSignature)) {
      writeJson(path.join(outDir, 'grouped_signature.baseline.json'), baseline);
      writeSummary(summary);
      throw new Error('grouped signature baseline mismatch');
    }
    summary.push('grouped_signature_baseline_match: yes');
  }

  writeSummary(summary);
  log('PASS tree view mvp');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_tree_view_smoke] FAIL: ${err.message}`);
  process.exit(1);
});

#!/usr/bin/env node
'use strict';

const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const SAMPLES_FILE = process.env.ATTACHMENT_UPLOAD_BROWSER_SAMPLES_FILE || '';
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5179';
const DB_NAME = process.env.DB_NAME || 'sc_prod';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const LIMIT = Number(process.env.ATTACHMENT_UPLOAD_BROWSER_LIMIT || 0);

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'attachment-upload-frontend-browser-matrix', ts);

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

function loadSamples() {
  if (!SAMPLES_FILE) throw new Error('ATTACHMENT_UPLOAD_BROWSER_SAMPLES_FILE is required');
  const data = JSON.parse(fs.readFileSync(SAMPLES_FILE, 'utf8'));
  const rows = Array.isArray(data.samples) ? data.samples : data;
  if (!Array.isArray(rows) || !rows.length) throw new Error('sample file has no samples');
  return (LIMIT > 0 ? rows.slice(0, LIMIT) : rows).filter((row) => row && row.model && row.record_id);
}

function parseLastJson(stdout) {
  const text = String(stdout || '').trim();
  const start = text.lastIndexOf('\n{');
  const candidate = start >= 0 ? text.slice(start + 1) : text;
  try {
    return JSON.parse(candidate);
  } catch {
    return { raw: text.slice(-2000) };
  }
}

function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const samples = loadSamples();
  const result = {
    pass: false,
    scope: 'attachment_upload_frontend_browser_matrix_acceptance',
    db: DB_NAME,
    login: LOGIN,
    frontend_url: FRONTEND_URL,
    sample_count: samples.length,
    artifact_dir: outDir,
    rows: [],
  };

  for (const sample of samples) {
    const env = {
      ...process.env,
      FRONTEND_URL,
      DB_NAME,
      E2E_LOGIN: LOGIN,
      E2E_PASSWORD: PASSWORD,
      MVP_MODEL: String(sample.model),
      RECORD_ID: String(sample.record_id),
      ACTION_ID: sample.action_id ? String(sample.action_id) : '',
      MENU_ID: sample.menu_id ? String(sample.menu_id) : '',
      ARTIFACTS_DIR,
    };
    const child = spawnSync(process.execPath, ['scripts/verify/attachment_upload_frontend_browser_acceptance.js'], {
      cwd: process.cwd(),
      env,
      encoding: 'utf8',
      maxBuffer: 20 * 1024 * 1024,
    });
    const parsed = parseLastJson(child.stdout);
    result.rows.push({
      model: sample.model,
      record_id: sample.record_id,
      action_id: sample.action_id || null,
      menu_id: sample.menu_id || null,
      pass: child.status === 0 && parsed.pass === true,
      status: child.status,
      attachment_id: parsed.attachment_id || null,
      artifact_dir: parsed.artifact_dir || null,
      fixture_sha256: parsed.fixture_sha256 || null,
      intent_download_sha256: parsed.intent_download_sha256 || null,
      ui_download_sha256: parsed.ui_download_sha256 || null,
      console_errors: parsed.console_errors,
      stderr: String(child.stderr || '').slice(-2000),
      stdout_tail: parsed.raw ? String(parsed.raw).slice(-2000) : '',
    });
  }

  result.attachment_ids = result.rows.map((row) => row.attachment_id).filter(Boolean);
  result.pass = result.rows.every((row) => row.pass);
  writeJson('summary.json', result);
  console.log(JSON.stringify({
    pass: result.pass,
    artifact_dir: outDir,
    sample_count: result.sample_count,
    passed: result.rows.filter((row) => row.pass).length,
    failed: result.rows.filter((row) => !row.pass).length,
    attachment_ids: result.attachment_ids,
  }, null, 2));
  process.exit(result.pass ? 0 : 1);
}

try {
  main();
} catch (err) {
  const result = {
    pass: false,
    artifact_dir: outDir,
    error: err instanceof Error ? err.message : String(err),
  };
  writeJson('summary.json', result);
  console.error(JSON.stringify(result, null, 2));
  process.exit(1);
}

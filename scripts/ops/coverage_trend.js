#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const SERIES = process.env.COVERAGE_SERIES || 'portal-shell-v0_8-semantic';
const LIMIT = Number(process.env.COVERAGE_LIMIT || 10);

const baseDir = path.join(ARTIFACTS_DIR, 'codex', SERIES);

function log(msg) {
  console.log(`[coverage_trend] ${msg}`);
}

function readJson(file) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (err) {
    return null;
  }
}

function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2));
}

function writeText(file, text) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, text);
}

function listCoverageEntries() {
  if (!fs.existsSync(baseDir)) {
    return [];
  }
  const entries = [];
  const dirs = fs.readdirSync(baseDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort();

  for (const dir of dirs) {
    const coveragePath = path.join(baseDir, dir, 'coverage.json');
    if (!fs.existsSync(coveragePath)) {
      continue;
    }
    const coverage = readJson(coveragePath);
    if (!coverage) {
      continue;
    }
    entries.push({ ts: dir, coverage });
  }
  return entries;
}

function main() {
  const entries = listCoverageEntries();
  if (!entries.length) {
    console.error(`[coverage_trend] FAIL: no coverage.json found under ${baseDir}`);
    process.exit(1);
  }

  const sliced = entries.slice(Math.max(0, entries.length - LIMIT));
  const rows = sliced.map((entry) => {
    const cov = entry.coverage || {};
    return {
      ts: entry.ts,
      model: cov.model || '-',
      view_type: cov.view_type || '-',
      present_count: cov.present_count ?? 0,
      required_count: cov.required_count ?? 0,
      missing_count: cov.missing_count ?? 0,
      blocking_missing: Array.isArray(cov.blocking_missing) ? cov.blocking_missing : [],
    };
  });

  const last = rows[rows.length - 1];
  const prev = rows.length > 1 ? rows[rows.length - 2] : null;
  const deltaPresent = prev ? last.present_count - prev.present_count : 0;
  const deltaMissing = prev ? last.missing_count - prev.missing_count : 0;

  const report = {
    series: SERIES,
    total_entries: entries.length,
    window: rows.length,
    latest: last,
    delta: {
      present: deltaPresent,
      missing: deltaMissing,
    },
    rows,
  };

  const outJson = path.join(baseDir, 'coverage_trend.json');
  writeJson(outJson, report);

  const lines = [];
  lines.push(`# Coverage Trend (${SERIES})`);
  lines.push('');
  lines.push(`entries: ${entries.length}`);
  lines.push(`window: last ${rows.length}`);
  lines.push(`latest: ${last.ts} present=${last.present_count} missing=${last.missing_count}`);
  if (prev) {
    lines.push(`delta: present ${deltaPresent >= 0 ? '+' : ''}${deltaPresent}, missing ${deltaMissing >= 0 ? '+' : ''}${deltaMissing}`);
  }
  lines.push('');
  lines.push('| timestamp | model | view | present | required | missing | blocking |');
  lines.push('|---|---|---|---:|---:|---:|---|');
  for (const row of rows) {
    lines.push(`| ${row.ts} | ${row.model} | ${row.view_type} | ${row.present_count} | ${row.required_count} | ${row.missing_count} | ${row.blocking_missing.join(',') || '-'} |`);
  }

  const outMd = path.join(baseDir, 'coverage_trend.md');
  writeText(outMd, lines.join('\n'));

  log(`wrote ${outJson}`);
  log(`wrote ${outMd}`);
}

main();

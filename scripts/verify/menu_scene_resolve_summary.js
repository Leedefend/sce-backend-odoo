#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const SUMMARY_PATH = process.env.SUMMARY_PATH || '';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-menu-scene-resolve', ts);

function log(msg) {
  console.log(`[menu_scene_resolve_summary] ${msg}`);
}

function findLatest(dir, filename) {
  if (!fs.existsSync(dir)) return '';
  const entries = fs
    .readdirSync(dir, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name)
    .sort()
    .reverse();
  for (const entry of entries) {
    const candidate = path.join(dir, entry, filename);
    if (fs.existsSync(candidate)) return candidate;
  }
  return '';
}

function appendSummary(lines) {
  if (!SUMMARY_PATH) return;
  fs.mkdirSync(path.dirname(SUMMARY_PATH), { recursive: true });
  fs.appendFileSync(SUMMARY_PATH, lines.join('\n') + '\n');
}

function main() {
  const baseDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-menu-scene-resolve');
  const jsonPath = findLatest(baseDir, 'menu_scene_resolve.json');
  if (!jsonPath) {
    log('no menu_scene_resolve.json found');
    return;
  }
  const raw = fs.readFileSync(jsonPath, 'utf-8');
  const data = JSON.parse(raw);
  const summary = data.summary || {};
  const total = summary.total ?? 'n/a';
  const resolved = summary.resolved ?? 'n/a';
  const failures = summary.failures ?? 'n/a';
  const coverage = summary.coverage ?? 'n/a';
  log(`latest: ${jsonPath}`);
  log(`total=${total} resolved=${resolved} failures=${failures} coverage=${coverage}%`);

  appendSummary([
    `menu_scene_resolve_json: ${jsonPath}`,
    `menu_scene_resolve_total: ${total}`,
    `menu_scene_resolve_resolved: ${resolved}`,
    `menu_scene_resolve_failures: ${failures}`,
    `menu_scene_resolve_coverage: ${coverage}%`,
  ]);
}

main();

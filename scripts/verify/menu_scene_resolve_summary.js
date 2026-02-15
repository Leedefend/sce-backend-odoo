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
  const exempt = summary.exempt ?? 0;
  const effectiveTotal = summary.effective_total ?? (typeof total === 'number' ? total : 'n/a');
  const coverage = summary.coverage ?? 'n/a';
  const enforcePrefixes = Array.isArray(summary.enforce_prefixes) ? summary.enforce_prefixes : [];
  const exemptList = Array.isArray(data.exempt) ? data.exempt : [];
  const autoExempt = exemptList.filter((item) => item && item.reason === 'auto_exempt_non_business_namespace').length;
  const manualExempt = Math.max(exemptList.length - autoExempt, 0);
  log(`latest: ${jsonPath}`);
  log(`total=${total} resolved=${resolved} failures=${failures} exempt=${exempt} effective_total=${effectiveTotal} coverage=${coverage}%`);
  if (enforcePrefixes.length) {
    log(`enforce_prefixes=${enforcePrefixes.join(',')}`);
  }
  log(`exempt_breakdown: manual=${manualExempt} auto=${autoExempt}`);

  appendSummary([
    `menu_scene_resolve_json: ${jsonPath}`,
    `menu_scene_resolve_total: ${total}`,
    `menu_scene_resolve_resolved: ${resolved}`,
    `menu_scene_resolve_failures: ${failures}`,
    `menu_scene_resolve_exempt: ${exempt}`,
    `menu_scene_resolve_exempt_manual: ${manualExempt}`,
    `menu_scene_resolve_exempt_auto: ${autoExempt}`,
    `menu_scene_resolve_effective_total: ${effectiveTotal}`,
    `menu_scene_resolve_coverage: ${coverage}%`,
    `menu_scene_resolve_enforce_prefixes: ${enforcePrefixes.join(',') || '-'}`,
  ]);
}

main();

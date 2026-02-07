#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const SUMMARY_PATH = process.env.SUMMARY_PATH || '';

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

function readJson(file) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf-8'));
  } catch {
    return null;
  }
}

function appendSummary(lines) {
  if (!SUMMARY_PATH) return;
  fs.mkdirSync(path.dirname(SUMMARY_PATH), { recursive: true });
  fs.appendFileSync(SUMMARY_PATH, lines.join('\n') + '\n');
}

function main() {
  const warningsDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-scene-warnings');
  const menuDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-menu-scene-resolve');

  const warningsPath = findLatest(warningsDir, 'warnings.json');
  const menuPath = findLatest(menuDir, 'menu_scene_resolve.json');

  const out = {
    warnings: warningsPath ? readJson(warningsPath) : null,
    menu_scene_resolve: menuPath ? readJson(menuPath) : null,
  };

  const outDir = path.join(ARTIFACTS_DIR, 'codex', 'phase-9-8');
  fs.mkdirSync(outDir, { recursive: true });
  const outFile = path.join(outDir, 'gate_summary.json');
  fs.writeFileSync(outFile, JSON.stringify(out, null, 2));

  const summaryLines = [
    `phase_9_8_gate_summary: ${outFile}`,
    `phase_9_8_menu_resolve: ${menuPath || 'n/a'}`,
    `phase_9_8_warnings: ${warningsPath || 'n/a'}`,
  ];
  appendSummary(summaryLines);
}

main();

#!/usr/bin/env node
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';

const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..', '..');
const require = createRequire(path.join(repoRoot, 'frontend', 'apps', 'web', 'package.json'));

function exists(filePath) {
  try {
    fs.accessSync(filePath);
    return true;
  } catch {
    return false;
  }
}

function isExecutable(filePath) {
  try {
    fs.accessSync(filePath, fs.constants.X_OK);
    return true;
  } catch {
    return false;
  }
}

function revisionOf(name) {
  const match = String(name || '').match(/-(\d+)$/);
  return match ? Number(match[1]) : 0;
}

function candidates(cacheRoot) {
  let entries = [];
  try {
    entries = fs.readdirSync(cacheRoot, { withFileTypes: true });
  } catch {
    return [];
  }
  return entries
    .filter((entry) => entry.isDirectory() && (entry.name.startsWith('chromium-') || entry.name.startsWith('chromium_headless_shell-')))
    .sort((a, b) => revisionOf(b.name) - revisionOf(a.name))
    .flatMap((entry) => [
      {
        dir: path.join(cacheRoot, entry.name),
        exe: path.join(cacheRoot, entry.name, 'chrome-linux64', 'chrome'),
      },
      {
        dir: path.join(cacheRoot, entry.name),
        exe: path.join(cacheRoot, entry.name, 'chrome-headless-shell-linux64', 'chrome-headless-shell'),
      },
    ])
    .filter((item) => isExecutable(item.exe));
}

function expectedExecutable() {
  const { chromium } = require('playwright');
  return chromium.executablePath();
}

function chooseCandidate(expectedPath, cacheRoot) {
  const expectedDirName = path.basename(expectedPath.split(path.sep).slice(0, -2).join(path.sep));
  const expectedName = path.basename(expectedPath);
  const rows = candidates(cacheRoot);
  return (
    rows.find((row) => path.basename(row.dir).split('-')[0] === expectedDirName.split('-')[0] && path.basename(row.exe) === expectedName)
    || rows.find((row) => path.basename(row.exe) === expectedName)
    || rows[0]
    || null
  );
}

function repairExpectedExecutable(expected, cacheRoot) {
  if (exists(expected)) {
    return { ok: true, status: 'already_present', expected };
  }
  const expectedDir = expected.split(path.sep).slice(0, -2).join(path.sep);
  const found = chooseCandidate(expected, cacheRoot);
  if (!found) {
    throw new Error(`No cached Chromium executable found under ${cacheRoot}; expected ${expected}`);
  }
  fs.mkdirSync(path.dirname(expectedDir), { recursive: true });
  if (exists(expectedDir) && !exists(expected)) {
    const brokenDir = `${expectedDir}.broken-${Date.now()}`;
    fs.renameSync(expectedDir, brokenDir);
  }
  if (!exists(expectedDir)) {
    fs.symlinkSync(found.dir, expectedDir, 'dir');
  }
  if (!exists(expected)) {
    throw new Error(`Created ${expectedDir} -> ${found.dir}, but expected executable is still missing: ${expected}`);
  }
  return { ok: true, status: 'linked', expected, linked_dir: expectedDir, source_dir: found.dir, source_executable: found.exe };
}

function siblingHeadlessShellExpected(chromiumExpected) {
  const chromiumDir = chromiumExpected.split(path.sep).slice(0, -2).join(path.sep);
  const revision = path.basename(chromiumDir).replace(/^chromium-/, '');
  if (!revision) return '';
  return path.join(path.dirname(chromiumDir), `chromium_headless_shell-${revision}`, 'chrome-headless-shell-linux64', 'chrome-headless-shell');
}

function main() {
  const cacheRoot = process.env.PLAYWRIGHT_BROWSERS_PATH || path.join(os.homedir(), '.cache', 'ms-playwright');
  const expected = expectedExecutable();
  const results = [repairExpectedExecutable(expected, cacheRoot)];
  const headlessExpected = siblingHeadlessShellExpected(expected);
  if (headlessExpected) {
    results.push(repairExpectedExecutable(headlessExpected, cacheRoot));
  }
  console.log(JSON.stringify({ ok: true, results }, null, 2));
}

main();

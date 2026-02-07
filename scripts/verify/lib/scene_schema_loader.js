#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const REPO_ROOT = path.resolve(__dirname, '../../..');

function normalizeVersion(input, fallback) {
  if (!input) return fallback;
  const raw = String(input).trim().toLowerCase();
  if (raw === 'v2' || raw === '2') return 'v2';
  if (raw === 'v1' || raw === '1') return 'v1';
  return fallback;
}

function findSchemaPath(relPath) {
  const roots = [
    process.env.SCENE_SCHEMA_ROOT,
    process.env.REPO_ROOT,
    REPO_ROOT,
    process.cwd(),
    '/mnt/extra-addons',
    '/mnt/addons_external',
    '/mnt/odoo',
  ].filter(Boolean);
  const stripped = relPath.startsWith('addons/') ? relPath.slice('addons/'.length) : relPath;
  const relPaths = [relPath, stripped];
  for (const root of roots) {
    for (const rel of relPaths) {
      const candidate = path.join(root, rel);
      if (fs.existsSync(candidate)) return candidate;
    }
  }
  return '';
}

function loadJson(relPath) {
  const filePath = findSchemaPath(relPath);
  if (!filePath) {
    throw new Error(`schema file not found: ${relPath}`);
  }
  const raw = fs.readFileSync(filePath, 'utf-8');
  return JSON.parse(raw);
}

function loadSchema(version) {
  const normalized = normalizeVersion(version, 'v1');
  const relPath = `addons/smart_construction_scene/schema/scene_schema_${normalized}.json`;
  return loadJson(relPath);
}

function loadProfiles(version) {
  const normalized = normalizeVersion(version, 'v1');
  const relPath = `addons/smart_construction_scene/schema/scene_profiles_${normalized}.json`;
  return loadJson(relPath);
}

module.exports = {
  normalizeVersion,
  loadSchema,
  loadProfiles,
};

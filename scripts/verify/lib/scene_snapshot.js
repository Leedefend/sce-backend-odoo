#!/usr/bin/env node
'use strict';

function sortStrings(items) {
  if (!Array.isArray(items)) return items;
  return [...items].sort();
}

function normalizeLabels(labels) {
  if (!labels || typeof labels !== 'object' || Array.isArray(labels)) return labels;
  const out = {};
  Object.keys(labels).sort().forEach((key) => {
    out[key] = labels[key];
  });
  return out;
}

function normalizeTarget(target) {
  if (!target || typeof target !== 'object') return target;
  const out = {};
  ['action_id', 'menu_id', 'model', 'view_mode', 'route'].forEach((key) => {
    if (target[key] !== undefined) out[key] = target[key];
  });
  return out;
}

function normalizeListProfile(profile) {
  if (!profile || typeof profile !== 'object') return profile;
  return {
    columns: sortStrings(profile.columns || []),
    hidden_columns: sortStrings(profile.hidden_columns || []),
    column_labels: normalizeLabels(profile.column_labels || {}),
    row_primary: profile.row_primary || '',
    row_secondary: profile.row_secondary || '',
  };
}

function normalizeFilter(filter) {
  if (!filter || typeof filter !== 'object') return null;
  return {
    key: filter.key || '',
    label: filter.label || '',
    domain: Array.isArray(filter.domain) ? filter.domain : [],
  };
}

function normalizeTile(tile) {
  if (!tile || typeof tile !== 'object') return null;
  const payload = tile.payload || {};
  const out = {
    key: tile.key || '',
    title: tile.title || '',
    subtitle: tile.subtitle || '',
    icon: tile.icon || '',
    scene_key: tile.scene_key || '',
    required_capabilities: sortStrings(tile.required_capabilities || []),
    payload: {},
  };
  ['action_xmlid', 'menu_xmlid', 'scene_key', 'route'].forEach((key) => {
    if (payload[key] !== undefined) out.payload[key] = payload[key];
  });
  return out;
}

function canonicalizeScene(scene) {
  const out = {
    code: scene.code || scene.key || '',
    name: scene.name || '',
    layout: scene.layout || {},
    target: normalizeTarget(scene.target || {}),
    list_profile: normalizeListProfile(scene.list_profile || {}),
    default_sort: scene.default_sort || '',
    filters: Array.isArray(scene.filters) ? scene.filters.map(normalizeFilter).filter(Boolean).sort((a, b) => a.key.localeCompare(b.key)) : [],
    tiles: Array.isArray(scene.tiles) ? scene.tiles.map(normalizeTile).filter(Boolean).sort((a, b) => a.key.localeCompare(b.key)) : [],
  };
  return out;
}

function canonicalizeScenes(scenes) {
  const list = Array.isArray(scenes) ? scenes : [];
  return list.map(canonicalizeScene).sort((a, b) => a.code.localeCompare(b.code));
}

module.exports = {
  canonicalizeScenes,
};

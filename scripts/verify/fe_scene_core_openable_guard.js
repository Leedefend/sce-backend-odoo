#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const SCENE_REGISTRY_CONTENT_PATH = path.resolve(
  __dirname,
  '../../addons/smart_construction_scene/profiles/scene_registry_content.py'
);

function fail(msg) {
  console.error(`[fe_scene_core_openable_guard] FAIL: ${msg}`);
  process.exit(1);
}

function main() {
  if (!fs.existsSync(SCENE_REGISTRY_CONTENT_PATH)) {
    fail(`scene registry content missing: ${SCENE_REGISTRY_CONTENT_PATH}`);
  }
  const src = fs.readFileSync(SCENE_REGISTRY_CONTENT_PATH, 'utf8');

  const required = [
    { scene: 'projects.list', marker: '"action_xmlid": "smart_construction_core.action_sc_project_list"' },
    { scene: 'projects.ledger', marker: '"action_xmlid": "smart_construction_core.action_sc_project_kanban_lifecycle"' },
    { scene: 'projects.intake', marker: '"action_xmlid": "smart_construction_core.action_project_initiation"' },
  ];

  for (const item of required) {
    if (!src.includes(`"code": "${item.scene}"`)) {
      fail(`scene missing in registry: ${item.scene}`);
    }
    if (!src.includes(item.marker)) {
      fail(`scene target missing action_xmlid: ${item.scene}`);
    }
  }

  console.log('[fe_scene_core_openable_guard] PASS');
}

main();

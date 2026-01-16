/** @odoo-module **/

import { buildMenuSections, normalizeMenus, parseActionId } from "../src/js/sc_sidebar";

QUnit.module("smart_construction_core.sidebar");

QUnit.test("parseActionId supports common formats", function (assert) {
  assert.strictEqual(parseActionId({ action: "ir.actions.act_window,448" }), 448);
  assert.strictEqual(parseActionId({ action: 12 }), 12);
  assert.strictEqual(parseActionId({ action: [34, "ir.actions.act_window"] }), 34);
  assert.strictEqual(parseActionId({ action: { id: 56 } }), 56);
  assert.strictEqual(parseActionId({ action: "invalid" }), null);
  assert.strictEqual(parseActionId({}), null);
});

QUnit.test("normalizeMenus unwraps root and menu_data", function (assert) {
  const root = { id: 1, children: [] };
  const wrapped = { root: { root } };
  assert.strictEqual(normalizeMenus(wrapped), root);

  let captured = null;
  const menuData = { 1: root };
  normalizeMenus({ menu_data: menuData }, (map) => (captured = map));
  assert.strictEqual(captured, menuData);
});

QUnit.test("buildMenuSections handles object children", function (assert) {
  const root = {
    id: 0,
    children: [
      { id: 1, name: "A", action: "ir.actions.act_window,10", children: [] },
      { id: 2, name: "B", children: [{ id: 3, name: "B1", action: "ir.actions.act_window,20" }] },
    ],
  };
  const sections = buildMenuSections(root, null);
  assert.strictEqual(sections.length, 2);
  assert.strictEqual(sections[0].actionId, 10);
  assert.strictEqual(sections[1].children.length, 1);
  assert.strictEqual(sections[1].children[0].actionId, 20);
});

QUnit.test("buildMenuSections handles id children via map", function (assert) {
  const menuMap = {
    1: { id: 1, name: "A", action: "ir.actions.act_window,10", children: [] },
    2: { id: 2, name: "B", children: [3] },
    3: { id: 3, name: "B1", action: "ir.actions.act_window,20", children: [] },
  };
  const root = { id: 0, children: [1, 2] };
  const sections = buildMenuSections(root, menuMap);
  assert.strictEqual(sections.length, 2);
  assert.strictEqual(sections[1].children.length, 1);
  assert.strictEqual(sections[1].children[0].actionId, 20);
});

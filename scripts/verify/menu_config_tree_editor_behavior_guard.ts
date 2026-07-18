#!/usr/bin/env node
import * as assert from 'assert/strict';
import { useMenuTreeEditor } from '../../frontend/apps/web/src/views/menuConfig/useMenuTreeEditor';
import type { MenuConfigMenu } from '../../frontend/apps/web/src/api/menuConfig';

type Box<T> = { value: T };

function box<T>(value: T): Box<T> {
  return { value };
}

function menu(id: number, runtimeGroup = false): MenuConfigMenu {
  return {
    id,
    menu_id: id,
    name: `menu-${id}`,
    display_name: `menu-${id}`,
    complete_name: `menu-${id}`,
    parent_id: 1,
    parent_name: 'root',
    sequence: id * 10,
    action: '',
    web_icon: '',
    xmlid: '',
    group_ids: [],
    group_names: [],
    children: [],
    ...(runtimeGroup ? { runtime_group: true } : {}),
  } as MenuConfigMenu;
}

function createHarness(enabled: boolean) {
  const normalMenu = menu(2);
  const runtimeGroup = menu(3, true);
  const tree = box<MenuConfigMenu[]>([normalMenu, runtimeGroup]);
  const dragSourceMenuId = box(0);
  const dragTargetMenuId = box(0);
  const dragDropPosition = box<'before' | 'after' | 'inside'>('before');
  const editor = useMenuTreeEditor({
    selectedMenuId: box(0) as any,
    collapsedMenuIds: box(new Set<number>()) as any,
    dragSourceMenuId: dragSourceMenuId as any,
    dragTargetMenuId: dragTargetMenuId as any,
    dragDropPosition: dragDropPosition as any,
    treeDragEnabled: box(enabled) as any,
    tree: tree as any,
    message: box('') as any,
    selectedMenuPath: () => new Set<number>(),
    menuById: (menuId) => tree.value.find((item) => item.id === menuId) || null,
    treeMenuById: (menuId) => tree.value.find((item) => item.id === menuId) || null,
    isRuntimeMenuGroup: (item) => Boolean((item as MenuConfigMenu & { runtime_group?: boolean } | null)?.runtime_group),
    parentOptionIds: () => new Set<number>(),
    draftFor: () => undefined,
    setSaveNotice: () => undefined,
  });
  return { editor, dragSourceMenuId, dragTargetMenuId, dragDropPosition };
}

function assertEnabledDragStartsWithoutRuntimeReferenceErrors() {
  const harness = createHarness(true);
  harness.editor.startTreeDrag(2);
  assert.equal(harness.dragSourceMenuId.value, 2);
  assert.equal(harness.dragTargetMenuId.value, 0);
  assert.equal(harness.dragDropPosition.value, 'after');
}

function assertDisabledDragDoesNotStart() {
  const harness = createHarness(false);
  harness.editor.startTreeDrag(2);
  assert.equal(harness.dragSourceMenuId.value, 0);
  assert.equal(harness.dragDropPosition.value, 'before');
}

function assertRuntimeGroupCannotBeDragged() {
  const harness = createHarness(true);
  harness.editor.startTreeDrag(3);
  assert.equal(harness.dragSourceMenuId.value, 0);
  assert.equal(harness.dragDropPosition.value, 'before');
}

assertEnabledDragStartsWithoutRuntimeReferenceErrors();
assertDisabledDragDoesNotStart();
assertRuntimeGroupCannotBeDragged();
console.log('[menu_config_tree_editor_behavior_guard] PASS');

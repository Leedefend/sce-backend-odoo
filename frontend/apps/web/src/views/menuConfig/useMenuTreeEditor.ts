import type { Ref } from 'vue';
import type { MenuConfigMenu } from '../../api/menuConfig';
import type { MenuConfigDropPosition as DropPosition } from './createMenuConfigTree';

type EditableDraft = { target_parent_menu_id: number; sequence_override: number };

export function useMenuTreeEditor(options: {
  selectedMenuId: Ref<number>;
  collapsedMenuIds: Ref<Set<number>>;
  dragSourceMenuId: Ref<number>;
  dragTargetMenuId: Ref<number>;
  dragDropPosition: Ref<DropPosition>;
  treeDragEnabled: Readonly<Ref<boolean>>;
  tree: Ref<MenuConfigMenu[]>;
  message: Ref<string>;
  selectedMenuPath: (items: MenuConfigMenu[], menuId: number) => Set<number>;
  menuById: (menuId: number) => MenuConfigMenu | null;
  treeMenuById: (menuId: number) => MenuConfigMenu | null;
  isRuntimeMenuGroup: (menu: MenuConfigMenu | null | undefined) => boolean;
  parentOptionIds: (menuId: number) => Set<number>;
  draftFor: (menuId: number) => EditableDraft | undefined;
  setSaveNotice: (value: string) => void;
}) {
  const {
    selectedMenuId,
    collapsedMenuIds,
    dragSourceMenuId,
    dragTargetMenuId,
    dragDropPosition,
    treeDragEnabled,
    tree,
    message,
  } = options;
  const {
    selectedMenuPath,
    menuById,
    treeMenuById,
    isRuntimeMenuGroup,
    parentOptionIds,
    draftFor,
    setSaveNotice,
  } = options;
  function initializeTreeCollapse(items: MenuConfigMenu[]) {
    const selectedPath = selectedMenuPath(items, selectedMenuId.value);
    const next = new Set<number>();
    const walk = (rows: MenuConfigMenu[]) => {
      rows.forEach((item) => {
        if (item.children?.length) {
          if (!selectedPath.has(item.id)) next.add(item.id);
          walk(item.children);
        }
      });
    };
    walk(items);
    collapsedMenuIds.value = next;
  }

  function toggleTreeNodeCollapse(menuId: number) {
    const next = new Set(collapsedMenuIds.value);
    if (next.has(menuId)) next.delete(menuId);
    else next.add(menuId);
    collapsedMenuIds.value = next;
  }

  function startTreeDrag(menuId: number) {
    if (!treeDragEnabled.value) return;
    const menu = treeMenuById(menuId);
    if (isRuntimeMenuGroup(menu)) return;
    dragSourceMenuId.value = menuId;
    dragTargetMenuId.value = 0;
    dragDropPosition.value = 'after';
  }

  function updateTreeDragTarget(payload: { menuId: number; position: DropPosition }) {
    if (!dragSourceMenuId.value || payload.menuId === dragSourceMenuId.value) return;
    if (!areVisualSiblings(tree.value, dragSourceMenuId.value, payload.menuId)) {
      const allowedParentIds = parentOptionIds(dragSourceMenuId.value);
      const targetMenu = menuById(payload.menuId);
      if (allowedParentIds.has(Number(payload.menuId))) {
        dragTargetMenuId.value = payload.menuId;
        dragDropPosition.value = 'inside';
        return;
      }
      if (!targetMenu || !allowedParentIds.has(Number(targetMenu.parent_id || 0))) {
        dragTargetMenuId.value = 0;
        return;
      }
      dragTargetMenuId.value = payload.menuId;
      dragDropPosition.value = payload.position;
      return;
    }
    dragTargetMenuId.value = payload.menuId;
    dragDropPosition.value = payload.position;
  }

  function resequenceBranch(items: MenuConfigMenu[]) {
    return items.map((item, index) => {
      const draft = draftFor(item.id);
      if (draft) {
        draft.sequence_override = (index + 1) * 10;
      }
      return item;
    });
  }

  function reorderSiblingBranch(items: MenuConfigMenu[], sourceId: number, targetId: number, position: DropPosition): MenuConfigMenu[] {
    const ids = items.map((item) => item.id);
    if (ids.includes(sourceId) && ids.includes(targetId)) {
      const source = items.find((item) => item.id === sourceId);
      if (!source) return items;
      const next = items.filter((item) => item.id !== sourceId);
      const targetIndex = next.findIndex((item) => item.id === targetId);
      if (targetIndex < 0) return items;
      next.splice(position === 'before' ? targetIndex : targetIndex + 1, 0, source);
      return resequenceBranch(next);
    }

    return items.map((item) => {
      if (!item.children?.length) return item;
      return { ...item, children: reorderSiblingBranch(item.children, sourceId, targetId, position) };
    });
  }

  function removeTreeNode(items: MenuConfigMenu[], sourceId: number): { rows: MenuConfigMenu[]; removed: MenuConfigMenu | null } {
    let removed: MenuConfigMenu | null = null;
    const rows = items.flatMap((item) => {
      if (Number(item.id) === Number(sourceId)) {
        removed = item;
        return [];
      }
      if (!item.children?.length) return [item];
      const result = removeTreeNode(item.children, sourceId);
      if (result.removed) {
        removed = result.removed;
        return [{ ...item, children: resequenceBranch(result.rows) }];
      }
      return [item];
    });
    return { rows, removed };
  }

  function insertTreeNodeInside(items: MenuConfigMenu[], parentId: number, source: MenuConfigMenu): { rows: MenuConfigMenu[]; inserted: boolean } {
    let inserted = false;
    const rows = items.map((item) => {
      if (Number(item.id) === Number(parentId)) {
        inserted = true;
        const nextChild = { ...source, parent_id: parentId, parent_name: item.complete_name || item.name };
        const children = resequenceBranch([...(item.children || []), nextChild]);
        return { ...item, children };
      }
      if (!item.children?.length) return item;
      const result = insertTreeNodeInside(item.children, parentId, source);
      inserted = inserted || result.inserted;
      return result.inserted ? { ...item, children: result.rows } : item;
    });
    return { rows, inserted };
  }

  function moveTreeNodeToParent(sourceId: number, parentId: number): boolean {
    if (!sourceId || !parentId || sourceId === parentId || !parentOptionIds(sourceId).has(parentId)) return false;
    const result = removeTreeNode(tree.value, sourceId);
    if (!result.removed) return false;
    const inserted = insertTreeNodeInside(result.rows, parentId, result.removed);
    if (!inserted.inserted) return false;
    const draft = draftFor(sourceId);
    if (draft) {
      draft.target_parent_menu_id = parentId;
    }
    tree.value = inserted.rows;
    setSaveNotice('');
    return true;
  }

  function insertTreeNodeRelative(
    items: MenuConfigMenu[],
    source: MenuConfigMenu,
    targetId: number,
    parentId: number,
    position: Exclude<DropPosition, 'inside'>,
  ): { rows: MenuConfigMenu[]; inserted: boolean } {
    const ids = items.map((item) => Number(item.id));
    if (ids.includes(Number(targetId))) {
      const target = items.find((item) => Number(item.id) === Number(targetId));
      const nextSource = { ...source, parent_id: parentId, parent_name: target?.parent_name || source.parent_name };
      const withoutSource = items.filter((item) => Number(item.id) !== Number(source.id));
      const targetIndex = withoutSource.findIndex((item) => Number(item.id) === Number(targetId));
      if (targetIndex < 0) return { rows: items, inserted: false };
      withoutSource.splice(position === 'before' ? targetIndex : targetIndex + 1, 0, nextSource);
      return { rows: resequenceBranch(withoutSource), inserted: true };
    }
    let inserted = false;
    const rows = items.map((item) => {
      if (!item.children?.length) return item;
      const result = insertTreeNodeRelative(item.children, source, targetId, parentId, position);
      inserted = inserted || result.inserted;
      return result.inserted ? { ...item, children: result.rows } : item;
    });
    return { rows, inserted };
  }

  function moveTreeNodeRelative(sourceId: number, targetId: number, position: Exclude<DropPosition, 'inside'>): boolean {
    if (!sourceId || !targetId || sourceId === targetId) return false;
    const target = menuById(targetId);
    const parentId = Number(target?.parent_id || 0);
    if (!target || !parentId || !parentOptionIds(sourceId).has(parentId)) return false;
    const result = removeTreeNode(tree.value, sourceId);
    if (!result.removed) return false;
    const inserted = insertTreeNodeRelative(result.rows, result.removed, targetId, parentId, position);
    if (!inserted.inserted) return false;
    const draft = draftFor(sourceId);
    if (draft) {
      draft.target_parent_menu_id = parentId;
    }
    tree.value = inserted.rows;
    setSaveNotice('');
    return true;
  }

  function moveTreeNodeOrder(payload: { menuId: number; delta: number }) {
    const moveInBranch = (items: MenuConfigMenu[]): { rows: MenuConfigMenu[]; moved: boolean } => {
      const index = items.findIndex((item) => item.id === payload.menuId);
      if (index >= 0) {
        const targetIndex = index + payload.delta;
        if (targetIndex < 0 || targetIndex >= items.length) return { rows: items, moved: false };
        const next = [...items];
        const [moved] = next.splice(index, 1);
        next.splice(targetIndex, 0, moved);
        next.forEach((item, itemIndex) => {
          const draft = draftFor(item.id);
          if (draft) draft.sequence_override = (itemIndex + 1) * 10;
        });
        return { rows: next, moved: true };
      }
      let moved = false;
      const rows = items.map((item) => {
        if (!item.children?.length || moved) return item;
        const result = moveInBranch(item.children);
        moved = result.moved;
        return result.moved ? { ...item, children: result.rows } : item;
      });
      return { rows, moved };
    };
    const result = moveInBranch(tree.value);
    if (!result.moved) return;
    tree.value = result.rows;
    message.value = '';
    setSaveNotice('');
  }

  function applyTreeReorder(payload: { sourceId: number; targetId: number; position: DropPosition }) {
    if (!payload.sourceId || !payload.targetId || payload.sourceId === payload.targetId) {
      clearTreeDrag();
      return;
    }
    if (!areVisualSiblings(tree.value, payload.sourceId, payload.targetId)) {
      const moved = payload.position === 'inside'
        ? moveTreeNodeToParent(payload.sourceId, payload.targetId)
        : moveTreeNodeRelative(payload.sourceId, payload.targetId, payload.position);
      if (moved) {
        message.value = '';
        setSaveNotice('');
      }
      clearTreeDrag();
      return;
    }
    tree.value = reorderSiblingBranch(tree.value, payload.sourceId, payload.targetId, payload.position);
    message.value = '';
    setSaveNotice('');
    clearTreeDrag();
  }

  function applyTreeDrop(targetId: number) {
    const sourceId = dragSourceMenuId.value;
    if (!sourceId || !targetId || sourceId === targetId || !dragTargetMenuId.value) {
      clearTreeDrag();
      return;
    }
    let moved = false;
    if (dragDropPosition.value === 'inside') {
      moved = moveTreeNodeToParent(sourceId, targetId);
    } else if (areVisualSiblings(tree.value, sourceId, targetId)) {
      tree.value = reorderSiblingBranch(tree.value, sourceId, targetId, dragDropPosition.value);
      moved = true;
    } else {
      moved = moveTreeNodeRelative(sourceId, targetId, dragDropPosition.value);
    }
    if (moved) {
      message.value = '';
      setSaveNotice('');
    }
    clearTreeDrag();
  }

  function clearTreeDrag() {
    dragSourceMenuId.value = 0;
    dragTargetMenuId.value = 0;
    dragDropPosition.value = 'after';
  }

  function areVisualSiblings(items: MenuConfigMenu[], sourceId: number, targetId: number): boolean {
    const ids = items.map((item) => item.id);
    if (ids.includes(sourceId) && ids.includes(targetId)) return true;
    return items.some((item) => item.children?.length && areVisualSiblings(item.children, sourceId, targetId));
  }
  return {
    initializeTreeCollapse,
    toggleTreeNodeCollapse,
    startTreeDrag,
    updateTreeDragTarget,
    moveTreeNodeOrder,
    applyTreeReorder,
    applyTreeDrop,
    clearTreeDrag,
  };
}

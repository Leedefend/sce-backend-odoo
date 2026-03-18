type NavNode = {
  id?: number;
  key?: string;
  scene_key?: string;
  code?: string;
  menu_id?: number;
  children?: NavNode[];
};

type SceneLike = {
  key?: string;
  code?: string;
};

export function useActionViewSceneIdentityRuntime() {
  function resolveSceneCode(scene: SceneLike): string {
    return String(scene?.code || scene?.key || '').trim();
  }

  function resolveNodeSceneKey(node: NavNode): string {
    return String(node?.scene_key || node?.key || node?.code || '').trim();
  }

  function findMenuNode(nodes: NavNode[], menuId?: number): NavNode | null {
    if (!menuId) {
      return null;
    }
    const walk = (items: NavNode[]): NavNode | null => {
      for (const node of items) {
        if (node.menu_id === menuId || node.id === menuId) {
          return node;
        }
        if (node.children?.length) {
          const found = walk(node.children);
          if (found) return found;
        }
      }
      return null;
    };
    return walk(nodes) || null;
  }

  return {
    resolveSceneCode,
    resolveNodeSceneKey,
    findMenuNode,
  };
}


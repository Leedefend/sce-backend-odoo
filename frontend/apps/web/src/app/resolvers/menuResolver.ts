import type { NavMeta, NavNode } from '@sc/schema';
import { resolveMenuActionCore } from './menuResolverCore';

export type MenuResolveResult =
  | { kind: 'leaf'; meta: NavMeta; node: NavNode }
  | { kind: 'group'; node: NavNode }
  | { kind: 'broken'; node: NavNode | null; reason: string };

export function resolveMenuAction(menuTree: NavNode[], menuId: number): MenuResolveResult {
  return resolveMenuActionCore(menuTree, menuId) as MenuResolveResult;
}

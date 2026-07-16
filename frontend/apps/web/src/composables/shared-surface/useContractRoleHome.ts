import { computed, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import type { NavNode } from '@sc/schema';
import { fetchMyWorkSummary, type ProductMyWorkItem, type ProductMyWorkWorkspace } from '../../api/myWork';
import { currentContextEpoch, isCurrentContextEpoch } from '../../app/contextEpoch';
import { usePageContract } from '../../app/pageContract';
import { useSessionStore, type ActivityPage } from '../../stores/session';

type SurfaceLink = { key: string; label: string; detail: string; route: string };
type SurfaceCount = { key: string; label: string; value: number };

function text(value: unknown): string {
  return String(value ?? '').trim();
}

function nodeRoute(node: NavNode): string {
  const source = node as NavNode & {
    route?: string;
    scene_key?: string;
    sceneKey?: string;
    action_id?: number;
    actionId?: number;
  };
  const meta = node.meta && typeof node.meta === 'object' ? node.meta as Record<string, unknown> : {};
  const route = text(source.route || meta.route);
  if (route) return route;
  const sceneKey = text(source.scene_key || source.sceneKey || meta.scene_key || meta.sceneKey);
  if (sceneKey) return `/s/${encodeURIComponent(sceneKey)}`;
  const actionId = Number(source.action_id || source.actionId || meta.action_id || meta.actionId || 0);
  const menuId = Number(node.menu_id || meta.menu_id || meta.menuId || 0);
  if (actionId > 0) return `/a/${actionId}${menuId > 0 ? `?menu_id=${menuId}&action_id=${actionId}` : ''}`;
  if (menuId > 0 && !node.children?.length) return `/m/${menuId}`;
  return '';
}

function nodeLabel(node: NavNode): string {
  return text(node.title || node.name || node.label).replace(/\s*\(\d+\)\s*$/g, '');
}

function firstReachable(node: NavNode): NavNode | null {
  if (nodeRoute(node)) return node;
  for (const child of node.children || []) {
    const reachable = firstReachable(child);
    if (reachable) return reachable;
  }
  return null;
}

function topNodes(nodes: NavNode[]): NavNode[] {
  return nodes.length === 1 && nodes[0]?.children?.length ? nodes[0].children : nodes;
}

function taskLink(item: ProductMyWorkItem): SurfaceLink | null {
  const route = text(item.target?.route);
  const label = text(item.record?.label);
  if (!route || !label) return null;
  return {
    key: text(item.key) || route,
    label,
    detail: [text(item.business_type), text(item.state?.label)].filter(Boolean).join(' · '),
    route,
  };
}

function recentMatchesCompany(page: ActivityPage, companyId: number): boolean {
  if (!companyId) return true;
  const pageCompanyId = Number(page.project_context?.company_id || page.project_context?.selected?.company_id || 0);
  return !pageCompanyId || pageCompanyId === companyId;
}

export function useContractRoleHome() {
  const router = useRouter();
  const session = useSessionStore();
  const pageContract = usePageContract('home');
  const loading = ref(false);
  const error = ref('');
  const workWorkspace = ref<ProductMyWorkWorkspace | null>(null);

  const pageProfile = computed(() => pageContract.contract.value?.page_orchestration_v1?.page || {});
  const title = computed(() => text(pageProfile.value.title) || pageContract.text('title', '首页'));
  const subtitle = computed(() => text(pageProfile.value.subtitle) || pageContract.text('subtitle', '查看当前账号可处理的事项和可用入口。'));
  const taskSection = computed(() => workWorkspace.value?.sections.find((section) => section.key === 'todo') || null);
  const tasks = computed<SurfaceLink[]>(() => (taskSection.value?.items || [])
    .map(taskLink)
    .filter((item): item is SurfaceLink => Boolean(item))
    .slice(0, 3));
  const summaries = computed<SurfaceCount[]>(() => (workWorkspace.value?.sections || [])
    .map((section) => ({ key: section.key, label: section.label, value: section.count }))
    .slice(0, 4));
  const quickLinks = computed<SurfaceLink[]>(() => topNodes(session.menuTree)
    .map((node) => ({ group: node, target: firstReachable(node) }))
    .filter((item): item is { group: NavNode; target: NavNode } => Boolean(item.target))
    .map(({ group, target }) => ({
      key: `${text(group.key || group.id)}:${nodeRoute(target)}`,
      label: nodeLabel(group) || nodeLabel(target),
      detail: nodeLabel(target),
      route: nodeRoute(target),
    }))
    .slice(0, 7));
  const recentItems = computed<SurfaceLink[]>(() => {
    const companyId = Number(session.projectContext?.company_id || 0);
    return session.activityPages
      .filter((page) => page.route && page.title && recentMatchesCompany(page, companyId))
      .sort((left, right) => right.last_active_at - left.last_active_at)
      .slice(0, 4)
      .map((page) => ({ key: page.key, label: page.title, detail: '', route: page.route }));
  });

  async function load() {
    if (!session.token) {
      workWorkspace.value = null;
      return;
    }
    const requestEpoch = currentContextEpoch();
    loading.value = true;
    error.value = '';
    workWorkspace.value = null;
    try {
      const result = await fetchMyWorkSummary(12, 4, { page: 1, pageSize: 12, sortBy: 'priority', sortDir: 'desc' });
      if (isCurrentContextEpoch(requestEpoch)) workWorkspace.value = result.product_workspace || null;
    } catch {
      if (isCurrentContextEpoch(requestEpoch)) {
        error.value = pageContract.text('load_error', '当前页面暂时无法加载，请稍后重试。');
      }
    } finally {
      if (isCurrentContextEpoch(requestEpoch)) loading.value = false;
    }
  }

  async function navigate(route: string) {
    if (route) await router.push(route);
  }

  watch(
    [
      () => session.token,
      () => session.projectContext?.company_id,
      () => session.projectContext?.selected?.id,
    ],
    () => { void load(); },
    { immediate: true },
  );

  return { title, subtitle, tasks, summaries, quickLinks, recentItems, loading, error, load, navigate };
}

import { createRouter, createWebHistory } from 'vue-router';
import { useSessionStore } from '../stores/session';
import LoginView from '../views/LoginView.vue';
import HomeView from '../views/HomeView.vue';
import MenuView from '../views/MenuView.vue';
import ActionView from '../views/ActionView.vue';
import RecordView from '../views/RecordView.vue';
import WorkbenchView from '../views/WorkbenchView.vue';
import SceneView from '../views/SceneView.vue';
import SceneHealthView from '../views/SceneHealthView.vue';
import ScenePackagesView from '../views/ScenePackagesView.vue';
import UsageAnalyticsView from '../views/UsageAnalyticsView.vue';
import MyWorkView from '../views/MyWorkView.vue';
import { ApiError } from '../api/client';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    { path: '/', name: 'home', component: HomeView, meta: { layout: 'shell' } },
    { path: '/projects', name: 'scene-projects', component: SceneView, meta: { layout: 'shell', sceneKey: 'projects' } },
    { path: '/projects/:id', name: 'scene-project', component: SceneView, meta: { layout: 'shell', sceneKey: 'project-record' } },
    { path: '/my-work', name: 'my-work', component: MyWorkView, meta: { layout: 'shell' } },
    { path: '/s/:sceneKey', name: 'scene', component: SceneView, meta: { layout: 'shell' } },
    { path: '/m/:menuId', name: 'menu', component: MenuView, meta: { layout: 'shell' } },
    // Diagnostic-only surface; must not be used as product navigation.
    { path: '/workbench', name: 'workbench', component: WorkbenchView, meta: { layout: 'shell' } },
    { path: '/admin/scene-health', name: 'scene-health', component: SceneHealthView, meta: { layout: 'shell', adminOnly: true } },
    { path: '/admin/scene-packages', name: 'scene-packages', component: ScenePackagesView, meta: { layout: 'shell', adminOnly: true } },
    { path: '/admin/usage-analytics', name: 'usage-analytics', component: UsageAnalyticsView, meta: { layout: 'shell', adminOnly: true } },
    { path: '/a/:actionId', name: 'action', component: ActionView, meta: { layout: 'shell' } },
    { path: '/r/:model/:id', name: 'record', component: RecordView, meta: { layout: 'shell' } },
  ],
});

router.beforeEach(async (to) => {
  const session = useSessionStore();
  if (to.name !== 'login' && !session.token) {
    return { name: 'login', query: { redirect: to.fullPath } };
  }
  if (to.name !== 'login' && session.token && !session.isReady) {
    try {
      await session.ensureReady();
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        return { name: 'login', query: { redirect: to.fullPath } };
      }
      return true;
    }
  }
  if (to.meta?.adminOnly) {
    const groups = session.user?.groups_xmlids || [];
    const isAdmin =
      groups.includes('base.group_system') ||
      groups.includes('smart_construction_core.group_sc_cap_config_admin');
    if (!isAdmin) {
      return { path: '/s/projects.list' };
    }
  }
  return true;
});

export default router;

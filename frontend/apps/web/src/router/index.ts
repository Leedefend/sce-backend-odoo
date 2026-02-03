import { createRouter, createWebHistory } from 'vue-router';
import { useSessionStore } from '../stores/session';
import HomeView from '../views/HomeView.vue';
import LoginView from '../views/LoginView.vue';
import MenuView from '../views/MenuView.vue';
import ActionView from '../views/ActionView.vue';
import RecordView from '../views/RecordView.vue';
import { ApiError } from '../api/client';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    { path: '/', name: 'home', component: HomeView, meta: { layout: 'shell' } },
    { path: '/m/:menuId', name: 'menu', component: MenuView, meta: { layout: 'shell' } },
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
  return true;
});

export default router;

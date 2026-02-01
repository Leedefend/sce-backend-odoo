import { createRouter, createWebHistory } from 'vue-router';
import { useSessionStore } from '../stores/session';
import HomeView from '../views/HomeView.vue';
import LoginView from '../views/LoginView.vue';
import MenuView from '../views/MenuView.vue';
import ActionView from '../views/ActionView.vue';
import RecordView from '../views/RecordView.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    { path: '/', name: 'home', component: HomeView },
    { path: '/m/:menuId', name: 'menu', component: MenuView, props: true },
    { path: '/a/:actionId', name: 'action', component: ActionView, props: true },
    { path: '/r/:model/:id', name: 'record', component: RecordView, props: true },
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
    } catch {
      return { name: 'login' };
    }
  }
  return true;
});

export default router;

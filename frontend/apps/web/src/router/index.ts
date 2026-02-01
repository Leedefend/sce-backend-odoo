import { createRouter, createWebHistory } from 'vue-router';
import { useSessionStore } from '../stores/session';
import HomeView from '../views/HomeView.vue';
import LoginView from '../views/LoginView.vue';
import ModelListPage from '../pages/ModelListPage.vue';
import ModelFormPage from '../pages/ModelFormPage.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    { path: '/', name: 'home', component: HomeView },
    { path: '/m/:model', name: 'model-list', component: ModelListPage, props: true },
    { path: '/m/:model/:id', name: 'model-form', component: ModelFormPage, props: true },
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
      return { name: 'login', query: { redirect: to.fullPath } };
    }
  }
  return true;
});

export default router;

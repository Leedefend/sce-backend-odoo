import { createApp } from 'vue';
import { createPinia } from 'pinia';
import router from './router';
import { bootstrapApp } from './app/init';
import App from './App.vue';
import './styles/design-system.css';
import './styles/product-patterns.css';
import { bootTheme } from './styles/theme';

declare global {
  interface Window {
    __SC_ROUTER__?: typeof router;
  }
}

const app = createApp(App);

app.use(createPinia());
app.use(router);

bootTheme();
bootstrapApp();

if (import.meta.env.DEV || import.meta.env.VITE_E2E_ROUTER_HOOK === '1') {
  window.__SC_ROUTER__ = router;
}

app.mount('#app');

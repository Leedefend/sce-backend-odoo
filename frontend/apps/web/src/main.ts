import { createApp } from 'vue';
import { createPinia } from 'pinia';
import router from './router';
import { bootstrapApp } from './app/init';
import App from './App.vue';

const appEnv = String(import.meta.env.VITE_APP_ENV ?? 'dev').trim().toLowerCase();
const shouldNormalizeLoopbackHost =
  typeof window !== 'undefined'
  && window.location.hostname === 'localhost'
  && appEnv !== 'dev'
  && appEnv !== 'local';

if (shouldNormalizeLoopbackHost) {
  const normalizedUrl = new URL(window.location.href);
  normalizedUrl.hostname = '127.0.0.1';
  window.location.replace(normalizedUrl.toString());
} else {
const app = createApp(App);

app.use(createPinia());
app.use(router);

bootstrapApp();

app.mount('#app');
}

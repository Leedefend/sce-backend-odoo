import { createApp } from 'vue';
import { createPinia } from 'pinia';
import router from './router';
import { bootstrapApp, STARTUP_STATUS_EVENT } from './app/init';
import App from './App.vue';
import './styles/index.css';

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
const startupOverlay = typeof document !== 'undefined'
  ? (() => {
      const el = document.createElement('div');
      el.setAttribute('data-startup-overlay', 'true');
      el.style.position = 'fixed';
      el.style.inset = '0';
      el.style.zIndex = '9999';
      el.style.display = 'grid';
      el.style.placeItems = 'center';
      el.style.background = 'linear-gradient(180deg, rgba(247, 243, 239, 0.96), rgba(238, 241, 247, 0.96))';
      el.style.color = '#1f2937';
      el.style.fontFamily = '"Space Grotesk", "IBM Plex Sans", system-ui, sans-serif';
      el.innerHTML = `
        <div style="display:grid;gap:10px;justify-items:center;padding:28px 32px;border:1px solid rgba(15,23,42,.08);border-radius:18px;background:rgba(255,255,255,.88);box-shadow:0 18px 45px rgba(15,23,42,.08);">
          <strong style="font-size:16px;line-height:1.4;">系统正在准备工作区</strong>
          <span data-startup-overlay-message="true" style="font-size:13px;line-height:1.6;color:#6b7280;">正在同步登录上下文与页面启动链…</span>
        </div>
      `;
      document.body.appendChild(el);
      return el;
    })()
  : null;

const removeStartupOverlay = () => {
  startupOverlay?.remove();
};

const updateStartupOverlayMessage = (message: string) => {
  const node = startupOverlay?.querySelector('[data-startup-overlay-message="true"]');
  if (node) node.textContent = message;
};

if (typeof window !== 'undefined') {
  window.addEventListener(STARTUP_STATUS_EVENT, ((event: Event) => {
    const custom = event as CustomEvent<Record<string, unknown>>;
    const status = String(custom.detail?.status || '').trim();
    if (status === 'bootstrapping') {
      updateStartupOverlayMessage('正在同步登录上下文与页面启动链…');
      return;
    }
    if (status === 'error') {
      updateStartupOverlayMessage('启动链较慢，页面将继续尝试加载…');
      window.setTimeout(removeStartupOverlay, 1200);
      return;
    }
    removeStartupOverlay();
  }) as EventListener, { once: false });
}

const app = createApp(App);

app.use(createPinia());
app.use(router);

void bootstrapApp().finally(() => {
  window.setTimeout(removeStartupOverlay, 180);
});

app.mount('#app');
}

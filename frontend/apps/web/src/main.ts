import { createApp } from 'vue';
import { createPinia } from 'pinia';
import router from './router';
import { bootstrapApp } from './app/init';
import App from './App.vue';
import './styles/design-system.css';
import './styles/product-patterns.css';
import { bootTheme } from './styles/theme';
import { installStaleAssetRecovery } from './app/staleAssetRecovery';

installStaleAssetRecovery();

const app = createApp(App);

app.use(createPinia());
app.use(router);

bootTheme();
bootstrapApp();

app.mount('#app');

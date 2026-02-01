import { createApp } from 'vue';
import { createPinia } from 'pinia';
import router from './router';
import { bootstrapApp } from './app/init';
import App from './App.vue';

const app = createApp(App);

app.use(createPinia());
app.use(router);

bootstrapApp();

app.mount('#app');

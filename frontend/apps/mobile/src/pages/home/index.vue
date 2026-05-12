<template>
  <view class="page">
    <view class="header">
      <view>
        <view class="kicker">我的工作</view>
        <view class="title">{{ userName || login || '已登录用户' }}</view>
        <view class="subtitle">{{ companyName || dbName || '智能工程项目管理系统' }}</view>
      </view>
      <button class="logout" @click="logout">退出</button>
    </view>

    <view class="status">
      <view class="status__item">
        <text class="status__label">服务地址</text>
        <text class="status__value">{{ baseUrl || '-' }}</text>
      </view>
      <view class="status__item">
        <text class="status__label">数据库</text>
        <text class="status__value">{{ dbName || '-' }}</text>
      </view>
      <view class="status__item">
        <text class="status__label">登录账号</text>
        <text class="status__value">{{ login || '-' }}</text>
      </view>
    </view>

    <view class="section">
      <view class="section__title">可用入口</view>
      <button
        v-for="app in apps"
        :key="app.id"
        class="app-tab"
        :class="{ 'app-tab--active': app.id === activeAppId }"
        @click="selectApp(app.id)"
      >
        {{ app.label }}
      </button>
      <button
        v-for="entry in navEntries"
        :key="entry.key"
        class="entry"
        @click="openNavEntry(entry)"
      >
        {{ entry.label }}
      </button>
      <view v-if="!navEntries.length" class="empty">当前契约未返回移动端可用入口</view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app';
import { ref } from 'vue';

const baseUrl = ref('');
const dbName = ref('');
const login = ref('');
const userName = ref('');
const companyName = ref('');
const apps = ref<AppEntry[]>([]);
const activeAppId = ref('');
const navEntries = ref<NavEntry[]>([]);

interface AppEntry {
  id: string;
  key: string;
  label: string;
}

interface NavEntry {
  key: string;
  label: string;
  appId: string;
  featureKey: string;
  sceneKey: string;
}

interface ShellContract {
  apps: AppEntry[];
  activeAppId: string;
  navigation: Record<string, unknown>;
  defaultEntry: NavEntry | null;
  defaultOpenTarget: Record<string, unknown>;
}

function readStorage(key: string): string {
  try {
    return String(uni.getStorageSync(key) || '').trim();
  } catch {
    return '';
  }
}

function asDict(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function asList(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function asText(value: unknown, fallback = ''): string {
  const text = String(value || '').trim();
  return text || fallback;
}

function endpoint(): string {
  return `${baseUrl.value}/api/v1/intent?db=${encodeURIComponent(dbName.value)}`;
}

function requestIntent(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
  const token = readStorage('sc_mobile_token');
  return new Promise((resolve, reject) => {
    uni.request({
      url: endpoint(),
      method: 'POST',
      data: payload,
      timeout: 15000,
      header: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
        'X-SC-Client-Type': 'harmony_h5',
      },
      success: (response) => {
        const statusCode = Number(response.statusCode || 0);
        const body = asDict(response.data);
        if (statusCode < 200 || statusCode >= 300) {
          reject(new Error(`request failed: ${statusCode}`));
          return;
        }
        if (body.ok === false) {
          reject(new Error('intent failed'));
          return;
        }
        resolve(body);
      },
      fail: (requestError) => reject(new Error(requestError.errMsg || 'request failed')),
    });
  });
}

function collectNavEntries(data: Record<string, unknown>): NavEntry[] {
  const entries: NavEntry[] = [];
  function walk(rows: unknown[]) {
    rows.forEach((item) => {
      const row = asDict(item);
      const meta = asDict(row.meta);
      const open = asDict(meta.open);
      const appId = asText(meta.app, activeAppId.value);
      const featureKey = asText(meta.feature);
      const sceneKey = asText(open.scene_key || meta.scene_key || row.scene_key);
      const children = asList(row.children);
      if ((sceneKey || featureKey) && children.length === 0) {
        entries.push({
          key: asText(row.key, sceneKey || featureKey),
          label: asText(row.label || row.title, sceneKey || featureKey),
          appId,
          featureKey,
          sceneKey,
        });
      }
      walk(children);
    });
  }
  walk(asList(data.sections));
  return entries.slice(0, 6);
}

function collectApps(data: Record<string, unknown>): AppEntry[] {
  return asList(data.apps)
    .map((item) => {
      const row = asDict(item);
      const meta = asDict(row.meta);
      const id = asText(row.id || meta.app_id || row.app_id || row.key).replace(/^app:/, '');
      return {
        id,
        key: asText(row.key, id),
        label: asText(row.label || row.title, id || '应用'),
      };
    })
    .filter((item) => item.id);
}

function collectShell(data: Record<string, unknown>): ShellContract {
  const defaultEntryRaw = asDict(data.defaultEntry);
  const defaultEntry = asText(defaultEntryRaw.key)
    ? {
        key: asText(defaultEntryRaw.key),
        label: asText(defaultEntryRaw.label, asText(defaultEntryRaw.key)),
        appId: asText(defaultEntryRaw.appId),
        featureKey: asText(defaultEntryRaw.featureKey),
        sceneKey: asText(defaultEntryRaw.sceneKey),
      }
    : null;
  return {
    apps: collectApps(data),
    activeAppId: asText(data.activeAppId),
    navigation: asDict(data.navigation),
    defaultEntry,
    defaultOpenTarget: asDict(data.defaultOpenTarget),
  };
}

async function loadAppsAndNav() {
  if (!baseUrl.value || !dbName.value) return;
  try {
    const response = await requestIntent({
      intent: 'terminal.shell.v2',
      params: {
        client_type: 'harmony_h5',
        delivery_profile: 'mobile_compact',
        max_items: 8,
        max_depth: 2,
      },
    });
    const shell = collectShell(asDict(response.data));
    apps.value = shell.apps;
    activeAppId.value = shell.activeAppId || shell.apps[0]?.id || 'workspace';
    const entries = collectNavEntries(shell.navigation);
    navEntries.value = entries.length ? entries : (shell.defaultEntry ? [shell.defaultEntry] : []);
  } catch {
    apps.value = [];
    activeAppId.value = '';
    navEntries.value = [];
  }
}

async function loadMobileNav(appId: string) {
  if (!baseUrl.value || !dbName.value || !appId) return;
  try {
    const response = await requestIntent({
      intent: 'app.nav',
      params: {
        app: appId,
        client_type: 'harmony_h5',
        delivery_profile: 'mobile_compact',
        max_items: 8,
        max_depth: 2,
      },
    });
    navEntries.value = collectNavEntries(asDict(response.data));
  } catch {
    navEntries.value = [];
  }
}

function selectApp(appId: string) {
  if (!appId || appId === activeAppId.value) return;
  activeAppId.value = appId;
  void loadMobileNav(appId);
}

function loadSession() {
  const token = readStorage('sc_mobile_token');
  if (!token) {
    uni.reLaunch({ url: '/pages/login/index' });
    return;
  }
  baseUrl.value = readStorage('sc_mobile_base_url');
  dbName.value = readStorage('sc_mobile_db');
  login.value = readStorage('sc_mobile_login');
  userName.value = readStorage('sc_mobile_user_name');
  companyName.value = readStorage('sc_mobile_company_name');
  void loadAppsAndNav();
}

async function openNavEntry(entry: NavEntry) {
  try {
    const response = await requestIntent({
      intent: 'app.open',
      params: {
        app: entry.appId || activeAppId.value,
        feature: entry.featureKey,
        client_type: 'harmony_h5',
        delivery_profile: 'mobile_compact',
      },
    });
    const data = asDict(response.data);
    const query: string[] = [];
    const subject = asText(data.subject);
    if (subject) query.push(`subject=${encodeURIComponent(subject)}`);
    const menuId = asText(data.menu_id || (subject === 'menu' ? data.id : ''));
    if (menuId) query.push(`menu_id=${encodeURIComponent(menuId)}`);
    const actionId = asText(data.action_id || (subject === 'action' ? data.id : ''));
    if (actionId) query.push(`action_id=${encodeURIComponent(actionId)}`);
    const model = asText(data.model);
    if (model) query.push(`model=${encodeURIComponent(model)}`);
    const sceneKey = asText(data.scene_key || entry.sceneKey);
    if (sceneKey) query.push(`scene_key=${encodeURIComponent(sceneKey)}`);
    uni.navigateTo({ url: `/pages/contract/index${query.length ? `?${query.join('&')}` : ''}` });
  } catch {
    uni.showToast({ title: '入口不可用', icon: 'none' });
  }
}

function logout() {
  uni.removeStorageSync('sc_mobile_token');
  uni.removeStorageSync('sc_mobile_login');
  uni.removeStorageSync('sc_mobile_user_name');
  uni.removeStorageSync('sc_mobile_company_name');
  uni.reLaunch({ url: '/pages/login/index' });
}

onShow(loadSession);
</script>

<style scoped>
.page {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 42rpx 30rpx;
  background: var(--sc-mobile-bg);
  color: var(--sc-mobile-text-primary);
}

.header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24rpx;
  margin-bottom: 32rpx;
}

.kicker {
  color: #5d7188;
  font-size: 24rpx;
  font-weight: 600;
}

.title {
  margin-top: 8rpx;
  color: var(--sc-mobile-text-primary);
  font-size: 40rpx;
  font-weight: 700;
  line-height: 1.2;
}

.subtitle {
  margin-top: 10rpx;
  color: var(--sc-mobile-text-secondary);
  font-size: 24rpx;
}

.logout {
  width: 112rpx;
  height: 58rpx;
  margin: 0;
  border-radius: 8rpx;
  background: var(--sc-mobile-panel);
  color: #344154;
  font-size: 24rpx;
  line-height: 58rpx;
}

.status,
.section {
  border: 1rpx solid var(--sc-mobile-border);
  border-radius: 8rpx;
  background: var(--sc-mobile-panel);
}

.status {
  margin-bottom: 24rpx;
}

.status__item {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  padding: 22rpx 24rpx;
  border-bottom: 1rpx solid #edf1f5;
}

.status__item:last-child {
  border-bottom: 0;
}

.status__label {
  color: #667789;
  font-size: 22rpx;
}

.status__value {
  color: var(--sc-mobile-text-primary);
  font-size: 26rpx;
  line-height: 1.35;
  word-break: break-all;
}

.section {
  padding: 24rpx;
}

.section__title {
  margin-bottom: 18rpx;
  color: #344154;
  font-size: 26rpx;
  font-weight: 700;
}

.app-tab {
  display: inline-block;
  width: auto;
  min-width: 132rpx;
  height: 58rpx;
  margin: 0 14rpx 16rpx 0;
  padding: 0 18rpx;
  border: 1rpx solid #cbd6e2;
  border-radius: 8rpx;
  background: var(--sc-mobile-panel);
  color: #344154;
  font-size: 23rpx;
  line-height: 58rpx;
}

.app-tab--active {
  background: var(--sc-mobile-primary);
  color: var(--sc-mobile-panel);
  border-color: var(--sc-mobile-primary);
}

.entry {
  height: 78rpx;
  margin-top: 14rpx;
  border-radius: 8rpx;
  background: var(--sc-mobile-primary);
  color: var(--sc-mobile-panel);
  font-size: 26rpx;
  line-height: 78rpx;
}

.entry:first-of-type {
  margin-top: 0;
}

.empty {
  color: #667789;
  font-size: 24rpx;
  line-height: 1.5;
}
</style>

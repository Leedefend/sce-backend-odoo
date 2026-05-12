<template>
  <view class="page">
    <view class="brand">
      <view class="brand__mark">SC</view>
      <view>
        <view class="brand__name">智能工程项目管理系统</view>
        <view class="brand__caption">项目、合同、资金与风险协同管理</view>
      </view>
    </view>

    <view class="panel">
      <view class="panel__header">
        <view class="panel__title">登录</view>
        <view class="panel__subtitle">欢迎使用系统</view>
      </view>

      <view class="form">
        <label class="field">
          <text class="field__label">服务地址</text>
          <input
            v-model="baseUrl"
            class="field__input"
            :disabled="loading"
            placeholder="http://服务器地址:8071"
          />
        </label>

        <label class="field">
          <text class="field__label">数据库</text>
          <input
            v-model="dbName"
            class="field__input"
            :disabled="loading"
            placeholder="sc_prod_sim"
          />
        </label>

        <label class="field">
          <text class="field__label">账号</text>
          <input
            v-model="login"
            class="field__input"
            :disabled="loading"
            placeholder="请输入账号"
          />
        </label>

        <label class="field">
          <text class="field__label">密码</text>
          <input
            v-model="password"
            class="field__input"
            :disabled="loading"
            password
            placeholder="请输入密码"
          />
        </label>

        <view v-if="error" class="error">{{ error }}</view>

        <button class="submit" :disabled="loading" @click="submitLogin">
          {{ loading ? '登录中...' : '进入系统' }}
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const DEFAULT_BACKEND_PROXY_PORT = '8071';
const DEFAULT_DB = 'sc_prod_sim';

const baseUrl = ref(readStorage('sc_mobile_base_url') || defaultBaseUrl());
const dbName = ref(readStorage('sc_mobile_db') || DEFAULT_DB);
const login = ref('');
const password = ref('');
const loading = ref(false);
const error = ref('');

function readStorage(key: string): string {
  try {
    return String(uni.getStorageSync(key) || '').trim();
  } catch {
    return '';
  }
}

function defaultBaseUrl(): string {
  const locationLike = (globalThis as typeof globalThis & { location?: { protocol?: string; hostname?: string } }).location;
  const protocol = String(locationLike?.protocol || 'http:').replace(/:$/, '') || 'http';
  const hostname = String(locationLike?.hostname || '').trim();
  if (hostname && hostname !== 'localhost' && hostname !== '127.0.0.1') {
    return `${protocol}://${hostname}:${DEFAULT_BACKEND_PROXY_PORT}`;
  }
  return `http://127.0.0.1:${DEFAULT_BACKEND_PROXY_PORT}`;
}

function normalizeBaseUrl(value: string): string {
  return value.trim().replace(/\/+$/, '');
}

function normalizeError(err: unknown): string {
  if (err instanceof Error && err.message) {
    const lower = err.message.toLowerCase();
    if (lower.includes('401') || lower.includes('password') || lower.includes('wrong') || lower.includes('invalid')) {
      return '账号或密码错误，请重新输入';
    }
    if (lower.includes('timeout') || lower.includes('request') || lower.includes('network')) {
      return '网络异常，请检查服务地址';
    }
  }
  return '登录失败，请稍后重试';
}

function requestLogin(endpoint: string, payload: Record<string, unknown>): Promise<Record<string, unknown>> {
  return new Promise((resolve, reject) => {
    uni.request({
      url: endpoint,
      method: 'POST',
      data: payload,
      timeout: 15000,
      header: {
        'Content-Type': 'application/json',
        'X-Anonymous-Intent': '1',
      },
      success: (response) => {
        const statusCode = Number(response.statusCode || 0);
        const body = response.data as Record<string, unknown>;
        if (statusCode < 200 || statusCode >= 300) {
          reject(new Error(`request failed: ${statusCode}`));
          return;
        }
        if (!body || body.ok === false) {
          const message = typeof body?.error === 'string' ? body.error : 'login failed';
          reject(new Error(message));
          return;
        }
        resolve(body);
      },
      fail: (requestError) => reject(new Error(requestError.errMsg || 'request failed')),
    });
  });
}

async function submitLogin() {
  error.value = '';
  const normalizedBaseUrl = normalizeBaseUrl(baseUrl.value);
  const normalizedDb = dbName.value.trim();
  const normalizedLogin = login.value.trim();
  if (!normalizedBaseUrl || !normalizedDb || !normalizedLogin || !password.value) {
    error.value = '请填写服务地址、数据库、账号和密码';
    return;
  }

  loading.value = true;
  try {
    const endpoint = `${normalizedBaseUrl}/api/v1/intent?db=${encodeURIComponent(normalizedDb)}`;
    const response = await requestLogin(endpoint, {
      intent: 'login',
      params: {
        db: normalizedDb,
        login: normalizedLogin,
        password: password.value,
      },
    });
    const data = (response.data || {}) as Record<string, unknown>;
    const session = (data.session || {}) as Record<string, unknown>;
    const user = (data.user || {}) as Record<string, unknown>;
    const token = String(data.token || session.token || '').trim();
    uni.setStorageSync('sc_mobile_base_url', normalizedBaseUrl);
    uni.setStorageSync('sc_mobile_db', normalizedDb);
    uni.setStorageSync('sc_mobile_token', token);
    uni.setStorageSync('sc_mobile_login', normalizedLogin);
    uni.setStorageSync('sc_mobile_user_name', String(user.name || normalizedLogin));
    uni.setStorageSync('sc_mobile_company_name', String(user.company_name || ''));
    uni.reLaunch({ url: '/pages/home/index' });
  } catch (err) {
    error.value = normalizeError(err);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 56rpx 32rpx 40rpx;
  background: var(--sc-mobile-bg);
  color: var(--sc-mobile-text-primary);
}

.brand {
  display: flex;
  align-items: center;
  gap: 18rpx;
  margin-bottom: 54rpx;
}

.brand__mark {
  width: 72rpx;
  height: 72rpx;
  border-radius: 10rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #26364a;
  color: var(--sc-mobile-panel);
  font-size: 26rpx;
  font-weight: 700;
}

.brand__name {
  color: var(--sc-mobile-text-primary);
  font-size: 34rpx;
  font-weight: 700;
  line-height: 1.25;
}

.brand__caption {
  margin-top: 8rpx;
  color: var(--sc-mobile-text-secondary);
  font-size: 24rpx;
  line-height: 1.35;
}

.panel {
  border: 1rpx solid var(--sc-mobile-border);
  border-radius: 8rpx;
  background: var(--sc-mobile-panel);
  padding: 34rpx 30rpx 32rpx;
}

.panel__header {
  margin-bottom: 30rpx;
}

.panel__title {
  color: var(--sc-mobile-text-primary);
  font-size: 40rpx;
  font-weight: 700;
  line-height: 1.2;
}

.panel__subtitle {
  margin-top: 8rpx;
  color: #667789;
  font-size: 24rpx;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.field__label {
  color: #344154;
  font-size: 24rpx;
  font-weight: 600;
}

.field__input {
  display: block;
  width: 100%;
  height: 82rpx;
  min-height: 82rpx;
  box-sizing: border-box;
  border: 1rpx solid #cfd8e3;
  border-radius: 8rpx;
  padding: 0 22rpx;
  background: #fbfcfd;
  color: var(--sc-mobile-text-primary);
  font-size: 28rpx;
  line-height: 82rpx;
}

.error {
  border: 1rpx solid #f0c8c8;
  border-radius: 8rpx;
  padding: 18rpx 20rpx;
  background: #fff4f4;
  color: #b42318;
  font-size: 24rpx;
  line-height: 1.4;
}

.submit {
  height: 86rpx;
  margin-top: 8rpx;
  border-radius: 8rpx;
  background: var(--sc-mobile-primary);
  color: var(--sc-mobile-panel);
  font-size: 28rpx;
  font-weight: 700;
  line-height: 86rpx;
}

.submit[disabled] {
  background: #93a1b3;
  color: #f7f9fb;
}
</style>

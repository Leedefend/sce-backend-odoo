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
      <button class="entry" @click="openContractRuntime">合同运行页</button>
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

function readStorage(key: string): string {
  try {
    return String(uni.getStorageSync(key) || '').trim();
  } catch {
    return '';
  }
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
}

function openContractRuntime() {
  uni.navigateTo({ url: '/pages/contract/index' });
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
  background: #f4f6f8;
  color: #17202a;
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
  color: #17202a;
  font-size: 40rpx;
  font-weight: 700;
  line-height: 1.2;
}

.subtitle {
  margin-top: 10rpx;
  color: #607083;
  font-size: 24rpx;
}

.logout {
  width: 112rpx;
  height: 58rpx;
  margin: 0;
  border-radius: 8rpx;
  background: #ffffff;
  color: #344154;
  font-size: 24rpx;
  line-height: 58rpx;
}

.status,
.section {
  border: 1rpx solid #dfe5ec;
  border-radius: 8rpx;
  background: #ffffff;
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
  color: #17202a;
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

.entry {
  height: 78rpx;
  border-radius: 8rpx;
  background: #1f3a5f;
  color: #ffffff;
  font-size: 26rpx;
  line-height: 78rpx;
}
</style>

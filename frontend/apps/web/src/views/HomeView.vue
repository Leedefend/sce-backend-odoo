<template>
  <main class="page">
    <section class="card">
      <header>
        <h1>App Initialized</h1>
        <p>User: {{ userName }}</p>
        <p class="meta">Menu items: {{ menuCount }}</p>
      </header>
      
      <!-- A3: 根菜单不匹配错误面板 -->
      <div v-if="showRootMismatchError" class="root-mismatch-error">
        <h2>⚠️ Root Menu Mismatch Error</h2>
        <div class="error-details">
          <p><strong>Expected root:</strong> smart_construction_core.menu_sc_root</p>
          <p><strong>Got root:</strong> {{ detectedRootName }}</p>
          <p><strong>Effective DB:</strong> {{ effectiveDb }}</p>
          <p><strong>First 3 menu items:</strong></p>
          <ul>
            <li v-for="(item, index) in firstThreeMenus" :key="index">
              {{ index + 1 }}. "{{ item.name }}" (xmlid: {{ item.xmlid || 'N/A' }}, id: {{ item.id || 'N/A' }})
            </li>
          </ul>
        </div>
        <div class="debug-actions">
          <button class="secondary" @click="reloadApp">Reload App Init</button>
          <button class="secondary" @click="dumpMenu">Dump Menu Details</button>
        </div>
      </div>
      
      <div class="menu">
        <h2>Menu ({{ menuCount }} items)</h2>
        <!-- 简单测试：直接显示菜单项名称 -->
        <div v-if="menuCount > 0" class="simple-menu">
          <h3>简单菜单列表（测试用）</h3>
          <div v-for="(item, index) in menuTree" :key="item.key || index" class="menu-item">
            <strong>{{ index + 1 }}.</strong> 
            {{ item.title || item.name || item.label || 'Unnamed' }}
            <span class="menu-id">(ID: {{ item.menu_id }})</span>
            <span v-if="item.children?.length" class="children-count"> - {{ item.children.length }} 个子菜单</span>
            <span v-else class="children-count"> - 无子菜单</span>
          </div>
        </div>
        <MenuTree :nodes="menuTree" @select="handleSelect" />
        <div v-if="menuCount === 0" class="empty">
          <p>No menu data received. Check app.init response.</p>
          <div v-if="debugIntent" class="debug-actions">
            <button class="secondary" @click="reloadApp">Reload App Init</button>
            <button class="secondary" @click="fetchNav">Fetch Nav</button>
            <button class="secondary" @click="dumpMenu">Dump Menu</button>
          </div>
        </div>
      </div>
      <button class="logout" @click="logout">Logout</button>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useSessionStore } from '../stores/session';
import MenuTree from '../components/MenuTree.vue';
import { openAction } from '../services/action_service';

const router = useRouter();
const session = useSessionStore();

const userName = computed(() => session.user?.name ?? 'unknown');
const menuTree = computed(() => session.menuTree);
const menuCount = computed(() => menuTree.value.length);
const debugIntent =
  import.meta.env.DEV ||
  localStorage.getItem('DEBUG_INTENT') === '1' ||
  new URLSearchParams(window.location.search).get('debug') === '1';

// A3: 根菜单不匹配检测
const effectiveDb = ref<string>('N/A');
const detectedRootName = ref<string>('N/A');
const firstThreeMenus = ref<any[]>([]);

const showRootMismatchError = computed(() => {
  if (!debugIntent) return false;
  // 检查是否是Odoo原生应用菜单
  if (menuTree.value.length === 0) return false;
  
  const firstMenu = menuTree.value[0];
  const firstMenuName = firstMenu.title || firstMenu.name || firstMenu.label || '';
  
  // Odoo原生应用菜单的典型名称
  const odooNativeMenuNames = [
    '讨论', '待办', '仪表板', '发票', '采购', '库存', '应用', '设置',
    'Discuss', 'To-do', 'Dashboard', 'Invoicing', 'Purchase', 'Inventory', 'Apps', 'Settings'
  ];
  
  return odooNativeMenuNames.includes(firstMenuName);
});

// 检测根菜单信息
function detectRootInfo() {
  if (menuTree.value.length > 0) {
    const firstMenu = menuTree.value[0];
    detectedRootName.value = firstMenu.title || firstMenu.name || firstMenu.label || 'Unknown';
    firstThreeMenus.value = menuTree.value.slice(0, 3).map(item => ({
      name: item.title || item.name || item.label || 'Unnamed',
      xmlid: item.xmlid || 'N/A',
      id: item.menu_id || (item as any).id || 'N/A'
    }));
  }
}

// 在菜单变化时检测
onMounted(() => {
  detectRootInfo();
});

function handleSelect(node: { meta?: { action_id?: number } } & { menu_id?: number }) {
  if (node.meta?.action_id) {
    openAction(router, node.meta, node.menu_id);
  }
}

async function reloadApp() {
  await session.loadAppInit();
}

async function fetchNav() {
  await session.loadNavFallback();
}

function dumpMenu() {
  if (!debugIntent) return;
  console.group('[A3] 菜单详细诊断');
  
  // 打印菜单树
  console.info('[debug] menuTree', session.menuTree);
  
  // 详细打印每个菜单项
  console.info('[debug] 菜单项详情:');
  session.menuTree.forEach((item, index) => {
    console.info(`  [${index}]`, {
      key: item.key,
      name: item.name,
      label: item.label,
      title: item.title,
      menu_id: item.menu_id,
      id: (item as any).id,
      xmlid: item.xmlid || 'N/A',
      children: item.children?.length || 0,
      meta: item.meta
    });
  });
  
  // 检查是否是Odoo原生菜单
  const firstMenu = session.menuTree[0];
  if (firstMenu) {
    const firstMenuName = firstMenu.title || firstMenu.name || firstMenu.label || '';
    const odooNativeMenuNames = [
      '讨论', '待办', '仪表板', '发票', '采购', '库存', '应用', '设置',
      'Discuss', 'To-do', 'Dashboard', 'Invoicing', 'Purchase', 'Inventory', 'Apps', 'Settings'
    ];
    
    if (odooNativeMenuNames.includes(firstMenuName)) {
      console.warn('⚠️ 检测到Odoo原生应用菜单作为根菜单！');
      console.warn('   第一个菜单名称:', firstMenuName);
      console.warn('   这表示后端可能没有使用 smart_construction_core.menu_sc_root 作为根');
    } else {
      console.info('✅ 第一个菜单不是Odoo原生应用菜单:', firstMenuName);
    }
  }
  
  // 打印完整的app.init响应数据
  console.info('[debug] Full app.init response nav data:', JSON.stringify(session.menuTree, null, 2));
  
  console.groupEnd();
}

async function logout() {
  await session.logout();
  router.push('/login');
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: #f3f4f6;
  font-family: "IBM Plex Sans", system-ui, sans-serif;
}

.card {
  width: min(720px, 92vw);
  background: white;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.12);
  display: grid;
  gap: 16px;
}

.menu {
  border-top: 1px solid #e2e8f0;
  padding-top: 12px;
  display: grid;
  gap: 12px;
}

.logout {
  padding: 10px 14px;
  border: none;
  border-radius: 10px;
  background: #1f2937;
  color: white;
  cursor: pointer;
}

.meta {
  color: #64748b;
  font-size: 14px;
}

.empty {
  border: 1px dashed #cbd5f5;
  padding: 12px;
  border-radius: 12px;
  background: #f8fafc;
  color: #475569;
  font-size: 14px;
}

.debug-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.secondary {
  padding: 8px 12px;
  border: 1px solid #cbd5f5;
  border-radius: 10px;
  background: white;
  cursor: pointer;
  color: #1f2937;
}

.simple-menu {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
  background: #f8fafc;
}

.menu-item {
  padding: 6px 0;
  border-bottom: 1px solid #e2e8f0;
}

.menu-item:last-child {
  border-bottom: none;
}

.simple-menu h3 {
  margin-top: 0;
  margin-bottom: 12px;
  color: #334155;
  font-size: 16px;
}

.menu-id {
  font-size: 12px;
  color: #64748b;
  margin-left: 8px;
}

.children-count {
  font-size: 12px;
  color: #94a3b8;
  font-style: italic;
}

/* A3: 根菜单不匹配错误面板样式 */
.root-mismatch-error {
  border: 2px solid #ef4444;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 20px;
  background: #fef2f2;
}

.root-mismatch-error h2 {
  color: #dc2626;
  margin-top: 0;
  margin-bottom: 12px;
  font-size: 18px;
}

.error-details {
  background: white;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  border: 1px solid #fecaca;
}

.error-details p {
  margin: 6px 0;
  color: #374151;
}

.error-details ul {
  margin: 8px 0 0 20px;
  padding: 0;
}

.error-details li {
  margin: 4px 0;
  color: #4b5563;
  font-size: 14px;
}
</style>

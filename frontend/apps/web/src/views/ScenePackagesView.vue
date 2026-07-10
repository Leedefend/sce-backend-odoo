<template>
  <section class="scene-packages">
    <header v-if="pageSectionEnabled('header', true) && pageSectionTagIs('header', 'header')" class="header" :style="pageSectionStyle('header')">
      <div>
        <h2>{{ pageText('title', '场景能力包') }}</h2>
        <p>{{ pageText('subtitle', '导入、导出与审阅已安装的 Scene 能力包。') }}</p>
      </div>
      <button
        v-for="action in headerActions"
        :key="action.key"
        class="secondary"
        :disabled="busy"
        @click="executeHeaderAction(action.key)"
      >
        {{ action.label }}
      </button>
    </header>

    <StatusPanel
      v-if="pageSectionEnabled('status_loading', true) && pageSectionTagIs('status_loading', 'section') && busy && !packages.length"
      :title="pageText('loading_title', '正在加载能力包')"
      variant="info"
      :style="pageSectionStyle('status_loading')"
    />
    <StatusPanel
      v-else-if="pageSectionEnabled('status_error', true) && pageSectionTagIs('status_error', 'section') && errorText"
      :title="pageText('error_title', '能力包操作失败')"
      :message="errorText"
      :trace-id="traceId || undefined"
      variant="error"
      :on-retry="loadPackages"
      :style="pageSectionStyle('status_error')"
    />

    <section
      v-else-if="pageSectionEnabled('content', true) && pageSectionTagIs('content', 'section')"
      class="content"
      :style="pageSectionStyle('content')"
    >
      <article
        v-if="pageSectionEnabled('installed_packages', true) && pageSectionTagIs('installed_packages', 'section')"
        class="card"
        :style="pageSectionStyle('installed_packages')"
      >
        <h3>已安装能力包</h3>
        <p class="hint">共 {{ packages.length }} 个</p>
        <pre>{{ JSON.stringify(packages, null, 2) }}</pre>
      </article>

      <article
        v-if="pageSectionEnabled('import_package', true) && pageSectionTagIs('import_package', 'section')"
        class="card"
        :style="pageSectionStyle('import_package')"
      >
        <h3>导入能力包</h3>
        <label>
          <span>能力包 JSON</span>
          <textarea v-model="importText" rows="10" placeholder="粘贴场景能力包 JSON"></textarea>
        </label>
        <label>
          <span>导入策略</span>
          <select v-model="importStrategy">
            <option value="skip_existing">跳过已存在项</option>
            <option value="override_existing">覆盖已存在项</option>
            <option value="rename_on_conflict">冲突时重命名</option>
          </select>
        </label>
        <label>
          <span>操作说明（必填）</span>
          <input v-model="importReason" type="text" placeholder="填写本次导入原因" />
        </label>
        <div class="actions">
          <button class="secondary" :disabled="busy" @click="runDryRun">预检查</button>
          <button class="danger" :disabled="busy" @click="runImport">导入</button>
        </div>
        <pre v-if="dryRunResult">{{ JSON.stringify(dryRunResult, null, 2) }}</pre>
      </article>

      <article
        v-if="pageSectionEnabled('export_package', true) && pageSectionTagIs('export_package', 'section')"
        class="card"
        :style="pageSectionStyle('export_package')"
      >
        <h3>导出能力包</h3>
        <label>
          <span>能力包名称</span>
          <input v-model="exportName" type="text" placeholder="例如：construction-default" />
        </label>
        <label>
          <span>能力包版本</span>
          <input v-model="exportVersion" type="text" placeholder="例如：1.0.0" />
        </label>
        <label>
          <span>发布通道</span>
          <select v-model="exportChannel">
            <option value="stable">稳定版</option>
            <option value="beta">灰度版</option>
            <option value="dev">开发版</option>
          </select>
        </label>
        <label>
          <span>操作说明</span>
          <input v-model="exportReason" type="text" placeholder="填写本次导出原因" />
        </label>
        <div class="actions">
          <button class="secondary" :disabled="busy" @click="runExport">导出</button>
        </div>
        <pre v-if="exportResult">{{ JSON.stringify(exportResult, null, 2) }}</pre>
      </article>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import StatusPanel from '../components/StatusPanel.vue';
import { usePageContract } from '../app/pageContract';
import { executePageContractAction } from '../app/pageContractActionRuntime';
import {
  scenePackageDryRunImport,
  scenePackageExport,
  scenePackageImport,
  scenePackageList,
} from '../api/scene';
import type { SceneChannel, ScenePackageDryRunResult, ScenePackageInfo } from '../contracts/scene';

const busy = ref(false);
const errorText = ref('');
const traceId = ref('');
const packages = ref<readonly ScenePackageInfo[]>([]);

const importText = ref('');
const importStrategy = ref<'skip_existing' | 'override_existing' | 'rename_on_conflict'>('skip_existing');
const importReason = ref('能力包导入');
const dryRunResult = ref<ScenePackageDryRunResult | null>(null);

const exportName = ref('scene-package');
const exportVersion = ref('1.0.0');
const exportChannel = ref<SceneChannel>('stable');
const exportReason = ref('能力包导出');
const exportResult = ref<Record<string, unknown> | null>(null);
const router = useRouter();
const pageContract = usePageContract('scene_packages');
const pageText = pageContract.text;
const pageActionIntent = pageContract.actionIntent;
const pageActionTarget = pageContract.actionTarget;
const pageGlobalActions = pageContract.globalActions;
const pageSectionEnabled = pageContract.sectionEnabled;
const pageSectionStyle = pageContract.sectionStyle;
const pageSectionTagIs = pageContract.sectionTagIs;
const headerActions = computed(() => pageGlobalActions.value);

function parsePackageJson(): Record<string, unknown> {
  const raw = importText.value.trim();
  if (!raw) {
    throw new Error('请先粘贴能力包 JSON');
  }
  const payload = JSON.parse(raw) as unknown;
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    throw new Error('能力包 JSON 必须是对象结构');
  }
  return payload as Record<string, unknown>;
}

async function loadPackages() {
  busy.value = true;
  errorText.value = '';
  try {
    const res = await scenePackageList();
    packages.value = Array.isArray(res.data.items) ? res.data.items : [];
    traceId.value = res.traceId || '';
  } catch (err) {
    errorText.value = err instanceof Error ? err.message : pageText('error_load_failed', '能力包加载失败');
    if (err && typeof err === 'object' && 'traceId' in err) {
      traceId.value = String((err as { traceId?: string }).traceId || '');
    }
  } finally {
    busy.value = false;
  }
}

async function runDryRun() {
  busy.value = true;
  errorText.value = '';
  dryRunResult.value = null;
  try {
    const pkg = parsePackageJson();
    const res = await scenePackageDryRunImport({ package: pkg });
    dryRunResult.value = res.data;
    traceId.value = res.traceId || '';
  } catch (err) {
    errorText.value = err instanceof Error ? err.message : pageText('error_dry_run_failed', '能力包预检查失败');
    if (err && typeof err === 'object' && 'traceId' in err) {
      traceId.value = String((err as { traceId?: string }).traceId || '');
    }
  } finally {
    busy.value = false;
  }
}

async function runImport() {
  const reason = importReason.value.trim();
  if (!reason) {
    errorText.value = pageText('error_reason_required', '请填写导入原因');
    return;
  }
  busy.value = true;
  errorText.value = '';
  try {
    const pkg = parsePackageJson();
    const ok = window.confirm('确认导入场景能力包？');
    if (!ok) {
      busy.value = false;
      return;
    }
    const res = await scenePackageImport({ package: pkg, strategy: importStrategy.value, reason });
    traceId.value = res.traceId || '';
    await loadPackages();
  } catch (err) {
    errorText.value = err instanceof Error ? err.message : pageText('error_import_failed', '能力包导入失败');
    if (err && typeof err === 'object' && 'traceId' in err) {
      traceId.value = String((err as { traceId?: string }).traceId || '');
    }
  } finally {
    busy.value = false;
  }
}

async function runExport() {
  busy.value = true;
  errorText.value = '';
  exportResult.value = null;
  try {
    const res = await scenePackageExport({
      package_name: exportName.value.trim(),
      package_version: exportVersion.value.trim(),
      scene_channel: exportChannel.value,
      reason: exportReason.value.trim() || '能力包导出',
    });
    exportResult.value = res.data.package;
    traceId.value = res.traceId || '';
  } catch (err) {
    errorText.value = err instanceof Error ? err.message : pageText('error_export_failed', '能力包导出失败');
    if (err && typeof err === 'object' && 'traceId' in err) {
      traceId.value = String((err as { traceId?: string }).traceId || '');
    }
  } finally {
    busy.value = false;
  }
}

onMounted(loadPackages);

async function executeHeaderAction(actionKey: string) {
  const handled = await executePageContractAction({
    actionKey,
    router,
    actionIntent: pageActionIntent,
    actionTarget: pageActionTarget,
    onRefresh: loadPackages,
    onFallback: async (key) => {
      if (key === 'refresh_page') {
        await loadPackages();
        return true;
      }
      return false;
    },
  });
  if (!handled && actionKey === 'refresh_page') {
    await loadPackages();
  }
}
</script>

<style scoped>
.scene-packages {
  display: grid;
  gap: 16px;
}

.header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.content {
  display: grid;
  gap: 16px;
}

.card {
  background: var(--sc-app-panel);
  border-radius: 12px;
  padding: 16px;
  box-shadow: var(--sc-app-shadow);
  display: grid;
  gap: 10px;
}

.hint {
  color: var(--sc-semantic-text-muted);
}

label {
  display: grid;
  gap: 6px;
}

input,
select,
textarea {
  border: 1px solid var(--sc-app-border-strong);
  border-radius: 8px;
  padding: 8px 10px;
}

.actions {
  display: flex;
  gap: 10px;
}

button {
  border: 0;
  border-radius: 8px;
  padding: 8px 12px;
  cursor: pointer;
}

button.secondary {
  background: var(--sc-app-muted-bg);
}

button.danger {
  background: var(--sc-app-danger-text);
  color: var(--sc-semantic-text-on-interactive);
}

pre {
  background: var(--sc-app-muted-bg);
  border-radius: 8px;
  padding: 10px;
  overflow: auto;
}
</style>

<template>
  <section class="scene-packages">
    <header class="header">
      <div>
        <h2>Scene Packages</h2>
        <p>导入、导出与审阅已安装的 Scene 能力包。</p>
      </div>
      <button class="secondary" :disabled="busy" @click="loadPackages">Refresh</button>
    </header>

    <StatusPanel v-if="busy && !packages.length" title="Loading packages..." variant="info" />
    <StatusPanel
      v-else-if="errorText"
      title="Package operation failed"
      :message="errorText"
      :trace-id="traceId || undefined"
      variant="error"
      :on-retry="loadPackages"
    />

    <section v-else class="content">
      <article class="card">
        <h3>Installed Packages</h3>
        <p class="hint">count: {{ packages.length }}</p>
        <pre>{{ JSON.stringify(packages, null, 2) }}</pre>
      </article>

      <article class="card">
        <h3>Import Package</h3>
        <label>
          <span>Package JSON</span>
          <textarea v-model="importText" rows="10" placeholder="Paste scene package json"></textarea>
        </label>
        <label>
          <span>Strategy</span>
          <select v-model="importStrategy">
            <option value="skip_existing">skip_existing</option>
            <option value="override_existing">override_existing</option>
            <option value="rename_on_conflict">rename_on_conflict</option>
          </select>
        </label>
        <label>
          <span>Reason (required)</span>
          <input v-model="importReason" type="text" placeholder="input reason" />
        </label>
        <div class="actions">
          <button class="secondary" :disabled="busy" @click="runDryRun">Dry Run</button>
          <button class="danger" :disabled="busy" @click="runImport">Import</button>
        </div>
        <pre v-if="dryRunResult">{{ JSON.stringify(dryRunResult, null, 2) }}</pre>
      </article>

      <article class="card">
        <h3>Export Package</h3>
        <label>
          <span>Package Name</span>
          <input v-model="exportName" type="text" placeholder="example: construction-default" />
        </label>
        <label>
          <span>Package Version</span>
          <input v-model="exportVersion" type="text" placeholder="example: 1.0.0" />
        </label>
        <label>
          <span>Scene Channel</span>
          <select v-model="exportChannel">
            <option value="stable">stable</option>
            <option value="beta">beta</option>
            <option value="dev">dev</option>
          </select>
        </label>
        <label>
          <span>Reason</span>
          <input v-model="exportReason" type="text" placeholder="scene package export" />
        </label>
        <div class="actions">
          <button class="secondary" :disabled="busy" @click="runExport">Export</button>
        </div>
        <pre v-if="exportResult">{{ JSON.stringify(exportResult, null, 2) }}</pre>
      </article>
    </section>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import StatusPanel from '../components/StatusPanel.vue';
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
const importReason = ref('phase10.6 package import');
const dryRunResult = ref<ScenePackageDryRunResult | null>(null);

const exportName = ref('scene-package');
const exportVersion = ref('1.0.0');
const exportChannel = ref<SceneChannel>('stable');
const exportReason = ref('phase10.6 package export');
const exportResult = ref<Record<string, unknown> | null>(null);

function parsePackageJson(): Record<string, unknown> {
  const raw = importText.value.trim();
  if (!raw) {
    throw new Error('package json is required');
  }
  const payload = JSON.parse(raw) as unknown;
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    throw new Error('package json must be object');
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
    errorText.value = err instanceof Error ? err.message : 'load packages failed';
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
    errorText.value = err instanceof Error ? err.message : 'dry-run failed';
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
    errorText.value = 'reason is required for import';
    return;
  }
  busy.value = true;
  errorText.value = '';
  try {
    const pkg = parsePackageJson();
    const ok = window.confirm('Confirm import scene package?');
    if (!ok) {
      busy.value = false;
      return;
    }
    const res = await scenePackageImport({ package: pkg, strategy: importStrategy.value, reason });
    traceId.value = res.traceId || '';
    await loadPackages();
  } catch (err) {
    errorText.value = err instanceof Error ? err.message : 'import failed';
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
      reason: exportReason.value.trim() || 'scene package export',
    });
    exportResult.value = res.data.package;
    traceId.value = res.traceId || '';
  } catch (err) {
    errorText.value = err instanceof Error ? err.message : 'export failed';
    if (err && typeof err === 'object' && 'traceId' in err) {
      traceId.value = String((err as { traceId?: string }).traceId || '');
    }
  } finally {
    busy.value = false;
  }
}

onMounted(loadPackages);
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
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
  display: grid;
  gap: 10px;
}

.hint {
  color: #6b7280;
}

label {
  display: grid;
  gap: 6px;
}

input,
select,
textarea {
  border: 1px solid #d1d5db;
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
  background: #e2e8f0;
}

button.danger {
  background: #dc2626;
  color: #fff;
}

pre {
  background: #f8fafc;
  border-radius: 8px;
  padding: 10px;
  overflow: auto;
}
</style>

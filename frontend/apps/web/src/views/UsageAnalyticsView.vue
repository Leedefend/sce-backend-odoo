<template>
  <section class="usage-analytics">
    <header class="header">
      <div>
        <h2>Usage Analytics</h2>
        <p>Scene / Capability 使用统计（按公司累计）。</p>
      </div>
      <div class="actions">
        <label>
          Top
          <select v-model="topN" :disabled="loading">
            <option :value="5">5</option>
            <option :value="10">10</option>
            <option :value="20">20</option>
          </select>
        </label>
        <label>
          趋势范围
          <select v-model="dailyRange" :disabled="loading">
            <option :value="3">最近 3 天</option>
            <option :value="7">最近 7 天</option>
          </select>
        </label>
        <label>
          隐藏原因
          <select v-model="hiddenReasonFilter" :disabled="loading">
            <option value="ALL">全部</option>
            <option v-for="item in reasonCounts" :key="`reason-filter-${item.reason_code}`" :value="item.reason_code">
              {{ item.reason_code }} ({{ item.count }})
            </option>
          </select>
        </label>
        <label>
          角色切片
          <select v-model="roleSlice" :disabled="loading">
            <option value="">全部角色</option>
            <option v-for="code in roleCodeOptions" :key="`role-${code}`" :value="code">
              {{ code }}
            </option>
          </select>
        </label>
        <label>
          用户切片
          <input
            v-model.number="userSlice"
            type="number"
            min="0"
            step="1"
            placeholder="0=全部"
            :disabled="loading"
          />
        </label>
        <label>
          Scene 前缀
          <input
            v-model.trim="scenePrefix"
            type="text"
            placeholder="如 projects."
            :disabled="loading"
          />
        </label>
        <label>
          Capability 前缀
          <input
            v-model.trim="capabilityPrefix"
            type="text"
            placeholder="如 contract."
            :disabled="loading"
          />
        </label>
        <label class="export-scope">
          <input v-model="exportFilteredOnly" type="checkbox" />
          仅导出当前筛选
        </label>
        <button class="secondary" :disabled="loading" @click="copyExportParams">复制导出参数</button>
        <button class="secondary" :disabled="loading" @click="resetFilters">重置筛选</button>
        <button class="secondary" :disabled="loading || !canExport" @click="exportCsv">导出 CSV</button>
        <button class="secondary" :disabled="loading" @click="load">刷新</button>
      </div>
    </header>

    <StatusPanel v-if="loading" title="Loading usage report..." variant="info" />
    <StatusPanel
      v-else-if="errorText"
      :title="errorCopy.title"
      :message="errorCopy.message"
      :trace-id="statusError?.traceId || errorTraceId || undefined"
      :error-code="statusError?.code"
      :reason-code="statusError?.reasonCode"
      :error-category="statusError?.errorCategory"
      :retryable="statusError?.retryable"
      :hint="errorCopy.hint"
      :suggested-action="statusError?.suggestedAction"
      variant="error"
      :on-retry="load"
    />

    <template v-else>
      <section class="slice-bar">
        <span>窗口：{{ report?.filters?.day_from || '-' }} ~ {{ report?.filters?.day_to || '-' }}</span>
        <span>角色：{{ report?.filters?.role_code || '全部' }}</span>
        <span>用户：{{ report?.filters?.user_id || 0 }}</span>
        <span>Scene 前缀：{{ report?.filters?.scene_key_prefix || '-' }}</span>
        <span>Capability 前缀：{{ report?.filters?.capability_key_prefix || '-' }}</span>
      </section>

      <section class="summary-grid">
        <article class="summary-card">
          <p class="label">Scene Open Total</p>
          <p class="count">{{ report?.totals.scene_open_total ?? 0 }}</p>
        </article>
        <article class="summary-card">
          <p class="label">Capability Open Total</p>
          <p class="count">{{ report?.totals.capability_open_total ?? 0 }}</p>
        </article>
        <article class="summary-card">
          <p class="label">Generated At</p>
          <p class="count small">{{ report?.generated_at || '-' }}</p>
        </article>
      </section>

      <section class="summary-grid">
        <article class="summary-card">
          <p class="label">Capability Total</p>
          <p class="count">{{ visibility?.summary.total ?? 0 }}</p>
        </article>
        <article class="summary-card">
          <p class="label">Visible / Hidden</p>
          <p class="count small">{{ visibility?.summary.visible ?? 0 }} / {{ visibility?.summary.hidden ?? 0 }}</p>
        </article>
        <article class="summary-card">
          <p class="label">Ready / Preview / Locked</p>
          <p class="count small">
            {{ visibility?.summary.ready ?? 0 }} / {{ visibility?.summary.preview ?? 0 }} / {{ visibility?.summary.locked ?? 0 }}
          </p>
        </article>
        <article class="summary-card">
          <p class="label">Role Codes</p>
          <p class="count small">{{ (visibility?.role_codes || []).join(', ') || '-' }}</p>
        </article>
      </section>

      <section class="tables">
        <article class="table-card">
          <h3>Top Scenes</h3>
          <table>
            <thead>
              <tr><th>Scene Key</th><th>Count</th></tr>
            </thead>
            <tbody>
              <tr v-if="!sceneTop.length"><td colspan="2" class="empty">暂无数据</td></tr>
              <tr v-for="item in sceneTop" :key="item.key">
                <td>{{ item.key }}</td>
                <td>{{ item.count }}</td>
              </tr>
            </tbody>
          </table>
        </article>

        <article class="table-card">
          <h3>Top Capabilities</h3>
          <table>
            <thead>
              <tr><th>Capability Key</th><th>Count</th></tr>
            </thead>
            <tbody>
              <tr v-if="!capabilityTop.length"><td colspan="2" class="empty">暂无数据</td></tr>
              <tr v-for="item in capabilityTop" :key="item.key">
                <td>{{ item.key }}</td>
                <td>{{ item.count }}</td>
              </tr>
            </tbody>
          </table>
        </article>
      </section>

      <section class="tables">
        <article class="table-card">
          <h3>Scene Open (Last 7 Days)</h3>
          <table>
            <thead>
              <tr><th>Date</th><th>Count</th></tr>
            </thead>
            <tbody>
              <tr v-if="!sceneDaily.length"><td colspan="2" class="empty">暂无数据</td></tr>
              <tr v-for="item in sceneDaily" :key="item.day">
                <td>{{ item.day }}</td>
                <td>{{ item.count }}</td>
              </tr>
            </tbody>
          </table>
        </article>

        <article class="table-card">
          <h3>Capability Open (Last 7 Days)</h3>
          <table>
            <thead>
              <tr><th>Date</th><th>Count</th></tr>
            </thead>
            <tbody>
              <tr v-if="!capabilityDaily.length"><td colspan="2" class="empty">暂无数据</td></tr>
              <tr v-for="item in capabilityDaily" :key="item.day">
                <td>{{ item.day }}</td>
                <td>{{ item.count }}</td>
              </tr>
            </tbody>
          </table>
        </article>
      </section>

      <section class="tables">
        <article class="table-card">
          <h3>Visibility Reason Counts</h3>
          <table>
            <thead>
              <tr><th>Reason Code</th><th>Count</th></tr>
            </thead>
            <tbody>
              <tr v-if="!reasonCounts.length"><td colspan="2" class="empty">暂无数据</td></tr>
              <tr v-for="item in reasonCounts" :key="item.reason_code">
                <td>{{ item.reason_code }}</td>
                <td>{{ item.count }}</td>
              </tr>
            </tbody>
          </table>
        </article>

        <article class="table-card">
          <h3>Hidden Capability Samples</h3>
          <table>
            <thead>
              <tr><th>Key</th><th>Reason</th></tr>
            </thead>
            <tbody>
              <tr v-if="!filteredHiddenSamples.length"><td colspan="2" class="empty">暂无数据</td></tr>
              <tr v-for="item in filteredHiddenSamples" :key="item.key">
                <td>{{ item.key }}</td>
                <td>{{ item.reason_code || item.reason || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </article>
      </section>

      <section class="tables">
        <article class="table-card">
          <h3>Role Top</h3>
          <table>
            <thead>
              <tr><th>Role Code</th><th>Scene</th><th>Capability</th><th>Total</th></tr>
            </thead>
            <tbody>
              <tr v-if="!roleTop.length"><td colspan="4" class="empty">暂无数据</td></tr>
              <tr v-for="item in roleTop" :key="`role-top-${item.role_code}`">
                <td>{{ item.role_code }}</td>
                <td>{{ item.scene_open_total }}</td>
                <td>{{ item.capability_open_total }}</td>
                <td>{{ item.combined_total }}</td>
              </tr>
            </tbody>
          </table>
        </article>

        <article class="table-card">
          <h3>User Top</h3>
          <table>
            <thead>
              <tr><th>User ID</th><th>Scene</th><th>Capability</th><th>Total</th></tr>
            </thead>
            <tbody>
              <tr v-if="!userTop.length"><td colspan="4" class="empty">暂无数据</td></tr>
              <tr v-for="item in userTop" :key="`user-top-${item.user_id}`">
                <td>{{ item.user_id }}</td>
                <td>{{ item.scene_open_total }}</td>
                <td>{{ item.capability_open_total }}</td>
                <td>{{ item.combined_total }}</td>
              </tr>
            </tbody>
          </table>
        </article>
      </section>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { exportUsageCsv, fetchCapabilityVisibilityReport, fetchUsageReport, type CapabilityVisibilityReport, type UsageReport } from '../api/usage';
import StatusPanel from '../components/StatusPanel.vue';
import { buildStatusError, resolveErrorCopy, type StatusError } from '../composables/useStatus';

const loading = ref(false);
const errorText = ref('');
const errorTraceId = ref('');
const statusError = ref<StatusError | null>(null);
const topN = ref(10);
const dailyRange = ref(7);
const hiddenReasonFilter = ref('ALL');
const roleSlice = ref('');
const userSlice = ref(0);
const scenePrefix = ref('');
const capabilityPrefix = ref('');
const exportFilteredOnly = ref(true);
const report = ref<UsageReport | null>(null);
const visibility = ref<CapabilityVisibilityReport | null>(null);

const sceneTop = computed(() => report.value?.scene_top || []);
const capabilityTop = computed(() => report.value?.capability_top || []);
const roleTop = computed(() => report.value?.role_top || []);
const userTop = computed(() => report.value?.user_top || []);
const sceneDaily = computed(() => report.value?.daily?.scene_open || []);
const capabilityDaily = computed(() => report.value?.daily?.capability_open || []);
const reasonCounts = computed(() => visibility.value?.reason_counts || []);
const roleCodeOptions = computed(() => visibility.value?.role_codes || []);
const hiddenSamples = computed(() => visibility.value?.hidden_samples || []);
const filteredHiddenSamples = computed(() => {
  if (hiddenReasonFilter.value === 'ALL') return hiddenSamples.value;
  return hiddenSamples.value.filter((item) => String(item.reason_code || '') === hiddenReasonFilter.value);
});
const canExport = computed(() => Boolean(report.value || visibility.value));
const errorCopy = computed(() => resolveErrorCopy(statusError.value, errorText.value || 'Failed to load usage report'));

async function exportCsv() {
  if (!canExport.value) return;
  try {
    const data = await exportUsageCsv({
      top: topN.value,
      days: dailyRange.value,
      hidden_reason: hiddenReasonFilter.value,
      export_filtered_only: exportFilteredOnly.value,
      role_code: roleSlice.value || '',
      user_id: Math.max(0, Number(userSlice.value || 0)),
      scene_key_prefix: scenePrefix.value || '',
      capability_key_prefix: capabilityPrefix.value || '',
    });
    const blob = new Blob([data.content || ''], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = data.filename || `usage-analytics-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (err) {
    errorText.value = err instanceof Error ? err.message : '导出失败';
    statusError.value = buildStatusError(err, errorText.value);
    errorTraceId.value = statusError.value.traceId || '';
  }
}

async function copyExportParams() {
  const payload = {
    top: topN.value,
    days: dailyRange.value,
    hidden_reason: hiddenReasonFilter.value,
    export_filtered_only: exportFilteredOnly.value,
    role_code: roleSlice.value || '',
    user_id: Math.max(0, Number(userSlice.value || 0)),
    scene_key_prefix: scenePrefix.value || '',
    capability_key_prefix: capabilityPrefix.value || '',
  };
  try {
    await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
  } catch {
    errorText.value = '复制导出参数失败';
  }
}

function resetFilters() {
  dailyRange.value = 7;
  hiddenReasonFilter.value = 'ALL';
  roleSlice.value = '';
  userSlice.value = 0;
  scenePrefix.value = '';
  capabilityPrefix.value = '';
  exportFilteredOnly.value = true;
  if (topN.value !== 10) {
    topN.value = 10;
    return;
  }
  void load();
}

async function load() {
  loading.value = true;
  errorText.value = '';
  errorTraceId.value = '';
  statusError.value = null;
  try {
    const [usage, vis] = await Promise.all([
      fetchUsageReport(
        topN.value,
        dailyRange.value,
        roleSlice.value || '',
        Math.max(0, Number(userSlice.value || 0)),
        scenePrefix.value || '',
        capabilityPrefix.value || '',
      ),
      fetchCapabilityVisibilityReport(),
    ]);
    report.value = usage;
    visibility.value = vis;
  } catch (err) {
    errorText.value = err instanceof Error ? err.message : 'Failed to load usage report';
    statusError.value = buildStatusError(err, errorText.value);
    errorTraceId.value = statusError.value.traceId || '';
  } finally {
    loading.value = false;
  }
}

watch([topN, dailyRange, roleSlice, userSlice, scenePrefix, capabilityPrefix], () => {
  load();
});

onMounted(load);
</script>

<style scoped>
.usage-analytics {
  display: grid;
  gap: 16px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.slice-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  color: #334155;
  font-size: 13px;
}

.slice-bar span {
  border: 1px solid #e2e8f0;
  border-radius: 999px;
  padding: 4px 10px;
  background: #fff;
}

.export-scope {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #334155;
}

.secondary {
  border: 1px solid #93c5fd;
  border-radius: 8px;
  background: #eff6ff;
  color: #1e3a8a;
  padding: 8px 10px;
  cursor: pointer;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
}

.summary-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px;
  background: #fff;
}

.summary-card .label {
  margin: 0;
  color: #64748b;
}

.summary-card .count {
  margin: 8px 0 0;
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
}

.summary-card .count.small {
  font-size: 14px;
}

.tables {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 12px;
}

.table-card {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
  overflow: hidden;
}

.table-card h3 {
  margin: 0;
  padding: 12px;
  border-bottom: 1px solid #f1f5f9;
  color: #0f172a;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 10px 12px;
  border-bottom: 1px solid #f1f5f9;
  text-align: left;
}

.empty {
  text-align: center;
  color: #64748b;
}
</style>

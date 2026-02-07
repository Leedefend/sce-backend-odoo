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
        <button class="secondary" :disabled="loading" @click="load">刷新</button>
      </div>
    </header>

    <StatusPanel v-if="loading" title="Loading usage report..." variant="info" />
    <StatusPanel
      v-else-if="errorText"
      title="Usage report failed"
      :message="errorText"
      :trace-id="errorTraceId || undefined"
      variant="error"
      :on-retry="load"
    />

    <template v-else>
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
              <tr v-if="!hiddenSamples.length"><td colspan="2" class="empty">暂无数据</td></tr>
              <tr v-for="item in hiddenSamples" :key="item.key">
                <td>{{ item.key }}</td>
                <td>{{ item.reason_code || item.reason || '-' }}</td>
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
import { ApiError } from '../api/client';
import { fetchCapabilityVisibilityReport, fetchUsageReport, type CapabilityVisibilityReport, type UsageReport } from '../api/usage';
import StatusPanel from '../components/StatusPanel.vue';

const loading = ref(false);
const errorText = ref('');
const errorTraceId = ref('');
const topN = ref(10);
const report = ref<UsageReport | null>(null);
const visibility = ref<CapabilityVisibilityReport | null>(null);

const sceneTop = computed(() => report.value?.scene_top || []);
const capabilityTop = computed(() => report.value?.capability_top || []);
const reasonCounts = computed(() => visibility.value?.reason_counts || []);
const hiddenSamples = computed(() => visibility.value?.hidden_samples || []);

async function load() {
  loading.value = true;
  errorText.value = '';
  errorTraceId.value = '';
  try {
    const [usage, vis] = await Promise.all([
      fetchUsageReport(topN.value),
      fetchCapabilityVisibilityReport(),
    ]);
    report.value = usage;
    visibility.value = vis;
  } catch (err) {
    errorText.value = err instanceof Error ? err.message : 'Failed to load usage report';
    if (err instanceof ApiError) {
      errorTraceId.value = err.traceId || '';
    }
  } finally {
    loading.value = false;
  }
}

watch(topN, () => {
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

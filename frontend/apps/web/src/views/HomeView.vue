<template>
  <section class="capability-home">
    <header class="hero">
      <div>
        <h2>能力目录</h2>
        <p class="lead">选择你要完成的工作，直接进入场景。</p>
        <p class="role-line">
          当前角色：{{ roleLabel }} · 默认落地：{{ roleLandingLabel }}
          <button class="inline-link" @click="openRoleLanding">进入工作台</button>
        </p>
        <p v-if="isHudEnabled" class="hud-line">
          HUD: role_key={{ roleSurface?.role_code || '-' }} · landing_scene_key={{ roleLandingScene }}
        </p>
        <p v-if="isHudEnabled" class="hud-line">
          HUD: internal_tiles={{ internalTileCount }} · visible_mode=show_all
        </p>
      </div>
      <div class="view-toggle">
        <button class="my-work-btn" @click="goToMyWork">我的工作</button>
        <button
          v-if="isAdmin"
          class="my-work-btn"
          @click="goToUsageAnalytics"
        >
          使用分析
        </button>
        <button :class="{ active: viewMode === 'card' }" @click="viewMode = 'card'">卡片</button>
        <button :class="{ active: viewMode === 'list' }" @click="viewMode = 'list'">列表</button>
      </div>
    </header>

    <section class="today-actions" aria-label="今日建议">
      <header class="today-actions-header">
        <h3>今日建议</h3>
        <p>10 秒内开始今天最常见的工作。</p>
      </header>
      <div class="today-actions-grid">
        <article v-for="item in todaySuggestions" :key="item.id" class="today-card">
          <p class="today-title">
            <span>{{ item.title }}</span>
            <span v-if="item.status" class="today-status" :class="`today-status-${item.status}`">
              {{ item.status === 'urgent' ? '紧急' : '普通' }}
            </span>
          </p>
          <p class="today-desc">{{ item.description }}</p>
          <p v-if="typeof item.count === 'number'" class="today-count">待处理 {{ item.count }}</p>
          <button class="today-btn" @click="openSuggestion(item.sceneKey, item.contextQuery)">立即进入</button>
        </article>
      </div>
    </section>

    <section class="filters">
      <div v-if="enterError" class="status-panel" role="status" aria-live="polite">
        <p class="status-title">进入失败：{{ enterError.message }}</p>
        <p class="status-detail">{{ enterError.hint }}</p>
        <p v-if="isHudEnabled" class="status-meta">
          code={{ enterError.code || '-' }} · trace_id={{ enterError.traceId || '-' }}
        </p>
        <div class="status-actions">
          <button v-if="lastFailedEntry" @click="retryOpen">重试</button>
          <button @click="clearEnterError">知道了</button>
        </div>
      </div>
      <input
        v-model.trim="searchText"
        class="search-input"
        type="search"
        placeholder="搜索能力名称或说明"
      />
      <label class="ready-only">
        <input v-model="readyOnly" type="checkbox" />
        仅显示可进入能力
      </label>
      <div class="state-filters">
        <button :class="{ active: stateFilter === 'ALL' }" @click="stateFilter = 'ALL'">
          全部 {{ allCount }}
        </button>
        <button :class="{ active: stateFilter === 'READY' }" @click="stateFilter = 'READY'">
          可进入 {{ stateCounts.READY }}
        </button>
        <button
          :class="{ active: stateFilter === 'LOCKED' }"
          :disabled="readyOnly"
          @click="stateFilter = 'LOCKED'"
        >
          暂不可用 {{ stateCounts.LOCKED }}
        </button>
        <button
          :class="{ active: stateFilter === 'PREVIEW' }"
          :disabled="readyOnly"
          @click="stateFilter = 'PREVIEW'"
        >
          即将开放 {{ stateCounts.PREVIEW }}
        </button>
      </div>
      <p v-if="readyOnly" class="filter-tip">已启用“仅显示可进入能力”，暂不可用与即将开放不会展示。</p>
      <div v-if="lockedReasonOptions.length" class="reason-filters">
        <button :class="{ active: lockReasonFilter === 'ALL' }" @click="lockReasonFilter = 'ALL'">
          锁定原因：全部
        </button>
        <button
          v-for="item in lockedReasonOptions"
          :key="`reason-${item.reasonCode}`"
          :class="{ active: lockReasonFilter === item.reasonCode }"
          @click="lockReasonFilter = item.reasonCode"
        >
          {{ lockReasonLabel(item.reasonCode) }} {{ item.count }}
        </button>
      </div>
      <div v-if="activeFilterChips.length" class="active-filters">
        <button
          v-for="chip in activeFilterChips"
          :key="chip.key"
          class="filter-chip"
          @click="clearFilterChip(chip.key)"
        >
          {{ chip.label }} ×
        </button>
      </div>
      <div v-if="groupedEntries.length" class="group-actions">
        <button @click="expandAllSceneGroups">展开全部分组</button>
        <button @click="collapseAllSceneGroups">折叠全部分组</button>
      </div>
    </section>

    <div v-if="!filteredEntries.length" class="empty">
      <template v-if="entries.length">
        <p>
          {{
            readyOnlyNoResult
              ? '当前启用了“仅显示可进入能力”，暂时没有可进入能力。'
              : searchKeyword
                ? `未找到与“${searchKeyword}”相关的能力，请调整筛选条件。`
                : '未找到相关能力，请调整筛选条件。'
          }}
        </p>
        <div class="empty-actions">
          <button v-if="readyOnlyNoResult" class="empty-btn" @click="showAllCapabilities">显示全部能力</button>
          <button class="empty-btn" @click="clearSearchAndFilters">清空搜索与筛选</button>
        </div>
      </template>
      <template v-else>
        <p>当前账号暂无可用能力，可能因为角色权限未开通或工作台尚未配置。</p>
        <div class="empty-actions">
          <button v-if="hasRoleSwitch" class="empty-btn" @click="goToMyWork">切换角色</button>
          <button class="empty-btn" @click="goHome">返回首页</button>
          <button class="empty-btn secondary" @click="toggleEmptyHelp">
            {{ showEmptyHelp ? '收起帮助' : '查看帮助' }}
          </button>
        </div>
        <p v-if="showEmptyHelp" class="empty-help">
          建议先点击“切换角色”确认当前角色；若仍无能力，请联系管理员开通角色权限或配置能力目录。
        </p>
      </template>
    </div>

    <div v-else class="scene-groups">
      <section v-for="group in groupedEntries" :key="`scene-${group.sceneKey}`" class="scene-group">
        <header class="scene-group-header">
          <button class="scene-toggle" @click="toggleSceneGroup(group.sceneKey)">
            <span>{{ collapsedSceneSet.has(group.sceneKey) ? '▶' : '▼' }}</span>
            <span>{{ group.sceneTitle }}</span>
            <span class="scene-count">{{ group.items.length }}</span>
          </button>
        </header>
        <div
          v-if="!collapsedSceneSet.has(group.sceneKey)"
          :class="viewMode === 'card' ? 'cards' : 'list'"
        >
          <article
            v-for="entry in group.items"
            :key="entry.id"
            class="entry"
            :class="`state-${entry.state.toLowerCase()}`"
          >
            <div class="entry-main">
              <p class="title-row">
                <span class="title">
                  <template v-for="(part, index) in highlightParts(entry.title)" :key="`title-${entry.id}-${index}`">
                    <span :class="{ hit: part.hit }">{{ part.text }}</span>
                  </template>
                </span>
                <span v-if="entry.state !== 'READY'" class="state">{{ stateLabel(entry.state) }}</span>
              </p>
              <p class="subtitle" :title="entry.reason || entry.subtitle">
                <template v-for="(part, index) in highlightParts(entry.subtitle || '无说明')" :key="`sub-${entry.id}-${index}`">
                  <span :class="{ hit: part.hit }">{{ part.text }}</span>
                </template>
              </p>
              <p v-if="isHudEnabled" class="hud-meta">scene_key={{ entry.sceneKey }} · capability_key={{ entry.key }}</p>
              <p v-if="entry.state === 'LOCKED'" class="lock-reason">
                {{ entry.reason || lockReasonLabel(entry.reasonCode) }}
              </p>
            </div>
            <button
              class="open-btn"
              :disabled="!canEnter(entry)"
              :title="entry.reason || ''"
              @click="openScene(entry)"
            >
              {{ actionLabel(entry) }}
            </button>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useSessionStore } from '../stores/session';
import { trackCapabilityOpen, trackUsageEvent } from '../api/usage';
import { fetchMyWorkSummary, type MyWorkSummaryItem } from '../api/myWork';

type EntryState = 'READY' | 'LOCKED' | 'PREVIEW';
type SuggestionStatus = 'urgent' | 'normal';
type CapabilityEntry = {
  id: string;
  key: string;
  recentKey: string;
  title: string;
  subtitle: string;
  sceneKey: string;
  sceneTitle: string;
  sequence: number;
  status: string;
  state: EntryState;
  reason: string;
  reasonCode: string;
  tags: string[];
};
type SuggestionItem = {
  id: string;
  title: string;
  description: string;
  sceneKey: string;
  contextQuery?: Record<string, string>;
  count?: number;
  status?: SuggestionStatus;
};
type SuggestionRoute = {
  path: string;
  query: Record<string, string>;
};
type FilterChip = { key: string; label: string };

const router = useRouter();
const route = useRoute();
const session = useSessionStore();
const viewMode = ref<'card' | 'list'>('card');
const searchText = ref('');
const stateFilter = ref<'ALL' | EntryState>('ALL');
const readyOnly = ref(false);
const lockReasonFilter = ref('ALL');
const collapsedSceneKeys = ref<string[]>([]);
const collapsedSceneSet = computed(() => new Set(collapsedSceneKeys.value));
const recentEntryKeys = ref<string[]>([]);
const lastFailedEntry = ref<CapabilityEntry | null>(null);
const enterError = ref<{ message: string; hint: string; code: string; traceId: string } | null>(null);
const lastTrackedSearch = ref('');
const lastTrackedFilterSignature = ref('');
const showEmptyHelp = ref(false);
const myWorkSummary = ref<MyWorkSummaryItem[]>([]);
const isHudEnabled = computed(() => {
  const hud = String(route.query.hud || '').trim();
  return import.meta.env.DEV || hud === '1' || hud.toLowerCase() === 'true';
});
const isAdmin = computed(() => {
  const groups = session.user?.groups_xmlids || [];
  return groups.includes('base.group_system') || groups.includes('smart_construction_core.group_sc_cap_config_admin');
});
const roleSurface = computed(() => session.roleSurface);
const hasRoleSwitch = computed(() => Object.keys(session.roleSurfaceMap || {}).length > 1);
const roleLabel = computed(() => {
  const raw = asText(roleSurface.value?.role_label) || asText(roleSurface.value?.role_code);
  const normalized = raw.toLowerCase();
  if (!raw) return '负责人';
  if (normalized === 'executive') return '高管';
  if (normalized === 'owner') return '负责人';
  return raw;
});
const sceneTitleMap = computed(() => {
  const map = new Map<string, string>();
  for (const scene of session.scenes) {
    const key = asText(scene.key);
    if (!key) continue;
    map.set(key, resolveSceneTitle(scene));
  }
  return map;
});
const roleLandingScene = computed(() => asText(roleSurface.value?.landing_scene_key) || 'projects.list');
const roleLandingLabel = computed(() => sceneTitleMap.value.get(roleLandingScene.value) || '工作台首页');
const internalTileCount = computed(() => {
  let count = 0;
  session.scenes.forEach((scene) => {
    const sceneKey = asText(scene.key);
    if (!sceneKey) return;
    const tiles = Array.isArray(scene.tiles) ? scene.tiles : [];
    tiles.forEach((tile, tileIndex) => {
      const key = asText(tile.key);
      if (!key) return;
      const title = asText((tile as { title?: string }).title) || `能力 ${tileIndex + 1}`;
      if (
        isInternalEntry({
          sceneKey,
          title,
          key,
          sceneTags: (scene as { tags?: unknown }).tags,
          tileTags: (tile as { tags?: unknown }).tags,
        })
      ) {
        count += 1;
      }
    });
  });
  return count;
});
const workspaceScopeKey = computed(() => {
  const roleKey = asText(roleSurface.value?.role_code) || 'default';
  const landingScene = asText(roleSurface.value?.landing_scene_key) || 'projects.list';
  const userId = Number(session.user?.id || 0) || 0;
  return `${userId}:${roleKey}:${landingScene}`;
});
const homeCollapseStorageKey = computed(() => `sc.home.scene_groups.collapsed.v2:${workspaceScopeKey.value}`);
const homeFilterStorageKey = computed(() => `sc.home.filters.v2:${workspaceScopeKey.value}`);
const homeViewModeStorageKey = computed(() => `workspace:view_mode:${workspaceScopeKey.value}`);
const homeRecentStorageKey = computed(() => `workspace:recent:${workspaceScopeKey.value}`);
const searchKeyword = computed(() => searchText.value.trim());

function stringifyEntryContext(context: { section?: string; source?: string; reason?: string; search?: string }) {
  const next: Record<string, string> = {};
  if (context.section) next.section = context.section;
  if (context.source) next.source = context.source;
  if (context.reason) next.reason = context.reason;
  if (context.search) next.search = context.search;
  if (!Object.keys(next).length) return '';
  return JSON.stringify(next);
}

function asText(value: unknown) {
  const text = String(value ?? '').trim();
  if (!text || text.toLowerCase() === 'undefined' || text.toLowerCase() === 'null') return '';
  return text;
}

function hasInternalTag(raw: unknown) {
  if (Array.isArray(raw)) {
    return raw.some((item) => {
      const key = asText(item).toLowerCase();
      return key === 'internal' || key === 'smoke' || key === 'test';
    });
  }
  const text = asText(raw).toLowerCase();
  if (!text) return false;
  return text.split(/[,\s;|]+/).some((item) => item === 'internal' || item === 'smoke' || item === 'test');
}

function resolveSceneTitle(scene: { title?: unknown; key?: unknown }) {
  const title = asText(scene.title);
  if (title) return title;
  const key = asText(scene.key);
  if (!key) return '未分类能力';
  return isHudEnabled.value ? `未分类能力（${key}）` : '未分类能力';
}

function isInternalEntry(params: {
  sceneKey: string;
  title: string;
  key: string;
  sceneTags?: unknown;
  tileTags?: unknown;
}) {
  if (hasInternalTag(params.sceneTags) || hasInternalTag(params.tileTags)) return true;
  const merged = `${params.sceneKey} ${params.title} ${params.key}`.toLowerCase();
  return merged.includes('smoke') || merged.includes('internal') || merged.includes('test');
}

function mapState(rawState: string | undefined, status: string): EntryState {
  const state = String(rawState || '').toUpperCase();
  if (state === 'READY' || state === 'LOCKED' || state === 'PREVIEW') {
    return state;
  }
  return status === 'ga' ? 'READY' : 'PREVIEW';
}

const entries = computed<CapabilityEntry[]>(() => {
  const list: CapabilityEntry[] = [];
  session.scenes.forEach((scene, sceneIndex) => {
    const sceneKey = asText(scene.key);
    if (!sceneKey) return;
    const sceneTitle = resolveSceneTitle(scene as { title?: unknown; key?: unknown });
    const tiles = Array.isArray(scene.tiles) ? scene.tiles : [];
    tiles.forEach((tile, tileIndex) => {
      const key = asText(tile.key);
      if (!key) return;
      const title = asText((tile as { title?: string }).title) || (isHudEnabled.value ? key : `能力 ${sceneIndex + 1}-${tileIndex + 1}`);
      if (
        !isHudEnabled.value &&
        isInternalEntry({
          sceneKey,
          title,
          key,
          sceneTags: (scene as { tags?: unknown }).tags,
          tileTags: (tile as { tags?: unknown }).tags,
        })
      ) {
        return;
      }
      const status = String((tile as { status?: string }).status || 'alpha').toLowerCase();
      const reason = String((tile as { reason?: string }).reason || '');
      const reasonCode = String((tile as { reason_code?: string }).reason_code || '');
      const state = mapState((tile as { state?: string }).state, status);
      list.push({
        id: `${sceneKey}-${key}-${sceneIndex}-${tileIndex}`,
        key,
        recentKey: `${sceneKey}::${key}`,
        title,
        subtitle: asText((tile as { subtitle?: string }).subtitle),
        sceneKey,
        sceneTitle,
        sequence: Number((tile as { sequence?: number }).sequence ?? 9999),
        status,
        state,
        reason,
        reasonCode,
        tags: [
          ...new Set(
            [
              ...(Array.isArray((scene as { tags?: unknown }).tags) ? (scene as { tags?: string[] }).tags : []),
              ...(Array.isArray((tile as { tags?: unknown }).tags) ? (tile as { tags?: string[] }).tags : []),
            ]
              .map((item) => asText(item).toLowerCase())
              .filter(Boolean),
          ),
        ],
      });
    });
  });
  return list.sort((a, b) => a.sequence - b.sequence || a.title.localeCompare(b.title));
});

const todaySuggestions = computed<SuggestionItem[]>(() => {
  const all = entries.value;
  const firstReady = all.find((entry) => entry.state === 'READY');
  const pickByKeyword = (keywords: string[], fallback?: string) => {
    const found = all.find((entry) => {
      const text = `${entry.title} ${entry.subtitle} ${entry.sceneKey}`.toLowerCase();
      return keywords.some((keyword) => text.includes(keyword));
    });
    if (found) {
      return { sceneKey: found.sceneKey, ready: found.state === 'READY' };
    }
    return { sceneKey: fallback || firstReady?.sceneKey || roleLandingScene.value, ready: false };
  };
  const project = pickByKeyword(['立项', 'project', 'intake']);
  const contract = pickByKeyword(['合同', 'contract', 'approve', 'approval']);
  const cost = pickByKeyword(['成本', 'cost', 'ledger']);
  const projectCount = resolveSuggestionCount(project.sceneKey, ['owned', 'todo']);
  const contractCount = resolveSuggestionCount(contract.sceneKey, ['todo']);
  const costCount = resolveSuggestionCount(cost.sceneKey, ['following', 'mentions']);
  return [
    {
      id: 'project-intake',
      title: '项目立项',
      description: '新建项目并完成立项信息录入。',
      sceneKey: project.sceneKey,
      contextQuery: {
        preset: 'project_intake',
        ctx_source: 'workspace_today',
        entry_context: stringifyEntryContext({ section: 'owned', search: '立项' }),
      },
      count: project.ready ? projectCount : undefined,
      status: 'normal',
    },
    {
      id: 'contract-approval',
      title: '合同审批',
      description: '查看待审批合同并快速处理。',
      sceneKey: contract.sceneKey,
      contextQuery: {
        preset: 'pending_approval',
        ctx_source: 'workspace_today',
        entry_context: stringifyEntryContext({ section: 'todo', source: 'mail.activity', search: '审批' }),
      },
      count: contract.ready ? contractCount : undefined,
      status: 'urgent',
    },
    {
      id: 'cost-ledger',
      title: '成本台账',
      description: '跟踪成本执行并核对差异。',
      sceneKey: cost.sceneKey,
      contextQuery: {
        preset: 'cost_watchlist',
        ctx_source: 'workspace_today',
        entry_context: stringifyEntryContext({ section: 'following', search: '成本' }),
      },
      count: cost.ready ? costCount : undefined,
      status: 'normal',
    },
  ];
});

function resolveSuggestionCount(sceneKey: string, fallbackKeys: string[]) {
  const byScene = myWorkSummary.value.find((item) => String(item.scene_key || '') === sceneKey);
  if (byScene) return Number(byScene.count || 0);
  for (const key of fallbackKeys) {
    const matched = myWorkSummary.value.find((item) => String(item.key || '') === key);
    if (matched) return Number(matched.count || 0);
  }
  return undefined;
}

function matchesSearch(entry: CapabilityEntry, query: string) {
  if (!query) return true;
  const fields = isHudEnabled.value
    ? [entry.title, entry.subtitle, entry.key, ...entry.tags]
    : [entry.title, entry.subtitle, ...entry.tags];
  return fields.some((text) => String(text || '').toLowerCase().includes(query));
}

const searchedEntries = computed<CapabilityEntry[]>(() => {
  const query = searchText.value.trim().toLowerCase();
  return entries.value.filter((entry) => matchesSearch(entry, query));
});

const tabBaseEntries = computed<CapabilityEntry[]>(() => {
  if (lockReasonFilter.value === 'ALL') return searchedEntries.value;
  return searchedEntries.value.filter((entry) => {
    if (entry.state !== 'LOCKED') return false;
    return String(entry.reasonCode || '').toUpperCase() === lockReasonFilter.value;
  });
});

const filteredEntries = computed<CapabilityEntry[]>(() => {
  return searchedEntries.value.filter((entry) => {
    if (readyOnly.value && entry.state !== 'READY') return false;
    const matchesState = stateFilter.value === 'ALL' ? true : entry.state === stateFilter.value;
    if (!matchesState) return false;
    if (lockReasonFilter.value !== 'ALL') {
      if (entry.state !== 'LOCKED') return false;
      if (String(entry.reasonCode || '').toUpperCase() !== lockReasonFilter.value) return false;
    }
    return true;
  });
});

const stateCounts = computed(() => {
  const counts = { READY: 0, LOCKED: 0, PREVIEW: 0 };
  for (const entry of tabBaseEntries.value) {
    counts[entry.state] += 1;
  }
  if (readyOnly.value) {
    return { READY: counts.READY, LOCKED: 0, PREVIEW: 0 };
  }
  return counts;
});

const allCount = computed(() => (readyOnly.value ? stateCounts.value.READY : tabBaseEntries.value.length));
const readyOnlyNoResult = computed(
  () => readyOnly.value && filteredEntries.value.length === 0 && stateCounts.value.READY === 0,
);
const activeFilterChips = computed<FilterChip[]>(() => {
  const chips: FilterChip[] = [];
  const keyword = searchText.value.trim();
  if (keyword) chips.push({ key: 'search', label: `搜索：${keyword}` });
  if (readyOnly.value) chips.push({ key: 'ready-only', label: '仅显示可进入' });
  if (stateFilter.value !== 'ALL') chips.push({ key: 'state', label: `状态：${stateLabel(stateFilter.value)}` });
  if (lockReasonFilter.value !== 'ALL') {
    chips.push({ key: 'reason', label: `锁定原因：${lockReasonLabel(lockReasonFilter.value)}` });
  }
  return chips;
});

const groupedEntries = computed(() => {
  const filteredByRecent = new Map(filteredEntries.value.map((entry) => [entry.recentKey, entry]));
  const recentItems = recentEntryKeys.value
    .map((key) => filteredByRecent.get(key))
    .filter((entry): entry is CapabilityEntry => Boolean(entry));
  const recentKeySet = new Set(recentItems.map((item) => item.recentKey));
  const map = new Map<string, { sceneKey: string; sceneTitle: string; items: CapabilityEntry[] }>();
  filteredEntries.value.forEach((entry) => {
    if (recentKeySet.has(entry.recentKey)) return;
    const current = map.get(entry.sceneKey);
    if (current) {
      current.items.push(entry);
      return;
    }
    map.set(entry.sceneKey, {
      sceneKey: entry.sceneKey,
      sceneTitle: entry.sceneTitle,
      items: [entry],
    });
  });
  const grouped = Array.from(map.values()).sort((a, b) => a.sceneTitle.localeCompare(b.sceneTitle));
  if (!recentItems.length) return grouped;
  return [{ sceneKey: '__recent__', sceneTitle: '最近使用', items: recentItems }, ...grouped];
});

const lockedReasonOptions = computed(() => {
  const map = new Map<string, number>();
  entries.value.forEach((entry) => {
    if (entry.state !== 'LOCKED') return;
    const code = String(entry.reasonCode || 'UNKNOWN').toUpperCase();
    map.set(code, (map.get(code) || 0) + 1);
  });
  return Array.from(map.entries())
    .map(([reasonCode, count]) => ({ reasonCode, count }))
    .sort((a, b) => b.count - a.count || a.reasonCode.localeCompare(b.reasonCode));
});

function toggleSceneGroup(sceneKey: string) {
  const next = new Set(collapsedSceneKeys.value);
  if (next.has(sceneKey)) next.delete(sceneKey);
  else next.add(sceneKey);
  collapsedSceneKeys.value = Array.from(next);
}

function expandAllSceneGroups() {
  collapsedSceneKeys.value = [];
}

function collapseAllSceneGroups() {
  collapsedSceneKeys.value = groupedEntries.value.map((group) => group.sceneKey);
}

function lockReasonLabel(reasonCode: string) {
  const code = String(reasonCode || '').toUpperCase();
  if (code === 'PERMISSION_DENIED') return '权限不足';
  if (code === 'FEATURE_DISABLED') return '订阅未开通';
  if (code === 'ROLE_SCOPE_MISMATCH') return '角色范围不匹配';
  if (code === 'CAPABILITY_SCOPE_MISSING') return '缺少前置能力';
  if (code === 'CAPABILITY_SCOPE_CYCLE') return '能力依赖异常';
  return '当前不可用';
}

function stateLabel(state: EntryState) {
  if (state === 'READY') return '可进入';
  if (state === 'LOCKED') return '暂不可用';
  return '即将开放';
}

function canEnter(entry: CapabilityEntry) {
  return entry.state === 'READY';
}

function actionLabel(entry: CapabilityEntry) {
  if (entry.state === 'LOCKED') return '暂不可用';
  if (entry.state === 'PREVIEW') return '即将开放';
  return '进入';
}

async function openScene(entry: CapabilityEntry) {
  if (!canEnter(entry)) return;
  lastFailedEntry.value = null;
  enterError.value = null;
  void trackUsageEvent('workspace.enter_click', { capability_key: entry.key, scene_key: entry.sceneKey }).catch(() => {});
  try {
    void trackCapabilityOpen(entry.key).catch(() => {});
    await router.push({ path: `/s/${entry.sceneKey}` });
    pushRecentEntry(entry.recentKey);
    void trackUsageEvent('workspace.enter_result', {
      capability_key: entry.key,
      scene_key: entry.sceneKey,
      result: 'ok',
    }).catch(() => {});
  } catch (error) {
    const message = resolveEnterErrorMessage(error);
    const hint = resolveEnterErrorHint(message.code);
    lastFailedEntry.value = entry;
    enterError.value = {
      message: message.message,
      hint,
      code: message.code,
      traceId: message.traceId,
    };
    void trackUsageEvent('workspace.enter_result', {
      capability_key: entry.key,
      scene_key: entry.sceneKey,
      result: 'error',
      code: message.code || 'UNKNOWN',
      trace_id: message.traceId || '',
    }).catch(() => {});
  }
}

function openRoleLanding() {
  router.push(session.resolveLandingPath('/s/projects.list')).catch(() => {});
}

function goToMyWork() {
  router.push({ path: '/my-work' }).catch(() => {});
}

function goToUsageAnalytics() {
  router.push({ path: '/admin/usage-analytics' }).catch(() => {});
}

function goHome() {
  router.push({ path: '/' }).catch(() => {});
}

function toggleEmptyHelp() {
  showEmptyHelp.value = !showEmptyHelp.value;
}

function clearSearchAndFilters() {
  searchText.value = '';
  readyOnly.value = false;
  stateFilter.value = 'ALL';
  lockReasonFilter.value = 'ALL';
}

function showAllCapabilities() {
  readyOnly.value = false;
  stateFilter.value = 'ALL';
}

function clearFilterChip(key: string) {
  if (key === 'search') searchText.value = '';
  if (key === 'ready-only') readyOnly.value = false;
  if (key === 'state') stateFilter.value = 'ALL';
  if (key === 'reason') lockReasonFilter.value = 'ALL';
}

function normalizeViewMode(raw: unknown) {
  return raw === 'list' ? 'list' : 'card';
}

function pushRecentEntry(recentKey: string) {
  if (!recentKey) return;
  const deduped = [recentKey, ...recentEntryKeys.value.filter((item) => item !== recentKey)].slice(0, 5);
  recentEntryKeys.value = deduped;
}

function openSuggestionWithContext(sceneKey: string, contextQuery?: Record<string, string>) {
  const safeSceneKey = asText(sceneKey);
  if (!safeSceneKey) {
    openRoleLanding();
    return;
  }
  router.push({ path: `/s/${safeSceneKey}`, query: { ...(contextQuery || {}) } }).catch(() => {});
}

function openSuggestion(sceneKey: string, contextQuery?: Record<string, string>) {
  const preset = asText(contextQuery?.preset);
  const ctxSource = asText(contextQuery?.ctx_source) || 'workspace_today';
  const entryContext = asText(contextQuery?.entry_context);
  const withEntryContext = (query: Record<string, string>) =>
    entryContext ? { ...query, entry_context: entryContext } : query;
  const presetRouteMap: Record<string, (source: string) => SuggestionRoute> = {
    pending_approval: (source) => ({
      path: '/my-work',
      query: withEntryContext({
        preset: 'pending_approval',
        ctx_source: source,
        section: 'todo',
        source: 'mail.activity',
        search: '审批',
      }),
    }),
    project_intake: (source) => ({
      path: '/my-work',
      query: withEntryContext({ preset: 'project_intake', ctx_source: source, section: 'owned', search: '立项' }),
    }),
    cost_watchlist: (source) => ({
      path: '/my-work',
      query: withEntryContext({ preset: 'cost_watchlist', ctx_source: source, section: 'following', search: '成本' }),
    }),
  };
  if (preset && presetRouteMap[preset]) {
    const target = presetRouteMap[preset](ctxSource);
    void trackUsageEvent('workspace.preset.navigate', {
      preset,
      from: 'workspace.home',
      to: target.path,
      ctx_source: ctxSource,
    }).catch(() => {});
    router.push(target).catch(() => {});
    return;
  }
  if (contextQuery && Object.keys(contextQuery).length) {
    void trackUsageEvent('workspace.preset.navigate', {
      preset: preset || '',
      from: 'workspace.home',
      to: `/s/${asText(sceneKey) || ''}`,
      ctx_source: ctxSource,
    }).catch(() => {});
    openSuggestionWithContext(sceneKey, contextQuery);
    return;
  }
  const safeSceneKey = asText(sceneKey);
  if (!safeSceneKey) {
    openRoleLanding();
    return;
  }
  void trackUsageEvent('workspace.preset.navigate', {
    preset: '',
    from: 'workspace.home',
    to: `/s/${safeSceneKey}`,
    ctx_source: '',
  }).catch(() => {});
  router.push({ path: `/s/${safeSceneKey}` }).catch(() => {});
}

function retryOpen() {
  if (!lastFailedEntry.value) return;
  void openScene(lastFailedEntry.value);
}

function clearEnterError() {
  enterError.value = null;
  lastFailedEntry.value = null;
}

function resolveEnterErrorMessage(error: unknown) {
  const message = asText((error as { message?: unknown })?.message) || '能力入口暂时不可用';
  const lowered = message.toLowerCase();
  const code = lowered.includes('permission')
    ? 'PERMISSION_DENIED'
    : lowered.includes('not found')
      ? 'ROUTE_NOT_FOUND'
      : lowered.includes('timeout')
        ? 'TIMEOUT'
        : 'ENTER_FAILED';
  const traceId = asText((error as { trace_id?: unknown })?.trace_id) || asText((error as { traceId?: unknown })?.traceId);
  return { message, code, traceId };
}

function resolveEnterErrorHint(code: string) {
  if (code === 'PERMISSION_DENIED') return '请联系管理员开通对应权限后重试。';
  if (code === 'ROUTE_NOT_FOUND') return '入口配置异常，请稍后重试或联系管理员。';
  if (code === 'TIMEOUT') return '网络连接超时，请检查网络后点击重试。';
  return '请稍后重试；如果问题持续，请联系管理员。';
}

onMounted(() => {
  void trackUsageEvent('workspace.view', {
    role_key: asText(roleSurface.value?.role_code) || 'unknown',
    landing_scene_key: roleLandingScene.value,
  }).catch(() => {});
  fetchMyWorkSummary(20, 8)
    .then((result) => {
      myWorkSummary.value = Array.isArray(result.summary) ? result.summary : [];
    })
    .catch(() => {
      myWorkSummary.value = [];
    });
  try {
    const raw = window.localStorage.getItem(homeCollapseStorageKey.value);
    if (raw) {
      const parsed = JSON.parse(raw) as string[];
      if (Array.isArray(parsed)) {
        collapsedSceneKeys.value = parsed.filter((key) => typeof key === 'string' && key);
      }
    }
  } catch {
    // Ignore broken local cache.
  }
  try {
    const raw = window.localStorage.getItem(homeFilterStorageKey.value);
    if (raw) {
      const parsed = JSON.parse(raw) as { ready_only?: boolean; state_filter?: string };
      readyOnly.value = Boolean(parsed?.ready_only);
      const state = String(parsed?.state_filter || '').toUpperCase();
      if (state === 'ALL' || state === 'READY' || state === 'LOCKED' || state === 'PREVIEW') {
        stateFilter.value = state;
      }
    }
  } catch {
    // Ignore broken local cache.
  }
  try {
    const raw = window.localStorage.getItem(homeViewModeStorageKey.value);
    if (raw) {
      viewMode.value = normalizeViewMode(raw);
    }
  } catch {
    // Ignore broken local cache.
  }
  try {
    const raw = window.localStorage.getItem(homeRecentStorageKey.value);
    if (raw) {
      const parsed = JSON.parse(raw) as string[];
      if (Array.isArray(parsed)) {
        recentEntryKeys.value = parsed.filter((item) => typeof item === 'string' && item).slice(0, 5);
      }
    }
  } catch {
    // Ignore broken local cache.
  }
});

watch(collapsedSceneKeys, () => {
  try {
    window.localStorage.setItem(homeCollapseStorageKey.value, JSON.stringify(collapsedSceneKeys.value));
  } catch {
    // Ignore local storage errors.
  }
});

watch([readyOnly, stateFilter], () => {
  try {
    window.localStorage.setItem(
      homeFilterStorageKey.value,
      JSON.stringify({ ready_only: readyOnly.value, state_filter: stateFilter.value }),
    );
  } catch {
    // Ignore local storage errors.
  }
});

watch(viewMode, (next) => {
  try {
    window.localStorage.setItem(homeViewModeStorageKey.value, normalizeViewMode(next));
  } catch {
    // Ignore local storage errors.
  }
});

watch(recentEntryKeys, () => {
  try {
    window.localStorage.setItem(homeRecentStorageKey.value, JSON.stringify(recentEntryKeys.value));
  } catch {
    // Ignore local storage errors.
  }
});

watch(readyOnly, (next) => {
  if (!next) return;
  stateFilter.value = 'READY';
  lockReasonFilter.value = 'ALL';
});

watch([readyOnly, stateFilter, lockReasonFilter], () => {
  const signature = `${readyOnly.value ? '1' : '0'}:${stateFilter.value}:${lockReasonFilter.value}`;
  if (signature === lastTrackedFilterSignature.value) return;
  lastTrackedFilterSignature.value = signature;
  void trackUsageEvent('workspace.filter_change', {
    ready_only: readyOnly.value,
    state_filter: stateFilter.value,
    lock_reason_filter: lockReasonFilter.value,
  }).catch(() => {});
});

watch(searchText, (next) => {
  const query = String(next || '').trim();
  if (!query) {
    lastTrackedSearch.value = '';
    return;
  }
  if (query === lastTrackedSearch.value) return;
  lastTrackedSearch.value = query;
  void trackUsageEvent('workspace.search', { query }).catch(() => {});
});

function highlightParts(raw: string) {
  const text = String(raw || '');
  const query = searchText.value.trim();
  if (!query) return [{ text, hit: false }];
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`(${escaped})`, 'ig');
  const parts = text.split(regex).filter((part) => part.length > 0);
  return parts.map((part) => ({ text: part, hit: part.toLowerCase() === query.toLowerCase() }));
}
</script>

<style scoped>
.capability-home {
  display: grid;
  gap: 16px;
}

.hero {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 12px;
  padding: 20px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(21, 128, 61, 0.08), rgba(2, 132, 199, 0.12));
}

.hero h2 {
  margin: 0 0 4px;
  font-size: 24px;
}

.lead {
  margin: 0;
  color: #4b5563;
}

.role-line {
  margin: 8px 0 0;
  color: #334155;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.hud-line {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 12px;
}

.inline-link {
  border: 0;
  background: transparent;
  color: #1d4ed8;
  text-decoration: underline;
  padding: 0;
  cursor: pointer;
}

.view-toggle {
  display: inline-flex;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  overflow: hidden;
}

.view-toggle button {
  border: 0;
  background: #f8fafc;
  color: #1f2937;
  padding: 8px 12px;
  cursor: pointer;
}

.view-toggle button.active {
  background: #1d4ed8;
  color: white;
}

.my-work-btn {
  border-right: 1px solid #d1d5db !important;
}

.empty {
  padding: 24px;
  border: 1px dashed #cbd5e1;
  border-radius: 12px;
  background: #f8fafc;
  display: grid;
  gap: 10px;
}

.empty p {
  margin: 0;
  color: #334155;
}

.empty-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.empty-btn {
  border: 1px solid #93c5fd;
  border-radius: 8px;
  background: #eff6ff;
  color: #1d4ed8;
  padding: 6px 10px;
  cursor: pointer;
}

.empty-btn.secondary {
  border-color: #cbd5e1;
  background: #fff;
  color: #475569;
}

.empty-help {
  font-size: 12px;
  color: #475569;
}

.filters {
  display: grid;
  gap: 10px;
}

.status-panel {
  border: 1px solid #fecaca;
  background: #fff1f2;
  border-radius: 10px;
  padding: 10px 12px;
  display: grid;
  gap: 6px;
}

.status-title {
  margin: 0;
  color: #9f1239;
  font-size: 13px;
  font-weight: 700;
}

.status-detail {
  margin: 0;
  color: #7f1d1d;
  font-size: 12px;
}

.status-meta {
  margin: 0;
  color: #9f1239;
  font-size: 11px;
}

.status-actions {
  display: inline-flex;
  gap: 8px;
}

.status-actions button {
  border: 1px solid #fda4af;
  border-radius: 8px;
  background: #fff;
  color: #9f1239;
  padding: 4px 8px;
  cursor: pointer;
}

.today-actions {
  border: 1px solid #dbeafe;
  border-radius: 12px;
  background: linear-gradient(135deg, #f0f9ff, #f8fafc);
  padding: 14px;
}

.today-actions-header h3 {
  margin: 0;
  font-size: 16px;
  color: #0f172a;
}

.today-actions-header p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #475569;
}

.today-actions-grid {
  margin-top: 12px;
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
}

.today-card {
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  background: #fff;
  padding: 12px;
  display: grid;
  gap: 8px;
}

.today-title {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 8px;
}

.today-status {
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 600;
}

.today-status-urgent {
  background: #fee2e2;
  color: #b91c1c;
}

.today-status-normal {
  background: #dbeafe;
  color: #1d4ed8;
}

.today-desc {
  margin: 0;
  font-size: 12px;
  color: #475569;
  min-height: 34px;
}

.today-count {
  margin: 0;
  font-size: 12px;
  color: #0f172a;
  font-weight: 600;
}

.today-btn {
  justify-self: start;
  border: 0;
  border-radius: 8px;
  background: #0ea5e9;
  color: #fff;
  padding: 6px 10px;
  cursor: pointer;
}

.search-input {
  width: 100%;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 10px 12px;
  background: #fff;
}

.state-filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.ready-only {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #334155;
  font-size: 13px;
}

.filter-tip {
  margin: -2px 0 0;
  color: #475569;
  font-size: 12px;
}

.state-filters button {
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  background: #fff;
  color: #334155;
  padding: 6px 10px;
  cursor: pointer;
}

.state-filters button.active {
  border-color: #1d4ed8;
  background: #eff6ff;
  color: #1e40af;
}

.state-filters button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.reason-filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.reason-filters button {
  border: 1px dashed #cbd5e1;
  border-radius: 999px;
  background: #fff;
  color: #334155;
  padding: 6px 10px;
  cursor: pointer;
}

.reason-filters button.active {
  border-color: #b91c1c;
  color: #b91c1c;
  background: #fff1f2;
}

.active-filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-chip {
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  color: #1e40af;
  background: #eff6ff;
  cursor: pointer;
}

.group-actions {
  display: inline-flex;
  gap: 8px;
}

.group-actions button {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
  color: #334155;
  padding: 6px 10px;
  cursor: pointer;
}

.scene-groups {
  display: grid;
  gap: 12px;
}

.scene-group {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
  padding: 10px;
}

.scene-group-header {
  margin-bottom: 10px;
}

.scene-toggle {
  border: 0;
  background: transparent;
  color: #0f172a;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.scene-count {
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  padding: 2px 8px;
  font-size: 12px;
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}

.list {
  display: grid;
  gap: 10px;
}

.entry {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  border: 1px solid #e2e8f0;
  background: #fff;
  border-radius: 12px;
  padding: 14px;
}

.entry-main {
  min-width: 0;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 6px 0;
}

.title {
  font-weight: 600;
}

.state {
  font-size: 12px;
  border-radius: 999px;
  padding: 2px 8px;
  border: 1px solid currentColor;
}

.subtitle {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hit {
  background: #fef08a;
}

.hud-meta {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 11px;
  overflow-wrap: anywhere;
}

.lock-reason {
  margin: 6px 0 0;
  color: #b91c1c;
  font-size: 12px;
}

.open-btn {
  align-self: center;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
  padding: 6px 10px;
  cursor: pointer;
}

.open-btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.state-ready .state {
  color: #166534;
}

.state-preview .state {
  color: #92400e;
}

.state-locked .state {
  color: #b91c1c;
}
</style>

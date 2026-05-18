<template>
  <section class="delivery-page">
    <header class="delivery-hero">
      <div class="delivery-hero__main">
        <p class="delivery-kicker">标准交付包 V1</p>
        <h2>用户页面交付看板</h2>
        <p class="delivery-lead">按角色、模块、旅程和验收状态组织，直接进入可交付的业务入口。</p>
      </div>
      <div class="delivery-hero__status">
        <span class="status-dot"></span>
        <span>当前交付状态</span>
        <strong>可演示</strong>
      </div>
    </header>

    <section class="delivery-summary" aria-label="交付概览">
      <article v-for="item in summaryCards" :key="item.label" class="summary-tile">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.hint }}</small>
      </article>
    </section>

    <section class="delivery-section">
      <header class="section-header">
        <div>
          <h3>关键旅程</h3>
          <p>面向 PM、财务、采购、领导四类核心使用路径。</p>
        </div>
      </header>
      <div class="journey-grid">
        <article v-for="journey in journeys" :key="journey.key" class="journey-card">
          <div class="journey-card__head">
            <span class="role-pill">{{ journey.role }}</span>
            <strong>{{ journey.title }}</strong>
          </div>
          <ol class="journey-steps">
            <li v-for="step in journey.steps" :key="`${journey.key}-${step.scene}`">
              <button type="button" @click="openScene(step.scene)">
                <span>{{ step.label }}</span>
                <small>{{ step.scene }}</small>
              </button>
            </li>
          </ol>
        </article>
      </div>
    </section>

    <section class="delivery-section">
      <header class="section-header">
        <div>
          <h3>10 个交付模块</h3>
          <p>每个模块都有用户角色、入口和验收点。</p>
        </div>
      </header>
      <div class="module-table" role="table" aria-label="交付模块">
        <div class="module-row module-row--head" role="row">
          <span role="columnheader">模块</span>
          <span role="columnheader">核心用户</span>
          <span role="columnheader">入口</span>
          <span role="columnheader">验收点</span>
        </div>
        <div v-for="module in deliveryModules" :key="module.name" class="module-row" role="row">
          <strong role="cell">{{ module.name }}</strong>
          <span role="cell">{{ module.roles }}</span>
          <span role="cell" class="entry-list">
            <button
              v-for="scene in module.scenes"
              :key="`${module.name}-${scene}`"
              type="button"
              @click="openScene(scene)"
            >
              {{ scene }}
            </button>
          </span>
          <span role="cell">{{ module.acceptance }}</span>
        </div>
      </div>
    </section>

    <section class="delivery-section">
      <header class="section-header">
        <div>
          <h3>角色包</h3>
          <p>每个角色有默认首页和可见模块边界。</p>
        </div>
      </header>
      <div class="role-grid">
        <article v-for="role in roles" :key="role.key" class="role-card">
          <div>
            <strong>{{ role.name }}</strong>
            <span>{{ role.key }}</span>
          </div>
          <button type="button" @click="openScene(role.defaultScene)">
            默认首页 {{ role.defaultScene }}
          </button>
          <p>{{ role.scope }}</p>
        </article>
      </div>
    </section>

    <section class="delivery-section delivery-section--evidence">
      <header class="section-header">
        <div>
          <h3>验收证据</h3>
          <p>交付页面与系统验收项保持同一口径。</p>
        </div>
      </header>
      <div class="evidence-grid">
        <article v-for="item in evidence" :key="item.label" class="evidence-item">
          <span>{{ item.status }}</span>
          <strong>{{ item.label }}</strong>
          <small>{{ item.source }}</small>
        </article>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { readWorkspaceContext } from '../app/workspaceContext';
import { useRoute } from 'vue-router';

type DeliveryModule = {
  name: string;
  roles: string;
  scenes: string[];
  acceptance: string;
};
type Journey = {
  key: string;
  role: string;
  title: string;
  steps: Array<{ label: string; scene: string }>;
};
type RoleCard = {
  key: string;
  name: string;
  defaultScene: string;
  scope: string;
};

const router = useRouter();
const route = useRoute();

const summaryCards = [
  { label: '交付模块', value: '10', hint: '覆盖项目、采购、现场、财务、治理' },
  { label: '关键角色', value: '6', hint: 'PM / 财务 / 采购 / 领导 / 管理员 / 运营' },
  { label: '关键旅程', value: '4', hint: 'PM、财务、采购、领导闭环' },
  { label: '默认入口', value: '65', hint: '按场景和菜单统一进入' },
];

const deliveryModules: DeliveryModule[] = [
  { name: '项目立项与台账', roles: 'PM、采购经理', scenes: ['projects.intake', 'projects.list', 'projects.ledger'], acceptance: '项目创建、列表检索、台账补录可追溯' },
  { name: '项目执行与任务协同', roles: 'PM', scenes: ['projects.dashboard', 'projects.execution', 'task.center'], acceptance: '任务推进动作成功并在看板可见' },
  { name: '采购与物资协同', roles: '采购经理、PM', scenes: ['material.center', 'material.procurement', 'material.inbound'], acceptance: '采购、验收、入库入口可追踪' },
  { name: '现场执行与质量安全', roles: 'PM、领导', scenes: ['construction.plan', 'construction.diary', 'quality.center', 'safety.center'], acceptance: '计划、日志、质量、安全入口可见' },
  { name: '付款申请与审批', roles: '财务、PM', scenes: ['finance.payment_requests', 'finance.center'], acceptance: '审批动作可执行且状态变化可见' },
  { name: '资金与结算台账', roles: '财务', scenes: ['finance.payment_ledger', 'finance.treasury_ledger', 'finance.settlement_orders'], acceptance: '付款结果在资金与结算台账可追溯' },
  { name: '成本预算与利润分析', roles: 'PM、财务', scenes: ['cost.project_budget', 'cost.project_cost_ledger', 'cost.profit_compare'], acceptance: '预算、成本、利润对比页面有数据' },
  { name: '经营指标与领导看板', roles: '领导', scenes: ['portal.dashboard', 'finance.operating_metrics'], acceptance: '只读角色可查看指标且无执行噪声' },
  { name: '生命周期与治理审计', roles: '管理员、领导', scenes: ['portal.lifecycle', 'portal.capability_matrix'], acceptance: '能力矩阵与场景治理正常渲染' },
  { name: '主数据与工作台', roles: '全角色', scenes: ['data.dictionary', 'workspace.home', 'my_work.workspace'], acceptance: '角色登录后进入默认首页且无跳错' },
];

const journeys: Journey[] = [
  {
    key: 'pm',
    role: 'PM',
    title: '立项到执行闭环',
    steps: [
      { label: '项目立项', scene: 'projects.intake' },
      { label: '项目列表', scene: 'projects.list' },
      { label: '项目台账', scene: 'projects.ledger' },
      { label: '项目看板', scene: 'projects.dashboard' },
    ],
  },
  {
    key: 'finance',
    role: '财务',
    title: '付款审批与资金台账',
    steps: [
      { label: '付款申请审批', scene: 'finance.payment_requests' },
      { label: '财务中心', scene: 'finance.center' },
      { label: '资金台账', scene: 'finance.treasury_ledger' },
      { label: '结算单', scene: 'finance.settlement_orders' },
    ],
  },
  {
    key: 'purchase',
    role: '采购',
    title: '物资采购协同',
    steps: [
      { label: '物资中心', scene: 'material.center' },
      { label: '采购协同', scene: 'material.procurement' },
      { label: '验收入库', scene: 'material.inbound' },
      { label: '价格库', scene: 'material.price_library' },
    ],
  },
  {
    key: 'executive',
    role: '领导',
    title: '经营洞察与治理',
    steps: [
      { label: '领导看板', scene: 'portal.dashboard' },
      { label: '经营指标', scene: 'finance.operating_metrics' },
      { label: '能力矩阵', scene: 'portal.capability_matrix' },
      { label: '生命周期', scene: 'portal.lifecycle' },
    ],
  },
];

const roles: RoleCard[] = [
  { key: 'pm', name: '项目经理', defaultScene: 'projects.dashboard', scope: '立项、执行、采购协同、付款申请、成本预算' },
  { key: 'finance', name: '财务经理', defaultScene: 'finance.center', scope: '付款审批、资金结算、成本分析、主数据' },
  { key: 'purchase_manager', name: '采购经理', defaultScene: 'cost.project_boq', scope: '采购、物资、成本预算、项目基础资料' },
  { key: 'executive', name: '老板/领导', defaultScene: 'portal.dashboard', scope: '经营看板、风险洞察、治理矩阵，只读优先' },
  { key: 'admin', name: '系统管理员', defaultScene: 'portal.capability_matrix', scope: '全模块治理、配置和审计' },
  { key: 'ops', name: '运营专员', defaultScene: 'projects.list', scope: '项目台账、付款跟单、主数据维护' },
];

const evidence = [
  { label: '用户入口浏览器验收', status: 'PASS', source: 'verify.user.entry.delivery.browser_acceptance' },
  { label: '场景交付角色公司矩阵', status: 'PASS', source: 'verify.scene.delivery.readiness.role_company_matrix' },
  { label: '产品交付主线验收', status: 'PASS', source: 'verify.product.delivery.mainline' },
  { label: '入口映射与无动作回归', status: 'PASS', source: 'verify.scene.no_action_scene.guard' },
];

function openScene(sceneKey: string) {
  router.push({
    path: `/s/${sceneKey}`,
    query: readWorkspaceContext(route.query as Record<string, unknown>),
  }).catch(() => {});
}
</script>

<style scoped>
.delivery-page {
  display: grid;
  gap: 18px;
  padding: 22px;
  color: var(--sc-app-text-primary);
}

.delivery-hero,
.delivery-section,
.summary-tile,
.journey-card,
.role-card,
.evidence-item {
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-panel);
  box-shadow: var(--sc-app-shadow);
}

.delivery-hero {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  padding: 22px;
}

.delivery-hero__main {
  display: grid;
  gap: 8px;
}

.delivery-kicker {
  margin: 0;
  color: var(--sc-app-text-secondary);
  font-size: 13px;
  font-weight: 700;
}

.delivery-hero h2,
.section-header h3 {
  margin: 0;
  letter-spacing: 0;
}

.delivery-hero h2 {
  font-size: 26px;
}

.delivery-lead,
.section-header p,
.journey-steps small,
.role-card span,
.role-card p,
.evidence-item small,
.summary-tile small {
  color: var(--sc-app-text-secondary);
}

.delivery-lead {
  max-width: 720px;
  margin: 0;
  line-height: 1.7;
}

.delivery-hero__status {
  display: grid;
  align-content: center;
  justify-items: end;
  min-width: 150px;
  gap: 4px;
  color: var(--sc-app-text-secondary);
}

.delivery-hero__status strong {
  color: var(--sc-app-success-text);
  font-size: 20px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: var(--sc-app-success-text);
}

.delivery-summary,
.journey-grid,
.role-grid,
.evidence-grid {
  display: grid;
  gap: 12px;
}

.delivery-summary {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.summary-tile,
.journey-card,
.role-card,
.evidence-item {
  padding: 14px;
}

.summary-tile {
  display: grid;
  gap: 6px;
}

.summary-tile strong {
  font-size: 24px;
}

.delivery-section {
  display: grid;
  gap: 14px;
  padding: 18px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.section-header p {
  margin: 6px 0 0;
}

.journey-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.journey-card {
  display: grid;
  gap: 12px;
}

.journey-card__head {
  display: grid;
  gap: 8px;
}

.role-pill {
  width: fit-content;
  border: 1px solid var(--sc-app-border);
  border-radius: 999px;
  padding: 3px 9px;
  background: var(--sc-app-subtle-bg);
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.journey-steps {
  display: grid;
  gap: 8px;
  margin: 0;
  padding-left: 18px;
}

.journey-steps button,
.entry-list button,
.role-card button {
  border: 1px solid var(--sc-app-border);
  border-radius: 6px;
  background: var(--sc-app-subtle-bg);
  color: var(--sc-app-text-primary);
  cursor: pointer;
}

.journey-steps button {
  display: grid;
  width: 100%;
  gap: 2px;
  padding: 8px;
  text-align: left;
}

.module-table {
  display: grid;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  overflow: hidden;
}

.module-row {
  display: grid;
  grid-template-columns: minmax(130px, 1.1fr) minmax(100px, 0.8fr) minmax(220px, 1.5fr) minmax(220px, 1.5fr);
  gap: 12px;
  align-items: center;
  padding: 11px 12px;
  border-bottom: 1px solid var(--sc-app-border);
}

.module-row:last-child {
  border-bottom: none;
}

.module-row--head {
  background: var(--sc-app-subtle-bg);
  color: var(--sc-app-text-secondary);
  font-weight: 700;
}

.entry-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.entry-list button,
.role-card button {
  padding: 6px 8px;
  font-size: 12px;
}

.role-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.role-card {
  display: grid;
  gap: 10px;
}

.role-card div {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.role-card p {
  margin: 0;
  line-height: 1.55;
}

.evidence-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.evidence-item {
  display: grid;
  gap: 6px;
}

.evidence-item span {
  color: var(--sc-app-success-text);
  font-weight: 700;
}

@media (max-width: 1180px) {
  .delivery-summary,
  .journey-grid,
  .evidence-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .module-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .delivery-page {
    padding: 12px;
  }

  .delivery-hero,
  .section-header {
    display: grid;
  }

  .delivery-hero__status {
    justify-items: start;
  }

  .delivery-summary,
  .journey-grid,
  .role-grid,
  .evidence-grid {
    grid-template-columns: 1fr;
  }
}
</style>

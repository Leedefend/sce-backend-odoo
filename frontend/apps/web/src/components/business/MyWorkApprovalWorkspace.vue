<template>
  <section class="product-work" aria-labelledby="my-work-title">
    <header class="product-work__header">
      <div>
        <h1 id="my-work-title">我的工作</h1>
        <p>只展示当前账号、公司和项目范围内真正可处理的业务事项。</p>
      </div>
      <button type="button" class="secondary" :disabled="busy" @click="$emit('refresh')">刷新</button>
    </header>

    <div class="product-work__counts" aria-label="工作项汇总">
      <button
        v-for="section in workspace.sections"
        :key="section.key"
        type="button"
        class="count-card"
        :data-section-key="section.key"
        :class="{ active: activeSection === section.key }"
        @click="activeSection = section.key"
      >
        <span>{{ section.label }}</span>
        <strong>{{ section.count }}</strong>
      </button>
    </div>

    <p v-if="feedback" class="feedback" :class="{ error: feedbackError }" role="status">{{ feedback }}</p>

    <section v-for="section in visibleSections" :key="section.key" class="work-section" :data-section-key="section.key">
      <h2>{{ section.label }} <span>{{ section.count }}</span></h2>
      <p v-if="!section.items.length" class="empty">当前范围内没有{{ section.label }}事项。</p>
      <article v-for="item in section.items" :key="item.key" class="work-card" :data-work-item-key="item.key">
        <div class="work-card__main">
          <div class="work-card__identity">
            <span class="business-type">{{ item.business_type }}</span>
            <span class="status-badge">{{ item.state.label }}</span>
          </div>
          <h3>{{ item.record.label }}</h3>
          <dl>
            <div><dt>项目</dt><dd>{{ item.project?.label || '未关联' }}</dd></div>
            <div><dt>公司</dt><dd>{{ item.company?.label || '未关联' }}</dd></div>
            <div><dt>往来方</dt><dd>{{ item.partner?.label || '未填写' }}</dd></div>
            <div><dt>金额</dt><dd>{{ formatMoney(item) }}</dd></div>
            <div><dt>发起人</dt><dd>{{ item.initiator?.label || '未知' }}</dd></div>
            <div><dt>发起时间</dt><dd>{{ formatDate(item.initiated_at) }}</dd></div>
          </dl>
        </div>
        <div class="work-card__actions">
          <button type="button" class="secondary" @click="openItem(item)">打开详情</button>
          <button
            v-for="action in item.actions"
            :key="action.key"
            type="button"
            :disabled="busy"
            @click="beginAction(item, action)"
          >
            {{ action.label }}
          </button>
        </div>
      </article>
    </section>

    <dialog ref="dialogRef" class="intent-dialog" @close="restoreFocus">
      <form method="dialog" @submit.prevent>
        <h2>{{ pendingAction?.label || '确认操作' }}</h2>
        <p v-if="pendingItem">
          {{ pendingItem.record.label }} · {{ formatMoney(pendingItem) }}
        </p>
        <label v-if="pendingAction?.requires_reason">
          拒绝原因
          <textarea ref="reasonRef" v-model.trim="reason" rows="3" required aria-describedby="reason-help" />
          <small id="reason-help">请说明拒绝原因，提交后会写入正式审批记录。</small>
        </label>
        <p v-if="dialogError" class="feedback error" role="alert">{{ dialogError }}</p>
        <div class="dialog-actions">
          <button type="button" class="secondary" :disabled="busy" @click="closeDialog">取消</button>
          <button type="button" :disabled="busy" @click="confirmAction">
            {{ busy ? '提交中…' : `确认${pendingAction?.label || ''}` }}
          </button>
        </div>
      </form>
    </dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, ref } from 'vue';
import { useRouter } from 'vue-router';
import { executePaymentRequestAction } from '../../api/paymentRequest';
import type { ProductMyWorkAction, ProductMyWorkItem, ProductMyWorkWorkspace } from '../../api/myWork';

const props = defineProps<{ workspace: ProductMyWorkWorkspace }>();
const emit = defineEmits<{ refresh: [] }>();
const router = useRouter();
const activeSection = ref('todo');
const busy = ref(false);
const feedback = ref('');
const feedbackError = ref(false);
const dialogError = ref('');
const reason = ref('');
const pendingItem = ref<ProductMyWorkItem | null>(null);
const pendingAction = ref<ProductMyWorkAction | null>(null);
const dialogRef = ref<HTMLDialogElement | null>(null);
const reasonRef = ref<HTMLTextAreaElement | null>(null);
let actionTrigger: HTMLElement | null = null;

const visibleSections = computed(() => {
  const selected = props.workspace.sections.find((row) => row.key === activeSection.value);
  return selected ? [selected] : props.workspace.sections;
});

function formatMoney(item: ProductMyWorkItem) {
  if (item.amount.value === null || item.amount.value === undefined) return '未填写';
  const digits = Number.isFinite(item.amount.digits) ? Number(item.amount.digits) : 2;
  return `${item.amount.currency_symbol || ''}${Number(item.amount.value).toLocaleString('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })} ${item.amount.currency || ''}`.trim();
}

function formatDate(value?: string) {
  return value ? String(value).replace('T', ' ').slice(0, 16) : '未知';
}

function openItem(item: ProductMyWorkItem) {
  void router.push(item.target.route);
}

async function beginAction(item: ProductMyWorkItem, action: ProductMyWorkAction) {
  if (busy.value) return;
  actionTrigger = document.activeElement as HTMLElement | null;
  pendingItem.value = item;
  pendingAction.value = action;
  reason.value = '';
  dialogError.value = '';
  dialogRef.value?.showModal();
  await nextTick();
  if (action.requires_reason) reasonRef.value?.focus();
  else dialogRef.value?.querySelector<HTMLButtonElement>('.dialog-actions button:last-child')?.focus();
}

function closeDialog() {
  dialogRef.value?.close();
}

function restoreFocus() {
  actionTrigger?.focus();
  actionTrigger = null;
}

async function confirmAction() {
  const item = pendingItem.value;
  const action = pendingAction.value;
  if (!item || !action || busy.value) return;
  if (action.requires_reason && !reason.value) {
    dialogError.value = '请填写拒绝原因。';
    reasonRef.value?.focus();
    return;
  }
  busy.value = true;
  dialogError.value = '';
  try {
    const result = await executePaymentRequestAction({
      paymentRequestId: item.target.record_id,
      action: action.key,
      reason: reason.value,
    });
    if (result.data.success === false) throw new Error(result.data.message || '操作失败');
    feedback.value = `${item.record.label}已${action.label}，工作项已同步刷新。`;
    feedbackError.value = false;
    closeDialog();
    emit('refresh');
  } catch (error) {
    dialogError.value = error instanceof Error ? error.message : '操作失败，请稍后重试。';
    feedback.value = dialogError.value;
    feedbackError.value = true;
  } finally {
    busy.value = false;
  }
}
</script>

<style scoped>
.product-work { display: grid; gap: 20px; }
.product-work__header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }
.product-work__header h1 { margin: 0; font-size: 28px; }
.product-work__header p { margin: 8px 0 0; color: var(--text-secondary, #64748b); }
.product-work__counts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.count-card { display: flex; justify-content: space-between; align-items: center; min-height: 72px; padding: 16px; background: var(--surface, #fff); color: inherit; border: 1px solid var(--border, #dbe2ea); border-radius: 12px; }
.count-card strong { font-size: 24px; }
.count-card.active { border-color: var(--primary, #2563eb); box-shadow: 0 0 0 2px rgb(37 99 235 / 12%); }
.work-section { display: grid; gap: 12px; }
.work-section h2 { margin: 0; font-size: 20px; }
.work-section h2 span { color: var(--text-secondary, #64748b); font-weight: 500; }
.work-card { display: flex; justify-content: space-between; gap: 20px; padding: 18px; background: var(--surface, #fff); border: 1px solid var(--border, #dbe2ea); border-radius: 12px; }
.work-card__main { min-width: 0; flex: 1; }
.work-card__identity { display: flex; gap: 8px; align-items: center; }
.business-type, .status-badge { display: inline-flex; padding: 3px 8px; border-radius: 999px; background: #eef4ff; color: #1d4ed8; font-size: 12px; }
.status-badge { background: #f1f5f9; color: #334155; }
.work-card h3 { margin: 10px 0 14px; overflow-wrap: anywhere; }
.work-card dl { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px 20px; margin: 0; }
.work-card dl div { min-width: 0; }
.work-card dt { color: var(--text-secondary, #64748b); font-size: 12px; }
.work-card dd { margin: 3px 0 0; overflow-wrap: anywhere; }
.work-card__actions { display: flex; flex-wrap: wrap; gap: 8px; align-content: flex-start; }
.empty { padding: 24px; border: 1px dashed var(--border, #dbe2ea); border-radius: 12px; color: var(--text-secondary, #64748b); }
.feedback { margin: 0; padding: 10px 12px; border-radius: 8px; background: #ecfdf5; color: #166534; }
.feedback.error { background: #fef2f2; color: #b91c1c; }
.intent-dialog { width: min(480px, calc(100vw - 32px)); border: 0; border-radius: 14px; padding: 22px; box-shadow: 0 24px 70px rgb(15 23 42 / 28%); }
.intent-dialog::backdrop { background: rgb(15 23 42 / 45%); }
.intent-dialog h2 { margin-top: 0; }
.intent-dialog label { display: grid; gap: 6px; }
.intent-dialog textarea { width: 100%; box-sizing: border-box; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
@media (max-width: 640px) {
  .product-work__header, .work-card { flex-direction: column; }
  .product-work__counts { grid-template-columns: 1fr; }
  .work-card dl { grid-template-columns: 1fr; }
  .work-card__actions { width: 100%; }
  .work-card__actions button { flex: 1 1 auto; }
}
</style>

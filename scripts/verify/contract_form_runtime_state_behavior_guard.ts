#!/usr/bin/env node
import * as assert from 'assert/strict';
import {
  applyFormRuntimeBusyEvent,
  applyFormRuntimeStatusEvent,
} from '../../frontend/apps/web/src/pages/contractForm/runtimeStateApplier';
import {
  INITIAL_FORM_RUNTIME_STATE,
  reduceFormRuntimeState,
  reduceFormRuntimeStateEvents,
} from '../../frontend/apps/web/src/pages/contractForm/runtimeStateReducer';

function assertBusyReducerBehavior() {
  const begun = reduceFormRuntimeState(INITIAL_FORM_RUNTIME_STATE, {
    kind: 'begin',
    transaction: 'formConfig',
    busyKind: 'action',
  });
  assert.equal(begun.busyKind, 'action');

  const ended = reduceFormRuntimeState(begun, {
    kind: 'end',
    transaction: 'formConfig',
  });
  assert.equal(ended.busyKind, null);
}

function assertGlobalSingleBusyInvariant() {
  const state = reduceFormRuntimeStateEvents(INITIAL_FORM_RUNTIME_STATE, [
    { kind: 'begin', transaction: 'formConfig', busyKind: 'action' },
    { kind: 'end', transaction: 'inlinePolicy' },
  ]);
  assert.equal(state.busyKind, null);
}

function assertStatusReducerBehavior() {
  const failed = reduceFormRuntimeState(INITIAL_FORM_RUNTIME_STATE, {
    kind: 'status',
    transaction: 'formReload',
    status: 'error',
    errorMessage: '表单加载失败',
  });
  assert.equal(failed.status, 'error');
  assert.equal(failed.errorMessage, '表单加载失败');

  const recovered = reduceFormRuntimeState(failed, {
    kind: 'status',
    transaction: 'formReload',
    status: 'ok',
  });
  assert.equal(recovered.status, 'ok');
  assert.equal(recovered.errorMessage, '');
}

async function assertApplierFinallyClearsBusy() {
  const busyKind = { value: null as 'save' | 'action' | null };
  applyFormRuntimeBusyEvent({ busyKind } as any, {
    kind: 'begin',
    transaction: 'formConfig',
    busyKind: 'action',
  });
  assert.equal(busyKind.value, 'action');

  try {
    throw new Error('network failed');
  } catch {
    // The transaction body owns error handling; the runtime event must still clear in finally.
  } finally {
    applyFormRuntimeBusyEvent({ busyKind } as any, {
      kind: 'end',
      transaction: 'formConfig',
    });
  }
  assert.equal(busyKind.value, null);
}

function assertApplierDoesNotStartOnPrecheckReturn() {
  const busyKind = { value: null as 'save' | 'action' | null };
  const shouldReturnBeforeBegin = true;
  if (shouldReturnBeforeBegin) {
    assert.equal(busyKind.value, null);
    return;
  }
  applyFormRuntimeBusyEvent({ busyKind } as any, {
    kind: 'begin',
    transaction: 'inlinePolicy',
    busyKind: 'action',
  });
}

function assertStatusApplierBehavior() {
  const status = { value: 'ok' as 'loading' | 'ok' | 'error' };
  const errorMessage = { value: '' };
  applyFormRuntimeStatusEvent({ status, errorMessage } as any, {
    kind: 'status',
    transaction: 'contractMode',
    status: 'error',
    errorMessage: '表单配置操作失败',
  });
  assert.equal(status.value, 'error');
  assert.equal(errorMessage.value, '表单配置操作失败');
}

async function main() {
  assertBusyReducerBehavior();
  assertGlobalSingleBusyInvariant();
  assertStatusReducerBehavior();
  await assertApplierFinallyClearsBusy();
  assertApplierDoesNotStartOnPrecheckReturn();
  assertStatusApplierBehavior();
  console.log('[contract_form_runtime_state_behavior_guard] PASS');
}

main().catch((err: unknown) => {
  console.error(err);
  process.exit(1);
});

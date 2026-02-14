# Phase 12 Stage 4: Payment Handoff Actor Match Contract

## Scope

- Keep payment approval business behavior unchanged.
- Extend action-surface contract so frontend can guide handoff by current actor role.

## Backend Contract Additions

Intent: `payment.request.available_actions`

Per action item now includes:

- `actor_matches_required_role: boolean`
- `handoff_required: boolean`

Existing fields remain unchanged:

- `required_role_key`
- `required_role_label`
- `required_group_xmlid`
- `handoff_hint`
- `delivery_priority`

## Frontend Delivery

- `ModelFormPage` renders actor-role match hint in semantic action cards.
- When role mismatch exists, UI shows explicit handoff copy:
  - `请转交给 <角色> 处理`
- Action-surface evidence utilities in user form:
  - `复制动作面` copies structured JSON (actions + role hints + priority).
  - `导出动作面` downloads JSON for delivery evidence.
  - `导出历史` downloads filtered action history JSON.
  - `导出证据包` downloads one bundle (action surface + action history + last feedback/trace).
  - `复制执行包` / `导出执行包` near feedback trace for latest execution snapshot.
  - `复制转交说明` (for handoff-required actions) copies a plain-text handoff note with role and trace.
  - stale refresh hint highlights action surface older than 60 seconds.
  - stale banner blocks user attention and provides one-click refresh before execution.
  - stale execution guard: semantic action execution asks for confirmation when surface is stale; cancel triggers auto-refresh.

## Verification

- `make verify.frontend.typecheck.strict` ✅
- `make verify.frontend.build` ✅
- `make verify.portal.payment_request_approval_smoke.container DB_NAME=sc_demo` ✅
- `make verify.portal.payment_request_approval_handoff_smoke.container DB_NAME=sc_demo` ✅

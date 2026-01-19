# P2 API & Intent Contract (Draft)

Goal: Provide stable intent/API contract for P2 capabilities, aligned with full capability v1.1.

## 1) Intent Types
- api.data: read-only data/insight payloads
- execute_button: server-side actions (object methods / actions)
- permission.check: lightweight authorization probes

## 2) Common Response Envelope
```
{
  "ok": true|false,
  "data": {...},
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable",
    "debug_id": "trace-id"
  }
}
```

## Action Payload Standardization
All execute_button returns MUST use the common envelope.

Example:
```
{
  "ok": true,
  "data": {
    "type": "ir.actions.act_window",
    "action": { ... }
  }
}
```

Rules:
- No raw action dicts at top-level.
- UI consumes only envelope; action is nested in data.action.

## 3) Intent: P2 Task Readiness (api.data)
Endpoint: `/api/insight?model=project.task&id=...&scene=task.entry`
Returns:
- readiness: { status, missing_fields, blockers, recommended_action }
- ui_model: { hero, next_best, more }

Errors:
- TASK_NOT_FOUND
- TASK_ACCESS_DENIED

## 4) Intent: Open WBS (execute_button)
Action: `action_open_wbs`
Input: { project_id }
Returns: standard action dict
Errors:
- ACTION_ACCESS_DENIED
- ACTION_UNAVAILABLE

## 5) Intent: Bind WBS to Task (execute_button)
Action: `action_link_wbs_task`
Input: { task_id, work_id }
Returns: { ok, data: { link_id } }
Errors:
- TASK_GUARD_MISSING_FIELDS
- WBS_ACCESS_DENIED

## 6) Intent: Submit Progress (execute_button)
Action: `action_submit_progress`
Input: { progress_entry_id }
Returns: { ok, data: { state } }
Errors:
- PROGRESS_INVALID
- PROGRESS_ACCESS_DENIED

## 7) Intent: Payment Submit (execute_button)
Action: `payment.request.action_submit`
Input: { request_id }
Returns: { ok, data: { state } }
Errors:
- P0_PROJECT_TERMINAL_BLOCKED
- P0_PAYMENT_SETTLEMENT_NOT_READY
- P0_PAYMENT_OVER_BALANCE

## 8) Permission Checks (permission.check)
Endpoint: `/api/permission/check`
Input: { model, action }
Returns: { ok, data: { allowed: true|false } }

## Notes
- All execute_button intents must be idempotent or guarded.
- Error codes must be stable for UI mapping.

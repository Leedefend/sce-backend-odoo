# Release Operator Write Model v1

## Goal

Define a stable write model contract for release operator actions so that:

- `promote`
- `approve`
- `rollback`

all enter the release system through a single validated write model before reaching `ReleaseOrchestrator`.

## Contract

Contract version:

- `release_operator_write_model_v1`

Shared shape:

```json
{
  "contract_version": "release_operator_write_model_v1",
  "operation": "promote_snapshot | approve_action | rollback_snapshot",
  "identity": {
    "product_key": "construction.standard",
    "base_product_key": "construction",
    "edition_key": "standard"
  },
  "payload": {}
}
```

## Operations

### promote_snapshot

```json
{
  "payload": {
    "snapshot_id": 123,
    "replace_active": true,
    "note": "optional"
  }
}
```

### approve_action

```json
{
  "payload": {
    "action_id": 456,
    "execute_after_approval": true,
    "note": "optional"
  }
}
```

### rollback_snapshot

```json
{
  "payload": {
    "target_snapshot_id": 789,
    "note": "optional"
  }
}
```

## Runtime Rule

- Frontend and handlers may still submit plain params.
- Backend handler must first build `release_operator_write_model_v1`.
- Only the validated write model may enter `ReleaseOrchestrator.submit_write_model()`.

## Layer Boundary

- Write model building: `addons/smart_core/delivery/release_operator_write_model_service.py`
- Action execution: `addons/smart_core/delivery/release_orchestrator.py`
- Intent entry: `addons/smart_core/handlers/release_operator.py`

No business execution rule is moved into frontend.

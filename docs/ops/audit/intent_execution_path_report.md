# Intent Execution Path Report

- write_intent_count: 37
- collision_count: 4
- non_allowlisted_write_count: 18

## Signature Collisions

- `21beebee3fc3` intents=global.message.read, global.message.send
- `6c53a857f03b` intents=my.work.complete, my.work.complete_batch
- `6f3d9c51796e` intents=release.operator.approve, release.operator.freeze, release.operator.promote, release.operator.rollback, release.operator.set_page_enabled, release.operator.sync_policy, release.operator.update_page_policy, release.operator.update_policy
- `bd3f5e83fbcc` intents=payment.request.approve, payment.request.done, payment.request.reject, payment.request.submit

## Non-Allowlisted Write Intents

- `chatter.activity.schedule` (addons/smart_core/handlers/chatter_activity_schedule.py)
- `chatter.activity.update` (addons/smart_core/handlers/chatter_activity_update.py)
- `cost.tracking.record.create` (addons/smart_construction_core/handlers/cost_tracking_record_create.py)
- `global.message.read` (addons/smart_core/handlers/global_messages.py)
- `global.message.send` (addons/smart_core/handlers/global_messages.py)
- `payment.record.create` (addons/smart_construction_core/handlers/payment_slice_record_create.py)
- `release.operator.approve` (addons/smart_core/handlers/release_operator.py)
- `release.operator.freeze` (addons/smart_core/handlers/release_operator.py)
- `release.operator.promote` (addons/smart_core/handlers/release_operator.py)
- `release.operator.rollback` (addons/smart_core/handlers/release_operator.py)
- `release.operator.set_page_enabled` (addons/smart_core/handlers/release_operator.py)
- `release.operator.sync_policy` (addons/smart_core/handlers/release_operator.py)
- `release.operator.update_page_policy` (addons/smart_core/handlers/release_operator.py)
- `release.operator.update_policy` (addons/smart_core/handlers/release_operator.py)
- `risk.action.execute` (addons/smart_construction_core/handlers/risk_action_execute.py)
- `search.favorite.set` (addons/smart_core/handlers/search_favorite_set.py)
- `telemetry.track` (addons/smart_construction_core/handlers/telemetry_track.py)
- `user.view.preference.set` (addons/smart_core/handlers/user_view_preference.py)

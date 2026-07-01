# Intent Capability Matrix Audit

- intent_count: 101
- missing_test_count: 6
- missing_smoke_target_count: 72
- write_without_required_groups_count: 16
- write_without_acl_hint_count: 29

## Matrix

| intent_type | layer | required_groups | acl_mode | etag_enabled | has_test | has_smoke_target | is_write | orm_used | may_sudo | source |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| api.data | core | 1 | - | N | Y | Y | N | Y | Y | addons/smart_core/handlers/api_data.py |
| api.data.batch | core | 1 | explicit_check | N | Y | N | Y | Y | N | addons/smart_core/handlers/api_data_batch.py |
| api.data.create | core | 1 | explicit_check | N | Y | Y | Y | Y | Y | addons/smart_core/handlers/api_data_write.py |
| api.data.unlink | core | 1 | explicit_check | N | Y | N | Y | Y | N | addons/smart_core/handlers/api_data_unlink.py |
| api.onchange | domain | 1 | explicit_check | N | Y | Y | N | Y | N | addons/smart_core/handlers/api_onchange.py |
| app.catalog | domain | 0 | - | Y | Y | N | N | N | N | addons/smart_core/handlers/app_shell.py |
| app.catalog | domain | 0 | - | Y | Y | N | N | Y | N | addons/smart_construction_core/handlers/app_catalog.py |
| app.nav | domain | 0 | - | Y | Y | N | N | N | N | addons/smart_core/handlers/app_shell.py |
| app.nav | domain | 0 | - | Y | Y | N | N | N | N | addons/smart_construction_core/handlers/app_nav.py |
| app.open | domain | 0 | - | N | Y | Y | N | N | N | addons/smart_core/handlers/app_shell.py |
| app.open | domain | 0 | - | N | Y | Y | N | N | N | addons/smart_construction_core/handlers/app_open.py |
| auth.logout | domain | 0 | - | N | Y | Y | N | Y | Y | addons/smart_core/handlers/login.py |
| business.evidence.trace | domain | 1 | - | N | Y | N | N | N | N | addons/smart_construction_core/handlers/business_evidence_trace.py |
| capability.describe | domain | 0 | - | N | Y | N | N | Y | Y | addons/smart_construction_core/handlers/capability_describe.py |
| capability.visibility.report | domain | 0 | - | N | Y | N | N | Y | Y | addons/smart_construction_core/handlers/capability_visibility_report.py |
| chatter.activity.schedule | domain | 1 | explicit_check | N | Y | N | Y | Y | Y | addons/smart_core/handlers/chatter_activity_schedule.py |
| chatter.activity.update | domain | 1 | explicit_check | N | N | N | Y | Y | Y | addons/smart_core/handlers/chatter_activity_update.py |
| chatter.post | domain | 1 | explicit_check | N | Y | N | Y | Y | N | addons/smart_core/handlers/chatter_post.py |
| chatter.timeline | domain | 0 | - | N | Y | N | N | Y | Y | addons/smart_core/handlers/chatter_timeline.py |
| collaboration.users.search | domain | 0 | - | N | N | N | N | Y | N | addons/smart_core/handlers/collaboration_users.py |
| cost.tracking.block.fetch | domain | 1 | - | N | Y | N | N | N | N | addons/smart_construction_core/handlers/cost_tracking_block_fetch.py |
| cost.tracking.enter | domain | 1 | - | N | Y | N | N | N | N | addons/smart_construction_core/handlers/cost_tracking_enter.py |
| cost.tracking.record.create | domain | 1 | explicit_check | N | Y | N | Y | N | N | addons/smart_construction_core/handlers/cost_tracking_record_create.py |
| dashboard.company.enter | domain | 1 | - | N | Y | N | N | N | N | addons/smart_construction_core/handlers/dashboard_company_enter.py |
| execute_button | core | 1 | explicit_check | N | Y | Y | Y | Y | Y | addons/smart_core/handlers/execute_button.py |
| file.download | core | 0 | - | N | Y | N | N | Y | Y | addons/smart_core/handlers/file_download.py |
| file.upload | core | 1 | explicit_check | N | Y | Y | Y | Y | N | addons/smart_core/handlers/file_upload.py |
| global.message.conversations | domain | 0 | - | N | N | N | N | Y | N | addons/smart_core/handlers/global_messages.py |
| global.message.inbox | domain | 0 | - | N | N | N | N | Y | N | addons/smart_core/handlers/global_messages.py |
| global.message.read | domain | 1 | explicit_check | N | N | N | Y | Y | N | addons/smart_core/handlers/global_messages.py |
| global.message.send | domain | 1 | explicit_check | N | N | N | Y | Y | N | addons/smart_core/handlers/global_messages.py |
| load_contract | domain | 0 | - | N | Y | Y | N | Y | Y | addons/smart_core/handlers/load_contract.py |
| load_metadata | domain | 0 | - | N | Y | N | N | N | N | addons/smart_core/handlers/load_metadata.py |
| load_view | domain | 0 | - | N | Y | Y | N | N | N | addons/smart_core/handlers/load_view.py |
| login | domain | 0 | - | N | Y | Y | N | Y | Y | addons/smart_core/handlers/login.py |
| meta.describe_model | domain | 0 | - | N | Y | N | N | N | N | addons/smart_core/handlers/meta_describe.py |
| meta.intent_catalog | domain | 0 | - | Y | Y | N | N | N | N | addons/smart_core/handlers/meta_intent_catalog.py |
| my.work.complete | domain | 1 | explicit_check | N | Y | N | Y | Y | N | addons/smart_construction_core/handlers/my_work_complete.py |
| my.work.complete_batch | domain | 1 | explicit_check | N | Y | N | Y | Y | N | addons/smart_construction_core/handlers/my_work_complete.py |
| my.work.summary | domain | 0 | - | N | Y | N | N | Y | Y | addons/smart_construction_core/handlers/my_work_summary.py |
| payment.block.fetch | domain | 1 | - | N | Y | N | N | N | N | addons/smart_construction_core/handlers/payment_slice_block_fetch.py |
| payment.enter | domain | 1 | - | N | Y | N | N | N | N | addons/smart_construction_core/handlers/payment_slice_enter.py |
| payment.record.create | domain | 1 | explicit_check | N | Y | N | Y | N | N | addons/smart_construction_core/handlers/payment_slice_record_create.py |
| payment.request.approve | domain | 0 | - | N | Y | Y | Y | Y | N | addons/smart_construction_core/handlers/payment_request_approval.py |
| payment.request.available_actions | domain | 0 | - | N | Y | N | N | Y | Y | addons/smart_construction_core/handlers/payment_request_available_actions.py |
| payment.request.done | domain | 0 | - | N | Y | Y | Y | Y | N | addons/smart_construction_core/handlers/payment_request_approval.py |
| payment.request.execute | domain | 1 | explicit_check | N | Y | N | Y | N | N | addons/smart_construction_core/handlers/payment_request_execute.py |
| payment.request.reject | domain | 0 | - | N | Y | Y | Y | Y | N | addons/smart_construction_core/handlers/payment_request_approval.py |
| payment.request.submit | domain | 1 | - | N | Y | Y | Y | Y | N | addons/smart_construction_core/handlers/payment_request_approval.py |
| permission.check | core | 0 | - | N | Y | N | N | Y | Y | addons/smart_core/handlers/permission_check.py |
| project.connection.transition | domain | 1 | - | N | Y | N | N | Y | N | addons/smart_construction_core/handlers/project_connection_transition.py |
| project.context.search | domain | 0 | - | N | Y | N | N | N | N | addons/smart_core/handlers/project_context.py |
| project.dashboard | domain | 0 | - | N | Y | Y | N | N | N | addons/smart_construction_core/handlers/project_dashboard.py |
| project.dashboard.block.fetch | domain | 1 | - | N | Y | N | N | N | N | addons/smart_construction_core/handlers/project_dashboard_block_fetch.py |
| project.dashboard.enter | domain | 1 | - | N | Y | N | N | N | Y | addons/smart_construction_core/handlers/project_dashboard_enter.py |
| project.dashboard.open | domain | 1 | - | N | Y | N | N | N | N | addons/smart_construction_core/handlers/project_dashboard_open.py |
| project.entry.context.options | domain | 1 | - | N | Y | N | N | N | N | addons/smart_construction_core/handlers/project_entry_context_options.py |
| project.entry.context.resolve | domain | 1 | - | N | Y | N | N | N | N | addons/smart_construction_core/handlers/project_entry_context_resolve.py |
| project.execution.advance | domain | 1 | - | N | Y | N | N | N | N | addons/smart_construction_core/handlers/project_execution_advance.py |
| project.execution.block.fetch | domain | 1 | - | N | Y | N | N | N | N | addons/smart_construction_core/handlers/project_execution_block_fetch.py |
| project.execution.enter | domain | 1 | - | N | Y | N | N | N | N | addons/smart_construction_core/handlers/project_execution_enter.py |
| project.initiation.enter | domain | 1 | - | N | Y | N | N | Y | N | addons/smart_construction_core/handlers/project_initiation_enter.py |
| project.plan_bootstrap.block.fetch | domain | 1 | - | N | Y | N | N | N | N | addons/smart_construction_core/handlers/project_plan_bootstrap_block_fetch.py |
| project.plan_bootstrap.enter | domain | 1 | - | N | Y | N | N | N | N | addons/smart_construction_core/handlers/project_plan_bootstrap_enter.py |
| release.operator.approve | domain | 0 | - | N | Y | N | Y | Y | Y | addons/smart_core/handlers/release_operator.py |
| release.operator.freeze | domain | 0 | - | N | Y | N | Y | Y | Y | addons/smart_core/handlers/release_operator.py |
| release.operator.promote | domain | 0 | - | N | Y | N | Y | Y | Y | addons/smart_core/handlers/release_operator.py |
| release.operator.rollback | domain | 0 | - | N | Y | N | Y | Y | Y | addons/smart_core/handlers/release_operator.py |
| release.operator.runtime_probe | domain | 0 | - | N | Y | N | N | Y | Y | addons/smart_core/handlers/release_operator.py |
| release.operator.set_page_enabled | domain | 0 | - | N | Y | N | Y | Y | Y | addons/smart_core/handlers/release_operator.py |
| release.operator.surface | domain | 0 | - | N | Y | N | N | Y | Y | addons/smart_core/handlers/release_operator.py |
| release.operator.sync_policy | domain | 0 | - | N | Y | N | Y | Y | Y | addons/smart_core/handlers/release_operator.py |
| release.operator.update_page_policy | domain | 0 | - | N | Y | N | Y | Y | Y | addons/smart_core/handlers/release_operator.py |
| release.operator.update_policy | domain | 0 | - | N | Y | N | Y | Y | Y | addons/smart_core/handlers/release_operator.py |
| risk.action.execute | domain | 1 | explicit_check | N | Y | N | Y | Y | Y | addons/smart_construction_core/handlers/risk_action_execute.py |
| scene.governance.export_contract | governance | 0 | - | N | Y | Y | N | N | N | addons/smart_core/handlers/scene_governance.py |
| scene.governance.pin_stable | governance | 0 | - | N | Y | Y | Y | N | N | addons/smart_core/handlers/scene_governance.py |
| scene.governance.rollback | governance | 0 | - | N | Y | Y | Y | N | N | addons/smart_core/handlers/scene_governance.py |
| scene.governance.set_channel | governance | 0 | - | N | Y | Y | Y | N | N | addons/smart_core/handlers/scene_governance.py |
| scene.health | domain | 0 | - | N | Y | Y | N | N | N | addons/smart_core/handlers/scene_health.py |
| scene.package.dry_run_import | governance | 0 | - | N | Y | Y | Y | N | N | addons/smart_core/handlers/scene_package.py |
| scene.package.export | governance | 0 | - | N | Y | Y | N | N | N | addons/smart_core/handlers/scene_package.py |
| scene.package.import | governance | 0 | - | N | Y | Y | Y | N | N | addons/smart_core/handlers/scene_package.py |
| scene.package.list | governance | 0 | - | N | Y | Y | N | N | N | addons/smart_core/handlers/scene_package.py |
| scene.packages.installed | domain | 1 | - | N | Y | N | N | N | N | addons/smart_core/handlers/scene_packages_installed.py |
| search.favorite.set | domain | 1 | explicit_check | N | Y | N | Y | Y | Y | addons/smart_core/handlers/search_favorite_set.py |
| session.bootstrap | domain | 0 | - | N | Y | N | N | Y | Y | addons/smart_core/handlers/session_bootstrap.py |
| settlement.block.fetch | domain | 1 | - | N | Y | N | Y | N | N | addons/smart_construction_core/handlers/settlement_slice_block_fetch.py |
| settlement.enter | domain | 1 | - | N | Y | N | Y | N | N | addons/smart_construction_core/handlers/settlement_slice_enter.py |
| system.init | core | 0 | - | Y | Y | Y | N | Y | Y | addons/smart_core/handlers/system_init.py |
| system.ping.construction | domain | 1 | record_rule | N | Y | N | Y | N | N | addons/smart_construction_core/handlers/system_ping_construction.py |
| telemetry.track | domain | 1 | explicit_check | N | Y | N | Y | N | N | addons/smart_construction_core/handlers/telemetry_track.py |
| terminal.shell.v2 | domain | 0 | - | N | Y | N | N | N | N | addons/smart_core/handlers/terminal_shell_v2.py |
| ui.contract | core | 0 | - | Y | Y | Y | N | Y | Y | addons/smart_core/handlers/ui_contract.py |
| ui.contract.v2 | domain | 0 | - | N | Y | Y | N | Y | Y | addons/smart_core/handlers/ui_contract_v2.py |
| usage.export.csv | domain | 1 | - | N | Y | N | N | Y | Y | addons/smart_core/handlers/usage_export_csv.py |
| usage.report | domain | 0 | - | N | Y | N | N | Y | Y | addons/smart_core/handlers/usage_report.py |
| usage.track | domain | 1 | explicit_check | N | Y | Y | Y | N | Y | addons/smart_core/handlers/usage_track.py |
| user.view.preference.get | domain | 0 | - | N | Y | N | N | Y | N | addons/smart_core/handlers/user_view_preference.py |
| user.view.preference.set | domain | 1 | explicit_check | N | Y | N | Y | Y | N | addons/smart_core/handlers/user_view_preference.py |
| workspace.home.enter | domain | 1 | - | N | Y | N | N | N | N | addons/smart_construction_core/handlers/workspace_home_enter.py |

## Missing Test Coverage

- `chatter.activity.update` (addons/smart_core/handlers/chatter_activity_update.py)
- `collaboration.users.search` (addons/smart_core/handlers/collaboration_users.py)
- `global.message.conversations` (addons/smart_core/handlers/global_messages.py)
- `global.message.inbox` (addons/smart_core/handlers/global_messages.py)
- `global.message.read` (addons/smart_core/handlers/global_messages.py)
- `global.message.send` (addons/smart_core/handlers/global_messages.py)

## Missing Smoke Make Targets

- `api.data.batch` (addons/smart_core/handlers/api_data_batch.py)
- `api.data.unlink` (addons/smart_core/handlers/api_data_unlink.py)
- `app.catalog` (addons/smart_core/handlers/app_shell.py)
- `app.catalog` (addons/smart_construction_core/handlers/app_catalog.py)
- `app.nav` (addons/smart_core/handlers/app_shell.py)
- `app.nav` (addons/smart_construction_core/handlers/app_nav.py)
- `business.evidence.trace` (addons/smart_construction_core/handlers/business_evidence_trace.py)
- `capability.describe` (addons/smart_construction_core/handlers/capability_describe.py)
- `capability.visibility.report` (addons/smart_construction_core/handlers/capability_visibility_report.py)
- `chatter.activity.schedule` (addons/smart_core/handlers/chatter_activity_schedule.py)
- `chatter.activity.update` (addons/smart_core/handlers/chatter_activity_update.py)
- `chatter.post` (addons/smart_core/handlers/chatter_post.py)
- `chatter.timeline` (addons/smart_core/handlers/chatter_timeline.py)
- `collaboration.users.search` (addons/smart_core/handlers/collaboration_users.py)
- `cost.tracking.block.fetch` (addons/smart_construction_core/handlers/cost_tracking_block_fetch.py)
- `cost.tracking.enter` (addons/smart_construction_core/handlers/cost_tracking_enter.py)
- `cost.tracking.record.create` (addons/smart_construction_core/handlers/cost_tracking_record_create.py)
- `dashboard.company.enter` (addons/smart_construction_core/handlers/dashboard_company_enter.py)
- `file.download` (addons/smart_core/handlers/file_download.py)
- `global.message.conversations` (addons/smart_core/handlers/global_messages.py)
- `global.message.inbox` (addons/smart_core/handlers/global_messages.py)
- `global.message.read` (addons/smart_core/handlers/global_messages.py)
- `global.message.send` (addons/smart_core/handlers/global_messages.py)
- `load_metadata` (addons/smart_core/handlers/load_metadata.py)
- `meta.describe_model` (addons/smart_core/handlers/meta_describe.py)
- `meta.intent_catalog` (addons/smart_core/handlers/meta_intent_catalog.py)
- `my.work.complete` (addons/smart_construction_core/handlers/my_work_complete.py)
- `my.work.complete_batch` (addons/smart_construction_core/handlers/my_work_complete.py)
- `my.work.summary` (addons/smart_construction_core/handlers/my_work_summary.py)
- `payment.block.fetch` (addons/smart_construction_core/handlers/payment_slice_block_fetch.py)
- `payment.enter` (addons/smart_construction_core/handlers/payment_slice_enter.py)
- `payment.record.create` (addons/smart_construction_core/handlers/payment_slice_record_create.py)
- `payment.request.available_actions` (addons/smart_construction_core/handlers/payment_request_available_actions.py)
- `payment.request.execute` (addons/smart_construction_core/handlers/payment_request_execute.py)
- `permission.check` (addons/smart_core/handlers/permission_check.py)
- `project.connection.transition` (addons/smart_construction_core/handlers/project_connection_transition.py)
- `project.context.search` (addons/smart_core/handlers/project_context.py)
- `project.dashboard.block.fetch` (addons/smart_construction_core/handlers/project_dashboard_block_fetch.py)
- `project.dashboard.enter` (addons/smart_construction_core/handlers/project_dashboard_enter.py)
- `project.dashboard.open` (addons/smart_construction_core/handlers/project_dashboard_open.py)
- `project.entry.context.options` (addons/smart_construction_core/handlers/project_entry_context_options.py)
- `project.entry.context.resolve` (addons/smart_construction_core/handlers/project_entry_context_resolve.py)
- `project.execution.advance` (addons/smart_construction_core/handlers/project_execution_advance.py)
- `project.execution.block.fetch` (addons/smart_construction_core/handlers/project_execution_block_fetch.py)
- `project.execution.enter` (addons/smart_construction_core/handlers/project_execution_enter.py)
- `project.initiation.enter` (addons/smart_construction_core/handlers/project_initiation_enter.py)
- `project.plan_bootstrap.block.fetch` (addons/smart_construction_core/handlers/project_plan_bootstrap_block_fetch.py)
- `project.plan_bootstrap.enter` (addons/smart_construction_core/handlers/project_plan_bootstrap_enter.py)
- `release.operator.approve` (addons/smart_core/handlers/release_operator.py)
- `release.operator.freeze` (addons/smart_core/handlers/release_operator.py)
- `release.operator.promote` (addons/smart_core/handlers/release_operator.py)
- `release.operator.rollback` (addons/smart_core/handlers/release_operator.py)
- `release.operator.runtime_probe` (addons/smart_core/handlers/release_operator.py)
- `release.operator.set_page_enabled` (addons/smart_core/handlers/release_operator.py)
- `release.operator.surface` (addons/smart_core/handlers/release_operator.py)
- `release.operator.sync_policy` (addons/smart_core/handlers/release_operator.py)
- `release.operator.update_page_policy` (addons/smart_core/handlers/release_operator.py)
- `release.operator.update_policy` (addons/smart_core/handlers/release_operator.py)
- `risk.action.execute` (addons/smart_construction_core/handlers/risk_action_execute.py)
- `scene.packages.installed` (addons/smart_core/handlers/scene_packages_installed.py)
- `search.favorite.set` (addons/smart_core/handlers/search_favorite_set.py)
- `session.bootstrap` (addons/smart_core/handlers/session_bootstrap.py)
- `settlement.block.fetch` (addons/smart_construction_core/handlers/settlement_slice_block_fetch.py)
- `settlement.enter` (addons/smart_construction_core/handlers/settlement_slice_enter.py)
- `system.ping.construction` (addons/smart_construction_core/handlers/system_ping_construction.py)
- `telemetry.track` (addons/smart_construction_core/handlers/telemetry_track.py)
- `terminal.shell.v2` (addons/smart_core/handlers/terminal_shell_v2.py)
- `usage.export.csv` (addons/smart_core/handlers/usage_export_csv.py)
- `usage.report` (addons/smart_core/handlers/usage_report.py)
- `user.view.preference.get` (addons/smart_core/handlers/user_view_preference.py)
- `user.view.preference.set` (addons/smart_core/handlers/user_view_preference.py)
- `workspace.home.enter` (addons/smart_construction_core/handlers/workspace_home_enter.py)

## Write Intents Without REQUIRED_GROUPS

- `payment.request.approve` (addons/smart_construction_core/handlers/payment_request_approval.py)
- `payment.request.done` (addons/smart_construction_core/handlers/payment_request_approval.py)
- `payment.request.reject` (addons/smart_construction_core/handlers/payment_request_approval.py)
- `release.operator.approve` (addons/smart_core/handlers/release_operator.py)
- `release.operator.freeze` (addons/smart_core/handlers/release_operator.py)
- `release.operator.promote` (addons/smart_core/handlers/release_operator.py)
- `release.operator.rollback` (addons/smart_core/handlers/release_operator.py)
- `release.operator.set_page_enabled` (addons/smart_core/handlers/release_operator.py)
- `release.operator.sync_policy` (addons/smart_core/handlers/release_operator.py)
- `release.operator.update_page_policy` (addons/smart_core/handlers/release_operator.py)
- `release.operator.update_policy` (addons/smart_core/handlers/release_operator.py)
- `scene.governance.pin_stable` (addons/smart_core/handlers/scene_governance.py)
- `scene.governance.rollback` (addons/smart_core/handlers/scene_governance.py)
- `scene.governance.set_channel` (addons/smart_core/handlers/scene_governance.py)
- `scene.package.dry_run_import` (addons/smart_core/handlers/scene_package.py)
- `scene.package.import` (addons/smart_core/handlers/scene_package.py)

## Write Intents Without ACL Guard Hints

- `cost.tracking.record.create` (addons/smart_construction_core/handlers/cost_tracking_record_create.py)
- `my.work.complete` (addons/smart_construction_core/handlers/my_work_complete.py)
- `my.work.complete_batch` (addons/smart_construction_core/handlers/my_work_complete.py)
- `payment.record.create` (addons/smart_construction_core/handlers/payment_slice_record_create.py)
- `payment.request.approve` (addons/smart_construction_core/handlers/payment_request_approval.py)
- `payment.request.done` (addons/smart_construction_core/handlers/payment_request_approval.py)
- `payment.request.execute` (addons/smart_construction_core/handlers/payment_request_execute.py)
- `payment.request.reject` (addons/smart_construction_core/handlers/payment_request_approval.py)
- `payment.request.submit` (addons/smart_construction_core/handlers/payment_request_approval.py)
- `release.operator.approve` (addons/smart_core/handlers/release_operator.py)
- `release.operator.freeze` (addons/smart_core/handlers/release_operator.py)
- `release.operator.promote` (addons/smart_core/handlers/release_operator.py)
- `release.operator.rollback` (addons/smart_core/handlers/release_operator.py)
- `release.operator.set_page_enabled` (addons/smart_core/handlers/release_operator.py)
- `release.operator.sync_policy` (addons/smart_core/handlers/release_operator.py)
- `release.operator.update_page_policy` (addons/smart_core/handlers/release_operator.py)
- `release.operator.update_policy` (addons/smart_core/handlers/release_operator.py)
- `risk.action.execute` (addons/smart_construction_core/handlers/risk_action_execute.py)
- `scene.governance.pin_stable` (addons/smart_core/handlers/scene_governance.py)
- `scene.governance.rollback` (addons/smart_core/handlers/scene_governance.py)
- `scene.governance.set_channel` (addons/smart_core/handlers/scene_governance.py)
- `scene.package.dry_run_import` (addons/smart_core/handlers/scene_package.py)
- `scene.package.import` (addons/smart_core/handlers/scene_package.py)
- `settlement.block.fetch` (addons/smart_construction_core/handlers/settlement_slice_block_fetch.py)
- `settlement.enter` (addons/smart_construction_core/handlers/settlement_slice_enter.py)
- `system.ping.construction` (addons/smart_construction_core/handlers/system_ping_construction.py)
- `telemetry.track` (addons/smart_construction_core/handlers/telemetry_track.py)
- `usage.track` (addons/smart_core/handlers/usage_track.py)
- `user.view.preference.set` (addons/smart_core/handlers/user_view_preference.py)

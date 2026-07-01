# Intent Layered Catalog

- intent_count: 101
- core_count: 10
- domain_count: 83
- governance_count: 8
- write_count: 40

| intent | layer | is_write | required_groups | source |
|---|---|---:|---:|---|
| api.data | core | N | 1 | addons/smart_core/handlers/api_data.py |
| api.data.batch | core | Y | 1 | addons/smart_core/handlers/api_data_batch.py |
| api.data.create | core | Y | 1 | addons/smart_core/handlers/api_data_write.py |
| api.data.unlink | core | Y | 1 | addons/smart_core/handlers/api_data_unlink.py |
| execute_button | core | Y | 1 | addons/smart_core/handlers/execute_button.py |
| file.download | core | N | 0 | addons/smart_core/handlers/file_download.py |
| file.upload | core | Y | 1 | addons/smart_core/handlers/file_upload.py |
| permission.check | core | N | 0 | addons/smart_core/handlers/permission_check.py |
| system.init | core | N | 0 | addons/smart_core/handlers/system_init.py |
| ui.contract | core | N | 0 | addons/smart_core/handlers/ui_contract.py |
| api.onchange | domain | N | 1 | addons/smart_core/handlers/api_onchange.py |
| app.catalog | domain | N | 0 | addons/smart_core/handlers/app_shell.py |
| app.catalog | domain | N | 0 | addons/smart_construction_core/handlers/app_catalog.py |
| app.nav | domain | N | 0 | addons/smart_core/handlers/app_shell.py |
| app.nav | domain | N | 0 | addons/smart_construction_core/handlers/app_nav.py |
| app.open | domain | N | 0 | addons/smart_core/handlers/app_shell.py |
| app.open | domain | N | 0 | addons/smart_construction_core/handlers/app_open.py |
| auth.logout | domain | N | 0 | addons/smart_core/handlers/login.py |
| business.evidence.trace | domain | N | 1 | addons/smart_construction_core/handlers/business_evidence_trace.py |
| capability.describe | domain | N | 0 | addons/smart_construction_core/handlers/capability_describe.py |
| capability.visibility.report | domain | N | 0 | addons/smart_construction_core/handlers/capability_visibility_report.py |
| chatter.activity.schedule | domain | Y | 1 | addons/smart_core/handlers/chatter_activity_schedule.py |
| chatter.activity.update | domain | Y | 1 | addons/smart_core/handlers/chatter_activity_update.py |
| chatter.post | domain | Y | 1 | addons/smart_core/handlers/chatter_post.py |
| chatter.timeline | domain | N | 0 | addons/smart_core/handlers/chatter_timeline.py |
| collaboration.users.search | domain | N | 0 | addons/smart_core/handlers/collaboration_users.py |
| cost.tracking.block.fetch | domain | N | 1 | addons/smart_construction_core/handlers/cost_tracking_block_fetch.py |
| cost.tracking.enter | domain | N | 1 | addons/smart_construction_core/handlers/cost_tracking_enter.py |
| cost.tracking.record.create | domain | Y | 1 | addons/smart_construction_core/handlers/cost_tracking_record_create.py |
| dashboard.company.enter | domain | N | 1 | addons/smart_construction_core/handlers/dashboard_company_enter.py |
| global.message.conversations | domain | N | 0 | addons/smart_core/handlers/global_messages.py |
| global.message.inbox | domain | N | 0 | addons/smart_core/handlers/global_messages.py |
| global.message.read | domain | Y | 1 | addons/smart_core/handlers/global_messages.py |
| global.message.send | domain | Y | 1 | addons/smart_core/handlers/global_messages.py |
| load_contract | domain | N | 0 | addons/smart_core/handlers/load_contract.py |
| load_metadata | domain | N | 0 | addons/smart_core/handlers/load_metadata.py |
| load_view | domain | N | 0 | addons/smart_core/handlers/load_view.py |
| login | domain | N | 0 | addons/smart_core/handlers/login.py |
| meta.describe_model | domain | N | 0 | addons/smart_core/handlers/meta_describe.py |
| meta.intent_catalog | domain | N | 0 | addons/smart_core/handlers/meta_intent_catalog.py |
| my.work.complete | domain | Y | 1 | addons/smart_construction_core/handlers/my_work_complete.py |
| my.work.complete_batch | domain | Y | 1 | addons/smart_construction_core/handlers/my_work_complete.py |
| my.work.summary | domain | N | 0 | addons/smart_construction_core/handlers/my_work_summary.py |
| payment.block.fetch | domain | N | 1 | addons/smart_construction_core/handlers/payment_slice_block_fetch.py |
| payment.enter | domain | N | 1 | addons/smart_construction_core/handlers/payment_slice_enter.py |
| payment.record.create | domain | Y | 1 | addons/smart_construction_core/handlers/payment_slice_record_create.py |
| payment.request.approve | domain | Y | 0 | addons/smart_construction_core/handlers/payment_request_approval.py |
| payment.request.available_actions | domain | N | 0 | addons/smart_construction_core/handlers/payment_request_available_actions.py |
| payment.request.done | domain | Y | 0 | addons/smart_construction_core/handlers/payment_request_approval.py |
| payment.request.execute | domain | Y | 1 | addons/smart_construction_core/handlers/payment_request_execute.py |
| payment.request.reject | domain | Y | 0 | addons/smart_construction_core/handlers/payment_request_approval.py |
| payment.request.submit | domain | Y | 1 | addons/smart_construction_core/handlers/payment_request_approval.py |
| project.connection.transition | domain | N | 1 | addons/smart_construction_core/handlers/project_connection_transition.py |
| project.context.search | domain | N | 0 | addons/smart_core/handlers/project_context.py |
| project.dashboard | domain | N | 0 | addons/smart_construction_core/handlers/project_dashboard.py |
| project.dashboard.block.fetch | domain | N | 1 | addons/smart_construction_core/handlers/project_dashboard_block_fetch.py |
| project.dashboard.enter | domain | N | 1 | addons/smart_construction_core/handlers/project_dashboard_enter.py |
| project.dashboard.open | domain | N | 1 | addons/smart_construction_core/handlers/project_dashboard_open.py |
| project.entry.context.options | domain | N | 1 | addons/smart_construction_core/handlers/project_entry_context_options.py |
| project.entry.context.resolve | domain | N | 1 | addons/smart_construction_core/handlers/project_entry_context_resolve.py |
| project.execution.advance | domain | N | 1 | addons/smart_construction_core/handlers/project_execution_advance.py |
| project.execution.block.fetch | domain | N | 1 | addons/smart_construction_core/handlers/project_execution_block_fetch.py |
| project.execution.enter | domain | N | 1 | addons/smart_construction_core/handlers/project_execution_enter.py |
| project.initiation.enter | domain | N | 1 | addons/smart_construction_core/handlers/project_initiation_enter.py |
| project.plan_bootstrap.block.fetch | domain | N | 1 | addons/smart_construction_core/handlers/project_plan_bootstrap_block_fetch.py |
| project.plan_bootstrap.enter | domain | N | 1 | addons/smart_construction_core/handlers/project_plan_bootstrap_enter.py |
| release.operator.approve | domain | Y | 0 | addons/smart_core/handlers/release_operator.py |
| release.operator.freeze | domain | Y | 0 | addons/smart_core/handlers/release_operator.py |
| release.operator.promote | domain | Y | 0 | addons/smart_core/handlers/release_operator.py |
| release.operator.rollback | domain | Y | 0 | addons/smart_core/handlers/release_operator.py |
| release.operator.runtime_probe | domain | N | 0 | addons/smart_core/handlers/release_operator.py |
| release.operator.set_page_enabled | domain | Y | 0 | addons/smart_core/handlers/release_operator.py |
| release.operator.surface | domain | N | 0 | addons/smart_core/handlers/release_operator.py |
| release.operator.sync_policy | domain | Y | 0 | addons/smart_core/handlers/release_operator.py |
| release.operator.update_page_policy | domain | Y | 0 | addons/smart_core/handlers/release_operator.py |
| release.operator.update_policy | domain | Y | 0 | addons/smart_core/handlers/release_operator.py |
| risk.action.execute | domain | Y | 1 | addons/smart_construction_core/handlers/risk_action_execute.py |
| scene.health | domain | N | 0 | addons/smart_core/handlers/scene_health.py |
| scene.packages.installed | domain | N | 1 | addons/smart_core/handlers/scene_packages_installed.py |
| search.favorite.set | domain | Y | 1 | addons/smart_core/handlers/search_favorite_set.py |
| session.bootstrap | domain | N | 0 | addons/smart_core/handlers/session_bootstrap.py |
| settlement.block.fetch | domain | Y | 1 | addons/smart_construction_core/handlers/settlement_slice_block_fetch.py |
| settlement.enter | domain | Y | 1 | addons/smart_construction_core/handlers/settlement_slice_enter.py |
| system.ping.construction | domain | Y | 1 | addons/smart_construction_core/handlers/system_ping_construction.py |
| telemetry.track | domain | Y | 1 | addons/smart_construction_core/handlers/telemetry_track.py |
| terminal.shell.v2 | domain | N | 0 | addons/smart_core/handlers/terminal_shell_v2.py |
| ui.contract.v2 | domain | N | 0 | addons/smart_core/handlers/ui_contract_v2.py |
| usage.export.csv | domain | N | 1 | addons/smart_core/handlers/usage_export_csv.py |
| usage.report | domain | N | 0 | addons/smart_core/handlers/usage_report.py |
| usage.track | domain | Y | 1 | addons/smart_core/handlers/usage_track.py |
| user.view.preference.get | domain | N | 0 | addons/smart_core/handlers/user_view_preference.py |
| user.view.preference.set | domain | Y | 1 | addons/smart_core/handlers/user_view_preference.py |
| workspace.home.enter | domain | N | 1 | addons/smart_construction_core/handlers/workspace_home_enter.py |
| scene.governance.export_contract | governance | N | 0 | addons/smart_core/handlers/scene_governance.py |
| scene.governance.pin_stable | governance | Y | 0 | addons/smart_core/handlers/scene_governance.py |
| scene.governance.rollback | governance | Y | 0 | addons/smart_core/handlers/scene_governance.py |
| scene.governance.set_channel | governance | Y | 0 | addons/smart_core/handlers/scene_governance.py |
| scene.package.dry_run_import | governance | Y | 0 | addons/smart_core/handlers/scene_package.py |
| scene.package.export | governance | N | 0 | addons/smart_core/handlers/scene_package.py |
| scene.package.import | governance | Y | 0 | addons/smart_core/handlers/scene_package.py |
| scene.package.list | governance | N | 0 | addons/smart_core/handlers/scene_package.py |

## Core Layer

- `api.data`
- `api.data.batch`
- `api.data.create`
- `api.data.unlink`
- `execute_button`
- `file.download`
- `file.upload`
- `permission.check`
- `system.init`
- `ui.contract`

## Domain Layer

- `api.onchange`
- `app.catalog`
- `app.catalog`
- `app.nav`
- `app.nav`
- `app.open`
- `app.open`
- `auth.logout`
- `business.evidence.trace`
- `capability.describe`
- `capability.visibility.report`
- `chatter.activity.schedule`
- `chatter.activity.update`
- `chatter.post`
- `chatter.timeline`
- `collaboration.users.search`
- `cost.tracking.block.fetch`
- `cost.tracking.enter`
- `cost.tracking.record.create`
- `dashboard.company.enter`
- `global.message.conversations`
- `global.message.inbox`
- `global.message.read`
- `global.message.send`
- `load_contract`
- `load_metadata`
- `load_view`
- `login`
- `meta.describe_model`
- `meta.intent_catalog`
- `my.work.complete`
- `my.work.complete_batch`
- `my.work.summary`
- `payment.block.fetch`
- `payment.enter`
- `payment.record.create`
- `payment.request.approve`
- `payment.request.available_actions`
- `payment.request.done`
- `payment.request.execute`
- `payment.request.reject`
- `payment.request.submit`
- `project.connection.transition`
- `project.context.search`
- `project.dashboard`
- `project.dashboard.block.fetch`
- `project.dashboard.enter`
- `project.dashboard.open`
- `project.entry.context.options`
- `project.entry.context.resolve`
- `project.execution.advance`
- `project.execution.block.fetch`
- `project.execution.enter`
- `project.initiation.enter`
- `project.plan_bootstrap.block.fetch`
- `project.plan_bootstrap.enter`
- `release.operator.approve`
- `release.operator.freeze`
- `release.operator.promote`
- `release.operator.rollback`
- `release.operator.runtime_probe`
- `release.operator.set_page_enabled`
- `release.operator.surface`
- `release.operator.sync_policy`
- `release.operator.update_page_policy`
- `release.operator.update_policy`
- `risk.action.execute`
- `scene.health`
- `scene.packages.installed`
- `search.favorite.set`
- `session.bootstrap`
- `settlement.block.fetch`
- `settlement.enter`
- `system.ping.construction`
- `telemetry.track`
- `terminal.shell.v2`
- `ui.contract.v2`
- `usage.export.csv`
- `usage.report`
- `usage.track`
- `user.view.preference.get`
- `user.view.preference.set`
- `workspace.home.enter`

## Governance Layer

- `scene.governance.export_contract`
- `scene.governance.pin_stable`
- `scene.governance.rollback`
- `scene.governance.set_channel`
- `scene.package.dry_run_import`
- `scene.package.export`
- `scene.package.import`
- `scene.package.list`

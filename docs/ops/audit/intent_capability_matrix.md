# Intent Capability Matrix Audit

- intent_count: 50
- missing_test_count: 0
- missing_smoke_target_count: 33
- write_without_required_groups_count: 20
- write_without_acl_hint_count: 14

## Matrix

| intent_type | required_groups | etag_enabled | has_test | has_smoke_target | is_write | orm_used | may_sudo | source |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| api.data | 0 | N | Y | N | N | Y | Y | addons/smart_core/handlers/api_data.py |
| api.data.batch | 0 | N | Y | N | Y | Y | Y | addons/smart_core/handlers/api_data_batch.py |
| api.data.create | 0 | N | Y | N | Y | Y | Y | addons/smart_core/handlers/api_data_write.py |
| api.data.unlink | 0 | N | Y | N | Y | Y | Y | addons/smart_core/handlers/api_data_unlink.py |
| app.catalog | 0 | Y | Y | N | N | Y | N | addons/smart_core/handlers/app_catalog.py |
| app.nav | 0 | Y | Y | N | N | N | N | addons/smart_core/handlers/app_nav.py |
| app.open | 0 | N | Y | N | N | N | N | addons/smart_core/handlers/app_open.py |
| auth.logout | 0 | N | Y | N | N | Y | Y | addons/smart_core/handlers/login.py |
| capability.describe | 0 | N | Y | N | N | Y | Y | addons/smart_construction_core/handlers/capability_describe.py |
| capability.visibility.report | 0 | N | Y | N | N | Y | Y | addons/smart_construction_core/handlers/capability_visibility_report.py |
| chatter.post | 0 | N | Y | N | Y | Y | N | addons/smart_core/handlers/chatter_post.py |
| chatter.timeline | 0 | N | Y | N | N | Y | Y | addons/smart_core/handlers/chatter_timeline.py |
| execute_button | 0 | N | Y | Y | Y | Y | Y | addons/smart_core/handlers/execute_button.py |
| file.download | 0 | N | Y | N | N | Y | Y | addons/smart_core/handlers/file_download.py |
| file.upload | 0 | N | Y | Y | Y | Y | N | addons/smart_core/handlers/file_upload.py |
| load_contract | 0 | N | Y | N | N | Y | Y | addons/smart_core/handlers/load_contract.py |
| load_metadata | 0 | N | Y | N | N | N | N | addons/smart_core/handlers/load_metadata.py |
| load_view | 0 | N | Y | Y | N | Y | N | addons/smart_core/handlers/load_view.py |
| login | 0 | N | Y | N | N | Y | Y | addons/smart_core/handlers/login.py |
| meta.describe_model | 0 | N | Y | N | N | N | N | addons/smart_core/handlers/meta_describe.py |
| my.work.complete | 0 | N | Y | N | Y | Y | Y | addons/smart_construction_core/handlers/my_work_complete.py |
| my.work.complete_batch | 0 | N | Y | N | Y | Y | Y | addons/smart_construction_core/handlers/my_work_complete.py |
| my.work.summary | 0 | N | Y | N | N | Y | N | addons/smart_construction_core/handlers/my_work_summary.py |
| payment.request.approve | 0 | N | Y | Y | Y | Y | Y | addons/smart_construction_core/handlers/payment_request_approval.py |
| payment.request.available_actions | 0 | N | Y | N | N | Y | Y | addons/smart_construction_core/handlers/payment_request_available_actions.py |
| payment.request.done | 0 | N | Y | Y | Y | Y | Y | addons/smart_construction_core/handlers/payment_request_approval.py |
| payment.request.execute | 0 | N | Y | N | Y | N | N | addons/smart_construction_core/handlers/payment_request_execute.py |
| payment.request.reject | 0 | N | Y | Y | Y | Y | Y | addons/smart_construction_core/handlers/payment_request_approval.py |
| payment.request.submit | 0 | N | Y | Y | Y | Y | Y | addons/smart_construction_core/handlers/payment_request_approval.py |
| permission.check | 0 | N | Y | N | N | Y | Y | addons/smart_core/handlers/permission_check.py |
| sample.enhanced | 0 | N | Y | N | N | N | N | addons/smart_core/handlers/enhanced_sample_handler.py |
| scene.governance.export_contract | 0 | N | Y | Y | N | N | N | addons/smart_core/handlers/scene_governance.py |
| scene.governance.pin_stable | 0 | N | Y | Y | Y | N | N | addons/smart_core/handlers/scene_governance.py |
| scene.governance.rollback | 0 | N | Y | Y | Y | N | N | addons/smart_core/handlers/scene_governance.py |
| scene.governance.set_channel | 0 | N | Y | Y | Y | N | N | addons/smart_core/handlers/scene_governance.py |
| scene.health | 0 | N | Y | Y | N | N | N | addons/smart_core/handlers/scene_health.py |
| scene.package.dry_run_import | 0 | N | Y | Y | Y | N | N | addons/smart_core/handlers/scene_package.py |
| scene.package.export | 0 | N | Y | Y | N | N | N | addons/smart_core/handlers/scene_package.py |
| scene.package.import | 0 | N | Y | Y | Y | N | N | addons/smart_core/handlers/scene_package.py |
| scene.package.list | 0 | N | Y | Y | N | N | N | addons/smart_core/handlers/scene_package.py |
| scene.packages.installed | 1 | N | Y | N | N | N | N | addons/smart_core/handlers/scene_packages_installed.py |
| session.bootstrap | 0 | N | Y | N | N | Y | Y | addons/smart_core/handlers/session_bootstrap.py |
| system.init | 0 | Y | Y | Y | N | Y | N | addons/smart_core/handlers/system_init.py |
| system.ping.construction | 0 | N | Y | N | Y | N | N | addons/smart_construction_core/handlers/system_ping_construction.py |
| ui.contract | 0 | Y | Y | N | N | Y | N | addons/smart_core/handlers/ui_contract.py |
| ui.contract.enhanced | 0 | N | Y | N | N | N | N | addons/smart_core/handlers/enhanced_ui_contract.py |
| ui.contract.model.view | 0 | N | Y | N | N | N | N | addons/smart_core/handlers/enhanced_ui_contract.py |
| usage.export.csv | 1 | N | Y | N | N | Y | Y | addons/smart_construction_core/handlers/usage_export_csv.py |
| usage.report | 0 | N | Y | N | N | Y | Y | addons/smart_construction_core/handlers/usage_report.py |
| usage.track | 0 | N | Y | N | Y | N | Y | addons/smart_construction_core/handlers/usage_track.py |

## Missing Test Coverage

- none

## Missing Smoke Make Targets

- `api.data` (addons/smart_core/handlers/api_data.py)
- `api.data.batch` (addons/smart_core/handlers/api_data_batch.py)
- `api.data.create` (addons/smart_core/handlers/api_data_write.py)
- `api.data.unlink` (addons/smart_core/handlers/api_data_unlink.py)
- `app.catalog` (addons/smart_core/handlers/app_catalog.py)
- `app.nav` (addons/smart_core/handlers/app_nav.py)
- `app.open` (addons/smart_core/handlers/app_open.py)
- `auth.logout` (addons/smart_core/handlers/login.py)
- `capability.describe` (addons/smart_construction_core/handlers/capability_describe.py)
- `capability.visibility.report` (addons/smart_construction_core/handlers/capability_visibility_report.py)
- `chatter.post` (addons/smart_core/handlers/chatter_post.py)
- `chatter.timeline` (addons/smart_core/handlers/chatter_timeline.py)
- `file.download` (addons/smart_core/handlers/file_download.py)
- `load_contract` (addons/smart_core/handlers/load_contract.py)
- `load_metadata` (addons/smart_core/handlers/load_metadata.py)
- `login` (addons/smart_core/handlers/login.py)
- `meta.describe_model` (addons/smart_core/handlers/meta_describe.py)
- `my.work.complete` (addons/smart_construction_core/handlers/my_work_complete.py)
- `my.work.complete_batch` (addons/smart_construction_core/handlers/my_work_complete.py)
- `my.work.summary` (addons/smart_construction_core/handlers/my_work_summary.py)
- `payment.request.available_actions` (addons/smart_construction_core/handlers/payment_request_available_actions.py)
- `payment.request.execute` (addons/smart_construction_core/handlers/payment_request_execute.py)
- `permission.check` (addons/smart_core/handlers/permission_check.py)
- `sample.enhanced` (addons/smart_core/handlers/enhanced_sample_handler.py)
- `scene.packages.installed` (addons/smart_core/handlers/scene_packages_installed.py)
- `session.bootstrap` (addons/smart_core/handlers/session_bootstrap.py)
- `system.ping.construction` (addons/smart_construction_core/handlers/system_ping_construction.py)
- `ui.contract` (addons/smart_core/handlers/ui_contract.py)
- `ui.contract.enhanced` (addons/smart_core/handlers/enhanced_ui_contract.py)
- `ui.contract.model.view` (addons/smart_core/handlers/enhanced_ui_contract.py)
- `usage.export.csv` (addons/smart_construction_core/handlers/usage_export_csv.py)
- `usage.report` (addons/smart_construction_core/handlers/usage_report.py)
- `usage.track` (addons/smart_construction_core/handlers/usage_track.py)

## Write Intents Without REQUIRED_GROUPS

- `api.data.batch` (addons/smart_core/handlers/api_data_batch.py)
- `api.data.create` (addons/smart_core/handlers/api_data_write.py)
- `api.data.unlink` (addons/smart_core/handlers/api_data_unlink.py)
- `chatter.post` (addons/smart_core/handlers/chatter_post.py)
- `execute_button` (addons/smart_core/handlers/execute_button.py)
- `file.upload` (addons/smart_core/handlers/file_upload.py)
- `my.work.complete` (addons/smart_construction_core/handlers/my_work_complete.py)
- `my.work.complete_batch` (addons/smart_construction_core/handlers/my_work_complete.py)
- `payment.request.approve` (addons/smart_construction_core/handlers/payment_request_approval.py)
- `payment.request.done` (addons/smart_construction_core/handlers/payment_request_approval.py)
- `payment.request.execute` (addons/smart_construction_core/handlers/payment_request_execute.py)
- `payment.request.reject` (addons/smart_construction_core/handlers/payment_request_approval.py)
- `payment.request.submit` (addons/smart_construction_core/handlers/payment_request_approval.py)
- `scene.governance.pin_stable` (addons/smart_core/handlers/scene_governance.py)
- `scene.governance.rollback` (addons/smart_core/handlers/scene_governance.py)
- `scene.governance.set_channel` (addons/smart_core/handlers/scene_governance.py)
- `scene.package.dry_run_import` (addons/smart_core/handlers/scene_package.py)
- `scene.package.import` (addons/smart_core/handlers/scene_package.py)
- `system.ping.construction` (addons/smart_construction_core/handlers/system_ping_construction.py)
- `usage.track` (addons/smart_construction_core/handlers/usage_track.py)

## Write Intents Without ACL Guard Hints

- `my.work.complete` (addons/smart_construction_core/handlers/my_work_complete.py)
- `my.work.complete_batch` (addons/smart_construction_core/handlers/my_work_complete.py)
- `payment.request.approve` (addons/smart_construction_core/handlers/payment_request_approval.py)
- `payment.request.done` (addons/smart_construction_core/handlers/payment_request_approval.py)
- `payment.request.execute` (addons/smart_construction_core/handlers/payment_request_execute.py)
- `payment.request.reject` (addons/smart_construction_core/handlers/payment_request_approval.py)
- `payment.request.submit` (addons/smart_construction_core/handlers/payment_request_approval.py)
- `scene.governance.pin_stable` (addons/smart_core/handlers/scene_governance.py)
- `scene.governance.rollback` (addons/smart_core/handlers/scene_governance.py)
- `scene.governance.set_channel` (addons/smart_core/handlers/scene_governance.py)
- `scene.package.dry_run_import` (addons/smart_core/handlers/scene_package.py)
- `scene.package.import` (addons/smart_core/handlers/scene_package.py)
- `system.ping.construction` (addons/smart_construction_core/handlers/system_ping_construction.py)
- `usage.track` (addons/smart_construction_core/handlers/usage_track.py)

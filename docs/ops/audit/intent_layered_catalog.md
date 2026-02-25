# Intent Layered Catalog

- intent_count: 50
- core_count: 10
- domain_count: 32
- governance_count: 8
- write_count: 20

| intent | layer | is_write | required_groups | source |
|---|---|---:|---:|---|
| api.data | core | N | 0 | addons/smart_core/handlers/api_data.py |
| api.data.batch | core | Y | 1 | addons/smart_core/handlers/api_data_batch.py |
| api.data.create | core | Y | 1 | addons/smart_core/handlers/api_data_write.py |
| api.data.unlink | core | Y | 1 | addons/smart_core/handlers/api_data_unlink.py |
| execute_button | core | Y | 1 | addons/smart_core/handlers/execute_button.py |
| file.download | core | N | 0 | addons/smart_core/handlers/file_download.py |
| file.upload | core | Y | 1 | addons/smart_core/handlers/file_upload.py |
| permission.check | core | N | 0 | addons/smart_core/handlers/permission_check.py |
| system.init | core | N | 0 | addons/smart_core/handlers/system_init.py |
| ui.contract | core | N | 0 | addons/smart_core/handlers/ui_contract.py |
| app.catalog | domain | N | 0 | addons/smart_core/handlers/app_catalog.py |
| app.nav | domain | N | 0 | addons/smart_core/handlers/app_nav.py |
| app.open | domain | N | 0 | addons/smart_core/handlers/app_open.py |
| auth.logout | domain | N | 0 | addons/smart_core/handlers/login.py |
| capability.describe | domain | N | 0 | addons/smart_construction_core/handlers/capability_describe.py |
| capability.visibility.report | domain | N | 0 | addons/smart_construction_core/handlers/capability_visibility_report.py |
| chatter.post | domain | Y | 1 | addons/smart_core/handlers/chatter_post.py |
| chatter.timeline | domain | N | 0 | addons/smart_core/handlers/chatter_timeline.py |
| load_contract | domain | N | 0 | addons/smart_core/handlers/load_contract.py |
| load_metadata | domain | N | 0 | addons/smart_core/handlers/load_metadata.py |
| load_view | domain | N | 0 | addons/smart_core/handlers/load_view.py |
| login | domain | N | 0 | addons/smart_core/handlers/login.py |
| meta.describe_model | domain | N | 0 | addons/smart_core/handlers/meta_describe.py |
| my.work.complete | domain | Y | 1 | addons/smart_construction_core/handlers/my_work_complete.py |
| my.work.complete_batch | domain | Y | 1 | addons/smart_construction_core/handlers/my_work_complete.py |
| my.work.summary | domain | N | 0 | addons/smart_construction_core/handlers/my_work_summary.py |
| payment.request.approve | domain | Y | 0 | addons/smart_construction_core/handlers/payment_request_approval.py |
| payment.request.available_actions | domain | N | 0 | addons/smart_construction_core/handlers/payment_request_available_actions.py |
| payment.request.done | domain | Y | 0 | addons/smart_construction_core/handlers/payment_request_approval.py |
| payment.request.execute | domain | Y | 1 | addons/smart_construction_core/handlers/payment_request_execute.py |
| payment.request.reject | domain | Y | 0 | addons/smart_construction_core/handlers/payment_request_approval.py |
| payment.request.submit | domain | Y | 0 | addons/smart_construction_core/handlers/payment_request_approval.py |
| sample.enhanced | domain | N | 0 | addons/smart_core/handlers/enhanced_sample_handler.py |
| scene.health | domain | N | 0 | addons/smart_core/handlers/scene_health.py |
| scene.packages.installed | domain | N | 1 | addons/smart_core/handlers/scene_packages_installed.py |
| session.bootstrap | domain | N | 0 | addons/smart_core/handlers/session_bootstrap.py |
| system.ping.construction | domain | Y | 1 | addons/smart_construction_core/handlers/system_ping_construction.py |
| ui.contract.enhanced | domain | N | 0 | addons/smart_core/handlers/enhanced_ui_contract.py |
| ui.contract.model.view | domain | N | 0 | addons/smart_core/handlers/enhanced_ui_contract.py |
| usage.export.csv | domain | N | 1 | addons/smart_construction_core/handlers/usage_export_csv.py |
| usage.report | domain | N | 0 | addons/smart_construction_core/handlers/usage_report.py |
| usage.track | domain | Y | 1 | addons/smart_construction_core/handlers/usage_track.py |
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

- `app.catalog`
- `app.nav`
- `app.open`
- `auth.logout`
- `capability.describe`
- `capability.visibility.report`
- `chatter.post`
- `chatter.timeline`
- `load_contract`
- `load_metadata`
- `load_view`
- `login`
- `meta.describe_model`
- `my.work.complete`
- `my.work.complete_batch`
- `my.work.summary`
- `payment.request.approve`
- `payment.request.available_actions`
- `payment.request.done`
- `payment.request.execute`
- `payment.request.reject`
- `payment.request.submit`
- `sample.enhanced`
- `scene.health`
- `scene.packages.installed`
- `session.bootstrap`
- `system.ping.construction`
- `ui.contract.enhanced`
- `ui.contract.model.view`
- `usage.export.csv`
- `usage.report`
- `usage.track`

## Governance Layer

- `scene.governance.export_contract`
- `scene.governance.pin_stable`
- `scene.governance.rollback`
- `scene.governance.set_channel`
- `scene.package.dry_run_import`
- `scene.package.export`
- `scene.package.import`
- `scene.package.list`

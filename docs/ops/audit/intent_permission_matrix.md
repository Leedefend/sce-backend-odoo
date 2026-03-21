# Intent Permission Matrix

- intent_count: 51
- write_intent_count: 21

| intent | is_write | required_groups | ACL_MODE | smoke | test | source |
|---|---:|---|---|---:|---:|---|
| api.data | N | - | - | N | Y | addons/smart_core/handlers/api_data.py |
| api.data.batch | Y | smart_core.group_smart_core_data_operator | explicit_check | N | Y | addons/smart_core/handlers/api_data_batch.py |
| api.data.create | Y | smart_core.group_smart_core_data_operator | explicit_check | N | Y | addons/smart_core/handlers/api_data_write.py |
| api.data.unlink | Y | smart_core.group_smart_core_data_operator | explicit_check | N | Y | addons/smart_core/handlers/api_data_unlink.py |
| app.catalog | N | - | - | N | Y | addons/smart_core/handlers/app_catalog.py |
| app.nav | N | - | - | N | Y | addons/smart_core/handlers/app_nav.py |
| app.open | N | - | - | N | Y | addons/smart_core/handlers/app_open.py |
| auth.logout | N | - | - | N | N | addons/smart_core/handlers/login.py |
| capability.describe | N | - | - | N | Y | addons/smart_construction_core/handlers/capability_describe.py |
| capability.visibility.report | N | - | - | N | N | addons/smart_construction_core/handlers/capability_visibility_report.py |
| chatter.post | Y | smart_core.group_smart_core_data_operator | explicit_check | N | Y | addons/smart_core/handlers/chatter_post.py |
| chatter.timeline | N | - | - | N | Y | addons/smart_core/handlers/chatter_timeline.py |
| execute_button | Y | smart_core.group_smart_core_data_operator | explicit_check | Y | Y | addons/smart_core/handlers/execute_button.py |
| file.download | N | - | - | N | Y | addons/smart_core/handlers/file_download.py |
| file.upload | Y | smart_core.group_smart_core_data_operator | explicit_check | Y | Y | addons/smart_core/handlers/file_upload.py |
| load_contract | N | - | - | N | Y | addons/smart_core/handlers/load_contract.py |
| load_metadata | N | - | - | N | Y | addons/smart_core/handlers/load_metadata.py |
| load_view | N | - | - | Y | Y | addons/smart_core/handlers/load_view.py |
| login | N | - | - | Y | Y | addons/smart_core/handlers/login.py |
| meta.describe_model | N | - | - | N | Y | addons/smart_core/handlers/meta_describe.py |
| my.work.complete | Y | smart_core.group_smart_core_data_operator | explicit_check | N | Y | addons/smart_construction_core/handlers/my_work_complete.py |
| my.work.complete_batch | Y | smart_core.group_smart_core_data_operator | explicit_check | N | Y | addons/smart_construction_core/handlers/my_work_complete.py |
| my.work.summary | N | - | - | N | Y | addons/smart_construction_core/handlers/my_work_summary.py |
| payment.request.approve | Y | smart_core.group_smart_core_finance_approver | explicit_check | N | Y | addons/smart_construction_core/handlers/payment_request_approval.py |
| payment.request.available_actions | N | - | - | N | Y | addons/smart_construction_core/handlers/payment_request_available_actions.py |
| payment.request.done | Y | smart_construction_core.group_sc_cap_finance_manager, smart_core.group_smart_core_finance_approver | explicit_check | N | Y | addons/smart_construction_core/handlers/payment_request_approval.py |
| payment.request.execute | Y | smart_construction_core.group_sc_cap_finance_user, smart_core.group_smart_core_finance_approver, smart_construction_core.group_sc_cap_finance_manager | explicit_check | N | Y | addons/smart_construction_core/handlers/payment_request_execute.py |
| payment.request.reject | Y | smart_core.group_smart_core_finance_approver | explicit_check | N | Y | addons/smart_construction_core/handlers/payment_request_approval.py |
| payment.request.submit | Y | smart_construction_core.group_sc_cap_finance_user, smart_core.group_smart_core_finance_approver | explicit_check | N | Y | addons/smart_construction_core/handlers/payment_request_approval.py |
| permission.check | N | - | - | N | Y | addons/smart_core/handlers/permission_check.py |
| sample.enhanced | N | - | - | N | Y | addons/smart_core/handlers/enhanced_sample_handler.py |
| scene.governance.export_contract | N | smart_core.group_smart_core_scene_admin | explicit_check | N | N | addons/smart_core/handlers/scene_governance.py |
| scene.governance.pin_stable | Y | smart_core.group_smart_core_scene_admin | explicit_check | N | Y | addons/smart_core/handlers/scene_governance.py |
| scene.governance.rollback | Y | smart_core.group_smart_core_scene_admin | explicit_check | N | Y | addons/smart_core/handlers/scene_governance.py |
| scene.governance.set_channel | Y | smart_core.group_smart_core_scene_admin | explicit_check | N | Y | addons/smart_core/handlers/scene_governance.py |
| scene.health | N | - | - | Y | Y | addons/smart_core/handlers/scene_health.py |
| scene.package.dry_run_import | Y | smart_construction_core.group_sc_cap_config_admin | explicit_check | N | Y | addons/smart_core/handlers/scene_package.py |
| scene.package.export | N | smart_construction_core.group_sc_cap_config_admin | explicit_check | Y | Y | addons/smart_core/handlers/scene_package.py |
| scene.package.import | Y | smart_construction_core.group_sc_cap_config_admin | explicit_check | Y | Y | addons/smart_core/handlers/scene_package.py |
| scene.package.list | N | smart_construction_core.group_sc_cap_config_admin | explicit_check | N | N | addons/smart_core/handlers/scene_package.py |
| scene.packages.installed | N | smart_construction_core.group_sc_cap_config_admin | - | N | Y | addons/smart_core/handlers/scene_packages_installed.py |
| session.bootstrap | N | - | - | N | Y | addons/smart_core/handlers/session_bootstrap.py |
| system.init | N | - | - | Y | Y | addons/smart_core/handlers/system_init.py |
| system.ping.construction | Y | smart_core.group_smart_core_data_operator | record_rule | N | Y | addons/smart_construction_core/handlers/system_ping_construction.py |
| telemetry.track | Y | base.group_user | explicit_check | N | Y | addons/smart_construction_core/handlers/telemetry_track.py |
| ui.contract | N | - | - | N | Y | addons/smart_core/handlers/ui_contract.py |
| ui.contract.enhanced | N | - | - | N | Y | addons/smart_core/handlers/enhanced_ui_contract.py |
| ui.contract.model.view | N | - | - | N | Y | addons/smart_core/handlers/enhanced_ui_contract.py |
| usage.export.csv | N | base.group_user | - | N | Y | addons/smart_construction_core/handlers/usage_export_csv.py |
| usage.report | N | - | - | N | Y | addons/smart_construction_core/handlers/usage_report.py |
| usage.track | Y | base.group_user | explicit_check | N | Y | addons/smart_construction_core/handlers/usage_track.py |

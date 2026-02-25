# Intent Orphan Report

- known_intent_count: 50
- scene_count: 24
- used_intent_count: 1
- orphan_intent_count: 49
- internal_only_suggest_count: 9
- merge_or_delete_suggest_count: 23

| intent | layer | action |
|---|---|---|
| api.data | core | keep |
| api.data.batch | core | keep |
| api.data.create | core | keep |
| api.data.unlink | core | keep |
| app.catalog | domain | internal_only |
| app.nav | domain | internal_only |
| app.open | domain | internal_only |
| auth.logout | domain | merge_or_delete |
| capability.describe | domain | merge_or_delete |
| capability.visibility.report | domain | merge_or_delete |
| chatter.post | domain | merge_or_delete |
| chatter.timeline | domain | merge_or_delete |
| execute_button | core | keep |
| file.download | core | keep |
| file.upload | core | keep |
| load_contract | domain | merge_or_delete |
| load_metadata | domain | merge_or_delete |
| load_view | domain | merge_or_delete |
| login | domain | internal_only |
| meta.describe_model | domain | internal_only |
| my.work.complete | domain | merge_or_delete |
| my.work.complete_batch | domain | merge_or_delete |
| my.work.summary | domain | merge_or_delete |
| payment.request.approve | domain | merge_or_delete |
| payment.request.available_actions | domain | merge_or_delete |
| payment.request.done | domain | merge_or_delete |
| payment.request.execute | domain | merge_or_delete |
| payment.request.reject | domain | merge_or_delete |
| payment.request.submit | domain | merge_or_delete |
| permission.check | core | keep |
| sample.enhanced | domain | merge_or_delete |
| scene.governance.export_contract | governance | keep |
| scene.governance.pin_stable | governance | keep |
| scene.governance.rollback | governance | keep |
| scene.governance.set_channel | governance | keep |
| scene.health | domain | internal_only |
| scene.package.dry_run_import | governance | keep |
| scene.package.export | governance | keep |
| scene.package.import | governance | keep |
| scene.package.list | governance | keep |
| scene.packages.installed | domain | merge_or_delete |
| session.bootstrap | domain | merge_or_delete |
| system.init | core | keep |
| system.ping.construction | domain | merge_or_delete |
| ui.contract.enhanced | domain | merge_or_delete |
| ui.contract.model.view | domain | merge_or_delete |
| usage.export.csv | domain | internal_only |
| usage.report | domain | internal_only |
| usage.track | domain | internal_only |

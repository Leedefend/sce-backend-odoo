# Intent Orphan Report

- known_intent_count: 98
- scene_count: 2
- used_intent_count: 1
- orphan_intent_count: 97
- internal_only_suggest_count: 10
- merge_or_delete_suggest_count: 70

| intent | layer | action |
|---|---|---|
| api.data | core | keep |
| api.data.batch | core | keep |
| api.data.create | core | keep |
| api.data.unlink | core | keep |
| api.onchange | domain | merge_or_delete |
| app.catalog | domain | internal_only |
| app.nav | domain | internal_only |
| app.open | domain | internal_only |
| auth.logout | domain | merge_or_delete |
| business.evidence.trace | domain | merge_or_delete |
| capability.describe | domain | merge_or_delete |
| capability.visibility.report | domain | merge_or_delete |
| chatter.activity.schedule | domain | merge_or_delete |
| chatter.activity.update | domain | merge_or_delete |
| chatter.post | domain | merge_or_delete |
| chatter.timeline | domain | merge_or_delete |
| collaboration.users.search | domain | merge_or_delete |
| cost.tracking.block.fetch | domain | merge_or_delete |
| cost.tracking.enter | domain | merge_or_delete |
| cost.tracking.record.create | domain | merge_or_delete |
| dashboard.company.enter | domain | merge_or_delete |
| execute_button | core | keep |
| file.download | core | keep |
| file.upload | core | keep |
| global.message.conversations | domain | merge_or_delete |
| global.message.inbox | domain | merge_or_delete |
| global.message.read | domain | merge_or_delete |
| global.message.send | domain | merge_or_delete |
| load_contract | domain | merge_or_delete |
| load_metadata | domain | merge_or_delete |
| load_view | domain | merge_or_delete |
| login | domain | internal_only |
| meta.describe_model | domain | internal_only |
| meta.intent_catalog | domain | internal_only |
| my.work.complete | domain | merge_or_delete |
| my.work.complete_batch | domain | merge_or_delete |
| my.work.summary | domain | merge_or_delete |
| payment.block.fetch | domain | merge_or_delete |
| payment.enter | domain | merge_or_delete |
| payment.record.create | domain | merge_or_delete |
| payment.request.approve | domain | merge_or_delete |
| payment.request.available_actions | domain | merge_or_delete |
| payment.request.done | domain | merge_or_delete |
| payment.request.execute | domain | merge_or_delete |
| payment.request.reject | domain | merge_or_delete |
| payment.request.submit | domain | merge_or_delete |
| permission.check | core | keep |
| project.connection.transition | domain | merge_or_delete |
| project.context.search | domain | merge_or_delete |
| project.dashboard | domain | merge_or_delete |
| project.dashboard.block.fetch | domain | merge_or_delete |
| project.dashboard.enter | domain | merge_or_delete |
| project.dashboard.open | domain | merge_or_delete |
| project.entry.context.options | domain | merge_or_delete |
| project.entry.context.resolve | domain | merge_or_delete |
| project.execution.advance | domain | merge_or_delete |
| project.execution.block.fetch | domain | merge_or_delete |
| project.execution.enter | domain | merge_or_delete |
| project.initiation.enter | domain | merge_or_delete |
| project.plan_bootstrap.block.fetch | domain | merge_or_delete |
| project.plan_bootstrap.enter | domain | merge_or_delete |
| release.operator.approve | domain | merge_or_delete |
| release.operator.freeze | domain | merge_or_delete |
| release.operator.promote | domain | merge_or_delete |
| release.operator.rollback | domain | merge_or_delete |
| release.operator.runtime_probe | domain | merge_or_delete |
| release.operator.set_page_enabled | domain | merge_or_delete |
| release.operator.surface | domain | merge_or_delete |
| release.operator.sync_policy | domain | merge_or_delete |
| release.operator.update_page_policy | domain | merge_or_delete |
| release.operator.update_policy | domain | merge_or_delete |
| risk.action.execute | domain | merge_or_delete |
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
| search.favorite.set | domain | merge_or_delete |
| session.bootstrap | domain | merge_or_delete |
| settlement.block.fetch | domain | merge_or_delete |
| settlement.enter | domain | merge_or_delete |
| system.init | core | keep |
| system.ping.construction | domain | merge_or_delete |
| telemetry.track | domain | merge_or_delete |
| terminal.shell.v2 | domain | merge_or_delete |
| ui.contract.v2 | domain | merge_or_delete |
| usage.export.csv | domain | internal_only |
| usage.report | domain | internal_only |
| usage.track | domain | internal_only |
| user.view.preference.get | domain | merge_or_delete |
| user.view.preference.set | domain | merge_or_delete |
| workspace.home.enter | domain | merge_or_delete |

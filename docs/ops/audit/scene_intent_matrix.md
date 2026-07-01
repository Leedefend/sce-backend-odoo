# Scene Intent Matrix

- scene_count: 68
- scene_with_capability_binding: 67

| scene_key | read intents | write intents | execute intents | 未覆盖 intent | 孤立 scene | capability_refs |
|---|---|---|---|---|---:|---:|
| construction.diary | ui.contract | - | - | - | N | 9 |
| construction.execution | ui.contract | - | - | - | N | 9 |
| construction.plan | ui.contract | - | - | - | N | 9 |
| construction.plan_report | ui.contract | - | - | - | N | 9 |
| contract.center | ui.contract | - | - | - | N | 4 |
| contracts.workspace | ui.contract | - | - | - | N | 4 |
| cost.analysis | ui.contract | - | - | - | N | 4 |
| cost.budget_alloc | ui.contract | - | - | - | N | 4 |
| cost.cost_compare | ui.contract | - | - | - | N | 4 |
| cost.profit_compare | ui.contract | - | - | - | N | 4 |
| cost.project_boq | ui.contract | - | - | - | N | 12 |
| cost.project_budget | ui.contract | - | - | - | N | 4 |
| cost.project_cost_ledger | ui.contract | - | - | - | N | 4 |
| cost.project_progress | ui.contract | - | - | - | N | 4 |
| data.dictionary | ui.contract | - | - | - | N | 4 |
| default | ui.contract | - | - | - | N | 5 |
| equipment.management | ui.contract | - | - | - | N | 12 |
| equipment.request | ui.contract | - | - | - | N | 12 |
| equipment.settlement | ui.contract | - | - | - | N | 12 |
| equipment.usage | ui.contract | - | - | - | N | 12 |
| finance.center | ui.contract | - | - | - | N | 4 |
| finance.operating_metrics | ui.contract | - | - | - | N | 4 |
| finance.payment_ledger | ui.contract | - | - | - | N | 5 |
| finance.payment_requests | ui.contract | - | - | - | N | 4 |
| finance.settlement_orders | ui.contract | - | - | - | N | 5 |
| finance.treasury_ledger | ui.contract | - | - | - | N | 5 |
| finance.workspace | ui.contract | - | - | - | N | 4 |
| labor.attendance | ui.contract | - | - | - | N | 12 |
| labor.management | ui.contract | - | - | - | N | 12 |
| labor.request | ui.contract | - | - | - | N | 12 |
| labor.settlement | ui.contract | - | - | - | N | 12 |
| material.acceptance | ui.contract | - | - | - | N | 12 |
| material.catalog | ui.contract | - | - | - | N | 12 |
| material.center | ui.contract | - | - | - | N | 12 |
| material.inbound | ui.contract | - | - | - | N | 12 |
| material.outbound | ui.contract | - | - | - | N | 12 |
| material.price_library | ui.contract | - | - | - | N | 12 |
| material.procurement | ui.contract | - | - | - | N | 12 |
| material.rental | ui.contract | - | - | - | N | 12 |
| material.rental_order | ui.contract | - | - | - | N | 12 |
| material.rental_settlement | ui.contract | - | - | - | N | 12 |
| material.rfq | ui.contract | - | - | - | N | 12 |
| material.settlement | ui.contract | - | - | - | N | 12 |
| my_work.workspace | ui.contract | - | - | - | N | 4 |
| portal.capability_matrix | ui.contract | - | - | - | N | 5 |
| portal.dashboard | ui.contract | - | - | - | N | 4 |
| portal.lifecycle | ui.contract | - | - | - | N | 5 |
| project.management | ui.contract | - | - | - | N | 11 |
| projects.dashboard | ui.contract | - | - | - | N | 11 |
| projects.execution | ui.contract | - | - | - | N | 11 |
| projects.intake | ui.contract | - | - | - | N | 6 |
| projects.ledger | ui.contract | - | - | - | N | 6 |
| projects.list | ui.contract | - | - | - | N | 6 |
| quality.center | ui.contract | - | - | - | N | 9 |
| quality.recheck | ui.contract | - | - | - | N | 9 |
| quality.rectification | ui.contract | - | - | - | N | 9 |
| risk.center | ui.contract | - | - | - | N | 11 |
| risk.monitor | ui.contract | - | - | - | N | 11 |
| safety.center | ui.contract | - | - | - | N | 9 |
| safety.recheck | ui.contract | - | - | - | N | 9 |
| safety.rectification | ui.contract | - | - | - | N | 9 |
| scene_smoke_default | - | - | - | - | Y | 0 |
| subcontract.management | ui.contract | - | - | - | N | 12 |
| subcontract.register | ui.contract | - | - | - | N | 12 |
| subcontract.request | ui.contract | - | - | - | N | 12 |
| subcontract.settlement | ui.contract | - | - | - | N | 12 |
| task.center | ui.contract | - | - | - | N | 11 |
| workspace.home | ui.contract | - | - | - | N | 4 |

## Orphan Intents

- `api.data`
- `api.data.batch`
- `api.data.create`
- `api.data.unlink`
- `api.onchange`
- `app.catalog`
- `app.nav`
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
- `execute_button`
- `file.download`
- `file.upload`
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
- `permission.check`
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
- `scene.governance.export_contract`
- `scene.governance.pin_stable`
- `scene.governance.rollback`
- `scene.governance.set_channel`
- `scene.health`
- `scene.package.dry_run_import`
- `scene.package.export`
- `scene.package.import`
- `scene.package.list`
- `scene.packages.installed`
- `search.favorite.set`
- `session.bootstrap`
- `settlement.block.fetch`
- `settlement.enter`
- `system.init`
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

## Uncovered Scenes

- `scene_smoke_default`

## No Write/Execute Scenes

- `construction.diary`
- `construction.execution`
- `construction.plan`
- `construction.plan_report`
- `contract.center`
- `contracts.workspace`
- `cost.analysis`
- `cost.budget_alloc`
- `cost.cost_compare`
- `cost.profit_compare`
- `cost.project_boq`
- `cost.project_budget`
- `cost.project_cost_ledger`
- `cost.project_progress`
- `data.dictionary`
- `default`
- `equipment.management`
- `equipment.request`
- `equipment.settlement`
- `equipment.usage`
- `finance.center`
- `finance.operating_metrics`
- `finance.payment_ledger`
- `finance.payment_requests`
- `finance.settlement_orders`
- `finance.treasury_ledger`
- `finance.workspace`
- `labor.attendance`
- `labor.management`
- `labor.request`
- `labor.settlement`
- `material.acceptance`
- `material.catalog`
- `material.center`
- `material.inbound`
- `material.outbound`
- `material.price_library`
- `material.procurement`
- `material.rental`
- `material.rental_order`
- `material.rental_settlement`
- `material.rfq`
- `material.settlement`
- `my_work.workspace`
- `portal.capability_matrix`
- `portal.dashboard`
- `portal.lifecycle`
- `project.management`
- `projects.dashboard`
- `projects.execution`
- `projects.intake`
- `projects.ledger`
- `projects.list`
- `quality.center`
- `quality.recheck`
- `quality.rectification`
- `risk.center`
- `risk.monitor`
- `safety.center`
- `safety.recheck`
- `safety.rectification`
- `subcontract.management`
- `subcontract.register`
- `subcontract.request`
- `subcontract.settlement`
- `task.center`
- `workspace.home`

## Scene Missing Intent Refs

- none

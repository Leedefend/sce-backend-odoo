# Menu and Role Visibility Governance Plan v1

Date: 2026-04-26
Database observed: `sc_prod_sim`

## Goal

The menu system must match real user work habits and risk boundaries:

- Business users see business processing entries only.
- Business system administrators see business configuration entries.
- Platform system administrators see platform and system configuration entries.

This is an operating boundary, not only a UI cleanup. If the menu is wrong,
users either cannot find daily work or receive authority that belongs to
implementation, platform operations, or system governance.

## Classification Principles

### L1 Business Processing

Audience: ordinary business roles: project, contract, cost, material, purchase,
finance, settlement, and their approval managers.

Frequency: daily or weekly.

Rule:

- Put high-frequency document creation, review, query, approval, and ledger
  screens here.
- Keep names close to business language, not implementation language.
- Do not expose scene governance, workflow definitions, subscription, system
  parameters, model configuration, or migration administration here.

Examples:

- 项目管理: project initiation, project list, lifecycle cockpit, execution
  structure, construction diary, engineering documents.
- 合同管理: income contracts, expense contracts, general contracts, historical
  contract evidence needed for day-to-day continuity.
- 财务账款: payment requests, payment execution, receipts, invoice
  registration, expense claims, treasury reconciliation, treasury ledger.
- 成本管理: budgets, BOQ, progress measurement, cost ledger, profit reports.
- 物资管理: material plans, material approval, selected material archive use.

### L2 Business Configuration

Audience: business system administrators and implementation key users.

Frequency: monthly, project setup, policy change, or master-data maintenance.

Rule:

- Configuration that changes business behavior or business master data belongs
  here.
- This layer must not imply Odoo `base.group_system`.
- Business managers do not automatically get this layer unless explicitly
  assigned.

Examples:

- 业务字典: disciplines, chapters, quota items, subitems, general business
  dictionary.
- 定额库 and quota import.
- 成本科目.
- 阶段要求配置 and project lifecycle requirement items.
- Partner/contact master maintenance if the user is assigned contact master
  responsibility.
- Controlled material-to-product promotion.

### L3 Platform/System Configuration

Audience: platform system administrators only.

Frequency: rare, implementation, release, system governance, troubleshooting.

Rule:

- This layer may imply Odoo `base.group_system`.
- No ordinary business role and no management/business-full role should receive
  this layer implicitly.
- Menus here should be hidden from users unless they administer the platform.

Examples:

- 场景与能力: capability catalog, scene orchestration, capability groups, scene
  versions, delivery package registry and installation records.
- Scene Governance: channel switching, pin/rollback, governance logs.
- Subscription and entitlement: plans, subscriptions, entitlement snapshots,
  usage counters, ops jobs.
- Workflow definitions, workflow instances, work items, workflow logs.
- Technical menu patches and platform initialization controls.

## Current Observed Problems

Observed with Odoo runtime menu visibility on `sc_prod_sim`.

1. `demo_role_project_read`, `demo_role_project_user`, `demo_role_project_manager`,
   and `demo_role_finance` can still see `Scene Governance / Governance Logs`
   through a child menu even though they do not have the top-level platform
   configuration menu. This is a system-configuration leak.

2. `demo_role_executive` currently has `base.group_system=true` because the
   executive role implies `group_sc_cap_config_admin`, and that group implies
   Odoo system administrator. This makes management a platform administrator,
   which is not acceptable for production.

3. The current `基础资料` menu mixes business configuration and platform
   configuration:

   - business configuration: dictionaries, quota library, cost subjects, stage
     requirements;
   - platform configuration: scene orchestration, subscriptions, workflow
     definitions, governance logs.

4. Some business configuration is attached under a high-frequency processing
   area, for example `项目管理 / 项目管理（后台） / 阶段要求配置`. This is useful
   for implementers, but it is not a daily business processing entry and should
   move to business configuration.

5. `Business Full` currently includes platform configuration through
   `group_sc_cap_config_admin`. A business-full test role should represent full
   business operation, not system administration.

## Proposed Role Boundary

| Layer | Group | Implies `base.group_system` | Intended users |
| --- | --- | --- | --- |
| Business processing | existing center read/user/manager groups | No | ordinary users and approvers |
| Business configuration | `group_sc_cap_business_config_admin` | No | business system administrators, implementation key users |
| Platform/system configuration | `group_sc_cap_config_admin` renamed as platform system admin | Yes | platform administrators only |

Compatibility note:

- Keep the XML id `group_sc_cap_config_admin` for platform system admin to avoid
  breaking existing references.
- Add a new XML id `group_sc_cap_business_config_admin` for business
  configuration.
- Remove `group_sc_cap_config_admin` from business-full and executive roles.

## Proposed Menu Structure

### Business Processing Menus

Keep the first screen focused on frequent work:

- 项目管理
- 合同管理
- 成本管理
- 物资管理
- 财务账款
- 看板中心 / 数据分析 where genuinely used for business review

Business users should not see:

- 基础资料
- 系统配置
- 场景与能力
- Scene Governance
- 工作流定义
- 订阅/授权/用量/运营任务

### Business Configuration Menus

Create or repurpose one top-level menu:

- 业务配置

Suggested children:

- 业务字典
- 定额库
- 成本科目
- 阶段要求配置
- 联系人/往来单位主数据, if required by the final business role policy
- 业务初始化完整度, for release/setup checks that business admins can run

Visibility:

- `group_sc_cap_business_config_admin`
- platform system admin through implication

### System Configuration Menus

Create or repurpose one top-level menu:

- 系统配置

Suggested children:

- 场景与能力
- Scene Governance
- 订阅与授权
- 工作流
- 交付包
- 运营任务
- platform initialization and technical checks

Visibility:

- `group_sc_cap_config_admin` only

## Implementation Plan

1. Security groups
   - Add `group_sc_cap_business_config_admin`.
   - Rename the display name of `group_sc_cap_config_admin` to platform system
     admin while keeping its XML id.
   - Remove platform admin from `Business Full`.
   - Remove platform admin from executive role; if needed, give executive
     business configuration only.

2. Menu roots
   - Keep existing business processing root.
   - Split current `基础资料` into `业务配置` and `系统配置`.
   - Do not use an invisible parent with visible child menus for platform
     configuration; every platform child must carry the platform admin group.

3. Menu moves
   - Move dictionaries, quota library, cost subjects, quota import, and stage
     requirement configuration under `业务配置`.
   - Move scene orchestration, scene governance, subscriptions, entitlements,
     usage counters, ops jobs, workflow definition/instance/log menus under
     `系统配置`.
   - Review `项目管理（后台）`: keep only operational manager views there; move
     durable configuration out.

4. Verification
   - Add a role menu visibility probe.
   - The probe must fail if ordinary business roles see system configuration.
   - The probe must fail if executive or business-full implies
     `base.group_system`.
   - The probe must pass only when business configuration appears for business
     config admins and system configuration appears only for platform admins.

## Acceptance Criteria

- Project/contract/finance/material/cost/settlement users see business
  processing menus only.
- Business managers see approval and management work surfaces, not platform
  system menus.
- Business system administrators see business configuration, but do not have
  `base.group_system`.
- Platform system administrators see business configuration and system
  configuration.
- No non-platform role sees `Scene Governance`, scene orchestration,
  subscriptions, entitlements, usage counters, ops jobs, or workflow technical
  menus.
- `Business Full` remains a full business role and is not a system
  administrator.
- Executive role is management/business visibility, not platform
  administration.


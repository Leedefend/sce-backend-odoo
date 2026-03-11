# SCEMS v1.0 Release Scope Freeze

## 1. Document Info
- Version: `v1.0`
- Status: `Draft` (scope freeze review)
- Master plan: `docs/releases/construction_system_v1_release_plan.en.md`

## 2. In Scope

### 2.1 Business Domains
- Project Management
- Contract Management
- Cost Control
- Fund Management
- Task Collaboration
- Risk Alerting

### 2.2 Primary Navigation (Frozen)
- My Work
- Project Ledger
- Project Management
- Contract Management
- Cost Control
- Fund Management
- Risk Alerts

### 2.3 Core Scenes (Frozen)
- `my_work.workspace`
- `projects.ledger`
- `project.management`
- `contracts.workspace`
- `cost.analysis`
- `finance.workspace`
- `risk.center`

### 2.4 Project Management Console (Frozen)
Must include 7 blocks:
- Header (basic info)
- Metrics
- Progress
- Contract
- Cost
- Finance
- Risk

## 3. Out of Scope
- Config Center in primary navigation
- Data Center in primary navigation
- System Governance in primary navigation
- New external dependencies/modules without change review

## 4. Delivery Policy
- Product surface: `construction_pm_v1`
- Main nav allowlist:
  - `project.management`
  - `projects.ledger`
  - `my_work.workspace`
  - `contracts.workspace`
  - `cost.analysis`
  - `finance.workspace`
  - `risk.center`
- Hidden patterns: `config.*`, `data.*`, `internal.*`

## 5. Freeze Exit Criteria
- Scope doc, asset inventory, and gap analysis are ready
- Navigation/scene list aligned with delivery policy
- Core path works end-to-end

## 6. Change Control
- Any scope change requires change request and release-owner approval
- After freeze, only release-blocking fixes are allowed


# Smart Construction Enterprise Management System v1.0 Release Plan

- Version: `v1.0`
- Goal: deliver the first deployable, demo-ready, production-usable release for construction enterprise project management.

## 1. Release Objectives

### Product Name

**Smart Construction Enterprise Management System**

Short name:

```
SCEMS v1.0
```

### Product Positioning

A digital management system for core construction project operations, targeting:

- Project managers
- Project operation staff
- Finance collaboration staff
- Executive supervisors

Core objective:

```
Make project execution transparent, risks visible, and decisions data-driven.
```

## 2. V1 Scope

V1 must provide an end-to-end business loop across:

```
Project Management
Contract Management
Cost Control
Fund Management
Task Collaboration
Risk Alerting
```

### Primary Navigation

Fixed V1 primary nav:

```
My Work
Project Ledger
Project Management
Contract Management
Cost Control
Fund Management
Risk Alerts
```

Excluded from primary nav:

```
Configuration Center
Data Center
System Governance
```

### Core Scenarios (minimum 4)

1) `my_work.workspace`
- To-do tasks, my projects, quick entries, risk summary.

2) `projects.ledger`
- Project list, filter/search, navigation to project console.

3) `project.management` (core)
- Must include 7 blocks:

```
Basic Info
Key Metrics
Progress
Contract Execution
Cost Control
Finance
Risk Alerts
```

Expected page structure:

```
Header
Metrics
Progress
Contract
Cost
Finance
Risk
```

4) Business Workbench
- Domain areas: contract center, cost control, fund management.

## 3. System Architecture

Five-layer architecture:

```
Domain Model Layer
Service Aggregation Layer
Capability Layer
Scene Orchestration Layer
Frontend Rendering Layer
```

### Domain Model Layer

Core Odoo models:

```
project.project
construction.contract
project.cost
payment.request
project.task
risk.signal
```

### Service Aggregation Layer

Planned services:

```
ProjectDashboardService
ContractSummaryService
CostAnalysisService
FinanceSummaryService
RiskDetectService
```

### Capability Layer

Planned capabilities:

```
project.dashboard.view
contract.execution.summary
cost.deviation.analysis
finance.payment.summary
risk.alert.detect
task.pending.summary
```

### Scene Orchestration Layer

Core scenes:

```
my_work.workspace
projects.ledger
project.management
contracts.workspace
cost.analysis
finance.workspace
risk.center
```

### Frontend Rendering Layer

Vue3-based components:

```
SceneView
DashboardView
RecordList
RecordForm
BlockComponent
```

Block types:

```
HeaderBlock
MetricBlock
ProgressBlock
TableBlock
AlertBlock
```

## 4. Delivery Strategy

Use Scene Delivery Policy with product surface:

```
construction_pm_v1
```

Primary nav scene allowlist:

```
project.management
projects.ledger
my_work.workspace
contracts.workspace
cost.analysis
finance.workspace
risk.center
```

Hidden patterns:

```
config.*
data.*
internal.*
```

## 5. Role and Permission Model

Fixed V1 roles:

```
Project Manager
Project Member
Contract Admin
Finance Collaborator
Management Viewer
System Administrator
```

Permission dimensions:

```
Model ACL
Record Rules
Block Visibility
Capability Access
```

## 6. Verification System

Required verification categories:

```
contract verify
scene route verify
permission verify
smoke test
```

Planned verify targets:

```
verify.project.dashboard.contract
verify.project.dashboard.route
verify.project.dashboard.permission
verify.portal.navigation
```

## 7. Deployment System

Environments:

```
dev
test
prod
```

Must provide:

```
Docker deployment
DB initialization
module install scripts
upgrade scripts
rollback plan
```

Deployment doc target:

```
docs/deploy/deployment_guide_v1.md
```

## 8. Demo and Acceptance

### Demo Script

File target:

```
docs/demo/system_demo_v1.md
```

Flow:

```
Login
My Work
Project Ledger
Project Console
Contract Execution
Cost
Finance
Risk Alerts
```

### User Acceptance Checklist

File target:

```
docs/releases/user_acceptance_checklist.md
```

Checklist:

```
Navigation correctness
Project access
Console stability
Contract data accuracy
Cost data accuracy
Finance data accuracy
Risk alerts accuracy
Permission correctness
```

## 9. Phase Plan

### Phase 0

Scope freeze outputs:

```
release_scope_v1.md
system_asset_inventory.md
release_gap_analysis.md
```

### Phase 1

Navigation convergence:

```
Scene Delivery Policy
construction_pm_v1 finalization
Primary nav lock
```

### Phase 2

Core scenario loop:

```
My Work
Project Ledger
Project Console
Business Workbench
```

### Phase 3

Role/permission system:

```
ACL
Block visibility
Role matrix
Demo fixtures
```

### Phase 4

Frontend stability:

```
Unified page framework
Unified block components
Unified interaction conventions
```

### Phase 5

Verification and deployment:

```
verify scripts
deployment guide
demo script
acceptance checklist
```

### Phase 6

Pilot and launch:

```
Pilot rollout
Feedback collection
v1.0 launch
```

## 10. Launch Success Criteria

System must be:

```
deployable
demo-ready
trainable
usable in real operations
```

Complete user path must work:

```
Login
→ My Work
→ Project Ledger
→ Project Console
→ Contract
→ Cost
→ Finance
→ Risk
```

## 11. Immediate Execution Tasks

Round 1:

```
Freeze V1 scope
Complete system asset inventory
Produce release gap analysis
Finalize construction_pm_v1 navigation
Confirm core scene list
```

Round 2:

```
Implement project.management scene
Implement project.dashboard contract
Implement ProjectDashboardService
Implement 7 dashboard blocks
```

Round 3:

```
Implement My Work
Implement Contract Center
Implement Fund Management
Implement permission control
```

## 12. Core Release Principles

System principles:

```
Requirement enters Scene first
Scene composes Capabilities
Capability is exposed via Contract
Service implements business logic
Delivery Policy controls product rollout
```

One-line summary:

```
Requirement → Scene → Capability → Contract → Service → UI → Release
```


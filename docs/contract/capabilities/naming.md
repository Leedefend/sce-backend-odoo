# Capability Key Naming

## Scope
Capability keys are platform-level identifiers for capability registry entries and contract payloads.

## Key Pattern
Use exactly three segments:

- `{domain}.{area}.{action}`
- `{domain}.{object}.{verb}`

Regex:

- `^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$`

Examples:

- `project.initiation.enter`
- `finance.payment_request.list`
- `analytics.lifecycle.monitor`

## Grouping
Every capability must define `group_key` and it must map to a registered capability group.

Current group keys:

- `project_management`
- `finance_management`
- `cost_management`
- `contract_management`
- `analytics`
- `governance`
- `material_management`
- `others`

## Entry Target
Every capability must provide an `entry_target.scene_key` that can be resolved to an openable scene target.

## Guard Requirements
`verify.capability.registry.smoke` enforces:

- key regex compliance
- `group_key` non-empty and known
- no duplicate keys
- minimum capability count (`>=30`)
- `entry_target.scene_key` exists and is openable through scene registry

# Main Entry Convergence v1

## Goal

Make [project.management](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/ProjectManagementDashboardView.vue) the primary product entry and downgrade `my_work.workspace` to an auxiliary entry.

## Entry Roles

### Primary Entry

- scene: `project.management`
- product meaning: project cockpit
- responsibility:
  - explain current project state
  - show recommended next action
  - surface business risks
  - return users back to the cockpit after a mainline action

### Auxiliary Entry

- scene: `my_work.workspace`
- product meaning: inbox / todo center
- responsibility:
  - aggregate reminders
  - show pending items
  - provide quick jump back to the cockpit

## Resolution Rule

Main entry project resolution is owned by:
- [project_entry_context_service.py](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/addons/smart_construction_core/services/project_entry_context_service.py)

Order:
1. explicit current project
2. latest project created by current user
3. user-related project
4. global fallback project
5. no project -> workspace fallback

## Dashboard Requirements

The primary entry must show:
- stage explanation
- milestone explanation
- status explanation
- recommended next action with reason
- readable risk reminders

## Return Rhythm

Stable product rhythm:
- cockpit -> business scene -> cockpit

This replaces menu-driven mainline navigation as the default user path.

## Boundary

- no project semantics in `smart_core`
- project-entry resolution stays in `smart_construction_core`
- frontend only consumes the resolved project-entry contract

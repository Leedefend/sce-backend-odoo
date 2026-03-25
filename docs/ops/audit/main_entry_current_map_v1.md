# Main Entry Current Map v1

## Scope

This audit records the current main-entry routing after `Main Entry Convergence v1` implementation.

## Current Defaults

### Login Success

- entry decision owner: [session.ts](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/stores/session.ts)
- redirect caller: [LoginView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/LoginView.vue)
- current rule:
  - resolve `project.entry.context.resolve`
  - if project is available: enter `/s/project.management`
  - if no project is available: fallback to `/my-work`

### Root Route `/`

- route consumer: [HomeView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/HomeView.vue)
- current rule:
  - immediately redirect to the same primary-entry decision
  - no longer treat `/` as a lasting homepage for the project mainline

### Workspace Entry

- page: [MyWorkView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/MyWorkView.vue)
- current role:
  - todo center
  - reminder inbox
  - auxiliary quick entry
- no longer intended to be the default project mainline entry when a usable project exists

## Project Resolution Rules

Resolver owner:
- backend service: [project_entry_context_service.py](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/addons/smart_construction_core/services/project_entry_context_service.py)

Resolution order:
1. explicit current project
2. latest project created by current user
3. user ownership/member domain project
4. global fallback project
5. no project -> `/my-work`

Returned shape:
- `project_context`
- `source`
- `confidence`
- `route`
- `diagnostics`

## Existing Jumps To Workspace

The following cases still legitimately go to `my_work.workspace`:
- login success with no resolvable project
- project dashboard enter returns `PROJECT_NOT_FOUND`
- user explicitly opens `/my-work`

## Existing Jumps To Dashboard

The following cases now resolve to `project.management`:
- login success for a project-bearing PM user
- root `/` after app bootstrap
- dashboard refresh and post-action return flow
- project quick-create first handoff

## Boundary Notes

- project-entry resolution stays in `smart_construction_core`
- `smart_core` is not aware of `project_context` business semantics
- no query-string `project_id` is required for the main entry path

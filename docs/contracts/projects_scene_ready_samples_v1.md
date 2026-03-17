# Projects Scene-ready Contract Samples v1

## `projects.list`（样例）

```json
{
  "scene": {"key": "projects.list", "title": "项目列表"},
  "page": {"scene_key": "projects.list", "route": "/s/projects.list"},
  "search_surface": {"default_sort": "write_date desc", "filters": [], "group_by": []},
  "permission_surface": {"visible": true, "allowed": true},
  "action_surface": {"primary": [], "secondary": [], "contextual": []}
}
```

## `projects.intake`（样例）

```json
{
  "scene": {"key": "projects.intake", "title": "项目立项"},
  "page": {"scene_key": "projects.intake", "route": "/s/projects.intake"},
  "next_scene": "project.management",
  "next_scene_route": "/s/project.management",
  "validation_surface": {"required_fields": ["name", "manager_id"]},
  "workflow_surface": {"state_field": "state", "states": []},
  "permission_surface": {"visible": true, "allowed": true}
}
```

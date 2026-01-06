# Audit Node Missing Exceptions

- action_get_list_view (project.view_project_kanban)
  - reason: NODE_MISSING
  - evidence: final merged kanban arch (get_view/fields_view_get) for admin in sc_demo contains no action_get_list_view nodes.
  - verdict: keep visible=0; do not backfill or chase historical mappings.

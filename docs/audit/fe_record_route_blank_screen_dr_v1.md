# FE Record Route Blank Screen DR

```json
{
  "next_candidate_family": "record_route_registration_missing",
  "family_scope": [
    "frontend/apps/web/src/router/index.ts",
    "frontend/apps/web/src/pages/ModelFormPage.vue",
    "frontend/apps/web/src/pages/ContractFormPage.vue"
  ],
  "reason": "The frontend still has record-form consumers and multiple producers that emit `/compat/record/...`, but the router no longer registers `/r/:model/:id`, `/f/:model/:id`, or `/compat/record/:model/:id`. `ModelFormPage.vue` and `ContractFormPage.vue` still exist as the intended record/form consumer surfaces, and `SceneView` still embeds `ContractFormPage` for record layouts. This means the reported unreachable record URL is primarily another missing thin bridge problem at the router boundary, not a proven form consumer failure or backend semantic gap."
}
```

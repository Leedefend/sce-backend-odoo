# FE Compat Record Retirement Screen DX

```json
{
  "next_candidate_family": "compat_record_ingress_verify_required",
  "family_scope": [
    "frontend/apps/web/src/views/CapabilityMatrixView.vue",
    "frontend/apps/web/src/app/resolvers/sceneRegistry.ts",
    "frontend/apps/web/src/app/action_runtime/useActionViewActionMetaRuntime.ts",
    "frontend/apps/web/src/router/index.ts"
  ],
  "reason": "The bounded frontend scope no longer contains any explicit producer that constructs `/compat/record/...` URLs. However, the residual consumer surfaces still treat `/compat/record/` as a live ingress family: CapabilityMatrixView still classifies it as an internal route, useActionViewActionMetaRuntime still accepts it as a shell route for self-navigation, sceneRegistry still recognizes it as a legacy compat route and rewrites legacy route inputs back onto the default scene route, and router/index.ts still registers the compat-record bridge. This means producer-side shrink is complete, but bridge retirement is not yet proven safe. The stronger next bounded family is an ingress verify line that checks whether old contract metadata, saved URLs, or runtime action payloads can still deliver `/compat/record/...` into the frontend."
}
```

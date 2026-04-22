# FE Compat Record Residual Screen DW

```json
{
  "next_candidate_family": "compat_record_bridge_retirement_verify",
  "family_scope": [
    "frontend/apps/web/src/views/CapabilityMatrixView.vue",
    "frontend/apps/web/src/app/resolvers/sceneRegistry.ts",
    "frontend/apps/web/src/app/action_runtime/useActionViewActionMetaRuntime.ts",
    "frontend/apps/web/src/router/index.ts"
  ],
  "reason": "A bounded search for `/compat/record` under frontend/apps/web/src no longer finds any active producer that constructs or emits `/compat/record/...` URLs. The remaining references are all consumer-side compatibility surfaces: CapabilityMatrixView and useActionViewActionMetaRuntime treat `/compat/record/` as an internal shell route, sceneRegistry still recognizes it as a legacy compat route family, and router/index.ts still registers the compat-record bridge. This means the strongest next bounded family is no longer producer migration; it is a retirement/verify line that proves whether compat-record bridge registration and recognizers can be safely narrowed or removed without reopening real usability regressions."
}
```

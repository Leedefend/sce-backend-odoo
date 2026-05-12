# ESLint Debt Scope Note

## 本次 PR 必需
- `frontend/apps/web/src/main.ts` / `styles/*` / `views/LoginView.vue` / `layouts/AppShell.vue` 为 token 化与主题切换交付必需改动。

## 历史债隔离
- `.eslintignore` 中列出的文件为仓库既有 lint 历史债，本次未做语义重构，仅隔离以避免阻断 token 产品化交付。

## 后续治理建议
- 单独批次移除 `.eslintignore` 条目并逐文件修复 no-unused-vars / no-explicit-any / vue/no-dupe-keys。

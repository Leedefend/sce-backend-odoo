# Commit Message 规范

采用 Angular 风格：

格式：
<type>(scope): <subject>

type 可选：
- feat: 新功能
- fix: 修复
- docs: 文档
- style: 代码格式
- refactor: 重构（不改变功能）
- test: 测试相关
- chore: 构建、依赖调整

示例：

feat(settlement): add settlement order models and views
fix(contract): correct compute of total_amount
docs: update module usage guide
# 分支命名规则

采用：type/issueID-short-description

示例：
feat/15-settlement-center
fix/22-contract-date-error
refactor/10-project-model-cleanup

主分支：
main（禁止直接 push）

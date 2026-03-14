# SCEMS v1.0 Phase 5：验证与部署检查清单

## 1. 目标
完成发布级验证闭环与部署可执行性，确保系统“可验证、可部署、可回滚”。

## 2. 覆盖范围
- 后端验证链路
- 前端构建与质量门
- 部署脚本与环境准备
- 发布证据与归档

## 3. 必做项

### A. 验证闭环
- [x] 发布关键 verify 链路通过（scene/catalog/runtime/contract）
- [x] 核心业务路径 smoke 测试通过
- [x] 关键角色（项目经理/财务协同/管理层）路径验证通过
- [x] 发布态 Demo 种子已加载并通过验收（`demo.load.release` + `verify.demo.release.seed`）

### B. 契约与一致性
- [x] `system.init` 与 `ui.contract` 在 user/hud 模式一致可用
- [x] 场景投放策略与导航输出一致
- [x] 契约导出与运行态无阻断级漂移

### C. 部署准备
- [x] `dev/test/prod` 环境参数清单完整
- [x] Docker 部署流程可重复执行
- [x] 模块安装、升级、回滚脚本可执行

### D. 发布文档齐套
- [x] 部署指南：`docs/deploy/deployment_guide_v1.md`
- [x] 演示脚本：`docs/demo/system_demo_v1.md`
- [x] 验收清单：`docs/releases/user_acceptance_checklist.md`

### E. 证据与归档
- [x] 发布验证证据归档到统一目录
- [x] 关键 artifact 可追溯（命令、时间、结果）
- [x] 发布结论（通过/阻塞）明确记录

## 4. 建议验证命令
- `make demo.load.release DB_NAME=sc_demo`
- `make verify.demo.release.seed DB_NAME=sc_demo`
- `make verify.phase_next.evidence.bundle`
- `make verify.runtime.surface.dashboard.strict.guard`
- `make verify.project.form.contract.surface.guard`
- `make verify.scene.catalog.governance.guard`

## 5. 交付产物
- Phase 5 报告（建议：`artifacts/release/phase5_verification_deployment.md`）
- 验证证据包（backend artifacts + scene governance + frontend quality）

## 6. 退出条件
- 清单项全部打勾
- 部署/回滚流程演练通过
- 执行看板 Phase 5 状态更新为 `DONE`

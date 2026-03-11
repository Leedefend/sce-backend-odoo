# SCEMS v1.0 执行看板（Execution Board）

状态图例：`TODO` / `DOING` / `BLOCKED` / `DONE`

## 1. 总体里程碑

| Phase | 目标 | 状态 | 关键输出 |
|---|---|---|---|
| Phase 0 | 范围冻结 | DONE | `release_scope_v1.md` `system_asset_inventory.md` `release_gap_analysis.md` |
| Phase 1 | 导航收口 | DONE | delivery policy 主导航锁定报告 |
| Phase 2 | 核心场景闭环 | DOING | 4 大场景可用性验收记录（workspace 基线已收口） |
| Phase 3 | 角色权限体系 | DONE | 角色矩阵 + ACL/可见性校验 + 退出就绪报告 |
| Phase 4 | 前端体验稳定 | DONE | 页面框架和 block 规范收敛（含 user/hud 与容器 smoke 证据） |
| Phase 5 | 验证与部署 | DONE | 发布验证包 + 部署文档 + 部署/回滚演练证据 |
| Phase 6 | 试运行首发 | TODO | 试运行报告 + v1.0 发布记录 |

## 2. 当前执行窗口（W1）

- 发布分支启动记录：`docs/releases/phase_0_scope_freeze_execution.md`

### W1-目标
- 完成 Phase 1（导航收口）
- 启动 Phase 2（核心场景闭环）

### W1-任务

| ID | 任务 | Phase | 状态 | 验收标准 |
|---|---|---|---|---|
| W1-01 | 固化 `construction_pm_v1` 主导航 allowlist | P1 | DONE | policy 文件与运行结果一致 |
| W1-02 | 输出主导航与 Scene 映射清单 | P1 | DONE | 7 个主导航项全部可追踪 |
| W1-03 | 建立 `project.management` 7-block 契约检查脚本 | P2 | DONE | verify 能识别 7 个 block |
| W1-04 | 梳理“我的工作”最小闭环数据 | P2 | DONE | 待办/我的项目/快捷入口可见 |
| W1-05 | 梳理“项目台账”入口到控制台链路 | P2 | DONE | ledger -> management 可达 |

## 3. 风险清单

| 风险 | 等级 | 现象 | 缓解动作 |
|---|---|---|---|
| 业务语义与契约字段偏移 | 高 | 页面有块，数据口径不一致 | 先定义 block 字段白名单与必填项 |
| 角色可见性不一致 | 中 | 同场景不同角色看到不稳定 | 引入角色矩阵验证脚本 |
| 发布文档与实现脱节 | 中 | 文档更新滞后 | 每个 Phase 结束强制更新执行看板 |

## 4. 当前执行窗口（W2）

| ID | 任务 | Phase | 状态 | 验收标准 |
|---|---|---|---|---|
| W2-01 | 建立管理层只读 guard | P3 | DONE | `verify.role.management_viewer.readonly.guard` PASS |
| W2-02 | 统一 project_member 角色映射 | P3 | DONE | `verify.role.project_member.unification.guard` PASS |
| W2-03 | 系统管理员最小权限审计报告 | P3 | DONE | `verify.role.system_admin.minimum_permission_audit.guard` PASS |

### W3-任务（Phase 3 退出收口）

| ID | 任务 | Phase | 状态 | 验收标准 |
|---|---|---|---|---|
| W3-01 | ACL 最小权限集 guard | P3 | DONE | `verify.role.acl.minimum_set.guard` PASS |
| W3-02 | 关系访问策略一致性审计 | P3 | DONE | `verify.relation.access_policy.consistency.audit` PASS |
| W3-03 | 三项运行时专项补齐 | P3 | DONE | `verify.project.dashboard.role_runtime.guard` + `verify.scene.permission_reasoncode_deeplink.guard` PASS |

### W4-任务（Phase 4 前端稳定）

| ID | 任务 | Phase | 状态 | 验收标准 |
|---|---|---|---|---|
| W4-01 | 前端页面/区块静态 guard 基线 | P4 | DONE | 9 个 frontend guard 全部 PASS |
| W4-02 | 构建与类型检查基线 | P4 | DONE | `verify.frontend.build` + `verify.frontend.typecheck.strict` PASS |
| W4-03 | lint 基线债务收口 | P4 | DONE | `verify.frontend.lint.src` 0 errors（剩余 6 warnings） |
| W4-04 | user/hud 跨模式稳定性专项 | P4 | DONE | hud 导航/编排方差/trace smoke 全 PASS |
| W4-05 | 页面框架与交互规范收口 | P4 | DONE | A/C 类校验命令链路全 PASS |
| W4-06 | 控制台严重报错专项证据 | P4 | DONE | fe/hud/render-mode 容器 smoke 全 PASS |

### W5-任务（Phase 5 验证与部署）

| ID | 任务 | Phase | 状态 | 验收标准 |
|---|---|---|---|---|
| W5-01 | 发布关键 verify 链路基线 | P5 | DONE | phase_next/runtime strict/scene governance PASS |
| W5-02 | 核心业务 smoke 与角色路径 | P5 | DONE | my_work smoke + role floor + management readonly PASS |
| W5-03 | 部署/演示/验收文档补齐 | P5 | DONE | deploy/demo/UAT 文档齐套 |
| W5-04 | 部署与回滚演练证据 | P5 | DONE | `make up`/`make mod.install`/`make mod.upgrade`/`make scene.rollback.stable` PASS |
| W5-05 | 发布结论归档 | P5 | DONE | Phase 5 报告与清单均明确记录“通过” |

## 5. 进入下一阶段条件

### Phase 1 -> Phase 2
- `construction_pm_v1` 主导航锁定完成
- 导航/scene/delivery policy 三者一致

### Phase 2 -> Phase 3
- 四大核心场景基本闭环可演示
- `project.management` 7-block 全量可见且契约通过

# SCEMS v1.0 执行看板（Execution Board）

状态图例：`TODO` / `DOING` / `BLOCKED` / `DONE`

## 1. 总体里程碑

| Phase | 目标 | 状态 | 关键输出 |
|---|---|---|---|
| Phase 0 | 范围冻结 | DONE | `release_scope_v1.md` `system_asset_inventory.md` `release_gap_analysis.md` |
| Phase 1 | 导航收口 | DOING | delivery policy 主导航锁定报告 |
| Phase 2 | 核心场景闭环 | TODO | 4 大场景可用性验收记录 |
| Phase 3 | 角色权限体系 | TODO | 角色矩阵 + ACL/可见性校验 |
| Phase 4 | 前端体验稳定 | TODO | 页面框架和 block 规范收敛 |
| Phase 5 | 验证与部署 | TODO | 发布验证包 + 部署文档 |
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

## 4. 进入下一阶段条件

### Phase 1 -> Phase 2
- `construction_pm_v1` 主导航锁定完成
- 导航/scene/delivery policy 三者一致

### Phase 2 -> Phase 3
- 四大核心场景基本闭环可演示
- `project.management` 7-block 全量可见且契约通过

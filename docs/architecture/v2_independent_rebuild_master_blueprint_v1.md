# v2 独立重建总体蓝图 v1

## 目标

将 `smart_core v2` 从“局部迁移驱动”切换为“阶段闭环驱动”，采用双轨策略：

- 旧模块继续承接现网运行
- 新模块独立重建、独立治理、成熟后切换

## 重建原则

1. 新模块先求完整闭环，不先抠局部最优。
2. 新旧模块硬隔离，禁止半新半旧混编。
3. 迭代按层级闭环推进，不按问题点推进。
4. 切换标准先冻结、后开发。

## 双轨边界

- 新模块：`addons/smart_core/v2/**`
- 旧模块：`addons/smart_core/**`（除 `v2` 子树）
- 新模块不反向修改旧模块 public contract。
- 切换前以对比与灰度为主，不做隐式替换。

## 六阶段节奏

### 阶段 0：重建准备期

**目标**：建立重建工程基础设施。

**必做项**：
- 命名与边界冻结
- 目录骨架完整建立
- 开发模板统一（intent/handler/parser/builder/verify）
- 最小治理骨架可运行（gate/schema/failure-path）
- 切换原则文档冻结

**不做项**：
- 复杂业务迁移
- 深度 parser 扩展

**退出标准**：
- 骨架齐全、模板可复用、门禁可跑。

### 阶段 1：入口与注册闭环

**目标**：请求可稳定寻址到唯一 intent + handler。

**必做项**：
- Intent Registry 可运行
- Dispatcher 只做分发/校验/异常壳
- 最小 request schema 体系
- Handler 模板统一

**退出标准**：
- 未注册/重复/僵尸意图可审计，主入口可稳定分发。

### 阶段 2：执行主链闭环

**目标**：handler/service/orchestrator/builder 职责清晰。

**必做项**：
- 分层拆分落地
- Result Object 化
- permission/capability/visibility policy 抽离

**退出标准**：
- handler 不再兼做 service/parser/builder。

### 阶段 3：解析闭环

**目标**：parser 体系化并具备覆盖/诊断能力。

**必做项**：
- BaseParser
- 分型解析器（structure/field/modifier/action/menu/capability）
- ParseResult 统一骨架
- coverage + diagnostics

**退出标准**：
- 未支持项可见，不再静默吞掉。

### 阶段 4：契约输出闭环

**目标**：输出稳定、版本化、可回归。

**必做项**：
- Response Envelope 统一
- Contract Builder 体系
- Contract version + snapshot
- failure-path contract 冻结

**退出标准**：
- 成功/失败路径均可快照回归。

### 阶段 5：治理与回归闭环

**目标**：从“能跑”到“可长期维护”。

**必做项**：
- governance gate 正式化
- profile 分层（ci_light/full/strict）
- golden samples
- 架构守卫

**退出标准**：
- 门禁体系稳定运行且可持续回归。

### 阶段 6：切换准备与灰度切换

**目标**：满足准入标准后小步接管旧模块。

**必做项**：
- 切换准入标准冻结
- 按入口族灰度，不按文件灰度
- 双轨对比观测期
- 回滚路径演练

**切换准入标准**：
1. 入口覆盖
2. 契约冻结
3. 门禁通过
4. 失败路径可观测
5. 回滚可行

**退出标准**：
- 具备可控切换能力，不依赖人工兜底。

## 执行节拍（每轮固定）

1. 声明本轮层级目标
2. 声明本轮不做项
3. 最小实现
4. verify/snapshot/docs 收尾
5. 更新阶段进度与下一轮衔接点

## 当前定位

- `1606-1617` 治理成果定位为“阶段 0 治理底座资产”。
- `1618-1619` 实质意图迁移定位为“阶段 1~2 过渡启动”。
- 下一目标：以阶段化主链推进 `session.bootstrap` 等核心入口，不回到局部点修节奏。

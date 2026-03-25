# 施工企业管理系统产品化迭代方向总纲 v1

## 一、文档定位

本文件用于定义系统从“已完成平台与功能能力”向“可交付产品”的迭代方向。

本文件不描述具体实现，而用于：

- 校准迭代方向
- 限制不必要扩展
- 指导任务调度

## 二、当前系统状态

### 2.1 已完成能力

系统当前已具备：

#### 平台层

- intent 统一入口
- contract 驱动
- scene 编排机制
- read / write model 分离
- release / operator / audit / approval 完整闭环

#### 产品切片层

- `projects.intake`
- `project.plan_bootstrap`
- `project.execution`
- `cost.tracking`
- `payment`
- `settlement`
- `my_work.workspace`

#### 内部主线能力

```text
project.plan_bootstrap
→ project.execution
→ cost.tracking
→ payment
→ settlement
```

### 2.2 当前缺口

系统缺失的不是能力，而是：

```text
Product Connection Layer
```

具体表现为：

#### 1. Released scene 未形成闭环

- 依赖 `project_id` 外部传递
- 无统一 project context

#### 2. next_actions 未产品化

- 有 intent
- 无稳定语义 `guidance / transition`

#### 3. dashboard 未成为驾驶舱

- 有聚合
- 无稳定决策与引导 contract

#### 4. 用户路径仍存在连接层断点

- 仍依赖菜单和入口页跳转
- 还不是系统全程引导

## 三、产品化目标

### 3.1 总目标

```text
让用户在不理解系统结构的情况下，
通过系统引导完成一个完整项目闭环
```

### 3.2 子目标

#### 1. 主线闭环

```text
立项 → 执行 → 成本 → 付款 → 结算 → 完成
```

#### 2. 场景闭环

```text
scene → next_action → scene
```

#### 3. 行为闭环

```text
action → state → next_action
```

#### 4. 体验闭环

```text
打开系统 → 知道当前 → 知道下一步 → 点击完成
```

## 四、产品架构目标

### 4.1 四层结构

#### 1. 平台层

已完成并冻结：

```text
intent / contract / scene / release / operator
```

#### 2. 场景层

已存在但仍需收口：

```text
execution / cost / payment / settlement
```

#### 3. 连接层

当前唯一重点：

```text
project context
next_actions
scene flow
dashboard
```

#### 4. 体验层

待形成：

```text
用户路径
驾驶舱
工作台
```

## 五、当前唯一方向

### Product Connection Layer

定义：

将以下四个要素收口为统一产品协议：

```text
released scene
project context
internal carrier
next_actions
```

## 六、阶段划分

### Phase 1：连接层收口

目标：

```text
让系统成为“可走通的产品”
```

必须完成：

#### 1. Project Context 统一

- 所有 released scene 统一 project context
- 消除隐式 `project_id` 传递

#### 2. next_actions 产品化

- 补齐 `action_kind`
- 全场景统一结构

#### 3. Project Dashboard

- 聚合 `execution / cost / payment / settlement`
- 稳定输出 `next_actions`

#### 4. Scene Flow 收口

```text
my_work → dashboard → next_action → 主线
```

### Phase 2：体验收口

目标：

```text
让用户“无学习成本使用”
```

范围：

- 风险提示
- 自动判断
- UI 收口
- 状态解释

### Phase 3：智能增强

目标：

```text
系统替用户决策
```

范围：

- AI 推荐
- 自动推进
- 智能分析

## 七、严格约束

### 7.1 不再扩平台

禁止：

- 新 contract 模型
- 新 release 机制
- 新 operator 扩展

### 7.2 不再新增业务模块

禁止：

- 材料
- 劳务
- 设备
- 其他外围扩展域

### 7.3 所有开发必须围绕主线 + next_action

允许：

- 聚合
- 统一
- 标准化

不允许：

- 发散式功能追加
- 与主线无关的平台再设计

## 八、成功判定标准

唯一标准：

```text
一个用户可以：
打开系统
→ 进入项目
→ 按 next_action 操作
→ 完成项目

且无需理解系统结构
```

## 九、当前阶段判断

当前阶段：

```text
Productization Phase 1
```

状态判断：

```text
平台：完成
能力：完成
产品：未完成
```

## 十、下一轮调度原则

- 只允许单一主任务
- 禁止并行多方向开发
- 所有实现必须直接服务于连接层收口

## 十一、下一轮唯一任务

```text
Project Connection Layer v1
```

## 十二、最终总结

当前系统在技术层面已经是平台级系统，但在产品层面还不是“用户可直接完成闭环的产品”。

接下来唯一正确的任务不是继续扩平台，也不是继续补新业务域，而是：

```text
把已有能力变成用户路径
```

也就是：

```text
把 released scene、project context、internal carrier、next_actions
收成一个正式的 Product Connection Layer
```

# 项目方向锚定文

Project Direction Anchor

> **定位说明**
> 本文档用于锚定项目的长期方向、工程判断与取舍原则。
> 它不是阶段总结，也不是对外宣传材料，而是项目在长期演进中的**决策基准文档**。

---

## 一、我们在做什么

## 1. What We Are Building

**中文**

我们不是在构建一个“工程项目管理功能集合”，
而是在构建一个**能够对工程项目的行为、决策与结果承担责任的系统平台**。

这个系统的目标，不是简单地“把事情放进系统里”，
而是确保每一个关键行为：

* 可解释
* 可验证
* 可追溯
* 可交付

即使在系统下线、人员更替、组织变化之后，
**系统产生的成果依然能够独立存在，并被第三方理解与认可。**

这是我们判断系统是否真正成熟的核心标准。

---

**English**

We are not building a mere collection of project management features.
We are building a **system platform that can take responsibility for project behaviors, decisions, and outcomes**.

The goal of this system is not simply to “store things inside the system,”
but to ensure that every critical action is:

* Explainable
* Verifiable
* Traceable
* Deliverable

Even if the system is offline, personnel change, or organizations evolve,
**the outcomes produced by the system must remain independently understandable and acceptable to third parties.**

This is our core criterion for system maturity.

---

## 二、不可动摇的核心判断

## 2. Non-Negotiable Core Principles

### 2.1 系统必须“知道自己在做什么”

### 2.1 The System Must Understand Its Own Actions

**中文**

系统中的行为不是偶然发生的：

* 每一次操作都有明确的 **意图（Intent）**
* 每一个页面都是一个 **场景（Scene）**
* 每一个可执行动作都是 **系统建议（Suggested Action）**
* 每一个结果都有明确的 **原因代码（Reason Code）**

系统行为必须是**语义化的、一等公民的**，
而不是隐含在代码分支或 UI 交互里的偶然结果。

---

**English**

Actions in the system must never be accidental:

* Every operation has a clear **Intent**
* Every page represents a **Scene**
* Every executable action is a **Suggested Action**
* Every outcome carries an explicit **Reason Code**

System behavior must be **semantic and first-class**,
not an implicit side effect hidden in code branches or UI interactions.

---

### 2.2 可运行 ≠ 可信

### 2.2 Runnable Does Not Mean Trustworthy

**中文**

一个系统可以“跑得起来”，但依然是不可靠的。

我们坚持：

* 行为必须有 **契约（Contract）**
* 结果必须有 **证据（Evidence）**
* 异常必须有 **解释（Reason Code）**
* 全链路必须有 **验证（Verify / Gate）**

任何**无法被验证的能力**，都不是资产，而是潜在风险。

---

**English**

A system may run successfully and still be untrustworthy.

We insist that:

* Every behavior is governed by a **Contract**
* Every outcome produces **Evidence**
* Every exception is **Explained via Reason Codes**
* The entire flow is protected by **Verification and Gates**

Any capability that cannot be verified is not an asset—it is a latent risk.

---

### 2.3 前后端分离是责任分工，而非技术偏好

### 2.3 Frontend–Backend Separation Is About Responsibility, Not Technology

**中文**

我们明确边界：

* **后端**

  * 定义能力、规则、约束、权限、状态推进
  * 是系统的事实来源与裁决者
* **前端**

  * 负责结构化呈现与交互
  * 不推理规则，不猜测权限

系统的正确性必须在后端成立，
而不是在 UI 上“看起来正确”。

---

**English**

We draw a clear line of responsibility:

* **Backend**

  * Defines capabilities, rules, constraints, permissions, and state transitions
  * Serves as the source of truth and final authority
* **Frontend**

  * Handles structured presentation and interaction
  * Does not infer rules or guess permissions

System correctness must be established in the backend,
not merely appear correct in the UI.

---

### 2.4 文档是系统的一部分，而不是附属物

### 2.4 Documentation Is Part of the System

**中文**

文档不是“事后补写的说明”，而是：

* 系统能力的对外表达
* 系统边界的自我约束
* 系统演进的长期记忆

我们坚持：

* 文档必须与系统能力对齐
* 文档必须可验证、可追溯
* 文档结构本身必须可治理

一个无法用文档清晰解释的系统，本质上是不完整的。

---

**English**

Documentation is not an after-the-fact explanation. It is:

* The external expression of system capabilities
* A self-imposed boundary of system responsibility
* The long-term memory of system evolution

We insist that documentation:

* Aligns with actual system capabilities
* Is verifiable and traceable
* Has a governable structure

A system that cannot be clearly explained through documentation is fundamentally incomplete.

---

## 三、我们明确拒绝的事情

## 3. What We Explicitly Refuse

**中文**

为了长期可持续性，我们明确拒绝：

* 为了短期演示牺牲系统结构
* 为了“尽快上线”绕过验证链路
* 在权限、规则、状态上留下默认允许的后门
* 让临时结论（TEMP）混入正式交付路径
* 让系统行为依赖某个人的隐性知识

我们宁愿慢，也不接受不可解释的快。

---

**English**

For long-term sustainability, we explicitly refuse to:

* Sacrifice structure for short-term demos
* Bypass verification chains to “go live faster”
* Leave default-allow backdoors in permissions or rules
* Mix temporary conclusions into formal delivery paths
* Depend on individual tribal knowledge for system behavior

We choose to move slowly rather than move fast without explanation.

---

## 四、持续自检的四个问题

## 4. The Four Self-Check Questions

**中文**

任何阶段、任何能力，都必须回答以下问题：

1. 这个能力是否有清晰的语义定位？
2. 第三方是否可以在不读代码的情况下理解它？
3. 如果系统此刻冻结，结果是否可以直接交付？
4. 错误使用是否能被 Gate 拦截？

只要有一个问题回答不上来，系统就还没准备好进入下一阶段。

---

**English**

At any stage, every capability must answer these questions:

1. Does it have a clear semantic identity?
2. Can a third party understand it without reading code?
3. If the system freezes now, can the result be delivered?
4. Can misuse be stopped by gates?

If any answer is “no,” the system is not ready to advance.

---

## 五、长期目标

## 5. Long-Term Objective

**中文**

我们的目标不是覆盖所有功能，
而是成为一个能够在复杂组织中运行复杂工程项目的系统平台：

* 行为可解释
* 责任可追溯
* 结果可交付
* 风险不隐性累积

系统本身承担起**组织记忆与责任边界**的角色。

---

**English**

Our goal is not feature completeness.
Our goal is to become a system platform capable of running complex engineering projects within complex organizations:

* Explainable behavior
* Traceable responsibility
* Deliverable outcomes
* No silent accumulation of risk

The system itself becomes the organization’s memory and responsibility boundary.

---

## 六、给未来自己的提醒

## 6. A Note to Our Future Selves

**中文**

如果有一天你觉得这个项目进展太慢，
请回到这里再读一遍。

你放慢脚步的地方，
正是大多数系统永远无法抵达的地方。

---

**English**

If one day this project feels slow,
return and read this document again.

Where you slowed down
is exactly where most systems never arrive.

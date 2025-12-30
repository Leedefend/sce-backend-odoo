# Smart Construction Demo Data

本模块提供 **Smart Construction Core** 的官方演示数据（Demo Dataset），用于：

- 快速搭建可演示的业务场景
- 验证核心模块的安装 / 升级幂等性
- 为协作者、测试人员、CI 提供稳定的演示与回归基线

> ⚠️ 说明  
> - 本模块 **只包含演示数据**，不包含任何业务逻辑  
> - 所有业务规则、权限、流程均定义在 `smart_construction_core`  
> - Demo 数据必须 **可重复 install / upgrade 而不报错**

---

## Quick Start

重建演示库（推荐）：
```bash
make demo.rebuild DB_NAME=sc_demo
```

列出可用场景：
```bash
make demo.list DB_NAME=sc_demo
```

加载单个场景：
```bash
make demo.load SCENARIO=s10_contract_payment DB_NAME=sc_demo
```

加载全部场景：
```bash
make demo.load.all DB_NAME=sc_demo
```

验收断言：
```bash
make demo.verify DB_NAME=sc_demo
```

---

## 模块结构说明

Demo 数据按 **Base / Scenario** 两层结构组织：

```
data/
├─ base/                       # 基础演示数据（可复用）
│  ├─ 00_dictionary.xml        # 数据字典
│  ├─ 10_partners.xml          # 业主 / 供应商
│  └─ 20_projects.xml          # 项目基础信息
└─ scenario/
   └─ s00_min_path/            # S00：最小可运行演示路径
      ├─ 10_project_boq.xml
      ├─ 20_project_links.xml
      └─ 30_project_revenue.xml
```

- **base/**：不依赖具体业务流程，多个场景可复用
- **scenario/s00_min_path/**：官方最小闭环演示场景（10 分钟）

---

## 安装与升级（统一使用 Makefile 命令）

> ⚠️ 请勿使用裸 `odoo` / `docker compose` 命令

### 首次安装 Demo（新库）
```bash
make mod.install MODULE=smart_construction_demo DB_NAME=sc_demo
```

### 升级 Demo（验证幂等性）

```bash
make mod.upgrade MODULE=smart_construction_demo DB_NAME=sc_demo
```

---

## S00 最小演示路径（10 分钟）

### 1️⃣ 项目（Project）

- **xmlid**：`smart_construction_demo.sc_demo_project_001`
- **预期**：
  - 项目可正常打开
  - 可看到基础信息与关联页签

---

### 2️⃣ 工程量清单 BOQ

- **xmlid**：
  - `sc_demo_boq_earthwork`
  - `sc_demo_boq_concrete`
- **预期**：
  - BOQ 树结构存在
  - 至少包含 2 个清单节点

---

### 3️⃣ 材料计划（Material Plan）

- **xmlid**：`sc_demo_material_plan_001`
- **预期**：
  - 材料计划记录存在
  - 至少包含 1 条计划行

---

### 4️⃣ 收入 / 发票（Revenue / Invoice）

- **xmlid**：
  - `sc_demo_invoice_progress`
  - `sc_demo_invoice_progress_2`
- **行为说明**：
  - Demo 安装阶段仅对 `draft` 状态的发票执行过账
  - 已过账的发票在 install / upgrade 时会被自动跳过
- **预期**：
  - install / upgrade 可重复执行
  - 不出现 “must be in draft” 错误

---

### 5️⃣ 会计基础数据

- **科目**：`sc_demo_account_revenue`
- **销售日记账**：`sc_demo_journal_sale`
- **预期**：
  - 收入发票可正常关联科目与日记账

---

## S10 合同付款演示路径（最小闭环）

场景目录：`data/scenario/s10_contract_payment/`

- 合同：`sc_demo_contract_out_010`（model: `construction.contract`，type=out）
- 付款申请：`sc_demo_pay_req_010_001`（model: `payment.request`，保持 draft；type=receive 与合同类型约束一致）
- 发票：`sc_demo_invoice_s10_001`、`sc_demo_invoice_s10_002`（默认 draft）

> 说明：S10 目前不默认写入 `__manifest__.py`，以保持 S00 为默认稳定演示路径；需要时可临时加入 manifest 进行加载验证。

验收命令：
```bash
make demo.verify DB_NAME=sc_demo
```

---

## S20 结算/核销演示路径（最小闭环）

场景目录：`data/scenario/s20_settlement_clearing/`

- 收款记录：`sc_demo_payment_020_001`（model: `payment.request`，type=receive）
- 结算单：`sc_demo_settlement_020_001`（model: `sc.settlement.order`）
- 结算明细：`sc_demo_settle_line_020_001`、`sc_demo_settle_line_020_002`

> 说明：S20 依赖 S10（合同/发票/付款申请），建议使用 `make demo.load.all` 加载。

验收命令：
```bash
make demo.verify DB_NAME=sc_demo
```

---

## S30 结算工作流演示路径（可推进但不自动推进）

场景目录：`data/scenario/s30_settlement_workflow/`

- 结算单：`sc_demo_settlement_030_001`（model: `sc.settlement.order`，保持 draft）
- 结算明细：`sc_demo_settlement_line_030_001`
- 收款关联：`sc_demo_pay_req_030_001`（model: `payment.request`，type=receive）
- 门禁样例：`sc_demo_settlement_030_bad_001`（无明细/无收款，必须保持 draft）

验收命令：
```bash
make demo.verify DB_NAME=sc_demo
```

---

## S40 失败路径 / 边界场景

场景目录：`data/scenario/s40_failure_paths/`

- 结构性违规：`sc_demo_settlement_040_structural_bad`（无明细、无收款关联）
- 金额违规：`sc_demo_settlement_040_amount_bad`（收款金额 > 结算金额）
- 关联违规：`sc_demo_settlement_040_link_bad`（有明细但无收款关联）

说明：
- S40 数据可以正常加载，但不应推进状态。
- demo.verify 会对 S40 的失败条件做强校验。

---

## Scenario Index

| 场景 | 目标 | 关键模型 | 可验证点 |
| --- | --- | --- | --- |
| S00 | 最短路径（项目/BOQ/材料/发票） | project.project / project.boq.line / project.material.plan / account.move | projects/boq/material/invoices |
| S10 | 合同 + 付款申请 + 发票（draft） | construction.contract / payment.request / account.move | contract/payment_request/invoices |
| S20 | 结算单 + 明细 + 收款关联 | sc.settlement.order / sc.settlement.order.line / payment.request | settlement/lines/payment_request.link |
| S30 | 工作流种子 + 门禁（bad） | sc.settlement.order / sc.settlement.order.line / payment.request | draft + gate |
| S40 | 失败路径（结构/金额/关联） | sc.settlement.order / sc.settlement.order.line / payment.request | fail conditions locked |

---

## Acceptance Matrix

- S00: 项目数量、BOQ 节点、材料计划、发票数量
- S10: 合同记录、付款申请、发票记录
- S20: 结算单、结算明细、收款关联
- S30: 结算单 draft、明细/收款关联、门禁样例 draft
- S40: 结构/金额/关联违规均保持 draft，且失败条件可验证

---

## 验收断言（Acceptance Checklist）

在数据库 `sc_demo` 中，应满足：

- 项目数量 ≥ 2
- BOQ 节点数量 ≥ 2
- 材料计划数量 ≥ 1
- 发票数量 ≥ 2
- 以下命令可重复执行且不报错：

  ```bash
  make mod.install MODULE=smart_construction_demo DB_NAME=sc_demo
  make mod.upgrade MODULE=smart_construction_demo DB_NAME=sc_demo
  ```

---

## 自动验收（demo.verify）

为便于回归测试与 CI 校验，提供自动化 Demo 验收命令：

```bash
make demo.verify DB_NAME=sc_demo
```

该命令将基于 PostgreSQL 只读检查以下断言：

- 项目数量 ≥ 2
- BOQ 节点数量 ≥ 2
- 材料计划数量 ≥ 1
- 发票数量 ≥ 2

任一断言失败将直接返回非 0 退出码，适用于本地验证与 CI 集成。

---

## 加载可选场景（Scenario Loader）

S10 等可选场景默认不写入 manifest，可使用命令按需加载：

```bash
make demo.load SCENARIO=s10_contract_payment DB_NAME=sc_demo
make demo.verify DB_NAME=sc_demo
```

列出可用场景：
```bash
make demo.list DB_NAME=sc_demo
```

加载全部场景：

```bash
make demo.load.all DB_NAME=sc_demo
```

一键重建演示库（清库 → 安装 → 全量加载 → 验收）：
```bash
make demo.rebuild DB_NAME=sc_demo
```

---

## 常见问题（Troubleshooting）

### ❌ 报错：`The entry XXX must be in draft`

- 原因：发票在 Demo 安装阶段被重复过账
- 检查：
  - `30_project_revenue.xml` 中的过账逻辑
  - 是否只对 `draft` 状态执行 `action_post`

---

### ❌ 报错：`External ID not found`

- 检查：
  - `__manifest__.py` 中 `data` 加载顺序
  - XML 中 `ref="..."` 是否指向已定义的 xmlid

---

## 操作排障小贴士

- 第一次安装/升级耗时较长，注意等待容器初始化完成。
- 若出现外键相关报错，优先检查场景文件顺序与 loader 的注册顺序。
- 付款/结算类型不匹配（in/out vs receive/pay）会触发一致性校验。
- docutils 警告不影响安装/升级，可后续再清理。
- demo.verify 失败时，可用相同 SQL 在 psql 中复查并定位具体记录。
- 若只想验证单个场景，可先 `make demo.load SCENARIO=...` 后再 `make demo.verify`。

---

## 设计原则说明

- Demo 数据 **必须幂等**
- Demo 不应反向推动 core 模型设计
- 所有状态型业务动作（如过账）必须：
  - 可跳过
  - 可重复执行
  - 不依赖人工环境


# **README.md**

```markdown
# 智能工程项目管理系统（Smart Construction Platform）

> 基于 **Odoo 17 + Vue 3** 打造的新一代智能化建筑工程项目管理解决方案  
> 采用 **结构驱动（Structure-Driven）+ 意图解释（Intent Interpreter）+ 契约式接口（Contract 2.0）** 架构体系，实现完全可配置、可扩展、可智能化的工程项目管理能力。

[![License](https://img.shields.io/badge/License-LGPL--3.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Vue](https://img.shields.io/badge/Vue-3.0%2B-green.svg)](https://vuejs.org)
[![Odoo](https://img.shields.io/badge/Odoo-17.0-purple.svg)](https://odoo.com)

---

## 📖 项目简介

智能工程项目管理系统是一套面向施工企业、业主单位、代建单位以及工程咨询公司的现代化项目管理平台。系统基于 **Odoo 17 后端 + Vue 3 前端**构建，通过 **Contract 2.0 契约驱动架构**实现前后端完全解耦，支持动态 UI 渲染、视图语义解析、业务意图执行、模型元数据驱动等能力。

系统核心目标包括：

- 让前端自动渲染所有 Odoo 页面（表单 / 列表 / 看板）
- 让后端以 Contract（契约）统一描述所有业务行为
- 让复杂工程场景（BOQ、多层级成本、施工管理等）具备高扩展性
- 为企业打造具备产品化能力、可推广的“平台级工程管理系统”

---

## 开发环境

本项目采用 DevContainer + Docker Compose 作为统一开发环境。

请在开始开发前，先阅读并完成以下文档中的环境验收清单：

👉 `docs/dev-env.md`

## Quick Start (Dev)

```bash
docker compose up -d
```

* Reverse proxy: http://localhost:18080/web
* Direct Odoo: http://localhost:8069/web

Demo bootstrap:

```bash
make demo.full DB=sc_demo
```

`docs/ops/dev_bootstrap.md`
`docs/ops/prod_command_policy.md`
`docs/ops/release_notes_v0.3.0-stable.md`
`docs/ops/release_checklist_v0.3.0-stable.md`


补充约束：所有 Makefile 中调用 Odoo 的 target 必须经由 `$(ODOO_EXEC)`，任何直接调用 `odoo` 的行为一律视为缺陷。

---

## 🏗️ 核心特性

### 🔹 1. 契约驱动架构（Contract 2.0）
所有页面行为由 Contract 决定：
- 字段、只读规则、默认值
- 按钮行为与 server action
- 视图布局结构（form/tree/kanban）
- 权限与上下文控制
- API 统一入口：`/api/contract/get` + `/api/intent/execute`

前端不再写页面，只需解析 Contract。

---

### 🔹 2. 结构驱动动态渲染引擎（前端 Vue 3）
支持：
- 表单视图（Form）
- 列表视图（Tree）
- 看板视图（Kanban）
- Ribbon / Button Box
- 动态字段解析
- 动态布局（notebook/page/group/col）
- 动态权限（invisible、readonly、attrs）

全部自动渲染，无需手写界面。

---

### 🔹 3. 工程量清单（BOQ）智能解析引擎
支持国内工程招标 / 合同常用格式：

- 分部分项工程量清单（F1）
- 单价措施项目清单（F2）
- 总价措施项目清单（F3）
- 规费
- 税金
- 其他项目清单（含层级）
- 合计/小计过滤（多行表头、合并单元格均支持）
- Excel 多 Sheet 自动识别类型

功能包括：

- 表头解析（含多行/合并单元格）
- 子目明细识别
- 费用项树形结构构建
- 自动金额合计
- 工程类别识别（建筑/安装/装饰/景观）
- 自动构建父子关系 parent_id
- 自动生成 WBS 工程结构

当前已支持复杂商务招标清单的完整处理逻辑。

---

### 🔹 4. 完整项目管理能力
包括：

- 项目主数据
- 项目阶段控制
- 工程结构与 WBS
- BOQ 清单管理
- 材料计划、采购扩展
- 成本中心与预算
- 合同与变更管理
- 结算管理（Settlement）
- 施工过程管控（任务 / 进度）

---

### 🔹 5. 高性能缓存机制（ETag）
Contract 响应自动加 ETag，提升前端加载性能约 50%~90%。

---

### 🔹 6. 模块化设计与强扩展性
所有业务模块完全独立，可按需组合：

- smart_core（核心引擎）
- smart_construction_core（工程业务）
- smart_contract（契约系统）
- project_extend（扩展模块）
- frontend_vue（独立前端）

---

## 🏛️ 系统架构

```

┌──────────────────────────────┐
│         Vue 3 前端应用        │
│  - 动态自动渲染 AutoPage       │
│  - Contract Intent Executor   │
│  - Token 认证与缓存           │
│  - UI 组件库（Tailwind+EP）    │
└───────────────▲──────────────┘
│ REST API & Contract
┌───────────────┴────────────────┐
│              Odoo 17            │
│   ┌──────────────────────────┐  │
│   │ smart_core               │  │
│   │ - Contract Service       │  │
│   │ - Intent Dispatcher      │  │
│   │ - View Semantic Parser   │  │
│   └──────────────────────────┘  │
│   ┌──────────────────────────┐  │
│   │ smart_construction_core  │  │
│   │ - BOQ Import Engine      │  │
│   │ - WBS 生成               │  │
│   │ - 成本/合同/结算模型     │  │
│   └──────────────────────────┘  │
│ PostgreSQL 15 | Redis | Nginx   │
└────────────────────────────────┘

```

---

## 📁 项目结构

```

e:\odoo17\addons
├── frontend_vue/
│   └── vue_app/                     # 完整 Vue 3 前端框架
│
├── smart_core/                      # Contract 2.0 + Intent 等核心底座
├── smart_construction_core/         # 建筑工程业务核心模块
│   ├── models/                      # BOQ、结算、进度、合同等
│   ├── wizard/                      # BOQ 导入与清单计算
│   └── views/                       # Odoo 视图定义（供前端解析）
│
├── smart_contract/                  # 契约引擎模块
├── project_extend/                  # Odoo 项目模块扩展
│
├── docs/
│   ├── git/
│   │   └── SmartConstruction-Git-Guide.md      # ← 新增 Git 分支与发布规范 v1.0
│   ├── api-reference.md
│   ├── wiki.md
│   ├── faq.md
│   └── boq/（建议存放 BOQ 清单解析技术文档）
│
├── requirements.txt
├── project.toml
└── README.md

````

---

## 🚀 快速开始

### 1. 环境要求

- **Python**: 3.8+
- **Node.js**: 16+
- **PostgreSQL**: 12+
- **Odoo**: 17.0
- **Redis**
- **Docker（推荐）**

---

### 2. 克隆项目

```bash
git clone <repository-url>
cd addons
````

---

### 3. 安装后端依赖

```bash
pip install -r requirements.txt
```

---

### 4. 安装前端依赖

```bash
cd frontend_vue/vue_app
npm install
# 或
pnpm install
```

---

### 5. 配置 Odoo

在 odoo.conf 中加入：

```
addons_path = /path/to/addons
```

登录 Odoo 后安装 smart_core、smart_construction_core 等模块。

---

### 6. 启动服务

#### 启动 Odoo

```bash
odoo -c /path/to/odoo.conf
```

#### 启动前端

```bash
cd frontend_vue/vue_app
npm run dev
```

---

## 📚 模块说明

### 🔧 smart_core（系统核心）

* Contract 2.0
* Intent Dispatcher
* ViewParser（视图语义解析）
* ETag 缓存
* 动态请求上下文处理

---

### 📄 smart_contract（契约服务）

* Contract JSON 构建器
* 动态字段权限
* 动态按钮行为
* 服务端意图执行器

---

### 🏢 smart_construction_core（工程核心）

包含完整的建筑企业业务：

* BOQ 智能导入（分部分项 / 单价措施 / 总价措施 / 规费 / 税金 / 其他项目）
* 其他项目清单合计计算
* 工程结构（WBS）生成
* 项目管理扩展
* 成本中心模型
* 合同与结算管理
* 采购扩展

---

### 🔧 project_extend

* 项目模块补充字段
* 统一接口支持
* 扩展 Contract 输出

---

### 🎨 frontend_vue

* Vue 3 + TypeScript
* Pinia
* TailwindCSS
* 动态渲染引擎（AutoPage）
* 兼容 Odoo 行为的交互逻辑

---

## 📖 API 文档（Contract API）

| 方法   | 地址                    | 功能        |
| ---- | --------------------- | --------- |
| GET  | `/api/contract/get`   | 获取页面契约    |
| POST | `/api/intent/execute` | 执行按钮/业务动作 |
| GET  | `/api/metadata`       | 获取模型元数据   |

详情见：`docs/api-reference.md`

---

## 🧪 测试

```bash
python -m pytest tests/
```

前端：

```bash
cd frontend_vue/vue_app
npm run test
```

---

## 📝 贡献指南

1. Fork 本仓库
2. 创建功能分支
3. 编写代码与测试
4. 提交 PR
5. Merge 后删除分支

---

## 📄 许可证

项目基于 **LGPL-3.0** 协议开源。

---

## 👥 团队

* **系统架构 & 后端开发**
* **前端研发**
* **产品设计**
* **测试与交付**

---

## 🔗 相关链接

* [Odoo 官方文档](https://www.odoo.com/documentation/17.0/)
* [Vue 3 官方文档](https://vuejs.org/)
* [项目 Wiki](docs/wiki.md)
* [API 文档](docs/api-reference.md)
* [Git 分支规范](docs/git/SmartConstruction-Git-Guide.md)
* [P0 Ledger Gate 规范](docs/spec/p0_ledger_gate.md)
* [FAQ](docs/faq.md)

---

# 📌 Backend Baseline（v0.1-backend-baseline）

**版本说明：**

这是系统在结构重建后的第一个稳定后端基线，包含：

### ✔ Docker 化环境

* Odoo 17
* PostgreSQL 15
* Redis
* Nginx
* n8n 自动化

### ✔ 统一数据库：`sc_odoo`

### ✔ 模块结构重建

* 完整的 smart_core
* 完整的 smart_construction_core
* 新版 BOQ 导入引擎
* 新建 settlement、contract、project_extend 模型

### ✔ 适配前后端分离的 Contract 2.0 能力

---

```
> 任何问题请提交 Issue 或联系维护者。
```

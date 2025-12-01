# 智能工程项目管理系统

> 基于 Odoo 17 和 Vue 3 的现代化建筑工程项目管理解决方案

[![License](https://img.shields.io/badge/License-LGPL--3.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Vue](https://img.shields.io/badge/Vue-3.0%2B-green.svg)](https://vuejs.org)
[![Odoo](https://img.shields.io/badge/Odoo-17.0-purple.svg)](https://odoo.com)

## 📖 项目简介

智能工程项目管理系统是一个现代化的建筑工程项目管理平台，采用契约驱动架构设计，实现前后端完全解耦。系统支持项目管理、施工流程控制、材料计划管理、合同管理等核心业务功能。

### 🏗️ 核心特性

- **契约驱动架构** - 基于Contract 2.0规范的统一接口设计
- **前后端分离** - Vue 3 + TypeScript前端 + Odoo 17后端
- **动态渲染引擎** - 支持表单、看板、树形等多种视图的动态渲染
- **智能缓存机制** - ETag缓存优化，提升系统性能
- **模块化设计** - 高度模块化，支持灵活扩展

## 🏛️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐
│   前端应用      │    │   后端服务      │
│   Vue 3        │◄──►│   Odoo 17      │
│   TypeScript   │    │   Python       │
│   Vite         │    │   PostgreSQL   │
└─────────────────┘    └─────────────────┘
```

### 📁 项目结构

```
e:\odoo17\addons\
├── frontend_vue/           # Vue 3 前端应用
│   └── vue_app/           # 前端项目根目录
├── smart_core/            # 系统核心引擎
├── smart_contract/        # 契约服务模块
├── smart_construction_enterprise/  # 建筑企业业务模块
├── project_extend/        # 项目扩展模块
├── requirements.txt       # 后端依赖
├── project.toml          # 项目配置
└── README.md             # 项目说明
```

## 🚀 快速开始

### 环境要求

- **Python**: 3.8+
- **Node.js**: 16+
- **PostgreSQL**: 12+
- **Odoo**: 17.0

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd addons
   ```

2. **安装后端依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **安装前端依赖**
   ```bash
   cd frontend_vue/vue_app
   npm install
   # 或使用 pnpm
   pnpm install
   ```

4. **配置Odoo**
   ```bash
   # 将addons目录添加到Odoo配置文件的addons_path中
   # 在Odoo管理界面安装相关模块
   ```

5. **启动服务**
   ```bash
   # 启动Odoo服务
   odoo -c /path/to/odoo.conf
   
   # 启动前端开发服务器
   cd frontend_vue/vue_app
   npm run dev
   ```

## 📚 模块说明

### 🎯 smart_core (核心引擎)
- 契约驱动API核心
- 意图路由调度机制
- 视图渲染引擎
- 基础服务组件

### 📄 smart_contract (契约服务)
- Contract 2.0规范实现
- ETag缓存机制
- 意图执行服务

### 🏢 smart_construction_enterprise (建筑企业)
- 施工流程管理
- 材料计划管理
- 预算成本控制
- 设备调度管理

### 🔧 project_extend (项目扩展)
- 项目模型扩展
- API接口集成
- 认证服务
- 基础工具类

### 🎨 frontend_vue (前端应用)
- Vue 3 + TypeScript
- Pinia状态管理
- Element Plus UI组件
- 动态渲染组件

## 🛠️ 开发指南

### 代码规范

- **Python**: 遵循PEP 8规范
- **JavaScript/TypeScript**: 使用ESLint + Prettier
- **文件命名**: 使用snake_case
- **类命名**: 使用PascalCase
- **函数/变量**: 使用snake_case

### 开发流程

1. 创建功能分支
2. 编写代码和测试
3. 运行测试确保通过
4. 提交代码审查
5. 合并到主分支

## 📖 API文档

系统提供统一的契约接口：

- **GET** `/api/contract/get` - 获取页面契约
- **POST** `/api/intent/execute` - 执行业务意图
- **GET** `/api/metadata` - 获取元数据信息

详细API文档请参考 [API Reference](docs/api-reference.md)

## 🧪 测试

```bash
# 运行后端测试
python -m pytest tests/

# 运行前端测试
cd frontend_vue/vue_app
npm run test
```

## 📝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

该项目基于 [LGPL-3.0](LICENSE) 许可证开源。

## 👥 团队

- **开发团队** - 系统设计与开发
- **产品团队** - 需求分析与规划
- **测试团队** - 质量保证

## 🔗 相关链接

- [Odoo官方文档](https://www.odoo.com/documentation/17.0/)
- [Vue 3官方文档](https://vuejs.org/)
- [项目Wiki](docs/wiki.md)
- [更新日志](CHANGELOG.md)

---

> 💡 如有问题，请查看 [FAQ](docs/faq.md) 或提交 [Issue](issues)
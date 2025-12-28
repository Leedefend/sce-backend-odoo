## 外部依赖（Git Submodule / 离线包）

### 背景
smart_construction_core 依赖 OCA 模块 base_tier_validation，位于：
addons_external/oca_server_ux/base_tier_validation

若部署环境缺失该子模块，安装会报：
`You try to install module 'smart_construction_core' that depends on module 'base_tier_validation'.`

### 部署前检查（必须）
在部署目录执行：

1) 检查 submodule 定义
```bash
test -f .gitmodules && cat .gitmodules || echo "NO .gitmodules"
```

2) 检查关键依赖目录是否存在
```bash
test -d addons_external/oca_server_ux/base_tier_validation \
  && echo "OK: base_tier_validation present" \
  || echo "MISSING: base_tier_validation"
```

### 方案 1：在线部署（推荐）
```bash
git submodule sync --recursive
git submodule update --init --recursive
```

### 方案 2：离线部署（无外网/慢网）
要求离线包必须包含：
addons_external/oca_server_ux（至少包含 base_tier_validation）

解压后再次执行检查：
```bash
test -d addons_external/oca_server_ux/base_tier_validation && echo OK
```

### 验收标准
* 目录 addons_external/oca_server_ux/base_tier_validation 存在
* Odoo 安装 smart_construction_core 不再报缺依赖

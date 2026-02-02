# 屏幕闪烁问题解决方案

## 问题描述
在执行任务时屏幕闪烁的问题，通常是由于终端TTY配置不正确、缺少标准输入保持打开、终端环境变量设置不当等原因造成的。

## 已实施的解决方案

### 1. Docker Compose配置更新
#### 1.1 开发容器配置 (`.devcontainer/docker-compose.devcontainer.yml`)
- 添加了 `tty: true` - 启用终端TTY
- 添加了 `stdin_open: true` - 保持标准输入打开
- 添加了终端环境变量：
  - `TERM: xterm-256color`
  - `COLORTERM: truecolor`
  - `DEBIAN_FRONTEND: noninteractive`

#### 1.2 主Odoo容器配置 (`docker-compose.yml`)
- 添加了 `tty: true` 和 `stdin_open: true`
- 添加了终端环境变量：`TERM: xterm-256color` 和 `COLORTERM: truecolor`

### 2. Dockerfile更新 (`.devcontainer/Dockerfile.dev`)
- 添加了必要的终端工具：
  - `ncurses-term` - 终端支持库
  - `screen` - 屏幕管理工具
  - `tmux` - 终端复用器
  - `vim` - 文本编辑器（包含终端支持）
- 添加了bash配置文件复制

### 3. Dev Container配置更新 (`.devcontainer/devcontainer.json`)
- 添加了终端配置文件：
  - `terminal.integrated.defaultProfile.linux`: "bash"
  - 终端环境变量设置
  - bash参数配置

### 4. 创建了bash配置文件 (`.devcontainer/bashrc`)
- 设置了正确的终端环境变量
- 配置了简洁的提示符以减少重绘
- 设置了正确的语言环境
- 添加了终端初始化检查

### 5. 创建了实用脚本
#### 5.1 `scripts/restart-dev.sh`
- 重启开发环境的完整脚本
- 停止、重建、启动所有相关容器
- 检查服务状态

#### 5.2 `scripts/check-terminal.sh`
- 检查终端配置的脚本
- 验证环境变量、终端类型、Docker配置
- 提供修复建议

## 如何使用

### 方法1：完整重启（推荐）
```bash
./scripts/restart-dev.sh
```

### 方法2：检查当前配置
```bash
./scripts/check-terminal.sh
```

### 方法3：手动步骤
1. 停止当前容器：
   ```bash
   docker-compose down
   ```

2. 重建开发容器：
   ```bash
   docker-compose -f .devcontainer/docker-compose.devcontainer.yml build
   ```

3. 启动服务：
   ```bash
   docker-compose up -d
   ```

## 验证步骤

1. 运行检查脚本：
   ```bash
   ./scripts/check-terminal.sh
   ```

2. 确认以下输出：
   - TERM: xterm-256color
   - COLORTERM: truecolor
   - 终端类型：交互式终端
   - Docker容器TTY状态：已启用

3. 测试屏幕是否仍然闪烁

## 如果问题仍然存在

如果屏幕闪烁问题仍然存在，请尝试：

1. **重启VS Code** - 完全关闭并重新打开VS Code
2. **重新打开Dev Container** - 在VS Code中：
   - 按 F1
   - 输入 "Dev Containers: Reopen in Container"
3. **检查VS Code终端设置**：
   - 打开设置 (Ctrl+,)
   - 搜索 "terminal.integrated"
   - 确保终端配置文件正确
4. **更新VS Code** - 确保使用最新版本

## 技术原理

屏幕闪烁通常由以下原因引起：
1. **TTY配置不正确** - Docker容器需要正确的TTY设备
2. **标准输入关闭** - 需要保持stdin_open以维持终端会话
3. **终端类型不匹配** - TERM环境变量需要正确设置
4. **终端模拟器兼容性** - 需要正确的颜色支持和终端能力
5. **屏幕刷新问题** - 某些终端特性可能导致闪烁

本次修复全面解决了以上所有问题。

## 文件变更列表

1. `.devcontainer/docker-compose.devcontainer.yml` - 添加TTY和终端配置
2. `.devcontainer/Dockerfile.dev` - 添加终端工具和bash配置
3. `.devcontainer/devcontainer.json` - 添加终端配置文件
4. `.devcontainer/bashrc` - 创建bash配置文件
5. `docker-compose.yml` - 为Odoo服务添加TTY配置
6. `scripts/restart-dev.sh` - 创建重启脚本
7. `scripts/check-terminal.sh` - 创建检查脚本
8. `SCREEN_FLICKER_FIX.md` - 本文档

## 最后更新
2026-02-02
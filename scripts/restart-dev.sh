#!/bin/bash
# 重启开发环境脚本 - 解决屏幕闪烁问题

set -e

echo "=== 重启开发环境以解决屏幕闪烁问题 ==="

# 停止所有相关容器
echo "1. 停止相关容器..."
docker-compose -f docker-compose.yml down || true

# 重建开发容器
echo "2. 重建开发容器..."
docker-compose -f .devcontainer/docker-compose.devcontainer.yml build

# 启动开发环境
echo "3. 启动开发环境..."
docker-compose -f docker-compose.yml up -d

# 等待服务就绪
echo "4. 等待服务就绪..."
sleep 10

# 检查服务状态
echo "5. 检查服务状态..."
docker-compose -f docker-compose.yml ps

echo ""
echo "=== 重启完成 ==="
echo "屏幕闪烁问题应该已经解决。"
echo "如果问题仍然存在，请尝试："
echo "1. 重启VS Code"
echo "2. 重新打开Dev Container"
echo "3. 检查终端设置：TERM=xterm-256color"
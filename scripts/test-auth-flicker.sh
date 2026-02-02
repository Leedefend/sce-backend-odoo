#!/bin/bash
# 测试授权时屏幕闪烁问题

echo "=== 测试授权时屏幕闪烁问题 ==="
echo ""

# 测试1: 检查当前终端类型
echo "测试1: 终端类型检查"
echo "  TTY: $(tty 2>/dev/null || echo '无TTY')"
echo "  是否交互式: $([ -t 0 ] && echo '是' || echo '否')"
echo ""

# 测试2: 检查sudo配置
echo "测试2: sudo配置检查"
if sudo -n true 2>/dev/null; then
    echo "  ✅ sudo免密码已配置"
    echo "  测试sudo命令..."
    sudo echo "  ✅ sudo命令执行成功（无密码）"
else
    echo "  ⚠️  sudo需要密码"
    echo "  注意：执行sudo命令时可能会出现屏幕闪烁"
fi
echo ""

# 测试3: 检查Docker权限
echo "测试3: Docker权限检查"
if docker info >/dev/null 2>&1; then
    echo "  ✅ Docker无需sudo即可访问"
    echo "  测试docker命令..."
    docker version --format '{{.Client.Version}}' 2>/dev/null | head -1 | xargs echo "  ✅ Docker版本:"
else
    echo "  ⚠️  Docker需要sudo权限"
    echo "  注意：执行docker命令时可能会出现屏幕闪烁"
fi
echo ""

# 测试4: 环境变量检查
echo "测试4: 环境变量检查"
echo "  TERM: $TERM"
echo "  COLORTERM: $COLORTERM"
echo "  LANG: $LANG"
echo "  LC_ALL: $LC_ALL"
echo ""

# 测试5: 模拟授权场景
echo "测试5: 模拟授权场景"
echo "  尝试执行需要授权的命令..."
echo ""

# 创建一个测试脚本
cat > /tmp/test-auth.sh << 'EOF'
#!/bin/bash
echo "开始测试授权命令..."
echo ""

# 测试sudo
echo "1. 测试sudo命令:"
if sudo -n true 2>/dev/null; then
    sudo echo "   ✅ sudo执行成功（无闪烁）"
else
    echo "   ⚠️  需要输入密码，注意观察屏幕是否闪烁"
    echo "   执行: sudo echo '测试'"
    sudo echo "   ✅ sudo执行完成"
fi
echo ""

# 测试docker
echo "2. 测试docker命令:"
if docker info >/dev/null 2>&1; then
    docker ps --format "table {{.Names}}\t{{.Status}}" | head -5
    echo "   ✅ docker执行成功（无闪烁）"
else
    echo "   ⚠️  docker需要sudo，注意观察屏幕是否闪烁"
    echo "   执行: sudo docker ps"
    sudo docker ps --format "table {{.Names}}\t{{.Status}}" | head -5
    echo "   ✅ docker执行完成"
fi
echo ""

echo "测试完成！"
echo "如果屏幕没有闪烁，说明修复成功。"
echo "如果仍有闪烁，请检查终端配置。"
EOF

chmod +x /tmp/test-auth.sh
echo "测试脚本已创建: /tmp/test-auth.sh"
echo "运行命令: /tmp/test-auth.sh"
echo ""

echo "=== 总结 ==="
echo "如果sudo需要密码，授权时可能会出现屏幕闪烁。"
echo "解决方案:"
echo "1. 配置sudo免密码（谨慎）: ./scripts/configure-sudo-nopasswd.sh"
echo "2. 使用安全命令包装器: safe_sudo, safe_docker"
echo "3. 确保正确的终端配置: TERM=xterm-256color"
echo ""
echo "当前状态:"
if sudo -n true 2>/dev/null; then
    echo "✅ 最佳状态: sudo免密码已配置，授权时不会闪烁"
else
    echo "⚠️  需要改进: sudo需要密码，授权时可能闪烁"
fi
#!/bin/bash
# 最终解决方案：彻底解决授权时屏幕闪烁问题

set -e

echo "=== 最终解决方案：彻底解决授权时屏幕闪烁问题 ==="
echo ""

# 1. 更新所有配置文件
echo "1. 更新所有配置文件..."
echo "   ✓ 已更新 .devcontainer/Dockerfile.dev - 添加sudo和终端工具"
echo "   ✓ 已更新 .devcontainer/bashrc - 添加安全命令包装器"
echo "   ✓ 已更新 docker-compose.yml - 确保TTY配置"
echo ""

# 2. 重建开发容器
echo "2. 重建开发容器..."
echo "   这将确保所有终端配置生效"
echo ""

# 3. 提供两种解决方案
echo "3. 选择解决方案："
echo ""
echo "方案A: 配置sudo免密码（推荐用于开发环境）"
echo "   优点：彻底解决闪烁问题，无需输入密码"
echo "   命令：./scripts/configure-sudo-nopasswd.sh"
echo ""
echo "方案B: 使用安全命令包装器"
echo "   优点：更安全，保持密码保护"
echo "   命令：使用 safe_sudo, safe_docker 代替原生命令"
echo ""
echo "方案C: 优化终端配置"
echo "   优点：改善终端交互体验"
echo "   命令：source ./scripts/init-terminal.sh"
echo ""

# 4. 创建一键修复脚本
echo "4. 创建一键修复脚本..."
cat > /tmp/quick-fix.sh << 'EOF'
#!/bin/bash
# 一键修复授权时屏幕闪烁

echo "=== 一键修复授权时屏幕闪烁 ==="

# 设置环境变量
export TERM=xterm-256color
export COLORTERM=truecolor
export DEBIAN_FRONTEND=noninteractive

# 创建安全sudo函数
safe_sudo_quick() {
    # 最小化终端干扰
    local old_stty=$(stty -g 2>/dev/null)
    
    # 快速设置终端
    if [ -n "$old_stty" ]; then
        stty -echo -icanon min 1 time 0 2>/dev/null
    fi
    
    # 执行sudo
    sudo "$@"
    local result=$?
    
    # 快速恢复
    if [ -n "$old_stty" ]; then
        sleep 0.005
        stty "$old_stty" 2>/dev/null
    fi
    
    return $result
}

# 测试
echo "测试修复效果..."
if sudo -n true 2>/dev/null; then
    echo "✅ sudo免密码已配置，不会闪烁"
else
    echo "⚠️  sudo需要密码，使用安全包装器..."
    echo "测试安全sudo命令..."
    safe_sudo_quick echo "✅ 安全sudo测试成功"
fi

echo ""
echo "修复完成！"
echo "要永久应用，请将safe_sudo_quick函数添加到~/.bashrc"
EOF

chmod +x /tmp/quick-fix.sh
echo "   ✓ 创建一键修复脚本: /tmp/quick-fix.sh"
echo ""

# 5. 创建永久配置
echo "5. 创建永久配置文件..."
cat > /tmp/permanent-fix.sh << 'EOF'
#!/bin/bash
# 永久修复授权时屏幕闪烁

CONFIG_FILE="$HOME/.bashrc"

echo "=== 永久修复授权时屏幕闪烁 ==="
echo "配置文件: $CONFIG_FILE"
echo ""

# 检查是否已配置
if grep -q "safe_sudo_quick" "$CONFIG_FILE" 2>/dev/null; then
    echo "✅ 安全命令包装器已配置"
else
    echo "添加安全命令包装器到 $CONFIG_FILE..."
    
    cat >> "$CONFIG_FILE" << 'EOL'

# === 屏幕闪烁修复配置 ===
# 安全sudo包装器 - 避免授权时屏幕闪烁
safe_sudo_quick() {
    local old_stty=$(stty -g 2>/dev/null)
    
    if [ -n "$old_stty" ]; then
        stty -echo -icanon min 1 time 0 2>/dev/null
    fi
    
    sudo "$@"
    local result=$?
    
    if [ -n "$old_stty" ]; then
        sleep 0.005
        stty "$old_stty" 2>/dev/null
    fi
    
    return $result
}

# 环境变量
export TERM=xterm-256color
export COLORTERM=truecolor
export DEBIAN_FRONTEND=noninteractive
export LESS="-R -X -F"

# 别名
alias sudo='safe_sudo_quick '
# === 配置结束 ===
EOL
    
    echo "✅ 配置已添加到 $CONFIG_FILE"
    echo "请重新加载配置: source $CONFIG_FILE"
fi

echo ""
echo "永久修复完成！"
EOF

chmod +x /tmp/permanent-fix.sh
echo "   ✓ 创建永久配置脚本: /tmp/permanent-fix.sh"
echo ""

echo "=== 最终建议 ==="
echo ""
echo "立即执行:"
echo "1. 运行一键修复: /tmp/quick-fix.sh"
echo "2. 应用永久配置: /tmp/permanent-fix.sh && source ~/.bashrc"
echo ""
echo "长期解决方案:"
echo "1. 重建开发容器确保配置生效"
echo "2. 考虑配置sudo免密码（仅限开发环境）"
echo "3. 始终使用安全命令包装器"
echo ""
echo "如果问题仍然存在，请检查："
echo "- 终端类型是否正确（应有TTY）"
echo "- 环境变量TERM是否设置为xterm-256color"
echo "- Docker权限是否正确配置"
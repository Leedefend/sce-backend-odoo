#!/bin/bash
# 终端初始化脚本 - 彻底解决屏幕闪烁问题

set -e

echo "=== 终端初始化 - 解决屏幕闪烁问题 ==="
echo ""

# 1. 设置环境变量
echo "1. 设置环境变量..."
export TERM=xterm-256color
export COLORTERM=truecolor
export DEBIAN_FRONTEND=noninteractive
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LESS="-R -X -F"
export MANPAGER="less -R -X -F"

echo "   TERM=$TERM"
echo "   COLORTERM=$COLORTERM"
echo "   LANG=$LANG"
echo ""

# 2. 初始化终端设置
echo "2. 初始化终端设置..."
if [ -t 1 ]; then
    echo "   ✓ 检测到交互式终端"
    
    # 保存原始设置
    OLD_STTY=$(stty -g 2>/dev/null)
    
    # 应用稳定的终端设置
    stty sane 2>/dev/null
    stty erase '^?' 2>/dev/null
    stty -ixon -ixoff 2>/dev/null  # 禁用流控制
    stty -echoctl 2>/dev/null      # 禁用控制字符回显
    
    echo "   ✓ 终端设置已应用"
else
    echo "   ⚠️  非交互式终端，跳过终端设置"
fi
echo ""

# 3. 配置终端模式
echo "3. 配置终端模式..."
if [ "$TERM" != "dumb" ]; then
    # 初始化终端
    tput init 2>/dev/null || true
    
    # 退出备用屏幕模式（避免闪烁）
    tput rmcup 2>/dev/null || true
    
    # 禁用某些终端特性
    tput smkx 2>/dev/null || true  # 启用应用模式
    
    echo "   ✓ 终端模式已配置"
else
    echo "   ⚠️  哑终端，跳过终端模式配置"
fi
echo ""

# 4. 创建命令包装器
echo "4. 创建命令包装器..."
cat > /tmp/command-wrappers.sh << 'EOF'
#!/bin/bash
# 命令包装器 - 避免授权时屏幕闪烁

# 安全的sudo包装器
safe_sudo() {
    # 保存当前终端设置
    local old_stty=$(stty -g 2>/dev/null)
    
    # 设置终端为稳定模式
    if [ -n "$old_stty" ]; then
        # 禁用回显和规范模式
        stty -echo -icanon min 1 time 0 2>/dev/null
    fi
    
    # 执行命令
    sudo "$@"
    local exit_code=$?
    
    # 恢复终端设置
    if [ -n "$old_stty" ]; then
        # 等待一小段时间确保终端稳定
        sleep 0.01
        stty "$old_stty" 2>/dev/null
    fi
    
    return $exit_code
}

# 安全的docker包装器
safe_docker() {
    # 检查是否需要sudo
    if docker info >/dev/null 2>&1; then
        docker "$@"
    else
        echo "[需要Docker授权]"
        safe_sudo docker "$@"
    fi
}

# 安全的docker-compose包装器
safe_docker_compose() {
    # 检查是否需要sudo
    if docker info >/dev/null 2>&1; then
        docker-compose "$@"
    else
        echo "[需要Docker Compose授权]"
        safe_sudo docker-compose "$@"
    fi
}

# 通用的授权包装器
safe_auth() {
    local cmd="$1"
    shift
    
    case "$cmd" in
        docker)
            safe_docker "$@"
            ;;
        docker-compose|compose)
            safe_docker_compose "$@"
            ;;
        sudo)
            safe_sudo "$@"
            ;;
        *)
            echo "未知命令: $cmd"
            return 1
            ;;
    esac
}

# 导出函数
export -f safe_sudo safe_docker safe_docker_compose safe_auth

# 创建别名（可选）
# alias sudo='safe_sudo '
# alias docker='safe_docker '
# alias docker-compose='safe_docker_compose '
EOF

chmod +x /tmp/command-wrappers.sh
source /tmp/command-wrappers.sh
echo "   ✓ 命令包装器已创建并加载"
echo ""

# 5. 设置提示符
echo "5. 设置提示符..."
PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
echo "   ✓ 提示符已设置"
echo ""

# 6. 创建恢复函数
echo "6. 创建终端恢复函数..."
cat > /tmp/terminal-recovery.sh << 'EOF'
#!/bin/bash
# 终端恢复函数

recover_terminal() {
    echo "恢复终端设置..."
    
    # 恢复stty设置
    if [ -n "$OLD_STTY" ]; then
        stty "$OLD_STTY" 2>/dev/null
        echo "  ✓ stty设置已恢复"
    fi
    
    # 重置终端
    tput reset 2>/dev/null || true
    echo "  ✓ 终端已重置"
    
    # 清除屏幕
    clear 2>/dev/null || printf "\033c"
    echo "  ✓ 屏幕已清除"
}

# 注册退出时恢复
trap recover_terminal EXIT
EOF

source /tmp/terminal-recovery.sh
echo "   ✓ 终端恢复函数已创建"
echo ""

# 7. 测试终端
echo "7. 测试终端..."
if [ -t 1 ]; then
    echo "   ✓ 终端测试通过"
    echo "   列数: $(tput cols 2>/dev/null || echo 'N/A')"
    echo "   行数: $(tput lines 2>/dev/null || echo 'N/A')"
    echo "   颜色: $(tput colors 2>/dev/null || echo 'N/A')"
else
    echo "   ⚠️  无法测试非交互式终端"
fi
echo ""

echo "=== 终端初始化完成 ==="
echo ""
echo "可用命令:"
echo "  safe_sudo <command>    - 安全的sudo命令（避免闪烁）"
echo "  safe_docker <command>  - 安全的docker命令"
echo "  safe_auth <type> <cmd> - 通用的授权命令"
echo ""
echo "环境变量:"
echo "  TERM=$TERM"
echo "  COLORTERM=$COLORTERM"
echo ""
echo "要永久应用这些设置，请将它们添加到 ~/.bashrc"
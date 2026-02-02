#!/bin/bash
# 修复授权时屏幕闪烁问题

set -e

echo "=== 修复授权时屏幕闪烁问题 ==="
echo ""

# 1. 检查当前用户和权限
echo "1. 检查当前用户和权限:"
echo "   用户: $(whoami)"
echo "   UID: $(id -u)"
echo "   GID: $(id -g)"
echo "   组: $(groups)"
echo ""

# 2. 检查sudo配置
echo "2. 检查sudo配置:"
if command -v sudo >/dev/null 2>&1; then
    echo "   ✓ sudo 可用"
    # 检查是否需要密码
    if sudo -n true 2>/dev/null; then
        echo "   ✓ 当前用户无需密码即可使用sudo"
    else
        echo "   ⚠️  当前用户需要密码才能使用sudo"
    fi
else
    echo "   ✗ sudo 不可用"
fi
echo ""

# 3. 检查终端设置
echo "3. 检查终端设置:"
echo "   TERM: $TERM"
echo "   COLORTERM: $COLORTERM"
echo "   DISPLAY: $DISPLAY"
echo "   SSH_TTY: $SSH_TTY"
echo ""

# 4. 检查Docker容器权限
echo "4. 检查Docker容器权限:"
if command -v docker >/dev/null 2>&1; then
    echo "   ✓ Docker 可用"
    # 检查是否在docker组
    if groups | grep -q docker; then
        echo "   ✓ 用户在docker组中"
    else
        echo "   ⚠️  用户不在docker组中，可能需要sudo"
    fi
    
    # 检查docker.sock权限
    if [ -e /var/run/docker.sock ]; then
        echo "   docker.sock权限: $(ls -la /var/run/docker.sock)"
    fi
else
    echo "   ✗ Docker 不可用"
fi
echo ""

# 5. 创建修复方案
echo "5. 创建修复方案:"
echo "   创建环境变量配置文件..."

# 创建环境变量配置文件
cat > /tmp/fix-flicker-env.sh << 'EOF'
#!/bin/bash
# 环境变量配置 - 解决授权时屏幕闪烁

# 设置终端环境变量
export TERM=xterm-256color
export COLORTERM=truecolor
export DEBIAN_FRONTEND=noninteractive

# 禁用某些可能导致闪烁的特性
export LESS="-R -X"
export MANPAGER="less -R -X"

# 设置语言环境
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# 设置提示符 - 简洁版
PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '

# 别名 - 避免使用可能引起闪烁的命令
alias sudo='sudo '
alias docker='docker '
alias docker-compose='docker-compose '

# 函数：安全的sudo包装器
safe_sudo() {
    # 保存当前终端设置
    local old_stty=$(stty -g 2>/dev/null)
    
    # 执行sudo命令
    sudo "$@"
    
    # 恢复终端设置
    if [ -n "$old_stty" ]; then
        stty "$old_stty" 2>/dev/null
    fi
}

# 函数：安全的docker包装器
safe_docker() {
    # 检查是否需要sudo
    if docker info >/dev/null 2>&1; then
        docker "$@"
    else
        echo "需要授权访问Docker..."
        safe_sudo docker "$@"
    fi
}

# 函数：安全的docker-compose包装器
safe_docker_compose() {
    # 检查是否需要sudo
    if docker info >/dev/null 2>&1; then
        docker-compose "$@"
    else
        echo "需要授权访问Docker..."
        safe_sudo docker-compose "$@"
    fi
}

# 导出函数
export -f safe_sudo safe_docker safe_docker_compose

echo "环境变量已配置，授权时屏幕闪烁问题应该已解决。"
EOF

chmod +x /tmp/fix-flicker-env.sh
echo "   ✓ 创建环境变量配置文件: /tmp/fix-flicker-env.sh"
echo ""

# 6. 创建sudoers配置（可选）
echo "6. 创建sudoers配置建议:"
cat > /tmp/sudoers-fix.txt << 'EOF'
# 为当前用户添加免密码sudo（谨慎使用）
# 将以下行添加到 /etc/sudoers.d/$(whoami)
# $(whoami) ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/local/bin/docker-compose

# 或者添加docker组免密码（更安全）
# %docker ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/local/bin/docker-compose
EOF
echo "   ✓ 创建sudoers配置建议: /tmp/sudoers-fix.txt"
echo ""

# 7. 创建bashrc补丁
echo "7. 创建bashrc补丁:"
cat >> /tmp/fix-flicker-env.sh << 'EOF'

# 应用到当前shell
if [ -f ~/.bashrc ]; then
    # 检查是否已经包含配置
    if ! grep -q "TERM=xterm-256color" ~/.bashrc; then
        echo "# 屏幕闪烁修复配置" >> ~/.bashrc
        echo "export TERM=xterm-256color" >> ~/.bashrc
        echo "export COLORTERM=truecolor" >> ~/.bashrc
        echo "export DEBIAN_FRONTEND=noninteractive" >> ~/.bashrc
        echo "export LESS=\"-R -X\"" >> ~/.bashrc
        echo "已更新 ~/.bashrc"
    fi
fi

# 初始化终端
if [ -t 1 ]; then
    stty sane 2>/dev/null
    stty erase '^?' 2>/dev/null
    tput init 2>/dev/null || true
fi
EOF

echo "=== 修复完成 ==="
echo ""
echo "使用方法:"
echo "1. 立即应用配置: source /tmp/fix-flicker-env.sh"
echo "2. 永久应用: 将配置添加到 ~/.bashrc"
echo "3. 避免sudo密码提示: 查看 /tmp/sudoers-fix.txt (谨慎使用)"
echo ""
echo "关键修复:"
echo "- 设置正确的终端环境变量"
echo "- 使用安全的命令包装器"
echo "- 禁用可能引起闪烁的终端特性"
echo "- 优化sudo和docker命令交互"
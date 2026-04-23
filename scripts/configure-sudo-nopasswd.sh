#!/bin/bash
# 配置sudo免密码（谨慎使用）

set -e

echo "=== 配置sudo免密码（解决授权时屏幕闪烁）==="
echo "警告：这将在sudoers中为当前用户添加免密码权限"
echo ""

# 检查当前用户
CURRENT_USER=$(whoami)
echo "当前用户: $CURRENT_USER"

# 检查是否已经是免密码
if sudo -n true 2>/dev/null; then
    echo "✅ 当前用户已经是免密码sudo"
    exit 0
fi

# 创建sudoers配置
SUDOERS_FILE="/etc/sudoers.d/$CURRENT_USER-no-password"

echo "创建sudoers配置: $SUDOERS_FILE"
echo ""

# 显示将要添加的内容
cat << EOF
将要添加以下内容到 $SUDOERS_FILE:
----------------------------------------
$CURRENT_USER ALL=(ALL) NOPASSWD: ALL
----------------------------------------
EOF

echo ""
read -p "是否继续？(y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "操作已取消"
    exit 0
fi

# 创建sudoers文件
echo "$CURRENT_USER ALL=(ALL) NOPASSWD: ALL" | sudo tee "$SUDOERS_FILE" > /dev/null

# 设置正确的权限
sudo chmod 0440 "$SUDOERS_FILE"

# 验证配置
if sudo -n true 2>/dev/null; then
    echo "✅ sudo免密码配置成功！"
    echo ""
    echo "测试: sudo echo '测试成功'"
    sudo echo "✅ sudo命令无需密码"
else
    echo "❌ 配置失败，请手动检查"
    exit 1
fi

echo ""
echo "=== 可选：更安全的配置 ==="
echo "如果只想为特定命令免密码，可以编辑 $SUDOERS_FILE:"
echo ""
echo "# 只允许docker和docker-compose免密码"
echo "$CURRENT_USER ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/local/bin/docker-compose"
echo ""
echo "# 或者允许docker组的所有用户"
echo "%docker ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/local/bin/docker-compose"
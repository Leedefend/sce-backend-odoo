#!/bin/bash

# Continue DeepSeek 配置脚本 (Bash)
# 使用方法: ./scripts/setup-continue-deepseek.sh

echo "=== Continue DeepSeek 配置工具 ==="

# 1. 检查 Continue 配置目录
CONTINUE_DIR="$HOME/.continue"
if [ ! -d "$CONTINUE_DIR" ]; then
    echo "创建 Continue 配置目录..."
    mkdir -p "$CONTINUE_DIR"
fi

# 2. 询问 DeepSeek API Key
read -p "请输入 DeepSeek API Key (留空跳过): " DEEPSEEK_KEY

if [ -n "$DEEPSEEK_KEY" ]; then
    # 设置环境变量
    echo "设置环境变量..."
    export DEEPSEEK_API_KEY="$DEEPSEEK_KEY"
    
    # 可选：永久设置
    read -p "是否永久设置环境变量？(y/n): " SET_PERMANENT
    if [ "$SET_PERMANENT" = "y" ] || [ "$SET_PERMANENT" = "Y" ]; then
        echo "export DEEPSEEK_API_KEY=\"$DEEPSEEK_KEY\"" >> ~/.bashrc
        echo "已永久设置环境变量 (添加到 ~/.bashrc)"
    fi
fi

# 3. 复制配置文件
echo "复制配置文件..."
CONFIG_SOURCE="$(dirname "$0")/../config/continue-deepseek.json"
CONFIG_DEST="$CONTINUE_DIR/config.json"

if [ -f "$CONFIG_SOURCE" ]; then
    cp "$CONFIG_SOURCE" "$CONFIG_DEST"
    echo "配置文件已复制到: $CONFIG_DEST"
else
    echo "警告：配置文件不存在: $CONFIG_SOURCE"
    
    # 创建默认配置
    cat > "$CONFIG_DEST" << 'EOF'
{
  "models": [
    {
      "title": "DeepSeek Coder",
      "provider": "openai",
      "model": "deepseek-coder",
      "apiKey": "${env:DEEPSEEK_API_KEY}",
      "apiBase": "https://api.deepseek.com",
      "contextLength": 16384
    },
    {
      "title": "DeepSeek Chat",
      "provider": "openai",
      "model": "deepseek-chat",
      "apiKey": "${env:DEEPSEEK_API_KEY}",
      "apiBase": "https://api.deepseek.com",
      "contextLength": 32768
    }
  ],
  "defaultModel": "DeepSeek Coder",
  "tabAutocompleteModel": {
    "title": "DeepSeek Coder",
    "provider": "openai",
    "model": "deepseek-coder",
    "apiKey": "${env:DEEPSEEK_API_KEY}",
    "apiBase": "https://api.deepseek.com"
  },
  "allowAnonymousTelemetry": false,
  "experimental": {
    "disableIndexing": true
  }
}
EOF
    
    echo "已创建默认配置文件"
fi

# 4. 验证配置
echo -e "\n验证配置..."
if [ -f "$CONFIG_DEST" ]; then
    if grep -q "deepseek" "$CONFIG_DEST"; then
        echo "✅ DeepSeek 配置检测成功"
    else
        echo "⚠️  配置文件中未找到 DeepSeek 配置"
    fi
else
    echo "❌ 配置文件不存在"
fi

# 5. 检查环境变量
if [ -n "$DEEPSEEK_API_KEY" ]; then
    echo "✅ DeepSeek API Key 已设置"
else
    echo "⚠️  DeepSeek API Key 未设置"
    echo "   请手动设置: export DEEPSEEK_API_KEY='你的_api_key'"
fi

# 6. 显示下一步操作
echo -e "\n=== 下一步操作 ==="
echo "1. 重启 Continue 服务:"
echo "   - 在 VS Code 中: Ctrl+Shift+P -> 'Developer: Reload Window'"
echo "   - 在 CLI 中: 重启 continue 进程"
echo -e "\n2. 验证模型:"
echo "   - 在 Continue 中输入 '/model' 查看可用模型"
echo "   - 输入 '/model DeepSeek Coder' 切换到 DeepSeek"
echo -e "\n3. 测试模型:"
echo "   - 输入 '@ 写一个 Python Hello World 程序'"

echo -e "\n=== 配置完成 ==="
echo "配置文件位置: $CONFIG_DEST"
echo "文档参考: docs/continue-deepseek-config.md"
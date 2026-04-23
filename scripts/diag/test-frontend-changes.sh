#!/bin/bash
# Usage: scripts/diag/test-frontend-changes.sh
# 测试前端修改是否生效

echo "=== 测试前端修改 ==="
echo ""

# 1. 检查文件修改
echo "1. 检查修改的文件:"
echo "   - frontend/apps/web/src/stores/session.ts (A1诊断)"
echo "   - frontend/apps/web/src/api/client.ts (A2网络诊断)"
echo "   - frontend/apps/web/src/views/HomeView.vue (A3根菜单不匹配检测)"
echo "   - frontend/apps/web/src/config.ts (C1环境变量)"
echo "   - frontend/apps/web/.env.local (C1环境变量文件)"
echo ""

# 2. 检查后端修改
echo "2. 检查后端修改:"
echo "   - addons/smart_core/app_config_engine/services/dispatchers/nav_dispatcher.py (B1诊断)"
echo "   - addons/smart_core/handlers/system_init.py (B1诊断)"
echo "   - addons/smart_core/controllers/intent_dispatcher.py (B2 DB解析)"
echo ""

# 3. 检查脚本
echo "3. 检查脚本:"
echo "   - scripts/diag/check-root-menu.py (B3根菜单检查)"
echo ""

# 4. 验证前端代码语法
echo "4. 验证前端TypeScript语法:"
cd frontend/apps/web
if command -v npx &> /dev/null; then
    npx tsc --noEmit --skipLibCheck
    if [ $? -eq 0 ]; then
        echo "   ✅ TypeScript语法检查通过"
    else
        echo "   ❌ TypeScript语法检查失败"
    fi
else
    echo "   ⚠️  npx不可用，跳过TypeScript检查"
fi
cd - > /dev/null

echo ""
echo "=== 使用说明 ==="
echo ""
echo "1. 启动前端开发服务器:"
echo "   cd frontend/apps/web && npm run dev"
echo ""
echo "2. 打开浏览器控制台查看诊断信息:"
echo "   - [C1] 环境变量配置"
echo "   - [A1] app.init 请求诊断"
echo "   - [A2] app.init 网络诊断快照"
echo "   - [A3] 菜单详细诊断 (点击Dump Menu按钮)"
echo ""
echo "3. 检查根菜单不匹配错误面板:"
echo "   - 如果返回Odoo原生菜单，会显示红色错误面板"
echo ""
echo "4. 运行后端检查脚本:"
echo "   python scripts/diag/check-root-menu.py --db sc_demo"
echo "   python scripts/diag/check-root-menu.py --db sc_demo --list-modules"
echo ""
echo "5. 查看后端日志中的诊断信息:"
echo "   - [B1] system.init 诊断信息"
echo "   - [B1] NavDispatcher 诊断信息"
echo "   - [B2] DB解析诊断"
echo "   - [B4] 权限过滤警告"
echo ""
echo "=== 预期结果 ==="
echo ""
echo "✅ 前端控制台应显示:"
echo "   - effective_db: sc_demo"
echo "   - effective_root_xmlid: smart_construction_core.menu_sc_root"
echo "   - 第一个菜单不是Odoo原生应用菜单"
echo ""
echo "✅ 后端日志应显示:"
echo "   - effective_db: sc_demo"
echo "   - db_source: header (如果前端正确发送X-Odoo-DB)"
echo "   - effective_root_xmlid: smart_construction_core.menu_sc_root"
echo ""
echo "❌ 如果出现问题:"
echo "   - 前端会显示根菜单不匹配错误面板"
echo "   - 控制台会有详细的诊断信息"
echo "   - 后端日志会有[B1][B2]诊断信息"

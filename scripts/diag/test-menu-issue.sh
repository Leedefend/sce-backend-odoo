#!/bin/bash
# Usage: scripts/diag/test-menu-issue.sh
# 测试菜单问题

echo "=== 诊断菜单问题 ==="
echo ""

echo "1. 检查数据库状态:"
docker exec sc-backend-odoo-db-1 psql -U odoo -d sc_demo -c "
SELECT name, state FROM ir_module_module 
WHERE name IN ('smart_core', 'smart_construction_core', 'smart_construction_bootstrap')
ORDER BY name;
" 2>/dev/null

echo ""
echo "2. 检查ir_ui_menu表:"
docker exec sc-backend-odoo-db-1 psql -U odoo -d sc_demo -c "
SELECT id, name, parent_id, complete_name 
FROM ir_ui_menu 
WHERE name LIKE '%root%' OR name LIKE '%Root%' OR complete_name LIKE '%root%'
ORDER BY id
LIMIT 10;
" 2>/dev/null

echo ""
echo "3. 检查ir.model.data中的菜单XMLID:"
docker exec sc-backend-odoo-db-1 psql -U odoo -d sc_demo -c "
SELECT imd.id, imd.module, imd.name, imd.res_id, m.name as menu_name
FROM ir_model_data imd
LEFT JOIN ir_ui_menu m ON imd.res_id = m.id
WHERE imd.model = 'ir.ui.menu' 
AND (imd.module LIKE '%smart%' OR imd.name LIKE '%root%')
ORDER BY imd.module, imd.name
LIMIT 20;
" 2>/dev/null

echo ""
echo "4. 检查Odoo默认根菜单:"
docker exec sc-backend-odoo-db-1 psql -U odoo -d sc_demo -c "
SELECT id, name, parent_id, complete_name 
FROM ir_ui_menu 
WHERE parent_id IS NULL
ORDER BY sequence, id
LIMIT 10;
" 2>/dev/null

echo ""
echo "5. 检查demo_full用户:"
docker exec sc-backend-odoo-db-1 psql -U odoo -d sc_demo -c "
SELECT id, login, name, active 
FROM res_users 
WHERE login LIKE '%demo%' OR name LIKE '%demo%'
ORDER BY id;
" 2>/dev/null

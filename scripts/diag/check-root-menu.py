#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Usage: python scripts/diag/check-root-menu.py --db <db_name> [--xmlid module.menu_xmlid]
"""
B3: 菜单根xmlid存在性与安装状态自检脚本
快速判断当前DB是否真的装了smart_construction_core模块
"""

import sys
import os
import argparse
from pathlib import Path

# 添加odoo路径（优先环境变量 ROOT_DIR，其次脚本相对路径）
ROOT_DIR = Path(os.environ.get("ROOT_DIR", Path(__file__).resolve().parents[2]))
ODOO_RUNTIME = ROOT_DIR / "runtime" / "odoo"
sys.path.append(str(ODOO_RUNTIME))

try:
    import odoo
    from odoo.tools import config
except ImportError as e:
    print(f"❌ 无法导入odoo: {e}")
    print("请确保在正确的环境中运行此脚本")
    sys.exit(1)

def check_root_menu(db_name, xmlid="smart_construction_core.menu_sc_root"):
    """
    检查指定数据库中根菜单的存在性和状态
    """
    print(f"=== B3: 根菜单检查 (DB: {db_name}, XMLID: {xmlid}) ===")
    print()
    
    # 设置数据库
    config['db_name'] = db_name
    
    try:
        # 初始化odoo注册表
        registry = odoo.registry(db_name)
        with registry.cursor() as cr:
            uid = odoo.SUPERUSER_ID
            env = odoo.api.Environment(cr, uid, {})
            
            print("1. 检查模块安装状态:")
            module = env['ir.module.module'].search([
                ('name', '=', 'smart_construction_core'),
                ('state', '=', 'installed')
            ], limit=1)
            
            if module:
                print(f"   ✅ smart_construction_core 模块已安装")
                print(f"      版本: {module.installed_version}")
                print(f"      状态: {module.state}")
            else:
                print(f"   ❌ smart_construction_core 模块未安装或未激活")
                # 检查是否存在但未安装
                all_modules = env['ir.module.module'].search([
                    ('name', '=', 'smart_construction_core')
                ], limit=1)
                if all_modules:
                    print(f"      模块存在但状态为: {all_modules.state}")
                else:
                    print(f"      模块不存在于数据库中")
                return False
            
            print()
            print("2. 检查ir.model.data记录:")
            imd = env['ir.model.data'].search([
                ('model', '=', 'ir.ui.menu'),
                ('module', '=', xmlid.split('.')[0]),
                ('name', '=', xmlid.split('.')[1])
            ], limit=1)
            
            if imd:
                print(f"   ✅ XMLID记录存在")
                print(f"      ID: {imd.id}")
                print(f"      res_id: {imd.res_id}")
                print(f"      完整XMLID: {imd.module}.{imd.name}")
            else:
                print(f"   ❌ XMLID记录不存在: {xmlid}")
                # 列出所有smart_construction_core模块的菜单
                all_menu_xmlids = env['ir.model.data'].search([
                    ('model', '=', 'ir.ui.menu'),
                    ('module', '=', 'smart_construction_core')
                ])
                print(f"      找到 {len(all_menu_xmlids)} 个smart_construction_core菜单XMLID:")
                for item in all_menu_xmlids[:10]:  # 只显示前10个
                    print(f"        - {item.module}.{item.name}")
                if len(all_menu_xmlids) > 10:
                    print(f"        ... 还有 {len(all_menu_xmlids) - 10} 个")
                return False
            
            print()
            print("3. 检查ir.ui.menu记录:")
            menu = env['ir.ui.menu'].browse(imd.res_id)
            if menu.exists():
                print(f"   ✅ 菜单记录存在")
                print(f"      ID: {menu.id}")
                print(f"      名称: {menu.name}")
                print(f"      完整路径: {menu.complete_name}")
                print(f"      是否激活: {menu.active}")
                print(f"      父菜单: {menu.parent_id.name if menu.parent_id else '无 (根菜单)'}")
                print(f"      序列号: {menu.sequence}")
            else:
                print(f"   ❌ 菜单记录不存在 (res_id={imd.res_id})")
                return False
            
            print()
            print("4. 检查菜单权限 (groups_id):")
            if menu.groups_id:
                print(f"   菜单有 {len(menu.groups_id)} 个权限组限制:")
                for group in menu.groups_id:
                    # 获取XMLID
                    group_xmlid = env['ir.model.data'].search([
                        ('model', '=', 'res.groups'),
                        ('res_id', '=', group.id)
                    ], limit=1)
                    xmlid_str = f"{group_xmlid.module}.{group_xmlid.name}" if group_xmlid else f"ID:{group.id}"
                    print(f"      - {group.name} ({xmlid_str})")
            else:
                print(f"   ✅ 菜单无权限组限制 (全员可见)")
            
            print()
            print("5. 检查demo_full用户权限:")
            demo_user = env['res.users'].search([
                ('login', '=', 'demo_full')
            ], limit=1)
            
            if demo_user:
                print(f"   ✅ demo_full用户存在 (ID: {demo_user.id})")
                print(f"      用户组: {len(demo_user.groups_id)} 个")
                
                # 检查demo_full是否能访问此菜单
                user_groups = set(demo_user.groups_id.ids)
                menu_groups = set(menu.groups_id.ids)
                
                if not menu.groups_id or user_groups.intersection(menu_groups):
                    print(f"   ✅ demo_full可以访问此菜单")
                    if menu.groups_id:
                        print(f"      原因: 用户有菜单所需权限组")
                else:
                    print(f"   ❌ demo_full无法访问此菜单")
                    print(f"      原因: 用户缺少菜单所需权限组")
                    print(f"      菜单所需组: {menu_groups}")
                    print(f"      用户拥有组: {user_groups}")
            else:
                print(f"   ⚠️  demo_full用户不存在")
            
            print()
            print("6. 检查菜单子项:")
            child_menus = env['ir.ui.menu'].search([
                ('parent_id', '=', menu.id)
            ])
            print(f"   有 {len(child_menus)} 个子菜单:")
            for child in child_menus[:5]:  # 只显示前5个
                print(f"      - {child.name} (ID: {child.id})")
            if len(child_menus) > 5:
                print(f"      ... 还有 {len(child_menus) - 5} 个")
            
            return True
            
    except Exception as e:
        print(f"❌ 检查过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='检查根菜单存在性与安装状态')
    parser.add_argument('--db', default='sc_demo', help='数据库名称 (默认: sc_demo)')
    parser.add_argument('--xmlid', default='smart_construction_core.menu_sc_root', 
                       help='根菜单XMLID (默认: smart_construction_core.menu_sc_root)')
    parser.add_argument('--list-modules', action='store_true', 
                       help='列出所有已安装的模块')
    
    args = parser.parse_args()
    
    if args.list_modules:
        print("=== 列出所有已安装模块 ===")
        try:
            config['db_name'] = args.db
            registry = odoo.registry(args.db)
            with registry.cursor() as cr:
                uid = odoo.SUPERUSER_ID
                env = odoo.api.Environment(cr, uid, {})
                modules = env['ir.module.module'].search([
                    ('state', '=', 'installed')
                ], order='name')
                print(f"数据库 {args.db} 中有 {len(modules)} 个已安装模块:")
                for module in modules:
                    print(f"  - {module.name}: {module.installed_version} ({module.state})")
        except Exception as e:
            print(f"❌ 列出模块时出错: {e}")
        return
    
    success = check_root_menu(args.db, args.xmlid)
    
    print()
    print("=" * 60)
    if success:
        print("✅ 检查完成: 根菜单配置正常")
    else:
        print("❌ 检查完成: 发现配置问题")
    print("=" * 60)

if __name__ == '__main__':
    main()

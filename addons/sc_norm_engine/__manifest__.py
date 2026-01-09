{
    "name": "SC Norm Engine (Sichuan 2015)",
    "version": "17.0.1.0.0",
    "summary": "Sichuan 2015 construction norm engine with import wizard",
    "category": "Construction",
    "author": "lidefend",
    "depends": ["base", "uom"],
    "data": [
        "security/ir.model.access.csv",
        "views/norm_views.xml",         # 定义视图和 actions
        "views/norm_import_views.xml",  # 导入向导
        "views/norm_menu.xml",          # 菜单引用上述 actions
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}

# -*- coding: utf-8 -*-
{
    "name": "Smart Construction Scene Orchestration",
    "version": "17.0.0.1",
    "summary": "Scene orchestration source for portal shell",
    "author": "Leedefend",
    "depends": [
        "smart_construction_core",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/scene_governance_views.xml",
        "data/sc_scene_orchestration.xml",
        "data/sc_scene_layout.xml",
        "data/sc_scene_tiles.xml",
        "data/sc_scene_list_profile.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}

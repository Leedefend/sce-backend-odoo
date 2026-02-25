# -*- coding: utf-8 -*-
from __future__ import annotations


class SystemInitNavRequestBuilder:
    @staticmethod
    def build(params: dict, scene: str) -> dict:
        payload = {"subject": "nav", "scene": scene}
        if params.get("root_xmlid"):
            payload["root_xmlid"] = params.get("root_xmlid")
        if params.get("root_menu_id"):
            payload["root_menu_id"] = params.get("root_menu_id")
        return payload

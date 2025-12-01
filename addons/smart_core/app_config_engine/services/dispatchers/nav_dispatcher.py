# -*- coding: utf-8 -*-
# smart_core/app_config_engine/services/dispatchers/nav_dispatcher.py
# 生成导航菜单契约：根归一 → 节点归一 → 富化(action/model/sequence/xmlid) → 过滤(scene/groups)
# → 排序 → 前端契约整形（去路由化：叶子以 menu_id 注入）→ 默认注入目标推断 → 指纹/ETag

from __future__ import annotations

import json
import logging
import hashlib
from typing import Dict, Any, List, Optional, Union, Iterable, Tuple
from collections.abc import Mapping

_logger = logging.getLogger(__name__)


class NavDispatcher:
    """
    返回“契约·导航（subject:'nav'）”：
    - 仅提供前端注入所需的“最小充分信息”，不固化 path/route；
    - 叶子节点以 menu_id 为稳定键，前端据此调用 contract.get(subject:'menu', id:menu_id) 渲染；
    - meta.fingerprint = md5(scene, groups_xmlids, cfg.version) 便于前端/HTTP 304 缓存。
    """

    def __init__(self, env, su_env):
        self.env = env       # 当前用户 env（用于 groups/权限过滤）
        self.su_env = su_env # sudo env（用于元数据与菜单树生成）

    # ========================= 对外入口 ========================= #

    def build_nav(self, p: Optional[Dict[str, Any]]):
        p = p or {}
        scene = p.get("scene") or self.env.context.get("scene") or "web"
        enrich_mode = (p.get("enrich_mode") or "model").lower()
        do_enrich = bool(p.get("enrich_nav", True))

        # 1) 从配置服务获取菜单树（sudo，避免权限阻塞元数据）
        cfg_model = self.su_env["app.menu.config"]
        cfg = cfg_model._generate_from_menus(model_name=None)
        tree_raw = cfg.get_menu_contract(model_name=None) or []

        # 2) 归一根集合
        roots = self._flatten_roots(tree_raw)
        _logger.info("NAV_DEBUG: raw_from_config count=%s type=%s", len(roots), type(tree_raw))

        # 3) 节点统一为 dict
        tree: List[Dict[str, Any]] = [self._node_to_dict(n) for n in roots if n is not None]

        # 4) 富化（批量化尽量避免 N+1）
        if do_enrich and tree:
            try:
                self._enrich_nav_models(tree, mode=enrich_mode)
            except Exception as e:
                _logger.warning("NavDispatcher enrich_nav failed: %s", e)
        _logger.info("NAV_DEBUG: after_enrich count=%s", len(tree))

        # 5) 过滤 + scene 继承（管理员短路）
        filtered = self._filter_and_normalize_nav(tree, scene=scene)

        # 管理员兜底（若被错误过滤为空）
        if not filtered and self.env.user.has_group("base.group_system") and tree:
            _logger.warning("NAV_DEBUG: filtered empty for admin -> fallback to unfiltered")
            filtered = self._mark_all_visible(self._inherit_scene(tree, parent_scene="web"))

        # 6) 子树稳定排序（sequence → label）
        filtered = self._sort_subtrees(filtered)

        # 7) 前端契约整形（去路由化；稳定键基于 menu_id）
        nav = self._to_front_contract(filtered)

        # 8) 默认注入目标：首个“叶子且有 menu_id”的节点；否则回退字符串 '/workbench'
        default_route = self._infer_default_injection(nav)

        # 9) 指纹（结合 cfg.version + scene + 当前用户 groups_xmlids）
        user_groups_xmlids = self._groups_to_xmlids(self.env.user.groups_id)
        meta = {
            "menu": int(getattr(cfg, "version", 1) or 1),
            "fingerprint": self._nav_fingerprint(cfg.version, scene, user_groups_xmlids),
        }

        _logger.info("NAV_DEBUG: final_count=%s (scene=%s, uid=%s)", len(nav), scene, self.env.user.id)
        data = {"nav": nav, "defaultRoute": default_route}
        return data, meta

    # ========================= 工具：根集合归一 ========================= #

    def _flatten_roots(self, root_obj: Any) -> List[Any]:
        """
        将各种可能形态的根集合统一成 list：
        - list/tuple/set → 直接展开为 list
        - Mapping → 优先取常见容器字段；否则 values() 展开
        - 其它 → 单元素 list
        """
        if root_obj is None:
            return []
        if isinstance(root_obj, (list, tuple, set)):
            return list(root_obj)
        if isinstance(root_obj, Mapping):
            for k in ("children", "items", "roots", "menus", "root"):
                if k in root_obj:
                    v = root_obj.get(k)
                    if isinstance(v, (list, tuple, set)):
                        return list(v)
                    return [v] if v is not None else []
            out: List[Any] = []
            try:
                for v in root_obj.values():
                    if isinstance(v, (list, tuple, set)):
                        out.extend(list(v))
                    elif v is not None:
                        out.append(v)
            except Exception:
                out = [root_obj]
            return out
        return [root_obj]

    # ========================= 工具：节点 / children 归一 ========================= #

    def _coerce_children(self, node: Union[Dict[str, Any], Any]) -> List[Any]:
        """尽可能从各种形态里取出 children 列表"""
        if isinstance(node, (list, tuple, set)):
            return list(node)
        if isinstance(node, Mapping):
            ch = node.get("children") or node.get("items") or []
            if isinstance(ch, (list, tuple, set)):
                return list(ch)
            return []
        for attr in ("children", "items", "childs", "nodes"):
            if hasattr(node, attr):
                val = getattr(node, attr)
                return list(val) if isinstance(val, (list, tuple, set)) else []
        return []

    def _node_to_dict(self, n: Any) -> Dict[str, Any]:
        """
        把任意节点尽力转成 dict：
        - Mapping → dict(...)
        - 有 to_dict() → 调用
        - 有 __dict__ → 复制（过滤私有字段）
        - 否则：按常见字段 getattr；仍不行则 {"label": str(n)}
        并确保 children 也转 dict 列表。
        """
        try:
            if isinstance(n, Mapping):
                d = dict(n)
            elif hasattr(n, "to_dict") and callable(getattr(n, "to_dict")):
                d = dict(getattr(n, "to_dict")())
            elif hasattr(n, "__dict__"):
                d = {k: v for k, v in vars(n).items() if not k.startswith("_")}
            else:
                d = {}
                for k in ("id", "menu_id", "name", "title", "scene", "groups",
                          "groups_xmlids", "action", "icon", "web_icon", "sequence"):
                    if hasattr(n, k):
                        d[k] = getattr(n, k)
                if not d:
                    d = {"label": str(n)}
        except Exception:
            d = {"label": str(n)}

        raw_children = None
        if isinstance(n, Mapping):
            raw_children = n.get("children")
        if raw_children is None:
            raw_children = self._coerce_children(n)
        d["children"] = [self._node_to_dict(x) for x in (raw_children or []) if x is not None]
        return d

    # ========================= 富化（批量尽量避免 N+1） ========================= #

    def _enrich_nav_models(self, tree: List[Dict[str, Any]], mode: str = "model"):
        if not tree:
            return
        su_env = self.su_env

        # 收集所有 menu_id
        mids: set[int] = set()
        def collect_mids(nodes: List[Dict[str, Any]]):
            for n in nodes or []:
                mid = n.get("menu_id") or n.get("id")
                if mid:
                    try:
                        mids.add(int(mid))
                    except Exception:
                        pass
                collect_mids(n.get("children") or [])
        collect_mids(tree)

        menu_map = {}
        if mids:
            menus = su_env["ir.ui.menu"].browse(list(mids)).exists()
            menu_map = {m.id: m for m in menus}

        def to_action_dict(act: Optional[Any]):
            if not act or not isinstance(act, Mapping):
                return None
            d = dict(act)
            for k in ("res_model", "view_id", "domain_raw", "web_icon"):
                if k in d and (d[k] is False or d[k] == "" or d[k] == []):
                    d[k] = None
            if "type" in d and "action_type" not in d:
                d["action_type"] = d.get("type")
            return d

        def xmlid_of(rec) -> Optional[str]:
            try:
                mapping = rec.get_external_id()
                if mapping:
                    return next(iter(mapping.values()))
            except Exception:
                pass
            return None

        def attach_from_action(node: Dict[str, Any], act_rec):
            try:
                node.setdefault("action_id", act_rec.id)
                node.setdefault("action_type", act_rec._name)
                ax = xmlid_of(act_rec)
                if ax:
                    node.setdefault("action_xmlid", ax)
                res_model = getattr(act_rec, "res_model", None)
                if res_model:
                    node.setdefault("model", res_model)
                if mode == "full" and act_rec._name == "ir.actions.act_window":
                    vm = (getattr(act_rec, "view_mode", None) or "").split(",")
                    vm = [v.strip() for v in vm if v and v.strip()]
                    if vm:
                        node.setdefault("view_modes", vm)
                    try:
                        views = getattr(act_rec, "views", None) or []
                        if views:
                            node.setdefault("views", [(vid, vtype) for (vid, vtype) in views])
                    except Exception:
                        pass
                    # 透传 domain/context（若有）
                    if getattr(act_rec, "domain", False):
                        node.setdefault("domain", act_rec.domain)
                    if getattr(act_rec, "context", False):
                        node.setdefault("context", act_rec.context)
            except Exception:
                pass

        def resolve_action_by_menu(menu_id) -> Optional[Any]:
            try:
                m = menu_map.get(int(menu_id))
                if not m or not m.exists():
                    return None
                act = m.action
                return act if act and act.exists() else None
            except Exception:
                return None

        def browse_action_by_hint(act_id: Optional[int], act_type: Optional[str]):
            if act_id and act_type:
                try:
                    rec = su_env[act_type].browse(int(act_id))
                    if rec and rec.exists():
                        return rec
                except Exception:
                    return None
            return None

        def walk(nodes: List[Dict[str, Any]]):
            for node in (nodes or []):
                if not isinstance(node, dict):
                    continue

                # 序列/菜单 XMLID 富化
                mid = node.get("menu_id") or node.get("id")
                if mid:
                    menu_rec = menu_map.get(int(mid))
                    if menu_rec and menu_rec.exists():
                        node.setdefault("sequence", getattr(menu_rec, "sequence", None))
                        mx = xmlid_of(menu_rec)
                        if mx:
                            node.setdefault("menu_xmlid", mx)

                act_dict = to_action_dict(node.get("action"))
                act_rec = None

                # action 字典内嵌 → 先填基本字段，再按 id/type 反查 action 记录
                if act_dict:
                    if act_dict.get("id"):
                        node.setdefault("action_id", act_dict["id"])
                    if act_dict.get("action_type") or act_dict.get("type"):
                        node.setdefault("action_type", act_dict.get("action_type") or act_dict.get("type"))
                    if act_dict.get("res_model"):
                        node.setdefault("model", act_dict["res_model"])

                    aid = act_dict.get("id")
                    atype = act_dict.get("action_type") or act_dict.get("type")
                    if (not node.get("model") or mode == "full") and aid:
                        act_rec = browse_action_by_hint(aid, atype)
                        if act_rec:
                            attach_from_action(node, act_rec)

                # 无 action 明确指向 → 从 menu.action 反查
                if not node.get("action_id") and not node.get("model") and mid:
                    act_rec = resolve_action_by_menu(mid)
                    if act_rec:
                        attach_from_action(node, act_rec)

                if node.get("children"):
                    walk(node["children"])

        walk(tree)

    # ==================== 过滤 + 归一（含 scene 继承） ==================== #

    def _filter_and_normalize_nav(self, tree: List[Dict[str, Any]],
                                  scene: Optional[Union[str, List[str]]] = None):
        if not tree:
            return []

        user = self.env.user

        # 管理员短路（直接 scene 继承 + 标记可见）
        if user.has_group("base.group_system"):
            _logger.info("NAV_DEBUG: admin bypass filtering (uid=%s)", user.id)
            return self._mark_all_visible(self._inherit_scene(tree, parent_scene="web"))

        # 非管理员：先继承 scene
        tree = self._inherit_scene(tree, parent_scene="web")

        user_group_ids = set(user.groups_id.ids)
        user_group_xmlids = self._groups_to_xmlids(user.groups_id)

        def scene_ok(node_scene: Union[str, List[str]], wanted: Optional[Union[str, List[str]]]) -> bool:
            def to_list(v):
                if v is None:
                    return [None]
            # noqa: E301
                if isinstance(v, (list, tuple, set)):
                    return list(v)
                return [v]
            ns = [x if (x not in ("", None)) else "web" for x in to_list(node_scene)]
            ws = to_list(wanted or "web")
            if any(str(x).lower() in ("all", "*") or x is None for x in ns):
                return True
            if any(str(x).lower() in ("all", "*") or x is None for x in ws):
                return True
            ns_norm = {str(x).strip().lower() for x in ns}
            ws_norm = {str(x).strip().lower() for x in ws}
            return not ns_norm.isdisjoint(ws_norm)

        def parse_groups_field(v) -> Tuple[set[str], set[int]]:
            if v is None:
                return set(), set()
            if isinstance(v, str):
                parts = [s.strip() for s in v.split(",") if s.strip()]
                xmls = {p for p in parts if "." in p}
                ids = {int(p) for p in parts if p.isdigit()}
                return xmls, ids
            if isinstance(v, (list, tuple, set)):
                xmls, ids = set(), set()
                for item in v:
                    if isinstance(item, int):
                        ids.add(item)
                    elif isinstance(item, str):
                        if item.isdigit():
                            ids.add(int(item))
                        elif "." in item:
                            xmls.add(item)
                return xmls, ids
            return set(), set()

        def norm_action(act: Any):
            if not act or not isinstance(act, Mapping):
                return None
            d = dict(act)
            for k in ("res_model", "view_id", "domain_raw", "web_icon"):
                if k in d and (d[k] is False or d[k] == "" or d[k] == []):
                    d[k] = None
            return d

        wanted_scene = scene or "web"

        def walk(nodes: List[Dict[str, Any]]):
            out = []
            for nn in (nodes or []):
                if not isinstance(nn, dict):
                    nn = self._node_to_dict(nn)
                nn["action"] = norm_action(nn.get("action"))
                nn["children"] = walk(nn.get("children") or [])

                node_scene = nn.get("scene")
                scene_pass = scene_ok(node_scene, wanted_scene)

                xmls1, ids1 = parse_groups_field(nn.get("groups_xmlids"))
                xmls2, ids2 = parse_groups_field(nn.get("groups"))
                required_xmlids = xmls1 | xmls2
                required_ids = ids1 | ids2
                groups_pass = True
                if required_xmlids or required_ids:
                    groups_pass = (not required_xmlids or not self._groups_intersection_empty(required_xmlids, user_group_xmlids)) and \
                                  (not required_ids or not self._ids_intersection_empty(required_ids, user_group_ids))

                self_visible = scene_pass and groups_pass
                have_visible_child = len(nn["children"]) > 0

                if self_visible or have_visible_child:
                    nn["visible"] = True
                    out.append(nn)
                else:
                    _logger.info(
                        "NAV_FILTER_DROP uid=%s id=%s label=%s scene_pass=%s groups_pass=%s node_scene=%s req_xmlids=%s req_ids=%s",
                        user.id, nn.get("menu_id") or nn.get("id"),
                        nn.get("name") or nn.get("title") or nn.get("label"),
                        scene_pass, groups_pass, node_scene, list(required_xmlids), list(required_ids)
                    )
            return out

        return walk(tree)

    # ==================== 排序（子树稳定序） ==================== #

    def _sort_subtrees(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        def sort_key(n: Dict[str, Any]):
            seq = n.get("sequence")
            # None 统一放到靠后
            return (seq if isinstance(seq, int) else 999999, (n.get("title") or n.get("label") or ""))

        out = []
        for n in nodes or []:
            n = dict(n)
            n["children"] = self._sort_subtrees(n.get("children") or [])
            out.append(n)
        out.sort(key=sort_key)
        return out

    # ==================== 前端契约整形（去路由化） ==================== #

    def _to_front_contract(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        def stable_key(n: Dict[str, Any]) -> str:
            mid = n.get("menu_id") or n.get("id")
            if mid is not None:
                try:
                    return f"menu:{int(mid)}"
                except Exception:
                    pass
            # 真无 ID 才兜底：对稳定字段签名（不要引用对象 id）
            sig = {
                "label": n.get("title") or n.get("name") or n.get("label") or "",
                "action_id": n.get("action_id") or (n.get("action") or {}).get("id"),
                "model": n.get("model") or (n.get("action") or {}).get("res_model"),
            }
            raw = json.dumps(sig, sort_keys=True, ensure_ascii=False)
            return "sig:" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]

        def label_of(n: Dict[str, Any]) -> str:
            return n.get("title") or n.get("name") or n.get("label") or "未命名菜单"

        def icon_of(n: Dict[str, Any]):
            act = n.get("action") or {}
            return n.get("web_icon") or n.get("icon") or act.get("web_icon")

        def meta_of(n: Dict[str, Any]) -> Dict[str, Any]:
            act = n.get("action") or {}
            m = {
                "scene": n.get("scene") or "web",
                "sequence": n.get("sequence"),
                "menu_id": n.get("menu_id") or n.get("id"),
                "menu_xmlid": n.get("menu_xmlid"),
                "action_id": n.get("action_id") or act.get("id"),
                "action_type": n.get("action_type") or act.get("action_type") or act.get("type"),
                "action_xmlid": n.get("action_xmlid"),
                "model": n.get("model") or act.get("res_model"),
                "view_modes": n.get("view_modes"),
                "views": n.get("views"),
                "domain": n.get("domain"),
                "context": n.get("context"),
                "groups_xmlids": n.get("groups") or n.get("groups_xmlids"),
            }
            return {k: v for k, v in m.items() if v not in (None, [], "", {})}

        def walk(arr: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            out = []
            for n in arr or []:
                ch = walk(n.get("children") or [])
                node = {
                    "key": stable_key(n),
                    "label": label_of(n),
                    "icon": icon_of(n),
                    "menu_id": n.get("menu_id") or n.get("id"),
                    "children": ch,
                    "meta": meta_of(n),
                }
                out.append(node)
            return out

        return walk(nodes)

    def _infer_default_injection(self, nav: List[Dict[str, Any]]) -> Union[Dict[str, Any], str]:
        """
        默认注入目标：
        - 广度优先：第一个“叶子且有 menu_id”的节点 → 返回 {"menu_id": <int>}
        - 否则回退 "/workbench"（向后兼容）
        """
        q = list(nav or [])
        while q:
            n = q.pop(0)
            children = n.get("children") or []
            if not children and n.get("menu_id"):
                return {"menu_id": n["menu_id"]}
            q = children + q
        return "/workbench"

    # ==================== 小工具 ==================== #

    def _inherit_scene(self, nodes: List[Dict[str, Any]], parent_scene: Union[str, List[str]] = "web"):
        out = []
        for n in (nodes or []):
            if not isinstance(n, dict):
                n = self._node_to_dict(n)
            my_scene = n.get("scene") or parent_scene or "web"
            n["scene"] = my_scene
            n["children"] = self._inherit_scene(n.get("children") or [], my_scene)
            out.append(n)
        return out

    def _mark_all_visible(self, nodes: List[Dict[str, Any]]):
        out = []
        for n in (nodes or []):
            if not isinstance(n, dict):
                n = self._node_to_dict(n)
            n["visible"] = True
            if n.get("children"):
                n["children"] = self._mark_all_visible(n["children"])
            out.append(n)
        return out

    def _groups_to_xmlids(self, groups_rec) -> set[str]:
        try:
            mapping = groups_rec.get_external_id()
            return {x for x in mapping.values() if x}
        except Exception:
            imd = self.su_env["ir.model.data"].search(
                [("model", "=", "res.groups"), ("res_id", "in", groups_rec.ids)]
            )
            return {f"{d.module}.{d.name}" for d in imd}

    @staticmethod
    def _groups_intersection_empty(required_xmlids: Iterable[str], user_xmlids: Iterable[str]) -> bool:
        return set(required_xmlids).isdisjoint(set(user_xmlids))

    @staticmethod
    def _ids_intersection_empty(required_ids: Iterable[int], user_ids: Iterable[int]) -> bool:
        return set(required_ids).isdisjoint(set(user_ids))

    @staticmethod
    def _nav_fingerprint(cfg_version: Any, scene: Any, groups_xmlids: Iterable[str]) -> str:
        base = {
            "cfg": int(cfg_version or 1),
            "scene": scene,
            "groups": sorted(set(groups_xmlids or [])),
        }
        raw = json.dumps(base, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

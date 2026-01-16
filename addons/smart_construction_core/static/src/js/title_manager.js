/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const mainComponents = registry.category("main_components");
const BRAND_TITLE = "智能施工";
const BRAND_ICON = "/smart_construction_core/static/png/系统图标(1).png";

class TitleManager extends Component {
  static template = "smart_construction_core.TitleManager";
  static props = {};

  setup() {
    const actionService = useService("action");
    if (actionService.__sc_title_patched) return;

    let lastTitle = "";

    const applyTitle = (name) => {
      const next = name ? `${name} · ${BRAND_TITLE}` : BRAND_TITLE;
      lastTitle = next;
      if (document.title !== next) document.title = next;
    };

    const ensureFavicon = () => {
      const links = document.querySelectorAll(
        "link[rel~=\"icon\"], link[rel=\"shortcut icon\"], link[rel=\"apple-touch-icon\"]"
      );
      links.forEach((link) => link.remove());
      const link = document.createElement("link");
      link.setAttribute("rel", "icon");
      link.setAttribute("type", "image/png");
      link.setAttribute("href", BRAND_ICON);
      const apple = document.createElement("link");
      apple.setAttribute("rel", "apple-touch-icon");
      apple.setAttribute("href", BRAND_ICON);
      document.head.appendChild(link);
      document.head.appendChild(apple);
    };

    const originalDoAction = actionService.doAction.bind(actionService);
    actionService.doAction = async (...args) => {
      const actionArg = args[0];
      const result = await originalDoAction(...args);
      applyTitle(resolveTitleFromAction(actionArg, result, actionService));
      window.setTimeout(() => applyTitle(resolveTitleFromAction(actionArg, result, actionService)), 50);
      return result;
    };

    const titleEl = document.querySelector("title");
    if (titleEl) {
      const observer = new MutationObserver(() => {
        if (lastTitle && document.title !== lastTitle) {
          document.title = lastTitle;
        }
        ensureFavicon();
      });
      observer.observe(titleEl, { childList: true });
    }

    actionService.__sc_title_patched = true;

    // Initial title sync for first load.
    applyTitle(resolveTitleFromAction(null, null, actionService));
    ensureFavicon();
  }
}

mainComponents.add("sc_title_manager", { Component: TitleManager });

function resolveTitleFromAction(actionArg, result, actionService) {
  return (
    resolveActionName(actionArg) ||
    resolveActionName(result && result.action) ||
    resolveActionName(actionService && actionService.currentAction) ||
    resolveActionName(actionService && actionService.currentController && actionService.currentController.action) ||
    ""
  );
}

function resolveActionName(action) {
  if (!action) return "";
  if (typeof action === "string") return "";
  if (typeof action === "number") return "";
  if (typeof action === "object" && action.name) return action.name;
  return "";
}

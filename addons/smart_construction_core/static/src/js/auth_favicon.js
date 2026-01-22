/** @odoo-module **/

const BRAND_ICON = "/smart_construction_core/static/png/system-icon-1.png";

const ensureFavicon = () => {
  const links = document.querySelectorAll(
    'link[rel~="icon"], link[rel="shortcut icon"], link[rel="apple-touch-icon"]'
  );
  links.forEach((link) => link.remove());

  const icon = document.createElement("link");
  icon.setAttribute("rel", "icon");
  icon.setAttribute("type", "image/png");
  icon.setAttribute("href", BRAND_ICON);
  document.head.appendChild(icon);

  const apple = document.createElement("link");
  apple.setAttribute("rel", "apple-touch-icon");
  apple.setAttribute("href", BRAND_ICON);
  document.head.appendChild(apple);

  const shortcut = document.createElement("link");
  shortcut.setAttribute("rel", "shortcut icon");
  shortcut.setAttribute("type", "image/png");
  shortcut.setAttribute("href", BRAND_ICON);
  document.head.appendChild(shortcut);
};

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", ensureFavicon);
} else {
  ensureFavicon();
}

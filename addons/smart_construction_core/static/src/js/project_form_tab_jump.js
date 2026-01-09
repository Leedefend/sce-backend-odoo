/** @odoo-module **/

const TAB_BUTTON_SELECTOR = ".sc-project-tab-jump";
const CONTAINER_SELECTOR = ".o_sc_project_overview";
const MODEL_NAME = "project.project";

function openNotebookTab(button) {
    const container = button.closest(CONTAINER_SELECTOR);
    if (!container || container.dataset.model !== MODEL_NAME) {
        return;
    }
    const tabName = button.dataset.tab;
    if (!tabName) {
        return;
    }
    const formView = button.closest(".o_form_view");
    if (!formView) {
        return;
    }
    const notebook = formView.querySelector(".o_notebook");
    if (!notebook) {
        return;
    }

    const selectors = [
        `[data-name="${tabName}"]`,
        `[data-tab="${tabName}"]`,
        `[data-bs-target="#${tabName}"]`,
        `[href="#${tabName}"]`,
        `[aria-controls="${tabName}"]`,
    ];
    for (const selector of selectors) {
        const tabLink = notebook.querySelector(selector);
        if (tabLink) {
            tabLink.click();
            return;
        }
    }

    const targetPane = notebook.querySelector(
        `.tab-pane[data-tab="${tabName}"], .tab-pane[data-name="${tabName}"]`
    );
    if (!targetPane || !targetPane.id) {
        return;
    }
    const paneSelectors = [
        `[aria-controls="${targetPane.id}"]`,
        `[href="#${targetPane.id}"]`,
        `[data-bs-target="#${targetPane.id}"]`,
    ];
    for (const selector of paneSelectors) {
        const tabLink = notebook.querySelector(selector);
        if (tabLink) {
            tabLink.click();
            return;
        }
    }
}

function handleClick(event) {
    const button = event.target.closest(TAB_BUTTON_SELECTOR);
    if (!button) {
        return;
    }
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
    openNotebookTab(button);
}

document.addEventListener("click", handleClick, true);

document.addEventListener(
    "keydown",
    (event) => {
        if (event.key !== "Enter" && event.key !== " ") {
            return;
        }
        const button = event.target.closest(TAB_BUTTON_SELECTOR);
        if (!button) {
            return;
        }
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();
        openNotebookTab(button);
    },
    true
);

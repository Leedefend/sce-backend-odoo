(function () {
  "use strict";

  const root = (window.scPortal = window.scPortal || {});

  function jsonRequest(url, payload) {
    return fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload || {}),
    }).then((res) => res.json());
  }

  function getJson(url) {
    return fetch(url, {credentials: "same-origin"}).then((res) => res.json());
  }

  function intent(intentName, params) {
    return jsonRequest("/api/v1/intent", {
      intent: intentName,
      params: params || {},
    });
  }

  function listProjects() {
    return intent("api.data", {
      op: "list",
      model: "project.project",
      fields: ["id", "name", "lifecycle_state"],
      order: "id desc",
      limit: 200,
    });
  }

  function getProjectCapabilities(projectId) {
    return getJson(`/api/meta/project_capabilities?project_id=${projectId}`);
  }

  function getPortalContract(route) {
    const encoded = encodeURIComponent(route || "/portal/lifecycle");
    return getJson(`/api/portal/contract?route=${encoded}`);
  }

  function getCapabilityMatrix() {
    return getJson("/api/contract/capability_matrix");
  }

  function getPortalDashboard() {
    return getJson("/api/contract/portal_dashboard");
  }

  function getPortalExecuteButton(params) {
    const query = new URLSearchParams(params || {}).toString();
    const url = query ? `/api/contract/portal_execute_button?${query}` : "/api/contract/portal_execute_button";
    return getJson(url);
  }

  function executePortalButton(payload) {
    return jsonRequest("/api/portal/execute_button", payload);
  }

  root.api = {
    intent,
    listProjects,
    getProjectCapabilities,
    getPortalContract,
    getCapabilityMatrix,
    getPortalDashboard,
    getPortalExecuteButton,
    executePortalButton,
  };
})();

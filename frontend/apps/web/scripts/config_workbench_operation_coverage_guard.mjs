import {
  CONFIG_WORKBENCH_OPERATION_COVERAGE,
  validateConfigWorkbenchOperationCoverage,
} from "./lib/config_workbench_operation_coverage.mjs";

validateConfigWorkbenchOperationCoverage();

console.log(JSON.stringify({
  ok: true,
  schema_version: "config_workbench_operation_coverage_guard.v1",
  journeys: CONFIG_WORKBENCH_OPERATION_COVERAGE.journeys.length,
  actions: CONFIG_WORKBENCH_OPERATION_COVERAGE.actions.length,
  assertions: CONFIG_WORKBENCH_OPERATION_COVERAGE.assertions.length,
  screenshots: CONFIG_WORKBENCH_OPERATION_COVERAGE.screenshotKeys.length,
  product_usability_tasks: CONFIG_WORKBENCH_OPERATION_COVERAGE.productUsabilityTasks.length,
  product_usability_dimensions: CONFIG_WORKBENCH_OPERATION_COVERAGE.productUsabilityDimensions.length,
  professional_dimensions: CONFIG_WORKBENCH_OPERATION_COVERAGE.professionalDimensions.length,
}));

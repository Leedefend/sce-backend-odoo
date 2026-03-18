type SectionInput = {
  showQuickFilters: boolean;
  showSavedFilters: boolean;
  showGroupBy: boolean;
  showFocus: boolean;
  showStrictAlert: boolean;
  showGroupSummary: boolean;
  showQuickActions: boolean;
  showHud: boolean;
};

export function resolveActionPageSections(input: SectionInput) {
  return {
    quickFilters: input.showQuickFilters,
    savedFilters: input.showSavedFilters,
    groupBy: input.showGroupBy,
    focus: input.showFocus,
    strictAlert: input.showStrictAlert,
    groupSummary: input.showGroupSummary,
    quickActions: input.showQuickActions,
    hud: input.showHud,
  };
}


type SectionEnabled = (key: string, defaultValue?: boolean) => boolean;
type SectionTagIs = (key: string, expectedTag: string) => boolean;
type SectionStyle = (key: string) => Record<string, string>;

type UseActionViewSectionRuntimeOptions = {
  pageSectionEnabled: SectionEnabled;
  pageSectionTagIs: SectionTagIs;
  pageSectionStyle: SectionStyle;
};

export function useActionViewSectionRuntime(options: UseActionViewSectionRuntimeOptions) {
  function isSectionVisible(
    key: string,
    input: {
      defaultEnabled?: boolean;
      tag: string;
      vmVisible?: boolean;
    },
  ): boolean {
    const defaultEnabled = typeof input.defaultEnabled === 'boolean' ? input.defaultEnabled : true;
    const vmVisible = typeof input.vmVisible === 'boolean' ? input.vmVisible : true;
    return vmVisible && options.pageSectionEnabled(key, defaultEnabled) && options.pageSectionTagIs(key, input.tag);
  }

  function getSectionStyle(key: string): Record<string, string> {
    return options.pageSectionStyle(key);
  }

  return {
    isSectionVisible,
    getSectionStyle,
  };
}


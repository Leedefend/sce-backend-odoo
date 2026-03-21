export type TemplateSectionKind = 'default' | 'header' | 'sheet' | 'group' | 'notebook' | 'page';

export type TemplateSectionInput = {
  title: string;
  kind: TemplateSectionKind;
};

export type TemplateSectionPresentation = {
  title: string;
  hint: string;
  tone: 'core' | 'advanced';
  isAdvanced: boolean;
};

export type ResolveTemplateSectionPresentationOptions = {
  projectCreateMode: boolean;
};

export function resolveTemplateSectionPresentation(
  section: TemplateSectionInput,
  options: ResolveTemplateSectionPresentationOptions,
): TemplateSectionPresentation {
  if (!options.projectCreateMode) {
    return {
      title: section.title,
      hint: '',
      tone: 'core',
      isAdvanced: false,
    };
  }

  const rawTitle = String(section.title || '').trim();
  const lowerTitle = rawTitle.toLowerCase();

  let title = rawTitle || '信息分组';
  if (lowerTitle.includes('高级')) {
    title = '更多信息（可选）';
  } else if (section.kind === 'default' || lowerTitle.includes('核心') || lowerTitle.includes('主体')) {
    title = '核心信息';
  }

  const isAdvanced = title === '更多信息（可选）';
  return {
    title,
    hint: title === '核心信息' ? '完成项目创建所需的最少信息' : '',
    tone: isAdvanced ? 'advanced' : 'core',
    isAdvanced,
  };
}

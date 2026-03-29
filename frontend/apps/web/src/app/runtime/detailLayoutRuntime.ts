import { resolveTemplateSectionPresentation } from '../../components/template/sectionPresentation.mapper';
import type { DetailSectionView, DetailShellView } from '../../components/template/detailLayout.types';
import type { FormSectionFieldSchema } from '../../components/template/formSection.types';

export type LayoutKind = 'default' | 'header' | 'sheet' | 'group' | 'notebook' | 'page';

export type LayoutNodeView = {
  key: string;
  kind: 'header' | 'sheet' | 'group' | 'notebook' | 'page' | 'field';
  name: string;
  label: string;
  readonly: boolean;
  required: boolean;
};

export type LayoutSectionView = {
  key: string;
  title: string;
  kind: LayoutKind;
  fields: LayoutNodeView[];
};

function resolveSectionShellClass(section: LayoutSectionView) {
  if (section.kind === 'sheet') return 'contract-form-shell--sheet';
  if (section.kind === 'group') return 'contract-form-shell--group';
  if (section.kind === 'page' || section.kind === 'notebook') return 'contract-form-shell--page';
  return 'contract-form-shell--default';
}

function resolveSectionEyebrow(section: LayoutSectionView, preferNativeFormSurface: boolean) {
  if (preferNativeFormSurface) {
    if (section.kind === 'group') return '分组';
    if (section.kind === 'page') return '页签';
    if (section.kind === 'notebook') return '页签容器';
    return '';
  }
  if (section.kind === 'sheet') return '主体';
  if (section.kind === 'group') return '分组';
  if (section.kind === 'page') return '页签';
  if (section.kind === 'notebook') return '页签容器';
  return '表单';
}

function resolveSectionSummary(
  section: LayoutSectionView,
  visibleFieldCount: number,
  preferNativeFormSurface: boolean,
) {
  if (preferNativeFormSurface) return '';
  if (visibleFieldCount <= 0) return '';
  return `${visibleFieldCount} 个字段`;
}

function resolveDetailShellClass(kind: LayoutKind) {
  if (kind === 'sheet') return 'contract-detail-shell--sheet';
  if (kind === 'page' || kind === 'notebook') return 'contract-detail-shell--page';
  return 'contract-detail-shell--default';
}

function resolveDetailShellEyebrow(kind: LayoutKind) {
  if (kind === 'sheet') return '主体';
  if (kind === 'page') return '页签';
  if (kind === 'notebook') return '页签容器';
  return '';
}

export function buildDetailSectionViews(options: {
  layoutSections: LayoutSectionView[];
  visibleSectionFieldCount: (section: LayoutSectionView) => number;
  buildSectionFields: (section: LayoutSectionView) => FormSectionFieldSchema[];
  preferNativeFormSurface: boolean;
  projectCreateMode: boolean;
}): DetailSectionView[] {
  const {
    layoutSections,
    visibleSectionFieldCount,
    buildSectionFields,
    preferNativeFormSurface,
    projectCreateMode,
  } = options;

  return layoutSections.map((section) => {
    const presentation = resolveTemplateSectionPresentation(section, { projectCreateMode });
    return {
      key: section.key,
      title: presentation.title,
      hint: presentation.hint,
      tone: presentation.tone,
      isAdvanced: presentation.isAdvanced,
      shellClass: resolveSectionShellClass(section),
      eyebrow: resolveSectionEyebrow(section, preferNativeFormSurface),
      summary: resolveSectionSummary(section, visibleSectionFieldCount(section), preferNativeFormSurface),
      fields: buildSectionFields(section),
    };
  });
}

export function buildDetailShellViews(options: {
  layoutSections: LayoutSectionView[];
  templateSections: DetailSectionView[];
}): DetailShellView[] {
  const { layoutSections, templateSections } = options;
  const shells: DetailShellView[] = [];
  let current: DetailShellView | null = null;

  const pushShell = () => {
    if (current && current.sections.length) shells.push(current);
    current = null;
  };

  for (let index = 0; index < templateSections.length; index += 1) {
    const section = templateSections[index];
    const layout = layoutSections[index];
    const kind = layout?.kind || 'default';
    const startsContainer = kind === 'sheet' || kind === 'page' || kind === 'notebook' || kind === 'default';
    if (!current || startsContainer) {
      pushShell();
      current = {
        key: `detail_shell_${section.key}`,
        title: kind === 'default' ? '' : section.title,
        kind,
        shellClass: resolveDetailShellClass(kind),
        eyebrow: resolveDetailShellEyebrow(kind),
        summary: '',
        sections: [],
      };
    }
    current.sections.push({
      ...section,
      eyebrow: kind === 'group' ? section.eyebrow : '',
      summary: current.sections.length > 0 ? section.summary : '',
      title: kind === 'sheet' && current.sections.length === 0 && current.title ? '' : section.title,
    });
  }

  pushShell();
  return shells;
}

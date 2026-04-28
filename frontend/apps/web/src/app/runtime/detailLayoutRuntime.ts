import { resolveTemplateSectionPresentation } from '../../components/template/sectionPresentation.mapper';
import type { DetailSectionView, DetailShellView } from '../../components/template/detailLayout.types';
import type { FormSectionFieldSchema } from '../../components/template/formSection.types';
import type { RenderProfile } from '../contractPolicies';

export type LayoutKind = 'default' | 'header' | 'sheet' | 'group' | 'notebook' | 'page';

function normalizeRenderProfile(value: unknown, fallback: RenderProfile): RenderProfile {
  return value === 'create' || value === 'edit' || value === 'readonly' ? value : fallback;
}

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
  columns?: 1 | 2;
  fields: LayoutNodeView[];
};

export type LayoutTreeSectionView = {
  key: string;
  title: string;
  kind: LayoutKind;
  columns?: 1 | 2;
  fields: LayoutNodeView[];
  children: LayoutTreeSectionView[];
};

function normalizeSectionColumns(columnsRaw: unknown): 1 | 2 {
  return Number(columnsRaw) === 1 ? 1 : 2;
}

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
  renderProfile: RenderProfile,
) {
  if (renderProfile === 'readonly') return '';
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
  renderProfile?: RenderProfile;
}): DetailSectionView[] {
  const {
    layoutSections,
    visibleSectionFieldCount,
    buildSectionFields,
    preferNativeFormSurface,
    projectCreateMode,
    renderProfile,
  } = options;
  const resolvedRenderProfile = normalizeRenderProfile(renderProfile, projectCreateMode ? 'create' : 'edit');

  return layoutSections.map((section) => {
    const presentation = resolveTemplateSectionPresentation(section, { projectCreateMode });
    return {
      key: section.key,
      title: presentation.title,
      hint: presentation.hint,
      tone: presentation.tone,
      isAdvanced: presentation.isAdvanced,
      columns: normalizeSectionColumns(section.columns),
      shellClass: resolveSectionShellClass(section),
      eyebrow: resolveSectionEyebrow(section, preferNativeFormSurface),
      summary: resolveSectionSummary(section, visibleSectionFieldCount(section), preferNativeFormSurface, resolvedRenderProfile),
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
  let notebookShell: DetailShellView | null = null;
  let activeNotebookTab: DetailShellView['tabs'][number] | null = null;

  const pushShell = () => {
    if (current && current.sections.length) shells.push(current);
    current = null;
  };
  const pushNotebookShell = () => {
    if (notebookShell && notebookShell.tabs?.length) shells.push(notebookShell);
    notebookShell = null;
    activeNotebookTab = null;
  };

  const tabLabel = (rawLabel: string): string => String(rawLabel || '').trim() || '信息页签';

  const nestedSection = (section: DetailSectionView, kind: LayoutKind, shell: DetailShellView | null): DetailSectionView => ({
    ...section,
    eyebrow: kind === 'group' ? section.eyebrow : '',
    summary: shell && shell.sections.length > 0 ? section.summary : '',
    title: kind === 'sheet' && shell && shell.sections.length === 0 && shell.title ? '' : section.title,
  });

  for (let index = 0; index < templateSections.length; index += 1) {
    const section = templateSections[index];
    const layout = layoutSections[index];
    const kind = layout?.kind || 'default';
    if (kind === 'notebook') {
      pushShell();
      pushNotebookShell();
      notebookShell = {
        key: `detail_shell_${section.key}`,
        title: section.title,
        kind,
        shellClass: resolveDetailShellClass(kind),
        eyebrow: resolveDetailShellEyebrow(kind),
        summary: '',
        sections: [],
        tabs: [],
      };
      activeNotebookTab = null;
      continue;
    }
    if (kind === 'page' && notebookShell) {
      const label = tabLabel(section.title);
      activeNotebookTab = {
        key: section.key,
        label,
        summary: section.summary,
        sections: [{ ...section, title: '' }],
      };
      notebookShell.tabs?.push(activeNotebookTab);
      continue;
    }
    if (notebookShell && activeNotebookTab) {
      activeNotebookTab.sections.push(nestedSection(section, kind, null));
      continue;
    }
    pushNotebookShell();
    const startsContainer = kind === 'sheet' || kind === 'page';
    if (!current || startsContainer) {
      pushShell();
      current = {
        key: `detail_shell_${section.key}`,
        title: kind === 'default' ? (current?.title || '') : section.title,
        kind,
        shellClass: resolveDetailShellClass(kind),
        eyebrow: resolveDetailShellEyebrow(kind),
        summary: '',
        sections: [],
      };
    }
    current.sections.push(nestedSection(section, kind, current));
  }

  pushShell();
  pushNotebookShell();
  return shells;
}

function createDetailSectionView(options: {
  section: LayoutTreeSectionView;
  visibleSectionFieldCount: (section: LayoutTreeSectionView) => number;
  buildSectionFields: (section: LayoutTreeSectionView) => FormSectionFieldSchema[];
  preferNativeFormSurface: boolean;
  projectCreateMode: boolean;
  renderProfile: RenderProfile;
  titleOverride?: string;
}): DetailSectionView {
  const {
    section,
    visibleSectionFieldCount,
    buildSectionFields,
    preferNativeFormSurface,
    projectCreateMode,
    renderProfile,
    titleOverride,
  } = options;
  const presentation = resolveTemplateSectionPresentation(section, { projectCreateMode });
  return {
    key: section.key,
    title: titleOverride ?? presentation.title,
    hint: presentation.hint,
    tone: presentation.tone,
    isAdvanced: presentation.isAdvanced,
    columns: normalizeSectionColumns(section.columns),
    shellClass: resolveSectionShellClass(section),
    eyebrow: resolveSectionEyebrow(section, preferNativeFormSurface),
    summary: resolveSectionSummary(section, visibleSectionFieldCount(section), preferNativeFormSurface, renderProfile),
    fields: buildSectionFields(section),
  };
}

function buildNestedSections(options: {
  nodes: LayoutTreeSectionView[];
  visibleSectionFieldCount: (section: LayoutTreeSectionView) => number;
  buildSectionFields: (section: LayoutTreeSectionView) => FormSectionFieldSchema[];
  preferNativeFormSurface: boolean;
  projectCreateMode: boolean;
  renderProfile: RenderProfile;
}): DetailSectionView[] {
  const {
    nodes,
    visibleSectionFieldCount,
    buildSectionFields,
    preferNativeFormSurface,
    projectCreateMode,
    renderProfile,
  } = options;
  const sections: DetailSectionView[] = [];
  const hasRenderableChildren = (node: LayoutTreeSectionView): boolean => node.children.some(
    (child) => child.kind !== 'notebook' && (child.fields.length > 0 || hasRenderableChildren(child)),
  );
  for (const node of nodes) {
    if (node.kind === 'notebook') continue;
    const includeSelf = node.fields.length > 0 || (node.kind === 'group' && hasRenderableChildren(node));
    if (includeSelf) {
      sections.push(createDetailSectionView({
        section: node,
        visibleSectionFieldCount,
        buildSectionFields,
        preferNativeFormSurface,
        projectCreateMode,
        renderProfile,
      }));
    }
    if (node.children.length) {
      sections.push(...buildNestedSections({
        nodes: node.children,
        visibleSectionFieldCount,
        buildSectionFields,
        preferNativeFormSurface,
        projectCreateMode,
        renderProfile,
      }));
    }
  }
  return sections;
}

function buildNotebookShell(node: LayoutTreeSectionView, options: {
  visibleSectionFieldCount: (section: LayoutTreeSectionView) => number;
  buildSectionFields: (section: LayoutTreeSectionView) => FormSectionFieldSchema[];
  preferNativeFormSurface: boolean;
  projectCreateMode: boolean;
  renderProfile: RenderProfile;
}): DetailShellView | null {
  const {
    visibleSectionFieldCount,
    buildSectionFields,
    preferNativeFormSurface,
    projectCreateMode,
    renderProfile,
  } = options;
  const collectPageNodesRecursively = (nodes: LayoutTreeSectionView[]): LayoutTreeSectionView[] => {
    const pages: LayoutTreeSectionView[] = [];
    for (const child of nodes) {
      if (child.kind === 'page') {
        pages.push(child);
        continue;
      }
      if (child.children.length) {
        pages.push(...collectPageNodesRecursively(child.children));
      }
    }
    return pages;
  };
  const explicitPages = node.children.filter((child) => child.kind === 'page');
  const recursivePages = explicitPages.length ? explicitPages : collectPageNodesRecursively(node.children);
  const fallbackPages = recursivePages.length ? recursivePages : node.children;
  const seenPageKeys = new Set<string>();
  const tabs = fallbackPages
    .filter((page) => {
      if (seenPageKeys.has(page.key)) return false;
      seenPageKeys.add(page.key);
      return true;
    })
    .map((page, pageIndex) => {
      const sections = buildContainerSections({
        container: page,
        visibleSectionFieldCount,
        buildSectionFields,
        preferNativeFormSurface,
        projectCreateMode,
        renderProfile,
      });
      const ensuredSections = sections.length
        ? sections
        : [{
          key: `${page.key}_placeholder`,
          title: page.title || `页签 ${pageIndex + 1}`,
          hint: '',
          tone: 'core' as const,
          isAdvanced: false,
          columns: 1 as const,
          shellClass: 'contract-form-shell--page',
          eyebrow: '',
          summary: '',
          fields: [],
        }];
      return {
        key: page.key,
        label: page.title || `页签 ${pageIndex + 1}`,
        summary: '',
        sections: ensuredSections,
      };
    });
  if (!tabs.length) return null;
  return {
    key: `detail_shell_${node.key}`,
    title: node.title,
    kind: node.kind,
    shellClass: resolveDetailShellClass(node.kind),
    eyebrow: resolveDetailShellEyebrow(node.kind),
    summary: '',
    sections: [],
    tabs,
  };
}

function collectNestedNotebookShells(nodes: LayoutTreeSectionView[], options: {
  visibleSectionFieldCount: (section: LayoutTreeSectionView) => number;
  buildSectionFields: (section: LayoutTreeSectionView) => FormSectionFieldSchema[];
  preferNativeFormSurface: boolean;
  projectCreateMode: boolean;
  renderProfile: RenderProfile;
}): DetailShellView[] {
  const shells: DetailShellView[] = [];
  for (const node of nodes) {
    if (node.kind === 'notebook') {
      const shell = buildNotebookShell(node, options);
      if (shell) shells.push(shell);
      continue;
    }
    if (node.children.length) {
      shells.push(...collectNestedNotebookShells(node.children, options));
    }
  }
  return shells;
}

function buildContainerSections(options: {
  container: LayoutTreeSectionView;
  visibleSectionFieldCount: (section: LayoutTreeSectionView) => number;
  buildSectionFields: (section: LayoutTreeSectionView) => FormSectionFieldSchema[];
  preferNativeFormSurface: boolean;
  projectCreateMode: boolean;
  renderProfile: RenderProfile;
}): DetailSectionView[] {
  const {
    container,
    visibleSectionFieldCount,
    buildSectionFields,
    preferNativeFormSurface,
    projectCreateMode,
    renderProfile,
  } = options;
  const sections: DetailSectionView[] = [];
  if (container.fields.length > 0) {
    sections.push(createDetailSectionView({
      section: container,
      visibleSectionFieldCount,
      buildSectionFields,
      preferNativeFormSurface,
      projectCreateMode,
      renderProfile,
    }));
  }
  if (container.children.length) {
    sections.push(...buildNestedSections({
      nodes: container.children,
      visibleSectionFieldCount,
      buildSectionFields,
      preferNativeFormSurface,
      projectCreateMode,
      renderProfile,
    }));
  }
  return sections;
}

export function buildDetailShellViewsFromTree(options: {
  layoutTrees: LayoutTreeSectionView[];
  visibleSectionFieldCount: (section: LayoutTreeSectionView) => number;
  buildSectionFields: (section: LayoutTreeSectionView) => FormSectionFieldSchema[];
  preferNativeFormSurface: boolean;
  projectCreateMode: boolean;
  renderProfile?: RenderProfile;
}): DetailShellView[] {
  const {
    layoutTrees,
    visibleSectionFieldCount,
    buildSectionFields,
    preferNativeFormSurface,
    projectCreateMode,
    renderProfile,
  } = options;
  const resolvedRenderProfile = normalizeRenderProfile(renderProfile, projectCreateMode ? 'create' : 'edit');
  const shells: DetailShellView[] = [];
  const shellOptions = {
    visibleSectionFieldCount,
    buildSectionFields,
    preferNativeFormSurface,
    projectCreateMode,
    renderProfile: resolvedRenderProfile,
  };
  const collectPageNodesRecursively = (nodes: LayoutTreeSectionView[]): LayoutTreeSectionView[] => {
    const pages: LayoutTreeSectionView[] = [];
    for (const node of nodes) {
      if (node.kind === 'page') {
        pages.push(node);
        continue;
      }
      if (node.children.length) {
        pages.push(...collectPageNodesRecursively(node.children));
      }
    }
    return pages;
  };
  const orphanPageNodes = collectPageNodesRecursively(layoutTrees);
  let orphanPagesConsumed = false;

  const buildSyntheticNotebookFromOrphanPages = (): DetailShellView | null => {
    if (!orphanPageNodes.length || orphanPagesConsumed) return null;
    const seenPageKeys = new Set<string>();
    const tabs = orphanPageNodes.filter((page) => {
      if (seenPageKeys.has(page.key)) return false;
      seenPageKeys.add(page.key);
      return true;
    }).map((page, pageIndex) => {
      const sections = buildContainerSections({
        container: page,
        visibleSectionFieldCount,
        buildSectionFields,
        preferNativeFormSurface,
        projectCreateMode,
        renderProfile: resolvedRenderProfile,
      });
      const ensuredSections = sections.length
        ? sections
        : [{
          key: `${page.key}_placeholder`,
          title: page.title || `页签 ${pageIndex + 1}`,
          hint: '',
          tone: 'core' as const,
          isAdvanced: false,
          columns: 1 as const,
          shellClass: 'contract-form-shell--page',
          eyebrow: '',
          summary: '',
          fields: [],
        }];
      return {
        key: page.key,
        label: page.title || `页签 ${pageIndex + 1}`,
        summary: '',
        sections: ensuredSections,
      };
    });
    orphanPagesConsumed = true;
    return {
      key: 'detail_shell_notebook_orphan_pages',
      title: '页签',
      kind: 'notebook',
      shellClass: resolveDetailShellClass('notebook'),
      eyebrow: resolveDetailShellEyebrow('notebook'),
      summary: '',
      sections: [],
      tabs,
    };
  };

  for (const node of layoutTrees) {
    if (node.kind === 'page') {
      continue;
    }
    if (node.kind === 'notebook') {
      let shell = buildNotebookShell(node, shellOptions);
      if (!shell) {
        shell = buildSyntheticNotebookFromOrphanPages();
      }
      if (!shell) continue;
      shells.push(shell);
      continue;
    }

    const sections = buildContainerSections({
      container: node,
      visibleSectionFieldCount,
      buildSectionFields,
      preferNativeFormSurface,
      projectCreateMode,
      renderProfile: resolvedRenderProfile,
    });
    if (!sections.length) continue;
    shells.push({
      key: `detail_shell_${node.key}`,
      title: node.kind === 'default' ? '' : node.title,
      kind: node.kind,
      shellClass: resolveDetailShellClass(node.kind),
      eyebrow: resolveDetailShellEyebrow(node.kind),
      summary: '',
      sections,
    });
    if (node.children.length) {
      shells.push(...collectNestedNotebookShells(node.children, shellOptions));
    }
  }

  if (!shells.some((shell) => Array.isArray(shell.tabs) && shell.tabs.length > 0)) {
    const synthetic = buildSyntheticNotebookFromOrphanPages();
    if (synthetic) shells.push(synthetic);
  }

  return shells;
}

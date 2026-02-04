export const SCENES = [
  {
    key: 'home',
    label: 'Workspace',
    route: '/',
    target: { route: '/' },
  },
  {
    key: 'workbench',
    label: 'Workbench',
    route: '/workbench',
    target: { route: '/workbench' },
  },
  {
    key: 'projects',
    label: 'Projects',
    route: '/projects',
    target: { model: 'project.project', view_mode: 'tree' },
  },
  {
    key: 'project-record',
    label: 'Project',
    route: '/projects/:id',
    target: { model: 'project.project', view_mode: 'form', record_id: ':id' },
  },
];

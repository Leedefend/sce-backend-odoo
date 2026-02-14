export const SCENES = [
  {
    key: 'home',
    label: '工作台',
    route: '/',
    target: { route: '/' },
  },
  {
    key: 'workbench',
    label: '工作区',
    route: '/workbench',
    target: { route: '/workbench' },
  },
  {
    key: 'projects',
    label: '项目',
    route: '/projects',
    target: { model: 'project.project', view_mode: 'tree' },
  },
  {
    key: 'project-record',
    label: '项目详情',
    route: '/projects/:id',
    target: { model: 'project.project', view_mode: 'form', record_id: ':id' },
  },
];

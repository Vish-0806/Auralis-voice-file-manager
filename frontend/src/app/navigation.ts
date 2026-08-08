export interface NavigationItem {
  id: string;
  label: string;
  path: string;
  icon?: string;
  section?: string;
  order?: number;
  disabled?: boolean;
  badge?: string | number;
  badgeVariant?: string;
  children?: NavigationItem[];
  requiredPermission?: string;
  external?: boolean;
}

export interface RouteMetadata {
  title: string;
  breadcrumbLabel: string;
  parentPath?: string;
  description?: string;
  layout?: 'app' | 'dashboard' | 'workspace';
}

export const navigationConfig: NavigationItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    path: '/dashboard',
    icon: 'bi-speedometer2',
    section: 'Main',
    order: 1
  },
  {
    id: 'assistant',
    label: 'Assistant',
    path: '/assistant',
    icon: 'bi-chat-left-dots',
    section: 'Features',
    order: 2
  },
  {
    id: 'files',
    label: 'File Manager',
    path: '/files',
    icon: 'bi-folder2-open',
    section: 'Features',
    order: 3
  },
  {
    id: 'workspace',
    label: 'Workspace',
    path: '/workspace',
    icon: 'bi-kanban',
    section: 'Features',
    order: 4
  },
  {
    id: 'settings',
    label: 'Settings',
    path: '/settings',
    icon: 'bi-gear',
    section: 'System',
    order: 5
  }
];

export const routeMetadataMap: Record<string, RouteMetadata> = {
  '/': {
    title: 'Dashboard',
    breadcrumbLabel: 'Dashboard',
    description: 'Overview of system status, tasks, and voice file manager metrics.',
    layout: 'dashboard'
  },
  '/dashboard': {
    title: 'Dashboard',
    breadcrumbLabel: 'Dashboard',
    description: 'Overview of system status, tasks, and voice file manager metrics.',
    layout: 'dashboard'
  },
  '/assistant': {
    title: 'Voice Assistant',
    breadcrumbLabel: 'Assistant',
    parentPath: '/',
    description: 'Interactive natural language conversational hub.',
    layout: 'app'
  },
  '/files': {
    title: 'File Manager',
    breadcrumbLabel: 'Files',
    parentPath: '/',
    description: 'Browse, manage, and search voice file directories.',
    layout: 'app'
  },
  '/workspace': {
    title: 'Workspace',
    breadcrumbLabel: 'Workspace',
    parentPath: '/',
    description: 'Active file buffers and document staging operations.',
    layout: 'workspace'
  },
  '/settings': {
    title: 'Settings',
    breadcrumbLabel: 'Settings',
    parentPath: '/',
    description: 'Configure interface theme settings and local API base URLs.',
    layout: 'app'
  }
};

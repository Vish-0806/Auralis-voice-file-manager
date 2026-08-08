import React, { createContext, useContext, useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from '../components/navigation/Sidebar';
import { TopBar } from '../components/navigation/TopBar';
import { NavItem } from '../components/navigation/NavItem';
import { Breadcrumbs } from '../components/navigation/Breadcrumbs';
import { PageHeader } from '../components/navigation/PageHeader';
import { Avatar } from '../components/common/Avatar';
import { IconButton } from '../components/common/IconButton';
import { ThemeToggle } from '../components/common/ThemeToggle';
import { navigationConfig, routeMetadataMap, RouteMetadata } from '../app/navigation';

export interface LayoutContextType {
  isMobileOpen: boolean;
  setMobileOpen: (open: boolean) => void;
  isCollapsed: boolean;
  setCollapsed: (collapsed: boolean) => void;
  actions: React.ReactNode | null;
  setActions: (actions: React.ReactNode | null) => void;
  description: string | null;
  setDescription: (desc: string | null) => void;
}

export const LayoutContext = createContext<LayoutContextType | undefined>(undefined);

export const useLayout = () => {
  const context = useContext(LayoutContext);
  if (!context) {
    throw new Error('useLayout must be used within a LayoutProvider');
  }
  return context;
};

export const AppLayout: React.FC = () => {
  const location = useLocation();
  const [isMobileOpen, setMobileOpen] = useState(false);
  const [isCollapsed, setCollapsed] = useState(false);
  const [actions, setActions] = useState<React.ReactNode | null>(null);
  const [description, setDescription] = useState<string | null>(null);

  useEffect(() => {
    setMobileOpen(false);
    setActions(null);
    setDescription(null);
  }, [location.pathname]);

  const currentPath = location.pathname;
  
  const metadata = routeMetadataMap[currentPath] || {
    title: 'Auralis',
    breadcrumbLabel: 'Page',
    description: ''
  };

  const breadcrumbsItems = [];
  let path: string | undefined = currentPath;
  while (path) {
    const meta: RouteMetadata | undefined = routeMetadataMap[path];
    if (meta) {
      breadcrumbsItems.unshift({
        label: meta.breadcrumbLabel,
        to: path === currentPath ? undefined : path
      });
      path = meta.parentPath;
    } else {
      break;
    }
  }

  if (currentPath !== '/' && currentPath !== '/dashboard' && !breadcrumbsItems.some(item => item.to === '/' || item.to === '/dashboard')) {
    breadcrumbsItems.unshift({ label: 'Dashboard', to: '/' });
  }

  return (
    <LayoutContext.Provider
      value={{
        isMobileOpen,
        setMobileOpen,
        isCollapsed,
        setCollapsed,
        actions,
        setActions,
        description,
        setDescription
      }}
    >
      <div className="app-layout">
        {isMobileOpen && (
          <div
            className="sidebar-backdrop d-lg-none"
            onClick={() => setMobileOpen(false)}
            aria-hidden="true"
          />
        )}

        <Sidebar
          brandName="Auralis"
          brandIcon="bi-soundwave"
          className={`app-sidebar ${isMobileOpen ? 'mobile-open' : ''} ${
            isCollapsed ? 'sidebar-collapsed' : ''
          }`}
        >
          {navigationConfig.map((item) => (
            <NavItem
              key={item.id}
              to={item.path}
              icon={item.icon}
              label={item.label}
              disabled={item.disabled}
              badge={item.badge}
              badgeVariant={item.badgeVariant}
            />
          ))}
        </Sidebar>

        <div className="app-main bg-light">
          <TopBar className="bg-white">
            <div className="d-flex align-items-center gap-2">
              <IconButton
                icon="bi-list"
                aria-label="Toggle Navigation Menu"
                className="d-lg-none"
                onClick={() => setMobileOpen(!isMobileOpen)}
              />
              <IconButton
                icon={isCollapsed ? 'bi-chevron-right' : 'bi-chevron-left'}
                aria-label={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
                className="d-none d-lg-inline-flex"
                onClick={() => setCollapsed(!isCollapsed)}
              />
              <span className="navbar-brand mb-0 h1 fs-5 fw-semibold text-secondary">
                Voice File Manager
              </span>
            </div>

            <div className="d-flex align-items-center gap-3">
              <ThemeToggle />
              <IconButton icon="bi-bell" aria-label="Notifications" />
              <Avatar alt="User profile" initials="A" size="sm" />
            </div>
          </TopBar>

          <main className="app-content">
            <PageHeader
              title={metadata.title}
              description={description || metadata.description}
              breadcrumbs={<Breadcrumbs items={breadcrumbsItems} />}
              actions={actions || undefined}
            />
            <div className="mt-3">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </LayoutContext.Provider>
  );
};

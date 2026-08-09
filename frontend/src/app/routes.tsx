import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { AppLayout } from '../layouts/AppLayout';
import { DashboardLayout } from '../layouts/DashboardLayout';
import { WorkspaceLayout } from '../layouts/WorkspaceLayout';
import { DashboardPage } from '../pages/dashboard/DashboardPage';
import { AssistantPage } from '../pages/assistant/AssistantPage';
import { FilesPage } from '../pages/files/FilesPage';
import { WorkspacePage } from '../pages/workspace/WorkspacePage';
import { SettingsPage } from '../pages/settings/SettingsPage';
import { NotFoundPage } from '../pages/not-found/NotFoundPage';
import { ErrorBoundary } from '../components/common/ErrorBoundary/ErrorBoundary';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        {/* Index route renders Dashboard layout directly */}
        <Route index element={
          <DashboardLayout>
            <ErrorBoundary>
              <DashboardPage />
            </ErrorBoundary>
          </DashboardLayout>
        } />
        
        {/* Dashboard nested layout boundary */}
        <Route path="dashboard" element={<DashboardLayout />}>
          <Route index element={
            <ErrorBoundary>
              <DashboardPage />
            </ErrorBoundary>
          } />
        </Route>
        
        {/* Workspace nested layout boundary */}
        <Route path="workspace" element={<WorkspaceLayout />}>
          <Route index element={
            <ErrorBoundary>
              <WorkspacePage />
            </ErrorBoundary>
          } />
        </Route>
        
        {/* General routes */}
        <Route path="assistant" element={
          <ErrorBoundary>
            <AssistantPage />
          </ErrorBoundary>
        } />
        <Route path="files" element={
          <ErrorBoundary>
            <FilesPage />
          </ErrorBoundary>
        } />
        <Route path="settings" element={
          <ErrorBoundary>
            <SettingsPage />
          </ErrorBoundary>
        } />
        
        {/* Unknown routes */}
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
};

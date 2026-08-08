import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { AppLayout } from '../layouts/AppLayout';
import { DashboardPage } from '../pages/dashboard/DashboardPage';
import { AssistantPage } from '../pages/assistant/AssistantPage';
import { FilesPage } from '../pages/files/FilesPage';
import { WorkspacePage } from '../pages/workspace/WorkspacePage';
import { SettingsPage } from '../pages/settings/SettingsPage';
import { NotFoundPage } from '../pages/not-found/NotFoundPage';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="assistant" element={<AssistantPage />} />
        <Route path="files" element={<FilesPage />} />
        <Route path="workspace" element={<WorkspacePage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
};

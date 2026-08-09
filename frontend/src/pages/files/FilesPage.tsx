import React, { useEffect } from 'react';
import { useLayout } from '../../layouts/AppLayout';
import { FileBrowser } from '../../features/workspace';

export const FilesPage: React.FC = () => {
  const { setDescription } = useLayout();

  useEffect(() => {
    setDescription('Browse, manage, and search voice file directories.');
  }, [setDescription]);

  return (
    <div className="container-fluid px-0">
      <FileBrowser />
    </div>
  );
};
export default FilesPage;

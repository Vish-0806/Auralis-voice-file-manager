import React, { useEffect } from 'react';
import { Providers } from './providers';
import { AppRoutes } from './routes';
import { syncService } from '../services/synchronization/synchronizationService';

export const App: React.FC = () => {
  useEffect(() => {
    syncService.start();
    return () => {
      syncService.stop();
    };
  }, []);

  return (
    <Providers>
      <AppRoutes />
    </Providers>
  );
};

import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import { AppLayout } from '../../src/layouts/AppLayout';
import { AppRoutes } from '../../src/app/routes';

describe('Layout Runtime Tests', () => {
  describe('AppLayout Component', () => {
    it('should render the header and sidebar correctly', () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <AppLayout />
        </MemoryRouter>
      );
      
      expect(screen.getByText('Voice File Manager')).toBeInTheDocument();
      expect(screen.getByText('Auralis')).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /dashboard/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /assistant/i })).toBeInTheDocument();
    });

    it('should toggle mobile menu when clicking menu button', () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <AppLayout />
        </MemoryRouter>
      );
      
      const toggleBtn = screen.getByLabelText('Toggle Navigation Menu');
      expect(toggleBtn).toBeInTheDocument();
      
      fireEvent.click(toggleBtn);
      const sidebar = screen.getByRole('complementary');
      expect(sidebar).toHaveClass('mobile-open');
    });

    it('should toggle desktop collapsed state when clicking collapse button', () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <AppLayout />
        </MemoryRouter>
      );
      
      const collapseBtn = screen.getByLabelText('Collapse Sidebar');
      expect(collapseBtn).toBeInTheDocument();
      
      fireEvent.click(collapseBtn);
      const sidebar = screen.getByRole('complementary');
      expect(sidebar).toHaveClass('sidebar-collapsed');
    });
  });

  describe('DashboardLayout & WorkspaceLayout Outlets', () => {
    it('should render DashboardLayout wrapper and nested outlets', () => {
      render(
        <MemoryRouter initialEntries={['/dashboard']}>
          <AppRoutes />
        </MemoryRouter>
      );
      
      expect(screen.getByText('Welcome to Auralis V2')).toBeInTheDocument();
    });

    it('should render WorkspaceLayout wrapper and nested outlets', () => {
      render(
        <MemoryRouter initialEntries={['/workspace']}>
          <AppRoutes />
        </MemoryRouter>
      );
      
      expect(screen.getByText('Workspace Operations')).toBeInTheDocument();
    });
  });
});

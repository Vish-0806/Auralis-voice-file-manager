import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import { NavItem, Sidebar, PageHeader } from '@/components';

describe('Navigation Components', () => {
  describe('NavItem Component', () => {
    it('should render correct navigation element', () => {
      render(
        <MemoryRouter>
          <NavItem to="/test" icon="bi-house" label="Home" badge={5} />
        </MemoryRouter>
      );
      const link = screen.getByRole('link', { name: /home/i });
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute('href', '/test');
      expect(screen.getByText('5')).toBeInTheDocument();
    });
  });

  describe('Sidebar Component', () => {
    it('should render Sidebar correctly', () => {
      render(
        <MemoryRouter>
          <Sidebar brandName="MyTest" brandIcon="bi-cpu">
            <div>Sidebar Child</div>
          </Sidebar>
        </MemoryRouter>
      );
      expect(screen.getByText('MyTest')).toBeInTheDocument();
      expect(screen.getByText('Sidebar Child')).toBeInTheDocument();
    });
  });

  describe('PageHeader Component', () => {
    it('should render Title, Description, and Actions', () => {
      render(
        <PageHeader
          title="Dashboard"
          description="Detailed statistics"
          actions={<button>Create New</button>}
        />
      );
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Detailed statistics')).toBeInTheDocument();
      expect(screen.getByText('Create New')).toBeInTheDocument();
    });
  });
});

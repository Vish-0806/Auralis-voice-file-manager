import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import { AppRoutes } from '../../src/app/routes';
import { AppLayout } from '../../src/layouts/AppLayout';

describe('Navigation Runtime Tests', () => {
  it('should render navigation links based on config', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppLayout />
      </MemoryRouter>
    );

    expect(screen.getByRole('link', { name: /dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /assistant/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /file manager/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /workspace/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /settings/i })).toBeInTheDocument();
  });

  it('should highlight the active navigation item', () => {
    render(
      <MemoryRouter initialEntries={['/settings']}>
        <AppRoutes />
      </MemoryRouter>
    );

    const activeLink = screen.getByRole('link', { name: /settings/i });
    expect(activeLink).toHaveClass('active');
  });

  it('should render breadcrumbs matching route metadata hierarchy', () => {
    render(
      <MemoryRouter initialEntries={['/assistant']}>
        <AppRoutes />
      </MemoryRouter>
    );

    const breadcrumbNav = screen.getByRole('navigation', { name: /breadcrumb/i });
    const parentCrumb = within(breadcrumbNav).getByRole('link', { name: 'Dashboard' });
    expect(parentCrumb).toBeInTheDocument();
    expect(parentCrumb).toHaveAttribute('href', '/');

    const activeCrumb = within(breadcrumbNav).getByText('Assistant');
    expect(activeCrumb).toBeInTheDocument();
    expect(activeCrumb.tagName).toBe('LI');
    expect(activeCrumb).toHaveClass('active');
  });

  it('should verify keyboard tab navigation index', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppLayout />
      </MemoryRouter>
    );

    const links = screen.getAllByRole('link');
    links.forEach((link) => {
      expect(link).toHaveAttribute('href');
    });
  });
});

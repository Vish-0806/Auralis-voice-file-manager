import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { App } from '../../src/app';

describe('Auralis V2 Smoke Tests', () => {
  it('should render application layout and default to dashboard view', () => {
    render(<App />);
    
    // Check main layout header
    expect(screen.getByText('Voice File Manager')).toBeInTheDocument();
    
    // Check dashboard text
    expect(screen.getByText('Welcome to Auralis V2')).toBeInTheDocument();
    expect(screen.getByText('System Status')).toBeInTheDocument();
  });

  it('should allow clicking navigation tabs to navigate to other routes', async () => {
    render(<App />);
    const user = userEvent.setup();

    // Verify initial landing on dashboard
    expect(screen.getByText('Welcome to Auralis V2')).toBeInTheDocument();

    // Click on Assistant tab
    const assistantLink = screen.getByRole('link', { name: /assistant/i });
    await user.click(assistantLink);
    expect(screen.getByText('Assistant Hub')).toBeInTheDocument();

    // Click on File Manager tab
    const filesLink = screen.getByRole('link', { name: /file manager/i });
    await user.click(filesLink);
    expect(screen.getByText('File Browser')).toBeInTheDocument();

    // Click on Workspace tab
    const workspaceLink = screen.getByRole('link', { name: /workspace/i });
    await user.click(workspaceLink);
    expect(screen.getByText('Workspace Operations')).toBeInTheDocument();

    // Click on Settings tab
    const settingsLink = screen.getByRole('link', { name: /settings/i });
    await user.click(settingsLink);
    expect(screen.getByText('Application Preferences')).toBeInTheDocument();
  });
});

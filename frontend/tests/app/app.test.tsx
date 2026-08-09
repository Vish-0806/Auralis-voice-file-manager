import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { App } from '../../src/app';

describe('Auralis V2 Smoke Tests', () => {
  it('should render application layout and default to dashboard view', async () => {
    render(<App />);
    
    // Check main layout header
    expect(await screen.findByText('Voice File Manager')).toBeInTheDocument();
    
    // Check dashboard text
    expect(await screen.findByText('Quick Access Shortcuts')).toBeInTheDocument();
    expect(await screen.findByText('Backend Service Status')).toBeInTheDocument();
  });

  it('should allow clicking navigation tabs to navigate to other routes', async () => {
    render(<App />);
    const user = userEvent.setup();

    // Verify initial landing on dashboard
    expect(screen.getByText('Quick Access Shortcuts')).toBeInTheDocument();

    // Click on Assistant tab
    const assistantLink = screen.getAllByRole('link', { name: /assistant/i })[0];
    await user.click(assistantLink);
    expect(screen.getByText('Assistant Hub')).toBeInTheDocument();

    // Click on File Manager tab
    const filesLink = screen.getAllByRole('link', { name: /file manager/i })[0];
    await user.click(filesLink);
    expect(screen.getByText('Sort by:')).toBeInTheDocument();

    // Click on Workspace tab
    const workspaceLink = screen.getAllByRole('link', { name: /workspace/i })[0];
    await user.click(workspaceLink);
    expect(screen.getByText('Directory Tree')).toBeInTheDocument();

    // Click on Settings tab
    const settingsLink = screen.getAllByRole('link', { name: /settings/i })[0];
    await user.click(settingsLink);
    expect(screen.getByText('Application Preferences')).toBeInTheDocument();
  });
});

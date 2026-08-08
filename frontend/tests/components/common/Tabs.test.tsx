import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Tabs } from '@/components';

describe('Tabs Component', () => {
  const mockTabs = [
    { key: 'tab1', label: 'Tab 1', content: <div>Content 1</div> },
    { key: 'tab2', label: 'Tab 2', content: <div>Content 2</div> }
  ];

  it('should render active tab content by default', () => {
    render(<Tabs items={mockTabs} />);
    expect(screen.getByText('Content 1')).toBeInTheDocument();
    expect(screen.queryByText('Content 2')).not.toBeInTheDocument();
  });

  it('should switch tab content on click', () => {
    render(<Tabs items={mockTabs} />);
    const tab2Button = screen.getByRole('tab', { name: 'Tab 2' });
    fireEvent.click(tab2Button);
    expect(screen.getByText('Content 2')).toBeInTheDocument();
    expect(screen.queryByText('Content 1')).not.toBeInTheDocument();
  });

  it('should support defaultActiveKey prop', () => {
    render(<Tabs items={mockTabs} defaultActiveKey="tab2" />);
    expect(screen.getByText('Content 2')).toBeInTheDocument();
    expect(screen.queryByText('Content 1')).not.toBeInTheDocument();
  });
});

import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Stack, Panel } from '@/components';

describe('Layout Components', () => {
  describe('Stack Component', () => {
    it('should render children and apply flex classes', () => {
      render(
        <Stack direction="row" gap={3} align="center" justify="between" data-testid="stack">
          <div>Item 1</div>
          <div>Item 2</div>
        </Stack>
      );
      const stack = screen.getByTestId('stack');
      expect(stack).toHaveClass('d-flex');
      expect(stack).toHaveClass('flex-row');
      expect(stack).toHaveClass('gap-3');
      expect(stack).toHaveClass('align-items-center');
      expect(stack).toHaveClass('justify-content-between');
    });
  });

  describe('Panel Component', () => {
    it('should render correct panel layout style', () => {
      render(
        <Panel bordered shadow="sm" padding={4} data-testid="panel">
          Panel content
        </Panel>
      );
      const panel = screen.getByTestId('panel');
      expect(panel).toHaveClass('bg-body');
      expect(panel).toHaveClass('border');
      expect(panel).toHaveClass('shadow-sm');
      expect(panel).toHaveClass('p-4');
    });
  });
});

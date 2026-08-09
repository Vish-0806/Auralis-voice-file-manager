import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import {
  VoiceControl,
  VoiceStatus,
  VoiceVisualizer,
  TranscriptPanel,
  ListenerControl,
  VoiceError
} from '../../src/voice/components';

describe('Voice UI Components Tests', () => {
  
  describe('VoiceControl Component', () => {
    it('should render idle state correctly', () => {
      const onStart = vi.fn();
      const onStop = vi.fn();
      render(
        <VoiceControl
          isListening={false}
          isProcessing={false}
          onStart={onStart}
          onStop={onStop}
        />
      );

      const btn = screen.getByRole('button', { name: /start listening/i });
      expect(btn).toBeInTheDocument();
      expect(btn).not.toBeDisabled();
      
      fireEvent.click(btn);
      expect(onStart).toHaveBeenCalledTimes(1);
    });

    it('should render listening state correctly', () => {
      const onStart = vi.fn();
      const onStop = vi.fn();
      render(
        <VoiceControl
          isListening={true}
          isProcessing={false}
          onStart={onStart}
          onStop={onStop}
        />
      );

      const btn = screen.getByRole('button', { name: /stop listening/i });
      expect(btn).toBeInTheDocument();
      expect(btn).toHaveClass('btn-danger');

      fireEvent.click(btn);
      expect(onStop).toHaveBeenCalledTimes(1);
    });

    it('should render processing state correctly and be disabled', () => {
      const onStart = vi.fn();
      render(
        <VoiceControl
          isListening={false}
          isProcessing={true}
          onStart={onStart}
          onStop={vi.fn()}
        />
      );

      const btn = screen.getByRole('button');
      expect(btn).toBeDisabled();
      expect(btn).toHaveAttribute('aria-busy', 'true');
      expect(screen.getByText('Processing...')).toBeInTheDocument();
    });

    it('should respect disabled prop', () => {
      render(
        <VoiceControl
          isListening={false}
          isProcessing={false}
          disabled={true}
          onStart={vi.fn()}
          onStop={vi.fn()}
        />
      );
      const btn = screen.getByRole('button');
      expect(btn).toBeDisabled();
    });
  });

  describe('VoiceStatus Component', () => {
    it('should render correct text and semantic aria live attributes for IDLE', () => {
      render(<VoiceStatus status="IDLE" />);
      const container = screen.getByRole('status');
      expect(container).toHaveAttribute('aria-live', 'polite');
      expect(screen.getByText('Ready')).toBeInTheDocument();
    });

    it('should render correct text for LISTENING', () => {
      render(<VoiceStatus status="LISTENING" />);
      expect(screen.getByText('Listening...')).toBeInTheDocument();
    });

    it('should render correct text for ERROR', () => {
      render(<VoiceStatus status="ERROR" />);
      expect(screen.getByText('Voice interaction failed')).toBeInTheDocument();
    });
  });

  describe('VoiceVisualizer Component', () => {
    it('should render 5 wave bars', () => {
      render(<VoiceVisualizer status="IDLE" />);
      const bars = screen.getAllByTestId(/voice-bar-/);
      expect(bars).toHaveLength(5);
    });

    it('should apply correct CSS classes for listening state', () => {
      render(<VoiceVisualizer status="LISTENING" />);
      const bar0 = screen.getByTestId('voice-bar-0');
      expect(bar0).toHaveClass('voice-bar-listening-0');
    });

    it('should apply correct CSS classes for processing state', () => {
      render(<VoiceVisualizer status="PROCESSING" />);
      const bar0 = screen.getByTestId('voice-bar-0');
      expect(bar0).toHaveClass('voice-bar-processing');
      expect(bar0).toHaveClass('voice-bar-processing-0');
    });
  });

  describe('TranscriptPanel Component', () => {
    it('should render empty state when no transcripts are present', () => {
      render(<TranscriptPanel />);
      expect(screen.getByText(/start speaking to see the transcript/i)).toBeInTheDocument();
    });

    it('should render partial and final transcript correctly', () => {
      render(
        <TranscriptPanel
          finalTranscript="create a folder"
          partialTranscript="named files"
        />
      );
      expect(screen.getByText(/create a folder/i)).toBeInTheDocument();
      expect(screen.getByText(/named files/i)).toBeInTheDocument();
    });

    it('should render command analysis details', () => {
      const result = {
        status: 'success',
        command: 'Create Archives folder',
        parsed_action: {
          action: 'create_folder',
          target: 'Archives'
        },
        message: 'Folder created successfully'
      };

      render(<TranscriptPanel latestResult={result} />);
      expect(screen.getByText('Command Analysis')).toBeInTheDocument();
      expect(screen.getByText('Create Archives folder')).toBeInTheDocument();
      expect(screen.getByText('create_folder ➔ Archives')).toBeInTheDocument();
      expect(screen.getByText('Folder created successfully')).toBeInTheDocument();
    });
  });

  describe('ListenerControl Component', () => {
    it('should render stopped state with start button', () => {
      const onStart = vi.fn();
      render(
        <ListenerControl
          isRunning={false}
          loading={false}
          onStart={onStart}
          onStop={vi.fn()}
          onRefresh={vi.fn()}
        />
      );

      expect(screen.getByTestId('listener-status-badge')).toHaveTextContent('Stopped');
      const startBtn = screen.getByRole('button', { name: /start/i });
      fireEvent.click(startBtn);
      expect(onStart).toHaveBeenCalledTimes(1);
    });

    it('should render running state with stop button', () => {
      const onStop = vi.fn();
      render(
        <ListenerControl
          isRunning={true}
          loading={false}
          onStart={vi.fn()}
          onStop={onStop}
          onRefresh={vi.fn()}
        />
      );

      expect(screen.getByTestId('listener-status-badge')).toHaveTextContent('Running');
      const stopBtn = screen.getByRole('button', { name: /stop/i });
      fireEvent.click(stopBtn);
      expect(onStop).toHaveBeenCalledTimes(1);
    });

    it('should disable buttons and trigger refresh when clicked', () => {
      const onRefresh = vi.fn();
      const { rerender } = render(
        <ListenerControl
          isRunning={true}
          loading={true}
          onStart={vi.fn()}
          onStop={vi.fn()}
          onRefresh={onRefresh}
        />
      );

      const stopBtn = screen.getByRole('button', { name: /stop/i });
      expect(stopBtn).toBeDisabled();

      const refreshBtn = screen.getByRole('button', { name: /refresh/i });
      expect(refreshBtn).toBeDisabled();

      // Re-render with loading = false to click and test trigger
      rerender(
        <ListenerControl
          isRunning={true}
          loading={false}
          onStart={vi.fn()}
          onStop={vi.fn()}
          onRefresh={onRefresh}
        />
      );

      expect(refreshBtn).not.toBeDisabled();
      fireEvent.click(refreshBtn);
      expect(onRefresh).toHaveBeenCalledTimes(1);
    });
  });

  describe('VoiceError Component', () => {
    it('should render error message and trigger close', () => {
      const onClear = vi.fn();
      const error = {
        type: 'permission_denied' as const,
        message: 'Mic permission was denied.'
      };

      render(<VoiceError error={error} onClear={onClear} />);
      expect(screen.getByText('Mic permission was denied.')).toBeInTheDocument();

      const closeBtn = screen.getByRole('button', { name: /close/i });
      fireEvent.click(closeBtn);
      expect(onClear).toHaveBeenCalledTimes(1);
    });
  });
});

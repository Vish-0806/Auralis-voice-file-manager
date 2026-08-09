import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useVoice, useVoiceListener } from '../../src/voice/hooks';
import { useVoiceStore } from '../../src/voice/state/voiceStore';
import { voiceController } from '../../src/voice/services/voiceController';

vi.mock('../../src/voice/services/voiceController', () => ({
  voiceController: {
    startListening: vi.fn(),
    stopListening: vi.fn(),
    startContinuousListener: vi.fn(),
    stopContinuousListener: vi.fn(),
    refreshListenerStatus: vi.fn(),
    checkPermission: vi.fn(),
  },
}));

describe('Voice Hooks Tests', () => {
  beforeEach(() => {
    act(() => {
      useVoiceStore.getState().reset();
    });
    vi.clearAllMocks();
  });

  describe('useVoice', () => {
    const VoiceTester = () => {
      const {
        status,
        transcript,
        isListening,
        isProcessing,
        startListening,
        stopListening,
        clearError,
        reset
      } = useVoice();

      return (
        <div>
          <span data-testid="status">{status}</span>
          <span data-testid="transcript">{transcript}</span>
          <span data-testid="isListening">{isListening ? 'yes' : 'no'}</span>
          <span data-testid="isProcessing">{isProcessing ? 'yes' : 'no'}</span>
          <button onClick={startListening} data-testid="start-btn">Start</button>
          <button onClick={stopListening} data-testid="stop-btn">Stop</button>
          <button onClick={clearError} data-testid="clear-btn">Clear</button>
          <button onClick={reset} data-testid="reset-btn">Reset</button>
        </div>
      );
    };

    it('should expose voice states and actions correctly', () => {
      render(<VoiceTester />);
      expect(screen.getByTestId('status')).toHaveTextContent('IDLE');
      expect(screen.getByTestId('isListening')).toHaveTextContent('no');

      // Click start
      fireEvent.click(screen.getByTestId('start-btn'));
      expect(voiceController.startListening).toHaveBeenCalledTimes(1);

      // Trigger state updates
      act(() => {
        useVoiceStore.getState().setVoiceStatus('LISTENING');
        useVoiceStore.getState().setTranscript('voice command');
      });

      expect(screen.getByTestId('status')).toHaveTextContent('LISTENING');
      expect(screen.getByTestId('transcript')).toHaveTextContent('voice command');
      expect(screen.getByTestId('isListening')).toHaveTextContent('yes');

      // Click stop
      fireEvent.click(screen.getByTestId('stop-btn'));
      expect(voiceController.stopListening).toHaveBeenCalledTimes(1);
    });
  });

  describe('useVoiceListener', () => {
    const ListenerTester = () => {
      const {
        listenerStatus,
        isRunning,
        loading,
        start,
        stop,
        refresh
      } = useVoiceListener();

      return (
        <div>
          <span data-testid="l-status">{listenerStatus}</span>
          <span data-testid="l-running">{isRunning ? 'yes' : 'no'}</span>
          <span data-testid="l-loading">{loading ? 'yes' : 'no'}</span>
          <button onClick={start} data-testid="start-btn">Start</button>
          <button onClick={stop} data-testid="stop-btn">Stop</button>
          <button onClick={refresh} data-testid="refresh-btn">Refresh</button>
        </div>
      );
    };

    it('should expose continuous listener state and trigger service actions', () => {
      render(<ListenerTester />);
      expect(screen.getByTestId('l-status')).toHaveTextContent('idle');
      expect(screen.getByTestId('l-running')).toHaveTextContent('no');

      // Click start
      fireEvent.click(screen.getByTestId('start-btn'));
      expect(voiceController.startContinuousListener).toHaveBeenCalledTimes(1);

      // Trigger state updates
      act(() => {
        useVoiceStore.getState().setListenerRunning(true);
        useVoiceStore.getState().setListenerStatus('running');
      });

      expect(screen.getByTestId('l-status')).toHaveTextContent('running');
      expect(screen.getByTestId('l-running')).toHaveTextContent('yes');

      // Click refresh
      fireEvent.click(screen.getByTestId('refresh-btn'));
      expect(voiceController.refreshListenerStatus).toHaveBeenCalledTimes(1);
    });
  });
});

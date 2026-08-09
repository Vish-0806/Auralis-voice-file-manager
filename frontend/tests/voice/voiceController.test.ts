import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { act } from 'react';
import { voiceController } from '../../src/voice/services/voiceController';
import { voiceService } from '../../src/services/api/voiceService';
import { useVoiceStore } from '../../src/voice/state/voiceStore';

// Mock voiceService
vi.mock('../../src/services/api/voiceService', () => ({
  voiceService: {
    listenVoice: vi.fn(),
    startListener: vi.fn(),
    stopListener: vi.fn(),
    getListenerStatus: vi.fn(),
  },
  default: {
    listenVoice: vi.fn(),
    startListener: vi.fn(),
    stopListener: vi.fn(),
    getListenerStatus: vi.fn(),
  }
}));

describe('voiceController Tests', () => {
  const originalMediaDevices = navigator.mediaDevices;

  beforeEach(() => {
    act(() => {
      useVoiceStore.getState().reset();
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    Object.defineProperty(navigator, 'mediaDevices', {
      writable: true,
      configurable: true,
      value: originalMediaDevices,
    });
  });

  it('should handle permission request successfully when user allows mic', async () => {
    const mockStream = {
      getTracks: () => [{ stop: vi.fn() }],
    };

    Object.defineProperty(navigator, 'mediaDevices', {
      writable: true,
      configurable: true,
      value: {
        getUserMedia: vi.fn().mockResolvedValue(mockStream),
      },
    });

    const success = await voiceController.checkPermission();
    expect(success).toBe(true);
    expect(useVoiceStore.getState().permissionStatus).toBe('granted');
    expect(useVoiceStore.getState().status).toBe('READY');
  });

  it('should handle permission request failure (denied)', async () => {
    const error = new Error('Permission denied');
    error.name = 'NotAllowedError';

    Object.defineProperty(navigator, 'mediaDevices', {
      writable: true,
      configurable: true,
      value: {
        getUserMedia: vi.fn().mockRejectedValue(error),
      },
    });

    const success = await voiceController.checkPermission();
    expect(success).toBe(false);
    expect(useVoiceStore.getState().permissionStatus).toBe('denied');
    expect(useVoiceStore.getState().status).toBe('ERROR');
    expect(useVoiceStore.getState().error?.type).toBe('permission_denied');
  });

  it('should handle unsupported mediaDevices gracefully', async () => {
    Object.defineProperty(navigator, 'mediaDevices', {
      writable: true,
      configurable: true,
      value: undefined,
    });

    const success = await voiceController.checkPermission();
    expect(success).toBe(false);
    expect(useVoiceStore.getState().permissionStatus).toBe('unavailable');
    expect(useVoiceStore.getState().error?.type).toBe('unsupported');
  });

  it('should handle startListening success', async () => {
    const mockStream = {
      getTracks: () => [{ stop: vi.fn() }],
    };
    Object.defineProperty(navigator, 'mediaDevices', {
      writable: true,
      configurable: true,
      value: {
        getUserMedia: vi.fn().mockResolvedValue(mockStream),
      },
    });

    vi.mocked(voiceService.listenVoice).mockResolvedValue({
      status: 'success',
      recognized_text: 'list files',
    });

    await voiceController.startListening();

    const state = useVoiceStore.getState();
    expect(state.status).toBe('COMPLETED');
    expect(state.finalTranscript).toBe('list files');
    expect(state.latestResult?.recognized_text).toBe('list files');
  });

  it('should handle startListening error from API', async () => {
    const mockStream = {
      getTracks: () => [{ stop: vi.fn() }],
    };
    Object.defineProperty(navigator, 'mediaDevices', {
      writable: true,
      configurable: true,
      value: {
        getUserMedia: vi.fn().mockResolvedValue(mockStream),
      },
    });

    vi.mocked(voiceService.listenVoice).mockRejectedValue(new Error('Network Error'));

    await voiceController.startListening();

    const state = useVoiceStore.getState();
    expect(state.status).toBe('ERROR');
    expect(state.error?.type).toBe('network');
    expect(state.error?.message).toContain('Network Error');
  });

  it('should handle continuous listener start success', async () => {
    vi.mocked(voiceService.startListener).mockResolvedValue({
      status: 'success',
      message: 'Listener started',
    });

    await voiceController.startContinuousListener();

    const state = useVoiceStore.getState();
    expect(state.listenerRunning).toBe(true);
    expect(state.listenerStatus).toBe('running');
  });

  it('should handle continuous listener start failure', async () => {
    vi.mocked(voiceService.startListener).mockRejectedValue(new Error('Internal server error'));

    await voiceController.startContinuousListener();

    const state = useVoiceStore.getState();
    expect(state.listenerRunning).toBe(false);
    expect(state.listenerStatus).toBe('error');
    expect(state.error?.message).toContain('Internal server error');
  });

  it('should handle continuous listener stop success', async () => {
    vi.mocked(voiceService.stopListener).mockResolvedValue({
      status: 'success',
      message: 'Listener stopped',
    });

    await voiceController.stopContinuousListener();

    const state = useVoiceStore.getState();
    expect(state.listenerRunning).toBe(false);
    expect(state.listenerStatus).toBe('stopped');
  });

  it('should handle continuous listener refresh', async () => {
    vi.mocked(voiceService.getListenerStatus).mockResolvedValue({
      running: true,
      status: 'running',
    });

    await voiceController.refreshListenerStatus();

    const state = useVoiceStore.getState();
    expect(state.listenerRunning).toBe(true);
    expect(state.listenerStatus).toBe('running');
  });
});

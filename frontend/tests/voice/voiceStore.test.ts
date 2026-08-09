import { describe, it, expect, beforeEach } from 'vitest';
import { act } from 'react';
import { useVoiceStore } from '../../src/voice/state/voiceStore';
import {
  selectVoiceStatus,
  selectPermissionStatus,
  selectListenerRunning,
  selectListenerStatus,
  selectVoiceTranscript,
  selectVoicePartialTranscript,
  selectVoiceFinalTranscript,
  selectVoiceProcessing,
  selectVoiceLatestResult,
  selectVoiceError,
  selectVoiceConnectionState,
} from '../../src/voice/state';

describe('Voice Store & Selectors Tests', () => {
  beforeEach(() => {
    act(() => {
      useVoiceStore.getState().reset();
    });
  });

  it('should initialize with correct default values', () => {
    const state = useVoiceStore.getState();
    expect(state.status).toBe('IDLE');
    expect(state.permissionStatus).toBe('prompt');
    expect(state.listenerRunning).toBe(false);
    expect(state.listenerStatus).toBe('idle');
    expect(state.transcript).toBe('');
    expect(state.partialTranscript).toBe('');
    expect(state.finalTranscript).toBe('');
    expect(state.processing).toBe(false);
    expect(state.latestResult).toBeNull();
    expect(state.error).toBeNull();
    expect(state.connectionState).toBe('DISCONNECTED');
  });

  it('should update states correctly through actions', () => {
    act(() => {
      useVoiceStore.getState().setVoiceStatus('LISTENING');
      useVoiceStore.getState().setPermissionStatus('granted');
      useVoiceStore.getState().setTranscript('hello world');
      useVoiceStore.getState().setPartialTranscript('hello');
      useVoiceStore.getState().setFinalTranscript('hello world');
      useVoiceStore.getState().setProcessing(true);
      useVoiceStore.getState().setListenerRunning(true);
      useVoiceStore.getState().setListenerStatus('running');
      useVoiceStore.getState().setVoiceResult({ status: 'success', recognized_text: 'hello world' });
      useVoiceStore.getState().setError({ type: 'permission_denied', message: 'mic blocked' });
      useVoiceStore.getState().setConnectionState('CONNECTED');
    });

    const state = useVoiceStore.getState();
    expect(state.status).toBe('LISTENING');
    expect(state.permissionStatus).toBe('granted');
    expect(state.transcript).toBe('hello world');
    expect(state.partialTranscript).toBe('hello');
    expect(state.finalTranscript).toBe('hello world');
    expect(state.processing).toBe(true);
    expect(state.listenerRunning).toBe(true);
    expect(state.listenerStatus).toBe('running');
    expect(state.latestResult).toEqual({ status: 'success', recognized_text: 'hello world' });
    expect(state.error).toEqual({ type: 'permission_denied', message: 'mic blocked' });
    expect(state.connectionState).toBe('CONNECTED');
  });

  it('should clear error state correctly', () => {
    act(() => {
      useVoiceStore.getState().setError({ type: 'network', message: 'no connection' });
    });
    expect(useVoiceStore.getState().error).toBeDefined();

    act(() => {
      useVoiceStore.getState().clearError();
    });
    expect(useVoiceStore.getState().error).toBeNull();
  });

  it('should reset to initial state correctly', () => {
    act(() => {
      useVoiceStore.getState().setVoiceStatus('COMPLETED');
      useVoiceStore.getState().setProcessing(true);
      useVoiceStore.getState().reset();
    });

    const state = useVoiceStore.getState();
    expect(state.status).toBe('IDLE');
    expect(state.processing).toBe(false);
  });

  it('should return correct values through selectors', () => {
    act(() => {
      useVoiceStore.getState().setVoiceStatus('PROCESSING');
      useVoiceStore.getState().setPermissionStatus('denied');
      useVoiceStore.getState().setListenerRunning(true);
      useVoiceStore.getState().setListenerStatus('error');
      useVoiceStore.getState().setTranscript('test');
      useVoiceStore.getState().setPartialTranscript('t');
      useVoiceStore.getState().setFinalTranscript('test');
      useVoiceStore.getState().setProcessing(true);
      useVoiceStore.getState().setVoiceResult({ status: 'success' });
      useVoiceStore.getState().setError({ type: 'timeout', message: 'timed out' });
      useVoiceStore.getState().setConnectionState('ERROR');
    });

    const state = useVoiceStore.getState();
    expect(selectVoiceStatus(state)).toBe('PROCESSING');
    expect(selectPermissionStatus(state)).toBe('denied');
    expect(selectListenerRunning(state)).toBe(true);
    expect(selectListenerStatus(state)).toBe('error');
    expect(selectVoiceTranscript(state)).toBe('test');
    expect(selectVoicePartialTranscript(state)).toBe('t');
    expect(selectVoiceFinalTranscript(state)).toBe('test');
    expect(selectVoiceProcessing(state)).toBe(true);
    expect(selectVoiceLatestResult(state)).toEqual({ status: 'success' });
    expect(selectVoiceError(state)).toEqual({ type: 'timeout', message: 'timed out' });
    expect(selectVoiceConnectionState(state)).toBe('ERROR');
  });
});

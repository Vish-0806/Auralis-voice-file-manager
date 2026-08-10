import { describe, it, expect, vi } from 'vitest';
import {
  TelemetryRuntime,
  TelemetryProvider,
  TelemetryStateError
} from '../../../src/observability';

describe('TelemetryRuntime & Lifecycle Tests', () => {
  it('1. constructor should initialize with default TelemetryProvider if none injected', () => {
    const runtime = new TelemetryRuntime();
    expect(runtime.provider()).toBeInstanceOf(TelemetryProvider);
  });

  it('2. constructor should accept and use an injected TelemetryProvider', () => {
    const provider = new TelemetryProvider();
    const runtime = new TelemetryRuntime(provider);
    expect(runtime.provider()).toBe(provider);
  });

  it('3. initialize() should move runtime state to READY', async () => {
    const runtime = new TelemetryRuntime();
    expect(runtime.getState()).toBe('UNINITIALIZED');
    await runtime.initialize();
    expect(runtime.getState()).toBe('READY');
  });

  it('4. shutdown() should move runtime state to STOPPED', async () => {
    const runtime = new TelemetryRuntime();
    await runtime.initialize();
    await runtime.shutdown();
    expect(runtime.getState()).toBe('STOPPED');
  });

  it('5. lifecycle operations should be idempotent', async () => {
    const runtime = new TelemetryRuntime();
    await runtime.initialize();
    await runtime.initialize();
    expect(runtime.getState()).toBe('READY');

    await runtime.shutdown();
    await runtime.shutdown();
    expect(runtime.getState()).toBe('STOPPED');
  });

  it('6. invalid lifecycle transitions should throw TelemetryStateError', async () => {
    const runtime = new TelemetryRuntime();
    await expect(runtime.shutdown()).rejects.toThrow(TelemetryStateError);

    await runtime.initialize();
    await runtime.shutdown();
    await expect(runtime.initialize()).rejects.toThrow(TelemetryStateError);
  });

  it('7. provider delegation works correctly', async () => {
    const provider = new TelemetryProvider();
    const runtime = new TelemetryRuntime(provider);
    const spy = vi.spyOn(provider, 'getState');
    runtime.getState();
    expect(spy).toHaveBeenCalled();
  });
});

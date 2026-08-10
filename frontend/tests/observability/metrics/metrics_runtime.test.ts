import { describe, it, expect, vi } from 'vitest';
import {
  MetricsRuntime,
  MetricsProvider,
  MetricsStateError
} from '../../../src/observability';

describe('MetricsRuntime & Lifecycle Tests', () => {
  it('1. constructor should initialize with default MetricsProvider if none injected', () => {
    const runtime = new MetricsRuntime();
    expect(runtime.provider()).toBeInstanceOf(MetricsProvider);
  });

  it('2. constructor should accept and use an injected MetricsProvider', () => {
    const provider = new MetricsProvider();
    const runtime = new MetricsRuntime(provider);
    expect(runtime.provider()).toBe(provider);
  });

  it('3. initialize() should move runtime state to READY', async () => {
    const runtime = new MetricsRuntime();
    expect(runtime.getState()).toBe('UNINITIALIZED');
    await runtime.initialize();
    expect(runtime.getState()).toBe('READY');
  });

  it('4. shutdown() should move runtime state to STOPPED', async () => {
    const runtime = new MetricsRuntime();
    await runtime.initialize();
    await runtime.shutdown();
    expect(runtime.getState()).toBe('STOPPED');
  });

  it('5. lifecycle operations should be idempotent', async () => {
    const runtime = new MetricsRuntime();
    await runtime.initialize();
    await runtime.initialize();
    expect(runtime.getState()).toBe('READY');

    await runtime.shutdown();
    await runtime.shutdown();
    expect(runtime.getState()).toBe('STOPPED');
  });

  it('6. invalid lifecycle transitions should throw MetricsStateError', async () => {
    const runtime = new MetricsRuntime();
    await expect(runtime.shutdown()).rejects.toThrow(MetricsStateError);

    await runtime.initialize();
    await runtime.shutdown();
    await expect(runtime.initialize()).rejects.toThrow(MetricsStateError);
  });

  it('7. provider delegation works correctly', async () => {
    const provider = new MetricsProvider();
    const runtime = new MetricsRuntime(provider);
    const spy = vi.spyOn(provider, 'getState');
    runtime.getState();
    expect(spy).toHaveBeenCalled();
  });
});

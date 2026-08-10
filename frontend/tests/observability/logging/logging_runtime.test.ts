import { describe, it, expect, vi } from 'vitest';
import {
  LoggingRuntime,
  LoggingProvider,
  LoggingStateError
} from '../../../src/observability';

describe('LoggingRuntime & Lifecycle Tests', () => {
  it('1. constructor should initialize with default LoggingProvider if none injected', () => {
    const runtime = new LoggingRuntime();
    expect(runtime.provider()).toBeInstanceOf(LoggingProvider);
  });

  it('2. constructor should accept and use an injected LoggingProvider', () => {
    const provider = new LoggingProvider();
    const runtime = new LoggingRuntime(provider);
    expect(runtime.provider()).toBe(provider);
  });

  it('3. initialize() should move runtime state to READY', async () => {
    const runtime = new LoggingRuntime();
    expect(runtime.getState()).toBe('UNINITIALIZED');
    await runtime.initialize();
    expect(runtime.getState()).toBe('READY');
  });

  it('4. shutdown() should move runtime state to STOPPED', async () => {
    const runtime = new LoggingRuntime();
    await runtime.initialize();
    await runtime.shutdown();
    expect(runtime.getState()).toBe('STOPPED');
  });

  it('5. lifecycle operations should be idempotent', async () => {
    const runtime = new LoggingRuntime();
    await runtime.initialize();
    await runtime.initialize();
    expect(runtime.getState()).toBe('READY');

    await runtime.shutdown();
    await runtime.shutdown();
    expect(runtime.getState()).toBe('STOPPED');
  });

  it('6. invalid lifecycle transitions should throw LoggingStateError', async () => {
    const runtime = new LoggingRuntime();
    // Cannot shutdown before initialization
    await expect(runtime.shutdown()).rejects.toThrow(LoggingStateError);

    await runtime.initialize();
    await runtime.shutdown();
    // Cannot initialize from STOPPED state
    await expect(runtime.initialize()).rejects.toThrow(LoggingStateError);
  });

  it('7. logger interface methods should log at appropriate levels', async () => {
    const runtime = new LoggingRuntime();
    await runtime.initialize();
    const logger = runtime.getLogger('test-logger');

    // Should not crash when logging
    logger.trace('trace message');
    logger.debug('debug message');
    logger.info('info message');
    logger.warn('warn message');
    logger.error('error message', new Error('test-err'));
    logger.fatal('fatal message', new Error('fatal-err'));
    
    expect(runtime.getStatistics().totalRecords).toBe(6);
  });

  it('8. child loggers should inherit configurations and context', async () => {
    const runtime = new LoggingRuntime();
    await runtime.initialize();
    const logger = runtime.getLogger('test-logger');
    const child = logger.child({ correlationId: '123' });

    expect(child.getName()).toBe('test-logger');
    
    // Log record via child should carry context
    child.info('Child log message');
    
    const logs = runtime.getRecentLogs();
    expect(logs.length).toBe(1);
    expect(logs[0].correlationId).toBe('123');
    expect(logs[0].context?.correlationId).toBe('123');
  });

  it('9. provider delegation works correctly', async () => {
    const provider = new LoggingProvider();
    const runtime = new LoggingRuntime(provider);
    const spy = vi.spyOn(provider, 'getState');
    runtime.getState();
    expect(spy).toHaveBeenCalled();
  });
});

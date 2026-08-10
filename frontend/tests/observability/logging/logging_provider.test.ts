import { describe, it, expect } from 'vitest';
import {
  LoggingProvider,
  LogLevel,
  InMemoryLogSink
} from '../../../src/observability';

describe('LoggingProvider Tests', () => {
  it('1. should register and unregister sinks correctly', async () => {
    const provider = new LoggingProvider();
    await provider.initialize();
    
    const sink = new InMemoryLogSink('s1', 'MemorySink');
    provider.registerSink(sink);
    expect(provider.listSinks().length).toBe(1);
    expect(provider.getSink('s1')).toBe(sink);

    provider.unregisterSink('s1');
    expect(provider.listSinks().length).toBe(0);
  });

  it('2. should apply global level filtering correctly', async () => {
    const provider = new LoggingProvider();
    await provider.initialize();
    provider.setGlobalMinLevel(LogLevel.WARN);

    const logger = provider.getLogger('test-logger');
    logger.debug('should be filtered');
    logger.info('should be filtered');
    logger.warn('should be logged');
    logger.error('should be logged');

    const stats = provider.getStatistics();
    expect(stats.totalRecords).toBe(4);
    expect(stats.filteredCount).toBe(2);
    expect(stats.warnCount).toBe(1);
    expect(stats.errorCount).toBe(1);
    expect(provider.getRecentLogs().length).toBe(2);
  });

  it('3. should support diagnostics and warnings', async () => {
    const provider = new LoggingProvider();
    await provider.initialize();
    
    const diag = provider.getDiagnostics();
    expect(diag.runtimeState).toBe('READY');
    expect(diag.generatedAt).toBeDefined();
    expect(diag.warnings.length).toBe(0);
  });

  it('4. should retrieve logs filtered by level, logger, and correlation ID', async () => {
    const provider = new LoggingProvider();
    await provider.initialize();
    
    const loggerA = provider.getLogger('logger-A');
    const loggerB = provider.getLogger('logger-B');

    loggerA.info('Message 1', { correlationId: 'corr-1' });
    loggerA.warn('Message 2', { correlationId: 'corr-2' });
    loggerB.info('Message 3', { correlationId: 'corr-1' });

    expect(provider.getLogsByLevel(LogLevel.INFO).length).toBe(2);
    expect(provider.getLogsByLogger('logger-A').length).toBe(2);
    expect(provider.getLogsByCorrelationId('corr-1').length).toBe(2);
  });

  it('5. should flush and clear history cleanly', async () => {
    const provider = new LoggingProvider();
    await provider.initialize();
    const logger = provider.getLogger('test-logger');
    
    logger.info('test');
    expect(provider.getRecentLogs().length).toBe(1);
    
    provider.clearHistory();
    expect(provider.getRecentLogs().length).toBe(0);
    
    await expect(provider.flush()).resolves.not.toThrow();
  });
});

import { describe, it, expect } from 'vitest';
import {
  InMemoryLogSink,
  LoggingProvider,
  LogLevel,
  LoggingValidationError
} from '../../../src/observability';

describe('InMemoryLogSink & Multiple Sinks Tests', () => {
  it('1. should validate capacity on construction', () => {
    expect(() => {
      new InMemoryLogSink('s1', 'Sink', 0);
    }).toThrow(LoggingValidationError);

    expect(() => {
      new InMemoryLogSink('s1', 'Sink', -1);
    }).toThrow(LoggingValidationError);
  });

  it('2. should enforce FIFO capacity eviction when full', async () => {
    const sink = new InMemoryLogSink('s1', 'Sink', 3);

    const provider = new LoggingProvider();
    await provider.initialize();

    const logger = provider.getLogger('test-logger');
    provider.registerSink(sink);

    logger.info('Log 1');
    logger.info('Log 2');
    logger.info('Log 3');
    expect(sink.getRecordCount()).toBe(3);
    
    // Evicts Log 1
    logger.info('Log 4');
    expect(sink.getRecordCount()).toBe(3);
    
    const records = sink.getRecords();
    expect(records[0].message).toBe('Log 2');
    expect(records[1].message).toBe('Log 3');
    expect(records[2].message).toBe('Log 4');
  });

  it('3. should support multiple sinks with different log levels', async () => {
    const provider = new LoggingProvider();
    await provider.initialize();

    const infoSink = new InMemoryLogSink('info-sink', 'Info Sink');
    infoSink.setMinLevel(LogLevel.INFO);
    
    const warnSink = new InMemoryLogSink('warn-sink', 'Warn Sink');
    warnSink.setMinLevel(LogLevel.WARN);

    provider.registerSink(infoSink);
    provider.registerSink(warnSink);

    const logger = provider.getLogger('test-logger');
    logger.info('Info message');
    logger.warn('Warn message');

    expect(infoSink.getRecordCount()).toBe(2);
    expect(warnSink.getRecordCount()).toBe(1);
  });

  it('4. should isolate sink failures from crashing logger calls', async () => {
    const provider = new LoggingProvider();
    await provider.initialize();

    const workingSink = new InMemoryLogSink('working', 'Working Sink');
    
    // Mock a failing sink
    const failingSink = {
      id: 'failing',
      name: 'Failing Sink',
      enabled: true,
      minLevel: LogLevel.TRACE,
      isEnabled: () => true,
      setEnabled: () => {},
      getMinLevel: () => LogLevel.TRACE,
      setMinLevel: () => {},
      write: async () => {
        throw new Error('Write failed');
      },
      flush: async () => {},
      close: async () => {},
      getStatistics: () => ({ totalWrites: 0, failedWrites: 1 })
    };

    provider.registerSink(workingSink);
    provider.registerSink(failingSink as any);

    const logger = provider.getLogger('test-logger');
    
    // Should not throw exception
    expect(() => {
      logger.info('Log message');
    }).not.toThrow();

    await new Promise(resolve => setTimeout(resolve, 0));

    expect(workingSink.getRecordCount()).toBe(1);
    expect(provider.getStatistics().failedSinkWrites).toBe(1);
  });

  it('5. should respect enabled/disabled states of sinks', async () => {
    const provider = new LoggingProvider();
    await provider.initialize();

    const sink = new InMemoryLogSink('s1', 'Sink');
    provider.registerSink(sink);

    const logger = provider.getLogger('test-logger');
    logger.info('Enabled');

    sink.setEnabled(false);
    logger.info('Disabled');

    expect(sink.getRecordCount()).toBe(1);
    expect(sink.getRecords()[0].message).toBe('Enabled');
  });

  it('6. should measure performance targets safely', async () => {
    const provider = new LoggingProvider();
    await provider.initialize();
    
    const start = performance.now();
    provider.getLogger('perf-logger');
    const end = performance.now();
    
    expect(end - start).toBeLessThan(10); // Target is low latency
  });
});

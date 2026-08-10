import { describe, it, expect } from 'vitest';
import {
  LoggingProvider,
  LoggingRegistry,
  LoggingRegistrationError,
  LoggerNotFoundError
} from '../../../src/observability';

describe('LoggingRegistry Tests', () => {
  it('1. should lazily create loggers and support duplicate config rejection', async () => {
    const provider = new LoggingProvider();
    await provider.initialize();
    
    const registry = new LoggingRegistry(provider);
    const logger1 = registry.getLogger('my-logger');
    const logger2 = registry.getLogger('my-logger');

    expect(logger1).toBe(logger2); // O(1) matching instance
    expect(registry.getLoggerCount()).toBe(1);

    // Registering duplicate configuration explicitly throws error
    expect(() => {
      registry.registerLogger('my-logger');
    }).toThrow(LoggingRegistrationError);
  });

  it('2. should unregister loggers correctly and throw if lookup missing', async () => {
    const provider = new LoggingProvider();
    await provider.initialize();
    
    const registry = new LoggingRegistry(provider);
    registry.registerLogger('log-a');
    expect(registry.hasLogger('log-a')).toBe(true);

    registry.unregisterLogger('log-a');
    expect(registry.hasLogger('log-a')).toBe(false);

    expect(() => {
      registry.unregisterLogger('log-a');
    }).toThrow(LoggerNotFoundError);
  });

  it('3. should list configurations and clear cleanly', async () => {
    const provider = new LoggingProvider();
    await provider.initialize();
    
    const registry = new LoggingRegistry(provider);
    registry.registerLogger('c', { minLevel: 'INFO' });
    registry.registerLogger('a', { minLevel: 'WARN' });

    const list = registry.listLoggers();
    expect(list.length).toBe(2);
    // Alphabetical sort by logger name
    expect(list[0].name).toBe('a');
    expect(list[1].name).toBe('c');

    registry.clear();
    expect(registry.getLoggerCount()).toBe(0);
  });
});

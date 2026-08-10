import { describe, it, expect } from 'vitest';
import {
  TelemetryRegistry,
  InMemoryTelemetryExporter,
  TelemetryExporterAlreadyExistsError,
  TelemetryExporterNotFoundError
} from '../../../src/observability';

describe('TelemetryRegistry Tests', () => {
  it('1. should register and retrieve exporters', () => {
    const registry = new TelemetryRegistry();
    const exporter = new InMemoryTelemetryExporter('test.exp');
    
    registry.register(exporter);
    expect(registry.getExporterCount()).toBe(1);
    expect(registry.get('test.exp')).toBe(exporter);

    expect(() => {
      registry.register(exporter); // duplicate name
    }).toThrow(TelemetryExporterAlreadyExistsError);
  });

  it('2. should check existence and remove correctly', () => {
    const registry = new TelemetryRegistry();
    const exporter = new InMemoryTelemetryExporter('exp');

    registry.register(exporter);
    expect(registry.has('exp')).toBe(true);

    registry.remove('exp');
    expect(registry.has('exp')).toBe(false);
    expect(() => {
      registry.get('exp');
    }).toThrow(TelemetryExporterNotFoundError);
  });
});

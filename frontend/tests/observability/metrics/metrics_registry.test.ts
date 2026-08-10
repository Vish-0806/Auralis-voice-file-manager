import { describe, it, expect } from 'vitest';
import {
  MetricsRegistry,
  CounterMetric,
  MetricType,
  MetricAlreadyExistsError,
  MetricsValidationError
} from '../../../src/observability';

describe('MetricsRegistry Tests', () => {
  it('1. should register and reject duplicates', () => {
    const registry = new MetricsRegistry();
    const mockDef = { name: 'm.name', type: MetricType.COUNTER, labelKeys: [], enabled: true };
    const inst = new CounterMetric(mockDef, () => {});
    
    registry.register(inst);
    expect(registry.getMetricCount()).toBe(1);

    expect(() => {
      registry.register(inst);
    }).toThrow(MetricAlreadyExistsError);
  });

  it('2. should validate metric naming rules', () => {
    const registry = new MetricsRegistry();
    const badDef = { name: 'invalid name here', type: MetricType.COUNTER, labelKeys: [], enabled: true };
    const inst = new CounterMetric(badDef, () => {});

    expect(() => {
      registry.register(inst);
    }).toThrow(MetricsValidationError);
  });

  it('3. should check has metric and support clear', () => {
    const registry = new MetricsRegistry();
    const mockDef = { name: 'c', type: MetricType.COUNTER, labelKeys: [], enabled: true };
    const inst = new CounterMetric(mockDef, () => {});

    registry.register(inst);
    expect(registry.has('c')).toBe(true);

    registry.clear();
    expect(registry.has('c')).toBe(false);
    expect(registry.getMetricCount()).toBe(0);
  });
});

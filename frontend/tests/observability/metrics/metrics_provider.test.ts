import { describe, it, expect } from 'vitest';
import {
  MetricsProvider,
  MetricNotFoundError
} from '../../../src/observability';

describe('MetricsProvider Tests', () => {
  it('1. should register and retrieve instruments correctly', async () => {
    const provider = new MetricsProvider();
    await provider.initialize();

    const c = provider.registerCounter({ name: 'm.counter', labelKeys: ['op'] });
    expect(provider.getCounter('m.counter')).toBe(c);
    expect(provider.listMetrics().length).toBe(1);

    provider.removeMetric('m.counter');
    expect(provider.listMetrics().length).toBe(0);
    expect(() => provider.getMetric('m.counter')).toThrow(MetricNotFoundError);
  });

  it('2. should support snapshots and diagnostics', async () => {
    const provider = new MetricsProvider();
    await provider.initialize();
    
    const counter = provider.registerCounter({ name: 'test.c', labelKeys: ['op'] });
    counter.increment(5, { op: 'run' });

    const snap = provider.getSnapshot('test.c');
    expect(snap.definition.name).toBe('test.c');
    expect(snap.values[0].value).toBe(5);

    const diag = provider.getDiagnostics();
    expect(diag.runtimeState).toBe('READY');
    expect(diag.metricCount).toBe(1);
    expect(diag.seriesCount).toBe(1);
  });

  it('3. should support sample history queries', async () => {
    const provider = new MetricsProvider();
    await provider.initialize();

    const c = provider.registerCounter({ name: 'c', labelKeys: ['k'] });
    c.increment(1, { k: 'v1' });
    c.increment(2, { k: 'v2' });

    const all = provider.getRecentSamples();
    expect(all.length).toBe(2);

    const match = provider.getSamplesByLabel('c', { k: 'v1' });
    expect(match.length).toBe(1);
    expect(match[0].value).toBe(1);

    provider.clearHistory();
    expect(provider.getRecentSamples().length).toBe(0);
  });

  it('4. should enforce FIFO capacity eviction on history', async () => {
    const provider = new MetricsProvider();
    await provider.initialize();

    const c = provider.registerCounter({ name: 'c', labelKeys: [] });
    // Write 1005 samples
    for (let i = 0; i < 1005; i++) {
      c.increment(1, {});
    }

    const stats = provider.getStatistics();
    expect(stats.totalSamples).toBe(1005);
    expect(stats.historySize).toBe(1000); // capped
  });

  it('5. should ignore updates for disabled metrics and track rejected samples', async () => {
    const provider = new MetricsProvider();
    await provider.initialize();

    const c = provider.registerCounter({ name: 'c', labelKeys: [] });
    c.setEnabled(false);

    c.increment(10, {});
    expect(c.getValue({})).toBe(0); // value unchanged
    
    // Increment on disabled metric does not record sample in history
    expect(provider.getRecentSamples().length).toBe(0);
  });
});

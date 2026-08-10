import { describe, it, expect } from 'vitest';
import {
  MetricsProvider,
  normalizeLabels,
  getSeriesKey,
  MetricsValidationError
} from '../../../src/observability';

describe('Metrics Aggregation & Labels Tests', () => {
  it('1. should resolve same series regardless of label order', () => {
    const l1 = { src: 'workspace', op: 'search' };
    const l2 = { op: 'search', src: 'workspace' };

    const n1 = normalizeLabels(l1);
    const n2 = normalizeLabels(l2);

    expect(getSeriesKey(n1)).toBe(getSeriesKey(n2));
  });

  it('2. should validate labels against schema', async () => {
    const provider = new MetricsProvider();
    await provider.initialize();

    const c = provider.registerCounter({ name: 'c', labelKeys: ['op', 'src'] });

    expect(() => {
      c.increment(1, { op: 'search' }); // missing 'src' key
    }).toThrow(MetricsValidationError);

    expect(() => {
      c.increment(1, { op: 'search', src: 'workspace', extra: 'bad' }); // extra key
    }).toThrow(MetricsValidationError);
  });

  it('3. snapshot values should be deeply frozen', async () => {
    const provider = new MetricsProvider();
    await provider.initialize();

    const c = provider.registerCounter({ name: 'c', labelKeys: ['k'] });
    c.increment(5, { k: 'v1' });

    const snap = provider.getSnapshot('c');
    expect(Object.isFrozen(snap)).toBe(true);
    expect(Object.isFrozen(snap.definition)).toBe(true);
    expect(Object.isFrozen(snap.values)).toBe(true);
    expect(Object.isFrozen(snap.values[0].labels)).toBe(true);
  });
});

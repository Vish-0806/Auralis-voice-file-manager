import { describe, it, expect } from 'vitest';
import {
  TelemetryProvider,
  TelemetryValidationError,
  shouldSampleRecord
} from '../../../src/observability';

describe('Telemetry Sampling Tests', () => {
  it('1. should validate invalid sampling rates', async () => {
    const provider = new TelemetryProvider();
    await provider.initialize();

    expect(() => {
      provider.setSamplingRate(-0.1);
    }).toThrow(TelemetryValidationError);

    expect(() => {
      provider.setSamplingRate(1.5);
    }).toThrow(TelemetryValidationError);
  });

  it('2. should make deterministic sampling decisions based on ID', () => {
    const rate = 0.5;
    const ids = ['r1', 'r2', 'r3', 'r4', 'r5', 'r6', 'r7', 'r8'];
    const decisions1 = ids.map(id => shouldSampleRecord(id, rate));
    const decisions2 = ids.map(id => shouldSampleRecord(id, rate));

    expect(decisions1).toEqual(decisions2); // deterministic
  });

  it('3. should always keep ERROR/FATAL severity regardless of sampling rate', async () => {
    const provider = new TelemetryProvider();
    await provider.initialize();

    provider.setSamplingRate(0.0); // drop everything normally

    provider.record({
      id: 'r.error',
      timestamp: Date.now(),
      type: 'LOG',
      source: 'test',
      name: 'log',
      severity: 'ERROR'
    });

    const stats = provider.getStatistics();
    expect(stats.recordsAccepted).toBe(1); // kept
    expect(stats.recordsSampled).toBe(0);
  });
});

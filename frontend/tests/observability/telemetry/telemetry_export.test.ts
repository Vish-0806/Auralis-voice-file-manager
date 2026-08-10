import { describe, it, expect } from 'vitest';
import {
  TelemetryProvider,
  InMemoryTelemetryExporter
} from '../../../src/observability';

describe('Telemetry Export Pipeline Tests', () => {
  it('1. should export batch successfully to enabled exporter', async () => {
    const provider = new TelemetryProvider();
    await provider.initialize();

    const exporter = new InMemoryTelemetryExporter('test.exp');
    provider.registerExporter(exporter);

    provider.recordEvent('click');
    await provider.flush();

    expect(exporter.getExportedRecords().length).toBe(1);
    expect(exporter.getExportedRecords()[0].name).toBe('click');

    const stats = provider.getStatistics();
    expect(stats.recordsExported).toBe(1);
  });

  it('2. should isolate failed exporter and not prevent other exporters from receiving batch', async () => {
    const provider = new TelemetryProvider();
    await provider.initialize();

    const exp1 = new InMemoryTelemetryExporter('exp1');
    const exp2 = new InMemoryTelemetryExporter('exp2');
    exp1.setShouldFail(true); // exp1 fails

    provider.registerExporter(exp1);
    provider.registerExporter(exp2);

    provider.recordEvent('click');
    await provider.flush();

    // exp2 should have received record, exp1 failed
    expect(exp2.getExportedRecords().length).toBe(1);
    expect(exp1.getExportedRecords().length).toBe(0);

    const stats = provider.getStatistics();
    expect(stats.exportFailures).toBeGreaterThan(0);
    expect(stats.recordsExported).toBe(1); // exp2 succeeded
  });

  it('3. should enforce retries on exporter failure', async () => {
    const provider = new TelemetryProvider();
    await provider.initialize();

    const exp = new InMemoryTelemetryExporter('exp');
    exp.setShouldFail(true); // fail all attempts

    provider.registerExporter(exp);
    provider.recordEvent('click');
    await provider.flush();

    const stats = provider.getStatistics();
    expect(stats.retryAttempts).toBe(3); // retries 3 times
  });
});
